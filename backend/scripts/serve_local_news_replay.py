"""Serve saved evidence and persisted APIs from a guarded private replay backend.

This launcher adds one read-only public-source preview route to a guarded
loopback test app. It never adds that route to the normal/cloud application.
"""
from datetime import datetime
from contextlib import contextmanager, ExitStack
from collections.abc import Iterator, AsyncIterator
from typing import Any
import os
from unittest.mock import patch

from scripts.seed_local_news_replay import require_local_test_database


def validate_target() -> None:
    from app.core.config import settings
    require_local_test_database(settings.DATABASE_URL)
    from app.core.database import engine
    require_local_test_database(engine.url.render_as_string(hide_password=False))


def simulation_clock() -> datetime:
    from scripts.replay_september24_pipeline import REPLAY_AT, available_articles
    clock = datetime.fromisoformat(os.environ.get("LANES_NEWS_SIMULATION_AT", REPLAY_AT.isoformat()))
    available_articles(clock)
    return clock


def simulation_snapshot() -> dict:
    validate_target()
    # An explicit requested addition can be captured/extracted in the normal
    # database. Reuse that service-produced snapshot and its actual run identity.
    import json
    from pathlib import Path
    from scripts.replay_september24_news import PUBLISHED, URL
    addition = Path(__file__).resolve().parents[2] / "data/news-replay/september24-cloud-addition.json"
    if addition.exists():
        from fastapi import HTTPException
        from app.schemas.news_results import NewsResultPlacementPreview
        if PUBLISHED > simulation_clock():
            raise HTTPException(409, "The article is not yet published at this simulation clock.")
        captured = json.loads(addition.read_text(encoding="utf-8"))
        if captured.get("source_url") != URL or not captured.get("existing_zones_unchanged"):
            raise HTTPException(503, "The connected-database capture could not be verified.")
        snapshot = captured["simulation_snapshot"]
        if snapshot.get("placement"):
            from app.services.news_placement_display_service import placement_display_sections, resolved_placement_display_zone
            placement = NewsResultPlacementPreview.model_validate(snapshot["placement"])
            placement.preview.display_sections = placement_display_sections(placement.preview.candidates)
            placement.preview.display_zone = resolved_placement_display_zone(placement.preview)
            snapshot["placement"] = placement.model_dump(mode="json")
        return snapshot
    from fastapi import HTTPException
    from sqlalchemy import text
    from app.core.database import SessionLocal
    from app.schemas.news_results import NewsResultPlacementPreview
    from app.services.news_results_service import browse_news_results, read_news_result
    from app.services.news_placement_preview_service import get_news_placement_preview_service
    from scripts.replay_september24_news import TITLE, URL
    clock = simulation_clock()
    with SessionLocal() as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        page = browse_news_results(db, page=1, page_size=100, search=TITLE, publisher=None,
            condition=None, placement=None, order="extraction_newest")
        items = [item for item in page.items if item.title == TITLE]
        if not items:
            raise HTTPException(503, "Run the real September 24 article capture/processing in the private database first.")
        service = get_news_placement_preview_service()
        placements = []
        for item in items:
            detail = read_news_result(db, item.run_id, item.claim_index)
            if detail.captured_input.canonical_url != URL:
                continue
            if item.published_at and item.published_at > clock:
                raise HTTPException(409, "The captured article was not yet published at this simulation clock.")
            placements.append(NewsResultPlacementPreview(run_id=item.run_id, claim_index=item.claim_index,
                input_fingerprint=detail.input_fingerprint, evidence_pipeline_version=detail.pipeline_version,
                placement_revision=service.revision, claim=detail.claim, preview=service.preview(detail.claim)))
        selected = next((p for p in placements if any(c.preview_geometry for c in p.preview.candidates)), None)
        db.rollback()
    return {"mode": "september24", "simulated_at": clock, "article_title": TITLE,
        "source_url": URL, "reported_locations": len(placements), "status": "Needs Review",
        "placement": selected.model_dump(mode="json") if selected else None,
        "modeled_candidates": sum(bool(c.preview_geometry) for c in selected.preview.candidates) if selected else 0,
        "routing_affected": False,
        "reason": "The original article yields modeled road candidates, but source/time/section checks do not permit active-zone creation.",
        "subsidence_reason": "These reported locations are outside the current Pasig prediction scope."}


