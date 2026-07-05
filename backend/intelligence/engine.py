from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .registry import load_source_registry

_DASHBOARDS = [
    {"id": "executive-summary", "name": "Executive Summary"},
    {"id": "australian-regulatory-intelligence", "name": "Australian Regulatory Intelligence"},
    {"id": "global-cyber-and-standards", "name": "Global Cyber & Standards"},
    {"id": "identity-and-access-management", "name": "Identity & Access Management"},
    {"id": "ai-security-and-agentic-ai", "name": "AI Security & Agentic AI"},
    {"id": "threat-intelligence", "name": "Threat Intelligence"},
    {"id": "financial-services-risk-and-compliance", "name": "Financial Services Risk & Compliance"},
    {"id": "research-and-emerging-technology", "name": "Research & Emerging Technology"},
    {"id": "executive-trends", "name": "Executive Trends"},
    {"id": "critical-alerts", "name": "Critical Alerts"},
]

_FRAMEWORK_KEYWORDS = {
    "NIST CSF": ["nist csf", "csf 2.0", "cybersecurity framework"],
    "NIST SP800": ["sp 800", "800-"],
    "NIST AI RMF": ["ai rmf", "ai risk management framework"],
    "MITRE ATT&CK": ["mitre", "att&ck", "technique", "tactic"],
    "MITRE D3FEND": ["d3fend"],
    "CIS Controls": ["cis controls", "center for internet security"],
    "ISO27001": ["iso 27001"],
    "ISO42001": ["iso 42001"],
    "OWASP Top 10": ["owasp top 10"],
    "OWASP API Top 10": ["owasp api"],
    "Cloud Security Alliance CCM": ["cloud security alliance", "ccm"],
    "SOC2": ["soc 2"],
    "PCI DSS": ["pci dss"],
    "DORA": ["dora", "digital operational resilience act"],
    "NIS2": ["nis2"],
    "APRA CPS230": ["cps 230", "apra cps230"],
    "APRA CPS234": ["cps 234", "apra cps234"],
    "ASD Essential Eight": ["essential eight"],
    "Australian Privacy Act": ["privacy act", "oaic", "notifiable data breach"],
    "Security of Critical Infrastructure Act": ["critical infrastructure", "soci"],
}

_CONTROL_KEYWORDS = {
    "Identity": ["identity", "iam", "iga", "pam", "authentication", "oauth", "oidc", "saml", "scim", "passkey", "fido"],
    "AI": ["ai", "llm", "agentic", "prompt injection", "model", "autonomous"],
    "Cloud": ["cloud", "kubernetes", "container", "ciem", "secrets"],
    "Operational Resilience": ["operational resilience", "business continuity", "resilience"],
    "Third Party Risk": ["third party", "vendor", "outsourcing", "supplier"],
    "Threat Intelligence": ["threat", "malware", "ransomware", "actor", "ioc"],
    "Privacy": ["privacy", "data breach", "pii"],
}

_TACTIC_KEYWORDS = {
    "Initial Access": ["phishing", "initial access"],
    "Execution": ["execution", "powershell"],
    "Persistence": ["persistence"],
    "Privilege Escalation": ["privilege escalation"],
    "Defense Evasion": ["defense evasion"],
    "Credential Access": ["credential"],
    "Discovery": ["discovery"],
    "Lateral Movement": ["lateral movement"],
    "Collection": ["collection"],
    "Exfiltration": ["exfiltration"],
    "Impact": ["impact", "disruption", "ransomware"],
}

_INDUSTRY_KEYWORDS = {
    "Financial Services": ["financial", "bank", "insurance", "payment", "superannuation"],
    "Banking": ["bank", "banking"],
    "Insurance": ["insurance"],
    "Superannuation": ["superannuation"],
    "Payments": ["payment", "card", "pci"],
}


def _safe_text(item: Dict[str, Any]) -> str:
    parts = [
        str(item.get("title") or ""),
        str(item.get("summary") or ""),
        str(item.get("source") or ""),
        " ".join(str(tag) for tag in item.get("tags") or []),
    ]
    return " ".join(parts).lower()


