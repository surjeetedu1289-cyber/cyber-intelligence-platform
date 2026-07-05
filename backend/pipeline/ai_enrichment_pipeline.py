from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.ai.claude_client import ClaudeClient, ClaudeClientError
from backend.config import DATA_DIR
from backend.logging_config import LOGGER


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    prompt_file: str
    categories: List[str]


AGENT_DEFINITIONS: List[AgentDefinition] = [
    AgentDefinition("Cybersecurity", "cyber.md", ["Threat", "General", "Vendor"]),
    AgentDefinition("IAM", "iam.md", ["Identity"]),
    AgentDefinition("Agentic AI", "agentic_ai.md", ["AI Agents"]),
    AgentDefinition("Machine Identity", "machine_identity.md", ["Machine Identity"]),
    AgentDefinition("Regulations", "regulations.md", ["Regulation"]),
    AgentDefinition("Vendor Intelligence", "vendors.md", ["Vendor"]),
    AgentDefinition("Research Papers", "research.md", ["Research"]),
    AgentDefinition("Threat Intelligence", "threat_intelligence.md", ["Threat"]),
]

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "ai" / "prompts"


def _ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _normalize_category(article: Dict[str, Any]) -> str:
    title = str(article.get("title") or "").lower()
    summary = str(article.get("summary") or "").lower()
    category = str(article.get("category") or "General").strip()
    if "machine identity" in title or "machine identity" in summary or category == "Machine Identity":
        return "Machine Identity"
    if "identity" in title or "identity" in summary or category in {"Identity", "Identity Governance"}:
        return "Identity"
    if "agent" in title or "ai" in title or category in {"AI Agents", "Agentic AI"}:
        return "AI Agents"
    if "regulation" in title or "nist" in title or "cisa" in title or category == "Regulation":
        return "Regulation"
    if "threat" in title or "exploit" in title or "ransomware" in title or category == "Threat":
        return "Threat"
    if "vendor" in title or "patch" in title or "advisory" in summary or category == "Vendor":
        return "Vendor"
    if "research" in title or "paper" in title or category == "Research":
        return "Research"
    return "General"


