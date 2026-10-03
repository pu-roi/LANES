"""Explicit persistence boundaries for operational attempts, not flood decisions."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.crud.news_telemetry import AttemptKind, finalize_attempt, interrupt_abandoned, list_attempts
from app.schemas.news_telemetry import FeedAttempt, FallbackLead, NewsTelemetryPage, TelemetryAttempt
from app.models.news import NewsArticle
from app.models.news_telemetry import NewsDiscoveryRun, NewsFallbackLookup, NewsFallbackLookupLead
from app.services.news_open_search_service import OpenSearchLookup


def begin_discovery(db: Session, actor_id: int | None) -> int:
    now = datetime.now(timezone.utc)
    interrupt_abandoned(db, now)
    row = NewsDiscoveryRun(actor_id=actor_id, trigger="staff" if actor_id is not None else "collector", started_at=now)
    db.add(row)
    db.flush()
    id = row.id
    db.commit()
    return id


def browse_telemetry(db: Session, kind: AttemptKind, page: int, page_size: int) -> NewsTelemetryPage:
    rows, children, total, actual = list_attempts(db, kind, page, page_size)
    grouped: dict[int, list] = {}
    for child in children:
        parent = child.discovery_run_id if kind == "discovery" else child.lookup_id
        grouped.setdefault(parent, []).append(child)
    items = []
    for row in rows:
        items.append(TelemetryAttempt(id=row.id, status=row.status, started_at=row.started_at,
            finished_at=row.finished_at, error_code=row.error_code,
            trigger=row.trigger if kind == "discovery" else None,
            article_id=row.article_id if kind == "fallback" else None,
            retrieve_articles=row.retrieve_articles if kind == "fallback" else None,
            retry_after_seconds=row.retry_after_seconds if kind == "fallback" else None,
            feeds=[FeedAttempt.model_validate(child) for child in grouped.get(row.id, [])] if kind == "discovery" else [],
            leads=[FallbackLead.model_validate(child) for child in grouped.get(row.id, [])] if kind == "fallback" else []))
    return NewsTelemetryPage(items=items, total=total, page=actual, page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size))


def begin_fallback(db: Session, article: NewsArticle, actor_id: int, retrieve_articles: bool) -> int:
    now = datetime.now(timezone.utc)
    interrupt_abandoned(db, now)
    row = NewsFallbackLookup(article_id=article.id, actor_id=actor_id,
        content_fingerprint=article.content_fingerprint, retrieve_articles=retrieve_articles, started_at=now)
    db.add(row)
    db.flush()
    id = row.id
    db.commit()
    return id


def finish_discovery(db: Session, id: int, error_code: str | None = None) -> None:
    finalize_attempt(db, NewsDiscoveryRun, id, status="failed" if error_code else "completed",
        now=datetime.now(timezone.utc), error_code=error_code)
    db.commit()


def finish_fallback(db: Session, id: int, result: OpenSearchLookup | None = None) -> None:
    error_code = "lookup_failed" if result is None else "provider_throttled" if result.retry_after_seconds is not None else "lookup_partial_failure" if result.errors else None
    # Finalization and child insertion commit atomically. Repeating finalization
    # cannot duplicate leads or replace a finalized/interrupted attempt.
    updated = finalize_attempt(db, NewsFallbackLookup, id, status="failed" if error_code else "completed",
        now=datetime.now(timezone.utc), error_code=error_code,
        retry_after_seconds=min(result.retry_after_seconds, 2_147_483_647) if result and result.retry_after_seconds is not None else None)
    if updated and result is not None:
        for ordinal, hit in enumerate(result.results):
            db.add(NewsFallbackLookupLead(lookup_id=id, ordinal=ordinal, article_url=hit.url,
                source_id=hit.publisher_source_id, retrieved_at=hit.fetched_at,
                retrieval_status="retrieved" if hit.article_text and not hit.article_error else "failed" if hit.article_error else "not_requested",
                error_code="article_retrieval_failed" if hit.article_error else None,
                assessment=hit.event_review.status if hit.event_review else hit.match_status))
    db.commit()