def _detect_list(text: str, dictionary: Dict[str, List[str]]) -> List[str]:
    detected: List[str] = []
    for key, terms in dictionary.items():
        if any(term in text for term in terms):
            detected.append(key)
    return detected


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _extract_cves(text: str) -> List[str]:
    tokens = text.upper().replace(",", " ").replace(";", " ").split()
    return sorted({token for token in tokens if token.startswith("CVE-") and len(token) >= 13})


def _extract_mitre_techniques(text: str) -> List[str]:
    tokens = text.upper().replace(",", " ").split()
    return sorted({token for token in tokens if token.startswith("T") and len(token) in {5, 6}})


def _severity(item: Dict[str, Any], text: str) -> str:
    severity = str(item.get("severity") or "").lower().strip()
    if severity in {"critical", "high", "medium", "low"}:
        return severity
    if any(term in text for term in ["critical", "actively exploited", "major incident"]):
        return "critical"
    if any(term in text for term in ["high", "ransomware", "breach", "zero-day"]):
        return "high"
    if any(term in text for term in ["low", "minor"]):
        return "low"
    return "medium"


def _quality_scores(item: Dict[str, Any], text: str, frameworks: List[str], controls: List[str]) -> Dict[str, float]:
    registry = load_source_registry()
    source = str(item.get("source") or "").lower().strip()
    source_entry = next((entry for entry in registry if str(entry.get("name") or "").lower() == source), None)

    authority = float(source_entry.get("trust_score", 0.75)) if source_entry else 0.75
    executive_relevance = float(source_entry.get("executive_relevance_score", 0.75)) if source_entry else 0.75

    now = datetime.now(timezone.utc)
    published = _parse_datetime(item.get("published") or item.get("published_at"))
    age_hours = max(0.0, (now - published).total_seconds() / 3600.0) if published else 72.0
    timeliness = max(0.2, min(1.0, 1.0 - (age_hours / 240.0)))

    business_impact = 0.65 + (0.08 * min(3, len(frameworks))) + (0.05 * min(3, len(controls)))
    australian_relevance = 1.0 if any(term in text for term in ["apra", "asic", "acsc", "asd", "oaic", "australia"]) else 0.45
    identity_relevance = 1.0 if "Identity" in controls else 0.4
    ai_relevance = 1.0 if "AI" in controls else 0.35
    fs_relevance = 1.0 if any(term in text for term in ["financial", "bank", "insurance", "superannuation", "payments"]) else 0.5
    threat_value = 1.0 if any(term in text for term in ["threat", "ioc", "ttp", "actor", "malware"]) else 0.45
    technical_accuracy = 0.9 if _extract_cves(text) or _extract_mitre_techniques(text) else 0.7

    business_impact = min(1.0, business_impact)
    overall = (
        authority * 0.16
        + timeliness * 0.1
        + business_impact * 0.16
        + executive_relevance * 0.16
        + australian_relevance * 0.08
        + identity_relevance * 0.08
        + ai_relevance * 0.08
        + fs_relevance * 0.08
        + threat_value * 0.06
        + technical_accuracy * 0.04
    )

    return {
        "authority": round(authority, 3),
        "timeliness": round(timeliness, 3),
        "businessImpact": round(business_impact, 3),
        "executiveRelevance": round(executive_relevance, 3),
        "australianRelevance": round(australian_relevance, 3),
        "identityRelevance": round(identity_relevance, 3),
        "aiRelevance": round(ai_relevance, 3),
        "financialServicesRelevance": round(fs_relevance, 3),
        "threatIntelligenceValue": round(threat_value, 3),
        "technicalAccuracy": round(technical_accuracy, 3),
        "overall": round(overall, 3),
    }


def _why_this_matters(controls: List[str], industries: List[str], frameworks: List[str], severity: str) -> Dict[str, Any]:
    board_escalation = severity in {"high", "critical"} or "APRA CPS234" in frameworks or "APRA CPS230" in frameworks
    risk_committee = board_escalation or "Financial Services" in industries

    return {
        "ciso": "Control gaps and threat exposure can materially impact cyber resilience and regulatory assurance.",
        "cio": "Technology roadmaps, third-party services, and resilience investments may need reprioritization.",
        "cto": "Architecture and platform controls may require rapid uplift to maintain operational resilience.",
        "iamLeader": "Identity, PAM, machine identity, and access governance controls should be validated for coverage.",
        "affectsFinancialServices": "Financial Services" in industries,
        "affectsSuperannuation": "Superannuation" in industries,
        "affectsBanking": "Banking" in industries,
        "controlsImpacted": controls,
        "policiesToReview": [
            "Information Security Policy",
            "Operational Resilience Policy",
            "Identity and Access Management Policy",
            "Third Party Risk Policy",
        ],
        "standardsToReview": frameworks,
        "escalateToBoard": board_escalation,
        "escalateToRiskCommittee": risk_committee,
        "triggerControlAssessment": severity in {"high", "critical"} or bool(controls),
    }


