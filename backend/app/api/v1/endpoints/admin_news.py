"""Staff-only read and probe actions for candidate publisher feeds."""

from dataclasses import asdict

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import hashlib
import uuid
from datetime import datetime, timezone

from app.api import deps
from app.crud.news import get_article, list_feed_checkpoints, list_pending_articles
from app.core.database import get_db
from app.core.limiter import limiter
from app.models.news import NewsArticle
from app.schemas.news_candidate import (
    ManualNewsCandidateInput,
    NewsArticleSummary,
    NewsDiscoveryRunSummary,
    NewsFeedCheckpointSummary,
    NewsFeedProbeResult,
    NewsSourceProbeResponse,
    NewsSourceSummary,
)
from app.services.news_discovery_service import discover_news
from app.services.news_feed_service import probe_feed
from app.services.news_sources import load_news_sources
from sqlalchemy import select
from sqlalchemy.orm import selectinload


router = APIRouter()


@router.get("/feeds", response_model=list[NewsFeedCheckpointSummary])
def list_news_feeds(
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> list[NewsFeedCheckpointSummary]:
    """Expose persisted feed success/failure state to staff."""
    return [NewsFeedCheckpointSummary.model_validate(row) for row in list_feed_checkpoints(db)]


@router.get("/candidates", response_model=list[NewsArticleSummary])
def list_news_candidates(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> list[NewsArticleSummary]:
    """Show pending RSS evidence to staff; this does not create flood reports."""
    return [NewsArticleSummary.model_validate(article) for article in list_pending_articles(db, limit)]


@router.post("/runs", response_model=NewsDiscoveryRunSummary)
@limiter.limit("1/10minutes")
def run_news_discovery(
    request: Request,
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> NewsDiscoveryRunSummary:
    """Staff-triggered collection; all evidence remains pending for review."""
    active = tuple(source for source in load_news_sources() if source.enabled and source.verified_at)
    if not active:
        raise HTTPException(status_code=503, detail="No verified news sources are enabled")
    try:
        with httpx.Client(timeout=httpx.Timeout(12.0, connect=5.0)) as client:
            result = discover_news(active, client, db)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="News discovery storage is unavailable") from exc
    return NewsDiscoveryRunSummary(
        probes=[NewsFeedProbeResult.model_validate(asdict(probe)) for probe in result.probes],
        new_or_updated_candidates=len(result.candidates),
    )


@router.get("/sources", response_model=list[NewsSourceSummary])
def list_news_sources(_staff: object = Depends(deps.get_current_active_admin)) -> list[NewsSourceSummary]:
    """Show candidate and enabled sources without changing moderation state."""
    return [NewsSourceSummary.model_validate(asdict(source)) for source in load_news_sources()]


@router.post("/sources/{source_id}/probe", response_model=NewsSourceProbeResponse)
@limiter.limit("5/minute")
def probe_news_source(
    request: Request,
    source_id: str,
    _staff: object = Depends(deps.get_current_active_admin),
) -> NewsSourceProbeResponse:
    """Check configured feeds for one publisher; no article fetch or activation."""
    source = next((item for item in load_news_sources() if item.id == source_id), None)
    if source is None:
        raise HTTPException(status_code=404, detail="News source not found")
    if not source.feed_urls:
        raise HTTPException(status_code=422, detail="No feed URL candidate is configured for this source")
    results: list[NewsFeedProbeResult] = []
    with httpx.Client(timeout=httpx.Timeout(12.0, connect=5.0)) as client:
        for feed_url in source.feed_urls:
            probe, _ = probe_feed(source, feed_url, client)
            results.append(NewsFeedProbeResult.model_validate(asdict(probe)))
    return NewsSourceProbeResponse(source_id=source_id, results=results)


@router.post("/manual-candidate", response_model=NewsArticleSummary)
def submit_manual_news_candidate(
    payload: ManualNewsCandidateInput,
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> NewsArticleSummary:
    """Permit administrator-supplied public post text or link (e.g. Facebook DRRMO / citizen post).
    
    Creates a pending news article candidate for extraction and review without requiring paid APIs.
    """
    now = datetime.now(timezone.utc)
    raw_url = payload.source_url.strip() if payload.source_url else None
    if not raw_url:
        raw_url = f"https://lanes.internal/manual-social/{uuid.uuid4().hex[:12]}"

    fingerprint = hashlib.sha256(f"{payload.title} {payload.text}".casefold().encode("utf-8")).hexdigest()

    article = get_article(db, raw_url)
    if article is None:
        article = NewsArticle(
            canonical_url=raw_url,
            publisher_source_id=payload.publisher[:100],
            title=payload.title[:500],
            excerpt=payload.text[:500],
            published_at=now,
            fetched_at=now,
            first_seen_at=now,
            last_seen_at=now,
            article_text=payload.text[:30_000],
            article_error=None,
            content_fingerprint=fingerprint,
            review_state="pending",
        )
        db.add(article)
    else:
        article.title = payload.title[:500]
        article.excerpt = payload.text[:500]
        article.article_text = payload.text[:30_000]
        article.last_seen_at = now
        article.content_fingerprint = fingerprint

    db.commit()
    refreshed = db.scalar(
        select(NewsArticle)
        .options(selectinload(NewsArticle.feed_entries))
        .where(NewsArticle.id == article.id)
    )
    return NewsArticleSummary.model_validate(refreshed)
