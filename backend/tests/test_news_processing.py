"""Durable extraction regressions without provider calls or public-state writes."""
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.core.database import get_db
from app.core.limiter import limiter
from app.crud.news import save_candidate
from app.crud.news_processing import (PIPELINE_VERSION, claim_due_run, enqueue_article, finish_owned_run)
from app.main import app
from app.models.news import (NewsArticle, NewsArticleFeedEntry, NewsArticleVersion, NewsExtractionRun, NewsFeedCheckpoint)
from app.services import news_processing_service
from app.services.hybrid_extraction_service import HybridExtractionService
from app.services.news_auto_ingestion_service import NewsAutoIngestionService
from app.services.news_discovery_service import NewsCandidate, discover_news, extract_saved_news_articles
from app.services.news_feed_service import NewsEntry
from app.services.news_sources import NewsSource

NOW = datetime(2026, 10, 2, 3, tzinfo=timezone.utc)
BODY = "As of 10 AM, abot-tuhod ang baha sa Maybunga, Pasig City."


@compiles(JSONB, "sqlite")
def sqlite_jsonb(_type, _compiler, **_kw):
    return "JSON"


def article(id=1, **changes):
    values = dict(id=id, canonical_url=f"https://example.org/flood/{id}", publisher_source_id="example",
                  title="Baha sa Pasig", excerpt="", published_at=NOW, fetched_at=NOW,
                  first_seen_at=NOW, last_seen_at=NOW, article_text=BODY, article_error=None,
                  content_fingerprint="0" * 64, review_state="pending")
    return NewsArticle(**{**values, **changes})


@pytest.fixture
def queue_db(monkeypatch):
    engine = create_engine("sqlite+pysqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    @event.listens_for(engine, "connect")
    def enable_fk(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")
    NewsArticle.metadata.create_all(engine, tables=[NewsArticle.__table__, NewsArticleFeedEntry.__table__,
        NewsFeedCheckpoint.__table__, NewsArticleVersion.__table__, NewsExtractionRun.__table__])
    def forbidden(*args, **kwargs):
        pytest.fail("Extraction attempted external audit or public ingestion")
    monkeypatch.setattr(HybridExtractionService, "audit_claim_with_llm", forbidden)
    monkeypatch.setattr(NewsAutoIngestionService, "process_and_ingest_article", forbidden)
    factory = sessionmaker(bind=engine)
    try:
        yield factory
    finally:
        engine.dispose()


@pytest.mark.asyncio
async def test_capture_process_restart_and_preview_share_exact_identity(queue_db):
    with queue_db() as db, db.begin():
        row = article()
        db.add(row)
        first = enqueue_article(db, row)
        row.fetched_at += timedelta(hours=1)
        assert enqueue_article(db, row) == first
        preview, = await extract_saved_news_articles([row])
        version = db.scalar(select(NewsArticleVersion))
        assert version.input_fingerprint == preview.input_fingerprint
        assert "fetched_at" not in version.input_snapshot
    result = await news_processing_service.process_saved_news(queue_db, clock=lambda: NOW)
    assert result.completed == 1 and not result.failed
    with queue_db() as db:
        run = db.get(NewsExtractionRun, first)
        assert run.status == "completed" and run.attempt_count == 1
        assert run.result["article_id"] == 1
        claim = next(c for c in run.result["claims"] if c["canonical_barangay"] == "Maybunga")
        assert claim["depth_canonical"] == "knee"
        assert claim["action_type"] != "auto_approved"
        assert db.get(NewsArticle, 1).review_state == "pending"
    restarted_factory = sessionmaker(bind=queue_db.kw["bind"])
    repeated = await news_processing_service.process_saved_news(restarted_factory, clock=lambda: NOW)
    assert repeated.completed == repeated.captured == 0 and repeated.runs == []


@pytest.mark.asyncio
async def test_capture_skips_blocked_missing_oversized_and_moderated_rows(queue_db):
    with queue_db() as db, db.begin():
        db.add_all([article(1, article_error="Article HTTP 403"), article(2, article_text=None),
                    article(3, article_text="x"*100_001), article(4, review_state="approved"),
                    article(5, article_text="   "), article(6, article_text="Flood control projects in Taguig City.")])
    result = await news_processing_service.process_saved_news(queue_db, clock=lambda: NOW)
    assert result.captured == result.completed == 1
    with queue_db() as db:
        version = db.scalar(select(NewsArticleVersion))
        assert version.article_id == 6
        assert db.scalar(select(NewsExtractionRun)).result["claims"] == []


@pytest.mark.asyncio
async def test_revision_keeps_prior_snapshot_and_failed_refresh_does_not_relabel(queue_db):
    entry = NewsEntry("example", "Example", "https://example.org/feed", "1", "Baha sa Pasig", "",
                      "https://example.org/flood/1", NOW)
    def candidate(body, error=None):
        return NewsCandidate("example", "Example", "1", entry.article_url, entry.title, "", entry.published_at,
                             NOW, body, error)
    with queue_db() as db, db.begin():
        row = save_candidate(db, entry, candidate(BODY))
        row_id = row.id
    revised = NewsEntry(**{**entry.__dict__, "published_at": NOW+timedelta(hours=1)})
    with queue_db() as db, db.begin():
        save_candidate(db, revised, candidate(BODY.replace("abot-tuhod", "abot-dibdib")))
    with queue_db() as db, db.begin():
        failed = NewsEntry(**{**entry.__dict__, "published_at": NOW+timedelta(hours=2)})
        save_candidate(db, failed, candidate(None, "Article HTTP 403"))
        snapshots = list(db.scalars(select(NewsArticleVersion).order_by(NewsArticleVersion.id)))
        assert len(snapshots) == 2
        assert snapshots[0].input_snapshot["article_text"] == BODY
        assert snapshots[1].input_snapshot["published_at"] == revised.published_at.isoformat()
    result = await news_processing_service.process_saved_news(queue_db, clock=lambda: NOW)
    assert result.completed == 2
    with queue_db() as db:
        assert db.get(NewsArticle, row_id).article_error == "Article HTTP 403"
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion)) == 2