def enrich_articles(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    enriched: List[Dict[str, Any]] = []

    for item in items:
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        url = str(item.get("url") or item.get("details_url") or "").strip()
        dedupe_key = (title.lower(), url.lower())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        text = _safe_text(item)
        frameworks = _detect_list(text, _FRAMEWORK_KEYWORDS)
        controls = _detect_list(text, _CONTROL_KEYWORDS)
        industries = _detect_list(text, _INDUSTRY_KEYWORDS)
        techniques = _extract_mitre_techniques(text)
        cves = _extract_cves(text)
        severity = _severity(item, text)
        tactics = _detect_list(text, _TACTIC_KEYWORDS)

        if not industries:
            industries = ["Financial Services"]

        quality = _quality_scores(item, text, frameworks, controls)

        enriched.append(
            {
                "title": title,
                "author": item.get("author") or "Unknown",
                "publishedDate": item.get("published") or item.get("published_at"),
                "source": item.get("source") or "Unknown",
                "category": item.get("category") or "General",
                "subcategory": item.get("subcategory") or "General",
                "country": "Australia" if any(term in text for term in ["apra", "asic", "acsc", "asd", "oaic", "australia"]) else "Global",
                "industry": industries,
                "framework": frameworks,
                "technology": controls,
                "threatActor": item.get("threat_actor") or "Unknown",
                "product": item.get("product") or "Unknown",
                "cve": cves,
                "mitreTechnique": techniques,
                "mitreTactic": tactics,
                "summary": item.get("summary") or "",
                "executiveSummary": item.get("executive_summary") or f"{title} has potential strategic risk and control implications.",
                "technicalSummary": item.get("summary") or "Technical details pending deeper triage.",
                "businessImpact": item.get("board_impact") or "Potential impact on compliance posture and operational resilience.",
                "operationalImpact": "Potential changes required to operating controls, runbooks, and assurance cadence.",
                "recommendedActions": item.get("recommended_actions") or [
                    "Assess internal control coverage against this update.",
                    "Assign control owners and remediation dates.",
                    "Escalate high-risk findings to executive governance forums.",
                ],
                "riskRating": severity,
                "confidenceScore": quality["technicalAccuracy"],
                "tags": item.get("tags") or [],
                "frameworkMappings": frameworks,
                "qualityScoring": quality,
                "whyThisMatters": _why_this_matters(controls, industries, frameworks, severity),
                "url": url,
            }
        )

    return sorted(enriched, key=lambda article: float(article.get("qualityScoring", {}).get("overall", 0.0)), reverse=True)


def _dashboard_match(article: Dict[str, Any], dashboard_id: str) -> bool:
    framework = {str(entry) for entry in article.get("framework") or []}
    technology = {str(entry) for entry in article.get("technology") or []}
    text = f"{article.get('title') or ''} {article.get('summary') or ''}".lower()

    if dashboard_id == "executive-summary":
        return True
    if dashboard_id == "australian-regulatory-intelligence":
        return article.get("country") == "Australia"
    if dashboard_id == "global-cyber-and-standards":
        return bool(framework)
    if dashboard_id == "identity-and-access-management":
        return "Identity" in technology or any(term in text for term in ["iam", "identity", "pam", "iga", "oauth", "oidc", "saml", "scim", "passkey"])
    if dashboard_id == "ai-security-and-agentic-ai":
        return "AI" in technology or any(term in text for term in ["ai", "agentic", "llm", "model"])
    if dashboard_id == "threat-intelligence":
        return any(term in text for term in ["threat", "actor", "ransomware", "malware", "exploit", "cve"])
    if dashboard_id == "financial-services-risk-and-compliance":
        return any(term in text for term in ["financial", "bank", "insurance", "superannuation", "apra", "asic", "payments"]) or "Financial Services" in (article.get("industry") or [])
    if dashboard_id == "research-and-emerging-technology":
        return any(term in text for term in ["research", "arxiv", "conference", "deepmind", "anthropic", "openai"])
    if dashboard_id == "executive-trends":
        return True
    if dashboard_id == "critical-alerts":
        return str(article.get("riskRating") or "").lower() in {"high", "critical"}
    return False


def build_dashboard_bundle(enriched: List[Dict[str, Any]]) -> Dict[str, Any]:
    dashboards: List[Dict[str, Any]] = []

    for definition in _DASHBOARDS:
        dashboard_items = [article for article in enriched if _dashboard_match(article, definition["id"])][:200]
        dashboards.append(
            {
                "id": definition["id"],
                "name": definition["name"],
                "count": len(dashboard_items),
                "widgets": {
                    "itemCount": len(dashboard_items),
                    "highRiskCount": sum(1 for article in dashboard_items if str(article.get("riskRating") or "").lower() in {"high", "critical"}),
                    "frameworkCount": len({framework for article in dashboard_items for framework in article.get("framework") or []}),
                    "controlCount": len({control for article in dashboard_items for control in article.get("technology") or []}),
                },
                "items": dashboard_items,
            }
        )

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "dashboards": dashboards,
    }


