"""Failed refreshes remain attention items when earlier credible evidence exists."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.crud.news import save_candidate
from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.services.news_collection_service import browse_news_collection
from app.services.news_discovery_service import NewsCandidate
from app.services.news_feed_service import NewsEntry
from app.services.news_processing_service import process_saved_news
from app.services.news_results_service import browse_news_results
from test_news_processing import queue_db

ORIGINAL = "As of 10 AM, knee-deep flooding affected Ortigas Avenue in Pasig City. Authorities monitored the flooded road and traffic was diverted."


def collection(db, status="attention"):
    return browse_news_collection(db, page=1, page_size=50, search="", publisher=None, status=status)


@pytest.mark.asyncio
@pytest.mark.parametrize("latest_status", ["pending", "failed"])
async def test_prior_credible_history_keeps_failed_refresh_visible_without_reviving_old_main_results(queue_db, latest_status: str) -> None:
    now = datetime.now(timezone.utc)
    entry = NewsEntry("example", "Example", "https://example.org/rss", "1", "Flood in Pasig", "", "https://example.org/1", now)
    def candidate(body, error=None):
        return NewsCandidate(entry.source_id, entry.publisher, entry.feed_id, entry.article_url,
            entry.title, entry.excerpt, entry.published_at, now, body, error)
    with queue_db() as db, db.begin():
        article_id = save_candidate(db, entry, candidate(ORIGINAL)).id
    assert (await process_saved_news(queue_db)).completed == 1
    with queue_db() as db, db.begin():
        old_run_id = db.scalar(select(NewsExtractionRun.id))
        revised = replace(entry, published_at=now + timedelta(minutes=1))
        save_candidate(db, revised, candidate(ORIGINAL.replace("knee-deep", "waist-deep")))
        newest = db.scalar(select(NewsExtractionRun).order_by(NewsExtractionRun.id.desc()))
        assert newest.id != old_run_id
        if latest_status == "failed":
            newest.status, newest.error_code, newest.completed_at = "failed", "extraction_exception", now
        save_candidate(db, revised, candidate(None, "Article HTTP 503"))
    with queue_db() as db:
        page = collection(db)
        assert page.total == 1
        assert page.items[0].collection_status == "retrieval_failed"
        assert page.items[0].processing_status == latest_status
        assert page.items[0].location_count == 0
        main = browse_news_results(db, page=1, page_size=50, search="", publisher=None,
            condition=None, placement=None, order="publication_newest")
        assert main.total == 0
        assert db.get(NewsExtractionRun, old_run_id).status == "completed"
        assert len(list(db.scalars(select(NewsArticleVersion)))) == 2


@pytest.mark.asyncio
async def test_unsupported_history_does_not_turn_legacy_retrieval_failures_into_attention(queue_db) -> None:
    now = datetime.now(timezone.utc)
    entry = NewsEntry("example", "Example", "https://example.org/rss", "1", "Flood prevention in Pasig", "", "https://example.org/1", now)
    body = "Officials in Pasig City discussed flood-control projects and drainage improvements at a meeting. They allocated additional funds to reduce future flood risk."
    candidate = NewsCandidate(entry.source_id, entry.publisher, entry.feed_id, entry.article_url,
        entry.title, "", now, now, body, None)
    with queue_db() as db, db.begin():
        save_candidate(db, entry, candidate)
    assert (await process_saved_news(queue_db)).completed == 1
    with queue_db() as db, db.begin():
        save_candidate(db, entry, replace(candidate, article_text=None, article_error="Article HTTP 503"))
    with queue_db() as db:
        assert collection(db).total == 0
        assert collection(db, "all").items[0].collection_status == "excluded"
