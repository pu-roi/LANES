"""Operational history is durable, bounded, staff-only and never activates floods."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.core.database import get_db
from app.main import app
from app.models.news import NewsArticle, NewsArticleFeedEntry, NewsArticleVersion, NewsExtractionRun, NewsFeedCheckpoint
from app.models.news_telemetry import NewsDiscoveryRun, NewsDiscoveryFeedRun, NewsFallbackLookup, NewsFallbackLookupLead
from app.models.role import Role
from app.models.user import User
from app.services.news_discovery_service import discover_news
from app.services.news_open_search_service import OpenSearchLookup, OpenSearchHit
from app.services.news_telemetry_service import begin_discovery, begin_fallback, finish_discovery, finish_fallback
from app.services.news_sources import NewsSource
from app.services.news_feed_service import FeedProbe


@compiles(JSONB, "sqlite")
def sqlite_jsonb(_type, _compiler, **_kw):
    return "JSON"


@pytest.fixture
def telemetry_db():
    engine = create_engine("sqlite+pysqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    tables = [Role.__table__, User.__table__, NewsArticle.__table__, NewsArticleFeedEntry.__table__,
        NewsArticleVersion.__table__, NewsExtractionRun.__table__, NewsFeedCheckpoint.__table__,
        NewsDiscoveryRun.__table__, NewsDiscoveryFeedRun.__table__, NewsFallbackLookup.__table__, NewsFallbackLookupLead.__table__]
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    NewsArticle.metadata.create_all(engine, tables=tables)
    with Session(engine) as db:
        db.add(Role(id=1, name="Admin"))
        db.flush()
        db.add(User(id=1, username="staff", email="staff@example.org", hashed_password="test", role_id=1))
        db.add(NewsArticle(id=1, canonical_url="https://example.org/original", publisher_source_id="test",
            title="Original flood report", excerpt="", article_text=None, article_error="Article HTTP 403",
            content_fingerprint="a" * 64, review_state="pending"))
        db.commit()
    writes = []
    def record(_connection, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE"}:
            writes.append(statement)
    event.listen(engine, "before_cursor_execute", record)
    def database():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = database
    try:
        yield engine, writes
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(deps.get_current_user, None)
        engine.dispose()


def test_discovery_partial_feed_failure_duplicates_and_counts(telemetry_db):
    engine, _ = telemetry_db
    source = NewsSource("test", "Test", ("example.org",), ("https://example.org/feed", "https://example.org/bad"), datetime.now().date(), True)
    def handler(request):
        if str(request.url).endswith("bad"):
            return httpx.Response(503)
        if str(request.url).endswith("feed"):
            item = '<item><guid>x</guid><title>Flood in Pasig</title><link>https://example.org/flood</link></item>'
            return httpx.Response(200, text=f'<rss><channel>{item * 2}</channel></rss>')
        return httpx.Response(403)
    with Session(engine) as db, httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = discover_news((source,), client, db)
        assert not result.candidates
        assert any("body verification unavailable" in notice.reason for notice in result.notices)
        run = db.scalar(select(NewsDiscoveryRun))
        assert run.status == "failed" and run.trigger == "collector" and run.actor_id is None
        feeds = list(db.scalars(select(NewsDiscoveryFeedRun).order_by(NewsDiscoveryFeedRun.id)))
        assert len(feeds) == 2
        assert feeds[0].candidates_saved == 0 and feeds[0].body_errors == 1
        assert feeds[1].error_code == "feed_probe_failed"
        assert db.scalar(select(func.count()).select_from(NewsArticle)) == 1


def test_failure_preserves_committed_feed_and_finalization_is_idempotent(telemetry_db, monkeypatch):
    from app.services import news_discovery_service
    engine, _ = telemetry_db
    calls = 0
    def probe(source, url, *_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("private network details")
        return FeedProbe(source.id, source.publisher, url, "empty", 200, 0, 0, None), ()
    monkeypatch.setattr(news_discovery_service, "probe_feed", probe)
    source = NewsSource("test", "Test", ("example.org",), ("https://example.org/one", "https://example.org/two"), datetime.now().date(), True)
    with Session(engine) as db, httpx.Client() as client:
        with pytest.raises(RuntimeError):
            discover_news((source,), client, db, actor_id=1)
        run = db.scalar(select(NewsDiscoveryRun))
        assert run.status == "failed" and run.error_code == "discovery_failed" and run.actor_id == 1
        assert db.scalar(select(func.count()).select_from(NewsDiscoveryFeedRun)) == 1
        finish_discovery(db, run.id)
        db.refresh(run)
        assert run.status == "failed"


@pytest.mark.parametrize("throttled", [False, True])
def test_fallback_zero_hits_throttle_and_lead_privacy(telemetry_db, throttled):
    engine, _ = telemetry_db
    now = datetime.now(timezone.utc)
    with Session(engine) as db:
        article = db.get(NewsArticle, 1)
        id = begin_fallback(db, article, 1, True)
        result = OpenSearchLookup(article.canonical_url, now, "index_links_only", (),
            ("private provider token",) if throttled else (), 90 if throttled else None)
        finish_fallback(db, id, result)
        run = db.get(NewsFallbackLookup, id)
        assert run.status == ("failed" if throttled else "completed")
        assert run.error_code == ("provider_throttled" if throttled else None)
        assert run.content_fingerprint == "a" * 64
        lead = OpenSearchHit("https://example.org/alternate", "Alternate", now, "possible_other_source", "event",
            publisher_source_id="test", article_text="private body", fetched_at=now)
        finish_fallback(db, id, replace(result, results=(lead,)))
        assert db.scalar(select(func.count()).select_from(NewsFallbackLookupLead)) == 0
        next_id = begin_fallback(db, article, 1, True)
        finish_fallback(db, next_id, replace(result, results=(lead,), errors=(), retry_after_seconds=None))
        stored = db.scalar(select(NewsFallbackLookupLead))
        assert stored.retrieval_status == "retrieved"
        assert not hasattr(stored, "article_text")
        assert article.review_state == "pending" and article.article_text is None


def test_abandoned_runs_interrupted_only_on_new_work(telemetry_db):
    engine, _ = telemetry_db
    now = datetime.now(timezone.utc)
    with Session(engine) as db:
        old = NewsDiscoveryRun(trigger="collector", started_at=now - timedelta(hours=3))
        fresh = NewsDiscoveryRun(trigger="collector", started_at=now - timedelta(minutes=3))
        db.add_all([old, fresh])
        db.commit()
        begin_discovery(db, None)
        db.refresh(old)
        db.refresh(fresh)
        assert old.status == "interrupted" and old.error_code == "worker_interrupted"
        assert fresh.status == "running"
        finish_discovery(db, old.id)
        db.refresh(old)
        assert old.status == "interrupted"


def test_lookup_capture_survives_article_revision_after_start_commit(telemetry_db):
    from app.services.news_fallback_service import FallbackInput
    engine, _ = telemetry_db
    with Session(engine) as db:
        article = db.get(NewsArticle, 1)
        captured = FallbackInput.capture(article)
        id = begin_fallback(db, article, 1, False)
        with Session(engine) as other:
            revised = other.get(NewsArticle, 1)
            revised.title = "New revision"
            revised.content_fingerprint = "b" * 64
            other.commit()
        db.expire(article)
        assert article.title == "New revision"
        assert captured.title == "Original flood report"
        assert db.get(NewsFallbackLookup, id).content_fingerprint == "a" * 64


@pytest.mark.asyncio
async def test_history_guards_pagination_read_only_and_sanitized_errors(telemetry_db, monkeypatch):
    engine, writes = telemetry_db
    with Session(engine) as db:
        for _ in range(7):
            begin_discovery(db, None)
    writes.clear()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        paths = ["/api/v1/admin/news/monitoring/discovery", "/api/v1/admin/news/monitoring/fallback"]
        for path in paths:
            assert (await client.get(path)).status_code == 401
        app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id=1, role=SimpleNamespace(name="Commuter"))
        for path in paths:
            assert (await client.get(path)).status_code == 403
        app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id=1, role=SimpleNamespace(name="Admin"))
        data = (await client.get(paths[0], params={"page_size": 5})).json()
        assert data["total"] == 7 and data["pages"] == 2
        assert [item["id"] for item in data["items"]] == [7, 6, 5, 4, 3]
        assert (await client.get(paths[0], params={"page": 999})).json()["page"] == 2
        assert (await client.get(paths[1])).json()["items"] == []
        assert (await client.get(paths[0], params={"page_size": 21})).status_code == 422
        assert (await client.get("/api/v1/admin/news/monitoring/invalid")).status_code == 422
        from app.api.v1.endpoints import admin_news
        from sqlalchemy.exc import OperationalError
        def fail(*_args, **_kwargs):
            raise OperationalError("secret connection", {}, Exception("secret"))
        monkeypatch.setattr(admin_news, "browse_telemetry", fail)
        response = await client.get(paths[0])
        assert response.status_code == 503 and "secret" not in response.text
    assert not writes


def test_fallback_finalization_failure_rolls_back_children(telemetry_db, monkeypatch):
    engine, _ = telemetry_db
    now = datetime.now(timezone.utc)
    with Session(engine) as db:
        id = begin_fallback(db, db.get(NewsArticle, 1), 1, False)
        lead = OpenSearchHit("https://example.org/alternate", "Alternate", now, "possible_other_source", "event")
        def fail():
            raise RuntimeError("commit failed")
        with monkeypatch.context() as patch:
            patch.setattr(db, "commit", fail)
            with pytest.raises(RuntimeError):
                finish_fallback(db, id, OpenSearchLookup("https://example.org/original", now, "index", (lead,), ()))
        db.rollback()
        assert db.get(NewsFallbackLookup, id).status == "running"
        assert db.scalar(select(func.count()).select_from(NewsFallbackLookupLead)) == 0


@pytest.mark.asyncio
async def test_fallback_api_records_exception_and_reports_telemetry_failure(telemetry_db, monkeypatch):
    from app.api.v1.endpoints import admin_news
    from app.core.limiter import limiter
    from sqlalchemy.exc import OperationalError
    engine, _ = telemetry_db
    limiter.reset()
    source = NewsSource("test", "Test", ("example.org",), ("https://example.org/feed",), datetime.now().date(), True)
    with Session(engine) as db:
        db.add(NewsArticleFeedEntry(article_id=1, source_id="test", feed_url=source.feed_urls[0], feed_guid="original"))
        db.commit()
    monkeypatch.setattr(admin_news, "load_news_sources", lambda: (source,))
    app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id=1, role=SimpleNamespace(name="Admin"))
    def broken_lookup(*_args, **_kwargs):
        raise RuntimeError("private network details")
    monkeypatch.setattr(admin_news, "lookup_news_leads", broken_lookup)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/admin/news/candidates/1/open-leads")
        assert response.status_code == 502 and "private" not in response.text
        with Session(engine) as db:
            run = db.scalar(select(NewsFallbackLookup))
            assert run.status == "failed" and run.error_code == "lookup_failed"
        from app.services import news_telemetry_service
        monkeypatch.setattr(admin_news, "lookup_news_leads", lambda *_args: OpenSearchLookup(
            "https://example.org/original", datetime.now(timezone.utc), "index_links_only_incomplete_article", (), ()))
        def broken_finalization(*_args, **_kwargs):
            raise OperationalError("private DB", {}, Exception("private details"))
        monkeypatch.setattr(news_telemetry_service, "finish_fallback", broken_finalization)
        response = await client.get("/api/v1/admin/news/candidates/1/open-leads")
        assert response.status_code == 503 and "private" not in response.text
        with Session(engine) as db:
            assert db.scalar(select(NewsFallbackLookup).order_by(NewsFallbackLookup.id.desc())).status == "running"
