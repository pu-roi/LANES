import logging
from typing import Optional, List, Any
from sqlalchemy.orm import Session
from app.schemas.report import FloodReportCreate
from app.services.geocoding_service import reverse_geocode, reverse_geocode_structured
from app.services.carriageway_service import build_road_segment_preview
from app.crud.report import create_flood_report

logger = logging.getLogger(__name__)


def validate_report_road_geometry(
    geometry: dict,
    road_name_hint: Optional[str],
    is_bidirectional: bool,
) -> tuple[dict, str]:
    """Rebuild authoritative road-only coverage from submitted road endpoints."""
    coordinates = geometry.get("coordinates", [])
    if geometry.get("type") == "MultiLineString":
        coordinates = coordinates[0] if coordinates else []
    if len(coordinates) < 2:
        return geometry, "UNMAPPED"
    preview = build_road_segment_preview(
        start=coordinates[0],
        end=coordinates[-1],
        is_bidirectional=is_bidirectional,
        road_name=road_name_hint,
    )
    return preview["coverage_geometry"], preview["road_type"]


def extract_representative_coordinates(geometry: Optional[dict]) -> Optional[tuple[float, float]]:
    """
    Extracts a representative (lat, lng) from Point, LineString, or MultiLineString geometries.
    For lines, the midpoint coordinate is returned.
    Coordinates in GeoJSON are formatted as [lng, lat].
    """
    if not geometry or not isinstance(geometry, dict):
        return None

    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])

    if not coords:
        return None

    try:
        if geom_type == "Point" and len(coords) >= 2:
            return float(coords[1]), float(coords[0])

        elif geom_type == "LineString" and len(coords) > 0:
            mid_idx = len(coords) // 2
            mid_pt = coords[mid_idx]
            if len(mid_pt) >= 2:
                return float(mid_pt[1]), float(mid_pt[0])

        elif geom_type == "MultiLineString" and len(coords) > 0:
            first_line = coords[0]
            if len(first_line) > 0:
                mid_idx = len(first_line) // 2
                mid_pt = first_line[mid_idx]
                if len(mid_pt) >= 2:
                    return float(mid_pt[1]), float(mid_pt[0])

        elif geom_type == "Polygon" and len(coords) > 0:
            ring = coords[0]
            if len(ring) > 0:
                mid_idx = len(ring) // 2
                mid_pt = ring[mid_idx]
                if len(mid_pt) >= 2:
                    return float(mid_pt[1]), float(mid_pt[0])
    except Exception as e:
        logger.warning(f"Error extracting representative coordinates from geometry: {e}")

    return None


async def process_new_report(
    db: Session,
    raw_text: str,
    source: str,
    severity: str,
    is_public: bool,
    is_bidirectional: bool = False,
    depth: str = None,
    human_readable_location: str = None,
    barangay: str = None,
    city: str = None,
    geometry: dict = None,
    media_urls: list[str] = None,
    user_id: int = None,
    survey_data: dict = None
):
    """
    Business logic for processing a new flood report.
    Automatically reverse-geocodes report coordinates to populate street/landmark,
    barangay, and city if not already supplied.
    Handles opposite carriageway calculation for bidirectional reports.
    """
    # Auto-resolve missing location details using coordinates
    rep_coords = extract_representative_coordinates(geometry)
    if rep_coords and (not human_readable_location or not barangay or not city):
        try:
            lat, lng = rep_coords
            parsed_loc = await reverse_geocode_structured(lat, lng)
            if parsed_loc:
                if not human_readable_location:
                    human_readable_location = parsed_loc.street or parsed_loc.display_name
                if not barangay and parsed_loc.barangay:
                    barangay = parsed_loc.barangay
                if not city and parsed_loc.city:
                    city = parsed_loc.city
                logger.info(
                    f"[process_new_report] Reverse geocoded location: street='{human_readable_location}', "
                    f"barangay='{barangay}', city='{city}'"
                )
        except Exception as e:
            logger.error(f"Failed to reverse geocode report location: {e}")

    # Preview geometry is advisory. Rebuild every submitted road segment so the
    # stored geometry is always the authoritative snapped road-only coverage.
    if geometry and geometry.get("type") in {"LineString", "MultiLineString"}:
        try:
            geometry, road_type = validate_report_road_geometry(
                geometry,
                human_readable_location,
                is_bidirectional,
            )
            if road_type == "DIVIDED_CARRIAGEWAY":
                logger.info(
                    "[process_new_report] Bidirectional: successfully combined original + "
                    "opposite carriageway into MultiLineString."
                )
            else:
                logger.info(
                    f"[process_new_report] Road geometry rebuilt. Classification: {road_type}. "
                    "Storing the authoritative original line only."
                )
        except Exception as e:
            logger.error(f"[process_new_report] Hybrid Strategy failed: {e}. Falling back to original geometry.")

    report_create = FloodReportCreate(
        raw_text=raw_text,
        source=source,
        severity=severity,
        depth=depth,
        human_readable_location=human_readable_location,
        barangay=barangay,
        city=city,
        is_public=is_public,
        is_bidirectional=is_bidirectional,
        geometry=geometry,
        media_urls=media_urls or [],
        user_id=user_id,
        survey_data=survey_data
    )
    
    created_report = create_flood_report(db=db, report=report_create)

    # Immediately post to Community Feed if is_public is True (without affecting /map routing barriers)
    if is_public and user_id:
        try:
            from app.schemas.post import CommunityPostCreate
            from app.crud.post import create_community_post
            post_in = CommunityPostCreate(
                flood_report_id=created_report.id,
                content=raw_text,
                media_urls=media_urls if media_urls else None,
                location_tag=barangay or human_readable_location or None
            )
            create_community_post(db=db, post_in=post_in, user_id=user_id)
            logger.info(f"[process_new_report] Created CommunityPost immediately for public report #{created_report.id}")
        except Exception as e:
            logger.error(f"[process_new_report] Failed to auto-create CommunityPost for report #{created_report.id}: {e}")

    return created_report


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
