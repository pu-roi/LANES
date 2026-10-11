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


@pytest.mark.parametrize("title,body", [
    ("Weather advisory for Metro Manila", "A weather advisory warns Metro Manila commuters about heavy rain tomorrow."),
    ("Traffic advisory in Pasig City", "A traffic advisory in Pasig City announces road closures this weekend."),
    ("MRT-3 service schedule", "MRT-3 service will operate on a shortened schedule this weekend."),
    ("Safety advisory in Marikina", "An evacuation advisory has been issued for Marikina residents."),
    ("ITCZ brings rains to parts of PH", "Metro Manila may expect scattered rains and thunderstorms due to the easterlies."),
])
def test_commuter_updates_are_shown_without_any_flood_story(queue_db, title, body):
    with queue_db() as db, db.begin():
        db.add(story(1, title=title, article_text=body, review_state="local_update"))
    with queue_db() as db:
        result = browse_local_news(db, now=NOW, sources=SOURCES)
        assert [item.title for item in result.items] == [title]
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun)) == 0


@pytest.mark.parametrize("title,body", [
    ("Traffic advisory in Cebu City", "A traffic advisory announces road closures in Cebu City."),
    ("Weather advisory in Cebu", "MANILA, Philippines — A weather advisory warns Cebu City about heavy rain."),
    ("Traffic advisory in Pasig City", "A traffic advisory announces road closures in Cebu City."),
    ("Metro Manila weather office", "The Manila weather office issues a weather advisory for Cebu City."),
    ("Pasig sports results", "The Pasig team won a local basketball game."),
    ("Markets in Makati", "Stock market trading resumed in Makati."),
])
def test_general_and_nonlocal_news_do_not_fill_the_widget(queue_db, title, body):
    with queue_db() as db, db.begin():
        db.add(story(1, title=title, article_text=body, review_state="local_update"))
    with queue_db() as db:
        assert browse_local_news(db, now=NOW, sources=SOURCES).items == []


def test_collector_persists_commuter_story_without_queuing_flood_extraction(queue_db):
    from email.utils import format_datetime
    from app.services.news_discovery_service import discover_news
    from app.models.news import NewsArticleFeedEntry
    source = SOURCES[0]
    url = "https://example.org/transport"
    published = datetime.now(timezone.utc) - timedelta(minutes=2)
    title = "MRT-3 service schedule this weekend"
    body = "MRT-3 service will operate on a shortened schedule this weekend. Commuters are advised to plan their journeys ahead. " * 2
    item = f"<item><guid>transport</guid><title>{title}</title><link>{url}</link><pubDate>{format_datetime(published)}</pubDate></item>"
    requests = []
    def handler(request):
        requests.append(str(request.url))
        if str(request.url) == source.feed_urls[0]:
            return httpx.Response(200, text=f"<rss><channel>{item}{item.replace('transport</guid>', 'duplicate</guid>')}</channel></rss>")
        return httpx.Response(200, text=f"<article><p>{body}</p></article>", headers={"content-type": "text/html"})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client, queue_db() as db:
        run = discover_news((source,), client, db)
        row = db.scalar(select(NewsArticle))
        assert row.review_state == "local_update"
        assert row.article_text == body.strip()
        assert run.candidates == ()
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun)) == 0
        assert db.scalar(select(func.count()).select_from(NewsArticleFeedEntry)) == 2
        assert browse_local_news(db, now=published+timedelta(minutes=3), sources=(source,)).items[0].title == title
        discover_news((source,), client, db)
        assert db.scalar(select(func.count()).select_from(NewsArticle)) == 1
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun)) == 0
    assert requests.count(url) == 1


