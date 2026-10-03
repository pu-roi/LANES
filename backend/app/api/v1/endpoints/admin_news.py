"""Staff-only read and probe actions for candidate publisher feeds."""

from dataclasses import asdict

import httpx
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response
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
    NewsSavedExtractionSummary,
    NewsExtractionRunSummary,
    NewsProcessingSummary,
    NewsDiscoveryRunSummary,
    NewsFeedCheckpointSummary,
    NewsFeedProbeResult,
    OpenSearchLookupSummary,
    NewsSourceProbeResponse,
    NewsSourceSummary,
)
from app.services.news_discovery_service import discover_news, extract_saved_news_articles
from app.services.news_fallback_service import FallbackInput, lookup_news_leads
from app.services.news_feed_service import canonical_article_url, probe_feed
from app.services.news_sources import load_news_sources
from app.schemas.news_browsing import ArticleOrder, BodyStatus, NewsArticleDetail, NewsArticlePage, ProcessingStatus
from app.services.news_browsing_service import browse_news_articles, read_news_article_detail
from app.schemas.news_extraction import FloodCondition
from app.schemas.news_results import NewsResultDetail, NewsResultPage, PlacementFilter, ResultOrder
from app.services.news_results_service import browse_news_results, read_news_result
from app.schemas.news_collection import CollectionFilter, NewsCollectionPage
from app.services.news_collection_service import browse_news_collection
from sqlalchemy import select
from sqlalchemy.orm import selectinload, sessionmaker
from app.schemas.news_monitoring import NewsMonitoringSummary
from app.services.news_monitoring_service import read_news_monitoring
from app.crud.news_telemetry import AttemptKind
from app.schemas.news_telemetry import NewsTelemetryPage
from app.services.news_telemetry_service import browse_telemetry


router = APIRouter()


@router.get("/monitoring/{kind}", response_model=NewsTelemetryPage)
def news_telemetry_history(
    kind: AttemptKind,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> NewsTelemetryPage:
    """Read bounded operational history; never triggers network or writes."""
    try:
        return browse_telemetry(db, kind, page, page_size)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="News telemetry storage is unavailable") from exc


@router.get("/monitoring", response_model=NewsMonitoringSummary)
def news_monitoring(
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> NewsMonitoringSummary:
    """Read current saved evidence totals; does not trigger collection."""
    try:
        return read_news_monitoring(db)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="News monitoring storage is unavailable") from exc


@router.get("/collection", response_model=NewsCollectionPage)
def browse_collection(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    search: str = Query(default="", max_length=200),
    publisher: str | None = Query(default=None, max_length=100),
    status: CollectionFilter = "attention",
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> NewsCollectionPage:
    """Read saved articles needing collection or extraction attention."""
    try:
        return browse_news_collection(db, page=page, page_size=page_size, search=search, publisher=publisher, status=status)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="News collection storage is unavailable") from exc


@router.get("/results", response_model=NewsResultPage)
def browse_results(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    search: str = Query(default="", max_length=200),
    publisher: str | None = Query(default=None, max_length=100),
    condition: FloodCondition | None = None,
    placement: PlacementFilter | None = None,
    order: ResultOrder = "extraction_newest",
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> NewsResultPage:
    """Paginate reported locations from each article's newest recorded run."""
    try:
        return browse_news_results(db, page=page, page_size=page_size, search=search,
            publisher=publisher, condition=condition, placement=placement, order=order)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="News result storage is unavailable") from exc


@router.get("/results/{run_id}/{claim_index}", response_model=NewsResultDetail)
def read_result(
    run_id: int = Path(ge=1),
    claim_index: int = Path(ge=0),
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> NewsResultDetail:
    """Read one artifact ordinal and its immutable source; no lifecycle inference."""
    try:
        detail = read_news_result(db, run_id, claim_index)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="News result storage is unavailable") from exc
    if detail is None:
        raise HTTPException(status_code=404, detail="News result not found")
    return detail


@router.get("/articles", response_model=NewsArticlePage)
def browse_articles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    search: str = Query(default="", max_length=200),
    publisher: str | None = Query(default=None, max_length=100),
    body: BodyStatus | None = None,
    processing: ProcessingStatus | None = None,
    order: ArticleOrder = "recently_seen",
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> NewsArticlePage:
    """Read saved articles with server-owned filters, ordering and pagination."""
    try:
        return browse_news_articles(db, page=page, page_size=page_size, search=search,
                                    publisher=publisher, body=body, processing=processing, order=order)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="News article storage is unavailable") from exc


@router.get("/articles/{article_id}", response_model=NewsArticleDetail)
def read_article(
    article_id: int,
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> NewsArticleDetail:
    """Read captured inputs and the newest twenty recorded runs; never recompute."""
    try:
        detail = read_news_article_detail(db, article_id)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="News article storage is unavailable") from exc
    if detail is None:
        raise HTTPException(status_code=404, detail="News article not found")
    return detail


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


