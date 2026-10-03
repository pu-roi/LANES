"""Combine queue identities in SQL before ordering, counting and pagination."""
from datetime import datetime

from sqlalchemy import DateTime, Integer, Text, and_, cast, func, literal, or_, select, union_all
from sqlalchemy.orm import Session
from sqlalchemy.engine import RowMapping
from sqlalchemy.sql.selectable import Subquery

from app.crud.news_results import readable_claim, readable_run, result_rows
from app.models.report import FloodReport
from app.services.hybrid_extraction_service import MAX_AUTO_ACTIVATION_AGE


def review_rows(db: Session, now: datetime) -> Subquery:
    report = FloodReport
    reports = select(
        literal("user_report").label("source"), report.id.label("record_id"),
        literal(-1, Integer).label("claim_index"), report.created_at.label("queued_at"),
        (literal("Report #") + cast(report.id, Text)).label("title"),
        func.coalesce(report.human_readable_location, report.barangay, report.city, "Location not specified").label("location"),
        report.raw_text.label("evidence"), literal("Pending user-report verification.").label("review_reason"),
        cast(report.severity, Text).label("severity"), report.depth,
    ).where(report.status == "pending", report.deleted_at.is_(None))

    news, value, _, _ = result_rows(db, latest_only=True)
    # Explicit historical observations must not become current merely because
    # somebody reprocessed an old captured article today.
    timestamp = lambda item: cast(item, DateTime(timezone=True)) if db.get_bind().dialect.name == "postgresql" else func.julianday(item)
    start, end = now - MAX_AUTO_ACTIVATION_AGE, now
    fresh = lambda item: timestamp(item).between(timestamp(literal(start)), timestamp(literal(end)))
    news = news.where(
        readable_claim(value), readable_run(db), value("action_type") == "flagged_review",
        value("condition").not_in(["subsided", "receding"]),
        or_(value("event_time_resolved").is_(None), timestamp(value("event_time_resolved")) >= timestamp(literal(start))),
    ).subquery()
    # Unknown publication clocks are reviewable only on newly discovered
    # evidence; this freshness bound does not invent an observation time.
    news = select(news).where(or_(
        fresh(news.c.published_at), and_(news.c.published_at.is_(None), fresh(news.c.saved_at)),
    )).subquery()
    if db.get_bind().dialect.name == "postgresql":
        field = lambda name: cast(news.c.claim.op("->>")(name), Text)
    else:
        field = lambda name: func.json_extract(news.c.claim, f"$.{name}")
    claims = select(
        literal("news_claim").label("source"), news.c.run_id.label("record_id"), news.c.claim_index,
        news.c.captured_at.label("queued_at"), news.c.title,
        func.coalesce(field("canonical_road"), field("raw_place_name"), "Location unresolved").label("location"),
        field("evidence_sentence").label("evidence"),
        func.coalesce(field("action_rationale"), "Incomplete or conflicting flood evidence.").label("review_reason"),
        literal(None, Text).label("severity"), field("depth_raw").label("depth"),
    )
    return union_all(reports, claims).subquery()


def list_review_identities(db: Session, now: datetime) -> list[RowMapping]:
    """Compact current identities; grouping precedes card pagination."""
    rows = review_rows(db, now)
    return list(db.execute(select(rows.c.source, rows.c.record_id, rows.c.claim_index, rows.c.queued_at)).mappings())


def list_report_group_metadata(db: Session) -> list[RowMapping]:
    """No report bodies, ORM relationships, road tracing or synthesis calls."""
    report = FloodReport
    geometry = func.ST_AsGeoJSON(func.ST_Transform(report.geometry, 32651)) if db.get_bind().dialect.name == "postgresql" else cast(report.geometry, Text)
    query = select(report.id, report.human_readable_location, report.city, report.barangay,
        report.created_at, geometry.label("geometry")).where(report.status == "pending", report.deleted_at.is_(None))
    return list(db.execute(query).mappings())


def read_review_members(db: Session, identities: list[tuple[str, int, int]], now: datetime) -> list[RowMapping]:
    if not identities:
        return []
    rows = review_rows(db, now)
    return list(db.execute(select(rows).where(or_(*(and_(rows.c.source == source,
        rows.c.record_id == record_id, rows.c.claim_index == index) for source, record_id, index in identities)))).mappings())


def is_current_review(db: Session, source: str, record_id: int, claim_index: int, now: datetime) -> bool:
    rows = review_rows(db, now)
    return db.scalar(select(rows.c.record_id).where(rows.c.source == source,
        rows.c.record_id == record_id, rows.c.claim_index == claim_index).limit(1)) is not None
