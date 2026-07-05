"""Pydantic models for cyber intelligence domain objects.

These models provide validation, type safety, documentation, and JSON-ready
serialization for the core entities used by the platform.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Severity(str, Enum):
    """Risk severity values used across intelligence records."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Confidence(str, Enum):
    """Confidence values for analytical findings."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class NewsArticle(BaseModel):
    """Represents a news item or article relevant to cyber intelligence."""

    id: Optional[str] = Field(default=None, description="Unique article identifier")
    title: str = Field(..., min_length=5, max_length=300, description="Article title")
    summary: str = Field(..., min_length=10, max_length=4000, description="Article summary")
    source: str = Field(..., min_length=2, max_length=200, description="Article source")
    category: str = Field(..., min_length=2, max_length=100, description="Article category")
    severity: Severity = Field(default=Severity.MEDIUM, description="Severity level")
    url: HttpUrl = Field(..., description="Article URL")
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Publication timestamp")
    tags: List[str] = Field(default_factory=list, description="Article tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Critical zero-day affecting enterprise VPN appliances",
                "summary": "A new vulnerability is being actively exploited in the wild.",
                "source": "CISA",
                "category": "Cybersecurity",
                "severity": "high",
                "url": "https://example.com/article",
                "published_at": "2026-07-04T08:30:00",
                "tags": ["vulnerability", "vpn"],
                "metadata": {"feed": "cisa"},
            }
        }
    }


class VendorUpdate(BaseModel):
    """Represents a security update or advisory issued by a vendor."""

    id: Optional[str] = Field(default=None)
    vendor: str = Field(..., min_length=2, max_length=200)
    title: str = Field(..., min_length=5, max_length=300)
    summary: str = Field(..., min_length=10, max_length=4000)
    severity: Severity = Field(default=Severity.MEDIUM)
    affected_products: List[str] = Field(default_factory=list)
    advisory_url: HttpUrl = Field(...)
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    remediation: Optional[str] = Field(default=None, max_length=2000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "vendor": "Acme Corp",
                "title": "Critical patch release for gateway appliances",
                "summary": "Acme released a patch for a vulnerability affecting multiple appliance versions.",
                "severity": "high",
                "affected_products": ["Gateway X", "Gateway Y"],
                "advisory_url": "https://example.com/advisory",
                "published_at": "2026-07-04T09:00:00",
                "remediation": "Apply the latest security update immediately.",
            }
        }
    }


class ResearchPaper(BaseModel):
    """Represents a research paper or technical report relevant to cybersecurity."""

    id: Optional[str] = Field(default=None)
    title: str = Field(..., min_length=5, max_length=300)
    authors: List[str] = Field(default_factory=list)
    publication: str = Field(..., min_length=2, max_length=200)
    summary: str = Field(..., min_length=10, max_length=5000)
    doi: Optional[str] = Field(default=None, max_length=200)
    url: Optional[HttpUrl] = Field(default=None)
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Evaluating the resilience of enterprise identity systems",
                "authors": ["A. Smith", "B. Jones"],
                "publication": "IEEE Security & Privacy",
                "summary": "The paper evaluates how identity systems respond to modern attack techniques.",
                "doi": "10.1000/example",
                "url": "https://example.com/paper",
                "published_at": "2026-07-04T10:00:00",
                "relevance_score": 0.91,
            }
        }
    }


class Threat(BaseModel):
    """Represents a threat actor, campaign, or threat pattern."""

    id: Optional[str] = Field(default=None)
    name: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., min_length=10, max_length=4000)
    threat_type: str = Field(..., min_length=2, max_length=100)
    severity: Severity = Field(default=Severity.MEDIUM)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    indicators: List[str] = Field(default_factory=list)
    mitigation: Optional[str] = Field(default=None, max_length=2000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Northwind Ransomware",
                "description": "A ransomware family targeting remote access infrastructure.",
                "threat_type": "ransomware",
                "severity": "high",
                "observed_at": "2026-07-04T11:00:00",
                "indicators": ["T1566", "T1486"],
                "mitigation": "Restrict remote access and ensure offline backups.",
            }
        }
    }


class RegulationUpdate(BaseModel):
    """Represents a new or updated regulation or compliance requirement."""

    id: Optional[str] = Field(default=None)
    jurisdiction: str = Field(..., min_length=2, max_length=200)
    title: str = Field(..., min_length=5, max_length=300)
    summary: str = Field(..., min_length=10, max_length=4000)
    effective_date: datetime = Field(...)
    authority: str = Field(..., min_length=2, max_length=200)
    impact: str = Field(..., min_length=5, max_length=2000)
    urgency: Severity = Field(default=Severity.MEDIUM)

    model_config = {
        "json_schema_extra": {
            "example": {
                "jurisdiction": "EU",
                "title": "New cybersecurity incident reporting requirements",
                "summary": "Organizations must report significant incidents within 24 hours.",
                "effective_date": "2026-08-01T00:00:00",
                "authority": "ENISA",
                "impact": "Mandatory reporting and evidence preservation obligations.",
                "urgency": "high",
            }
        }
    }


class ExecutiveSummary(BaseModel):
    """Represents an executive-ready summary of intelligence findings."""

    id: Optional[str] = Field(default=None)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    headline: str = Field(..., min_length=5, max_length=300)
    summary: str = Field(..., min_length=20, max_length=8000)
    key_risks: List[str] = Field(default_factory=list)
    top_priorities: List[str] = Field(default_factory=list)
    confidence: Confidence = Field(default=Confidence.MEDIUM)

    model_config = {
        "json_schema_extra": {
            "example": {
                "headline": "Elevated exposure from active exploitation of VPN appliances",
                "summary": "The organization faces elevated risk from active exploitation of widely used VPN platforms.",
                "key_risks": ["Credential theft", "Remote access abuse"],
                "top_priorities": ["Patch affected systems", "Review MFA coverage"],
                "confidence": "high",
            }
        }
    }


class Trend(BaseModel):
    """Represents a long-term trend observed in the intelligence landscape."""

    id: Optional[str] = Field(default=None)
    name: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., min_length=10, max_length=4000)
    direction: str = Field(..., pattern="^(up|down|stable)$")
    confidence: Confidence = Field(default=Confidence.MEDIUM)
    observed_since: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Increase in identity-based attacks",
                "description": "Threat actors are increasingly targeting identity systems and authentication workflows.",
                "direction": "up",
                "confidence": "high",
                "observed_since": "2026-01-01T00:00:00",
            }
        }
    }


class RiskAssessment(BaseModel):
    """Represents a structured risk assessment for a cybersecurity scenario."""

    id: Optional[str] = Field(default=None)
    subject: str = Field(..., min_length=2, max_length=300)
    summary: str = Field(..., min_length=10, max_length=4000)
    severity: Severity = Field(default=Severity.MEDIUM)
    likelihood: Severity = Field(default=Severity.MEDIUM)
    impact: Severity = Field(default=Severity.MEDIUM)
    residual_risk: Optional[str] = Field(default=None, max_length=2000)
    recommended_actions: List[str] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "subject": "Third-party access management",
                "summary": "Over-privileged third-party accounts create elevated exposure to unauthorized access.",
                "severity": "high",
                "likelihood": "medium",
                "impact": "high",
                "residual_risk": "Residual risk remains moderate after MFA enforcement.",
                "recommended_actions": ["Review service accounts", "Enforce least privilege"],
            }
        }
    }


class IntelligenceEnvelope(BaseModel):
    """Container for multiple intelligence objects in a single payload."""

    articles: List[NewsArticle] = Field(default_factory=list)
    vendor_updates: List[VendorUpdate] = Field(default_factory=list)
    research_papers: List[ResearchPaper] = Field(default_factory=list)
    threats: List[Threat] = Field(default_factory=list)
    regulations: List[RegulationUpdate] = Field(default_factory=list)
    executive_summaries: List[ExecutiveSummary] = Field(default_factory=list)
    trends: List[Trend] = Field(default_factory=list)
    risk_assessments: List[RiskAssessment] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "articles": [NewsArticle.model_json_schema()["example"]],
                "vendor_updates": [VendorUpdate.model_json_schema()["example"]],
            }
        }
    }
