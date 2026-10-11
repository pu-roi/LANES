"""Saved evidence handoff: real rules, stable identity, staff access, no writes."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.core.database import get_db
from app.core.limiter import limiter
from app.main import app
from app.models.news import NewsArticle, NewsArticleFeedEntry
from app.services.hybrid_extraction_service import HybridExtractionService
from app.services.news_discovery_service import extract_saved_news_articles
from app.services.news_auto_ingestion_service import NewsAutoIngestionService


def article(article_id: int = 1, **changes: object) -> NewsArticle:
    values = dict(id=article_id, canonical_url=f"https://news.example.org/{article_id}",
                  publisher_source_id="example", title="Baha sa Maybunga, Pasig City", excerpt="",
                  published_at=datetime(2026, 10, 1, 11, tzinfo=timezone(timedelta(hours=8))),
                  fetched_at=datetime.now(timezone.utc), review_state="pending", content_fingerprint="0" * 64,
                  last_seen_at=datetime(2026, 10, 1, 12, tzinfo=timezone.utc) + timedelta(minutes=article_id),
                  article_text="Binaha ang Barangay Maybunga sa Pasig City, abot-tuhod ang tubig as of 10 a.m.")
    values.update(changes)
    return NewsArticle(**values)


@pytest.fixture(autouse=True)
def prohibit_auditor_and_ingestion(monkeypatch: pytest.MonkeyPatch) -> None:
    async def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Saved preview invoked external audit or zone ingestion")
    monkeypatch.setattr(HybridExtractionService, "audit_claim_with_llm", forbidden)
    monkeypatch.setattr(NewsAutoIngestionService, "process_and_ingest_article", forbidden)


@pytest.mark.asyncio
async def test_saved_extraction_uses_real_id_body_time_and_keeps_review_state() -> None:
    row = article()
    first, = await extract_saved_news_articles([row])
    assert first.error is None
    assert first.article_id == row.id == first.extraction.article_id
    assert first.extraction.is_metadata_only is False
    claim = next(claim for claim in first.extraction.claims if claim.canonical_barangay == "Maybunga")
    assert claim.canonical_city == "City of Pasig"
    assert claim.depth_canonical == "knee"
    assert claim.event_time_resolved is not None
    assert claim.event_time_resolved.hour == 10
    assert claim.action_type != "auto_approved"
    assert row.review_state == "pending"
    row.fetched_at += timedelta(hours=1)
    second, = await extract_saved_news_articles([row])
    assert second.input_fingerprint == first.input_fingerprint
    row.published_at = row.published_at.astimezone(timezone.utc)
    equivalent, = await extract_saved_news_articles([row])
    assert equivalent.input_fingerprint == first.input_fingerprint
    row.article_text = row.article_text.replace("abot-tuhod", "abot-dibdib")
    changed, = await extract_saved_news_articles([row])
    assert changed.input_fingerprint != first.input_fingerprint


@pytest.mark.parametrize("changes,expected", [
    ({"article_text": None}, "Article body unavailable"),
    ({"article_error": "Article HTTP 403"}, "Article HTTP 403"),
    ({"article_text": "x" * 100_001}, "Article text exceeds processing limit"),
])
@pytest.mark.asyncio
async def test_saved_unavailable_or_errored_body_does_not_extract(changes: dict, expected: str,
                                                               monkeypatch: pytest.MonkeyPatch) -> None:
    async def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Unavailable body entered extraction")
    monkeypatch.setattr(HybridExtractionService, "extract_hybrid", forbidden)
    result, = await extract_saved_news_articles([article(**changes)])
    assert result.error == expected
    assert result.extraction is None


@pytest.mark.asyncio
async def test_saved_batch_failure_is_visible_and_does_not_lose_later_article(monkeypatch: pytest.MonkeyPatch) -> None:
    real_extract = HybridExtractionService.extract_hybrid
    async def extract(self: HybridExtractionService, source: object, mode: str):
        if source.article_id == 1:
            raise RuntimeError("private error details")
        return await real_extract(self, source, mode=mode)
    monkeypatch.setattr(HybridExtractionService, "extract_hybrid", extract)
    failed, successful = await extract_saved_news_articles([article(), article(2)])
    assert failed.error == "Extraction failed: RuntimeError"
    assert successful.extraction.article_id == 2
    assert successful.error is None


@pytest.fixture
def saved_db():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    NewsArticle.metadata.create_all(engine, tables=[NewsArticle.__table__, NewsArticleFeedEntry.__table__])
    with Session(engine) as db:
        db.add_all([article(), article(2, article_error="Article HTTP 403")])
        db.commit()
    writes: list[str] = []
    def record(_connection, _cursor, statement: str, _parameters, _context, _many) -> None:
        if statement.lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE"}:
            writes.append(statement)
    event.listen(engine, "before_cursor_execute", record)
    try:
        yield engine, writes
    finally:
        engine.dispose()


@pytest.mark.asyncio
async def test_saved_preview_api_checks_staff_access_and_preserves_evidence(saved_db) -> None:
    engine, writes = saved_db
    limiter.reset()
    def test_db():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = test_db
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            url = "/api/v1/admin/news/candidates/1/extraction"
            assert (await client.get(url)).status_code == 401
            app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Commuter"))
            assert (await client.get(url)).status_code == 403
            app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Admin"))
            response = await client.get(url)
            assert response.status_code == 200
            data = response.json()
            assert data["read_only"] is True
            assert data["article_id"] == data["extraction"]["article_id"] == 1
            assert len(data["input_fingerprint"]) == 64
            assert data["extraction_mode"] == "rules_only"
            assert any(claim["depth_canonical"] == "knee" for claim in data["extraction"]["claims"])
            blocked = await client.get("/api/v1/admin/news/candidates/2/extraction")
            assert blocked.json()["error"] == "Article HTTP 403"
            assert blocked.json()["extraction"] is None
            assert (await client.get("/api/v1/admin/news/candidates/999/extraction")).status_code == 404
        with Session(engine) as db:
            assert db.get(NewsArticle, 1).review_state == "pending"
            assert db.get(NewsArticle, 2).article_error == "Article HTTP 403"
        assert not writes
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(deps.get_current_user, None)
        limiter.reset()


@compiles(JSONB, "sqlite")
def _sqlite_jsonb(_type: JSONB, _compiler: object, **_kw: object) -> str:
    return "JSON"


def test_saved_cli_reads_pending_rows_and_surfaces_failure_without_writes(saved_db, monkeypatch: pytest.MonkeyPatch,
                                                                       capsys: pytest.CaptureFixture[str]) -> None:
    import json
    import sys
    from scripts import run_news_discovery
    engine, writes = saved_db
    monkeypatch.setattr(run_news_discovery, "SessionLocal", lambda: Session(engine))
    monkeypatch.setattr(sys, "argv", ["collector", "--extract-saved", "--dry-run", "--limit", "2"])
    assert run_news_discovery.main() == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["outcome"] == "extraction_errors"
    assert payload["read_only"] is True
    results = {item["article_id"]: item for item in payload["extractions"]}
    assert list(results) == [2, 1]
    assert results[1]["extraction"]["claims"]
    assert results[2]["error"] == "Article HTTP 403"
    assert not writes


@pytest.mark.parametrize("args", [
    ["--extract-saved"], ["--extract-saved", "--dry-run", "--limit", "201"],
    ["--extract-saved", "--dry-run", "--source", "example"],
])
def test_saved_cli_rejects_invalid_modes_before_database(monkeypatch: pytest.MonkeyPatch, args: list[str]) -> None:
    import sys
    from scripts import run_news_discovery
    monkeypatch.setattr(run_news_discovery, "SessionLocal", lambda: pytest.fail("Invalid mode accessed database"))
    monkeypatch.setattr(sys, "argv", ["collector", *args])
    with pytest.raises(SystemExit) as exc:
        run_news_discovery.main()
    assert exc.value.code == 2


def test_saved_cli_empty_pending_list_does_not_claim_successful_extraction(saved_db, monkeypatch: pytest.MonkeyPatch,
                                                                       capsys: pytest.CaptureFixture[str]) -> None:
    import json
    import sys
    from scripts import run_news_discovery
    engine, writes = saved_db
    with Session(engine) as db:
        for row in db.scalars(select(NewsArticle)):
            row.review_state = "flagged_review"
        db.commit()
    writes.clear()
    monkeypatch.setattr(run_news_discovery, "SessionLocal", lambda: Session(engine))
    monkeypatch.setattr(sys, "argv", ["collector", "--extract-saved", "--dry-run"])
    assert run_news_discovery.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["outcome"] == "no_candidates"
    assert payload["extractions"] == []
    assert not writes
