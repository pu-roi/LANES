"""Persist the September 24 replay only in the dedicated loopback test database."""
from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import httpx
from sqlalchemy import func, select
from sqlalchemy.engine import make_url

from scripts.replay_september24_news import PUBLISHED, TITLE, URL


def require_local_test_database(database_url: str) -> None:
    """Reject cloud servers and every database except the dedicated test target."""
    target = make_url(database_url)
    if (target.get_backend_name() != "postgresql"
            or target.host not in {"localhost", "127.0.0.1", "::1"}
            or target.database != "lanes_news_test"
            or any(key in target.query for key in {"host", "hostaddr", "service", "dbname", "database", "port"})):
        raise ValueError("Replay writes require loopback PostgreSQL database lanes_news_test")


async def seed_replay(body_file: Path | None) -> dict:
    from app.core.config import settings
    require_local_test_database(settings.DATABASE_URL)

    from app.core.database import SessionLocal
    from app.crud.news import save_candidate
    from app.models import FloodAvoidanceZone
    from app.models.news import NewsArticle, NewsExtractionRun
    from app.services.news_discovery_service import NewsCandidate, body_has_metro_manila_flood_claim, fetch_article_text
    from app.services.news_feed_service import NewsEntry
    from app.services.news_processing_service import process_saved_news
    from app.services.news_results_service import browse_news_results
    from app.services.news_sources import NewsSource

    source_id = "Daily Tribune (local historical test)"
    source = NewsSource(source_id, "Daily Tribune", ("tribune.net.ph",), (), None, False)
    if body_file is not None:
        body, error = body_file.read_text(encoding="utf-8"), None
    else:
        with httpx.Client(timeout=30) as client:
            body, error = fetch_article_text(source, URL, client)
    if error or not body:
        raise RuntimeError("Could not retrieve the historical article body")
    entry = NewsEntry(source_id, source.publisher, "local-historical-replay", URL, TITLE,
                      "Local historical replay of September 24, 2026; not a current flood alert.", URL, PUBLISHED)
    if not body_has_metro_manila_flood_claim(entry, body):
        raise RuntimeError("Historical source did not pass the actual flood evidence policy")
    with SessionLocal() as db:
        zones_before = db.scalar(select(func.count()).select_from(FloodAvoidanceZone))
    with SessionLocal() as db, db.begin():
        article = save_candidate(db, entry, NewsCandidate(source_id, source.publisher,
            entry.feed_id, URL, TITLE, entry.excerpt, PUBLISHED, datetime.now(timezone.utc), body, None))
        article_id = article.id
    processed = await process_saved_news(SessionLocal, article_id=article_id)
    if processed.failed or processed.retry_wait or processed.lease_lost:
        raise RuntimeError("Historical replay processing did not complete successfully")
    with SessionLocal() as db:
        page = browse_news_results(db, page=1, page_size=50, search=TITLE, publisher=None,
                                  condition=None, placement=None, order="extraction_newest")
        sites = [item for item in page.items if item.article_id == article_id]
        roads = {item.claim.canonical_road: item.claim for item in sites if item.claim.canonical_road}
        expected = {"Boni Avenue", "Quirino Avenue", "Gov. Pascual Avenue", "East Avenue", "Aurora Boulevard"}
        if set(roads) != expected or len(sites) != 5:
            raise RuntimeError("Saved API reader results differ from the historical replay expectations")
        if any(claim.action_type == "auto_approved" for claim in roads.values()):
            raise RuntimeError("Historical replay unexpectedly qualified for automatic activation")
        zones_after = db.scalar(select(func.count()).select_from(FloodAvoidanceZone))
        if zones_after != zones_before:
            raise RuntimeError("Historical replay unexpectedly changed flood avoidance zones")
        return {"database": "lanes_news_test", "article_id": article_id,
                "article_count": db.scalar(select(func.count()).select_from(NewsArticle)),
                "extraction_run_count": db.scalar(select(func.count()).select_from(NewsExtractionRun)),
                "readable_locations": len(sites), "road_sites": len(roads),
                "published_at": PUBLISHED.isoformat(), "production_writes": False,
                "zone_count_unchanged": True, "processing": asdict(processed)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body-file", type=Path, help="Previously retrieved publisher body for offline replay")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(seed_replay(args.body_file)), indent=2))


if __name__ == "__main__":
    main()