def get_widget_payload(enriched: List[Dict[str, Any]], dashboard_id: str, widget_id: str) -> Dict[str, Any]:
    dashboard_items = [article for article in enriched if _dashboard_match(article, dashboard_id)]

    if widget_id == "topStories":
        payload = dashboard_items[:10]
    elif widget_id == "frameworkBreakdown":
        counter = Counter(framework for article in dashboard_items for framework in article.get("framework") or [])
        payload = [{"name": name, "count": count} for name, count in counter.most_common(20)]
    elif widget_id == "riskBreakdown":
        counter = Counter(str(article.get("riskRating") or "medium").lower() for article in dashboard_items)
        payload = [{"name": name, "count": count} for name, count in counter.most_common()]
    else:
        payload = dashboard_items

    return {
        "dashboardId": dashboard_id,
        "widgetId": widget_id,
        "count": len(payload) if isinstance(payload, list) else 1,
        "data": payload,
    }


def build_daily_brief(enriched: List[Dict[str, Any]]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    week_start = now - timedelta(days=7)

    def _is_since(article: Dict[str, Any], cutoff: datetime) -> bool:
        published = _parse_datetime(article.get("publishedDate"))
        if not published:
            return False
        return published >= cutoff

    australian = [article for article in enriched if article.get("country") == "Australia"]
    global_updates = [article for article in enriched if article.get("country") != "Australia"]
    nist = [article for article in enriched if "NIST CSF" in (article.get("framework") or []) or "NIST SP800" in (article.get("framework") or [])]
    mitre = [article for article in enriched if "MITRE ATT&CK" in (article.get("framework") or [])]
    identity = [article for article in enriched if "Identity" in (article.get("technology") or [])]
    ai = [article for article in enriched if "AI" in (article.get("technology") or [])]
    threat = [article for article in enriched if any(term in (article.get("summary") or "").lower() for term in ["threat", "ransomware", "exploit", "malware"])]
    financial = [article for article in enriched if "Financial Services" in (article.get("industry") or [])]
    research = [article for article in enriched if "research" in (article.get("summary") or "").lower()]

    changed_yesterday = [article for article in enriched if _is_since(article, yesterday)]
    changed_week = [article for article in enriched if _is_since(article, week_start)]
    urgent = [article for article in enriched if str(article.get("riskRating") or "").lower() in {"critical", "high"}][:10]

    return {
        "generatedAt": now.isoformat(),
        "top10Stories": enriched[:10],
        "australianRegulatoryChanges": australian[:10],
        "globalRegulatoryChanges": global_updates[:10],
        "nistUpdates": nist[:10],
        "mitreUpdates": mitre[:10],
        "identitySecurityNews": identity[:10],
        "aiSecurityNews": ai[:10],
        "threatIntelligence": threat[:10],
        "financialServicesUpdates": financial[:10],
        "researchHighlights": research[:10],
        "emergingRisks": urgent,
        "boardBrief": [
            "Monitor high-risk cyber and regulatory shifts affecting critical business services.",
            "Confirm management action plans for APRA, ASIC, and global framework updates.",
            "Track unresolved high-severity findings and required investment decisions.",
        ],
        "executiveActions": [
            "Run rapid control impact assessment for all high-severity intelligence items.",
            "Confirm ownership and due dates for policy and standards updates.",
            "Escalate unresolved resilience risks to the board and risk committee.",
        ],
        "whatChangedSinceYesterday": changed_yesterday,
        "whatChangedThisWeek": changed_week,
        "whatRequiresImmediateAttention": urgent,
    }


def build_reports(enriched: List[Dict[str, Any]], report_type: str) -> Dict[str, Any]:
    report = {
        "reportType": report_type,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "totalArticles": len(enriched),
            "highRisk": sum(1 for article in enriched if str(article.get("riskRating") or "").lower() in {"high", "critical"}),
            "financialServicesRelevant": sum(1 for article in enriched if "Financial Services" in (article.get("industry") or [])),
            "identityRelevant": sum(1 for article in enriched if "Identity" in (article.get("technology") or [])),
            "aiRelevant": sum(1 for article in enriched if "AI" in (article.get("technology") or [])),
        },
        "topItems": enriched[:20],
        "boardRecommendations": [
            "Approve prioritized remediation for high-risk control gaps.",
            "Increase oversight cadence for regulatory and AI governance updates.",
            "Fund resilience improvements for critical business services.",
        ],
        "exportFormats": ["json", "pdf", "pptx", "email", "teams"],
    }
    return report


