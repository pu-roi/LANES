"""Publication API permissions run before lookup; public output stays private-field free."""
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.api import deps
from app.api.v1.endpoints import admin_news_publication, news_alerts
from app.core.database import get_db
from app.crud.news_publication import NewsPublicationError
from app.main import app
from app.schemas.news_publication import PublicNewsAlert, PublicNewsAlertPage

NOW = datetime(2026, 10, 5, 12, tzinfo=timezone.utc)


def alert(**changes):
    return PublicNewsAlert(case_id=1, decision_id=2, revision=1, status="Active",
        location_label="C5, Ugong, Pasig", location_qualifier="Exact affected footprint is unverified",
        depth_label="knee-deep", condition_label="Reported flooding",
        passability_label="Not established by this alert", observed_at=NOW, expires_at=NOW,
        updated_at=NOW, source_title="Flood report", source_publisher="Fixture publisher",
        source_url="https://example.org/report", source_published_at=NOW,
        evidence_excerpt="Source-reported flooding", **changes)


@pytest.fixture
def api_state(monkeypatch):
    calls = []
    db = SimpleNamespace(commit=lambda: calls.append("commit"), rollback=lambda: calls.append("rollback"))
    overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield calls, db
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(overrides)


@pytest.mark.asyncio
async def test_public_read_safe_projection_and_bounds(api_state, monkeypatch):
    calls, _ = api_state
    def browse(db, **params):
        calls.append(params)
        return PublicNewsAlertPage(items=[alert()], total=1, page=1, page_size=params["page_size"], pages=1, as_of=NOW)
    monkeypatch.setattr(news_alerts, "browse_public_news_alerts", browse)
    monkeypatch.setattr(news_alerts, "read_public_news_alert", lambda *_: alert())
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/news/alerts")
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        body = response.json()
        assert body["items"][0]["affects_routing"] is False
        assert body["items"][0]["display_geojson"] is None
        assert not {"private_reason", "audit", "captured_input", "provider", "request_sha256"} & body["items"][0].keys()
        assert (await client.get("/api/v1/news/alerts/1")).status_code == 200
        for params in ({"page": 0}, {"page_size": 101}, {"page_size": 0}):
            assert (await client.get("/api/v1/news/alerts", params=params)).status_code == 422
        assert (await client.get("/api/v1/news/alerts/0")).status_code == 422
    assert "commit" not in calls and "rollback" not in calls


@pytest.mark.asyncio
async def test_public_storage_errors_are_visible_and_sanitized(api_state, monkeypatch):
    def unavailable(*_, **__):
        raise SQLAlchemyError("sensitive connection details")
    monkeypatch.setattr(news_alerts, "browse_public_news_alerts", unavailable)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/news/alerts")
        assert response.status_code == 503
        assert "sensitive" not in response.text
        monkeypatch.setattr(news_alerts, "read_public_news_alert", lambda *_: None)
        assert (await client.get("/api/v1/news/alerts/4")).status_code == 404


@pytest.mark.asyncio
async def test_staff_guards_before_evidence_lookup(api_state, monkeypatch):
    def unexpected(*_, **__):
        raise AssertionError("Unauthorized evidence lookup")
    monkeypatch.setattr(admin_news_publication, "read_news_claim_detail", unexpected)
    paths = ["/api/v1/admin/news/claims/1", "/api/v1/admin/news/claims/1/history"]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        for path in paths:
            assert (await client.get(path)).status_code == 401
        for role, permissions in (("Commuter", {"reports": "full"}), ("Officer", {}), ("Officer", {"reports": "none"})):
            app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id=7, role=SimpleNamespace(name=role, permissions=permissions))
            for path in paths:
                assert (await client.get(path)).status_code == 403


@pytest.mark.asyncio
async def test_read_only_staff_cannot_submit_decisions(api_state):
    app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id=7, role=SimpleNamespace(name="Officer", permissions={"reports": "view"}))
    body = dict(request_id=str(uuid4()), expected_revision=1, operation="reject", reason="Incorrect evidence")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/admin/news/claims/1/decisions", json=body)
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_decision_conflict_rolls_back_and_never_broadcasts(api_state, monkeypatch):
    from app.services import news_publication_service
    calls, _ = api_state
    app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id=7, role=SimpleNamespace(name="Officer", permissions={"reports": "full"}))
    app.dependency_overrides[admin_news_publication.publication_policy] = lambda: SimpleNamespace()
    def conflict(*_, **__):
        raise NewsPublicationError("stale_revision", 409, revision=3)
    monkeypatch.setattr(news_publication_service, "apply_staff_decision", conflict)
    async def broadcast(_):
        calls.append("broadcast")
    monkeypatch.setattr(admin_news_publication.manager, "broadcast", broadcast)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/admin/news/claims/1/decisions", json=dict(
            request_id=str(uuid4()), expected_revision=2, operation="reject", reason="Incorrect evidence"))
        assert response.status_code == 409 and response.json()["detail"]["current_revision"] == 3
    assert calls == ["rollback"]


@pytest.mark.asyncio
async def test_success_commits_before_safe_invalidation(api_state, monkeypatch):
    from app.services import news_publication_service
    calls, _ = api_state
    app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id=7, role=SimpleNamespace(name="Officer", permissions={"reports": "full"}))
    app.dependency_overrides[admin_news_publication.publication_policy] = lambda: SimpleNamespace()
    decision = SimpleNamespace(id=5, revision=2, operation="reject", public_state="withdrawn", review_state="resolved",
                               reason_code="staff_rejected", decided_at=NOW, observed_at=None, expires_at=None)
    monkeypatch.setattr(news_publication_service, "apply_staff_decision", lambda *_, **__: decision)
    async def broadcast(message):
        assert calls == ["commit"]
        assert message == {"type": "news_updated", "case_id": 1}
        calls.append("broadcast")
    monkeypatch.setattr(admin_news_publication.manager, "broadcast", broadcast)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/admin/news/claims/1/decisions", json=dict(
            request_id=str(uuid4()), expected_revision=1, operation="reject", reason="Private internal explanation"))
        assert response.status_code == 200 and "Private internal" not in response.text
    assert calls == ["commit", "broadcast"]
