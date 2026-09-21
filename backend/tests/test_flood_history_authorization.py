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
                "/api/v1/admin/flood-events/analytics",
                "/api/v1/admin/flood-events/export",
                "/api/v1/admin/flood-events/999999/history-detail",
            ):
                response = client.get(path)
                assert response.status_code == status.HTTP_403_FORBIDDEN
    finally:
        app.dependency_overrides.pop(deps.get_current_active_admin, None)
        app.router.lifespan_context = original_lifespan
