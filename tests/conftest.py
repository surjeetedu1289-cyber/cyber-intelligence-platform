from pathlib import Path

import pytest


@pytest.fixture
def sample_articles():
    return [
        {
            "title": "CISA warns of active exploitation against enterprise VPN appliances",
            "summary": "Security agencies highlighted active exploitation of a widely used VPN platform.",
            "source": "CISA",
            "category": "Threat",
            "severity": "High",
            "url": "https://example.com/cisa-vpn-incident",
            "published_at": "2026-07-04T08:00:00",
            "tags": ["vpn", "exploitation"],
        },
        {
            "title": "New NIST guidance strengthens identity governance controls",
            "summary": "NIST released guidance for improving identity governance and access reviews.",
            "source": "NIST",
            "category": "Identity",
            "severity": "Medium",
            "url": "https://example.com/nist-identity-governance",
            "published_at": "2026-07-04T09:30:00",
            "tags": ["identity", "governance"],
        },
    ]


@pytest.fixture
def prompt_dir():
    return Path("backend/ai/prompts")
