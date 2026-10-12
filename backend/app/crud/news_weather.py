"""Read/write the controller's own JSON record and bounded pipeline predicates."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.orm import Session
from app.models.setting import SystemSetting
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimEvaluation, NewsClaimSource
from app.models.news_telemetry import NewsDiscoveryRun
from app.models.report import FloodAvoidanceZone, FloodEvent
from app.schemas.configuration import OperationalSettings
from app.schemas.news_weather import NewsWeatherController

CONTROLLER_KEY = "news_weather_controller_v1"


def read_controller(db: Session) -> NewsWeatherController:
    row = db.get(SystemSetting, CONTROLLER_KEY, populate_existing=True)
    return NewsWeatherController.model_validate(row.value) if row else NewsWeatherController()


def save_controller(db: Session, state: NewsWeatherController) -> None:
    row = db.get(SystemSetting, CONTROLLER_KEY)
    if row is None:
        row = SystemSetting(key=CONTROLLER_KEY)
        db.add(row)
    row.value = state.model_dump(mode="json")
    db.commit()


def latest_collection_at(db: Session) -> datetime | None:
    value = db.scalar(select(NewsDiscoveryRun.started_at).where(NewsDiscoveryRun.trigger == "collector")
                      .order_by(NewsDiscoveryRun.started_at.desc()).limit(1))
    return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


def current_flood_until(db: Session, now: datetime) -> datetime | None:
    """Original clocks/deadlines apply even when display expiry is paused."""
    cutoff = now-timedelta(hours=2)
    news_deadline = db.scalar(select(func.max(func.least(NewsClaimDecision.observed_at+timedelta(hours=2), NewsClaimDecision.expires_at)))
        .join(NewsClaimCase, and_(NewsClaimCase.id == NewsClaimDecision.case_id,
                                NewsClaimCase.revision == NewsClaimDecision.revision))
        .where(NewsClaimDecision.public_state.in_(("active_alert", "active_zone")),
               NewsClaimDecision.observed_at > cutoff, NewsClaimDecision.observed_at <= now,
               NewsClaimDecision.expires_at > now))
    # Citizen/staff zones use their permanent incident's original observation
    # clock, not zone edits, refreshes, or late historical activation timestamps.
    wet_clock = func.coalesce(FloodEvent.first_reported_at, FloodEvent.verified_at)
    zone_deadline = db.scalar(select(func.max(func.least(wet_clock+timedelta(hours=2),
        func.coalesce(FloodAvoidanceZone.expires_at, wet_clock+timedelta(hours=2))))).select_from(FloodAvoidanceZone)
        .join(FloodEvent, FloodEvent.id == FloodAvoidanceZone.event_id)
        .where(FloodAvoidanceZone.is_active.is_(True), FloodEvent.status == "active",
               wet_clock > cutoff, wet_clock <= now,
               or_(FloodAvoidanceZone.expires_at.is_(None), FloodAvoidanceZone.expires_at > now)))
    deadlines = [value for value in (news_deadline, zone_deadline) if value]
    return max(deadlines) if deadlines else None


def pending_pipeline_work(db: Session, now: datetime, config: OperationalSettings, source_ids: tuple[str, ...],
                          *, policy_fingerprint: str, admission_age: timedelta) -> bool:
    def due(model: type) -> object:
        return or_(model.status == "pending", and_(model.status == "retry_wait", model.next_attempt_at <= now),
                   and_(model.status == "processing", model.lease_expires_at <= now))

    if config.news_processing_enabled and source_ids:
        from app.crud.news_processing import current_pipeline_version
        from app.services.news_discovery_service import MAX_ARTICLE_CHARS
        captured = exists(select(NewsExtractionRun.id).join(NewsArticleVersion).where(
            NewsArticleVersion.article_id == NewsArticle.id, NewsExtractionRun.pipeline_version == current_pipeline_version()))
        if db.scalar(select(NewsArticle.id).where(NewsArticle.publisher_source_id.in_(source_ids),
            NewsArticle.review_state == "pending", NewsArticle.article_error.is_(None),
            func.length(func.trim(NewsArticle.article_text)) > 0, func.length(NewsArticle.article_text) <= MAX_ARTICLE_CHARS,
            ~captured).limit(1)) is not None:
            return True
        runs = select(NewsExtractionRun.id).join(NewsArticleVersion).join(NewsArticle).where(
            NewsArticle.publisher_source_id.in_(source_ids), NewsExtractionRun.pipeline_version == current_pipeline_version(),
            due(NewsExtractionRun)).limit(1)
        if db.scalar(runs) is not None:
            return True
        bound = exists(select(NewsClaimEvaluation.id).join(NewsClaimSource).where(
            NewsClaimSource.extraction_run_id == NewsExtractionRun.id, NewsClaimEvaluation.policy_fingerprint == policy_fingerprint))
        # Only a completed result with claims needs binding; empty extractions
        # must not cause a permanently hot worker.
        unbound = select(NewsExtractionRun.id).join(NewsArticleVersion).join(NewsArticle).where(
            NewsArticle.publisher_source_id.in_(source_ids), NewsExtractionRun.status == "completed",
            NewsExtractionRun.pipeline_version == current_pipeline_version(), ~bound,
            NewsArticle.published_at >= now-admission_age, NewsArticle.published_at <= now,
            case((func.jsonb_typeof(NewsExtractionRun.result["claims"]) == "array",
                  func.jsonb_array_length(NewsExtractionRun.result["claims"])), else_=0) > 0).limit(1)
        if db.scalar(unbound) is not None:
            return True
        evaluations = select(NewsClaimEvaluation.id).join(NewsClaimSource).join(NewsExtractionRun).join(NewsArticleVersion).join(NewsArticle).where(
            NewsArticle.publisher_source_id.in_(source_ids), NewsClaimEvaluation.policy_fingerprint == policy_fingerprint,
            due(NewsClaimEvaluation)).limit(1)
        from app.services.news_audit_quota_service import read_quota, deadline, real_now, quota_identity
        from app.services.news_claim_auditor import NewsClaimAuditor
        auditor = NewsClaimAuditor()
        quota = read_quota(db, identity=quota_identity(auditor))
        blocked_until = deadline(quota.blocked_until)
        if blocked_until and blocked_until > real_now():
            # New/unclassified claims still run local gates once. Deferred rows
            # only wake maintenance early when their evidence deadline is due.
            evaluations = evaluations.where(or_(NewsClaimEvaluation.error_code.is_(None),
                NewsClaimEvaluation.error_code.not_in(("auditor_daily_quota_exhausted", "auditor_rate_limited", "auditor_quota_unavailable", "auditor_quota_unknown"))))
        from app.services.news_audit_availability_service import read_availability
        model_until = deadline(read_availability(db, auditor).blocked_until)
        if model_until and model_until > real_now():
            evaluations = evaluations.where(or_(NewsClaimEvaluation.error_code.is_(None),
                NewsClaimEvaluation.error_code != "auditor_model_cooldown"))
        if db.scalar(evaluations) is not None:
            return True
    if source_ids:
        # A completed audit that has no decision is actionable even if the
        # collector is paused. Later decisions retain immutable evaluation IDs.
        decided = exists(select(NewsClaimDecision.id).where(NewsClaimDecision.evaluation_id == NewsClaimEvaluation.id))
        clearance = NewsClaimEvaluation.result["audit"]["evidence"]["status"]["classification"].astext == "subsided"
        query = select(NewsClaimEvaluation.id).join(NewsClaimSource).join(NewsExtractionRun).join(NewsArticleVersion).join(NewsArticle).where(
            NewsArticle.publisher_source_id.in_(source_ids), NewsClaimEvaluation.status == "completed", ~decided,
            or_(NewsClaimEvaluation.policy_fingerprint == policy_fingerprint, clearance)).limit(1)
        if not config.news_publication_enabled:
            query = query.where(clearance)
        if db.scalar(query) is not None:
            return True
    if config.news_publication_enabled:
        # Recover an interrupted publication→plot handoff. Failed estimates
        # save their review revision, so unresolved cases do not keep launching.
        pending_placement = select(NewsClaimDecision.id).join(NewsClaimCase, and_(
            NewsClaimCase.id == NewsClaimDecision.case_id, NewsClaimCase.revision == NewsClaimDecision.revision)).where(
            NewsClaimDecision.public_state == "active_alert", NewsClaimDecision.actor_kind == "automatic",
            NewsClaimDecision.operation == "evaluate", NewsClaimDecision.expires_at > now,
            NewsClaimDecision.snapshot["policy_fingerprint"].astext == policy_fingerprint,
            NewsClaimDecision.snapshot["estimated_road_review_revision"].astext.is_(None)).limit(1)
        if db.scalar(pending_placement) is not None:
            return True
    if config.automatic_expiry_enabled:
        return db.scalar(select(NewsClaimDecision.id).join(NewsClaimCase, and_(
            NewsClaimCase.id == NewsClaimDecision.case_id, NewsClaimCase.revision == NewsClaimDecision.revision))
            .where(NewsClaimDecision.public_state.in_(("active_alert", "active_zone")),
                   NewsClaimDecision.expires_at <= now).limit(1)) is not None
    return False
