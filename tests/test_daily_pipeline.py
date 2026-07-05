from pathlib import Path

from backend.pipeline.daily_pipeline import run_daily_pipeline


def test_run_daily_pipeline_writes_expected_outputs(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.pipeline.daily_pipeline.DATA_DIR", tmp_path)

    result = run_daily_pipeline()

    assert result["executive_summary"]["headline"]
    assert len(result["top_ten_news"]) >= 1
    assert len(result["trending_topics"]) >= 1
    assert len(result["vendor_updates"]) >= 1
    assert len(result["regulation_updates"]) >= 1
    assert len(result["threat_intelligence"]) >= 1
    assert len(result["identity_news"]) >= 1
    assert len(result["machine_identity"]) >= 1
    assert len(result["ai_agents"]) >= 1
    assert len(result["research_papers"]) >= 1

    expected_files = [
        tmp_path / "daily" / "executive_summary.json",
        tmp_path / "daily" / "top_ten_news.json",
        tmp_path / "daily" / "trending_topics.json",
        tmp_path / "daily" / "vendor_updates.json",
        tmp_path / "daily" / "regulation_updates.json",
        tmp_path / "daily" / "threat_intelligence.json",
        tmp_path / "daily" / "identity_news.json",
        tmp_path / "daily" / "machine_identity.json",
        tmp_path / "daily" / "ai_agents.json",
        tmp_path / "daily" / "research_papers.json",
        tmp_path / "daily" / "collection_summary.json",
        tmp_path / "daily" / "workflow_diagram.md",
    ]
    for path in expected_files:
        assert path.exists(), f"Expected {path} to exist"
