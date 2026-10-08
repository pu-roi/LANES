"""Append-only observation storage in the existing audit table."""
from sqlalchemy import select, func
from sqlalchemy.orm import Session, aliased
from app.models.audit import AuditLog
from app.models.report import FloodAvoidanceZone

OBSERVATION_ACTION = "ZONE_PUBLIC_OBSERVATION"
REVIEW_ACTION = "ZONE_PUBLIC_OBSERVATION_REVIEW"


def zone(db: Session, zone_id: int, *, lock: bool = False) -> FloodAvoidanceZone | None:
    query = select(FloodAvoidanceZone).where(FloodAvoidanceZone.id == zone_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    return db.scalar(query)


def observations(db: Session, zone_id: int, *, limit: int = 50, before_id: int | None = None) -> list[AuditLog]:
    query = select(AuditLog).where(AuditLog.action_type == OBSERVATION_ACTION,
        AuditLog.target_table == "flood_avoidance_zones", AuditLog.target_id == zone_id)
    if before_id is not None:
        query = query.where(AuditLog.id < before_id)
    return list(db.scalars(query.order_by(AuditLog.id.desc()).limit(limit + 1)))


def reviews(db: Session, ids: list[int]) -> dict[int, AuditLog]:
    rows = db.scalars(select(AuditLog).where(AuditLog.action_type == REVIEW_ACTION,
        AuditLog.target_table == "audit_logs", AuditLog.target_id.in_(ids)).order_by(AuditLog.id.desc()))
    result: dict[int, AuditLog] = {}
    for row in rows:
        result.setdefault(row.target_id, row)
    return result


def applications(db: Session, zone_id: int, ids: list[int]) -> dict[int, list[dict]]:
    if not ids:
        return {}
    rows = db.scalars(select(AuditLog).where(AuditLog.action_type == "UPDATE_ZONE",
        AuditLog.target_table == "flood_avoidance_zones", AuditLog.target_id == zone_id,
        AuditLog.metadata_json["community_update_id"].astext.in_([str(value) for value in ids]))
        .order_by(AuditLog.id.desc()))
    result: dict[int, list[dict]] = {}
    for row in rows:
        data = row.metadata_json
        result.setdefault(data["community_update_id"], []).append({"id": row.id,
            "saved_at": row.created_at.isoformat(), "fields": data["applied_fields"],
            "reason": data["reason"], "zone_version": data["zone_version"], "staff_id": row.admin_id})
    return result


def pending_counts(db: Session, ids: list[int]) -> dict[int, int]:
    review = aliased(AuditLog)
    has_review = select(review.id).where(review.action_type == REVIEW_ACTION,
        review.target_table == "audit_logs", review.target_id == AuditLog.id).exists()
    rows = db.execute(select(AuditLog.target_id, func.count()).join(FloodAvoidanceZone,
        FloodAvoidanceZone.id == AuditLog.target_id).where(AuditLog.action_type == OBSERVATION_ACTION,
        AuditLog.target_table == "flood_avoidance_zones", AuditLog.target_id.in_(ids),
        FloodAvoidanceZone.is_active.is_(True), ~has_review).group_by(AuditLog.target_id))
    return {zone_id: count for zone_id, count in rows}