def search_articles(
    enriched: List[Dict[str, Any]],
    framework: Optional[str] = None,
    control: Optional[str] = None,
    country: Optional[str] = None,
    industry: Optional[str] = None,
    threat_actor: Optional[str] = None,
    mitre_technique: Optional[str] = None,
    cve: Optional[str] = None,
    technology: Optional[str] = None,
    vendor: Optional[str] = None,
    regulator: Optional[str] = None,
    identity_topic: Optional[str] = None,
    cloud_topic: Optional[str] = None,
    ai_topic: Optional[str] = None,
    risk_level: Optional[str] = None,
) -> List[Dict[str, Any]]:
    def _contains(values: List[str], needle: str) -> bool:
        needle_lower = needle.lower()
        return any(needle_lower in str(value).lower() for value in values)

    filtered = enriched

    if framework:
        filtered = [article for article in filtered if _contains(article.get("framework") or [], framework)]
    if control:
        filtered = [article for article in filtered if _contains(article.get("technology") or [], control)]
    if country:
        filtered = [article for article in filtered if str(article.get("country") or "").lower() == country.lower()]
    if industry:
        filtered = [article for article in filtered if _contains(article.get("industry") or [], industry)]
    if threat_actor:
        filtered = [article for article in filtered if threat_actor.lower() in str(article.get("threatActor") or "").lower()]
    if mitre_technique:
        filtered = [article for article in filtered if _contains(article.get("mitreTechnique") or [], mitre_technique)]
    if cve:
        filtered = [article for article in filtered if _contains(article.get("cve") or [], cve)]
    if technology:
        filtered = [article for article in filtered if _contains(article.get("technology") or [], technology)]
    if vendor:
        filtered = [article for article in filtered if vendor.lower() in str(article.get("source") or "").lower()]
    if regulator:
        filtered = [article for article in filtered if regulator.lower() in str(article.get("source") or "").lower()]
    if identity_topic:
        filtered = [article for article in filtered if identity_topic.lower() in f"{article.get('summary') or ''} {article.get('title') or ''}".lower()]
    if cloud_topic:
        filtered = [article for article in filtered if cloud_topic.lower() in f"{article.get('summary') or ''} {article.get('title') or ''}".lower()]
    if ai_topic:
        filtered = [article for article in filtered if ai_topic.lower() in f"{article.get('summary') or ''} {article.get('title') or ''}".lower()]
    if risk_level:
        filtered = [article for article in filtered if str(article.get("riskRating") or "").lower() == risk_level.lower()]

    return filtered
