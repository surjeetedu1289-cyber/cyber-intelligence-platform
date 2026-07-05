from __future__ import annotations

from typing import Any, Dict, List

import requests

from backend.collectors.base import BaseCollector


class APICollector(BaseCollector):
    """Collector for JSON-based official APIs."""

    def __init__(self, name: str, source_name: str, category: str, endpoint: str, items_key: str = "items", metadata: Dict[str, Any] | None = None):
        super().__init__(name=name, source_name=source_name, category=category, endpoint=endpoint, metadata=metadata)
        self.items_key = items_key

    def fetch(self) -> List[Dict[str, Any]]:
        response = requests.get(self.endpoint, timeout=20)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            return payload.get(self.items_key, [])
        return payload

    def parse(self, payload: Any) -> List[Dict[str, Any]]:
        return payload
