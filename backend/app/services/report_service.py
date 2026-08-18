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
        geometry=geometry,
        media_urls=media_urls or [],
        user_id=user_id,
        survey_data=survey_data
    )
    
    return create_flood_report(db=db, report=report_create)
