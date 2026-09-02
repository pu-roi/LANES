from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
import json

from app import crud, schemas
from app.core.database import get_db
from app.services.cloudinary_service import upload_image

router = APIRouter()


from app.services.report_service import process_new_report

from app.api.deps import get_current_user
from app import models

@router.post("", response_model=schemas.FloodReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    raw_text: str = Form(...),
    source: str = Form(...),
    severity: str = Form("medium"),
    depth: str = Form(None),
    human_readable_location: str = Form(None),
    is_public: bool = Form(False),
    is_bidirectional: bool = Form(False),
    geometry: str = Form(None),
    survey_data: str = Form(None),
    media: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Submit a new flood report (raw Taglish text and optional coordinates/image).
    """
    media_urls = []
    for file in media:
        if file and file.filename:
            url = upload_image(file)
            if url:
                media_urls.append(url)

    geom_obj = None
    if geometry:
        try:
            geom_obj = json.loads(geometry)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid geometry JSON: {e}")

    survey_obj = None
    if survey_data:
        try:
            survey_obj = json.loads(survey_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid survey_data JSON: {e}")

    return await process_new_report(
        db=db,
        raw_text=raw_text,
        source=source,
        severity=severity,
        depth=depth,
        human_readable_location=human_readable_location,
        is_public=is_public,
        is_bidirectional=is_bidirectional,
        geometry=geom_obj,
        media_urls=media_urls,
        user_id=current_user.id,
        survey_data=survey_obj
    )


@router.get("/me", response_model=List[schemas.FloodReportResponse])
def read_my_reports(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve flood reports submitted by the current user.
    """
    try:
        return crud.get_flood_reports_by_user(db=db, user_id=current_user.id, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database is offline: {e}")


@router.get("", response_model=List[schemas.FloodReportResponse])
def read_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve list of flood reports (paginated).
    """
    try:
        return crud.get_flood_reports(db=db, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database is offline: {e}")


@router.get("/active-zones", response_model=List[schemas.FloodAvoidanceZoneResponse])
def read_active_avoidance_zones(db: Session = Depends(get_db)):
    """
    Retrieve all active flood avoidance zones (polygons representing detour zones).
    """
    try:
        return crud.get_active_avoidance_zones(db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database is offline: {e}")


@router.post("/avoidance-zones", response_model=schemas.FloodAvoidanceZoneResponse, status_code=status.HTTP_201_CREATED)
def create_avoidance_zone(zone: schemas.FloodAvoidanceZoneCreate, db: Session = Depends(get_db)):
    """
    Create a new flood avoidance zone (polygonal boundary coordinates associated with a report).
    """
    # Verify that the report exists
    report = crud.get_flood_report(db=db, report_id=zone.report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flood report with ID {zone.report_id} not found"
        )
    return crud.create_flood_avoidance_zone(db=db, zone=zone)


from app.services.ors_service import calculate_flood_safe_route

@router.post("/route", response_model=schemas.MultiRouteResponse)
async def get_safe_route(payload: schemas.RouteRequest, db: Session = Depends(get_db)):
    """
    Calculates route candidates between start and end coordinates using OpenRouteService.
    Each candidate is annotated with flood zone intersection status and
    a recommended_index pointing to the safest available option.
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
        
    return await calculate_flood_safe_route(
        db=db,
        start=payload.start,
        end=payload.end,
        ignore_floods=payload.ignore_floods,
        vehicle_profile=payload.vehicle_profile
    )


from pydantic import BaseModel as PydanticBaseModel
from typing import Optional as TypingOptional

class BidirectionalPreviewRequest(PydanticBaseModel):
    coordinates: list  # List of [lng, lat] points forming the original road segment
    road_name: TypingOptional[str] = None  # Optional road name for validation

class BidirectionalPreviewResponse(PydanticBaseModel):
    original: dict       # GeoJSON LineString of the original road
    opposite: TypingOptional[dict] = None  # GeoJSON LineString of opposite carriageway (None if one-way)
    is_divided: bool     # True if a valid opposite carriageway was found
    road_type: str       # NARROW_TWO_WAY, DIVIDED_CARRIAGEWAY, TRUE_ONE_WAY, UNMAPPED

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
