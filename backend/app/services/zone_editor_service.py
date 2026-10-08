"""Atomic operational edits and community-evidence provenance, without new tables."""
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app import models
from app.crud import zone_update as store
from app.crud.flood_followup import append_audit
from app.schemas.report import FloodAvoidanceZoneUpdate
from app.schemas.common import ensure_utc
from app.services.flood_depth import severity_for_flood_depth
from app.services.flood_followup_service import FollowupError
from app.services.zone_update_service import editor_proposal, require_staff_permission
from app.services.flood_event_service import record_zone_update, deactivate_zone_and_end_event_if_final


def snapshot(db: Session, zone: models.FloodAvoidanceZone) -> dict[str, Any]:
    geometry = zone.report_geometry if zone.report_geometry is not None else zone.geometry
    raw = db.query(func.ST_AsGeoJSON(geometry)).scalar()
    return {"depth": zone.depth, "severity": zone.severity,
        "passable_vehicles": zone.passable_vehicles_override if zone.passable_vehicles_override is not None else zone.passable_vehicles,
        "hidden_hazards": zone.hidden_hazards,
        "geometry": json.loads(raw) if raw else None}


def save_zone(db: Session, zone_id: int, user: models.User, body: FloodAvoidanceZoneUpdate,
              client_ip: str | None = None) -> models.FloodAvoidanceZone:
    require_staff_permission(user, write=True)
    try:
        zone = store.zone(db, zone_id, lock=True)
        if zone is None:
            raise FollowupError(404, "Zone not found.")
        if body.expected_updated_at is not None and ensure_utc(body.expected_updated_at) != ensure_utc(zone.updated_at):
            raise FollowupError(409, "Another administrator changed this zone. Your draft is kept; reopen the latest details before saving.")
        source = body.community_update
        if source:
            if body.expected_updated_at is None:
                raise FollowupError(422, "A current zone version is required when using community evidence.")
            editor_proposal(db, zone_id, source.update_id, user, source)
            if body.is_active is False:
                raise FollowupError(422, "Community field application is separate from a verified clearance decision.")
        if body.is_active is True and zone.flood_event and zone.flood_event.status == models.FloodEventStatus.ENDED:
            raise FollowupError(409, "Ended Flood Events cannot be reopened. Verify a new flooding event instead.")
        before = snapshot(db, zone)
        if body.depth_override is not None:
            expected_severity = severity_for_flood_depth(body.depth_override)
            if body.severity_override is not None and body.severity_override != expected_severity:
                raise FollowupError(422, "Severity must match the selected flood depth.")
            zone.severity_override = expected_severity
        for field in ("name", "severity_override", "depth_override", "admin_notes", "passable_vehicles_override", "hidden_hazards_override"):
            value = getattr(body, field)
            if value is not None:
                setattr(zone, field, value)
        if body.geometry is not None:
            expression = func.ST_SetSRID(func.ST_GeomFromGeoJSON(body.geometry.model_dump_json()), 4326)
            if body.geometry.type in {"LineString", "MultiLineString"}:
                from app.services.configuration_service import read_configuration
                raw = db.query(func.ST_AsGeoJSON(func.ST_Transform(func.ST_Buffer(func.ST_Transform(expression, 32651),
                    read_configuration(db).staff_road_buffer_metres), 4326))).scalar()
                geometry = json.loads(raw) if raw else None
                if not geometry or geometry.get("type") != "Polygon":
                    raise FollowupError(422, "The selected road geometry must form one continuous avoidance zone.")
                zone.source_geometry = expression
                zone.geometry = func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps(geometry)), 4326)
            else:
                zone.geometry = expression
                zone.source_geometry = None
        changes = body.model_dump(exclude_none=True, exclude={"expected_updated_at", "community_update"}, mode="json")
        if body.is_active is False:
            deactivate_zone_and_end_event_if_final(db=db, zone=zone, commit=False)
        else:
            if body.is_active is True:
                zone.is_active = True
            if zone.event_id:
                record_zone_update(db=db, zone=zone, changes=changes, commit=False)
        zone.updated_at = datetime.now(timezone.utc)
        db.flush()
        db.refresh(zone)
        after = snapshot(db, zone)
        metadata: dict[str, Any] = {"zone_id": zone.id, "zone_version": zone.updated_at.isoformat(), "changes": changes}
        if source:
            # Provenance describes actual changed facts, not every checkbox/opened editor.
            applied = [field for field in dict.fromkeys(source.fields) if before[field] != after[field]]
            if not applied:
                raise FollowupError(422, "None of the selected community fields changed. Adjust the draft or save without this evidence selection.")
            metadata.update(community_update_id=source.update_id, applied_fields=applied,
                reason=source.reason, before={field: before[field] for field in applied}, after={field: after[field] for field in applied})
        audit = append_audit(db, action="UPDATE_ZONE", target_table="flood_avoidance_zones", target_id=zone.id,
            actor_id=user.id, created_at=datetime.now(timezone.utc), metadata=metadata)
        audit.ip_address = client_ip
        db.commit()
        db.refresh(zone)
        return zone
    except FollowupError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise FollowupError(503, "The zone could not be saved. Your draft is kept; please retry.") from exc
    except Exception:
        db.rollback()
        raise
