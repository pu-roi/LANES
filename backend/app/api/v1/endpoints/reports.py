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
        except Exception:
            pass

    survey_obj = None
    if survey_data:
        try:
            survey_obj = json.loads(survey_data)
        except Exception:
            pass

    return await process_new_report(
        db=db,
        raw_text=raw_text,
        source=source,
        severity=severity,
        depth=depth,
        human_readable_location=human_readable_location,
        is_public=is_public,
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
        print(f"Warning: Database is offline ({e}). Returning empty list for reports.")
        return []


@router.get("", response_model=List[schemas.FloodReportResponse])
def read_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve list of flood reports (paginated).
    """
    try:
        return crud.get_flood_reports(db=db, skip=skip, limit=limit)
    except Exception as e:
        print(f"Warning: Database is offline ({e}). Returning empty list for reports.")
        return []


@router.get("/active-zones", response_model=List[schemas.FloodAvoidanceZoneResponse])
def read_active_avoidance_zones(db: Session = Depends(get_db)):
    """
    Retrieve all active flood avoidance zones (polygons representing detour zones).
    """
    try:
        return crud.get_active_avoidance_zones(db=db)
    except Exception as e:
        print(f"Warning: Database is offline ({e}). Returning empty list for active zones.")
        return []


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


from app.services.graphhopper_service import calculate_flood_safe_route

@router.post("/route", response_model=schemas.MultiRouteResponse)
async def get_safe_route(payload: schemas.RouteRequest, db: Session = Depends(get_db)):
    """
    Calculates up to 3 route candidates between start and end coordinates.
    Each candidate is annotated with flood zone intersection status and
    a recommended_index pointing to the safest available option.
    """
    return await calculate_flood_safe_route(
        db=db,
        start=payload.start,
        end=payload.end,
        ignore_floods=payload.ignore_floods,
        vehicle_profile=payload.vehicle_profile
    )