@contextmanager
def simulation_reads(clock: datetime, *, publication_admission_at: datetime | None = None) -> Iterator[None]:
    """Keep persisted-zone eligibility and its news details on one private clock."""
    validate_target()
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise ValueError("Simulation clock requires a timezone offset")
    from app import crud
    from app.crud import report
    from app.services import news_publication_read_service, news_zone_projection_service, zone_prediction_service, spatial_review_service, flood_routing_policy
    from app.services import news_evaluation_service, news_pipeline_service
    from app.crud import spatial_review as review_crud
    from app.api.v1.endpoints import admin_news_publication
    normal_policy = news_evaluation_service.evaluation_policy
    normal_review_rows = review_crud.review_rows
    normal_reader = report.get_active_avoidance_zones
    normal_list = report.get_all_avoidance_zones_filtered
    normal_prediction = zone_prediction_service.predict_zone
    # Routing and SSE call the same SQL-backed eligibility reader, including
    # callers that imported it before this launcher configured the clock.
    from sqlalchemy import literal
    normal_sql_functions = flood_routing_policy.func
    class ReplaySQLFunctions:
        def now(self) -> Any:
            return literal(clock)
        def __getattr__(self, name: str) -> Any:
            return getattr(normal_sql_functions, name)
    with ExitStack() as stack:
        if publication_admission_at is not None:
            if publication_admission_at.tzinfo is None or publication_admission_at.utcoffset() is None:
                raise ValueError("Reconstruction publication clock requires a timezone offset")
            def replay_policy(auditor, configuration=None, **kwargs):
                return normal_policy(auditor, configuration,
                    publication_admission_at=kwargs.get("publication_admission_at") or publication_admission_at)
            for module in (news_evaluation_service, news_pipeline_service, admin_news_publication):
                stack.enter_context(patch.object(module, "evaluation_policy", replay_policy))
            stack.enter_context(patch.object(review_crud, "review_rows",
                lambda db, now: normal_review_rows(db, now, publication_admission_at=publication_admission_at)))
        reader = lambda db, **kwargs: normal_reader(db, now=kwargs.get("now", clock))
        stack.enter_context(patch.object(report, "get_active_avoidance_zones", reader))
        stack.enter_context(patch.object(crud, "get_active_avoidance_zones", reader))
        list_reader = lambda db, *args, **kwargs: normal_list(db, *args, **{**kwargs, "now": kwargs.get("now", clock)})
        stack.enter_context(patch.object(report, "get_all_avoidance_zones_filtered", list_reader))
        stack.enter_context(patch.object(crud, "get_all_avoidance_zones_filtered", list_reader))
        stack.enter_context(patch.object(news_publication_read_service, "publication_read_clock", lambda: clock))
        stack.enter_context(patch.object(news_zone_projection_service, "utc_now", lambda: clock))
        stack.enter_context(patch.object(spatial_review_service, "review_clock", lambda: clock))
        stack.enter_context(patch.object(flood_routing_policy, "func", ReplaySQLFunctions()))
        stack.enter_context(patch.object(zone_prediction_service, "predict_zone",
            lambda db, zone_id, user, **kwargs: normal_prediction(db, zone_id, user, now=kwargs.get("now", clock))))
        yield


def main() -> None:
    validate_target()
    import uvicorn
    from fastapi import Response
    from app.main import app, origins
    # Only this guarded loopback process accepts the dedicated browser origin.
    origins.extend(["http://127.0.0.1:3001", "http://localhost:3001"])
    clock = simulation_clock()

    @app.get("/api/v1/news/simulation")
    def read_simulation(response: Response) -> dict:
        response.headers["Cache-Control"] = "no-store"
        return simulation_snapshot()

    # Background retention uses wall time; it must not purge historical replay
    # evidence while the operator inspects a frozen simulated present.
    from contextlib import asynccontextmanager
    from fastapi import FastAPI
    @asynccontextmanager
    async def replay_lifespan(_application: FastAPI) -> AsyncIterator[None]:
        yield
        from app.services.flood_sync_service import flood_sync
        await flood_sync.close()
    app.router.lifespan_context = replay_lifespan
    reconstruction_at = os.environ.get("LANES_NEWS_RECONSTRUCTION_PUBLICATION_AT")
    with simulation_reads(clock, publication_admission_at=datetime.fromisoformat(reconstruction_at) if reconstruction_at else None):
        uvicorn.run(app, host="127.0.0.1", port=8001)


if __name__ == "__main__":
    main()
