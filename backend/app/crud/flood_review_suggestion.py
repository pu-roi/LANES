"""Bounded immutable suggestion records in the existing private audit store."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog

SUGGESTION_ACTION = "FLOOD_ML_REVIEW_SUGGESTION"
MAX_SUGGESTIONS_PER_REPORT = 100


def suggestions(db: Session, report_id: int) -> list[AuditLog]:
    return list(db.scalars(select(AuditLog).where(AuditLog.action_type == SUGGESTION_ACTION,
        AuditLog.target_table == "flood_reports", AuditLog.target_id == report_id)
        .order_by(AuditLog.id.desc()).limit(MAX_SUGGESTIONS_PER_REPORT)))


def latest_page(db: Session, *, limit: int, before_id: int | None) -> list[AuditLog]:
    # Select the latest per case before pagination; old versions never reappear
    # when the newest version falls outside the cursor.
    latest = select(func.max(AuditLog.id).label("id")).where(
        AuditLog.action_type == SUGGESTION_ACTION, AuditLog.target_table == "flood_reports"
    ).group_by(AuditLog.target_id).subquery()
    query = select(AuditLog).join(latest, latest.c.id == AuditLog.id)
    if before_id is not None:
        query = query.where(AuditLog.id < before_id)
    return list(db.scalars(query.order_by(AuditLog.id.desc()).limit(limit + 1)))
