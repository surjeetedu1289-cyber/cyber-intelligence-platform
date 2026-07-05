from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SourceDefinition:
    id: str
    name: str
    group: str
    collector_type: str
    endpoint: Optional[str]
    category: str
    subcategory: str
    monitors: List[str]
    credibility_weight: float
    official_url: str


def source_registry() -> Dict[str, List[SourceDefinition]]:
    return {
        "australian_regulators": [
            SourceDefinition("apra", "APRA", "Australian Regulators", "rss", "https://www.apra.gov.au/rss.xml", "Regulation", "APRA", ["CPS 230", "CPS 234", "Prudential Standards", "Operational Resilience"], 0.99, "https://www.apra.gov.au"),
            SourceDefinition("asic", "ASIC", "Australian Regulators", "rss", "https://asic.gov.au/about-asic/news-centre/find-a-media-release/rss-feed/", "Regulation", "ASIC", ["Regulatory Guides", "Enforcement Actions", "Consultation Papers"], 0.99, "https://asic.gov.au"),
            SourceDefinition("acsc", "ACSC", "Australian Regulators", "rss", "https://www.cyber.gov.au/rss.xml", "Regulation", "ACSC Advisory", ["Essential Eight", "Cyber Advisories", "Critical Infrastructure"], 0.99, "https://www.cyber.gov.au"),
            SourceDefinition("asd", "ASD", "Australian Regulators", "rss", "https://www.asd.gov.au/rss.xml", "Regulation", "ASD Advisory", ["Essential Eight", "Cyber Advisories", "Critical Infrastructure"], 0.98, "https://www.asd.gov.au"),
            SourceDefinition("oaic", "OAIC", "Australian Regulators", "rss", "https://www.oaic.gov.au/rss.xml", "Regulation", "Privacy Guidance", ["Privacy Guidance", "Enforcement Actions", "Media Releases"], 0.98, "https://www.oaic.gov.au"),
            SourceDefinition("rba", "Reserve Bank of Australia", "Australian Regulators", "rss", "https://www.rba.gov.au/rss/rss-cb.xml", "Regulation", "Financial Stability", ["Financial Stability", "Speeches", "Media Releases"], 0.97, "https://www.rba.gov.au"),
            SourceDefinition("cfr", "Council of Financial Regulators", "Australian Regulators", "rss", "https://www.cfr.gov.au/rss.xml", "Regulation", "Financial Stability", ["Financial Stability", "Operational Resilience", "Consultation Papers"], 0.97, "https://www.cfr.gov.au"),
            SourceDefinition("home-affairs", "Department of Home Affairs", "Australian Regulators", "rss", "https://www.homeaffairs.gov.au/rss.xml", "Regulation", "Critical Infrastructure", ["Critical Infrastructure", "Cyber Advisories", "Media Releases"], 0.96, "https://www.homeaffairs.gov.au"),
        ],
        "global_standards": [
            SourceDefinition("nist", "NIST", "Global Standards", "rss", "https://www.nist.gov/news-events/news/feed", "Regulation", "NIST", ["Framework updates", "AI security guidance", "Identity security"], 0.99, "https://www.nist.gov"),
            SourceDefinition("cisa", "CISA", "Global Standards", "rss", "https://www.cisa.gov/news-events/cybersecurity-advisories/feed", "Regulation", "CISA", ["Zero Trust guidance", "Supply chain security", "Cyber advisories"], 0.99, "https://www.cisa.gov"),
            SourceDefinition("mitre", "MITRE", "Global Standards", "rss", "https://www.mitre.org/news-insights/rss.xml", "Regulation", "MITRE", ["ATT&CK updates", "Framework updates"], 0.98, "https://www.mitre.org"),
            SourceDefinition("cis", "CIS", "Global Standards", "rss", "https://www.cisecurity.org/insights/blog/rss.xml", "Regulation", "CIS", ["Control updates", "Benchmarks", "Zero Trust guidance"], 0.97, "https://www.cisecurity.org"),
            SourceDefinition("owasp", "OWASP", "Global Standards", "rss", "https://owasp.org/feed.xml", "Regulation", "OWASP", ["AI security guidance", "Application security controls"], 0.97, "https://owasp.org"),
            SourceDefinition("enisa", "ENISA", "Global Standards", "rss", "https://www.enisa.europa.eu/rss.xml", "Regulation", "ENISA", ["EU guidance", "Supply chain security", "Zero Trust guidance"], 0.97, "https://www.enisa.europa.eu"),
            SourceDefinition("cloud-security-alliance", "Cloud Security Alliance", "Global Standards", "rss", "https://cloudsecurityalliance.org/articles/rss.xml", "Regulation", "CSA", ["Cloud frameworks", "AI governance", "Identity security"], 0.95, "https://cloudsecurityalliance.org"),
            SourceDefinition("first", "FIRST", "Global Standards", "rss", "https://www.first.org/newsroom/rss.xml", "Regulation", "FIRST", ["Incident response standards", "Threat intel sharing"], 0.95, "https://www.first.org"),
            SourceDefinition("iso", "ISO public updates", "Global Standards", "rss", "https://www.iso.org/contents/news.rss", "Regulation", "ISO", ["ISO updates", "Control updates", "Governance guidance"], 0.95, "https://www.iso.org"),
        ],
        "threat_intelligence": [
            SourceDefinition("google-threat-intel", "Google Threat Intelligence", "Threat Intelligence", "rss", "https://cloud.google.com/blog/topics/threat-intelligence/rss", "Threat", "Threat Intel", ["Campaigns", "IOCs", "Threat actor behavior"], 0.96, "https://cloud.google.com/security"),
            SourceDefinition("microsoft-threat-intel", "Microsoft Threat Intelligence", "Threat Intelligence", "rss", "https://www.microsoft.com/en-us/security/blog/feed/", "Threat", "Threat Intel", ["Campaigns", "Threat actor behavior", "Defender guidance"], 0.96, "https://www.microsoft.com/security"),
            SourceDefinition("cisco-talos", "Cisco Talos", "Threat Intelligence", "rss", "https://blog.talosintelligence.com/feeds/posts/default", "Threat", "Threat Intel", ["Malware", "Threat actor behavior", "Exploits"], 0.95, "https://blog.talosintelligence.com"),
            SourceDefinition("mandiant", "Mandiant", "Threat Intelligence", "rss", "https://www.mandiant.com/resources/blog/rss.xml", "Threat", "Threat Intel", ["Campaigns", "Incident response", "Threat actor behavior"], 0.95, "https://www.mandiant.com"),
            SourceDefinition("unit42", "Unit 42", "Threat Intelligence", "rss", "https://unit42.paloaltonetworks.com/feed/", "Threat", "Threat Intel", ["Campaigns", "Ransomware", "Cloud attacks"], 0.95, "https://unit42.paloaltonetworks.com"),
            SourceDefinition("recorded-future", "Recorded Future", "Threat Intelligence", "rss", "https://www.recordedfuture.com/feed", "Threat", "Threat Intel", ["Threat actor behavior", "Geopolitical cyber risk"], 0.94, "https://www.recordedfuture.com"),
            SourceDefinition("sophos-xops", "Sophos X-Ops", "Threat Intelligence", "rss", "https://news.sophos.com/en-us/category/threat-research/feed/", "Threat", "Threat Intel", ["Malware", "Ransomware", "Defensive guidance"], 0.93, "https://news.sophos.com"),
            SourceDefinition("red-canary", "Red Canary", "Threat Intelligence", "rss", "https://redcanary.com/blog/feed/", "Threat", "Threat Intel", ["Detection engineering", "Threat trends"], 0.93, "https://redcanary.com"),
            SourceDefinition("elastic-security-labs", "Elastic Security Labs", "Threat Intelligence", "rss", "https://www.elastic.co/security-labs/rss", "Threat", "Threat Intel", ["Threat research", "Detection analytics"], 0.93, "https://www.elastic.co/security-labs"),
            SourceDefinition("secureworks-ctu", "Secureworks CTU", "Threat Intelligence", "rss", "https://www.secureworks.com/rss?feed=threat-intelligence", "Threat", "Threat Intel", ["Threat actor behavior", "Campaign updates"], 0.93, "https://www.secureworks.com"),
        ],
        "identity_security": [
            SourceDefinition("nist-identity", "NIST Identity", "Identity Security", "rss", "https://www.nist.gov/itl/applied-cybersecurity/nice/news/feed", "Identity", "Identity Governance", ["Identity Governance", "Authentication", "Authorization", "Zero Trust Identity"], 0.96, "https://www.nist.gov"),
            SourceDefinition("fido", "FIDO Alliance", "Identity Security", "rss", "https://fidoalliance.org/feed/", "Identity", "Passkeys & FIDO", ["Passkeys", "FIDO", "Authentication"], 0.96, "https://fidoalliance.org"),
            SourceDefinition("openid", "OpenID Foundation", "Identity Security", "rss", "https://openid.net/feed/", "Identity", "OAuth/OIDC", ["OAuth", "OIDC", "SCIM", "Identity Fabric"], 0.95, "https://openid.net"),
            SourceDefinition("scim", "SCIM Working Group", "Identity Security", "rss", "https://scim.cloud/feed", "Identity", "SCIM", ["SCIM", "Identity Provisioning", "IGA"], 0.92, "https://scim.cloud"),
        ],
        "ai_security": [
            SourceDefinition("nist-ai", "NIST AI", "AI Security", "rss", "https://www.nist.gov/artificial-intelligence/news-events/feed", "AI Security", "AI Governance", ["AI Governance", "Responsible AI", "Model Security"], 0.97, "https://www.nist.gov/artificial-intelligence"),
            SourceDefinition("owasp-llm", "OWASP AI Security", "AI Security", "rss", "https://owasp.org/www-project-top-10-for-large-language-model-applications/feed.xml", "AI Security", "LLM Security", ["LLM Security", "Prompt Injection", "Model Security"], 0.96, "https://owasp.org"),
            SourceDefinition("mcp", "Model Context Protocol", "AI Security", "rss", "https://modelcontextprotocol.io/feed.xml", "AI Security", "Model Context Protocol", ["MCP", "Agentic AI", "Autonomous Agents"], 0.94, "https://modelcontextprotocol.io"),
            SourceDefinition("cisa-ai", "CISA AI Security", "AI Security", "rss", "https://www.cisa.gov/topics/artificial-intelligence/rss.xml", "AI Security", "AI Security", ["AI Security", "Responsible AI", "Governance"], 0.96, "https://www.cisa.gov"),
        ],
        "independent_journalism": [
            SourceDefinition("krebs", "KrebsOnSecurity", "Independent Security Journalism", "rss", "https://krebsonsecurity.com/feed/", "Threat", "Independent Journalism", ["Independent reporting", "Investigations", "Breach analysis"], 0.92, "https://krebsonsecurity.com"),
            SourceDefinition("bleepingcomputer", "BleepingComputer", "Independent Security Journalism", "rss", "https://www.bleepingcomputer.com/feed/", "Threat", "Independent Journalism", ["Incident reporting", "Vulnerability coverage"], 0.9, "https://www.bleepingcomputer.com"),
            SourceDefinition("dark-reading", "Dark Reading", "Independent Security Journalism", "rss", "https://www.darkreading.com/rss.xml", "Threat", "Independent Journalism", ["Industry coverage", "Threat reporting"], 0.9, "https://www.darkreading.com"),
            SourceDefinition("securityweek", "SecurityWeek", "Independent Security Journalism", "rss", "https://feeds.feedburner.com/securityweek?format=xml", "Threat", "Independent Journalism", ["Industry coverage", "Threat reporting"], 0.9, "https://www.securityweek.com"),
            SourceDefinition("the-record", "The Record", "Independent Security Journalism", "rss", "https://therecord.media/feed", "Threat", "Independent Journalism", ["Investigative reporting", "Policy coverage"], 0.9, "https://therecord.media"),
            SourceDefinition("help-net-security", "Help Net Security", "Independent Security Journalism", "rss", "https://www.helpnetsecurity.com/feed/", "Threat", "Independent Journalism", ["Industry reporting", "Research coverage"], 0.89, "https://www.helpnetsecurity.com"),
            SourceDefinition("cyberscoop", "CyberScoop", "Independent Security Journalism", "rss", "https://cyberscoop.com/feed/", "Threat", "Independent Journalism", ["Policy coverage", "Cyber operations"], 0.89, "https://cyberscoop.com"),
            SourceDefinition("cso-online", "CSO Online", "Independent Security Journalism", "rss", "https://www.csoonline.com/feed", "Threat", "Independent Journalism", ["Leadership coverage", "Enterprise security"], 0.88, "https://www.csoonline.com"),
            SourceDefinition("sc-media", "SC Media", "Independent Security Journalism", "rss", "https://www.scworld.com/feed", "Threat", "Independent Journalism", ["Threat reporting", "Technology security"], 0.88, "https://www.scworld.com"),
            SourceDefinition("infosecurity-magazine", "Infosecurity Magazine", "Independent Security Journalism", "rss", "https://www.infosecurity-magazine.com/rss/news/", "Threat", "Independent Journalism", ["Threat reporting", "Regulation coverage"], 0.88, "https://www.infosecurity-magazine.com"),
        ],
    }


def flattened_sources() -> List[SourceDefinition]:
    sources: List[SourceDefinition] = []
    for group_sources in source_registry().values():
        sources.extend(group_sources)
    return sources
