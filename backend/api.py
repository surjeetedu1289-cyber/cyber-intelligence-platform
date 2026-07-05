import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import ALLOWED_ORIGIN_REGEX, ALLOWED_ORIGINS, DATA_DIR
from backend.collectors.source_registry import flattened_sources
from backend.database.db import SessionLocal
from backend.exceptions import ArticleServiceError
from backend.intelligence import (
    build_daily_brief,
    build_dashboard_bundle,
    build_reports,
    enrich_articles,
    get_widget_payload,
    load_source_registry,
    run_ingestion_enrichment_pipeline,
    search_articles,
    source_registry_health,
)
from backend.intelligence.scheduler import DailyPipelineScheduler, scheduler_status
from backend.logging_config import LOGGER
from backend.models import Article, NewsArticle
from backend.services.article_service import save_article

app = FastAPI(
    title="Cyber Intelligence Platform API",
    description="Cyber intelligence APIs for news, trends, vendors, regulations, threats, executive summaries, and research.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_START_TIME = time.time()
_REQUEST_COUNT = 0
_SOURCE_DEFINITION_BY_NAME = {definition.name.lower(): definition for definition in flattened_sources()}
_EXECUTIVE_SCHEDULER = DailyPipelineScheduler(job_runner=run_ingestion_enrichment_pipeline)


@app.on_event("startup")
def _start_background_scheduler() -> None:
    _EXECUTIVE_SCHEDULER.start()


@app.on_event("shutdown")
def _stop_background_scheduler() -> None:
    _EXECUTIVE_SCHEDULER.stop()

_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
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
    "Research": ["research", "study", "whitepaper", "analysis", "arxiv", "findings"],
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
    "Threat": ["threat", "ransomware", "malware", "trojan", "botnet", "phishing", "attack", "breach", "stealer"],
    "Identity": ["identity", "iam", "entra", "okta", "sso", "mfa", "access management", "authentication", "authorization", "credential"],
}

_AUTHORITATIVE_GROUPS = {"Australian Regulators", "Global Standards", "Global Authorities"}
_INDEPENDENT_GROUPS = {
    "Threat Intelligence",
    "Independent Security Journalism",
    "Independent Security News",
    "Identity Security",
    "AI Security",
}
_PROMOTIONAL_TERMS = {
    "webinar",
    "sponsored",
    "product update",
    "product launch",
    "customer story",
    "customer success",
    "book a demo",
    "register now",
    "free trial",
}

_VENDOR_BLOG_SOURCES = {
    "azure",
    "aws security",
    "google cloud security",
    "cyberark",
    "sailpoint",
    "okta",
    "ping identity",
    "saviynt",
    "beyondtrust",
    "microsoft entra",
    "microsoft security",
    "vendor news",
    "vendor advisory",
}

_STRICT_ALLOWED_SOURCES = {
    "apra",
    "asic",
    "acsc",
    "asd",
    "oaic",
    "reserve bank of australia",
    "council of financial regulators",
    "department of home affairs",
    "nist",
    "cisa",
    "mitre",
    "cis",
    "center for internet security",
    "owasp",
    "owasp foundation",
    "enisa",
    "sans institute",
    "cloud security alliance",
    "first",
    "iso public updates",
    "google threat intelligence",
    "microsoft threat intelligence",
    "cisco talos",
    "mandiant",
    "unit 42",
    "palo alto unit 42",
    "recorded future",
    "sophos x-ops",
    "red canary",
    "elastic security labs",
    "secureworks ctu",
    "krebsonsecurity",
    "krebs on security",
    "bleepingcomputer",
    "dark reading",
    "securityweek",
    "the record",
    "help net security",
    "cyberscoop",
    "cso online",
    "sc media",
    "infosecurity magazine",
    "the hacker news",
}

_EXECUTIVE_DAILY_TOP_SOURCES = {
    "nist",
    "cisa",
    "mitre",
    "apra",
    "asic",
    "acsc",
    "asd",
    "center for internet security",
    "owasp",
    "cloud security alliance",
    "enisa",
    "sans institute",
    "google threat intelligence",
    "cisco talos",
    "mandiant",
    "palo alto unit 42",
    "recorded future",
    "krebs on security",
    "dark reading",
    "securityweek",
}

_FINANCIAL_SERVICES_PRIORITY_SOURCES = {
    "reserve bank of australia",
    "council of financial regulators",
    "oaic",
    "department of home affairs",
    "european banking authority",
    "financial stability board",
    "bank for international settlements",
}

_AUSTRALIAN_REGULATOR_SOURCES = {
    "apra",
    "asic",
    "asd",
    "acsc",
    "reserve bank of australia",
    "council of financial regulators",
    "oaic",
    "department of home affairs",
}

_COMPLIANCE_FRAMEWORK_KEYWORDS: Dict[str, List[str]] = {
    "APRA CPS 230": ["cps 230", "operational resilience", "business continuity", "service provider"],
    "APRA CPS 234": ["cps 234", "information security", "cyber security incident", "security capability"],
    "ASD Essential Eight": ["essential eight", "essential 8", "mitigation strategies"],
    "NIST CSF": ["nist csf", "cybersecurity framework", "csf 2.0"],
    "NIST AI RMF": ["ai rmf", "ai risk management framework", "nist ai"],
    "MITRE ATT&CK": ["mitre att&ck", "attack technique", "tactic", "ttp"],
    "MITRE D3FEND": ["mitre d3fend", "d3fend"],
    "CIS Controls": ["cis controls", "center for internet security", "safeguard"],
    "ISO 27001": ["iso 27001", "isms"],
    "ISO 42001": ["iso 42001", "ai management system"],
    "PCI DSS": ["pci dss", "payment card industry", "cardholder data"],
    "SOC 2": ["soc 2", "trust services criteria"],
    "DORA": ["dora", "digital operational resilience act"],
    "NIS2": ["nis2", "network and information systems directive"],
    "Australian Privacy Act": ["privacy act", "notifiable data breach", "oaic"],
    "Security of Critical Infrastructure Act": ["security of critical infrastructure", "soci act", "critical infrastructure"],
}

_CONTROL_KEYWORDS: Dict[str, List[str]] = {
    "Identity & Access Management": ["identity", "iam", "mfa", "sso", "authentication", "authorization", "privileged"],
    "AI Governance": ["artificial intelligence", "ai governance", "llm", "model risk", "ai safety"],
    "Cloud Security": ["cloud", "saas", "iaas", "container", "kubernetes"],
    "Operational Resilience": ["operational resilience", "business continuity", "resilience", "outage", "critical operations"],
    "Third Party Risk": ["third party", "outsourcing", "supplier", "service provider", "vendor risk"],
    "Incident Response": ["incident response", "breach", "ransomware", "containment", "recovery"],
    "Vulnerability Management": ["vulnerability", "cve", "patch", "exploit", "known exploited"],
    "Data Protection & Privacy": ["privacy", "data breach", "personal information", "pii", "consent"],
}

_INDUSTRY_KEYWORDS: Dict[str, List[str]] = {
    "Financial Services": ["bank", "financial", "payment", "insurance", "superannuation"],
    "Government": ["government", "public sector", "agency"],
    "Healthcare": ["healthcare", "hospital", "medical"],
    "Critical Infrastructure": ["critical infrastructure", "energy", "utilities", "transport"],
    "Technology": ["technology", "software", "cloud", "saas"],
}

