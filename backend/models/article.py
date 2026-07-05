from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func

from backend.database.db import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, unique=True, index=True)
    summary = Column(Text, nullable=True)
    source = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=True)
    url = Column(String(500), nullable=False, unique=True)
    published_at = Column(DateTime(timezone=False), nullable=True)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