@pytest.mark.asyncio
async def test_failure_retries_due_only_then_exhausts_and_keeps_later_work(queue_db, monkeypatch):
    with queue_db() as db, db.begin():
        db.add_all([article(), article(2)])
    real = news_processing_service.extract_captured_news_article
    async def fail_one(source):
        if source.article_id == 1:
            raise RuntimeError("secret private error details")
        return await real(source)
    monkeypatch.setattr(news_processing_service, "extract_captured_news_article", fail_one)
    now = NOW
    first = await news_processing_service.process_saved_news(queue_db, clock=lambda: now)
    assert first.retry_wait == first.completed == 1
    assert "secret" not in json.dumps(first.__dict__)
    early = await news_processing_service.process_saved_news(queue_db, clock=lambda: now)
    assert early.runs == []
    for attempt in range(2, 6):
        now += timedelta(seconds=60*2**(attempt-2))
        summary = await news_processing_service.process_saved_news(queue_db, clock=lambda: now)
        assert (summary.failed if attempt == 5 else summary.retry_wait) == 1
    with queue_db() as db:
        run = db.scalar(select(NewsExtractionRun).join(NewsArticleVersion).where(NewsArticleVersion.article_id == 1))
        assert run.attempt_count == 5 and run.status == "failed"
        assert run.next_attempt_at is None and run.lease_token is None
    assert not (await news_processing_service.process_saved_news(queue_db, clock=lambda: now+timedelta(days=1))).runs


def test_expired_owner_cannot_finish_reclaimed_lease(queue_db):
    with queue_db() as db, db.begin():
        row = article()
        db.add(row)
        enqueue_article(db, row)
    with queue_db() as db, db.begin():
        old = claim_due_run(db, NOW)
    with queue_db() as db, db.begin():
        assert claim_due_run(db, NOW) is None
        assert not finish_owned_run(db, old, NOW+timedelta(minutes=6), result={})
        current = claim_due_run(db, NOW+timedelta(minutes=6))
    with queue_db() as db, db.begin():
        assert current.lease_token != old.lease_token and current.attempt_count == 2
        assert not finish_owned_run(db, old, NOW+timedelta(minutes=6), result={})
        assert finish_owned_run(db, current, NOW+timedelta(minutes=6), result={"claims": []})


