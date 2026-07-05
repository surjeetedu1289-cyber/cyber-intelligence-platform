from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

from backend.collectors.base import BaseCollector
from backend.logging_config import LOGGER


class CollectorOrchestrator:
    """Coordinates collectors, deduplicates records, and writes JSON bundles."""

    def __init__(self, collectors: Sequence[BaseCollector], output_dir: Path | str | None = None):
        self.collectors = list(collectors)
        self.output_dir = Path(output_dir or "data/daily")

    def _deduplicate(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        deduped: List[Dict[str, Any]] = []
        for item in items:
            key = (item.get("title") or "", item.get("url") or "")
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def run(self) -> Dict[str, Any]:
        article_batches: List[Dict[str, Any]] = []
        for collector in self.collectors:
            try:
                collected = collector.collect()
                if collected:
                    article_batches.extend(collected)
                    collector.write_json(self.output_dir / f"{collector.name}.json", collected)
                    LOGGER.info("Collector %s produced %s items", collector.name, len(collected))
            except Exception as exc:  # pragma: no cover - defensive fallback
                LOGGER.exception("Collector %s failed during orchestrated run: %s", collector.name, exc)

        deduped = self._deduplicate(article_batches)
        (self.output_dir / "combined.json").write_text(json.dumps(deduped, indent=2), encoding="utf-8")
        return {"articles": deduped, "collector_count": len(self.collectors)}