_TECHNOLOGY_KEYWORDS: Dict[str, List[str]] = {
    "Identity Platforms": ["iam", "identity", "sso", "mfa", "privileged access"],
    "Cloud Platforms": ["cloud", "kubernetes", "container", "serverless"],
    "AI/ML Systems": ["ai", "machine learning", "model", "llm"],
    "Endpoint and Network": ["endpoint", "edr", "network", "firewall", "vpn"],
    "Data Platforms": ["database", "data lake", "warehouse", "backup"],
}

_SECURITY_DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "Identity": ["identity", "iam", "authentication", "authorization", "privileged"],
    "Cloud": ["cloud", "saas", "iaas", "kubernetes", "container"],
    "AI": ["ai", "llm", "model", "prompt"],
    "Operational Resilience": ["resilience", "business continuity", "operational"],
    "Privacy": ["privacy", "personal information", "data protection", "notifiable data breach"],
    "Critical Infrastructure": ["critical infrastructure", "soci", "essential services"],
}

_COMPLIANCE_MONITOR_SCOPE: Dict[str, Dict[str, List[str]]] = {
    "primaryAustralianRegulators": {
        "APRA": [
            "CPS 230",
            "CPS 234",
            "Prudential Standards",
            "Prudential Practice Guides",
            "Information Papers",
            "Consultation Papers",
            "Media Releases",
            "Speeches",
            "Enforcement activity",
        ],
        "ASIC": [
            "Regulatory Guides",
            "Information Sheets",
            "Reports",
            "Cyber Guidance",
            "Enforcement Actions",
            "Consultation Papers",
            "Speeches",
            "Media Releases",
        ],
        "ASD": [
            "Essential Eight",
            "Mitigation Strategies",
            "Cyber Advisories",
            "Security Publications",
            "Annual Threat Reports",
        ],
        "ACSC": [
            "Advisories",
            "Alerts",
            "Vulnerability Bulletins",
            "Malware Alerts",
            "Ransomware Guidance",
            "Incident Response Guidance",
        ],
        "Reserve Bank of Australia": [
            "Operational Resilience",
            "Financial Stability Reviews",
            "Cyber Risk Publications",
            "Payment System Resilience",
        ],
        "Council of Financial Regulators": [
            "Joint Statements",
            "Financial Stability Publications",
            "Cyber Resilience Publications",
        ],
        "OAIC": [
            "Privacy Act Updates",
            "Notifiable Data Breach Guidance",
            "AI Guidance",
            "Privacy Determinations",
        ],
        "Department of Home Affairs": [
            "Critical Infrastructure",
            "Security of Critical Infrastructure Act",
            "Cyber Security Strategy",
            "National Cyber Updates",
        ],
    },
    "globalFrameworks": {
        "NIST": ["CSF 2.0", "SP 800 Series", "AI Risk Management Framework", "Cybersecurity Publications"],
        "CISA": ["Known Exploited Vulnerabilities", "Alerts", "Advisories", "Binding Operational Directives"],
        "MITRE": ["ATT&CK", "D3FEND", "CAPEC", "CVE"],
        "CIS": ["CIS Controls", "Benchmarks"],
        "OWASP": ["Top 10", "LLM Top 10", "API Security", "ASVS"],
        "Cloud Security Alliance": ["Research", "Guidance", "Zero Trust"],
        "ENISA": ["Threat Landscape Reports", "AI Security", "Cloud Guidance"],
        "ISO": ["ISO 27001", "ISO 27002", "ISO 42001", "SOC 2", "PCI DSS", "DORA", "NIS2"],
    },
}


def _contains_any(text: str, terms: List[str]) -> bool:
    return any(term in text for term in terms)


def _infer_frameworks(text: str, source: str) -> List[str]:
    frameworks: List[str] = []
    for framework, terms in _COMPLIANCE_FRAMEWORK_KEYWORDS.items():
        if _contains_any(text, terms):
            frameworks.append(framework)

    source_lower = source.lower()
    if source_lower == "apra":
        frameworks.extend(["APRA CPS 230", "APRA CPS 234"])
    if source_lower == "asd":
        frameworks.append("ASD Essential Eight")
    if source_lower == "nist":
        frameworks.extend(["NIST CSF", "NIST AI RMF"])
    if source_lower == "mitre":
        frameworks.extend(["MITRE ATT&CK", "MITRE D3FEND"])
    if source_lower == "cis":
        frameworks.append("CIS Controls")
    if source_lower == "oaic":
        frameworks.append("Australian Privacy Act")
    if source_lower == "department of home affairs":
        frameworks.append("Security of Critical Infrastructure Act")

    seen: Set[str] = set()
    ordered: List[str] = []
    for entry in frameworks:
        if entry not in seen:
            seen.add(entry)
            ordered.append(entry)
    return ordered


def _infer_controls(text: str) -> List[str]:
    controls = [control for control, terms in _CONTROL_KEYWORDS.items() if _contains_any(text, terms)]
    return controls or ["Governance and Oversight"]


def _infer_boolean_impacts(text: str, controls: List[str], frameworks: List[str]) -> Dict[str, bool]:
    return {
        "introducesNewControl": _contains_any(text, ["new control", "new requirement", "introduces", "new obligation"]),
        "changesExistingGuidance": _contains_any(text, ["update", "revised", "amend", "consultation", "change"]) or bool(frameworks),
        "impactsRegulatedFinancialInstitutions": _contains_any(text, ["apra", "prudential", "financial", "bank", "insurer", "payment"]),
        "impactsIAM": "Identity & Access Management" in controls,
        "impactsAIGovernance": "AI Governance" in controls,
        "impactsCloudSecurity": "Cloud Security" in controls,
        "impactsOperationalResilience": "Operational Resilience" in controls,
        "impactsThirdPartyRisk": "Third Party Risk" in controls,
    }


def _infer_security_domains(text: str, controls: List[str]) -> List[str]:
    inferred: List[str] = []
    for domain, terms in _SECURITY_DOMAIN_KEYWORDS.items():
        if _contains_any(text, terms):
            inferred.append(domain)
    if "Identity & Access Management" in controls and "Identity" not in inferred:
        inferred.append("Identity")
    if "Cloud Security" in controls and "Cloud" not in inferred:
        inferred.append("Cloud")
    if "AI Governance" in controls and "AI" not in inferred:
        inferred.append("AI")
    if "Operational Resilience" in controls and "Operational Resilience" not in inferred:
        inferred.append("Operational Resilience")
    if "Data Protection & Privacy" in controls and "Privacy" not in inferred:
        inferred.append("Privacy")
    return inferred or ["Governance"]


def _infer_industries(text: str) -> List[str]:
    industries = [industry for industry, terms in _INDUSTRY_KEYWORDS.items() if _contains_any(text, terms)]
    if "Financial Services" not in industries:
        industries.insert(0, "Financial Services")
    return industries


def _infer_technologies(text: str) -> List[str]:
    technologies = [tech for tech, terms in _TECHNOLOGY_KEYWORDS.items() if _contains_any(text, terms)]
    return technologies or ["Enterprise Security Stack"]


def _likelihood_from_severity(severity: str) -> str:
    severity_lower = severity.lower()
    if severity_lower == "critical":
        return "high"
    if severity_lower == "high":
        return "medium-high"
    if severity_lower == "medium":
        return "medium"
    return "low"


def _potential_financial_impact(severity: str, impacts_financial: bool) -> str:
    severity_lower = severity.lower()
    if impacts_financial and severity_lower in {"critical", "high"}:
        return "High potential financial impact due to resilience, compliance, and enforcement exposure."
    if impacts_financial:
        return "Moderate potential financial impact through compliance uplift and control remediation costs."
    return "Limited direct financial impact unless exposure intersects critical business services."


