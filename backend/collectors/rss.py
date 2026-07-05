from __future__ import annotations

from typing import Any, Dict, List
import xml.etree.ElementTree as ET

import requests

from backend.collectors.base import BaseCollector
from backend.logging_config import LOGGER


class RSSCollector(BaseCollector):
    """Collector for any RSS/Atom feed."""

    def __init__(self, name: str, source_name: str, category: str, endpoint: str, metadata: Dict[str, Any] | None = None):
        super().__init__(name=name, source_name=source_name, category=category, endpoint=endpoint, metadata=metadata)

    def fetch(self) -> List[Dict[str, Any]]:
        try:
            response = requests.get(self.endpoint, timeout=20, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/rss+xml, application/xml, text/xml"})
            response.raise_for_status()
            return [{"raw": response.text}]
        except requests.RequestException as exc:
            LOGGER.warning("RSS collector %s could not fetch %s: %s", self.name, self.endpoint, exc)
            return []

    def parse(self, payload: Any) -> List[Dict[str, Any]]:
        raw = payload[0]["raw"] if payload else ""
        if not raw:
            return []

        root = ET.fromstring(raw)
        items: List[Dict[str, Any]] = []
        entries = []
        if root.tag.endswith("rss"):
            channel = root.find("channel")
            if channel is not None:
                entries = list(channel.findall("item"))
        elif root.tag.endswith("feed"):
            entries = [child for child in root if child.tag.endswith("entry")]
        else:
            entries = [child for child in root if child.tag.endswith("item") or child.tag.endswith("entry")]

        for entry in entries:
            title = self._find_text(entry, ["title", "headline"])
            description = self._find_text(entry, ["description", "summary", "content"])
            items.append(
                {
                    "title": title or self._find_text(entry, ["link"]) or "",
                    "author": self._find_text(entry, ["author", "creator", "name"]) or "Unknown",
                    "published_at": self._find_text(entry, ["pubDate", "published", "updated", "published_at"]),
                    "url": self._find_text(entry, ["link", "url"])
                    or self._find_attr(entry, ["link"], "href")
                    or "",
                    "summary": description or "",
                }
            )
        return items

    def _find_text(self, element: Any, names: List[str]) -> str:
        for name in names:
            node = element.find(name)
            if node is not None and node.text:
                return node.text.strip()
            if element.findtext(name):
                return element.findtext(name).strip()
        return ""

    def _find_attr(self, element: Any, names: List[str], attr: str) -> str:
        for name in names:
            node = element.find(name)
            if node is not None:
                value = node.attrib.get(attr, "")
                if value:
                    return value.strip()
        return ""
