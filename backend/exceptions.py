"""Custom exception types for the backend."""


class ArticleServiceError(Exception):
    """Raised when article persistence or retrieval fails."""


class CollectorError(Exception):
    """Raised when the daily collector cannot ingest content."""