def _priority_from_rank(overall: float) -> str:
    if overall >= 0.9:
        return "P1"
    if overall >= 0.8:
        return "P2"
    if overall >= 0.7:
        return "P3"
    return "P4"


def _business_units_from_domains(domains: List[str]) -> List[str]:
    units: List[str] = ["Risk & Compliance", "Technology"]
    if "Identity" in domains:
        units.append("Identity & Access Management")
    if "Cloud" in domains:
        units.append("Cloud Platform Engineering")
    if "AI" in domains:
        units.append("Data & AI")
    if "Operational Resilience" in domains:
        units.append("Operational Resilience")
    if "Privacy" in domains:
        units.append("Privacy Office")
    return units


def _security_teams_from_domains(domains: List[str]) -> List[str]:
    teams: List[str] = ["Security Architecture", "Security Operations"]
    if "Identity" in domains:
        teams.append("IAM Engineering")
    if "Cloud" in domains:
        teams.append("Cloud Security")
    if "AI" in domains:
        teams.append("AI Security")
    if "Operational Resilience" in domains:
        teams.append("Resilience & Incident Management")
    if "Privacy" in domains:
        teams.append("Privacy & Data Protection")
    return teams


def _build_smart_impact_analysis(record: Dict[str, Any]) -> Dict[str, Any]:
    domains = record["securityDomains"]
    frameworks = record["controlCrossReference"]
    controls = record["controlMapping"]["controls"]
    business_units = _business_units_from_domains(domains)
    security_teams = _security_teams_from_domains(domains)

    return {
        "whatChanged": record["changeSummary"],
        "whyItMatters": record["executiveAnalysis"]["businessImpact"],
        "organisationsAffected": record["affectedIndustries"],
        "businessUnitsAffected": business_units,
        "securityTeamsAffected": security_teams,
        "iamControlsAffected": [entry for entry in controls if "Identity" in entry] or ["Identity governance review required"],
        "apraCpsControlsAffected": [entry for entry in frameworks if entry in {"APRA CPS 230", "APRA CPS 234"}],
        "nistControlsAffected": [entry for entry in frameworks if entry in {"NIST CSF", "NIST AI RMF"}],
        "policiesToReview": [
            "Information Security Policy",
            "Third Party Risk Policy",
            "Incident Response Policy",
        ],
        "standardsToUpdate": frameworks[:5],
        "cisoWeeklyActions": record["executiveAnalysis"]["recommendedActions"][:3],
        "cioKeyTakeaway": "Assess delivery and operational resilience implications for critical technology services.",
        "boardKeyTakeaway": record["executiveAnalysis"]["boardSummary"],
    }


def _build_compliance_record(item: Dict[str, Any]) -> Dict[str, Any]:
    title = str(item.get("title") or "")
    summary = str(item.get("summary") or "")
    source = str(item.get("source") or "Unknown")
    source_lower = source.lower()
    text = f"{title} {summary} {' '.join(str(t) for t in item.get('tags') or [])}".lower()

    frameworks = _infer_frameworks(text, source)
    controls = _infer_controls(text)
    boolean_impacts = _infer_boolean_impacts(text, controls, frameworks)
    domains = _infer_security_domains(text, controls)
    industries = _infer_industries(text)
    technologies = _infer_technologies(text)
    rankings = item.get("rankings") if isinstance(item.get("rankings"), dict) else {}
    overall_rank = float(rankings.get("overall", 0.0))
    severity = str(item.get("severity") or "medium").lower()

    executive_summary = str(item.get("executive_summary") or "").strip() or f"{title}: regulatory and control implications require assessment."
    technical_summary = summary or "Technical details pending source publication specifics."
    business_impact = "Potential compliance, resilience, and operational risk implications for regulated institutions."
    operational_impact = "Control owners may need to update operating procedures, assurance cadence, and evidence collection."

    record = {
        "title": title,
        "summary": summary,
        "url": item.get("url"),
        "publishedAt": item.get("published_at") or item.get("published"),
        "country": "Australia" if source_lower in _AUSTRALIAN_REGULATOR_SOURCES else "Global",
        "regulator": source,
        "framework": frameworks,
        "control": controls,
        "riskLevel": severity,
        "securityDomains": domains,
        "affectedIndustries": industries,
        "affectedTechnologies": technologies,
        "controlMapping": {
            "frameworks": frameworks,
            "controls": controls,
            **boolean_impacts,
        },
        "controlCrossReference": frameworks,
        "changeSummary": "New or revised regulatory and control guidance identified.",
        "executiveAnalysis": {
            "executiveSummary": executive_summary,
            "technicalSummary": technical_summary,
            "businessImpact": business_impact,
            "operationalImpact": operational_impact,
            "riskRating": severity,
            "likelihood": _likelihood_from_severity(severity),
            "potentialFinancialImpact": _potential_financial_impact(severity, boolean_impacts["impactsRegulatedFinancialInstitutions"]),
            "affectedIndustries": industries,
            "affectedTechnologies": technologies,
            "affectedControls": controls,
            "affectedSecurityDomains": domains,
            "recommendedActions": [
                "Perform control impact assessment against current policy and standards library.",
                "Assign accountable owners for any control uplift and target completion dates.",
                "Brief risk committee and executive leadership on residual risk and funding needs.",
            ],
            "priority": _priority_from_rank(overall_rank),
            "boardSummary": str(item.get("board_impact") or "Board-level attention required due to potential regulatory and resilience implications."),
        },
        "ranking": {
            "credibility": float(rankings.get("credibility", 0.8)),
            "executiveRelevance": float(rankings.get("executive_relevance", 0.8)),
            "businessImpact": float(rankings.get("business_impact", 0.75)),
            "regulatoryImportance": float(rankings.get("regulatory_importance", 0.75)),
            "overall": overall_rank,
        },
        "filters": {
            "identity": "Identity" in domains,
            "cloud": "Cloud" in domains,
            "ai": "AI" in domains,
            "operationalResilience": "Operational Resilience" in domains,
            "privacy": "Privacy" in domains,
            "criticalInfrastructure": "Critical Infrastructure" in domains,
        },
    }
    record["smartImpactAnalysis"] = _build_smart_impact_analysis(record)
    return record


def _build_compliance_items() -> List[Dict[str, Any]]:
    base_items = _load_combined_articles()
    compliance_items = [_build_compliance_record(item) for item in base_items]
    return sorted(
        compliance_items,
        key=lambda entry: (
            float(entry.get("ranking", {}).get("executiveRelevance", 0.0)),
            float(entry.get("ranking", {}).get("regulatoryImportance", 0.0)),
            float(entry.get("ranking", {}).get("businessImpact", 0.0)),
            float(entry.get("ranking", {}).get("overall", 0.0)),
        ),
        reverse=True,
    )


