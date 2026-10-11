"""Combine queue identities in SQL before ordering, counting and pagination."""
from datetime import datetime

from sqlalchemy import DateTime, Integer, Text, and_, cast, func, literal, or_, select, union_all
from sqlalchemy.orm import Session
from sqlalchemy.engine import RowMapping
from sqlalchemy.sql.selectable import Subquery

from app.crud.news_results import readable_claim, readable_run, result_rows
from app.models.report import FloodReport
from app.models.news import NewsExtractionRun
from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimSource
from app.services.hybrid_extraction_service import MAX_AUTO_ACTIVATION_AGE


def review_rows(db: Session, now: datetime, *, publication_admission_at: datetime | None = None) -> Subquery:
    report = FloodReport
    reports = select(
        literal("user_report").label("source"), report.id.label("record_id"),
        literal(-1, Integer).label("claim_index"), report.created_at.label("queued_at"),
        (literal("Report #") + cast(report.id, Text)).label("title"),
        func.coalesce(report.human_readable_location, report.barangay, report.city, "Location not specified").label("location"),
        report.raw_text.label("evidence"), literal("Pending user-report verification.").label("review_reason"),
        cast(report.severity, Text).label("severity"), report.depth, report.city, report.barangay,
    ).where(report.status == "pending", report.deleted_at.is_(None))

    news, value, _, _ = result_rows(db, latest_only=True)
    if db.get_bind().dialect.name == "postgresql":
        # A preserved extraction action is not a durable current decision.
        # Select the case's latest revision before excluding resolved/deferred
        # work, so an old needs-review decision cannot resurrect an active case.
        # New extraction evidence can be consumed by an existing incident case.
        # Check that case's current decision as well as the source's own case;
        # an obsolete exception on the latter must not resurrect resolved work.
        decision_source = or_(NewsClaimDecision.case_id == NewsClaimSource.case_id,
            NewsClaimDecision.snapshot["claim_source_id"].as_integer() == NewsClaimSource.id)
        current = select(NewsClaimSource.id).select_from(NewsClaimSource).join(
            NewsClaimDecision, decision_source).join(NewsClaimCase,
            and_(NewsClaimDecision.case_id == NewsClaimCase.id,
                 NewsClaimDecision.revision == NewsClaimCase.revision)).where(
            NewsClaimSource.extraction_run_id == NewsExtractionRun.id,
            NewsClaimSource.claim_ordinal == news.selected_columns.claim_index,
            or_(NewsClaimDecision.review_state == "resolved",
                and_(NewsClaimDecision.review_state == "deferred",
                     cast(NewsClaimDecision.snapshot["deferred_until"].astext, DateTime(timezone=True)) > now)),
        ).correlate_except(NewsClaimSource, NewsClaimCase, NewsClaimDecision).exists()
        news = news.where(~current)
        geometry_review = select(literal(
            "Flood evidence is verified; the affected road geometry still requires resolution."
        )).select_from(NewsClaimSource).join(NewsClaimDecision, decision_source).join(NewsClaimCase,
            and_(NewsClaimDecision.case_id == NewsClaimCase.id,
                 NewsClaimDecision.revision == NewsClaimCase.revision)).where(
            NewsClaimSource.extraction_run_id == NewsExtractionRun.id,
            NewsClaimSource.claim_ordinal == news.selected_columns.claim_index,
            NewsClaimDecision.review_state == "needs_review",
            NewsClaimDecision.reason_code == "estimated_road_needs_review",
        ).correlate_except(NewsClaimSource, NewsClaimCase, NewsClaimDecision).limit(1).scalar_subquery()
        news = news.add_columns(geometry_review.label("lifecycle_review_reason"))
    else:
        news = news.add_columns(literal(None, Text).label("lifecycle_review_reason"))
    # Explicit historical observations must not become current merely because
    # somebody reprocessed an old captured article today.
    timestamp = lambda item: cast(item, DateTime(timezone=True)) if db.get_bind().dialect.name == "postgresql" else func.julianday(item)
    start = now - MAX_AUTO_ACTIVATION_AGE
    publication_now = publication_admission_at or now
    publication_start = publication_now - MAX_AUTO_ACTIVATION_AGE
    fresh = lambda item: timestamp(item).between(timestamp(literal(publication_start)), timestamp(literal(publication_now)))
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
        func.coalesce(news.c.lifecycle_review_reason, field("action_rationale"), "Incomplete or conflicting flood evidence.").label("review_reason"),
        literal(None, Text).label("severity"), field("depth_raw").label("depth"),
        field("canonical_city").label("city"), field("canonical_barangay").label("barangay"),
    )
    return union_all(reports, claims).subquery()


def list_review_identities(db: Session, now: datetime) -> list[RowMapping]:
    """Queue facts for server search/summary; no detail relationships are loaded."""
    rows = review_rows(db, now)
    return list(db.execute(select(rows)).mappings())


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