def test_commuter_article_becomes_normal_flood_input_only_with_flood_evidence(queue_db):
    from app.crud.news import save_candidate
    from app.services.news_discovery_service import NewsCandidate
    from app.services.news_feed_service import NewsEntry
    with queue_db() as db, db.begin():
        row = story(1, review_state="local_update", title="Traffic advisory in Pasig", article_text="A traffic advisory in Pasig announces road closures.")
        db.add(row)
    entry = NewsEntry("example", "Example News", "https://example.org/feed", "event", "Flooding in Pasig", "", "https://example.org/flood/1", NOW)
    candidate = NewsCandidate("example", "Example News", "event", entry.article_url, entry.title, "", NOW, NOW, BODY, None)
    with queue_db() as db, db.begin():
        updated = save_candidate(db, entry, candidate)
        assert updated.review_state == "pending"
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun)) == 1
        # A later commuter correction cannot take a flood article out of its
        # immutable flood-processing lifecycle or reset staff rejection.
        save_candidate(db, entry, candidate, local_update_only=True)
        assert updated.review_state == "pending"
        updated.review_state = "rejected"
        save_candidate(db, entry, candidate)
        assert updated.review_state == "rejected"


def test_failed_commuter_refresh_hides_previous_body_from_public_widget(queue_db):
    from email.utils import format_datetime
    from app.services.news_discovery_service import discover_news
    source = SOURCES[0]
    now = datetime.now(timezone.utc)
    with queue_db() as db, db.begin():
        db.add(story(1, review_state="local_update", published_at=now-timedelta(hours=1), title="MRT-3 service schedule", article_text="MRT-3 service will operate on a shortened schedule."))
    item = f"<item><guid>transport</guid><title>MRT-3 service schedule updated</title><link>https://example.org/flood/1</link><pubDate>{format_datetime(now)}</pubDate></item>"
    def handler(request):
        if str(request.url) == source.feed_urls[0]: return httpx.Response(200, text=f"<rss><channel>{item}</channel></rss>")
        return httpx.Response(403)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client, queue_db() as db:
        discover_news((source,), client, db)
        assert db.scalar(select(NewsArticle)).article_error
        assert db.scalar(select(NewsArticle)).review_state == "local_update"
        assert browse_local_news(db, now=now, sources=(source,)).items == []
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun)) == 0


def test_commuter_fetch_budget_does_not_consume_flood_retrieval_budget(queue_db, monkeypatch):
    from email.utils import format_datetime
    from app.services import news_discovery_service
    source = SOURCES[0]
    monkeypatch.setattr(news_discovery_service, "MAX_COMMUTER_BODY_PROBES", 2)
    monkeypatch.setattr(news_discovery_service, "MAX_COMMUTER_BODY_PROBES_PER_FEED", 2)
    published = datetime.now(timezone.utc) - timedelta(minutes=2)
    date = format_datetime(published)
    items = ''.join(f"<item><guid>{i}</guid><title>MRT-3 service schedule {i}</title><link>https://example.org/train/{i}</link><pubDate>{date}</pubDate></item>" for i in range(5))
    items += f"<item><guid>flood</guid><title>Flooding in Pasig</title><link>https://example.org/active-flood</link><pubDate>{date}</pubDate></item>"
    fetched = []
    def handler(request):
        if str(request.url) == source.feed_urls[0]:return httpx.Response(200, text=f"<rss><channel>{items}</channel></rss>")
        fetched.append(str(request.url))
        body = BODY * 3 if request.url.path == "/active-flood" else "MRT-3 service will operate on a shortened schedule this weekend. Commuters should plan their journeys ahead. " * 2
        return httpx.Response(200, text=f"<article><p>{body}</p></article>",headers={"content-type":"text/html"})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client, queue_db() as db:
        run = news_discovery_service.discover_news((source,), client, db)
        assert len(run.candidates) == 1
        assert len(fetched) == 3
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun)) == 1
        assert db.scalar(select(func.count()).select_from(NewsArticle).where(NewsArticle.review_state == "local_update")) == 2
        assert sum("Commuter article retrieval limit reached" == n.reason for n in run.notices) == 3
