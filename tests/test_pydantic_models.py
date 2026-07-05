from backend.models.intelligence_schemas import (
    ExecutiveSummary,
    NewsArticle,
    RegulationUpdate,
    ResearchPaper,
    RiskAssessment,
    Threat,
    Trend,
    VendorUpdate,
)


def test_models_validate_and_serialize():
    article = NewsArticle(
        title="Critical zero-day affecting enterprise VPN appliances",
        summary="A vulnerability is being exploited in the wild.",
        source="CISA",
        category="Cybersecurity",
        severity="high",
        url="https://example.com/article",
    )
    assert article.title.startswith("Critical")
    assert article.model_dump()["source"] == "CISA"

    vendor = VendorUpdate(
        vendor="Acme Corp",
        title="Patch released",
        summary="A patch is now available for affected products.",
        severity="high",
        affected_products=["Gateway X"],
        advisory_url="https://example.com/advisory",
    )
    assert vendor.model_dump()["vendor"] == "Acme Corp"

    paper = ResearchPaper(
        title="Research on enterprise identity resilience",
        authors=["A. Smith"],
        publication="IEEE",
        summary="The paper discusses important identity guidance.",
        relevance_score=0.92,
    )
    assert paper.relevance_score == 0.92

    threat = Threat(
        name="Northwind Ransomware",
        description="A ransomware family targeting remote access tools.",
        threat_type="ransomware",
        severity="critical",
        indicators=["T1486"],
    )
    assert threat.severity == "critical"

    regulation = RegulationUpdate(
        jurisdiction="EU",
        title="New reporting requirements",
        summary="Organizations must report major incidents within 24 hours.",
        effective_date="2026-08-01T00:00:00",
        authority="ENISA",
        impact="Requires reporting and evidence preservation.",
    )
    assert regulation.authority == "ENISA"

    executive_summary = ExecutiveSummary(
        headline="Elevated exposure from active exploitation",
        summary="The organization faces elevated risk from active exploitation of VPN products.",
        key_risks=["Credential theft"],
        top_priorities=["Patch immediately"],
        confidence="high",
    )
    assert executive_summary.confidence == "high"

    trend = Trend(
        name="Increase in identity-based attacks",
        description="Identity attacks continue to grow in volume and sophistication.",
        direction="up",
        confidence="high",
    )
    assert trend.direction == "up"

    assessment = RiskAssessment(
        subject="Third-party remote access",
        summary="Excessive access rights create elevated exposure.",
        severity="high",
        likelihood="medium",
        impact="high",
        recommended_actions=["Review access"],
    )
    assert assessment.recommended_actions[0] == "Review access"
