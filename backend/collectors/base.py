from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from backend.logging_config import LOGGER


class CollectorError(Exception):
    """Raised when a collector cannot complete its operation."""


class BaseCollector:
    """Base implementation for all intelligence collectors."""

    def __init__(self, name: str, source_name: str, category: str, endpoint: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.source_name = source_name
        self.category = category
        self.endpoint = endpoint
        self.metadata = metadata or {}

    def fetch(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def parse(self, payload: Any) -> List[Dict[str, Any]]:
        raise NotImplementedError

    CATEGORY_KEYWORDS = {
        "Regulation": [
            "regulation",
            "compliance",
            "governance",
            "framework",
            "gdpr",
            "hipaa",
            "pci",
            "iso 27001",
            "nist",
            "cisa",
            "dora",
        ],
        "Research": [
            "research",
            "study",
            "whitepaper",
            "report",
            "analysis",
            "arxiv",
            "findings",
        ],
        "Vulnerability": [
            "cve-",
            "vulnerability",
            "zero-day",
            "0-day",
            "rce",
            "deserialization",
            "privilege escalation",
            "patch",
            "advisory",
            "exploit",
        ],
        "Threat": [
            "threat",
            "ransomware",
            "malware",
            "trojan",
            "botnet",
            "phishing",
            "attack",
            "breach",
            "stealer",
        ],
        "Identity": [
            "identity",
            "iam",
            "entra",
            "okta",
            "sso",
            "mfa",
            "access management",
            "authentication",
            "authorization",
            "credential",
        ],
    }

    SUBCATEGORY_KEYWORDS = {
        "CPS 230": ["cps 230", "operational resilience"],
        "CPS 234": ["cps 234", "information security"],
        "Essential Eight": ["essential eight", "asd e8"],
        "Cyber Advisories": ["advisory", "urgent", "alert"],
        "Privacy Guidance": ["privacy", "oaic"],
        "Financial Stability": ["financial stability", "reserve bank", "rba", "cfr"],
        "Identity Governance": ["identity governance", "iga", "joiner", "mover", "leaver"],
        "PAM": ["pam", "privileged access", "least privilege"],
        "CIEM": ["ciem", "cloud entitlement", "permission"],
        "ITDR": ["itdr", "identity threat detection", "identity attack"],
        "Machine Identity": ["machine identity", "certificate", "workload identity", "non-human"],
        "OAuth/OIDC": ["oauth", "oidc", "openid", "token"],
        "Passkeys/FIDO": ["passkey", "fido", "webauthn"],
        "Agentic AI": ["agentic", "autonomous agent", "ai agent", "copilot"],
        "Prompt Injection": ["prompt injection", "jailbreak"],
        "LLM Security": ["llm security", "model security", "inference"],
        "Threat Intel": ["threat intelligence", "campaign", "ioc", "ttp", "mitre"],
    }

    INDUSTRY_KEYWORDS = {
        "Financial Services": ["bank", "financial", "apra", "asic", "payments", "fintech"],
        "Government": ["government", "department", "agency", "public sector"],
        "Healthcare": ["health", "hospital", "clinical"],
        "Critical Infrastructure": ["critical infrastructure", "energy", "utilities", "transport"],
        "Technology": ["cloud", "saas", "software", "it"],
    }

    IAM_KEYWORDS = {
        "Identity Governance": ["identity governance", "iga"],
        "Authentication": ["authentication", "mfa", "passkey", "fido"],
        "Authorization": ["authorization", "policy", "rbac", "abac"],
        "Privileged Access": ["pam", "privileged", "admin"],
        "Machine Identity": ["machine identity", "certificate", "workload identity", "non-human"],
        "Federation": ["oauth", "oidc", "saml", "federation"],
    }

    CONTROL_MAPPINGS = {
        "NIST": ["nist", "csf", "800-53", "zero trust"],
        "MITRE ATT&CK": ["mitre", "attack", "ttp"],
        "CIS Controls": ["cis controls", "cis benchmark"],
        "ISO 27001": ["iso", "27001", "27002"],
        "APRA CPS 230": ["cps 230", "operational resilience"],
        "APRA CPS 234": ["cps 234", "information security"],
        "ASD Essential Eight": ["essential eight", "asd"],
    }

    def _classify_category(self, item: Dict[str, Any]) -> str:
        title = str(item.get("title") or "")
        summary = str(item.get("summary") or item.get("description") or "")
        source = str(item.get("source") or self.source_name or "")
        tag_text = " ".join(str(tag) for tag in item.get("tags", []) if isinstance(tag, str))
        haystack = f"{title} {summary} {source} {tag_text}".lower()
        haystack = re.sub(r"\s+", " ", haystack)

        if not haystack.strip():
            return self.category

        best_category = self.category
        best_score = 0
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in haystack)
            if score > best_score:
                best_score = score
                best_category = category

        if best_score == 0:
            return self.category

        # Preserve explicit research/regulation sources when keyword signals tie.
        if self.category in {"Research", "Regulation"} and best_score <= 1:
            return self.category

        return best_category

    def _classify_subcategory(self, item: Dict[str, Any]) -> str:
        preferred = str(self.metadata.get("source_subcategory") or "").strip()
        if preferred:
            return preferred
        title = str(item.get("title") or "").lower()
        summary = str(item.get("summary") or item.get("description") or "").lower()
        haystack = f"{title} {summary}"
        for subcategory, keywords in self.SUBCATEGORY_KEYWORDS.items():
            if any(keyword in haystack for keyword in keywords):
                return subcategory
        return "General"

    def _match_keywords(self, haystack: str, mapping: Dict[str, List[str]]) -> List[str]:
        matched = [name for name, keywords in mapping.items() if any(keyword in haystack for keyword in keywords)]
        return matched or ["General"]

    def _executive_summary(self, title: str, summary: str, category: str) -> str:
        if summary:
            return f"{category}: {summary[:280].strip()}"
        return f"{category}: {title[:280].strip()}"

    def _recommended_actions(self, category: str, severity: str) -> List[str]:
        actions = [
            "Assess enterprise exposure and affected business processes.",
            "Update risk register and assign accountable owner.",
            "Track remediation completion against policy deadlines.",
        ]
        if category == "Regulation":
            actions.insert(0, "Validate control alignment and compliance obligations with legal/risk teams.")
        if category == "Identity":
            actions.insert(0, "Review IAM control effectiveness for privileged and non-human identities.")
        if severity in {"high", "critical"}:
            actions.insert(0, "Initiate rapid response review and executive escalation.")
        return actions[:4]

    def _board_impact(self, category: str, severity: str) -> str:
        if severity == "critical":
            return "Material risk to operational continuity and potential regulatory exposure; board oversight recommended."
        if category == "Regulation":
            return "Potential compliance and supervisory impact requiring governance and assurance updates."
        if category == "Identity":
            return "Identity control weakness could increase enterprise-wide breach and fraud exposure."
        return "May impact risk appetite, resilience objectives, and technology investment priorities."

    def _ciso_actions(self, category: str) -> List[str]:
        base = [
            "Confirm detection, response, and reporting ownership.",
            "Validate compensating controls and policy exceptions.",
            "Publish an executive status update with next milestones.",
        ]
        if category == "AI Security":
            base.insert(0, "Verify AI use-case guardrails, model access controls, and prompt safety testing.")
        if category == "Threat":
            base.insert(0, "Hunt for related indicators and validate containment playbooks.")
        return base[:4]

    def _severity_rank(self, severity: str) -> int:
        ranks = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return ranks.get(severity, 2)

    def _rank(self, category: str, severity: str, source_group: str) -> Dict[str, float]:
        credibility = float(self.metadata.get("credibility_weight", 0.8))
        executive_relevance = 0.7
        regulatory_importance = 0.4
        business_impact = min(1.0, 0.25 * self._severity_rank(severity))

        if category in {"Regulation", "Identity", "Threat"}:
            executive_relevance += 0.15
        if category == "Regulation" or source_group in {"Australian Regulators", "Global Standards"}:
            regulatory_importance = 1.0
        elif category in {"Threat", "AI Security"}:
            regulatory_importance = 0.6

        overall = round((credibility * 0.35) + (executive_relevance * 0.25) + (business_impact * 0.25) + (regulatory_importance * 0.15), 3)
        return {
            "credibility": round(credibility, 3),
            "executive_relevance": round(executive_relevance, 3),
            "business_impact": round(business_impact, 3),
            "regulatory_importance": round(regulatory_importance, 3),
            "overall": overall,
        }

    def normalize(self, item: Dict[str, Any]) -> Dict[str, Any]:
        published_at = item.get("published_at") or item.get("publishedDate") or item.get("pubDate")
        raw_tags = item.get("tags")
        tags = raw_tags if isinstance(raw_tags, list) else []
        severity = str(item.get("severity") or "medium").strip().lower() or "medium"
        category = str(item.get("category") or "").strip() or self._classify_category(item)
        subcategory = str(item.get("subcategory") or "").strip() or self._classify_subcategory(item)
        url = str(item.get("url") or item.get("link") or "").strip()
        source_group = str(self.metadata.get("source_group") or "General Sources")
        monitors = self.metadata.get("monitors")
        if not isinstance(monitors, list):
            monitors = []

        haystack = f"{str(item.get('title') or '')} {str(item.get('summary') or item.get('description') or '')}".lower()
        affected_industries = item.get("affected_industries")
        if not isinstance(affected_industries, list):
            affected_industries = self._match_keywords(haystack, self.INDUSTRY_KEYWORDS)

        affected_iam_domains = item.get("affected_iam_domains")
        if not isinstance(affected_iam_domains, list):
            affected_iam_domains = self._match_keywords(haystack, self.IAM_KEYWORDS)

        control_mappings = item.get("control_mappings")
        if not isinstance(control_mappings, list):
            control_mappings = self._match_keywords(haystack, self.CONTROL_MAPPINGS)

        executive_summary = str(item.get("executive_summary") or "").strip() or self._executive_summary(str(item.get("title") or ""), str(item.get("summary") or item.get("description") or ""), category)
        recommended_actions = item.get("recommended_actions")
        if not isinstance(recommended_actions, list):
            recommended_actions = self._recommended_actions(category, severity)
        board_impact = str(item.get("board_impact") or "").strip() or self._board_impact(category, severity)
        ciso_action_items = item.get("ciso_action_items")
        if not isinstance(ciso_action_items, list):
            ciso_action_items = self._ciso_actions(category)
        rankings = item.get("rankings")
        if not isinstance(rankings, dict):
            rankings = self._rank(category, severity, source_group)

        normalized = {
            "title": str(item.get("title") or "").strip(),
            "author": str(item.get("author") or item.get("authors") or "Unknown").strip(),
            "published_at": self._normalize_datetime(published_at),
            "published_date": self._normalize_datetime(published_at),
            "published": self._normalize_datetime(published_at),
            "url": url,
            "details_url": url,
            "summary": str(item.get("summary") or item.get("description") or "").strip(),
            "category": category,
            "subcategory": subcategory,
            "source": self.source_name,
            "vendor": str(item.get("vendor") or self.source_name).strip(),
            "source_group": source_group,
            "monitors": [str(entry) for entry in monitors if str(entry).strip()],
            "official_url": str(self.metadata.get("official_url") or "").strip(),
            "severity": severity,
            "tags": [str(tag).strip() for tag in tags if str(tag).strip()],
            "executive_summary": executive_summary,
            "affected_industries": [str(entry) for entry in affected_industries if str(entry).strip()],
            "affected_iam_domains": [str(entry) for entry in affected_iam_domains if str(entry).strip()],
            "control_mappings": [str(entry) for entry in control_mappings if str(entry).strip()],
            "recommended_actions": [str(entry) for entry in recommended_actions if str(entry).strip()],
            "board_impact": board_impact,
            "ciso_action_items": [str(entry) for entry in ciso_action_items if str(entry).strip()],
            "rankings": rankings,
        }
        return normalized

    def _normalize_datetime(self, value: Any) -> Optional[str]:
        if not value:
            return None
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).isoformat()
        if isinstance(value, str):
            text = value.strip()
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            try:
                parsed = datetime.fromisoformat(text)
            except ValueError:
                try:
                    parsed = datetime.strptime(text, "%a, %d %b %Y %H:%M:%S %Z")
                except ValueError:
                    return text
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat()
        return str(value)

    def _is_today(self, item: Dict[str, Any]) -> bool:
        published_at = item.get("published_at") or item.get("published_date")
        if not published_at:
            return True
        if isinstance(published_at, str):
            try:
                parsed = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            except ValueError:
                return True
            return parsed.astimezone(timezone.utc).date() == datetime.now(timezone.utc).date()
        return True

    def collect(self, max_retries: int = 3) -> List[Dict[str, Any]]:
        for attempt in range(1, max_retries + 1):
            try:
                payload = self.fetch()
                parsed = self.parse(payload)
                normalized = [self.normalize(item) for item in parsed if item]
                today_items = [item for item in normalized if item.get("title") and self._is_today(item)]
                return today_items
            except Exception as exc:  # pragma: no cover - defensive fallback
                LOGGER.exception("Collector %s failed on attempt %s: %s", self.name, attempt, exc)
                if attempt == max_retries:
                    raise CollectorError(f"Collector {self.name} failed after retries") from exc
                time.sleep(2)
        return []

    def write_json(self, output_path: Path, items: List[Dict[str, Any]]) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(items, indent=2), encoding="utf-8")
