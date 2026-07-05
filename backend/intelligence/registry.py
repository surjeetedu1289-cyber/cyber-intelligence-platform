from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from backend.config import BASE_DIR

_REGISTRY_PATH = BASE_DIR / "config" / "source_registry.json"


def _virtual_topic_sources() -> List[Dict[str, Any]]:
    base_virtuals = [
        {
            "name": "Identity Governance Topic Monitor",
            "tier": "TIER 4",
            "category": "Identity & Access Management",
            "rss_feed": None,
            "official_website": "",
            "api": None,
            "refresh_frequency": "15m",
            "trust_score": 0.9,
            "executive_relevance_score": 0.95,
            "geographic_coverage": ["Global", "Australia"],
            "industry_coverage": ["Financial Services", "Cross-Industry"],
            "supported_frameworks": ["NIST CSF", "APRA CPS234", "ISO27001"],
            "collection_method": "derived-topical-index",
            "last_successful_sync": None,
        },
        {
            "name": "AI Security & Agentic AI Topic Monitor",
            "tier": "TIER 5",
            "category": "AI Security",
            "rss_feed": None,
            "official_website": "",
            "api": None,
            "refresh_frequency": "15m",
            "trust_score": 0.9,
            "executive_relevance_score": 0.96,
            "geographic_coverage": ["Global", "Australia"],
            "industry_coverage": ["Financial Services", "Cross-Industry"],
            "supported_frameworks": ["NIST AI RMF", "ISO42001"],
            "collection_method": "derived-topical-index",
            "last_successful_sync": None,
        },
        {
            "name": "Financial Services Cyber Risk Topic Monitor",
            "tier": "TIER 6",
            "category": "Financial Services",
            "rss_feed": None,
            "official_website": "",
            "api": None,
            "refresh_frequency": "15m",
            "trust_score": 0.92,
            "executive_relevance_score": 0.98,
            "geographic_coverage": ["Australia", "Global"],
            "industry_coverage": ["Financial Services", "Banking", "Insurance", "Superannuation", "Payments"],
            "supported_frameworks": ["APRA CPS230", "APRA CPS234", "DORA", "NIS2", "PCI DSS"],
            "collection_method": "derived-topical-index",
            "last_successful_sync": None,
        },
        {
            "name": "Research & Emerging Technology Topic Monitor",
            "tier": "TIER 8",
            "category": "Research",
            "rss_feed": None,
            "official_website": "",
            "api": None,
            "refresh_frequency": "60m",
            "trust_score": 0.88,
            "executive_relevance_score": 0.84,
            "geographic_coverage": ["Global"],
            "industry_coverage": ["Cross-Industry", "Financial Services"],
            "supported_frameworks": ["NIST CSF", "NIST AI RMF", "MITRE ATT&CK"],
            "collection_method": "derived-topical-index",
            "last_successful_sync": None,
        },
    ]

    required_named_sources = [
        ("Black Hat", "TIER 8", "Research"),
        ("DEF CON", "TIER 8", "Research"),
        ("RSA Conference", "TIER 8", "Research"),
        ("USENIX", "TIER 8", "Research"),
        ("arXiv", "TIER 8", "Research"),
        ("OpenAI Research", "TIER 8", "Research"),
        ("Anthropic Research", "TIER 8", "Research"),
        ("Google DeepMind", "TIER 8", "Research"),
        ("Microsoft Research", "TIER 8", "Research"),
        ("MLCommons", "TIER 8", "Research"),
        ("AI Incident Database", "TIER 8", "Research"),
        ("FIDO Alliance", "TIER 4", "Identity & Access Management"),
        ("OpenID Foundation", "TIER 4", "Identity & Access Management"),
        ("SCIM Working Group", "TIER 4", "Identity & Access Management"),
    ]

    for name, tier, category in required_named_sources:
        base_virtuals.append(
            {
                "name": name,
                "tier": tier,
                "category": category,
                "rss_feed": None,
                "official_website": "",
                "api": None,
                "refresh_frequency": "60m",
                "trust_score": 0.85,
                "executive_relevance_score": 0.82,
                "geographic_coverage": ["Global"],
                "industry_coverage": ["Cross-Industry", "Financial Services"],
                "supported_frameworks": ["NIST CSF", "NIST AI RMF", "ISO27001", "ISO42001"],
                "collection_method": "derived-topical-index",
                "last_successful_sync": None,
            }
        )

    return base_virtuals


def load_source_registry() -> List[Dict[str, Any]]:
    if not _REGISTRY_PATH.exists():
        return []

    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return []

    sources: List[Dict[str, Any]] = []
    for source in payload:
        if not isinstance(source, dict):
            continue
        normalized = {
            "name": str(source.get("name") or "Unknown"),
            "tier": str(source.get("tier") or "TIER 0"),
            "category": str(source.get("category") or "General"),
            "rss_feed": source.get("rss_feed"),
            "official_website": str(source.get("official_website") or ""),
            "api": source.get("api"),
            "refresh_frequency": str(source.get("refresh_frequency") or "60m"),
            "trust_score": float(source.get("trust_score") or 0.5),
            "executive_relevance_score": float(source.get("executive_relevance_score") or 0.5),
            "geographic_coverage": [str(entry) for entry in source.get("geographic_coverage") or []],
            "industry_coverage": [str(entry) for entry in source.get("industry_coverage") or []],
            "supported_frameworks": [str(entry) for entry in source.get("supported_frameworks") or []],
            "collection_method": str(source.get("collection_method") or "rss"),
            "last_successful_sync": source.get("last_successful_sync"),
        }
        sources.append(normalized)

    existing_names = {str(source.get("name") or "").lower() for source in sources}
    for virtual_source in _virtual_topic_sources():
        if str(virtual_source.get("name") or "").lower() in existing_names:
            continue
        sources.append(virtual_source)

    return sources


def source_registry_health(registry: List[Dict[str, Any]]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    healthy = 0
    degraded = 0

    for source in registry:
        if source.get("last_successful_sync"):
            healthy += 1
        else:
            degraded += 1

    return {
        "timestamp": now,
        "sourceCount": len(registry),
        "healthySources": healthy,
        "degradedSources": degraded,
        "tiers": sorted({str(item.get("tier") or "TIER 0") for item in registry}),
    }
