"""Bounded latest-decision reads; public reads never advance the lifecycle."""
from datetime import datetime, timedelta

from sqlalchemy import Integer, and_, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimSource


def latest_decisions():
    return select(NewsClaimDecision).join(NewsClaimCase, and_(
        NewsClaimDecision.case_id == NewsClaimCase.id,
        NewsClaimDecision.revision == NewsClaimCase.revision))


def current_public_query(now: datetime, approved_source_ids: tuple[str, ...]):
    decision = NewsClaimDecision
    source = NewsClaimSource
    # Immutable source bindings, rather than an article's mutable latest body,
    # identify the publisher of the stored public decision.
    source_id = cast(decision.snapshot["claim_source_id"].astext, Integer)
    hours = cast(decision.snapshot["unconfirmed_retention_hours"].astext, Integer)
    retention = hours * timedelta(hours=1)
    return latest_decisions().join(source, source.id == source_id).join(
        NewsExtractionRun, NewsExtractionRun.id == source.extraction_run_id).join(
        NewsArticleVersion, NewsArticleVersion.id == NewsExtractionRun.article_version_id).where(
        decision.snapshot["schema_version"].astext == "news-publication-v1",
        decision.snapshot["public"].is_not(None),
        NewsArticleVersion.input_snapshot["publisher"].astext.in_(approved_source_ids),
        hours.between(1, 72),
        or_(
            and_(decision.public_state.in_(("active_alert", "active_zone", "expired")),
                 decision.expires_at.is_not(None), decision.expires_at + retention > now),
            and_(decision.operation == "clear", decision.observed_at.is_not(None),
                 decision.observed_at + retention > now),
        ))


def list_public_decisions(db: Session, *, now: datetime, approved_source_ids: tuple[str, ...],
                          page: int, page_size: int) -> tuple[list[NewsClaimDecision], int, int]:
    query = current_public_query(now, approved_source_ids)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    actual_page = min(page, max(1, (total + page_size - 1) // page_size))
    rows = list(db.scalars(query.order_by(NewsClaimDecision.decided_at.desc(), NewsClaimDecision.id.desc())
                          .offset((actual_page - 1) * page_size).limit(page_size)))
    return rows, total, actual_page


def read_latest_decision(db: Session, case_id: int) -> NewsClaimDecision | None:
    return db.scalar(latest_decisions().where(NewsClaimCase.id == case_id))


def list_decision_history(db: Session, case_id: int, *, page: int, page_size: int) -> tuple[list[NewsClaimDecision], int, int]:
    query = select(NewsClaimDecision).where(NewsClaimDecision.case_id == case_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    actual_page = min(page, max(1, (total + page_size - 1) // page_size))
    return list(db.scalars(query.order_by(NewsClaimDecision.revision.desc())
        .offset((actual_page - 1) * page_size).limit(page_size))), total, actual_page


def source_for_claim(db: Session, run_id: int, ordinal: int) -> NewsClaimSource | None:
    return db.scalar(select(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run_id,
                                                NewsClaimSource.claim_ordinal == ordinal))


def source_input_for_decision(db: Session, decision: NewsClaimDecision) -> dict | None:
    identity = decision.snapshot.get("claim_source_id")
    if not isinstance(identity, int) or identity <= 0:
        return None
    row = db.execute(select(NewsArticleVersion.input_snapshot, NewsArticleVersion.article_id).join(
        NewsExtractionRun, NewsExtractionRun.article_version_id == NewsArticleVersion.id).join(
        NewsClaimSource, NewsClaimSource.extraction_run_id == NewsExtractionRun.id).where(NewsClaimSource.id == identity)).first()
    return {**row[0], "article_id": row[1]} if row else None
