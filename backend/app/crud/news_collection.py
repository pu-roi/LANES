"""Paginate collection attention states and counts without loading article bodies."""

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.orm import Session, defer
from sqlalchemy.sql import ColumnElement, Select

from app.crud.news_browsing import article_body_status, latest_article_runs
from app.crud.news_results import context_only_claim, readable_claim, readable_run, result_rows
from app.models.news import NewsArticle, NewsExtractionRun
from app.schemas.news_collection import CollectionFilter


def collection_rows(db: Session) -> tuple[Select, ColumnElement]:
    rows, value, _, _ = result_rows(db, latest_only=True)
    totals = rows.with_only_columns(
        NewsExtractionRun.id.label("run_id"),
        func.sum(case((~context_only_claim(value), 1), else_=0)).label("claim_count"),
        func.sum(case((readable_claim(value) & readable_run(db), 1), else_=0)).label("location_count"),
    ).group_by(NewsExtractionRun.id).subquery()
    latest = latest_article_runs()
    claim_count = func.coalesce(totals.c.claim_count, 0)
    location_count = func.coalesce(totals.c.location_count, 0)
    body = article_body_status()
    # Metadata-only legacy leads cannot establish the actual-flood requirement.
    # Failed refreshes of previously qualifying evidence remain visible issues.
    history, history_value, _, _ = result_rows(db)
    credible_history = history.where(readable_claim(history_value), readable_run(db)).subquery()
    had_readable_evidence = exists(select(1).select_from(credible_history).where(
        credible_history.c.article_id == NewsArticle.id))
    unsupported_body = and_(location_count == 0, body.in_(["error", "missing"]), ~had_readable_evidence)
    processing = func.coalesce(NewsExtractionRun.status, "not_recorded")
    status = case(
        (NewsArticle.review_state == "local_update", "excluded"),
        (unsupported_body, "excluded"),
        (body == "error", "retrieval_failed"), (body == "missing", "missing_text"),
        (processing == "not_recorded", "waiting"),
        (processing.in_(["pending", "processing", "retry_wait"]), "processing"),
        (processing == "failed", "processing_failed"),
        (or_(NewsExtractionRun.result.is_(None), ~readable_run(db)), "needs_checking"),
        (location_count == 0, "excluded"), (location_count < claim_count, "needs_checking"),
        else_="ready",
    )
    query = select(NewsArticle, body, processing, NewsExtractionRun.id, status.label("collection_status"),
        location_count, case((status == "excluded", 0), else_=claim_count - location_count).label("questionable_count")).outerjoin(
        latest, latest.c.article_id == NewsArticle.id).outerjoin(NewsExtractionRun, NewsExtractionRun.id == latest.c.run_id
        ).outerjoin(totals, totals.c.run_id == NewsExtractionRun.id)
    return query, status


def list_collection(db: Session, *, page: int, page_size: int, search: str, publisher: str | None,
                    status: CollectionFilter) -> tuple[list, int, int, dict[str, int], list[str]]:
    query, state = collection_rows(db)
    overview = query.subquery()
    counts = dict(db.execute(select(overview.c.collection_status, func.count()).group_by(overview.c.collection_status)).all())
    if status == "attention":
        query = query.where(state.not_in(["ready", "excluded", "no_locations"]))
    elif status != "all":
        query = query.where(state == status)
    if search.strip():
        query = query.where(or_(NewsArticle.title.icontains(search.strip(), autoescape=True),
                               NewsArticle.excerpt.icontains(search.strip(), autoescape=True)))
    if publisher:
        query = query.where(NewsArticle.publisher_source_id == publisher)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    actual_page = min(page, max(1, (total + page_size - 1) // page_size))
    rows = db.execute(query.options(defer(NewsArticle.article_text)).order_by(NewsArticle.last_seen_at.desc(),
        NewsArticle.id.desc()).offset((actual_page - 1) * page_size).limit(page_size)).all()
    publishers = list(db.scalars(select(NewsArticle.publisher_source_id).distinct().order_by(NewsArticle.publisher_source_id)))
    return list(rows), total, actual_page, counts, publishers