@pytest.mark.asyncio
async def test_expired_final_attempt_is_reported_failed(queue_db):
    with queue_db() as db, db.begin():
        row = article()
        db.add(row)
        enqueue_article(db, row)
        run = db.scalar(select(NewsExtractionRun))
        run.attempt_count = 4
        final = claim_due_run(db, NOW)
        assert final.attempt_count == 5
    result = await news_processing_service.process_saved_news(queue_db, clock=lambda: NOW+timedelta(minutes=6))
    assert result.failed == 1 and result.runs[0]["error_code"] == "lease_expired_exhausted"


@pytest.mark.asyncio
async def test_pipeline_bump_enqueues_new_run_without_duplicate_input(queue_db, monkeypatch):
    with queue_db() as db, db.begin():
        row = article()
        db.add(row)
        first = enqueue_article(db, row)
        second = enqueue_article(db, row, pipeline_version="intentional-next-policy")
        assert first != second
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion)) == 1


@pytest.mark.asyncio
async def test_staff_processing_auth_status_and_idempotency(queue_db):
    with queue_db() as db, db.begin():
        db.add_all([article(), article(2, article_error="Article HTTP 403")])
    def dependency():
        with queue_db() as db:
            yield db
    app.dependency_overrides[get_db] = dependency
    limiter.reset()
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            url = "/api/v1/admin/news/candidates/1/processing"
            assert (await client.post(url)).status_code == 401
            assert (await client.get(url)).status_code == 401
            app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Commuter"))
            assert (await client.post(url)).status_code == 403
            assert (await client.get(url)).status_code == 403
            app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Admin"))
            assert (await client.post("/api/v1/admin/news/candidates/999/processing")).status_code == 404
            assert (await client.post("/api/v1/admin/news/candidates/2/processing")).status_code == 409
            response = await client.post(url)
            assert response.status_code == 200 and response.json()["completed"] == 1
            status = (await client.get(url)).json()[0]
            assert status["status"] == "completed" and status["result"]["article_id"] == 1
            assert "lease_token" not in status
            assert (await client.post(url)).json()["completed"] == 0
            assert (await client.post(url)).json()["completed"] == 0
            assert (await client.post(url)).status_code == 429
            limiter.reset()
            assert (await client.post(url)).json()["completed"] == 0
        with queue_db() as db:
            assert db.get(NewsArticle, 1).review_state == "pending"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(deps.get_current_user, None)
        limiter.reset()


@pytest.mark.asyncio
async def test_manual_submissions_capture_revisions_without_duplicate_work(queue_db, monkeypatch):
    from app.crud import news_processing
    from sqlalchemy.exc import SQLAlchemyError
    def dependency():
        with queue_db() as db:
            yield db
    app.dependency_overrides[get_db] = dependency
    app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Admin"))
    payload = {"source_url": "https://example.org/manual/flood", "publisher": "Staff DRRMO",
               "title": "Baha sa Pasig", "text": BODY}
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            url = "/api/v1/admin/news/manual-candidate"
            first = await client.post(url, json=payload)
            repeated = await client.post(url, json=payload)
            assert first.status_code == repeated.status_code == 200
            assert first.json()["published_at"] == repeated.json()["published_at"]
            with queue_db() as db:
                assert db.scalar(select(func.count()).select_from(NewsExtractionRun)) == 1
            revision = await client.post(url, json={**payload, "text": BODY.replace("tuhod", "dibdib")})
            assert revision.status_code == 200
            with queue_db() as db:
                assert db.scalar(select(func.count()).select_from(NewsArticleVersion)) == 2
                snapshots = db.scalars(select(NewsArticleVersion).order_by(NewsArticleVersion.id)).all()
                assert snapshots[0].input_snapshot["article_text"] == BODY
                assert "dibdib" in snapshots[1].input_snapshot["article_text"]
            result = await news_processing_service.process_saved_news(queue_db)
            assert result.completed == 2 and not result.failed
            def storage_failure(*args, **kwargs):
                raise SQLAlchemyError("private connection details")
            monkeypatch.setattr(news_processing, "enqueue_article", storage_failure)
            failed = await client.post(url, json={**payload, "text": "Must not replace evidence"})
            assert failed.status_code == 503 and "private" not in failed.text
            with queue_db() as db:
                assert "dibdib" in db.get(NewsArticle, first.json()["id"]).article_text
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(deps.get_current_user, None)


