"""Witness evidence never changes operational depth, geometry, expiry or routing."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

from fastapi import UploadFile
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.crud import zone_update as store
from app.crud.flood_followup import append_audit
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.zone_update import ZoneObservationCreate, ZoneObservationReview
from app.services.flood_depth import severity_for_flood_depth
from app.services.flood_followup_service import FollowupError, require_active_user
from app.services.cloudinary_service import upload_image
from app.services.carriageway_service import build_road_segment_preview
from geoalchemy2.shape import to_shape

MAX_MEDIA = 5
MAX_BYTES = 10 * 1024 * 1024


def update_context(db: Session, zone_id: int, user: User) -> dict[str, Any]:
    require_active_user(user)
    zone = store.zone(db, zone_id)
    if zone is None:
        raise FollowupError(404, "Flood Zone not found.")
    if not zone.is_active:
        raise FollowupError(409, "This zone is no longer active.")
    geometry = to_shape(zone.report_geometry) if zone.report_geometry is not None else None
    line = geometry if geometry is not None and geometry.geom_type == "LineString" else (
        next(iter(geometry.geoms), None) if geometry is not None and geometry.geom_type == "MultiLineString" else None)
    return {"start": list(line.coords[0])[:2] if line is not None and not line.is_empty else None,
        "end": list(line.coords[-1])[:2] if line is not None and not line.is_empty else None,
        "name": zone.name, "depth": zone.depth, "has_road_endpoints": line is not None,
        "is_bidirectional": bool(zone.primary_report and zone.primary_report.is_bidirectional),
        "has_multiple_segments": geometry is not None and geometry.geom_type == "MultiLineString"}


def require_staff_permission(user: User, *, write: bool) -> None:
    require_active_user(user)
    role = user.role
    permissions = getattr(role, "permissions", None)
    if (role is None or role.name == "Commuter" or not isinstance(permissions, dict)
            or permissions.get("zones") not in ({"full"} if write else {"view", "full"})):
        raise FollowupError(403, "Your role does not allow this Spatial Operations action.")


def _response(row: AuditLog, review: AuditLog | None) -> dict[str, Any]:
    return {"id": row.id, "zone_id": row.target_id, "submitted_at": row.created_at.isoformat(),
        **{key: value for key, value in row.metadata_json.items() if key not in {"media_hashes", "request_id"}},
        "review_state": review.metadata_json["decision"] if review else "pending",
        "review": {**review.metadata_json, "reviewed_at": review.created_at.isoformat()} if review else None}


def _media_hashes(files: list[UploadFile]) -> list[str]:
    if len(files) > MAX_MEDIA:
        raise FollowupError(422, "Attach at most five photos or videos.")
    hashes = []
    for file in files:
        data = file.file.read(MAX_BYTES + 1)
        file.file.seek(0)
        if not data or len(data) > MAX_BYTES:
            raise FollowupError(422, "Each attachment must be nonempty and no larger than 10MB.")
        mime = file.content_type or ""
        image = (data.startswith(b"\xff\xd8\xff") or data.startswith(b"\x89PNG\r\n\x1a\n")
            or data.startswith((b"GIF87a", b"GIF89a"))
            or (data.startswith(b"RIFF") and data[8:12] == b"WEBP"))
        video = data[4:8] == b"ftyp" or data.startswith(b"\x1aE\xdf\xa3")
        if not ((image and mime in {"image/jpeg", "image/png", "image/gif", "image/webp"})
                or (video and mime in {"video/mp4", "video/quicktime", "video/webm"})):
            raise FollowupError(422, "Use JPEG, PNG, GIF, WebP, MP4, MOV or WebM attachments.")
        hashes.append(sha256(data).hexdigest())
    return hashes


def submit(db: Session, zone_id: int, user: User, payload: ZoneObservationCreate,
           media: list[UploadFile]) -> dict[str, Any]:
    require_active_user(user)
    zone = store.zone(db, zone_id, lock=True)
    if zone is None:
        raise FollowupError(404, "Flood Zone not found.")
    details = payload.model_dump(mode="json")
    hashes = _media_hashes(media)
    previous = db.scalar(select(AuditLog).where(AuditLog.action_type == store.OBSERVATION_ACTION,
        AuditLog.target_id == zone_id, AuditLog.metadata_json["request_id"].astext == str(payload.request_id)))
    if previous is not None:
        if previous.admin_id != user.id or previous.metadata_json.get("media_hashes") != hashes or any(
                previous.metadata_json.get(key) != value for key, value in details.items()):
            raise FollowupError(409, "This submission ID was already used with different details. Start a new update.")
        result = _response(previous, store.reviews(db, [previous.id]).get(previous.id))
        db.rollback()
        return result
    if not zone.is_active:
        raise FollowupError(409, "This zone is no longer active. Your update has not been submitted.")
    now = datetime.now(timezone.utc)
    recent = db.scalar(select(func.count()).select_from(AuditLog).where(
        AuditLog.action_type == store.OBSERVATION_ACTION, AuditLog.admin_id == user.id,
        AuditLog.target_id == zone_id, AuditLog.created_at >= now - timedelta(hours=1)))
    if recent >= 5:
        raise FollowupError(429, "You have sent five updates for this zone in an hour. Please try again later.")
    # Rebuild a proposed extent using the same road service as citizen reports.
    # It remains witness evidence, never an operational geometry write.
    proposal = None
    if payload.road_start is not None:
        try:
            preview = build_road_segment_preview(start=payload.road_start, end=payload.road_end,
                is_bidirectional=payload.is_bidirectional, road_name=None)
        except Exception as exc:
            raise FollowupError(503, "Could not verify the proposed road extent. Your update was not submitted; please retry.") from exc
        proposal = {"geometry": preview["coverage_geometry"], "validation_status": preview["validation_status"],
            "road_type": preview["road_type"], "message": preview["message"]}
    # Validate all files before uploading; no observation is saved with missing selected evidence.
    urls = []
    for file in media:
        url = upload_image(file)
        if not url:
            raise FollowupError(502, "An attachment could not be uploaded. Your update was not submitted; please retry.")
        urls.append(url)
    row = append_audit(db, action=store.OBSERVATION_ACTION, target_table="flood_avoidance_zones",
        target_id=zone.id, actor_id=user.id, created_at=now, metadata={**details,
            "proposed_extent": proposal, "observation_time_recorded": payload.observed_at is not None,
            "author_id": user.id, "author_name": user.username, "media_urls": urls, "media_hashes": hashes,
            "severity": severity_for_flood_depth(payload.depth).value if payload.depth else None,
            "zone_version": zone.updated_at.isoformat(), "official_depth": zone.depth_override,
            "official_severity": zone.severity_override.value if zone.severity_override else None})
    result = _response(row, None)
    db.commit()
    return result


def list_updates(db: Session, zone_id: int, user: User, limit: int, before_id: int | None) -> dict[str, Any]:
    require_staff_permission(user, write=False)
    zone = store.zone(db, zone_id)
    if zone is None:
        raise FollowupError(404, "Flood Zone not found.")
    rows = store.observations(db, zone_id, limit=limit, before_id=before_id)
    has_more = len(rows) > limit
    rows = rows[:limit]
    reviews = store.reviews(db, [row.id for row in rows])
    return {"updates": [_response(row, reviews.get(row.id)) for row in rows],
        "next_before_id": rows[-1].id if has_more else None,
        "is_active": zone.is_active, "can_review": user.role.permissions.get("zones") == "full"}


def counts(db: Session, ids: list[int], user: User) -> dict[int, int]:
    require_staff_permission(user, write=False)
    return store.pending_counts(db, ids)


def review(db: Session, zone_id: int, update_id: int, user: User,
           payload: ZoneObservationReview) -> dict[str, Any]:
    require_staff_permission(user, write=True)
    # Same lock order as submission, serializing decisions with operational zone writes.
    if store.zone(db, zone_id, lock=True) is None:
        raise FollowupError(404, "Flood Zone not found.")
    row = db.scalar(select(AuditLog).where(AuditLog.id == update_id,
        AuditLog.action_type == store.OBSERVATION_ACTION, AuditLog.target_id == zone_id,
        AuditLog.target_table == "flood_avoidance_zones").with_for_update())
    if row is None:
        raise FollowupError(404, "Update not found for this zone.")
    if row.admin_id == user.id:
        raise FollowupError(403, "You cannot review your own observation.")
    existing = store.reviews(db, [row.id]).get(row.id)
    if existing is not None:
        if existing.admin_id == user.id and all(existing.metadata_json.get(k) == v for k, v in payload.model_dump().items()):
            result = _response(row, existing)
            db.rollback()
            return result
        raise FollowupError(409, "This update has already been reviewed.")
    entry = append_audit(db, action=store.REVIEW_ACTION, target_table="audit_logs", target_id=row.id,
        actor_id=user.id, created_at=datetime.now(timezone.utc), metadata={**payload.model_dump(),
            "reviewer_id": user.id, "zone_id": zone_id, "zone_update_id": row.id})
    result = _response(row, entry)
    db.commit()
    return result