@router.get("/candidates/{article_id}/extraction", response_model=NewsSavedExtractionSummary)
@limiter.limit("3/minute")
async def preview_saved_news_extraction(
    request: Request,
    response: Response,
    article_id: int,
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> NewsSavedExtractionSummary:
    """Preview rules extraction of saved evidence without processing/zone writes."""
    article = db.get(NewsArticle, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="News article not found")
    result = (await extract_saved_news_articles([article]))[0]
    return NewsSavedExtractionSummary.model_validate(asdict(result))


@router.get("/candidates/{article_id}/processing", response_model=list[NewsExtractionRunSummary])
def saved_news_processing_status(
    article_id: int,
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> list[NewsExtractionRunSummary]:
    from app.crud.news_processing import list_article_runs
    if db.get(NewsArticle, article_id) is None:
        raise HTTPException(status_code=404, detail="News article not found")
    return [NewsExtractionRunSummary.model_validate(row) for row in list_article_runs(db, article_id)]


@router.post("/candidates/{article_id}/processing", response_model=NewsProcessingSummary)
@limiter.limit("3/minute")
async def process_saved_news_candidate(
    request: Request,
    response: Response,
    article_id: int,
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> NewsProcessingSummary:
    from app.crud.news_processing import enqueue_article
    from app.services.news_processing_service import process_saved_news
    article = db.get(NewsArticle, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="News article not found")
    try:
        if enqueue_article(db, article) is None:
            raise HTTPException(status_code=409, detail="Processing requires pending evidence with an available, error-free body")
        db.commit()
        result = await process_saved_news(sessionmaker(bind=db.get_bind()), limit=20, article_id=article_id)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="News processing storage is unavailable") from exc
    return NewsProcessingSummary.model_validate(asdict(result))


@router.get("/candidates/{article_id}/open-leads", response_model=OpenSearchLookupSummary)
@limiter.limit("3/minute")
def lookup_open_news_leads(
    request: Request,
    response: Response,
    article_id: int,
    retrieve_articles: bool = Query(default=False),
    db: Session = Depends(get_db),
    _staff: object = Depends(deps.get_current_active_admin),
) -> OpenSearchLookupSummary:
    """Search public GDELT article links for a blocked publisher page."""
    article = db.get(NewsArticle, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="News article not found")
    if article.article_text is not None and not article.article_error:
        raise HTTPException(status_code=409, detail="Full article text is already available")
    source = next((item for item in load_news_sources() if item.id == article.publisher_source_id
                   and item.enabled and item.verified_at is not None), None)
    if (source is None or canonical_article_url(article.canonical_url, source) is None or
            not any(entry.source_id == source.id and entry.feed_url in source.feed_urls
                    for entry in article.feed_entries)):
        raise HTTPException(status_code=409, detail="Open lookup requires a verified publisher feed candidate")
    from app.services.news_telemetry_service import begin_fallback, finish_fallback
    captured_input = FallbackInput.capture(article)
    lookup_id = None
    try:
        lookup_id = begin_fallback(db, article, _staff.id, retrieve_articles)
        result = lookup_news_leads(captured_input, retrieve_articles)
        finish_fallback(db, lookup_id, result)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="News lookup telemetry storage is unavailable") from exc
    except Exception:
        db.rollback()
        try:
            if lookup_id is not None:
                finish_fallback(db, lookup_id)
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(status_code=503, detail="News lookup telemetry storage is unavailable") from exc
        raise HTTPException(status_code=502, detail="News lookup failed")
    if result.retry_after_seconds is not None:
        response.headers["Retry-After"] = str(result.retry_after_seconds)
    return OpenSearchLookupSummary.model_validate(asdict(result))




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
            result = discover_news(active, client, db, actor_id=_staff.id)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="News discovery storage is unavailable") from exc
    return NewsDiscoveryRunSummary(
        probes=[NewsFeedProbeResult.model_validate(asdict(probe)) for probe in result.probes],
        new_or_updated_candidates=len(result.candidates),
        notices=[asdict(notice) for notice in result.notices],
    )


@router.get("/sources", response_model=list[NewsSourceSummary])
def list_news_sources(_staff: object = Depends(deps.get_current_active_admin)) -> list[NewsSourceSummary]:
    """Show configured runtime sources without changing moderation state."""
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
    from app.crud.news_processing import enqueue_article
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
        try:
            enqueue_article(db, article)
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(status_code=503, detail="News candidate storage is unavailable") from exc
        changed = article.title != payload.title[:500] or article.article_text != payload.text[:30_000]
        article.title = payload.title[:500]
        article.excerpt = payload.text[:500]
        article.article_text = payload.text[:30_000]
        article.last_seen_at = now
        article.content_fingerprint = fingerprint
        if changed:
            article.published_at = now
        article.fetched_at = now
        article.article_error = None

    try:
        db.flush()
        enqueue_article(db, article)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="News candidate storage is unavailable") from exc
    refreshed = db.scalar(
        select(NewsArticle)
        .options(selectinload(NewsArticle.feed_entries))
        .where(NewsArticle.id == article.id)
    )
    return NewsArticleSummary.model_validate(refreshed)
