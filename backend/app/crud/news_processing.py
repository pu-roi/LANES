"""Transactional immutable inputs, idempotent enqueue, and owned worker leases."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import exists, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_discovery_service import MAX_ARTICLE_CHARS, extraction_input_snapshot

PIPELINE_VERSION = "rules-spatial-preview-v11"
MAX_ATTEMPTS = 5
LEASE_SECONDS = 300


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def current_pipeline_version() -> str:
    from app.services.news_road_placement_service import get_news_road_placement_provider
    from app.services.news_placement_preview_service import get_news_placement_preview_service
    sources = f"{get_news_road_placement_provider().revision}:{get_news_placement_preview_service().revision}"
    return f"{PIPELINE_VERSION}:{hashlib.sha256(sources.encode()).hexdigest()}"


def enqueue_article(db: Session, article: NewsArticle, *, pipeline_version: str | None = None) -> int | None:
    """Capture valid pending input in the caller's article transaction; no commit."""
    if (article.review_state != "pending" or article.article_error or not (article.article_text or "").strip()
            or len(article.article_text or "") > MAX_ARTICLE_CHARS):
        return None
    db.flush()
    pipeline_version = pipeline_version or current_pipeline_version()
    source = NewsArticleExtractorInput(
        article_id=article.id, canonical_url=article.canonical_url, publisher=article.publisher_source_id,
        title=article.title, excerpt=article.excerpt or "", article_text=article.article_text,
        published_at=article.published_at,
    )
    snapshot, fingerprint = extraction_input_snapshot(source)
    dialect = db.get_bind().dialect.name
    insert = pg_insert if dialect == "postgresql" else sqlite_insert if dialect == "sqlite" else None
    if insert is None:
        raise ValueError("News processing requires PostgreSQL or development SQLite")
    now = utc_now()
    version_id = db.scalar(insert(NewsArticleVersion).values(
        article_id=article.id, input_fingerprint=fingerprint, input_snapshot=snapshot, created_at=now,
    ).on_conflict_do_nothing(index_elements=["article_id", "input_fingerprint"]).returning(NewsArticleVersion.id))
    if version_id is None:
        version_id = db.scalar(select(NewsArticleVersion.id).where(
            NewsArticleVersion.article_id == article.id, NewsArticleVersion.input_fingerprint == fingerprint))
    run_id = db.scalar(insert(NewsExtractionRun).values(
        article_version_id=version_id, pipeline_version=pipeline_version, mode="rules_only", status="pending",
        attempt_count=0, created_at=now, updated_at=now,
    ).on_conflict_do_nothing(index_elements=["article_version_id", "pipeline_version", "mode"]).returning(NewsExtractionRun.id))
    return run_id if run_id is not None else db.scalar(select(NewsExtractionRun.id).where(
        NewsExtractionRun.article_version_id == version_id, NewsExtractionRun.pipeline_version == pipeline_version,
        NewsExtractionRun.mode == "rules_only"))


def capture_pending_inputs(db: Session, limit: int) -> int:
    """Bounded migration/restart handoff; skip captured runs and moderated history."""
    captured = exists(select(NewsExtractionRun.id).join(
        NewsArticleVersion, NewsArticleVersion.id == NewsExtractionRun.article_version_id,
    ).where(NewsArticleVersion.article_id == NewsArticle.id, NewsExtractionRun.pipeline_version == current_pipeline_version()))
    articles = db.scalars(select(NewsArticle).where(
        NewsArticle.review_state == "pending", NewsArticle.article_error.is_(None),
        func.length(func.trim(NewsArticle.article_text)) > 0,
        func.length(NewsArticle.article_text) <= MAX_ARTICLE_CHARS, ~captured,
    ).order_by(NewsArticle.id).limit(limit)).all()
    return sum(enqueue_article(db, article) is not None for article in articles)


@dataclass(frozen=True)
class ClaimedExtraction:
    run_id: int
    article_id: int
    lease_token: UUID | None
    attempt_count: int
    input_snapshot: dict
    input_fingerprint: str
    exhausted: bool = False


def claim_due_run(db: Session, now: datetime, *, article_id: int | None = None) -> ClaimedExtraction | None:
    """Caller commits the short claim transaction before doing CPU extraction."""
    run = NewsExtractionRun
    due = or_(run.status == "pending", (run.status == "retry_wait") & (run.next_attempt_at <= now),
              (run.status == "processing") & (run.lease_expires_at <= now))
    query = select(run).join(NewsArticleVersion).where(due, run.pipeline_version == current_pipeline_version())
    if article_id is not None:
        query = query.where(NewsArticleVersion.article_id == article_id)
    while True:
        row = db.scalar(query.order_by(run.created_at, run.id).with_for_update(of=run, skip_locked=True).limit(1))
        if row is None:
            return None
        if row.attempt_count >= MAX_ATTEMPTS:
            row.status, row.error_code = "failed", "lease_expired_exhausted"
            row.lease_token = row.lease_expires_at = row.next_attempt_at = None
            row.completed_at = row.updated_at = now
            db.flush()
            version = db.get(NewsArticleVersion, row.article_version_id)
            return ClaimedExtraction(row.id, version.article_id, None, row.attempt_count,
                                     deepcopy(version.input_snapshot), version.input_fingerprint, exhausted=True)
        row.status = "processing"
        row.attempt_count += 1
        row.lease_token = uuid4()
        row.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
        row.started_at = row.updated_at = now
        row.next_attempt_at = row.completed_at = row.error_code = None
        row.result = None
        db.flush()
        version = db.get(NewsArticleVersion, row.article_version_id)
        return ClaimedExtraction(row.id, version.article_id, row.lease_token, row.attempt_count,
                                 deepcopy(version.input_snapshot), version.input_fingerprint)


def finish_owned_run(db: Session, claim: ClaimedExtraction, now: datetime, *, result: dict | None = None,
                     error_code: str | None = None, retryable: bool = False) -> bool:
    """Expired/superseded attempts cannot complete or fail someone else's lease."""
    values: dict = {"lease_token": None, "lease_expires_at": None, "updated_at": now}
    if error_code:
        retry = retryable and claim.attempt_count < MAX_ATTEMPTS
        values.update(status="retry_wait" if retry else "failed", error_code=error_code[:100], result=None,
                      next_attempt_at=now + timedelta(seconds=min(900, 60 * 2 ** (claim.attempt_count - 1))) if retry else None,
                      completed_at=None if retry else now)
    else:
        if result is None:
            raise ValueError("Completed extraction requires a result")
        values.update(status="completed", result=result, error_code=None, next_attempt_at=None, completed_at=now)
    updated = db.execute(update(NewsExtractionRun).where(
        NewsExtractionRun.id == claim.run_id, NewsExtractionRun.status == "processing",
        NewsExtractionRun.lease_token == claim.lease_token, NewsExtractionRun.lease_expires_at > now,
    ).values(**values).execution_options(synchronize_session=False))
    return updated.rowcount == 1


def list_article_runs(db: Session, article_id: int, limit: int = 20) -> list[NewsExtractionRun]:
    return list(db.scalars(select(NewsExtractionRun).join(NewsArticleVersion).where(
        NewsArticleVersion.article_id == article_id,
    ).order_by(NewsExtractionRun.id.desc()).limit(limit)))
