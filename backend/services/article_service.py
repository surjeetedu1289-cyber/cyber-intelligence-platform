from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.db import Base, SessionLocal, engine
from backend.exceptions import ArticleServiceError
from backend.logging_config import LOGGER
from backend.models.article import Article


def initialize_storage() -> None:
    """Create database tables if they are missing."""
    Base.metadata.create_all(bind=engine)


def _coerce_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            LOGGER.warning("Could not parse datetime value: %s", value)
            return None
    return None


def save_article(db: Session, payload: Dict[str, Any]) -> Article:
    """Persist a new article if it does not already exist by URL."""
    try:
        existing = db.query(Article).filter(Article.url == payload["url"]).first()
        if existing:
            return existing

        article = Article(
            title=payload["title"],
            summary=payload.get("summary"),
            source=payload.get("source", "Unknown"),
            category=payload.get("category", "General"),
            severity=payload.get("severity"),
            url=payload["url"],
            published_at=_coerce_datetime(payload.get("published_at")),
            tags=payload.get("tags", []),
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        LOGGER.info("Saved article: %s", article.title)
        return article
    except SQLAlchemyError as exc:
        db.rollback()
        LOGGER.exception("Failed to save article: %s", exc)
        raise ArticleServiceError("Unable to persist article") from exc


def get_articles(
    db: Optional[Session] = None,
    limit: int = 50,
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Article]:
    """Retrieve articles with optional category and text search filters."""
    session = db or SessionLocal()
    try:
        query = session.query(Article)
        if category:
            query = query.filter(Article.category == category)
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                (Article.title.ilike(search_term))
                | (Article.summary.ilike(search_term))
                | (Article.source.ilike(search_term))
            )
        return query.order_by(Article.created_at.desc()).limit(limit).all()
    except SQLAlchemyError as exc:
        LOGGER.exception("Failed to fetch articles: %s", exc)
        raise ArticleServiceError("Unable to fetch articles") from exc


def get_dashboard_stats(db: Optional[Session] = None) -> Dict[str, Any]:
    """Compute dashboard statistics from the article repository."""
    session = db or SessionLocal()
    try:
        total_articles = session.query(Article).count()
        categories = [row[0] for row in session.query(Article.category).distinct().all()]
        severities = [row[0] for row in session.query(Article.severity).distinct().all() if row[0]]
        return {
            "total_articles": total_articles,
            "categories": categories,
            "severities": severities,
        }
    except SQLAlchemyError as exc:
        LOGGER.exception("Failed to build dashboard stats: %s", exc)
        raise ArticleServiceError("Unable to compute dashboard stats") from exc


initialize_storage()
