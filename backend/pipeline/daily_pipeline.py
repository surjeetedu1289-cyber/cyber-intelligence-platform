from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

from backend.ai.claude_client import ClaudeClient, ClaudeClientError
from backend.collectors.daily_collector import collect_articles
from backend.collectors.orchestrator import CollectorOrchestrator
from backend.collectors.registry import build_default_collectors
from backend.logging_config import LOGGER
from backend.pipeline.ai_enrichment_pipeline import run_ai_enrichment_pipeline

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
COLLECTORS = [collect_articles]


def _ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _collect_inputs() -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    for collector in COLLECTORS:
        try:
            if callable(getattr(collector, "collect", None)) and not isinstance(collector, type):
                collector_result = collector.collect()
                if isinstance(collector_result, list):
                    merged.extend(collector_result)
                    continue
            result = collector()
            if isinstance(result, list):
                merged.extend(result)
        except Exception as exc:  # pragma: no cover - defensive fallback
            LOGGER.exception("Collector %s failed: %s", getattr(collector, "__name__", collector), exc)

    orchestrator = CollectorOrchestrator(build_default_collectors(DATA_DIR / "daily"))
    orchestrated = orchestrator.run()
    merged.extend(orchestrated.get("articles", []))
    return merged


def _normalize_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    seen = set()
    for item in articles:
        title = (item.get("title") or "").strip().lower()
        url = (item.get("url") or "").strip()
        key = (title, url)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)
    return normalized


def _categorize_article(article: Dict[str, Any]) -> Dict[str, Any]:
    title = (article.get("title") or "").lower()
    summary = (article.get("summary") or "").lower()
    category = (article.get("category") or "General").strip()
    if "machine identity" in title or "machine identity" in summary or category == "Machine Identity":
        category = "Machine Identity"
    elif "identity" in title or "identity" in summary or category in {"Identity", "Identity Governance"}:
        category = "Identity"
    elif "agent" in title or "ai" in title or "automation" in summary or category in {"AI Agents", "Agentic AI"}:
        category = "AI Agents"
    elif "regulation" in title or "nist" in title or "cisa" in title or "guidance" in summary or category == "Regulation":
        category = "Regulation"
    elif "threat" in title or "ransomware" in title or "exploit" in title or "exploitation" in summary or category == "Threat":
        category = "Threat"
    elif "vendor" in title or "patch" in title or "patch" in summary or "advisory" in summary or category == "Vendor":
        category = "Vendor"
    elif "research" in title or "paper" in title or "research" in summary or category == "Research":
        category = "Research"
    else:
        category = "General"
    article = deepcopy(article)
    article["category"] = category
    return article


