from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import schemas

router = APIRouter()


class BidirectionalPreviewRequest(BaseModel):
    # ``coordinates`` keeps older clients compatible. New clients send the raw
    # anchors so the backend—not a legal-driving preview route—builds the line.
    coordinates: Optional[list] = None
    start: Optional[list[float]] = None
    end: Optional[list[float]] = None
    is_bidirectional: bool = True
    road_name: Optional[str] = None  # Optional road name for validation


class BidirectionalPreviewResponse(BaseModel):
    original: dict  # GeoJSON LineString of the original road
    opposite: Optional[dict] = None  # GeoJSON LineString of opposite carriageway (None if one-way)
    coverage_geometry: dict
    is_divided: bool  # True if a valid opposite carriageway was found
    road_type: str
    validation_status: str
    message: str


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
    from app.services.carriageway_service import build_road_segment_preview

    start = payload.start
    end = payload.end
    if (not start or not end) and payload.coordinates and len(payload.coordinates) >= 2:
        start = payload.coordinates[0]
        end = payload.coordinates[-1]
    if not start or not end or len(start) != 2 or len(end) != 2:
        raise HTTPException(status_code=422, detail="Start and end coordinates are required.")

    return BidirectionalPreviewResponse(**build_road_segment_preview(
        start=start,
        end=end,
        is_bidirectional=payload.is_bidirectional,
        road_name=payload.road_name,
    ))
