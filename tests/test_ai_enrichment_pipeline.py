import json
from datetime import date

from backend.pipeline.ai_enrichment_pipeline import run_ai_enrichment_pipeline


def test_ai_enrichment_pipeline_writes_dated_output(tmp_path, monkeypatch):
    combined_payload = [
        {
            "title": "CISA warns of active exploitation",
            "summary": "Threats are actively exploiting enterprise VPN assets.",
            "url": "https://example.com/cisa-threat",
            "category": "Threat",
            "source": "CISA",
            "severity": "High",
        },
        {
            "title": "Identity governance update",
            "summary": "IAM teams are updating access certification controls.",
            "url": "https://example.com/iam-update",
            "category": "Identity",
            "source": "Vendor",
            "severity": "Medium",
        },
    ]
    (tmp_path / "combined.json").write_text(json.dumps(combined_payload), encoding="utf-8")

    class FakeClaudeClient:
        def send_prompt(self, prompt, system_prompt=None):
            return json.dumps(
                {
                    "executive_summary": "Executive summary",
                    "business_impact": "Business impact",
                    "iam_impact": "IAM impact",
                    "risk_level": "high",
                    "recommended_actions": ["Action 1", "Action 2"],
                    "confidence_score": 0.9,
                    "tags": ["identity", "threat"],
                }
            )

    monkeypatch.setattr("backend.pipeline.ai_enrichment_pipeline.ClaudeClient", FakeClaudeClient)

    run_day = date(2026, 7, 5)
    payload = run_ai_enrichment_pipeline(input_dir=tmp_path, output_dir=tmp_path, run_date=run_day)

    output_file = tmp_path / "2026-07-05.json"
    assert output_file.exists()
    assert payload["date"] == "2026-07-05"
    assert payload["article_count"] == 2
    assert len(payload["agents"]) == 8
    for item in payload["agents"]:
        assert "executive_summary" in item
        assert "business_impact" in item
        assert "iam_impact" in item
        assert "risk_level" in item
        assert "recommended_actions" in item
        assert "confidence_score" in item
        assert "tags" in item