def _filter_compliance_items(
    items: List[Dict[str, Any]],
    country: Optional[str],
    framework: Optional[str],
    regulator: Optional[str],
    control: Optional[str],
    industry: Optional[str],
    risk_level: Optional[str],
    security_domain: Optional[str],
    identity: Optional[bool],
    cloud: Optional[bool],
    ai: Optional[bool],
    operational_resilience: Optional[bool],
    privacy: Optional[bool],
    critical_infrastructure: Optional[bool],
) -> List[Dict[str, Any]]:
    filtered = items

    if country:
        filtered = [entry for entry in filtered if str(entry.get("country") or "").lower() == country.lower()]
    if framework:
        framework_lower = framework.lower()
        filtered = [entry for entry in filtered if any(framework_lower in str(value).lower() for value in entry.get("framework", []))]
    if regulator:
        filtered = [entry for entry in filtered if str(entry.get("regulator") or "").lower() == regulator.lower()]
    if control:
        control_lower = control.lower()
        filtered = [entry for entry in filtered if any(control_lower in str(value).lower() for value in entry.get("control", []))]
    if industry:
        industry_lower = industry.lower()
        filtered = [entry for entry in filtered if any(industry_lower in str(value).lower() for value in entry.get("affectedIndustries", []))]
    if risk_level:
        filtered = [entry for entry in filtered if str(entry.get("riskLevel") or "").lower() == risk_level.lower()]
    if security_domain:
        domain_lower = security_domain.lower()
        filtered = [entry for entry in filtered if any(domain_lower in str(value).lower() for value in entry.get("securityDomains", []))]

    for key, value in {
        "identity": identity,
        "cloud": cloud,
        "ai": ai,
        "operationalResilience": operational_resilience,
        "privacy": privacy,
        "criticalInfrastructure": critical_infrastructure,
    }.items():
        if value is not None:
            filtered = [entry for entry in filtered if bool(entry.get("filters", {}).get(key)) == value]

    return filtered


def _compliance_widgets(items: List[Dict[str, Any]]) -> Dict[str, int]:
    def _count(predicate) -> int:
        return sum(1 for entry in items if predicate(entry))

    return {
        "newRegulations": _count(lambda entry: bool(entry.get("controlMapping", {}).get("introducesNewControl"))),
        "updatedRegulations": _count(lambda entry: bool(entry.get("controlMapping", {}).get("changesExistingGuidance"))),
        "upcomingComplianceDeadlines": _count(
            lambda entry: "deadline" in f"{entry.get('title') or ''} {entry.get('summary') or ''}".lower()
            or "effective" in f"{entry.get('title') or ''} {entry.get('summary') or ''}".lower()
        ),
        "controlsImpacted": sum(len(entry.get("control", [])) for entry in items),
        "frameworkUpdates": sum(len(entry.get("framework", [])) for entry in items),
        "criticalRegulatoryAlerts": _count(lambda entry: str(entry.get("riskLevel") or "").lower() in {"critical", "high"}),
        "apraUpdates": _count(lambda entry: str(entry.get("regulator") or "").lower() == "apra"),
        "asicUpdates": _count(lambda entry: str(entry.get("regulator") or "").lower() == "asic"),
        "asdUpdates": _count(lambda entry: str(entry.get("regulator") or "").lower() == "asd"),
        "acscUpdates": _count(lambda entry: str(entry.get("regulator") or "").lower() == "acsc"),
        "nistUpdates": _count(lambda entry: str(entry.get("regulator") or "").lower() == "nist"),
        "mitreUpdates": _count(lambda entry: str(entry.get("regulator") or "").lower() == "mitre"),
        "privacyUpdates": _count(lambda entry: bool(entry.get("filters", {}).get("privacy"))),
        "operationalResilience": _count(lambda entry: bool(entry.get("filters", {}).get("operationalResilience"))),
        "identityControlChanges": _count(lambda entry: bool(entry.get("filters", {}).get("identity"))),
        "aiGovernanceChanges": _count(lambda entry: bool(entry.get("filters", {}).get("ai"))),
    }


