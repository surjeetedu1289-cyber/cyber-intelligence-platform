from pathlib import Path

from backend.collectors.base import BaseCollector
from backend.collectors.orchestrator import CollectorOrchestrator
from backend.collectors.registry import build_default_collectors
from backend.collectors.rss import RSSCollector


class FakeCollector(BaseCollector):
    def __init__(self):
        super().__init__(name="fake", source_name="Fake Source", category="Threat")

    def fetch(self):
        return [{
            "title": "Example advisory",
            "author": "Jane Doe",
            "published_at": "2026-07-05T10:00:00Z",
            "url": "https://example.com/advisory",
            "summary": "A test advisory",
        }]

    def parse(self, payload):
        return payload


def test_rss_collector_normalizes_feed_items(monkeypatch):
    class FakeResponse:
        def __init__(self, text):
            self.text = text
            self.status_code = 200

        def raise_for_status(self):
            return None

    payload = """<?xml version=\"1.0\"?>
    <rss version=\"2.0\"><channel><title>Example</title><item><title>New advisory</title><link>https://example.com/item</link><description>Detailed summary</description><pubDate>Sat, 05 Jul 2026 10:00:00 GMT</pubDate><author>Jane</author></item></channel></rss>"""
    monkeypatch.setattr("backend.collectors.rss.requests.get", lambda *args, **kwargs: FakeResponse(payload))

    collector = RSSCollector("rss-demo", "RSS Demo", "Threat", "https://example.com/feed")
    articles = collector.collect()

    assert articles[0]["title"] == "New advisory"
    assert articles[0]["source"] == "RSS Demo"
    assert articles[0]["category"] == "Threat"


def test_orchestrator_deduplicates_and_writes_json(tmp_path):
    orchestrator = CollectorOrchestrator([FakeCollector(), FakeCollector()], output_dir=tmp_path)
    result = orchestrator.run()

    assert len(result["articles"]) == 1
    assert (tmp_path / "fake.json").exists()
    assert (tmp_path / "combined.json").exists()


def test_default_registry_contains_all_requested_sources():
    collectors = build_default_collectors()
    names = {collector.name for collector in collectors}
    expected = {
        "microsoft-security",
        "microsoft-entra",
        "sailpoint",
        "cyberark",
        "okta",
        "pingidentity",
        "saviynt",
        "beyondtrust",
        "aws-security",
        "google-cloud-security",
        "cisa",
        "nist",
        "krebs",
        "the-hacker-news",
        "bleepingcomputer",
        "dark-reading",
        "help-net-security",
        "securityweek",
        "arxiv",
    }
    assert expected.issubset(names)
