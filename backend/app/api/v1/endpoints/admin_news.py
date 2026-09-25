"""Staff-only read and probe actions for candidate publisher feeds."""

from dataclasses import asdict

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.news import list_feed_checkpoints, list_pending_articles
from app.core.database import get_db
from app.core.limiter import limiter
from app.schemas.news_candidate import NewsArticleSummary, NewsDiscoveryRunSummary, NewsFeedCheckpointSummary, NewsFeedProbeResult, NewsSourceProbeResponse, NewsSourceSummary
from app.services.news_discovery_service import discover_news
from app.services.news_feed_service import probe_feed
from app.services.news_sources import load_news_sources


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