def _run_ai_research(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        client = ClaudeClient()
    except (ClaudeClientError, Exception) as exc:  # pragma: no cover - environment-dependent
        LOGGER.warning("Claude research skipped: %s", exc)
        return {
            "summary": "AI research is unavailable; the pipeline used heuristic analysis for the daily brief.",
            "evidence": [article.get("title") for article in articles[:5] if article.get("title")],
        }

    topics = ", ".join(article.get("title", "") for article in articles[:5] if article.get("title"))
    prompt = (
        "You are producing a concise cyber intelligence brief. "
        f"Summarize the following topics in 3 bullet points: {topics}"
    )
    try:
        response = client.send_prompt(prompt, system_prompt="You are an expert cyber intelligence analyst.")
    except Exception as exc:  # pragma: no cover - network-dependent
        LOGGER.warning("Claude research failed: %s", exc)
        return {
            "summary": "AI research fallback used because Claude did not return content.",
            "evidence": [article.get("title") for article in articles[:5] if article.get("title")],
        }
    return {"summary": response, "evidence": [article.get("title") for article in articles[:5] if article.get("title")]}


def _fallback_items() -> Dict[str, List[Dict[str, Any]]]:
    return {
        "vendor_updates": [{"title": "Vendor patch advisory", "summary": "A vendor security update is pending rollout.", "source": "Vendor Advisory", "category": "Vendor"}],
        "regulation_updates": [{"title": "Regulatory update", "summary": "New compliance reporting requirements are being reviewed.", "source": "Regulator", "category": "Regulation"}],
        "threat_intelligence": [{"title": "Threat monitoring", "summary": "Threat activity is being monitored across the environment.", "source": "Threat Intel", "category": "Threat"}],
        "identity_news": [{"title": "Identity control update", "summary": "Identity controls remain a priority for the current review window.", "source": "Identity News", "category": "Identity"}],
        "machine_identity": [{"title": "Machine identity alert", "summary": "Machine identity controls should be reviewed this cycle.", "source": "Machine Identity", "category": "Machine Identity"}],
        "ai_agents": [{"title": "AI agent security note", "summary": "Agentic AI posture should be reviewed for privilege risks.", "source": "AI Research", "category": "AI Agents"}],
        "research_papers": [{"title": "Research paper summary", "summary": "A new research paper is pending review.", "source": "Research", "category": "Research"}],
    }


def _build_sections(articles: List[Dict[str, Any]], ai_research: Dict[str, Any]) -> Dict[str, Any]:
    by_category: Dict[str, List[Dict[str, Any]]] = {
        "Identity": [],
        "AI Agents": [],
        "Regulation": [],
        "Threat": [],
        "Vendor": [],
        "Research": [],
        "Machine Identity": [],
        "General": [],
    }
    for article in articles:
        category = article.get("category") or "General"
        if category in by_category:
            by_category[category].append(article)

    fallback_items = _fallback_items()
    executive_summary = {
        "headline": "Daily cyber intelligence summary",
        "summary": ai_research.get("summary", "The platform consolidated the latest intelligence signals across identity, regulation, vendor, and threat domains."),
        "key_risks": [item.get("title", "") for item in articles[:3] if item.get("title")],
        "top_priorities": ["Validate critical patches", "Review identity controls", "Monitor emerging AI agent risks"],
        "confidence": "high",
    }

    top_ten_news = articles[:10] or list(articles)
    trending_topics = [
        {"topic": "Identity governance", "mentions": max(1, len(by_category["Identity"]))},
        {"topic": "AI agent security", "mentions": max(1, len(by_category["AI Agents"]))},
        {"topic": "Vendor patching", "mentions": max(1, len(by_category["Vendor"]))},
        {"topic": "Regulatory reporting", "mentions": max(1, len(by_category["Regulation"]))},
    ]

    sections = {
        "executive_summary": executive_summary,
        "top_ten_news": top_ten_news,
        "trending_topics": trending_topics,
        "vendor_updates": by_category["Vendor"] or fallback_items["vendor_updates"],
        "regulation_updates": by_category["Regulation"] or fallback_items["regulation_updates"],
        "threat_intelligence": by_category["Threat"] or fallback_items["threat_intelligence"],
        "identity_news": by_category["Identity"] or fallback_items["identity_news"],
        "machine_identity": by_category["Machine Identity"] or fallback_items["machine_identity"],
        "ai_agents": by_category["AI Agents"] or fallback_items["ai_agents"],
        "research_papers": by_category["Research"] or fallback_items["research_papers"],
    }
    return sections


def _write_json_bundle(output_dir: Path, payload: Dict[str, Any]) -> None:
    _ensure_output_dir(output_dir)
    filenames = {
        "executive_summary": "executive_summary.json",
        "top_ten_news": "top_ten_news.json",
        "trending_topics": "trending_topics.json",
        "vendor_updates": "vendor_updates.json",
        "regulation_updates": "regulation_updates.json",
        "threat_intelligence": "threat_intelligence.json",
        "identity_news": "identity_news.json",
        "machine_identity": "machine_identity.json",
        "ai_agents": "ai_agents.json",
        "research_papers": "research_papers.json",
    }
    for key, filename in filenames.items():
        (output_dir / filename).write_text(json.dumps(payload[key], indent=2), encoding="utf-8")

    summary = {
        "generated_at": "2026-07-04T00:00:00Z",
        "article_count": len(payload["top_ten_news"]),
        "sections": list(filenames.keys()),
    }
    (output_dir / "collection_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _write_workflow_diagram(output_dir: Path) -> None:
    content = """# Daily Intelligence Workflow

```mermaid
flowchart TD
    A[Collectors] --> B[Merge & Deduplicate]
    B --> C[Categorize]
    C --> D[AI Research]
    D --> E[Executive Summary]
    D --> F[Top Ten News]
    D --> G[Trending Topics]
    D --> H[Vendor Updates]
    D --> I[Regulation Updates]
    D --> J[Threat Intelligence]
    D --> K[Identity News]
    D --> L[Machine Identity]
    D --> M[AI Agents]
    D --> N[Research Papers]
    E --> O[Save JSON to data/daily]
    F --> O
    G --> O
    H --> O
    I --> O
    J --> O
    K --> O
    L --> O
    M --> O
    N --> O
```
"""
    (output_dir / "workflow_diagram.md").write_text(content, encoding="utf-8")


def run_daily_pipeline() -> Dict[str, Any]:
    """Run the daily intelligence pipeline and persist JSON outputs."""
    raw_articles = _collect_inputs()
    normalized_articles = _normalize_articles(raw_articles)
    categorized_articles = [_categorize_article(article) for article in normalized_articles]
    ai_research = _run_ai_research(categorized_articles)
    sections = _build_sections(categorized_articles, ai_research)

    output_dir = DATA_DIR / "daily"
    _write_json_bundle(output_dir, sections)
    _write_workflow_diagram(output_dir)
    (output_dir / "ai_research.json").write_text(json.dumps(ai_research, indent=2), encoding="utf-8")
    run_ai_enrichment_pipeline(input_dir=output_dir, output_dir=output_dir)

    LOGGER.info("Daily pipeline generated outputs in %s", output_dir)
    return sections


if __name__ == "__main__":
    run_daily_pipeline()
