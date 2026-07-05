import json
import time
from pathlib import Path
from typing import Any, Dict, List

from backend.collectors import __doc__ as collector_doc
from backend.database.db import SessionLocal
from backend.exceptions import CollectorError
from backend.logging_config import LOGGER
from backend.services.article_service import initialize_storage, save_article

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def sample_articles() -> List[Dict[str, Any]]:
    """Return a curated set of sample intelligence items for the MVP collector."""
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
        {
            "title": "AI agents expand into privileged workflow automation",
            "summary": "Security teams are evaluating agentic AI systems for privileged operations.",
            "source": "Vendor News",
            "category": "AI Agents",
            "severity": "Medium",
            "url": "https://example.com/ai-agents-privileged",
            "published_at": "2026-07-04T10:15:00",
            "tags": ["ai", "automation"],
        },
        {
            "title": "Vendor advisory: critical patch released for remote access gateway",
            "summary": "A vendor issued a patch advisory for a remote access appliance with active exploitability.",
            "source": "Vendor Advisory",
            "category": "Vendor",
            "severity": "High",
            "url": "https://example.com/vendor-patch-advisory",
            "published_at": "2026-07-04T10:45:00",
            "tags": ["vendor", "patch"],
        },
        {
            "title": "EU proposes new incident reporting obligations for critical infrastructure",
            "summary": "Regulators are proposing tighter reporting obligations for significant incidents.",
            "source": "EU",
            "category": "Regulation",
            "severity": "Medium",
            "url": "https://example.com/eu-regulation-reporting",
            "published_at": "2026-07-04T11:00:00",
            "tags": ["regulation", "reporting"],
        },
        {
            "title": "Research paper examines resilient machine identity controls in cloud environments",
            "summary": "A new research paper reviews machine identity lifecycle controls and certificate hygiene.",
            "source": "Research",
            "category": "Research",
            "severity": "Low",
            "url": "https://example.com/research-machine-identity",
            "published_at": "2026-07-04T11:15:00",
            "tags": ["research", "machine-identity"],
        },
        {
            "title": "Threat actor uses stolen OAuth tokens to access cloud workloads",
            "summary": "Recent intrusion activity shows attackers abusing OAuth tokens to pivot across services.",
            "source": "Threat Intel",
            "category": "Threat",
            "severity": "High",
            "url": "https://example.com/threat-oauth-tokens",
            "published_at": "2026-07-04T11:30:00",
            "tags": ["threat", "oauth"],
        },
        {
            "title": "Identity news: passwordless phishing resistance improves MFA adoption",
            "summary": "Security teams are observing better engagement with passwordless authentication controls.",
            "source": "Identity News",
            "category": "Identity",
            "severity": "Medium",
            "url": "https://example.com/identity-passwordless",
            "published_at": "2026-07-04T11:45:00",
            "tags": ["identity", "mfa"],
        },
        {
            "title": "Machine identity: certificate lifecycle automation reduces outages",
            "summary": "Automation around certificate rotation improves resilience and lowers operational risk.",
            "source": "Machine Identity",
            "category": "Machine Identity",
            "severity": "Medium",
            "url": "https://example.com/machine-identity-automation",
            "published_at": "2026-07-04T12:00:00",
            "tags": ["machine-identity", "certificates"],
        },
        {
            "title": "AI agents raise new concerns around autonomous privilege escalation",
            "summary": "Researchers warn that AI agents can increase risk when given elevated permissions.",
            "source": "AI Research",
            "category": "AI Agents",
            "severity": "Medium",
            "url": "https://example.com/ai-agents-privilege-escalation",
            "published_at": "2026-07-04T12:15:00",
            "tags": ["ai", "privilege"],
        },
    ]


def collect_articles(max_retries: int = 3) -> List[Dict[str, Any]]:
    """Collect and persist intelligence articles with retries and logging."""
    initialize_storage()
    db = SessionLocal()
    try:
        saved: List[Dict[str, Any]] = []
        for attempt in range(1, max_retries + 1):
            try:
                articles = sample_articles()
                for article in articles:
                    saved_article = save_article(db, article)
                    saved.append(
                        {
                            "id": saved_article.id,
                            "title": saved_article.title,
                            "category": saved_article.category,
                            "source": saved_article.source,
                        }
                    )
                LOGGER.info("Daily collector completed successfully")
                return saved
            except Exception as exc:  # pragma: no cover - defensive fallback
                LOGGER.exception("Collector attempt %s failed: %s", attempt, exc)
                if attempt == max_retries:
                    raise CollectorError("Daily collection failed after retries") from exc
                time.sleep(2)
        raise CollectorError("Daily collection did not complete")
    finally:
        db.close()


if __name__ == "__main__":
    collected = collect_articles()
    output_file = DATA_DIR / "daily_collection.json"
    output_file.write_text(json.dumps(collected, indent=2))
    print(f"Collected {len(collected)} articles")
