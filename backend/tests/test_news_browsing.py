"""Article browsing enforces staff access, version provenance and read-only reads."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.core.database import get_db
from app.main import app
from app.models.news import NewsArticle, NewsArticleFeedEntry, NewsArticleVersion, NewsExtractionRun
from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_discovery_service import extraction_input_snapshot
from app.services.taglish_extraction_service import extract_taglish_flood_facts

NOW = datetime(2026, 10, 2, 10, tzinfo=timezone.utc)


@compiles(JSONB, "sqlite")
def sqlite_jsonb(_type: JSONB, _compiler: object, **_kw: object) -> str:
    return "JSON"


@pytest.fixture
def evidence_db(request):
    engine = create_engine("sqlite+pysqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    NewsArticle.metadata.create_all(engine, tables=[NewsArticle.__table__, NewsArticleFeedEntry.__table__, NewsArticleVersion.__table__, NewsExtractionRun.__table__])
    with Session(engine) as db:
        for id, title, publisher, body, error, publication in [
            (1, "Baha sa Pasig", "feedspot-01", "New body", None, NOW),
            (2, "Flood 100% verified?", "feedspot-05", None, None, None),
            (3, "Flood advisory", "feedspot-05", "Last successful body", "Article HTTP 403", NOW - timedelta(days=1)),
        ]:
            db.add(NewsArticle(id=id, canonical_url=f"https://example.org/{id}", title=title,
                publisher_source_id=publisher, excerpt="Publisher excerpt", article_text=body, article_error=error,
                published_at=publication, first_seen_at=NOW, last_seen_at=NOW, content_fingerprint="0" * 64,
                review_state="approved" if id == 2 else "pending"))
        source = NewsArticleExtractorInput(article_id=1, canonical_url="https://example.org/1", publisher="feedspot-01",
            title="Older headline", article_text="As of 10 AM, abot-tuhod ang baha sa Maybunga, Pasig City.", published_at=NOW)
        snapshot, fingerprint = extraction_input_snapshot(source)
        db.add(NewsArticleVersion(id=1, article_id=1, input_snapshot=snapshot, input_fingerprint=fingerprint, created_at=NOW))
        source.article_text = "New body"
        new_snapshot, new_fingerprint = extraction_input_snapshot(source)
        db.add(NewsArticleVersion(id=2, article_id=1, input_snapshot=new_snapshot, input_fingerprint=new_fingerprint, created_at=NOW))
        db.flush()
        result = extract_taglish_flood_facts(NewsArticleExtractorInput(article_id=1, **snapshot))
        db.add_all([
            NewsExtractionRun(id=1, article_version_id=1, pipeline_version="test-old", status="completed", mode="rules_only",
                result=result.model_dump(mode="json"), attempt_count=1, created_at=NOW, updated_at=NOW, completed_at=NOW),
            NewsExtractionRun(id=2, article_version_id=2, pipeline_version="test-new", status="failed", mode="rules_only",
                error_code="extraction_failed", attempt_count=5, created_at=NOW, updated_at=NOW, completed_at=NOW),
        ])
        for index in range(getattr(request, "param", 0)):
            db.add(NewsExtractionRun(id=index + 3, article_version_id=2, pipeline_version=f"test-history-{index}",
                status="pending", mode="rules_only", attempt_count=0, created_at=NOW, updated_at=NOW))
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
        yield writes
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(deps.get_current_user, None)
        engine.dispose()


def staff() -> None:
    app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Admin"))


@pytest.mark.asyncio
async def test_staff_guard_pagination_filters_and_no_writes(evidence_db):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        for path in ["/api/v1/admin/news/articles", "/api/v1/admin/news/articles/1"]:
            assert (await client.get(path)).status_code == 401
        app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Commuter"))
        for path in ["/api/v1/admin/news/articles", "/api/v1/admin/news/articles/1"]:
            assert (await client.get(path)).status_code == 403
        staff()
        async def read(**params):
            response = await client.get("/api/v1/admin/news/articles", params=params)
            assert response.status_code == 200, response.text
            return response.json()
        page = await read(page_size=2)
        assert page["total"] == 3 and page["pages"] == 2
        assert [item["id"] for item in page["items"]] == [3, 2]  # Ties use stable ID ordering.
        assert "article_text" not in page["items"][0]
        assert page["items"][0]["body_status"] == "error"
        assert page["items"][1]["review_state"] == "approved"  # All saved evidence, not pending only.
        second = await read(page_size=2, page=2)
        assert second["items"][0]["processing_status"] == "failed"  # Latest run, not an older success.
        assert (await read(page_size=2, page=999))["page"] == 2
        assert [item["id"] for item in (await read(order="publication_newest"))["items"]] == [1, 3, 2]
        assert (await read(body="missing"))["items"][0]["id"] == 2
        assert (await read(processing="completed"))["total"] == 0
        assert (await read(processing="failed"))["items"][0]["latest_run_id"] == 2
        assert (await read(publisher="feedspot-01"))["total"] == 1
        assert (await read(search="100%"))["total"] == 1
        assert (await read(search="_"))["total"] == 0
        assert {item["label"] for item in page["publishers"]} == {"GMA News Online", "Philstar.com"}
        for params in [{"body": "bogus"}, {"page_size": 51}, {"page": 0}, {"processing": "approved"}, {"search": "x" * 201}]:
            assert (await client.get("/api/v1/admin/news/articles", params=params)).status_code == 422
    assert not evidence_db


@pytest.mark.asyncio
async def test_detail_keeps_each_run_bound_to_immutable_evidence(evidence_db):
    staff()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/admin/news/articles/1")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["read_only"] is True
        assert data["article"]["article_text"] == "New body"
        assert [run["id"] for run in data["runs"]] == [2, 1]
        assert data["history_total"] == 2 and data["history_limit"] == 20
        versions = {version["id"]: version for version in data["versions"]}
        old_run = data["runs"][1]
        old_input = versions[old_run["article_version_id"]]["input_snapshot"]
        assert "abot-tuhod" in old_input["article_text"]
        assert old_input["title"] == "Older headline"
        assert any(claim["depth_canonical"] == "knee" for claim in old_run["result"]["claims"])
        assert (await client.get("/api/v1/admin/news/articles/2")).json()["runs"] == []
        assert (await client.get("/api/v1/admin/news/articles/999")).status_code == 404
    assert not evidence_db


@pytest.mark.asyncio
async def test_storage_errors_are_visible(evidence_db, monkeypatch):
    from sqlalchemy.exc import OperationalError
    from app.api.v1.endpoints import admin_news
    staff()
    def fail(*args, **kwargs):
        raise OperationalError("private connection string", {}, Exception("private details"))
    monkeypatch.setattr(admin_news, "browse_news_articles", fail)
    monkeypatch.setattr(admin_news, "read_news_article_detail", fail)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        for path in ["/api/v1/admin/news/articles", "/api/v1/admin/news/articles/1"]:
            response = await client.get(path)
            assert response.status_code == 503
            assert response.json()["detail"] == "News article storage is unavailable"
            assert "private" not in response.text
    assert not evidence_db


@pytest.mark.parametrize("evidence_db", [25], indirect=True)
@pytest.mark.asyncio
async def test_detail_history_is_bounded_without_unrelated_versions(evidence_db):
    staff()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/admin/news/articles/1")
        assert response.status_code == 200
        data = response.json()
        assert data["history_total"] == 27
        assert len(data["runs"]) == data["history_limit"] == 20
        assert [run["id"] for run in data["runs"]] == list(range(27, 7, -1))
        assert [version["id"] for version in data["versions"]] == [2]
    assert not evidence_db
