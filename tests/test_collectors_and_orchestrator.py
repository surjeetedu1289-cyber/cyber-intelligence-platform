from pathlib import Path
from unittest.mock import Mock, patch

from backend.collectors.daily_collector import collect_articles, sample_articles
from backend.pipeline.daily_pipeline import (
    _build_sections,
    _categorize_article,
    _collect_inputs,
    _normalize_articles,
    _run_ai_research,
    run_daily_pipeline,
)


def test_sample_articles_fixture_returns_data():
    articles = sample_articles()
    assert len(articles) >= 3
    assert articles[0]["title"]


def test_collect_articles_persists_sample_records(monkeypatch):
    monkeypatch.setattr("backend.collectors.daily_collector.save_article", lambda db, payload: Mock(id=1, title=payload["title"], category=payload["category"], source=payload["source"]))
    results = collect_articles(max_retries=1)
    assert len(results) >= 1


def test_pipeline_helpers_process_articles(sample_articles):
    normalized = _normalize_articles(sample_articles)
    categorized = [_categorize_article(article) for article in normalized]
    assert len(normalized) == len(sample_articles)
    assert categorized[0]["category"] in {"Threat", "Identity", "AI Agents", "Vendor", "Regulation", "Research"}


def test_build_sections_creates_expected_sections(sample_articles):
    categorized = [_categorize_article(article) for article in sample_articles]
    sections = _build_sections(categorized, {"summary": "brief", "evidence": []})
    assert sections["executive_summary"]["headline"]
    assert sections["top_ten_news"]
    assert sections["vendor_updates"] or sections["regulation_updates"] or sections["threat_intelligence"]


def test_run_ai_research_falls_back_without_client(monkeypatch):
    monkeypatch.setattr("backend.pipeline.daily_pipeline.ClaudeClient", lambda: (_ for _ in ()).throw(RuntimeError("no client")))
    result = _run_ai_research([{"title": "Threat article"}])
    assert "summary" in result


def test_collect_inputs_handles_failed_collectors(monkeypatch):
    def broken_collector():
        raise RuntimeError("boom")

    monkeypatch.setattr("backend.pipeline.daily_pipeline.COLLECTORS", [broken_collector])
    result = _collect_inputs()
    assert isinstance(result, list)
    assert result is not None


def test_run_daily_pipeline_writes_outputs(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.pipeline.daily_pipeline.DATA_DIR", tmp_path)
    monkeypatch.setattr("backend.pipeline.daily_pipeline.COLLECTORS", [lambda: [{"title": "Example", "summary": "Example summary", "source": "Test", "category": "Threat", "severity": "High", "url": "https://example.com"}]])
    result = run_daily_pipeline()
    assert result["executive_summary"]["headline"]
    assert (tmp_path / "daily" / "executive_summary.json").exists()
