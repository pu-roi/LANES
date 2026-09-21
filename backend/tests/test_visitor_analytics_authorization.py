from contextlib import asynccontextmanager

from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.api import deps
from app.main import app


@asynccontextmanager
async def _no_database_lifespan(_app):
    yield


def _deny_non_admin() -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="The user doesn't have enough privileges",
    )


def test_visitor_analytics_is_not_available_to_non_admins() -> None:
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _no_database_lifespan
    app.dependency_overrides[deps.get_current_active_admin] = _deny_non_admin
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/admin/dashboard/visitors")
            assert response.status_code == status.HTTP_403_FORBIDDEN
    finally:
        app.dependency_overrides.pop(deps.get_current_active_admin, None)
        app.router.lifespan_context = original_lifespan
