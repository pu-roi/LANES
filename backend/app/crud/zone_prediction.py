"""Bounded read-only spatial discovery and explicit zone evidence links."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimZoneLink
from app.models.report import FloodAvoidanceZone, FloodReport, ReportStatus
from app.models.audit import AuditLog

MAX_RECORDS = 100


def unchanged_official_registration(db: Session, zone: FloodAvoidanceZone) -> AuditLog | None:
    """A recording clock for simulations, never a physical observation clock."""
    if db.scalar(select(AuditLog.id).where(AuditLog.target_table == "flood_avoidance_zones",
            AuditLog.target_id == zone.id, AuditLog.action_type == "UPDATE_ZONE").limit(1)) is not None:
        return None
    return db.scalar(select(AuditLog).where(AuditLog.target_table == "flood_avoidance_zones",
        AuditLog.target_id == zone.id, AuditLog.action_type == "CREATE_OFFICIAL_ZONE").order_by(AuditLog.id).limit(1))


def get_zone(db: Session, zone_id: int) -> FloodAvoidanceZone | None:
    return db.get(FloodAvoidanceZone, zone_id)


def linked_reports(db: Session, zone_id: int) -> list[FloodReport]:
    return list(db.scalars(select(FloodReport).where(FloodReport.zone_id == zone_id,
        FloodReport.deleted_at.is_(None)).order_by(FloodReport.id).limit(MAX_RECORDS + 1)))


def nearby_report_count(db: Session, zone: FloodAvoidanceZone, *, distance_metres: float) -> int:
    # As in merge discovery, proximity supplies candidates, never an evidence link.
    distance = func.ST_Distance(func.ST_Transform(FloodReport.geometry, 32651),
        func.ST_Transform(zone.geometry, 32651))
    ids = list(db.scalars(select(FloodReport.id).where(FloodReport.deleted_at.is_(None),
        FloodReport.geometry.is_not(None), FloodReport.status == ReportStatus.PENDING,
        (FloodReport.zone_id.is_(None) | (FloodReport.zone_id != zone.id)),
        func.ST_DWithin(func.ST_Transform(FloodReport.geometry, 32651),
            func.ST_Transform(zone.geometry, 32651), distance_metres))
        .order_by(distance, FloodReport.id).limit(MAX_RECORDS)))
    return len(ids)


def current_news(db: Session, zone_id: int) -> list[NewsClaimDecision]:
    return list(db.scalars(select(NewsClaimDecision).join(NewsClaimZoneLink,
        NewsClaimZoneLink.decision_id == NewsClaimDecision.id).join(NewsClaimCase,
        NewsClaimCase.id == NewsClaimDecision.case_id).where(NewsClaimZoneLink.zone_id == zone_id,
        NewsClaimDecision.revision == NewsClaimCase.revision).order_by(NewsClaimDecision.id)
        .limit(MAX_RECORDS + 1)))


def news_history(db: Session, case_id: int) -> list[NewsClaimDecision]:
    return list(db.scalars(select(NewsClaimDecision).where(NewsClaimDecision.case_id == case_id)
        .order_by(NewsClaimDecision.revision.desc()).limit(MAX_RECORDS + 1)))
