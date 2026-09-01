import logging
from sqlalchemy.orm import Session
from app.schemas.report import FloodReportCreate
from app.services.geocoding_service import reverse_geocode
from app.crud.report import create_flood_report

logger = logging.getLogger(__name__)

async def process_new_report(
    db: Session,
    raw_text: str,
    source: str,
    severity: str,
    is_public: bool,
    is_bidirectional: bool = False,
    depth: str = None,
    human_readable_location: str = None,
    geometry: dict = None,
    media_urls: list[str] = None,
    user_id: int = None,
    survey_data: dict = None
):
    """
    Business logic for processing a new flood report.
    Handles reverse geocoding to find a human_readable_location.
    """
    # If no NLP match is found, fallback to reverse geocoding
    if not human_readable_location and geometry and geometry.get("type") == "Point":
        try:
            coords = geometry.get("coordinates", [])
            if len(coords) >= 2:
                lng, lat = coords[0], coords[1]
                # Reverse geocode (OpenStreetMap Nominatim)
                location = await reverse_geocode(lat, lng)
                if location:
                    human_readable_location = location
        except Exception as e:
            logger.error(f"Failed to reverse geocode report location: {e}")

    report_create = FloodReportCreate(
        raw_text=raw_text,
        source=source,
        severity=severity,
        depth=depth,
        human_readable_location=human_readable_location,
        is_public=is_public,
        is_bidirectional=is_bidirectional,
        geometry=geometry,
        media_urls=media_urls or [],
        user_id=user_id,
        survey_data=survey_data
    )
    
    return create_flood_report(db=db, report=report_create)

import json
from sqlalchemy import func
from app.models.report import FloodReport, FloodAvoidanceZone

def get_active_floods(db: Session):
    zones = db.query(
        func.ST_AsGeoJSON(FloodAvoidanceZone.geometry).label("geojson"),
        FloodReport.severity,
        FloodAvoidanceZone.id,
    ).join(
        FloodReport, FloodAvoidanceZone.id == FloodReport.zone_id
    ).filter(
        FloodAvoidanceZone.is_active == True,
        (FloodAvoidanceZone.expires_at == None) | (FloodAvoidanceZone.expires_at > func.now())
    ).all()
    
    data = []
    for z in zones:
        geom = json.loads(z.geojson) if z.geojson else None
        data.append({
            "id": z.id,
            "status": "active",
            "severity": z.severity.value if hasattr(z.severity, "value") else z.severity,
            "polygon": geom
        })
    return data
