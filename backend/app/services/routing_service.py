"""Provider orchestration for online flood-safe routing."""

import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.services import ors_service, valhalla_service

logger = logging.getLogger(__name__)


async def calculate_route(payload: schemas.RouteRequest, db: Session) -> dict[str, Any]:
    """Use the selected provider, with ORS as the Valhalla availability fallback."""
    if payload.engine == "ors":
        response = await ors_service.calculate_flood_safe_route(
            db=db,
            start=payload.start,
            end=payload.end,
            ignore_floods=payload.ignore_floods,
            vehicle_profile=payload.vehicle_profile,
        )
        return {**response, "engine_used": "ors", "fallback_used": False}

    try:
        response = valhalla_service.calculate_flood_safe_route(
            db=db,
            start=payload.start,
            end=payload.end,
            ignore_floods=payload.ignore_floods,
            vehicle_profile=payload.vehicle_profile,
            heading=payload.heading,
        )
        return {**response, "engine_used": "valhalla", "fallback_used": False}
    except valhalla_service.ValhallaServiceUnavailable as valhalla_error:
        logger.warning("routing_ors_fallback reason=%s", valhalla_error)
        try:
            response = await ors_service.calculate_flood_safe_route(
                db=db,
                start=payload.start,
                end=payload.end,
                ignore_floods=payload.ignore_floods,
                vehicle_profile=payload.vehicle_profile,
            )
            logger.info("routing_ors_fallback_succeeded")
            return {**response, "engine_used": "ors", "fallback_used": True}
        except HTTPException as ors_error:
            logger.error("routing_ors_fallback_failed status=%s", ors_error.status_code)
            raise HTTPException(
                status_code=503,
                detail="Routing is temporarily unavailable. Please try again shortly.",
            ) from ors_error
