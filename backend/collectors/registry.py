from __future__ import annotations

from pathlib import Path
from typing import List

from backend.collectors.api import APICollector
from backend.collectors.base import BaseCollector
from backend.collectors.rss import RSSCollector
from backend.collectors.source_registry import flattened_sources


def build_default_collectors(output_dir: Path | None = None) -> List[BaseCollector]:
    collectors: List[BaseCollector] = []
    for source in flattened_sources():
        if not source.endpoint:
            continue
        metadata = {
            "source_group": source.group,
            "source_subcategory": source.subcategory,
            "monitors": source.monitors,
            "credibility_weight": source.credibility_weight,
            "official_url": source.official_url,
        }
        if source.collector_type == "api":
            collectors.append(APICollector(source.id, source.name, source.category, source.endpoint, metadata=metadata))
        else:
            collectors.append(RSSCollector(source.id, source.name, source.category, source.endpoint, metadata=metadata))
    return collectors
