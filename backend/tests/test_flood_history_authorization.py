from contextlib import asynccontextmanager

from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.api import deps
from app.main import app


@asynccontextmanager
async def _no_database_lifespan(_app):
    """Keep authorization tests independent from the developer's local database."""
    yield


def _deny_non_admin() -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="The user doesn't have enough privileges",
    )


def test_flood_history_and_export_routes_reject_non_admin_and_guessed_ids() -> None:
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _no_database_lifespan
    app.dependency_overrides[deps.get_current_active_admin] = _deny_non_admin
    try:
        with TestClient(app) as client:
            for path in (
                "/api/v1/admin/flood-events/history",
                "/api/v1/admin/flood-events/history?page=1&page_size=20",
                "/api/v1/admin/flood-events/history?summary=true&limit=250",
                "/api/v1/admin/flood-events/analytics",
                "/api/v1/admin/flood-events/export",
                "/api/v1/admin/flood-events/999999/history-detail",
            ):
                response = client.get(path)
                assert response.status_code == status.HTTP_403_FORBIDDEN
    finally:
        app.dependency_overrides.pop(deps.get_current_active_admin, None)
        app.router.lifespan_context = original_lifespan


def test_history_database_failure_returns_retryable_service_error(monkeypatch) -> None:
    from sqlalchemy.exc import SQLAlchemyError
    from app.api.v1.endpoints import admin
    from app.core.database import get_db

    def unavailable(*_args, **_kwargs):
        raise SQLAlchemyError("Unavailable test database")

    monkeypatch.setattr(admin, "flood_history_window", unavailable)
    # Authorization is exercised separately; this isolated request tests error serialization.
    app.dependency_overrides[deps.get_current_active_admin] = lambda: object()
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(admin, "build_flood_event_history_query", lambda *_args, **_kwargs: object())
    try:
        response = TestClient(app).get("/api/v1/admin/flood-events/history?summary=true")
        assert response.status_code == 503
        assert "temporarily unavailable" in response.json()["detail"]
        assert "test database" not in response.text
    finally:
        app.dependency_overrides.pop(deps.get_current_active_admin, None)
        app.dependency_overrides.pop(get_db, None)
