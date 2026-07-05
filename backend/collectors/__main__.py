from pathlib import Path

from backend.collectors.orchestrator import CollectorOrchestrator
from backend.collectors.registry import build_default_collectors


if __name__ == "__main__":
    output_dir = Path("data/daily")
    orchestrator = CollectorOrchestrator(build_default_collectors(output_dir), output_dir=output_dir)
    result = orchestrator.run()
    print(f"Collected {len(result['articles'])} articles from {result['collector_count']} collectors")
