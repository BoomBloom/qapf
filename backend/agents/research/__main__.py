"""Manual verification runner: python -m agents.research"""

import json
import logging
import os

from .pipeline import ResearchIngestionPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    github_token = os.getenv("GITHUB_TOKEN")
    pipeline = ResearchIngestionPipeline(github_token=github_token)

    target_topics = ["co-integration", "statistical arbitrage", "optimal execution", "order book"]
    results = pipeline.run(topics=target_topics, max_results=3, days_back=90)

    print(f"\n=== {len(results)} papers found ===\n")
    print(json.dumps([r.model_dump() for r in results], indent=2))


if __name__ == "__main__":
    main()
