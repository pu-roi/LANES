"""Provider orchestration for online flood-safe routing."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app import schemas
from app.services import ors_service, valhalla_service
from app.services.flood_routing_policy import (
    get_active_flood_zones,
    evaluate_route,
    polygons_for,
    rank_routes,
)

logger = logging.getLogger(__name__)


async def calculate_route(payload: schemas.RouteRequest, db: Session) -> dict[str, Any]:
    """Generate provider candidates, then apply one flood policy and ranker."""
    # Keep the legacy request field for older clients, but never let a public
    # navigation request opt out of hard flood exclusions.
    zones = get_active_flood_zones(db)
    hard_polygons = polygons_for(zones, payload.vehicle_profile, {"blocked"})
    cautious_polygons = polygons_for(zones, payload.vehicle_profile, {"cautious"})

    async def fetch(engine: str, exclusions: list[list[list[float]]]) -> list[dict[str, Any]]:
        if engine == "ors":
            return await ors_service.fetch_route_candidates(
                start=payload.start, end=payload.end,
                exclude_polygons=exclusions, vehicle_profile=payload.vehicle_profile,
            )
        return valhalla_service.fetch_route_candidates(
            start=payload.start, end=payload.end,
            exclude_polygons=exclusions, vehicle_profile=payload.vehicle_profile,
            heading=payload.heading,
        )

    async def route_with(engine: str) -> dict[str, Any]:
        # The unfiltered baseline is never navigable by itself. It lets LANES
        # explain an unsafe direct route only after actual intersection checks.
        raw_candidates = await fetch(engine, [])
        if zones:
            raw_candidates.extend(await fetch(engine, hard_polygons))
            if cautious_polygons:
                raw_candidates.extend(await fetch(engine, hard_polygons + cautious_polygons))
        evaluated = [evaluate_route(candidate, zones, payload.vehicle_profile) for candidate in raw_candidates]
        routes, baseline = rank_routes(evaluated)
        baseline_summary = None
        if baseline:
            baseline_summary = {
                "distance": baseline["distance"],
                "duration": baseline["duration"],
                "flood_exposure": baseline["flood_exposure"],
                "message": "The normal fastest route crosses floodwater that is impassable for the selected travel type.",
            }
        if not routes:
            return {"routes": [], "recommended_index": -1, "blocked_baseline": baseline_summary}
        return {"routes": routes, "recommended_index": 0, "blocked_baseline": baseline_summary}

    if payload.engine == "ors":
        response = await route_with("ors")
        return {**response, "engine_used": "ors", "fallback_used": False}
    try:
        response = await route_with("valhalla")
        return {**response, "engine_used": "valhalla", "fallback_used": False}
    except valhalla_service.ValhallaServiceUnavailable as error:
        logger.warning("routing_ors_fallback reason=%s", error)
        response = await route_with("ors")
        return {**response, "engine_used": "ors", "fallback_used": True}
