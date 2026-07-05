from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from backend.config import DATA_DIR
from backend.logging_config import LOGGER

from .engine import build_daily_brief, build_reports, enrich_articles
from .persistence import upsert_intelligence_records
from .registry import load_source_registry
from .reliability import with_retries


_HTTP_HEADERS = {
    "User-Agent": "CyberExecutiveIntelligence/1.0",
    "Accept": "application/json, application/rss+xml, application/xml, text/xml, text/html",
}


@dataclass
class IngestionSummary:
    source_count: int
    attempted_sources: int
    successful_sources: int
    collected_items: int
    deduplicated_items: int
    inserted_records: int
    updated_records: int
    skipped_records: int
    generated_at: str


def _safe_get(url: str, timeout_seconds: int = 20) -> requests.Response:
    return requests.get(url, timeout=timeout_seconds, headers=_HTTP_HEADERS)


def _extract_text(entry: ET.Element, names: List[str]) -> str:
    for name in names:
        node = entry.find(name)
        if node is not None and node.text:
            return node.text.strip()
        found = entry.findtext(name)
        if found:
            return found.strip()
    return ""


def _extract_link(entry: ET.Element) -> str:
    direct = _extract_text(entry, ["link", "url"])
    if direct:
        return direct
    link_node = entry.find("link")
    if link_node is not None:
        href = link_node.attrib.get("href", "")
        if href:
            return href.strip()
    return ""


def _parse_rss(source: Dict[str, Any], rss_feed: str) -> List[Dict[str, Any]]:
    response = _safe_get(rss_feed)
    response.raise_for_status()
    root = ET.fromstring(response.text)

    entries: List[ET.Element] = []
    if root.tag.endswith("rss"):
        channel = root.find("channel")
        if channel is not None:
            entries = list(channel.findall("item"))
    elif root.tag.endswith("feed"):
        entries = [child for child in root if child.tag.endswith("entry")]

    items: List[Dict[str, Any]] = []
    for entry in entries[:50]:
        title = _extract_text(entry, ["title"])
        url = _extract_link(entry)
        summary = _extract_text(entry, ["description", "summary", "content"])
        if not title and not url:
            continue
        items.append(
            {
                "title": title or url,
                "summary": summary,
                "author": _extract_text(entry, ["author", "creator", "name"]) or "Unknown",
                "published_at": _extract_text(entry, ["pubDate", "published", "updated"]),
                "url": url,
                "source": source.get("name"),
                "category": source.get("category") or "General",
                "tags": source.get("supported_frameworks") or [],
            }
        )
    return items


def _parse_api(source: Dict[str, Any], api_url: str) -> List[Dict[str, Any]]:
    response = _safe_get(api_url)
    response.raise_for_status()
    payload = response.json()

    items: List[Dict[str, Any]]
    if isinstance(payload, dict):
        if isinstance(payload.get("items"), list):
            items = payload["items"]
        elif isinstance(payload.get("vulnerabilities"), list):
            items = payload["vulnerabilities"]
        else:
            items = [payload]
    elif isinstance(payload, list):
        items = payload
    else:
        items = []

    normalized: List[Dict[str, Any]] = []
    for item in items[:100]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("name") or item.get("cveID") or item.get("cve") or "").strip()
        url = str(item.get("url") or item.get("link") or source.get("official_website") or "").strip()
        summary = str(item.get("summary") or item.get("description") or item.get("shortDescription") or "").strip()
        if not title and not summary:
            continue
        normalized.append(
            {
                "title": title or summary[:120],
                "summary": summary,
                "author": str(item.get("author") or "Unknown"),
                "published_at": item.get("published") or item.get("dateAdded") or item.get("published_at"),
                "url": url,
                "source": source.get("name"),
                "category": source.get("category") or "General",
                "tags": source.get("supported_frameworks") or [],
            }
        )
    return normalized


def _parse_html(source: Dict[str, Any], website_url: str) -> List[Dict[str, Any]]:
    response = _safe_get(website_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    items: List[Dict[str, Any]] = []
    candidates = soup.select("article a[href], h2 a[href], h3 a[href]")
    for node in candidates[:60]:
        href = (node.get("href") or "").strip()
        title = node.get_text(" ", strip=True)
        if not title or not href:
            continue
        if href.startswith("/"):
            href = website_url.rstrip("/") + href

        items.append(
            {
                "title": title,
                "summary": "",
                "author": "Unknown",
                "published_at": None,
                "url": href,
                "source": source.get("name"),
                "category": source.get("category") or "General",
                "tags": source.get("supported_frameworks") or [],
            }
        )
    return items


def _collect_source(source: Dict[str, Any]) -> List[Dict[str, Any]]:
    method = str(source.get("collection_method") or "rss").lower()

    api_url = source.get("api")
    rss_feed = source.get("rss_feed")
    website = source.get("official_website")

    if api_url and ("api" in method or method in {"api", "api+rss"}):
        api_items = _parse_api(source, str(api_url))
        if api_items:
            return api_items

    if rss_feed:
        rss_items = _parse_rss(source, str(rss_feed))
        if rss_items:
            return rss_items

    if api_url:
        api_items = _parse_api(source, str(api_url))
        if api_items:
            return api_items

    if website:
        return _parse_html(source, str(website))

    return []


def _dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for item in items:
        title = str(item.get("title") or "").strip().lower()
        url = str(item.get("url") or "").strip().lower()
        key = (title, url)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_ingestion_enrichment_pipeline(max_sources: Optional[int] = None) -> Dict[str, Any]:
    """Collect from configured sources, enrich, persist, and publish snapshots."""

    sources = [
        source
        for source in load_source_registry()
        if any(source.get(key) for key in ["api", "rss_feed", "official_website"])
    ]
    if max_sources is not None:
        sources = sources[: max(0, max_sources)]

    collected: List[Dict[str, Any]] = []
    attempted = 0
    successful = 0

    for source in sources:
        attempted += 1

        def _op() -> List[Dict[str, Any]]:
            return _collect_source(source)

        try:
            items = with_retries(_op, retries=2, base_delay_seconds=0.5)
        except Exception:
            LOGGER.warning("Source collection failed for %s", source.get("name"), exc_info=True)
            continue

        if not items:
            continue

        now = datetime.now(timezone.utc).isoformat()
        source["last_successful_sync"] = now
        successful += 1
        for item in items:
            item["source_group"] = source.get("category") or "General Sources"
        collected.extend(items)

    deduped = _dedupe(collected)
    enriched = enrich_articles(deduped)
    persistence = upsert_intelligence_records(enriched)

    daily_dir = DATA_DIR / "daily"
    _write_json(daily_dir / "combined.json", deduped)
    _write_json(daily_dir / "enriched_v2.json", enriched)
    _write_json(daily_dir / "executive_daily_brief_v2.json", build_daily_brief(enriched))
    _write_json(daily_dir / "weekly_report_v2.json", build_reports(enriched, report_type="weekly"))
    _write_json(daily_dir / "monthly_report_v2.json", build_reports(enriched, report_type="monthly"))
    _write_json(daily_dir / "board_report_v2.json", build_reports(enriched, report_type="board"))

    summary = IngestionSummary(
        source_count=len(sources),
        attempted_sources=attempted,
        successful_sources=successful,
        collected_items=len(collected),
        deduplicated_items=len(deduped),
        inserted_records=persistence["inserted"],
        updated_records=persistence["updated"],
        skipped_records=persistence["skipped"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    payload = summary.__dict__
    _write_json(daily_dir / "ingestion_status_v2.json", payload)
    return payload
