"""Read-only spatial trace for a real GMA Pasig flood article.

The article is historical. This audit demonstrates extraction, bounded OSM
section matching, Pasig DRRMO context, and all three NOAH scenarios. It never
creates a report, alert, Flood Zone, or routing change.

Run from backend/ with the ignored local Metro Manila OSM/NOAH files and the
cleaned Pasig DRRMO CSV available::

    python scripts/audit_phase36_pasig_article_prediction.py \
      ../data/metro_manila_road_audit.osm.pbf \
      ../frontend/public/pasig-boundary.geojson \
      ../data/flooded_areas_pasig_clean.csv \
      ../data/noah_metro_5yr_inspect.zip \
      ../data/noah_metro_25yr_inspect.zip \
      ../data/noah_metro_100yr_inspect.zip
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from shapely.geometry import LineString, shape
from shapely.ops import transform

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.article_road_context_service import match_article_road_context
from app.services.article_road_match_service import load_bounded_osm_roads, split_named_road_at_intersections
from app.services.hybrid_extraction_service import HybridExtractionService
from app.services.hybrid_extraction_service import MAX_AUTO_ACTIVATION_AGE
from app.services.news_discovery_service import fetch_article_text
from app.services.news_sources import load_news_sources
from app.services.noah_road_prediction_service import RoadSectionEvidence, rank_noah_road_sections
from scripts.audit_noah_road_intersections import hazard_overlap, local_projector


ARTICLE_URL = (
    "https://www.gmanetwork.com/news/topstories/nation/951995/"
    "floods-reported-in-luzon-mindanao-amid-heavy-rains/story/"
)
ARTICLE_TITLE = "Floods reported in Luzon, Mindanao amid heavy rains"
ARTICLE_PUBLISHED_AT = datetime(2025, 7, 9, 11, 29, tzinfo=ZoneInfo("Asia/Manila"))
ARTICLE_ROAD = "Caruncho Avenue"
ARTICLE_CITY = "City of Pasig"
REPO_ROOT = Path(__file__).resolve().parents[2]


async def extract_article_claim(article_text: str):
    article = NewsArticleExtractorInput(
        article_id=1,
        canonical_url=ARTICLE_URL,
        publisher="GMA News",
        title=ARTICLE_TITLE,
        article_text=article_text,
        published_at=ARTICLE_PUBLISHED_AT,
    )
    result = await HybridExtractionService().extract_hybrid(article, mode="rules_only")
    claim = next((item for item in result.claims
                  if item.canonical_road == ARTICLE_ROAD and item.canonical_city == ARTICLE_CITY), None)
    if claim is None:
        raise ValueError("The full article did not yield the expected Pasig road claim")
    return claim, result.claims


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("osm_pbf", type=Path)
    parser.add_argument("pasig_boundary", type=Path)
    parser.add_argument("pasig_drrmo_csv", type=Path)
    parser.add_argument("noah_5yr", type=Path)
    parser.add_argument("noah_25yr", type=Path)
    parser.add_argument("noah_100yr", type=Path)
    args = parser.parse_args()
    inputs = (args.osm_pbf, args.pasig_boundary, args.pasig_drrmo_csv,
              args.noah_5yr, args.noah_25yr, args.noah_100yr)
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        raise FileNotFoundError("Required local audit input is missing: " + ", ".join(missing))

    source = next((item for item in load_news_sources()
                   if item.accepts_article_host(httpx.URL(ARTICLE_URL).host)), None)
    if source is None:
        raise ValueError("The fixed article host is not in the approved source registry")
    with httpx.Client(
        timeout=25,
        trust_env=False,
        headers={"User-Agent": "LANES-Phase36-readonly-audit/0.1 (+https://github.com/pu-roi/LANES)"},
    ) as client:
        article_text, fetch_error = fetch_article_text(source, ARTICLE_URL, client)
    if fetch_error or not article_text:
        raise RuntimeError(f"Full article fetch failed closed: {fetch_error or 'empty body'}")

    claim, article_claims = asyncio.run(extract_article_claim(article_text))
    boundary = shape(json.loads(args.pasig_boundary.read_text(encoding="utf-8-sig")))
    if boundary.is_empty or not boundary.is_valid:
        raise ValueError("Pasig boundary input is empty or invalid")
    ways = load_bounded_osm_roads(str(args.osm_pbf), boundary.bounds)
    sections = split_named_road_at_intersections(
        ARTICLE_ROAD, ways, boundary, f"local-osm-pbf:{args.osm_pbf.name}",
    )
    if not sections:
        raise ValueError("No between-intersection Caruncho Avenue sections match Pasig")
    context = match_article_road_context(claim, sections, boundary, args.pasig_drrmo_csv)
    candidates = set(context.candidate_section_ids)
    evidence = [RoadSectionEvidence(
        section_id=section.section_id,
        metric_centerline=transform(
            local_projector(), LineString(section.centerline_geojson["coordinates"]),
        ),
        osm_source_id=section.source_id,
        article_place_level=context.article_place_levels[section.section_id],
        matching_drrmo_rows=len(context.historical_rows_by_section[section.section_id]),
        bounded_road_section=not section.ambiguous_carriageway,
    ) for section in sections if section.section_id in candidates]
    prediction = rank_noah_road_sections(
        evidence,
        {5: args.noah_5yr, 25: args.noah_25yr, 100: args.noah_100yr},
        hazard_overlap,
    )

    print(f"Source: {ARTICLE_URL}")
    print(f"Fetched full article characters: {len(article_text)}")
    print(f"Extracted claim: {claim.raw_place_name}; {claim.canonical_city}; "
          f"event time kind={claim.event_time_kind}; extraction_historical_flag={claim.is_historical}")
    mandaluyong_landmarks = [item for item in article_claims
                             if item.place_type == "landmark"
                             and item.canonical_city == "City of Mandaluyong"]
    print("Extracted Mandaluyong landmark context: " + (
        "; ".join(f"{item.raw_place_name} / {item.canonical_barangay or 'barangay unresolved'}"
                   for item in mandaluyong_landmarks)
        if mandaluyong_landmarks else "none in article claims"
    ))
    article_age = datetime.now(timezone.utc) - ARTICLE_PUBLISHED_AT.astimezone(timezone.utc)
    fresh_for_auto_activation = timedelta(0) <= article_age <= MAX_AUTO_ACTIVATION_AGE
    print(f"Article age: {article_age}; within {MAX_AUTO_ACTIVATION_AGE} activation window="
          f"{fresh_for_auto_activation}; auto-activation eligible=False "
          "(the report has no resolved observation time or verified flooded extent)")
    print(f"OSM sections in checked Pasig boundary: {len(sections)}")
    print(f"Candidate sections retained: {len(candidates)} ({context.reason})")
    print(f"Place-matched DRRMO rows: "
          f"{sum(len(rows) for rows in context.historical_rows_by_section.values())}; "
          f"unmatched rows kept visible: {len(context.unmatched_history_rows)}")
    print(f"NOAH prediction: {prediction.predicted_section_id or 'unresolved'} "
          f"({prediction.reason})")
    for item in prediction.ranked_sections:
        print(f"  {item.section_id}: DRRMO rows={item.matching_drrmo_rows}; "
              f"overlap 5/25/100yr=" + "/".join(
                  f"{item.modeled_overlap_fraction[period]:.3f}" for period in (5, 25, 100)
              ))
    print("Status: historical location prediction only; no report, alert, zone, or route was written")


if __name__ == "__main__":
    main()
