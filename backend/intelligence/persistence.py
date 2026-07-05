from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy.orm import Session

from backend.database.db import SessionLocal
from backend.logging_config import LOGGER
from backend.models import IntelligenceRecord


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(entry) for entry in value if str(entry).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _dedupe_key(article: Dict[str, Any]) -> str:
    title = str(article.get("title") or "").strip().lower()
    url = str(article.get("url") or "").strip().lower()
    raw = f"{title}|{url}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def upsert_intelligence_records(enriched_articles: Iterable[Dict[str, Any]], db: Session | None = None) -> Dict[str, int]:
    """Upsert enriched intelligence articles into normalized storage."""

    owns_session = db is None
    session = db or SessionLocal()

    inserted = 0
    updated = 0
    skipped = 0

    try:
        for article in enriched_articles:
            title = str(article.get("title") or "").strip()
            if not title:
                skipped += 1
                continue

            dedupe_key = _dedupe_key(article)
            record = session.query(IntelligenceRecord).filter(IntelligenceRecord.dedupe_key == dedupe_key).first()

            payload = {
                "title": title,
                "author": str(article.get("author") or "Unknown"),
                "source": str(article.get("source") or "Unknown"),
                "category": str(article.get("category") or "General"),
                "subcategory": str(article.get("subcategory") or "General"),
                "country": str(article.get("country") or "Global"),
                "summary": str(article.get("summary") or ""),
                "executive_summary": str(article.get("executiveSummary") or ""),
                "technical_summary": str(article.get("technicalSummary") or ""),
                "business_impact": str(article.get("businessImpact") or ""),
                "operational_impact": str(article.get("operationalImpact") or ""),
                "risk_rating": str(article.get("riskRating") or "medium"),
                "confidence_score": float(article.get("confidenceScore") or 0.0),
                "url": str(article.get("url") or ""),
                "published_at": _parse_datetime(article.get("publishedDate")),
                "industries": _as_list(article.get("industry")),
                "frameworks": _as_list(article.get("framework")),
                "technologies": _as_list(article.get("technology")),
                "cves": _as_list(article.get("cve")),
                "mitre_techniques": _as_list(article.get("mitreTechnique")),
                "mitre_tactics": _as_list(article.get("mitreTactic")),
                "tags": _as_list(article.get("tags")),
                "quality_scoring": article.get("qualityScoring") or {},
                "why_this_matters": article.get("whyThisMatters") or {},
            }

            if record is None:
                record = IntelligenceRecord(dedupe_key=dedupe_key, **payload)
                session.add(record)
                inserted += 1
            else:
                for field, value in payload.items():
                    setattr(record, field, value)
                updated += 1

        session.commit()
    except Exception:
        session.rollback()
        LOGGER.exception("Failed to upsert intelligence records")
        raise
    finally:
        if owns_session:
            session.close()

    return {"inserted": inserted, "updated": updated, "skipped": skipped}
