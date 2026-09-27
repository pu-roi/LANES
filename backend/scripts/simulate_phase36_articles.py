"""Read-only Phase 36 simulation using the existing news and extraction services.

Fetches three historical Metro Manila articles from registered publisher domains,
then runs the same bounded article fetch, deterministic extraction, PSGC-backed
location ranking, Pasig history lookup (when applicable), and action evaluator
used by LANES. No database session, LLM request, map alert, or zone write occurs.

Usage from backend/:
    python scripts/simulate_phase36_articles.py --output ../data/phase36_article_simulation_results.json
"""

from __future__ import annotations

import asyncio
import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.hybrid_extraction_service import HybridExtractionService
from app.services.news_discovery_service import fetch_article_text
from app.services.news_sources import load_news_sources


PHT = ZoneInfo("Asia/Manila")
CASES = (
    (
        "philstar-sep-09",
        "https://qa.philstar.com/headlines/2026/09/09/2555106/list-flooded-metro-manila-areas-september-9/amp/",
        "LIST: Flooded Metro Manila areas on September 9",
        datetime(2026, 9, 9, 17, 3, tzinfo=PHT),
    ),
    (
        "pna-aug-17",
        "https://www.pna.gov.ph/articles/1282103",
        "MMDA deploys flood teams as habagat rains near Ondoy level",
        datetime(2026, 8, 17, 20, 40, tzinfo=PHT),
    ),
    (
        "pna-aug-08",
        "https://www.pna.gov.ph/articles/1281410",
        "Flooding reported in NCR but water subsiding quick",
        datetime(2026, 8, 8, 19, 43, tzinfo=PHT),
    ),
)


async def simulate() -> list[dict]:
    sources = load_news_sources()
    hybrid = HybridExtractionService()
    results = []
    for case_number, (case_id, url, title, published_at) in enumerate(CASES, start=1):
        source = next((item for item in sources if item.accepts_article_host(httpx.URL(url).host)), None)
        if source is None:
            results.append({"id": case_id, "url": url, "error": "Publisher domain not registered"})
            continue
        with httpx.Client(timeout=25) as client:
            article_text, article_error = fetch_article_text(source, url, client)
        if article_error or not article_text:
            results.append({"id": case_id, "url": url, "error": article_error or "No full article text"})
            continue
        article = NewsArticleExtractorInput(
            article_id=9000 + case_number,
            canonical_url=url,
            publisher=source.publisher,
            title=title,
            article_text=article_text,
            published_at=published_at,
        )
        extraction = await hybrid.extract_hybrid(article, mode="rules_only")
        claims = [
            {
                "place": claim.raw_place_name,
                "place_type": claim.place_type,
                "city": claim.canonical_city,
                "barangay": claim.canonical_barangay,
                "road_segment": claim.road_segment_raw,
                "local_area": claim.local_area_raw,
                "depth_raw": claim.depth_raw,
                "depth_canonical": claim.depth_canonical,
                "passability": claim.road_passability,
                "condition": claim.condition,
                "event_time": claim.event_time_raw,
                "event_time_kind": claim.event_time_kind,
                "action": claim.action_type,
                "geometry_provenance": claim.ranked_location.geometry_provenance if claim.ranked_location else None,
                "uncertainty": claim.uncertainty_reasons,
            }
            for claim in extraction.claims
        ]
        results.append({
            "id": case_id,
            "url": url,
            "publisher": source.publisher,
            "publication_time": published_at.isoformat(),
            "article_chars": len(article_text),
            "metadata_only": extraction.is_metadata_only,
            "claim_count": len(claims),
            "place_types": dict(Counter(claim["place_type"] for claim in claims)),
            "actions": dict(Counter(claim["action"] for claim in claims)),
            "claims": claims,
        })
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write derived claim fields as UTF-8 JSON")
    args = parser.parse_args()
    serialized = json.dumps(asyncio.run(simulate()), ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(serialized + "\n", encoding="utf-8")
        print(f"Wrote derived claim fields to {args.output}")
    else:
        print(serialized)
