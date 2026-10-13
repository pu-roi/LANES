"""Local review-only API without app.main's seeding or maintenance lifespan."""
from fastapi import FastAPI

from app.api.v1.endpoints.mcp_review import router


def create_app() -> FastAPI:
    app = FastAPI(title="LANES MCP review pilot", docs_url=None, redoc_url=None, openapi_url=None)
    app.include_router(router, prefix="/api/v1/internal/mcp-review")
    return app