def _load_articles(input_dir: Path) -> List[Dict[str, Any]]:
    combined_path = input_dir / "combined.json"
    articles: List[Dict[str, Any]] = []

    if combined_path.exists():
        try:
            payload = json.loads(combined_path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                articles.extend(payload)
        except json.JSONDecodeError as exc:
            LOGGER.warning("Failed to parse %s: %s", combined_path, exc)

    if not articles:
        for file_path in sorted(input_dir.glob("*.json")):
            if re.match(r"\d{4}-\d{2}-\d{2}\.json$", file_path.name):
                continue
            if file_path.name in {"collection_summary.json", "ai_research.json"}:
                continue
            try:
                payload = json.loads(file_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                LOGGER.warning("Failed to parse %s: %s", file_path, exc)
                continue
            if isinstance(payload, list):
                for item in payload:
                    if isinstance(item, dict):
                        articles.append(item)

    deduped: List[Dict[str, Any]] = []
    seen = set()
    for article in articles:
        key = (
            str(article.get("title") or "").strip().lower(),
            str(article.get("url") or "").strip(),
        )
        if key in seen or not key[0]:
            continue
        seen.add(key)
        normalized = dict(article)
        normalized["category"] = _normalize_category(article)
        deduped.append(normalized)

    return deduped


def _load_prompt(prompt_file: str) -> str:
    path = PROMPTS_DIR / prompt_file
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def _prepare_agent_prompt(agent_name: str, articles: List[Dict[str, Any]]) -> str:
    schema_hint = {
        "executive_summary": "string",
        "business_impact": "string",
        "iam_impact": "string",
        "risk_level": "critical|high|medium|low",
        "recommended_actions": ["string"],
        "confidence_score": 0.0,
        "tags": ["string"],
    }
    return (
        "Analyze the article set and return only valid JSON with no markdown.\n"
        f"JSON schema: {json.dumps(schema_hint)}\n"
        "Use evidence from the provided articles and keep the response concise.\n"
        f"Agent: {agent_name}\n"
        f"Articles: {json.dumps(articles[:25], ensure_ascii=False)}"
    )


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
        candidate = re.sub(r"\s*```$", "", candidate)

    try:
        payload = json.loads(candidate)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start != -1 and end != -1 and end > start:
        fragment = candidate[start : end + 1]
        try:
            payload = json.loads(fragment)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            return None
    return None


def _fallback_enrichment(agent_name: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    top_titles = [str(item.get("title") or "") for item in articles[:3] if item.get("title")]
    risk_level = "medium"
    if any("critical" in str(item.get("severity") or "").lower() for item in articles):
        risk_level = "high"
    if any("ransomware" in str(item.get("title") or "").lower() for item in articles):
        risk_level = "critical"

    return {
        "executive_summary": f"{agent_name} analysis generated from {len(articles)} articles.",
        "business_impact": "Potential operational and governance impact should be reviewed by leadership.",
        "iam_impact": "Validate authentication, authorization, and privileged access controls for affected systems.",
        "risk_level": risk_level,
        "recommended_actions": [
            "Validate exposure in your environment.",
            "Prioritize remediation for high-risk findings.",
            "Track actions in the risk register.",
        ],
        "confidence_score": 0.55,
        "tags": [agent_name.lower().replace(" ", "-"), "fallback"],
        "evidence_titles": top_titles,
    }


def _normalize_output(agent_name: str, output: Dict[str, Any], article_count: int) -> Dict[str, Any]:
    confidence_raw = output.get("confidence_score", output.get("confidence", 0.5))
    try:
        confidence_score = float(confidence_raw)
    except (TypeError, ValueError):
        confidence_score = 0.5
    confidence_score = max(0.0, min(confidence_score, 1.0))

    risk_level = str(output.get("risk_level") or "medium").lower()
    if risk_level not in {"critical", "high", "medium", "low"}:
        risk_level = "medium"

    actions = output.get("recommended_actions")
    if not isinstance(actions, list):
        actions = ["Review findings and define remediation priorities."]

    tags = output.get("tags")
    if not isinstance(tags, list):
        tags = [agent_name.lower().replace(" ", "-")]

    return {
        "agent": agent_name,
        "article_count": article_count,
        "executive_summary": str(output.get("executive_summary") or output.get("summary") or "No summary available."),
        "business_impact": str(output.get("business_impact") or "Business impact requires review."),
        "iam_impact": str(output.get("iam_impact") or "IAM impact requires review."),
        "risk_level": risk_level,
        "recommended_actions": [str(item) for item in actions if str(item).strip()],
        "confidence_score": confidence_score,
        "tags": [str(item) for item in tags if str(item).strip()],
    }


def _agent_articles(all_articles: List[Dict[str, Any]], categories: List[str]) -> List[Dict[str, Any]]:
    selected = [item for item in all_articles if item.get("category") in categories]
    if selected:
        return selected
    return all_articles[:20]


def _run_agent(client: Optional[ClaudeClient], definition: AgentDefinition, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    selected_articles = _agent_articles(articles, definition.categories)
    if not selected_articles:
        return _normalize_output(definition.name, _fallback_enrichment(definition.name, []), 0)

    if client is None:
        LOGGER.warning("Claude client unavailable, using fallback for %s", definition.name)
        fallback = _fallback_enrichment(definition.name, selected_articles)
        return _normalize_output(definition.name, fallback, len(selected_articles))

    prompt = _prepare_agent_prompt(definition.name, selected_articles)
    system_prompt = _load_prompt(definition.prompt_file)
    try:
        response_text = client.send_prompt(prompt, system_prompt=system_prompt)
        parsed = _extract_json(response_text)
        if not parsed:
            LOGGER.warning("Non-JSON Claude response for %s, using fallback", definition.name)
            parsed = _fallback_enrichment(definition.name, selected_articles)
    except Exception as exc:  # pragma: no cover - network dependent
        LOGGER.warning("Claude enrichment failed for %s: %s", definition.name, exc)
        parsed = _fallback_enrichment(definition.name, selected_articles)

    return _normalize_output(definition.name, parsed, len(selected_articles))


def run_ai_enrichment_pipeline(
    input_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    run_date: Optional[date] = None,
) -> Dict[str, Any]:
    """Read collected articles, run specialized AI enrichments, and write a dated bundle."""
    source_dir = input_dir or (DATA_DIR / "daily")
    destination_dir = output_dir or (DATA_DIR / "daily")
    _ensure_output_dir(destination_dir)

    articles = _load_articles(source_dir)
    today = run_date or datetime.now(timezone.utc).date()

    try:
        client = ClaudeClient()
    except (ClaudeClientError, Exception) as exc:
        LOGGER.warning("Claude client unavailable for enrichment: %s", exc)
        client = None

    enrichments = [_run_agent(client, definition, articles) for definition in AGENT_DEFINITIONS]
    payload = {
        "date": today.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "article_count": len(articles),
        "agents": enrichments,
    }

    output_file = destination_dir / f"{today.isoformat()}.json"
    output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    LOGGER.info("AI enrichment report generated: %s", output_file)
    return payload


if __name__ == "__main__":
    run_ai_enrichment_pipeline()
