from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from backend.api import (
    _aggregate_today_dashboard,
    _filter_by_domain,
    _load_combined_articles,
    compliance_control_intelligence,
)
from backend.logging_config import LOGGER

FRONTEND_DATA_DIR = Path(__file__).resolve().parents[2] / "frontend" / "public" / "data"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _summary_payload(dashboard_payload: Dict[str, Any]) -> Dict[str, Any]:
    summary = dashboard_payload.get("summary")
    if isinstance(summary, dict):
        return summary
    return {
        "headline": "Daily cyber intelligence summary",
        "summary": "Dashboard is currently updating.",
        "key_risks": [],
        "top_priorities": [],
        "confidence": "medium",
    }


def _build_domain_payload(items: List[Dict[str, Any]], generated_at: str) -> Dict[str, Any]:
    return {
        "generatedAt": generated_at,
        "count": len(items),
        "items": items,
    }


def export_static_dashboard_data() -> Dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    dashboard_payload = _aggregate_today_dashboard()
    combined_items = _load_combined_articles()

    news_payload = _build_domain_payload(dashboard_payload.get("articles", []), generated_at)
    trends_payload = {
        "generatedAt": generated_at,
        "trendData": dashboard_payload.get("trendData", []),
        "sourceGroups": dashboard_payload.get("sourceGroups", []),
    }
    regulations_payload = compliance_control_intelligence(
        country=None,
        framework=None,
        regulator=None,
        control=None,
        industry=None,
        risk_level=None,
        security_domain=None,
        identity=None,
        cloud=None,
        ai=None,
        operational_resilience=None,
        privacy=None,
        critical_infrastructure=None,
    )
    threats_payload = _build_domain_payload(_filter_by_domain(combined_items, "threats"), generated_at)
    research_payload = _build_domain_payload(_filter_by_domain(combined_items, "research"), generated_at)

    _write_json(FRONTEND_DATA_DIR / "dashboard.json", dashboard_payload)
    _write_json(FRONTEND_DATA_DIR / "news.json", news_payload)
    _write_json(FRONTEND_DATA_DIR / "trends.json", trends_payload)
    _write_json(FRONTEND_DATA_DIR / "executive-summary.json", _summary_payload(dashboard_payload))
    _write_json(FRONTEND_DATA_DIR / "regulations.json", regulations_payload)
    _write_json(FRONTEND_DATA_DIR / "threats.json", threats_payload)
    _write_json(FRONTEND_DATA_DIR / "research.json", research_payload)

    manifest = {
        "generatedAt": generated_at,
        "files": [
            "dashboard.json",
            "news.json",
            "trends.json",
            "executive-summary.json",
            "regulations.json",
            "threats.json",
            "research.json",
        ],
    }
    _write_json(FRONTEND_DATA_DIR / "manifest.json", manifest)

    LOGGER.info("Exported static dashboard payloads to %s", FRONTEND_DATA_DIR)
    return manifest


if __name__ == "__main__":
    export_static_dashboard_data()
