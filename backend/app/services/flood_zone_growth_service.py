"""Reviewed coverage composition shared by preview and transactional publication."""
import json
import math
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from shapely.errors import ShapelyError

from app.models.report import FloodAvoidanceZone, FloodEventStatus
from app.schemas.report import MergedZoneFinalData


def validate_active_target(zone: FloodAvoidanceZone) -> None:
    expiry = zone.expires_at
    if expiry and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if (not zone.is_active or not zone.event_id or not zone.flood_event
            or zone.flood_event.status != FloodEventStatus.ACTIVE
            or (expiry and expiry <= datetime.now(timezone.utc))):
        raise ValueError("Choose an active, unexpired zone belonging to an active Flood Event.")


def compose_reviewed_coverage(db: Session, final: MergedZoneFinalData,
        target: FloodAvoidanceZone | None, mode: str) -> tuple[Any, Any, dict]:
    """Never fill a dry gap with a convex hull or replace coverage during extension."""
    if "buffer_radius" not in final.model_fields_set:
        from app.services.configuration_service import read_configuration
        final = final.model_copy(update={"buffer_radius": read_configuration(db).staff_road_buffer_metres})
    if target:
        validate_active_target(target)
    if mode == "corroborate":
        polygon, core = target.geometry, target.source_geometry
    else:
        raw = final.geometry.model_dump()
        if raw["type"] == "Point":
            raise ValueError("A point cannot define verified coverage. Draw a boundary or select an affected road section.")
        from shapely.geometry import shape
        try:
            reviewed = shape(raw)
        except (ValueError, TypeError, IndexError, ShapelyError) as exc:
            raise ValueError("Draw a valid affected road section or boundary.") from exc
        if reviewed.is_empty or not reviewed.is_valid:
            raise ValueError("The reviewed geometry must be valid and non-empty.")
        def valid_coordinates(coordinates):
            if coordinates and isinstance(coordinates[0], (int, float)):
                return (len(coordinates) == 2 and all(math.isfinite(v) for v in coordinates)
                    and -180 <= coordinates[0] <= 180 and -90 < coordinates[1] < 90)
            return bool(coordinates) and all(valid_coordinates(part) for part in coordinates)
        if not valid_coordinates(raw["coordinates"]):
            raise ValueError("Coordinates must be finite longitude/latitude pairs.")
        geom = func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps(raw)), 4326)
        valid = db.execute(select(func.ST_IsValid(geom), func.ST_IsEmpty(geom))).one()
        if not valid[0] or valid[1]:
            raise ValueError("The reviewed geometry must be valid and non-empty.")
        core = geom if raw["type"] in {"LineString", "MultiLineString"} else None
        polygon = geom if raw["type"] == "Polygon" else func.ST_Transform(
            func.ST_Buffer(func.ST_Transform(geom, 32651), final.buffer_radius), 4326)
        if target and mode == "extend":
            polygon = func.ST_UnaryUnion(func.ST_Collect(target.geometry, polygon))
            old_core = target.source_geometry
            if old_core is None:
                old_lines = [report.geometry for report in target.reports if report.geometry is not None]
                for line in old_lines:
                    line = func.ST_CollectionExtract(line, 2)
                    old_core = line if old_core is None else func.ST_Collect(old_core, line)
            if old_core is not None:
                core = old_core if core is None else func.ST_UnaryUnion(func.ST_Collect(old_core, core))
    boundary, core_json, kind, valid = db.execute(select(func.ST_AsGeoJSON(polygon),
        func.ST_AsGeoJSON(core) if core is not None else None,
        func.ST_GeometryType(polygon), func.ST_IsValid(polygon))).one()
    if kind != "ST_Polygon" or not valid:
        raise ValueError("Coverage is disconnected. Confirm a continuous affected boundary, or add a separate section to the same event.")
    if core is not None:
        core = func.ST_Multi(func.ST_CollectionExtract(core, 2))
        core_json = db.scalar(select(func.ST_AsGeoJSON(core)))
        if not json.loads(core_json)["coordinates"]:
            core, core_json = None, None
    return polygon, core, {"geometry": json.loads(boundary),
        "reviewed_geometry": final.geometry.model_dump(),
        "source_geometry": json.loads(core_json) if core_json else None,
        "preserves_existing_coverage": target is not None and mode in {"extend", "corroborate"}, "read_only": True}
