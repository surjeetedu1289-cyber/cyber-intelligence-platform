from __future__ import annotations

from typing import Any, Dict, List

from backend.collectors.base import BaseCollector


class VendorBlogCollector(BaseCollector):
    """Collector for vendor blogs and product updates."""

    def parse(self, payload: Any) -> List[Dict[str, Any]]:
        return payload


class SecurityAdvisoryCollector(BaseCollector):
    """Collector for security advisories and incident reports."""

    def parse(self, payload: Any) -> List[Dict[str, Any]]:
        return payload
