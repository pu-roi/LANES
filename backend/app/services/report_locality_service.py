"""Resolve canonical Pasig report metadata from final geometry and PSGC assets.

OSM supplies the snapped road. Reviewed administrative polygons determine its
localities; reverse-geocoder address labels never override that geometry.
"""
from datetime import datetime, timezone
import hashlib
from typing import Any

from geoalchemy2.shape import to_shape
from shapely.geometry import shape
from shapely.errors import ShapelyError
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.audit import AuditLog
from app.models.report import FloodReport
from app.services.flood_location_service import get_flood_location_provider

RECONCILIATION_ACTION = "RECONCILE_REPORT_LOCALITY"


def pasig_geometry_locality(geometry: Any) -> dict[str, Any] | None:
    provider = get_flood_location_provider()
    if provider.error or provider.city_boundary is None or geometry is None:
        return None
    if not isinstance(geometry, dict) and getattr(geometry, "srid", None) != 4326:
        return None
    try:
        footprint = shape(geometry) if isinstance(geometry, dict) else to_shape(geometry)
        if (footprint.geom_type not in {"Point", "LineString", "MultiLineString", "Polygon", "MultiPolygon"}
                or footprint.is_empty or not footprint.is_valid or not provider.city_boundary.covers(footprint)):
            return None
        covered = [record for record, boundary in provider.records.values() if boundary.covers(footprint)]
        if len(covered) == 1:
            records = covered
        else:
            records = [record for record, boundary in provider.records.values()
                if (boundary.intersection(footprint).area > 0 if footprint.geom_type in {"Polygon", "MultiPolygon"}
                    else boundary.intersection(footprint).length > 0)]
        if not records:
            return None
        names = sorted({record.barangay for record in records})
        return {"city": "Pasig", "barangay": names[0] if len(names) == 1 else None,
            "barangays": names, "psgc_codes": sorted({record.psgc_code for record in records}),
            "boundary_revision": provider.revision, "basis": "final_geometry_reviewed_psgc_boundary"}
    except (TypeError, ValueError, AttributeError, ShapelyError):
        return None


def reconcile_report_locality(db: Session, report: FloodReport) -> dict[str, Any] | None:
    """Correct derived labels, preserving the actual source/edit clock and audits.

    This changes administrative metadata only: not geometry, observation time,
    status, event or depth. Immutable submissions/follow-ups remain intact.
    Caller holds the configuration/zone lock and owns the transaction.
    """
    locality = pasig_geometry_locality(report.geometry)
    if locality is None or (report.city == locality["city"] and report.barangay == locality["barangay"]):
        return None
    before = {"city": report.city, "barangay": report.barangay}
    geometry_hash = hashlib.sha256(to_shape(report.geometry).wkb).hexdigest()
    report.city, report.barangay = locality["city"], locality["barangay"]
    # Derived canonical labels do not represent a new physical/source edit.
    # The separate append-only correction clock exposes when this was done.
    flag_modified(report, "updated_at")
    metadata = {"before": before, "after": {"city":report.city,"barangay":report.barangay},
        "geometry_sha256": geometry_hash, "resolved_locality": locality,
        "preserved_source_updated_at": report.updated_at.isoformat(),
        "changes_observation_time": False, "changes_geometry": False}
    db.add(AuditLog(action_type=RECONCILIATION_ACTION,target_table="flood_reports",target_id=report.id,
        created_at=datetime.now(timezone.utc),metadata_json=metadata))
    db.flush()
    return metadata


def snapshot_matches_reconciled_locality(db: Session, report: FloodReport, saved: dict[str, Any]) -> bool:
    """Accept only a documented derived-label correction of the SAME snapshot.

    No geometry/episode/road edits are excused. Old claims remain attributable
    to their original labels; a correction cannot grant a clearance decision.
    """
    from app.services.flood_followup_service import _location_snapshot
    current = _location_snapshot(report)
    if saved == current:
        return True
    identity_fields = set(current) - {"city", "barangay"}
    if any(saved.get(k) != current[k] for k in identity_fields):
        return False
    corrections = db.scalars(select(AuditLog).where(AuditLog.action_type==RECONCILIATION_ACTION,
        AuditLog.target_table=="flood_reports",AuditLog.target_id==report.id).order_by(AuditLog.id.desc()).limit(100))
    for row in corrections:
        data = row.metadata_json or {}
        if (data.get("geometry_sha256")==current["geometry_sha256"]
                and data.get("before")=={k:saved.get(k) for k in ("city","barangay")}
                and data.get("after")=={k:current[k] for k in ("city","barangay")}):
            return True
    return False
