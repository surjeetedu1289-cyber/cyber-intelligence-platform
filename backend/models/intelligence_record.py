from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.sql import func

from backend.database.db import Base


class IntelligenceRecord(Base):
    """Normalized executive intelligence record for relational storage.

    This schema is intentionally SQLAlchemy-portable and works on SQLite
    and PostgreSQL-compatible databases.
    """

    __tablename__ = "intelligence_records"

    id = Column(Integer, primary_key=True, index=True)
    dedupe_key = Column(String(512), nullable=False, unique=True, index=True)
    title = Column(String(512), nullable=False)
    author = Column(String(255), nullable=True)
    source = Column(String(255), nullable=False, index=True)
    category = Column(String(120), nullable=True, index=True)
    subcategory = Column(String(120), nullable=True, index=True)
    country = Column(String(120), nullable=True, index=True)
    summary = Column(Text, nullable=True)
    executive_summary = Column(Text, nullable=True)
    technical_summary = Column(Text, nullable=True)
    business_impact = Column(Text, nullable=True)
    operational_impact = Column(Text, nullable=True)
    risk_rating = Column(String(32), nullable=True, index=True)
    confidence_score = Column(Float, nullable=True)
    url = Column(String(1200), nullable=True)
    published_at = Column(DateTime(timezone=False), nullable=True)

    industries = Column(JSON, default=list)
    frameworks = Column(JSON, default=list)
    technologies = Column(JSON, default=list)
    cves = Column(JSON, default=list)
    mitre_techniques = Column(JSON, default=list)
    mitre_tactics = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    quality_scoring = Column(JSON, default=dict)
    why_this_matters = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())
