"""Public collected-article reads without extraction runs or publication writes."""
from datetime import date, datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.main import app
from app.models.news import NewsArticle, NewsExtractionRun
from app.services import local_news_service
from app.services.local_news_service import browse_local_news
from app.services.news_sources import NewsSource
from tests.test_news_processing import article, queue_db  # noqa: F401

NOW = datetime(2026, 10, 11, 1, tzinfo=timezone.utc)
SOURCES = (
    NewsSource("example", "Example News", ("example.org",), ("https://example.org/feed",), date(2026, 10, 10), True),
    NewsSource("disabled", "Disabled", ("disabled.org",), (), date(2026, 10, 10), False),
    NewsSource("unverified", "Unverified", ("unverified.org",), (), None, True),
)
BODY = "As of 8 AM, knee-deep floodwaters were reported along C5 Road in Pasig City."


def story(id: int, **changes) -> NewsArticle:
    return article(id, **{"title": f"Flood news {id}", "article_text": BODY,
        "published_at": NOW - timedelta(minutes=id), "first_seen_at": NOW, "last_seen_at": NOW, **changes})


def test_unprocessed_articles_have_one_public_row_each_and_reads_do_not_write(queue_db):
    with queue_db() as db, db.begin():
        db.add_all([story(1), story(2), story(3)])
    statements = []
    def record(_connection, _cursor, statement, *_args):
        statements.append(statement)
    engine = queue_db.kw["bind"]
    event.listen(engine, "before_cursor_execute", record)
    try:
        with queue_db() as db:
            assert db.scalar(select(func.count()).select_from(NewsExtractionRun)) == 0
            result = browse_local_news(db, limit=2, now=NOW, sources=SOURCES)
            assert [item.id for item in result.items] == [1, 2]
            assert result.items[0].publisher == "Example News"
            assert result.items[0].source_url == "https://example.org/flood/1"
            assert result.items[0].published_at.tzinfo is not None
            assert set(result.items[0].model_dump()) == {"id", "title", "publisher", "source_url", "published_at"}
            assert result.as_of == NOW
    finally:
        event.remove(engine, "before_cursor_execute", record)
    assert all(statement.lstrip().upper().startswith("SELECT") for statement in statements)


@pytest.mark.parametrize("changes", [
    {"published_at": NOW - timedelta(days=8)}, {"published_at": NOW + timedelta(minutes=1)},
    {"published_at": None}, {"article_text": None}, {"article_text": "   "},
    {"article_text": "x" * 100_001}, {"article_error": "private retrieval diagnostics"},
    {"title": " "}, {"review_state": "suppressed"}, {"review_state": "rejected"},
    {"publisher_source_id": "unknown"}, {"publisher_source_id": "disabled"},
    {"publisher_source_id": "unverified"}, {"canonical_url": "https://evil.org/flood"},
    {"canonical_url": "https://example.org.evil.org/flood"},
    {"canonical_url": "http://example.org/flood"},
    {"canonical_url": "https://user:password@example.org/flood"},
    {"article_text": "Officials discussed flood-control corruption in Pasig City."},
    {"article_text": "As of 8 AM, knee-deep floodwaters were reported in Cebu City."},
    {"article_text": "Flooding may occur in Pasig City tomorrow."},
    {"article_text": "Officials confirmed there was no flooding along C5 Road in Pasig City."},
])
def test_unsafe_unavailable_stale_or_irrelevant_articles_are_excluded(queue_db, changes):
    with queue_db() as db, db.begin():
        db.add_all([story(1, **changes), story(2)])
    with queue_db() as db:
        assert [item.id for item in browse_local_news(db, now=NOW, sources=SOURCES).items] == [2]


def test_latest_body_relevance_and_publication_date_not_collection_date(queue_db):
    with queue_db() as db, db.begin():
        db.add_all([story(1, last_seen_at=NOW + timedelta(days=10)), story(2, published_at=NOW),
            story(3, article_text="The publisher corrected its story: no flooding occurred in Pasig City.")])
    with queue_db() as db:
        assert [item.id for item in browse_local_news(db, now=NOW, sources=SOURCES).items] == [2, 1]
        assert browse_local_news(db, now=NOW, sources=()).items == []


@pytest.mark.asyncio
async def test_endpoint_is_public_validates_limit_and_surfaces_storage_failure(queue_db, monkeypatch):
    with queue_db() as db, db.begin():
        db.add(story(1))
    def session():
        with queue_db() as db:
            yield db
    app.dependency_overrides[get_db] = session
    monkeypatch.setattr(local_news_service, "load_news_sources", lambda: SOURCES)
    monkeypatch.setattr(local_news_service, "local_news_clock", lambda: NOW)
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/news/local-updates")
            assert response.status_code == 200
            assert response.headers["cache-control"] == "no-store"
            assert len(response.json()["items"]) == 1
            assert "article_text" not in response.text and "review_state" not in response.text
            for limit in (0, 11):
                assert (await client.get(f"/api/v1/news/local-updates?limit={limit}")).status_code == 422
            def unavailable(*args, **kwargs):
                raise SQLAlchemyError("private database details")
            monkeypatch.setattr(local_news_service, "recent_local_news_candidates", unavailable)
            failed = await client.get("/api/v1/news/local-updates")
            assert failed.status_code == 503
            assert "private database details" not in failed.text
    finally:
        app.dependency_overrides.pop(get_db, None)
