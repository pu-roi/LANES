"""Report status updates stored in the existing notification transaction."""

from typing import Any

from sqlalchemy.orm import Session

from app.crud.notification import create_notification
from app.models.notification import Notification, NotificationType
from app.models.report import FloodReport, ReportStatus
from app.schemas.notification import NotificationCreate


_STATUS_MESSAGES = {
    ReportStatus.PENDING: (
        "flood_report_under_review", "Flood Report Under Review",
        "Your submitted flood report is awaiting review by our administrators or authorized "
        "DRRMO personnel. You will be notified once a decision has been made.",
    ),
    ReportStatus.APPROVED: (
        "flood_report_approved", "Flood Report Approved",
        "Your submitted flood report has been reviewed and approved. "
        "Thank you for helping keep the community informed about flood conditions.",
    ),
    ReportStatus.REJECTED: (
        "flood_report_rejected", "Flood Report Rejected",
        "Your submitted flood report has been reviewed and rejected.",
    ),
}


def stage_report_status_notification(
    db: Session,
    report: FloodReport,
    *,
    message: str | None = None,
    extra_payload: dict[str, Any] | None = None,
) -> Notification | None:
    """Stage one owner update per persisted report status, without committing.

    Call only at a status transition. Flushing and locking the report serializes
    concurrent notification writers; JSON payloads reuse the existing storage.
    A failure propagates so the caller rolls back both the action and its notice.
    """
    if report.user_id is None or report.status not in _STATUS_MESSAGES:
        return None
    db.flush()
    persisted = db.query(FloodReport.id).filter(
        FloodReport.id == report.id,
        FloodReport.user_id == report.user_id,
        FloodReport.status == report.status,
        FloodReport.deleted_at.is_(None),
    ).with_for_update().first()
    if persisted is None:
        return None
    action, title, default_message = _STATUS_MESSAGES[report.status]
    existing = db.query(Notification).filter(
        Notification.user_id == report.user_id,
        Notification.type == NotificationType.SYSTEM,
        Notification.payload["report_id"].as_integer() == report.id,
        Notification.payload["action"].as_string() == action,
    ).first()
    if existing is not None:
        return existing
    return create_notification(db, NotificationCreate(
        user_id=report.user_id,
        type=NotificationType.SYSTEM,
        message=message or default_message,
        payload={**(extra_payload or {}), "report_id": report.id, "action": action, "title": title},
    ), commit=False)