def _weekly_board_report(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    top = items[:15]

    def _titles(entries: List[Dict[str, Any]], limit: int = 5) -> List[str]:
        return [str(entry.get("title") or "Untitled update") for entry in entries[:limit]]

    high_risk = [entry for entry in top if str(entry.get("riskLevel") or "").lower() in {"critical", "high"}]
    controls_needing_review = [
        control
        for entry in top
        for control in entry.get("control", [])
    ]
    standards_to_update = [
        framework
        for entry in top
        for framework in entry.get("framework", [])
    ]

    return {
        "topRegulatoryChanges": _titles(top, limit=7),
        "topComplianceRisks": _titles(high_risk or top, limit=5),
        "topControlChanges": list(dict.fromkeys(controls_needing_review))[:10],
        "controlsRequiringReview": list(dict.fromkeys(controls_needing_review))[:10],
        "policiesRequiringUpdate": [
            "Information Security Policy",
            "Operational Resilience Standard",
            "Third Party Risk Management Policy",
            "Identity and Access Management Standard",
            "AI Governance Policy",
        ],
        "standardsRequiringUpdate": list(dict.fromkeys(standards_to_update))[:10],
        "recommendedExecutiveActions": [
            "Approve a 30-day compliance impact assessment for affected controls and standards.",
            "Fund priority remediation for critical and high-risk regulatory changes.",
            "Mandate cross-functional governance tracking for policy and standard updates.",
        ],
        "recommendedBoardDecisions": [
            "Confirm risk appetite alignment for resilience and compliance obligations.",
            "Approve oversight cadence for APRA, ASIC, OAIC, and global framework changes.",
            "Request assurance attestation for high-impact control updates.",
        ],
        "recommendedSecurityInvestments": [
            "Identity governance and privileged access uplift.",
            "Cloud security posture and continuous control monitoring.",
            "AI governance controls and model risk management capability.",
        ],
    }


def get_db() -> Generator[Any, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    global _REQUEST_COUNT
    _REQUEST_COUNT += 1
    LOGGER.info("Incoming %s %s", request.method, request.url.path)
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)
    LOGGER.info("Completed %s %s in %.2fms", request.method, request.url.path, duration_ms)
    response.headers["X-Process-Time"] = str(duration_ms)
    return response


@app.get("/health")
def health_check() -> Dict[str, Any]:
    return {"status": "ok", "service": "cyber-intelligence-platform"}


@app.get("/metrics")
def metrics() -> Dict[str, Any]:
    return {
        "requests": _REQUEST_COUNT,
        "uptime_seconds": round(time.time() - _START_TIME, 2),
        "database": str(DATA_DIR / "cyber_intelligence.db"),
    }


def _article_to_model(article: Any) -> NewsArticle:
    return NewsArticle.model_validate(
        {
            "id": str(article.id) if article.id is not None else None,
            "title": article.title,
            "summary": article.summary,
            "source": article.source,
            "category": article.category,
            "severity": article.severity,
            "url": article.url,
            "published_at": article.published_at,
            "tags": article.tags or [],
            "metadata": {},
        }
    )


def _load_json_payload(name: str) -> List[Dict[str, Any]]:
    path = DATA_DIR / "daily" / name
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_article_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    title = str(item.get("title") or "").strip()
    summary = str(item.get("summary") or item.get("description") or "").strip()
    source = str(item.get("source") or item.get("vendor") or "Unknown").strip() or "Unknown"
    category = str(item.get("category") or "General").strip() or "General"
    subcategory = str(item.get("subcategory") or "").strip() or "General"
    url = str(item.get("url") or item.get("link") or "").strip()
    published = item.get("published_at") or item.get("published_date") or item.get("published")
    severity = str(item.get("severity") or "medium").strip().lower() or "medium"
    tags = item.get("tags")
    if not isinstance(tags, list):
        tags = []

    haystack = " ".join(
        [
            title.lower(),
            summary.lower(),
            source.lower(),
            " ".join(str(tag).lower() for tag in tags if str(tag).strip()),
        ]
    )
    category_scores = {
        candidate: sum(1 for keyword in keywords if keyword in haystack)
        for candidate, keywords in _CATEGORY_KEYWORDS.items()
    }
    inferred_category, inferred_score = max(category_scores.items(), key=lambda entry: entry[1])
    current_score = category_scores.get(category, 0)
    if inferred_score >= 2 and inferred_score > current_score:
        category = inferred_category

    source_group = str(item.get("source_group") or "").strip()
    official_url = str(item.get("official_url") or "").strip()
    source_definition = _SOURCE_DEFINITION_BY_NAME.get(source.lower())
    if source_definition:
        if not source_group:
            source_group = source_definition.group
        if not official_url:
            official_url = source_definition.official_url
        if subcategory == "General":
            subcategory = source_definition.subcategory

    severity_weights = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    severity_score = severity_weights.get(severity, 2)
    credibility = float(item.get("rankings", {}).get("credibility", source_definition.credibility_weight if source_definition else 0.8)) if isinstance(item.get("rankings"), dict) else float(source_definition.credibility_weight if source_definition else 0.8)
    executive_relevance = float(item.get("rankings", {}).get("executive_relevance", 0.85 if category in {"Regulation", "Threat", "Identity"} else 0.7)) if isinstance(item.get("rankings"), dict) else (0.85 if category in {"Regulation", "Threat", "Identity"} else 0.7)
    business_impact = float(item.get("rankings", {}).get("business_impact", min(1.0, severity_score * 0.25))) if isinstance(item.get("rankings"), dict) else min(1.0, severity_score * 0.25)
    regulatory_importance = float(item.get("rankings", {}).get("regulatory_importance", 1.0 if category == "Regulation" else 0.55)) if isinstance(item.get("rankings"), dict) else (1.0 if category == "Regulation" else 0.55)
    overall_rank = round((credibility * 0.35) + (executive_relevance * 0.25) + (business_impact * 0.25) + (regulatory_importance * 0.15), 3)

    executive_summary = str(item.get("executive_summary") or "").strip() or f"{category}: {(summary or title)[:280]}"
    board_impact = str(item.get("board_impact") or "").strip() or "Requires executive review for resilience, compliance, and operating risk impact."
    recommended_actions = item.get("recommended_actions")
    if not isinstance(recommended_actions, list):
        recommended_actions = [
            "Validate exposure and control coverage.",
            "Prioritize remediation against business criticality.",
            "Track completion and residual risk in governance forums.",
        ]
    ciso_action_items = item.get("ciso_action_items")
    if not isinstance(ciso_action_items, list):
        ciso_action_items = [
            "Assign owners and timelines for mitigations.",
            "Validate detection and response readiness.",
            "Brief executive stakeholders on residual risk.",
        ]

    affected_industries = item.get("affected_industries")
    if not isinstance(affected_industries, list):
        affected_industries = ["General"]

    affected_iam_domains = item.get("affected_iam_domains")
    if not isinstance(affected_iam_domains, list):
        affected_iam_domains = ["General"]

    control_mappings = item.get("control_mappings")
    if not isinstance(control_mappings, list):
        control_mappings = []

    monitors = item.get("monitors")
    if not isinstance(monitors, list):
        monitors = source_definition.monitors if source_definition else []

    return {
        "title": title,
        "summary": summary,
        "url": url,
        "details_url": url,
        "published": published,
        "published_at": published,
        "source": source,
        "vendor": source,
        "category": category,
        "subcategory": subcategory,
        "source_group": source_group or "General Sources",
        "monitors": [str(entry) for entry in monitors if str(entry).strip()],
        "official_url": official_url,
        "severity": severity,
        "tags": [str(tag) for tag in tags if str(tag).strip()],
        "executive_summary": executive_summary,
        "affected_industries": [str(entry) for entry in affected_industries if str(entry).strip()],
        "affected_iam_domains": [str(entry) for entry in affected_iam_domains if str(entry).strip()],
        "control_mappings": [str(entry) for entry in control_mappings if str(entry).strip()],
        "recommended_actions": [str(entry) for entry in recommended_actions if str(entry).strip()],
        "board_impact": board_impact,
        "ciso_action_items": [str(entry) for entry in ciso_action_items if str(entry).strip()],
        "rankings": {
            "credibility": round(credibility, 3),
            "executive_relevance": round(executive_relevance, 3),
            "business_impact": round(business_impact, 3),
            "regulatory_importance": round(regulatory_importance, 3),
            "overall": overall_rank,
        },
    }


def _source_priority(item: Dict[str, Any]) -> int:
    group = str(item.get("source_group") or "General Sources")
    source = str(item.get("source") or "").lower().strip()
    if source in _EXECUTIVE_DAILY_TOP_SOURCES:
        return 5
    if source in _FINANCIAL_SERVICES_PRIORITY_SOURCES:
        return 4
    if group in _AUTHORITATIVE_GROUPS:
        return 3
    if group in _INDEPENDENT_GROUPS:
        return 2
    return 1


def _source_cap(item: Dict[str, Any]) -> int:
    group = str(item.get("source_group") or "General Sources")
    source = str(item.get("source") or "").lower().strip()
    if source in _EXECUTIVE_DAILY_TOP_SOURCES:
        return 120
    if source in _FINANCIAL_SERVICES_PRIORITY_SOURCES:
        return 90
    if group in _AUTHORITATIVE_GROUPS:
        return 80
    if group in _INDEPENDENT_GROUPS:
        return 40
    if source in _VENDOR_BLOG_SOURCES:
        return 6
    return 12


def _is_promotional(item: Dict[str, Any]) -> bool:
    text = f"{item.get('title') or ''} {item.get('summary') or ''}".lower()
    return any(term in text for term in _PROMOTIONAL_TERMS)


def _rebalance_product_neutral(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ordered = sorted(
        items,
        key=lambda item: (
            float((item.get("rankings") or {}).get("overall", 0.0)),
            _source_priority(item),
            (_parse_published_datetime(item.get("published") or item.get("published_at")) or datetime(1970, 1, 1, tzinfo=timezone.utc)).timestamp(),
        ),
        reverse=True,
    )

    source_counts: Counter[str] = Counter()
    balanced: List[Dict[str, Any]] = []

    for item in ordered:
        source = str(item.get("source") or "Unknown")
        source_lower = source.lower().strip()

        # Strict allowlist from user-provided trusted source catalog.
        if source_lower not in _STRICT_ALLOWED_SOURCES:
            continue

        # Hard-exclude vendor blogs from dashboard outputs.
        if source_lower in _VENDOR_BLOG_SOURCES:
            continue

        cap = _source_cap(item)
        severity = str(item.get("severity") or "medium").lower()
        if source_counts[source] >= cap:
            continue

        # Keep high-signal alerts, but down-rank marketing-heavy content from non-authoritative sources.
        if _source_priority(item) == 1 and _is_promotional(item) and severity not in {"high", "critical"}:
            continue

        source_counts[source] += 1
        balanced.append(item)

    if balanced:
        return balanced
    return ordered[:200]


def _load_combined_articles() -> List[Dict[str, Any]]:
    combined_path = DATA_DIR / "daily" / "combined.json"
    raw_items: List[Dict[str, Any]] = []

    if combined_path.exists():
        try:
            payload = json.loads(combined_path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                raw_items = [item for item in payload if isinstance(item, dict)]
        except json.JSONDecodeError as exc:
            LOGGER.warning("Failed to parse %s: %s", combined_path, exc)

    if not raw_items:
        db = SessionLocal()
        try:
            articles = db.query(Article).order_by(Article.created_at.desc()).all()
            for article in articles:
                raw_items.append(
                    {
                        "title": article.title,
                        "summary": article.summary,
                        "url": article.url,
                        "published_at": article.published_at.isoformat() if article.published_at else None,
                        "source": article.source,
                        "category": article.category,
                        "severity": article.severity,
                        "tags": article.tags or [],
                    }
                )
        finally:
            db.close()

    normalized = []
    seen = set()
    for item in raw_items:
        normalized_item = _normalize_article_payload(item)
        if not normalized_item["title"]:
            continue
        dedupe_key = (normalized_item["title"].lower(), normalized_item.get("url") or "")
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        normalized.append(normalized_item)

    return _rebalance_product_neutral(normalized)


def _paginate(items: List[Dict[str, Any]], page: int, page_size: int) -> Dict[str, Any]:
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    start = (page - 1) * page_size
    end = start + page_size
    sliced = items[start:end]
    return {
        "items": sliced,
        "page": page,
        "page_size": page_size,
        "total": len(items),
        "pages": max(1, (len(items) + page_size - 1) // page_size),
    }


def _filter_and_sort(items: List[Dict[str, Any]], category: Optional[str], search: Optional[str], sort: Optional[str]) -> List[Dict[str, Any]]:
    filtered = items
    if category:
        filtered = [item for item in filtered if str(item.get("category") or "").lower() == category.lower()]
    if search:
        search_term = search.lower()
        filtered = [
            item
            for item in filtered
            if search_term in str(item.get("title") or "").lower()
            or search_term in str(item.get("summary") or "").lower()
            or search_term in str(item.get("source") or "").lower()
        ]
    if sort == "asc":
        filtered = sorted(filtered, key=lambda item: str(item.get("title") or "").lower())
    elif sort == "desc":
        filtered = sorted(filtered, key=lambda item: str(item.get("title") or "").lower(), reverse=True)
    return filtered


def _filter_by_domain(items: List[Dict[str, Any]], domain: str) -> List[Dict[str, Any]]:
    domain_key = domain.lower()
    filtered = []
    for item in items:
        category = str(item.get("category") or "").lower()
        source = str(item.get("source") or "").lower()
        title = str(item.get("title") or "").lower()
        summary = str(item.get("summary") or "").lower()
        haystack = f"{category} {source} {title} {summary}"
        if domain_key == "vendors" and ("vendor" in haystack or "patch" in haystack or "advisory" in haystack):
            filtered.append(item)
        elif domain_key == "regulations" and ("regulation" in haystack or "compliance" in haystack or "nist" in haystack or "cisa" in haystack):
            filtered.append(item)
        elif domain_key == "threats" and ("threat" in haystack or "ransomware" in haystack or "exploit" in haystack):
            filtered.append(item)
        elif domain_key == "research" and ("research" in haystack or "paper" in haystack or "arxiv" in haystack):
            filtered.append(item)
    return filtered


@app.get(
    "/news",
    response_model=Dict[str, Any],
    summary="List news articles",
    description="Returns paginated intelligence news items for the current daily report.",
)
def list_news(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort: Optional[str] = Query(None, pattern="^(asc|desc)$"),
) -> Dict[str, Any]:
    items = _load_combined_articles()
    filtered = _filter_and_sort(items, category=category, search=search, sort=sort)
    return _paginate(filtered, page=page, page_size=page_size)


@app.get("/trends", response_model=Dict[str, Any], summary="List trending topics")
def list_trends(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort: Optional[str] = Query(None, pattern="^(asc|desc)$"),
) -> Dict[str, Any]:
    items = _load_json_payload("trending_topics.json")
    filtered = _filter_and_sort(items, category=None, search=search, sort=sort)
    return _paginate(filtered, page=page, page_size=page_size)


@app.get(
    "/vendors",
    response_model=Dict[str, Any],
    summary="List vendor updates",
    description="Returns paginated vendor intelligence and advisory updates.",
)
def list_vendors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort: Optional[str] = Query(None, pattern="^(asc|desc)$"),
) -> Dict[str, Any]:
    items = _filter_by_domain(_load_combined_articles(), "vendors")
    filtered = _filter_and_sort(items, category=None, search=search, sort=sort)
    return _paginate(filtered, page=page, page_size=page_size)


@app.get(
    "/regulations",
    response_model=Dict[str, Any],
    summary="List regulation updates",
    description="Returns paginated cybersecurity regulation and compliance updates.",
)
def list_regulations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort: Optional[str] = Query(None, pattern="^(asc|desc)$"),
) -> Dict[str, Any]:
    items = _filter_by_domain(_load_combined_articles(), "regulations")
    filtered = _filter_and_sort(items, category=None, search=search, sort=sort)
    return _paginate(filtered, page=page, page_size=page_size)


@app.get(
    "/threats",
    response_model=Dict[str, Any],
    summary="List threat intelligence",
    description="Returns paginated threat intelligence entries for today's reporting set.",
)
def list_threats(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort: Optional[str] = Query(None, pattern="^(asc|desc)$"),
) -> Dict[str, Any]:
    items = _filter_by_domain(_load_combined_articles(), "threats")
    filtered = _filter_and_sort(items, category=None, search=search, sort=sort)
    return _paginate(filtered, page=page, page_size=page_size)


@app.get(
    "/research",
    response_model=Dict[str, Any],
    summary="List research papers",
    description="Returns paginated cybersecurity research and paper summaries.",
)
def list_research(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort: Optional[str] = Query(None, pattern="^(asc|desc)$"),
) -> Dict[str, Any]:
    items = _filter_by_domain(_load_combined_articles(), "research")
    filtered = _filter_and_sort(items, category=None, search=search, sort=sort)
    return _paginate(filtered, page=page, page_size=page_size)


@app.get("/executive-summary", response_model=Dict[str, Any], summary="Get executive summary")
def executive_summary() -> Dict[str, Any]:
    payload = _load_json_payload("executive_summary.json")
    if not payload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Executive summary not found")
    return payload


def _today_date_key() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _load_today_enrichment_bundle() -> Dict[str, Any]:
    today_path = DATA_DIR / "daily" / f"{_today_date_key()}.json"
    if not today_path.exists():
        return {}
    with today_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def _parse_published_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _aggregate_today_dashboard() -> Dict[str, Any]:
    all_items = _load_combined_articles()
    news = all_items
    vendors = _filter_by_domain(all_items, "vendors")
    regulations = _filter_by_domain(all_items, "regulations")
    threats = _filter_by_domain(all_items, "threats")
    research = _filter_by_domain(all_items, "research")
    enrichment = _load_today_enrichment_bundle()

    section_counts = {
        "news": len(news),
        "vendors": len(vendors),
        "regulations": len(regulations),
        "threats": len(threats),
        "research": len(research),
    }

    category_counter = Counter(str(item.get("category") or "General") for item in all_items)
    source_counter = Counter(str(item.get("source") or "Unknown") for item in all_items)
    group_counter = Counter(str(item.get("source_group") or "General Sources") for item in all_items)

    agents = enrichment.get("agents") if isinstance(enrichment, dict) else []
    if not isinstance(agents, list):
        agents = []

    tag_counter: Counter[str] = Counter()
    for agent in agents:
        if isinstance(agent, dict):
            tags = agent.get("tags")
            if isinstance(tags, list):
                tag_counter.update(str(tag) for tag in tags)

    summary_payload: Dict[str, Any]
    summary_file_path = DATA_DIR / "daily" / "executive_summary.json"
    if summary_file_path.exists():
        try:
            parsed_summary = json.loads(summary_file_path.read_text(encoding="utf-8"))
            summary_payload = parsed_summary if isinstance(parsed_summary, dict) else {}
        except json.JSONDecodeError:
            summary_payload = {}
    else:
        summary_payload = {}

    if not summary_payload and agents:
        first_agent = agents[0] if isinstance(agents[0], dict) else {}
        summary_payload = {
            "headline": "Daily cyber intelligence summary",
            "summary": first_agent.get("executive_summary", "Executive summary unavailable."),
            "key_risks": [],
            "top_priorities": first_agent.get("recommended_actions", []),
            "confidence": "medium",
        }

    categories = [{"name": k, "count": v} for k, v in category_counter.most_common(50)]
    sources = [{"name": k, "count": v} for k, v in source_counter.most_common(50)]
    trend_data = [{"name": entry["name"], "value": entry["count"]} for entry in categories[:20]]
    last_updated = enrichment.get("generated_at") if isinstance(enrichment, dict) else None

    def _count_items(predicate):
        return sum(1 for item in all_items if predicate(item))

    australian_regulatory_updates = _count_items(lambda i: str(i.get("source_group") or "") == "Australian Regulators")
    global_regulatory_updates = _count_items(lambda i: str(i.get("source_group") or "") == "Global Standards")
    nist_updates = _count_items(lambda i: str(i.get("source") or "").lower() == "nist")
    apra_updates = _count_items(lambda i: str(i.get("source") or "").lower() == "apra")
    asic_updates = _count_items(lambda i: str(i.get("source") or "").lower() == "asic")
    asd_acsc_updates = _count_items(lambda i: str(i.get("source") or "").lower() in {"asd", "acsc"})
    iam_updates = _count_items(lambda i: str(i.get("category") or "") == "Identity")
    ai_security_updates = _count_items(lambda i: str(i.get("category") or "") == "AI Security")
    threat_intelligence_updates = _count_items(lambda i: str(i.get("category") or "") == "Threat")
    research_papers = _count_items(lambda i: str(i.get("category") or "") == "Research")
    emerging_risks = _count_items(
        lambda i: str(i.get("severity") or "").lower() in {"high", "critical"}
        or float((i.get("rankings") or {}).get("overall", 0.0)) >= 0.82
    )

    top_10_executive_stories = sorted(
        all_items,
        key=lambda i: float((i.get("rankings") or {}).get("overall", 0.0)),
        reverse=True,
    )[:10]

    yesterday_cutoff = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    changed_since_yesterday = [
        item
        for item in all_items
        if (_parse_published_datetime(item.get("published") or item.get("published_at")) or yesterday_cutoff) >= yesterday_cutoff
    ]

    widgets = {
        "australianRegulatoryUpdates": australian_regulatory_updates,
        "globalRegulatoryUpdates": global_regulatory_updates,
        "nistUpdates": nist_updates,
        "apraUpdates": apra_updates,
        "asicUpdates": asic_updates,
        "asdAcscAdvisories": asd_acsc_updates,
        "identityAndAccessManagement": iam_updates,
        "aiSecurity": ai_security_updates,
        "threatIntelligence": threat_intelligence_updates,
        "researchPapers": research_papers,
        "emergingRisks": emerging_risks,
        "top10ExecutiveStories": len(top_10_executive_stories),
        "whatChangedSinceYesterday": len(changed_since_yesterday),
    }

    return {
        "summary": summary_payload,
        "articles": all_items,
        "categories": categories,
        "sources": sources,
        "trendData": trend_data,
        "lastUpdated": last_updated,
        "stats": {
            "articleCount": len(all_items),
            "categoryCount": len(categories),
            "sourceCount": len(sources),
        },
        "widgets": widgets,
        "sourceGroups": [{"name": key, "count": count} for key, count in group_counter.most_common()],
        "topExecutiveStories": top_10_executive_stories,
        "whatChangedSinceYesterday": changed_since_yesterday[:20],
        "sectionCounts": section_counts,
        "topTags": [{"tag": k, "count": v} for k, v in tag_counter.most_common(10)],
    }


@app.get(
    "/summary",
    response_model=Dict[str, Any],
    summary="Get today executive summary",
    description="Returns the executive summary generated from today's intelligence collection and enrichment outputs.",
)
def summary() -> Dict[str, Any]:
    payload = _load_json_payload("executive_summary.json")
    if payload:
        return payload

    enrichment = _load_today_enrichment_bundle()
    agents = enrichment.get("agents") if isinstance(enrichment, dict) else []
    if isinstance(agents, list) and agents:
        top_agent = agents[0] if isinstance(agents[0], dict) else {}
        return {
            "headline": "Daily cyber intelligence summary",
            "summary": top_agent.get("executive_summary", "Executive summary unavailable."),
            "key_risks": [],
            "top_priorities": top_agent.get("recommended_actions", []),
            "confidence": "medium",
        }

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")


@app.get("/search", response_model=Dict[str, Any], summary="Search across intelligence content")
def search_content(q: str = Query(..., min_length=1), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)) -> Dict[str, Any]:
    flattened = _load_combined_articles()
    filtered = [item for item in flattened if q.lower() in str(item.get("title") or "").lower() or q.lower() in str(item.get("summary") or "").lower()]
    return _paginate(filtered, page=page, page_size=page_size)


@app.get("/source-registry", response_model=Dict[str, Any], summary="Get modular source registry")
def get_source_registry() -> Dict[str, Any]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for definition in flattened_sources():
        grouped.setdefault(definition.group, []).append(
            {
                "id": definition.id,
                "name": definition.name,
                "category": definition.category,
                "subcategory": definition.subcategory,
                "endpoint": definition.endpoint,
                "officialUrl": definition.official_url,
                "monitors": definition.monitors,
                "credibilityWeight": definition.credibility_weight,
            }
        )
    return {"groups": grouped}


@app.get(
    "/dashboard",
    response_model=Dict[str, Any],
    summary="Get today's intelligence dashboard",
    description="Aggregates today's intelligence across news, vendors, regulations, threats, research, and AI enrichment outputs.",
)
def dashboard() -> Dict[str, Any]:
    try:
        return _aggregate_today_dashboard()
    except ArticleServiceError as exc:
        LOGGER.exception("Dashboard request failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to load dashboard data") from exc


def _load_enriched_intelligence() -> List[Dict[str, Any]]:
    return enrich_articles(_load_combined_articles())


@app.get(
    "/v2/source-registry",
    response_model=Dict[str, Any],
    summary="Get enterprise source registry",
    description="Returns configurable source registry with trust, relevance, coverage, framework support, and sync metadata.",
)
def source_registry_v2() -> Dict[str, Any]:
    registry = load_source_registry()
    return {
        "health": source_registry_health(registry),
        "sources": registry,
    }


@app.get(
    "/v2/executive/dashboards",
    response_model=Dict[str, Any],
    summary="Get all executive dashboards",
    description="Returns all executive dashboard datasets and widget aggregates.",
)
def executive_dashboards() -> Dict[str, Any]:
    return build_dashboard_bundle(_load_enriched_intelligence())


@app.get(
    "/v2/executive/dashboards/{dashboard_id}",
    response_model=Dict[str, Any],
    summary="Get executive dashboard by id",
)
def executive_dashboard(dashboard_id: str) -> Dict[str, Any]:
    bundle = build_dashboard_bundle(_load_enriched_intelligence())
    for dashboard in bundle.get("dashboards", []):
        if str(dashboard.get("id") or "") == dashboard_id:
            return dashboard
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")


@app.get(
    "/v2/executive/widgets/{dashboard_id}/{widget_id}",
    response_model=Dict[str, Any],
    summary="Get widget payload",
    description="Returns REST payload for any dashboard widget.",
)
def executive_widget_payload(dashboard_id: str, widget_id: str) -> Dict[str, Any]:
    return get_widget_payload(_load_enriched_intelligence(), dashboard_id=dashboard_id, widget_id=widget_id)


@app.get(
    "/v2/executive/daily-brief",
    response_model=Dict[str, Any],
    summary="Get executive daily brief",
    description="Returns executive daily brief with top stories, changes, risk focus, and action recommendations.",
)
def executive_daily_brief() -> Dict[str, Any]:
    return build_daily_brief(_load_enriched_intelligence())


@app.get(
    "/v2/executive/reports/{report_type}",
    response_model=Dict[str, Any],
    summary="Get executive report payload",
    description="Returns report-ready payload for weekly, monthly, board, pdf, ppt, email, and teams channels.",
)
def executive_report(report_type: str) -> Dict[str, Any]:
    supported = {"weekly", "monthly", "board", "pdf", "ppt", "email", "teams"}
    if report_type.lower() not in supported:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported report type. Supported: {sorted(supported)}")
    return build_reports(_load_enriched_intelligence(), report_type=report_type.lower())


@app.get(
    "/v2/executive/search",
    response_model=Dict[str, Any],
    summary="Search executive intelligence",
    description="Search by framework, control, country, industry, threat actor, MITRE technique, CVE, technology, vendor, regulator, identity/cloud/ai topics and risk level.",
)
def executive_search(
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
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    items = search_articles(
        _load_enriched_intelligence(),
        framework=framework,
        control=control,
        country=country,
        industry=industry,
        threat_actor=threat_actor,
        mitre_technique=mitre_technique,
        cve=cve,
        technology=technology,
        vendor=vendor,
        regulator=regulator,
        identity_topic=identity_topic,
        cloud_topic=cloud_topic,
        ai_topic=ai_topic,
        risk_level=risk_level,
    )
    return _paginate(items, page=page, page_size=page_size)


@app.get(
    "/v2/executive/scheduler",
    response_model=Dict[str, Any],
    summary="Get scheduling metadata",
    description="Returns scheduler job metadata for collection, enrichment, daily briefs, and board reports.",
)
def executive_scheduler() -> Dict[str, Any]:
    runtime = _EXECUTIVE_SCHEDULER.runtime_status()
    if runtime.get("enabled") and not runtime.get("running"):
        _EXECUTIVE_SCHEDULER.start()
        runtime = _EXECUTIVE_SCHEDULER.runtime_status()
    return scheduler_status(health_fn=lambda: {"status": "ready"}, runtime=runtime)


@app.post(
    "/v2/executive/pipeline/run",
    response_model=Dict[str, Any],
    summary="Run ingestion and enrichment pipeline",
    description="Collects sources using API/RSS/HTML fallback, enriches content, persists normalized records, and writes executive brief/report snapshots.",
)
def run_executive_pipeline(max_sources: Optional[int] = Query(None, ge=1, le=500)) -> Dict[str, Any]:
    result = run_ingestion_enrichment_pipeline(max_sources=max_sources)
    if isinstance(result, dict):
        _EXECUTIVE_SCHEDULER.record_manual_run(result)
    return result


@app.get(
    "/compliance-control-intelligence",
    response_model=Dict[str, Any],
    summary="Get Compliance & Control Intelligence module",
    description="Returns compliance-focused intelligence with control mapping, cross-framework references, executive analysis, smart impact analysis, board report, and dashboard widgets.",
)
def compliance_control_intelligence(
    country: Optional[str] = Query(None),
    framework: Optional[str] = Query(None),
    regulator: Optional[str] = Query(None),
    control: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    security_domain: Optional[str] = Query(None),
    identity: Optional[bool] = Query(None),
    cloud: Optional[bool] = Query(None),
    ai: Optional[bool] = Query(None),
    operational_resilience: Optional[bool] = Query(None),
    privacy: Optional[bool] = Query(None),
    critical_infrastructure: Optional[bool] = Query(None),
) -> Dict[str, Any]:
    items = _build_compliance_items()
    filtered_items = _filter_compliance_items(
        items=items,
        country=country,
        framework=framework,
        regulator=regulator,
        control=control,
        industry=industry,
        risk_level=risk_level,
        security_domain=security_domain,
        identity=identity,
        cloud=cloud,
        ai=ai,
        operational_resilience=operational_resilience,
        privacy=privacy,
        critical_infrastructure=critical_infrastructure,
    )

    frameworks = Counter(framework_name for item in filtered_items for framework_name in item.get("framework", []))
    regulators = Counter(str(item.get("regulator") or "Unknown") for item in filtered_items)
    controls = Counter(control_name for item in filtered_items for control_name in item.get("control", []))
    industries = Counter(industry_name for item in filtered_items for industry_name in item.get("affectedIndustries", []))
    domains = Counter(domain_name for item in filtered_items for domain_name in item.get("securityDomains", []))

    return {
        "module": "Compliance & Control Intelligence",
        "audience": [
            "CISO",
            "CIO",
            "CTO",
            "Head of Security",
            "Head of IAM",
            "Risk Officer",
            "Compliance Team",
        ],
        "monitorScope": _COMPLIANCE_MONITOR_SCOPE,
        "prioritization": "executive_relevance_over_publication_date",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "filtersApplied": {
            "country": country,
            "framework": framework,
            "regulator": regulator,
            "control": control,
            "industry": industry,
            "riskLevel": risk_level,
            "securityDomain": security_domain,
            "identity": identity,
            "cloud": cloud,
            "ai": ai,
            "operationalResilience": operational_resilience,
            "privacy": privacy,
            "criticalInfrastructure": critical_infrastructure,
        },
        "availableFilters": {
            "country": sorted({str(item.get("country") or "Unknown") for item in items}),
            "framework": [name for name, _ in frameworks.most_common(50)],
            "regulator": [name for name, _ in regulators.most_common(50)],
            "control": [name for name, _ in controls.most_common(50)],
            "industry": [name for name, _ in industries.most_common(50)],
            "riskLevel": sorted({str(item.get("riskLevel") or "medium") for item in items}),
            "securityDomain": [name for name, _ in domains.most_common(50)],
            "identity": [True, False],
            "cloud": [True, False],
            "ai": [True, False],
            "operationalResilience": [True, False],
            "privacy": [True, False],
            "criticalInfrastructure": [True, False],
        },
        "widgets": _compliance_widgets(filtered_items),
        "dashboard": {
            "frameworkUpdates": [{"name": name, "count": count} for name, count in frameworks.most_common(15)],
            "regulatorUpdates": [{"name": name, "count": count} for name, count in regulators.most_common(15)],
            "controlsImpacted": [{"name": name, "count": count} for name, count in controls.most_common(15)],
            "industryImpact": [{"name": name, "count": count} for name, count in industries.most_common(15)],
            "securityDomains": [{"name": name, "count": count} for name, count in domains.most_common(15)],
        },
        "boardReport": _weekly_board_report(filtered_items),
        "count": len(filtered_items),
        "items": filtered_items,
    }


@app.post("/articles", response_model=NewsArticle, status_code=status.HTTP_201_CREATED)
def create_article(payload: NewsArticle) -> NewsArticle:
    db = SessionLocal()
    try:
        article = save_article(db=db, payload=payload.model_dump(mode="json"))
        return _article_to_model(article)
    except ArticleServiceError as exc:
        LOGGER.exception("Article creation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to create article") from exc
    finally:
        db.close()
