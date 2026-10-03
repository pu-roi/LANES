"""Read-only historical replay of the September 24 Daily Tribune flood report."""
from __future__ import annotations

import asyncio
import argparse
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_discovery_service import (
    body_has_metro_manila_flood_claim,
    extract_captured_news_article,
    fetch_article_text,
    MAX_NEWS_AGE,
)
from app.services.news_feed_service import NewsEntry
from app.services.news_presentation_service import claim_reading_reason
from app.services.news_sources import NewsSource, load_news_sources

URL = "https://tribune.net.ph/2026/09/24/minor-flooding-hits-some-metro-areas"
TITLE = "Minor flooding hits some metro areas"
PUBLISHED = datetime.fromisoformat("2026-09-25T04:41:00+08:00")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body-file", type=Path, help="Replay a previously captured article body offline")
    parser.add_argument("--output", type=Path, help="Save the structured replay result")
    args = parser.parse_args()
    source = NewsSource("historical-tribune-replay", "Daily Tribune", ("tribune.net.ph",), (), None, False)
    if args.body_file:
        body, error = args.body_file.read_text(encoding="utf-8"), None
    else:
        with httpx.Client(timeout=30) as client:
            body, error = fetch_article_text(source, URL, client)
    if error:
        print(json.dumps({"retrieval_error": error}))
        raise SystemExit(1)
    (Path(tempfile.gettempdir()) / "lanes-sept24-replay-body.txt").write_text(body, encoding="utf-8")
    entry = NewsEntry(source.id, source.publisher, "historical-replay", URL, TITLE, "", URL, PUBLISHED)
    extracted = await extract_captured_news_article(NewsArticleExtractorInput(
        article_id=-24, canonical_url=URL, publisher=source.publisher, title=TITLE,
        article_text=body, published_at=PUBLISHED,
    ))
    result = {
        "source_url": URL, "published_at": PUBLISHED.isoformat(),
        "replayed_at": datetime.now(timezone.utc).isoformat(),
        "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "source_configured_for_live_discovery": any(s.enabled and s.accepts_article_host("tribune.net.ph")
                                                   for s in load_news_sources()),
        "outside_live_collection_window": datetime.now(timezone.utc) - PUBLISHED > MAX_NEWS_AGE,
        "production_writes": False,
        "extractor_version": extracted.extraction.extractor_version if extracted.extraction else None,
        "body_characters": len(body), "body_admitted": body_has_metro_manila_flood_claim(entry, body),
        "extraction_error": extracted.error,
        "claims": [{**claim.model_dump(mode="json", exclude={"ranked_location", "road_placement"}),
                    "placement_status": claim.road_placement.status,
                    "placement_reason": claim.road_placement.reason,
                    "placement_candidates": claim.road_placement.total_candidate_count,
                    "reading_reason": claim_reading_reason(claim)}
                   for claim in extracted.extraction.claims] if extracted.extraction else [],
    }
    roads = {c["canonical_road"]: c for c in result["claims"] if c["place_type"] == "street"}
    checks = {
        "body_admitted": result["body_admitted"],
        "five_road_sites": set(roads) == {"Boni Avenue", "Quirino Avenue", "Gov. Pascual Avenue", "East Avenue", "Aurora Boulevard"},
        "all_road_claims_readable": all(c["reading_reason"] is None for c in roads.values()),
        "no_automatic_activation": all(c["action_type"] != "auto_approved" for c in result["claims"]),
    }
    expected = {
        "Boni Avenue": ("City of Mandaluyong", "half-knee", "active", "2026-09-24T16:34:00+08:00"),
        "Quirino Avenue": ("City of Manila", "gutter", "active", None),
        "Gov. Pascual Avenue": ("City of Malabon", "gutter", "active", None),
        "East Avenue": ("Quezon City", None, "subsided", "2026-09-24T15:20:00+08:00"),
        "Aurora Boulevard": ("Quezon City", None, "subsided", "2026-09-24T15:29:00+08:00"),
    }
    for name, facts in expected.items():
        claim = roads.get(name, {})
        checks[name] = tuple(claim.get(field) for field in
            ["canonical_city", "depth_canonical", "condition", "event_time_resolved"]) == facts
    checks["boni_passable_all"] = roads.get("Boni Avenue", {}).get("road_passability") == "passable_all"
    result["checks"] = checks
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(serialized, encoding="utf-8")
    print(json.dumps({**{key: value for key, value in result.items() if key != "claims"},
                      "claim_count": len(result["claims"]),
                      "readable_claim_count": sum(c["reading_reason"] is None for c in result["claims"]),
                      "road_results": [{key: c.get(key) for key in ["canonical_road", "canonical_city",
                          "road_segment_raw", "depth_raw", "condition", "event_time_resolved",
                          "road_passability", "placement_reason"]} for c in roads.values()]},
                     ensure_ascii=False, indent=2))
    if extracted.error or not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
