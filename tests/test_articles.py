from backend.services.article_service import initialize_storage, save_article, get_articles, get_dashboard_stats
from backend.database.db import SessionLocal
from backend.models.article import Article


def test_article_deduplication_and_dashboard_stats():
    initialize_storage()
    db = SessionLocal()
    try:
        first = save_article(
            db,
            {
                "title": "Critical vulnerability disclosed in firewall appliance",
                "summary": "A severe flaw affects a popular firewall vendor.",
                "source": "CISA",
                "category": "Cybersecurity",
                "severity": "High",
                "url": "https://example.com/critical-vuln",
                "published_at": "2026-07-04T08:00:00",
                "tags": ["vulnerability", "firewall"],
            },
        )
        second = save_article(
            db,
            {
                "title": "Critical vulnerability disclosed in firewall appliance",
                "summary": "A severe flaw affects a popular firewall vendor.",
                "source": "CISA",
                "category": "Cybersecurity",
                "severity": "High",
                "url": "https://example.com/critical-vuln",
                "published_at": "2026-07-04T08:00:00",
                "tags": ["vulnerability", "firewall"],
            },
        )

        assert first.id == second.id
        assert db.query(Article).count() >= 1

        articles = get_articles(db=db, limit=10)
        assert len(articles) >= 1

        stats = get_dashboard_stats(db=db)
        assert stats["total_articles"] >= 1
        assert "Cybersecurity" in stats["categories"]
    finally:
        db.close()
