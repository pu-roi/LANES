"""Bounded queries and append-only persistence for follow-up audit evidence."""
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.models.audit import AuditLog
from app.models.report import FloodEventTimelineEntry, FloodReport

OBSERVATION_ACTION = "FLOOD_FOLLOWUP_OBSERVATION"
REVIEW_ACTION = "FLOOD_FOLLOWUP_REVIEW"
MAX_FOLLOWUPS_PER_REPORT = 100


def get_report(db: Session, report_id: int, *, lock: bool = False) -> FloodReport | None:
    statement = select(FloodReport).where(FloodReport.id == report_id)
    if lock:
        statement = statement.with_for_update().execution_options(populate_existing=True)
    return db.scalar(statement)


def get_followup(db: Session, followup_id: int, *, lock: bool = False) -> AuditLog | None:
    statement = select(AuditLog).where(AuditLog.id == followup_id,
        AuditLog.action_type == OBSERVATION_ACTION, AuditLog.target_table == "flood_reports")
    if lock:
        statement = statement.with_for_update().execution_options(populate_existing=True)
    return db.scalar(statement)


def report_followups(db: Session, report_id: int) -> list[AuditLog]:
    return list(db.scalars(select(AuditLog).where(AuditLog.action_type == OBSERVATION_ACTION,
        AuditLog.target_table == "flood_reports", AuditLog.target_id == report_id)
        .order_by(AuditLog.id.desc()).limit(MAX_FOLLOWUPS_PER_REPORT)))


def find_request(db: Session, report_id: int, request_id: str) -> AuditLog | None:
    return db.scalar(select(AuditLog).where(AuditLog.action_type == OBSERVATION_ACTION,
        AuditLog.target_table == "flood_reports", AuditLog.target_id == report_id,
        AuditLog.metadata_json["request_id"].astext == request_id).order_by(AuditLog.id).limit(1))


def latest_reviews(db: Session, followup_ids: list[int]) -> dict[int, AuditLog]:
    if not followup_ids:
        return {}
    rows = db.scalars(select(AuditLog).where(AuditLog.action_type == REVIEW_ACTION,
        AuditLog.target_table == "audit_logs", AuditLog.target_id.in_(followup_ids))
        .order_by(AuditLog.id.desc()))
    latest: dict[int, AuditLog] = {}
    for row in rows:
        latest.setdefault(row.target_id, row)
    return latest


def staff_followups(db: Session, review_state: str, limit: int, before_id: int | None) -> list[AuditLog]:
    review = aliased(AuditLog)
    latest_decision = select(review.metadata_json["decision"].astext).where(
        review.action_type == REVIEW_ACTION, review.target_table == "audit_logs",
        review.target_id == AuditLog.id).order_by(review.id.desc()).limit(1).correlate(AuditLog).scalar_subquery()
    statement = select(AuditLog).where(AuditLog.action_type == OBSERVATION_ACTION,
        AuditLog.target_table == "flood_reports")
    if review_state == "pending":
        statement = statement.where(latest_decision.is_(None))
    elif review_state != "all":
        statement = statement.where(latest_decision == review_state)
    if before_id is not None:
        statement = statement.where(AuditLog.id < before_id)
    return list(db.scalars(statement.order_by(AuditLog.id.desc()).limit(limit + 1)))


def original_observation(db: Session, report_id: int) -> AuditLog | None:
    return db.scalar(select(AuditLog).where(AuditLog.action_type == "CITIZEN_OBSERVATION",
        AuditLog.target_table == "flood_reports", AuditLog.target_id == report_id)
        .order_by(AuditLog.id.desc()).limit(1))


def append_audit(db: Session, *, action: str, target_table: str, target_id: int,
                 actor_id: int, metadata: dict[str, Any], created_at: datetime) -> AuditLog:
    row = AuditLog(action_type=action, target_table=target_table, target_id=target_id,
        admin_id=actor_id, metadata_json=metadata, created_at=created_at)
    db.add(row)
    db.flush()
    return row


def append_timeline(db: Session, *, event_id: int, observed_at: datetime,
                    summary: str, snapshot: dict[str, Any]) -> None:
    db.add(FloodEventTimelineEntry(event_id=event_id, entry_type="flood_followup_reviewed",
        occurred_at=observed_at, summary=summary, snapshot_json=snapshot))