def test_process_cli_no_http_and_repeated_delivery(queue_db, monkeypatch, capsys):
    from scripts import run_news_discovery
    with queue_db() as db, db.begin():
        db.add(article())
    monkeypatch.setattr(run_news_discovery, "SessionLocal", queue_db)
    monkeypatch.setattr(run_news_discovery.httpx, "Client", lambda **kw: pytest.fail("Saved processing opened HTTP"))
    monkeypatch.setattr(sys, "argv", ["collector", "--process-saved", "--limit", "2"])
    assert run_news_discovery.main() == 0
    assert json.loads(capsys.readouterr().out)["completed"] == 1
    assert run_news_discovery.main() == 0
    assert json.loads(capsys.readouterr().out)["completed"] == 0


@pytest.mark.parametrize("args", [["--process-saved", "--dry-run"], ["--probe", "--process"],
    ["--discover", "--process", "--dry-run"], ["--process-saved", "--limit", "201"]])
def test_invalid_processing_cli_never_opens_database(args, monkeypatch):
    from scripts import run_news_discovery
    monkeypatch.setattr(run_news_discovery, "SessionLocal", lambda: pytest.fail("Invalid mode opened database"))
    monkeypatch.setattr(sys, "argv", ["collector", *args])
    with pytest.raises(SystemExit) as error:
        run_news_discovery.main()
    assert error.value.code == 2


def test_discovery_304_still_processes_previously_saved_evidence(queue_db, monkeypatch, capsys):
    from scripts import run_news_discovery
    from datetime import date
    source = NewsSource("example", "Example", ("example.org",), ("https://example.org/feed",), date(2026, 10, 1), True)
    with queue_db() as db, db.begin():
        db.add(article())
        db.add(NewsFeedCheckpoint(source_id="example", feed_url=source.feed_urls[0], etag="prior"))
    requests = []
    def handler(request):
        requests.append(str(request.url))
        assert request.headers["if-none-match"] == "prior"
        return httpx.Response(304, headers={"etag": "prior"})
    real_client = httpx.Client
    monkeypatch.setattr(run_news_discovery, "SessionLocal", queue_db)
    monkeypatch.setattr(run_news_discovery, "load_news_sources", lambda path: (source,))
    monkeypatch.setattr(run_news_discovery.httpx, "Client", lambda **kw: real_client(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(sys, "argv", ["collector", "--discover", "--process"])
    assert run_news_discovery.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["probes"][0]["status"] == "unchanged"
    assert payload["candidates"] == [] and payload["processing"]["completed"] == 1
    assert requests == [source.feed_urls[0]]


@pytest.mark.asyncio
async def test_bounded_capture_advances_past_completed_inputs(queue_db):
    with queue_db() as db, db.begin():
        db.add_all([article(i) for i in range(1, 6)])
    counts = [(await news_processing_service.process_saved_news(queue_db, limit=2, clock=lambda: NOW)).completed for _ in range(3)]
    assert counts == [2, 2, 1]


@pytest.mark.asyncio
async def test_corrupt_snapshot_fails_permanently_before_extraction(queue_db, monkeypatch):
    with queue_db() as db, db.begin():
        row = article()
        db.add(row)
        enqueue_article(db, row)
        version = db.scalar(select(NewsArticleVersion))
        # SQLite control simulates corrupt storage; PostgreSQL also prevents updates.
        version.input_snapshot = {**version.input_snapshot, "article_text": "changed"}
    monkeypatch.setattr(news_processing_service, "extract_captured_news_article", lambda source: pytest.fail("Corrupt source extracted"))
    result = await news_processing_service.process_saved_news(queue_db, clock=lambda: NOW)
    assert result.failed == 1 and result.runs[0]["error_code"] == "input_fingerprint_mismatch"
