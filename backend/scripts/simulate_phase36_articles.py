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
import re
import sys
import unicodedata
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
EXPECTED_SITES_PATH = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "phase36_expected_sites.json"


def _fold(value: object) -> str:
    """Compare factual labels despite punctuation, spacing, or diacritics."""
    decomposed = unicodedata.normalize("NFKD", str(value or "")).casefold()
    return re.sub(r"[^a-z0-9]", "", "".join(char for char in decomposed if not unicodedata.combining(char)))


def evaluate_expected_sites(results: list[dict], expected: dict) -> bool:
    """Match every cited site to a distinct extracted claim and check its facts."""
    all_matched = True
    for article in results:
        case = expected[article["id"]]
        source_matches = article.get("url") == case["source"] if "source" in case else True
        used_claims: set[int] = set()
        missing = []
        for site in case["sites"]:
            required = {**case.get("defaults", {}), **site}
            location = required.pop("location")
            match = next(
                (
                    index
                    for index, claim in enumerate(article.get("claims", []))
                    if index not in used_claims
                    and _fold(claim.get("road_segment") or claim.get("place")) == _fold(location)
                    and all(_fold(claim.get(field)) == _fold(value) for field, value in required.items())
                ),
                None,
            )
            if match is None:
                missing.append(required | {"location": location})
            else:
                used_claims.add(match)
        article["expected_site_count"] = len(case["sites"])
        article["matched_site_count"] = len(used_claims)
        article["missing_sites"] = missing
        all_matched = all_matched and source_matches and not missing and "error" not in article
    return all_matched and len(results) == len(expected) and {article["id"] for article in results} == set(expected)


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
    parser.add_argument("--check", action="store_true", help="Exit nonzero if a cited flood site or its facts are missing")
    args = parser.parse_args()
    results = asyncio.run(simulate())
    expected = json.loads(EXPECTED_SITES_PATH.read_text(encoding="utf-8"))
    passed = evaluate_expected_sites(results, expected)
    serialized = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(serialized + "\n", encoding="utf-8")
        print(f"Wrote derived claim fields to {args.output}")
    else:
        print(serialized)
    for article in results:
        print(f"{article['id']}: {article['matched_site_count']}/{article['expected_site_count']} cited sites matched", file=sys.stderr)
    if args.check and not passed:
        sys.exit(1)
