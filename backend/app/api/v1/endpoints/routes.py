from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import schemas

router = APIRouter()


class BidirectionalPreviewRequest(BaseModel):
    coordinates: list  # List of [lng, lat] points forming the original road segment
    road_name: Optional[str] = None  # Optional road name for validation


class BidirectionalPreviewResponse(BaseModel):
    original: dict  # GeoJSON LineString of the original road
    opposite: Optional[dict] = None  # GeoJSON LineString of opposite carriageway (None if one-way)
    is_divided: bool  # True if a valid opposite carriageway was found
    road_type: str  # NARROW_TWO_WAY, DIVIDED_CARRIAGEWAY, TRUE_ONE_WAY, UNMAPPED


@router.post("", response_model=schemas.MultiRouteResponse)
@router.post("/route", response_model=schemas.MultiRouteResponse)
async def calculate_route(payload: schemas.RouteRequest, db: Session = Depends(get_db)):
    """
    Calculates flood-safe alternative routes between start and end coordinates.
    Primary Engine: Valhalla (online/local).
    Fallback Engine: OpenRouteService.
    Each candidate is evaluated against active flood avoidance zones.
    """
    if payload.engine == "valhalla":
        from app.services.valhalla_service import calculate_flood_safe_route as valhalla_route
        return valhalla_route(
            db=db,
            start=payload.start,
            end=payload.end,
            ignore_floods=payload.ignore_floods,
            vehicle_profile=payload.vehicle_profile,
            heading=payload.heading
        )

    from app.services.ors_service import calculate_flood_safe_route as ors_route
    return await ors_route(
        db=db,
        start=payload.start,
        end=payload.end,
        ignore_floods=payload.ignore_floods,
        vehicle_profile=payload.vehicle_profile
    )


@router.post("/preview-bidirectional", response_model=BidirectionalPreviewResponse)
def preview_bidirectional(payload: BidirectionalPreviewRequest):
    """
    Given a list of coordinates forming a road segment, uses the Traversability-Aware
    Hybrid Strategy (perpendicular dynamic offset + Valhalla map-matching + name validation)
    to detect and return the actual opposite carriageway geometry for preview before submission.
    """
    from app.services.valhalla_service import find_opposite_carriageway

    original_geom = {
        "type": "LineString",
        "coordinates": payload.coordinates
    }

    road_type, opposite_geom = find_opposite_carriageway(
        route_coords=payload.coordinates,
        original_road_name=payload.road_name
    )

    return BidirectionalPreviewResponse(
        original=original_geom,
        opposite=opposite_geom,
        is_divided=opposite_geom is not None,
        road_type=road_type
    )
