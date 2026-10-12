"""Independent, durable claim auditing after extraction; no public/domain writes."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
import time
from math import ceil

import httpx
from pydantic import ValidationError
from sqlalchemy import case, exists, func, select
from sqlalchemy.orm import Session

from app.crud.news_evaluation import (
    bind_completed_run, canonical_sha256, finish_owned_evaluation, claim_due_batch, start_owned_attempt,
    require_utc, validate_run,
)
from app.crud.news_processing import current_pipeline_version, utc_now
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimEvaluation, NewsClaimSource
from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput, NewsExtractionResult
from app.services.news_claim_auditor import NewsClaimAuditor, canonical_claim_sha256, MAX_BATCH_CLAIMS
from app.schemas.news_audit import IndependentAuditResult
from app.schemas.news_audit_batch import AuditCandidate
from app.services.news_audit_quota_service import (audit_dispatch_lock, check_quota, dispatched, record_error,
    deadline, real_now, save_quota)
from app.services.news_audit_availability_service import read_availability, record_availability, ModelAvailability
from app.services.news_discovery_service import extraction_input_snapshot
from app.services.news_evidence_policy import has_flood_observation, metro_manila_claim
from app.services.news_feed_service import canonical_article_url
from app.services.news_sources import NewsSource, load_news_sources

EVALUATION_POLICY_VERSION = "independent-claim-evaluation-v1"
OPERATIONAL_ZONE_POLICY_VERSION = "audited-flood-depth-access-reprocessing-v3"
ADMISSION_AGE = timedelta(hours=12)
OBSERVATION_FALLBACK = timedelta(hours=2)


@dataclass(frozen=True)
class EvaluationPolicy:
    fingerprint: str
    pipeline_version: str
    auditor_identity: dict
    expiry_minutes: dict[str, int] | None = None
    retention_hours: int | None = None
    publication_admission_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.publication_admission_at is None:
            return
        require_utc(self.publication_admission_at)
        from app.services.local_news_scenario_service import admits_connected_reconstruction
        if admits_connected_reconstruction(self.publication_admission_at):
            return
        # Later-published evidence may be used to reconstruct an earlier
        # observation only in the dedicated private replay database.
        from app.core.config import settings
        from app.core.database import engine
        from sqlalchemy.engine import make_url
        configured = make_url(settings.DATABASE_URL)
        if (configured != engine.url or configured.get_backend_name() != "postgresql"
            or configured.host not in {"localhost", "127.0.0.1", "::1"}
            or configured.database != "lanes_news_test"
            or any(key in configured.query for key in {"host", "hostaddr", "service", "dbname", "database", "port"})):
            raise ValueError("Historical reconstruction requires the dedicated loopback replay database")


def evaluation_policy(auditor: NewsClaimAuditor, configuration=None, *,
                      publication_admission_at: datetime | None = None) -> EvaluationPolicy:
    identity = auditor.policy_identity()
    pipeline = current_pipeline_version()
    configuration_identity = ({"expiry_minutes": configuration.evidence_expiry_minutes, "retention_hours": configuration.news_unconfirmed_retention_hours} if configuration is not None else {})
    fingerprint = canonical_sha256({"version": EVALUATION_POLICY_VERSION, "pipeline_version": pipeline,
                                    "operational_zone_policy": OPERATIONAL_ZONE_POLICY_VERSION,
                                    "auditor": identity, "admission_seconds": 43200,
                                    "observation_fallback_seconds": 7200,
                                    "publication_admission_at": publication_admission_at.isoformat() if publication_admission_at else None,
                                    **configuration_identity})
    return EvaluationPolicy(fingerprint, pipeline, identity, configuration.evidence_expiry_minutes if configuration is not None else None, configuration.news_unconfirmed_retention_hours if configuration is not None else None, publication_admission_at)


def source_is_approved(article: NewsArticleExtractorInput, sources: tuple[NewsSource, ...]) -> bool:
    return any(source.id == article.publisher and source.enabled and source.verified_at is not None
               and canonical_article_url(article.canonical_url, source) is not None for source in sources)


def publication_is_current(article: NewsArticleExtractorInput, now: datetime,
                           policy: EvaluationPolicy | None = None) -> bool:
    from app.services.local_news_scenario_service import admitted_source_matches
    if not admitted_source_matches(article.canonical_url):
        return False
    published = article.published_at
    admission_at = policy.publication_admission_at if policy and policy.publication_admission_at else now
    return bool(published is not None and published.tzinfo is not None
                and timedelta(0) <= admission_at - published <= ADMISSION_AGE)


def preliminary_reason(claim: ExtractedClaim, now: datetime, policy: EvaluationPolicy | None = None) -> str | None:
    """Local evidence gates reduce needless external calls; never confirm a claim."""
    if not metro_manila_claim(claim):
        return "unsupported_locality"
    if claim.is_negated:
        return "negated_claim"
    if claim.is_forecast:
        return "forecast_claim"
    if claim.is_historical:
        return "historical_claim"
    if any(reason in claim.uncertainty_reasons for reason in
           ("photo_caption_only", "metadata_only_lead", "contradictory_update", "location_context_only",
            "city_context_ambiguous")):
        return "unsupported_claim_context"
    if not claim.flood_mentioned or not has_flood_observation(claim.evidence_sentence):
        return "not_observed_flood_evidence"
    if claim.condition not in ("active", "rising", "receding", "subsided"):
        return "unclear_flood_status"
    observed = claim.event_time_resolved
    if claim.event_time_kind != "observation" or observed is None or observed.tzinfo is None:
        return "missing_supported_observation_time"
    if not timedelta(0) <= now - observed <= ADMISSION_AGE:
        return "observation_outside_admission_window"
    if claim.condition in ("active", "rising", "receding") and now >= observed + timedelta(minutes=(policy.expiry_minutes.get(claim.depth_canonical or "unknown", 120) if policy and policy.expiry_minutes else 120)):
        return "observation_evidence_expired"
    return None


@dataclass
class EvaluationSummary:
    sources_created: int = 0
    evaluations_created: int = 0
    completed: int = 0
    retry_wait: int = 0
    failed: int = 0
    lease_lost: int = 0
    next_after_run_id: int = 0
    request_count: int = 0
    claims_dispatched: int = 0
    quota_deferred: int = 0
    availability_deferred: int = 0
    budget_deferred: int = 0
    error_code: str | None = None
    skipped: list[dict] = field(default_factory=list)
    evaluations: list[dict] = field(default_factory=list)


def seed_claim_evaluations(session_factory: Callable[[], Session], policy: EvaluationPolicy, *,
                           now: datetime, limit: int = 50, after_run_id: int = 0,
                           run_id: int | None = None,
                           sources: tuple[NewsSource, ...] | None = None,
                           unbound_only: bool = False, obey_configuration: bool = False) -> EvaluationSummary:
    """Bounded explicit handoff after extraction commits, with a resumable cursor."""
    now = require_utc(now)
    if not 1 <= limit <= 200 or after_run_id < 0 or (run_id is not None and run_id <= 0):
        raise ValueError("Invalid evaluation seed batch")
    sources = sources if sources is not None else load_news_sources()
    summary = EvaluationSummary(next_after_run_id=after_run_id)
    with session_factory() as db:
        query = select(NewsExtractionRun.id).where(NewsExtractionRun.status == "completed")
        if unbound_only:
            # Scheduled jobs start without a saved cursor. Ignore runs already
            # handed off for this policy and empty/old extraction rather than
            # letting them monopolize every recurring batch. These predicates
            # only shortlist: immutable input and freshness are checked below.
            claims = NewsExtractionRun.result["claims"]
            nonempty_claims = case((func.jsonb_typeof(claims) == "array", func.jsonb_array_length(claims)), else_=0) > 0
            evaluated = exists(select(NewsClaimEvaluation.id).join(NewsClaimSource,
                NewsClaimSource.id == NewsClaimEvaluation.claim_source_id).where(
                NewsClaimSource.extraction_run_id == NewsExtractionRun.id,
                NewsClaimEvaluation.policy_fingerprint == policy.fingerprint))
            query = query.join(NewsArticleVersion, NewsArticleVersion.id == NewsExtractionRun.article_version_id).join(
                NewsArticle, NewsArticle.id == NewsArticleVersion.article_id).where(
                NewsExtractionRun.pipeline_version == policy.pipeline_version, nonempty_claims, ~evaluated,
                NewsArticle.published_at >= (policy.publication_admission_at or now) - ADMISSION_AGE,
                NewsArticle.published_at <= (policy.publication_admission_at or now))
        if run_id is not None:
            query = query.where(NewsExtractionRun.id == run_id)
        else:
            query = query.where(NewsExtractionRun.id > after_run_id)
        ids = list(db.scalars(query.order_by(NewsExtractionRun.id).limit(limit)))
    for selected_id in ids:
        summary.next_after_run_id = selected_id
        # One run per transaction; a bad run never rolls back other runs' work.
        with session_factory() as db, db.begin():
            if obey_configuration:
                from app.services.configuration_service import read_configuration, selected_news_sources
                if not read_configuration(db).news_processing_enabled:
                    break
                sources = selected_news_sources(db, sources)
            run = db.get(NewsExtractionRun, selected_id)
            version = db.get(NewsArticleVersion, run.article_version_id)
            try:
                article, _ = validate_run(run, version)
            except (ValueError, ValidationError, TypeError, KeyError):
                summary.skipped.append({"run_id": selected_id, "reason_code": "invalid_immutable_extraction"})
                continue
            reason = ("stale_extraction_policy" if run.pipeline_version != policy.pipeline_version else
                      "unapproved_article_source" if not source_is_approved(article, sources) else
                      "publication_outside_admission_window" if not publication_is_current(article, now, policy) else None)
            if reason:
                summary.skipped.append({"run_id": selected_id, "reason_code": reason})
                continue
            created, queued = bind_completed_run(db, selected_id, policy.fingerprint, now)
            summary.sources_created += created
            summary.evaluations_created += queued
    if unbound_only and len(ids) < limit:
        summary.next_after_run_id = 0
    return summary


def _prepare(owned, auditor, policy, sources, now):
    article = NewsArticleExtractorInput.model_validate(owned.input_snapshot)
    extraction = NewsExtractionResult.model_validate(owned.extraction_result)
    claim = extraction.claims[owned.claim_ordinal]
    error = ("immutable_evidence_mismatch" if extraction_input_snapshot(article)[1] != owned.input_fingerprint
             or canonical_claim_sha256(claim) != owned.claim_sha256 else
             "source_admission_changed" if not source_is_approved(article, sources) or not publication_is_current(article, now, policy) else
             "evaluation_policy_changed" if auditor.policy_identity() != policy.auditor_identity
             or current_pipeline_version() != policy.pipeline_version else None)
    return article, claim, error, preliminary_reason(claim, now, policy) if error is None else None


def _completed_result(owned, policy, reason, audit, claim, article, now):
    return {"schema_version": EVALUATION_POLICY_VERSION, "policy_fingerprint": owned.policy_fingerprint,
        "policy_identity": policy.auditor_identity,
        "publication_admission_at": policy.publication_admission_at.isoformat() if policy.publication_admission_at else None,
        "input_sha256": owned.input_fingerprint, "claim_sha256": owned.claim_sha256, "reason_code": reason,
        "audit": audit.model_dump(mode="json") if audit else None,
        "freshness_reason_at_completion": "publication_outside_admission_window" if not publication_is_current(article, now, policy)
            else preliminary_reason(claim, now, policy), "publication_permitted": False, "may_affect_routing": False}


async def evaluate_news_claims(session_factory: Callable[[], Session], *, limit: int = 50,
                               run_id: int | None = None, auditor: NewsClaimAuditor | None = None,
                               policy: EvaluationPolicy | None = None,
                               client: httpx.AsyncClient | None = None, obey_configuration: bool = False,
                               sources: tuple[NewsSource, ...] | None = None,
                               clock: Callable[[], datetime] = utc_now,
                               on_progress: Callable[[dict], None] | None = None) -> EvaluationSummary:
    if not 1 <= limit <= 200:
        raise ValueError("Evaluation limit must be between 1 and 200")
    auditor = auditor if auditor is not None else NewsClaimAuditor()
    if client is None:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60, connect=5, write=10, pool=5),
                                     follow_redirects=False) as scoped_client:
            return await evaluate_news_claims(session_factory, limit=limit, run_id=run_id, auditor=auditor,
                policy=policy, client=scoped_client, obey_configuration=obey_configuration,
                sources=sources, clock=clock, on_progress=on_progress)
    policy = policy if policy is not None else evaluation_policy(auditor)
    sources = sources if sources is not None else load_news_sources()
    summary = EvaluationSummary()
    visited: list[int] = []
    quota = None
    stop_dispatch = False
    cycle_started = time.monotonic()

    def eligible_for_dispatch(owned):
        if owned.exhausted:
            return False
        try:
            _, _, error, reason = _prepare(owned, auditor, policy, sources, require_utc(clock()))
            return error is None and reason is None
        except (ValidationError, ValueError, IndexError, TypeError, KeyError):
            return False

    def save(owned, article=None, claim=None, *, reason=None, audit=None, error=None, retryable=False, retry_at=None):
        now = require_utc(clock())
        result = None
        diagnostic = None
        if audit and (audit.input_sha256 != owned.input_fingerprint or audit.claim_sha256 != owned.claim_sha256):
            error, retryable = "audit_evidence_mismatch", False
        if audit and not error and audit.outcome in ("unavailable", "invalid"):
            error, retryable = audit.reason_code, audit.retryable
        if auditor.policy_identity() != policy.auditor_identity or current_pipeline_version() != policy.pipeline_version:
            error, retryable = "evaluation_policy_changed", False
        if error and audit:
            diagnostic = {key: value for key, value in audit.model_dump(mode="json").items()
                if key in {"provider_http_status", "provider_request_id", "retry_after_seconds", "reason_code", "transport"} and value is not None}
        if error is None:
            result = _completed_result(owned, policy, audit.reason_code if audit else reason, audit, claim, article, now)
            if len(json.dumps(result, ensure_ascii=False, allow_nan=False).encode()) > 65536:
                result, error, retryable = None, "evaluation_result_oversized", False
        with session_factory() as db, db.begin():
            saved = finish_owned_evaluation(db, owned, now, result=result, error_code=error, retryable=retryable,
                                           retry_at=retry_at, diagnostic=diagnostic)
        status = "lease_lost" if not saved else "retry_wait" if error and retryable and owned.attempt_count < 5 else "failed" if error else "completed"
        setattr(summary, status, getattr(summary, status) + 1)
        summary.evaluations.append({"evaluation_id": owned.evaluation_id, "case_id": owned.case_id,
                                   "status": status, "error_code": error})

    with audit_dispatch_lock(session_factory) as acquired:
        if not acquired:
            summary.error_code = "auditor_already_running"
            return summary
        while len(visited) < limit:
            with session_factory() as db, db.begin():
                if obey_configuration:
                    from app.services.configuration_service import read_configuration, selected_news_sources
                    if not read_configuration(db).news_processing_enabled:
                        break
                    sources = selected_news_sources(db, sources)
                    if not sources:
                        break
                owned_batch = claim_due_batch(db, require_utc(clock()), policy_fingerprint=policy.fingerprint,
                    limit=getattr(getattr(auditor, "config", None), "batch_size", MAX_BATCH_CLAIMS),
                    max_rows=limit-len(visited), eligibility_test=eligible_for_dispatch,
                    run_id=run_id, exclude_evaluation_ids=tuple(visited),
                    source_ids=tuple(s.id for s in sources) if obey_configuration else None)
            if not owned_batch:
                break
            eligible = []
            for owned in owned_batch:
                visited.append(owned.evaluation_id)
                if owned.exhausted:
                    summary.failed += 1
                    summary.evaluations.append({"evaluation_id": owned.evaluation_id, "status": "failed", "error_code": "lease_expired_exhausted"})
                    continue
                try:
                    article, claim, error, reason = _prepare(owned, auditor, policy, sources, require_utc(clock()))
                    if error or reason:
                        save(owned, article, claim, error=error, reason=reason)
                    else:
                        eligible.append((owned, article, claim))
                except (ValidationError, ValueError, IndexError, TypeError, KeyError):
                    save(owned, error="invalid_evaluation_evidence")
            if not eligible:
                continue
            if getattr(auditor, "config", None) and auditor.config.error_code():
                for owned, article, claim in eligible:
                    save(owned, article, claim, error=auditor.config.error_code())
                continue
            # Validate/size-bound groups before counting any provider attempt.
            groups = [eligible]
            while groups:
                group = groups.pop(0)
                candidates = tuple(AuditCandidate(candidate_id=str(o.evaluation_id), claim=c) for o, a, c in group)
                try:
                    auditor.batch_document(candidates, group[0][1])
                except ValueError as exc:
                    if str(exc) == "audit_input_oversized" and len(group) > 1:
                        middle = len(group)//2
                        groups[0:0] = [group[:middle], group[middle:]]
                        continue
                    for owned, article, claim in group:
                        save(owned, article, claim, reason=str(exc))
                    continue
                if getattr(auditor, "config", None) and auditor.config.provider == "openrouter" and not auditor.config.error_code():
                    quota = await check_quota(session_factory, auditor, client=client)
                    from app.services.news_audit_quota_service import free_router
                    if quota.remaining == 0 and free_router(auditor) and not deadline(quota.blocked_until):
                        quota.blocked_until = (real_now()+timedelta(minutes=30)).isoformat()
                        quota.error_code = "auditor_daily_quota_exhausted"
                        save_quota(session_factory, quota)
                blocked = deadline(quota.blocked_until) if quota else None
                with session_factory() as db:
                    availability = read_availability(db, auditor) if getattr(auditor, "config", None) else ModelAvailability()
                model_blocked = deadline(availability.blocked_until)
                budget_spent = (summary.request_count >= 6 or
                    time.monotonic() - cycle_started + getattr(auditor, "timeout_seconds", 60) + 5 > 360)
                quota_blocked = stop_dispatch or bool(blocked and blocked > real_now())
                unavailable = bool(model_blocked and model_blocked > real_now())
                if quota_blocked or unavailable or budget_spent:
                    until = blocked if quota_blocked else model_blocked if unavailable else None
                    delay = max(1, ceil((until-real_now()).total_seconds())) if until else 60 if budget_spent else 900
                    for owned, article, claim in group:
                        observation_deadline = claim.event_time_resolved + (timedelta(minutes=(policy.expiry_minutes or {}).get(claim.depth_canonical or "unknown", 120))
                            if claim.condition != "subsided" else ADMISSION_AGE)
                        quota_retry_at = require_utc(clock())+timedelta(seconds=delay)
                        retry_at = min(quota_retry_at, observation_deadline)
                        error = ("auditor_quota_evidence_due" if observation_deadline <= quota_retry_at else
                            (quota.error_code if quota and quota.error_code else "auditor_rate_limited") if quota_blocked else
                            "auditor_model_cooldown" if unavailable else "auditor_cycle_deferred")
                        save(owned, article, claim, error=error,
                             retryable=True, retry_at=retry_at)
                        if quota_blocked:
                            summary.quota_deferred += 1
                        elif unavailable:
                            summary.availability_deferred += 1
                        else:
                            summary.budget_deferred += 1
                    continue
                ready = []
                # Recheck current toggles/source policy and freshness after quota IO.
                with session_factory() as db:
                    if obey_configuration:
                        from app.services.configuration_service import read_configuration, selected_news_sources
                        allowed = read_configuration(db).news_processing_enabled
                        sources = selected_news_sources(db, sources) if allowed else ()
                for owned, article, claim in group:
                    _, _, error, reason = _prepare(owned, auditor, policy, sources, require_utc(clock()))
                    if error or reason:
                        save(owned, article, claim, error=error, reason=reason)
                        continue
                    with session_factory() as db, db.begin():
                        started = start_owned_attempt(db, owned, require_utc(clock()))
                    if started is None:
                        summary.lease_lost += 1
                    else:
                        ready.append((started, article, claim))
                if not ready:
                    continue
                candidates = tuple(AuditCandidate(candidate_id=str(o.evaluation_id), claim=c) for o, a, c in ready)
                summary.request_count += 1
                summary.claims_dispatched += len(ready)
                if quota:
                    dispatched(session_factory, quota, len(ready))
                try:
                    results = await auditor.audit_batch(candidates, ready[0][1], client=client)
                except Exception:
                    results = {c.candidate_id: IndependentAuditResult(outcome="unavailable", reason_code="auditor_exception", retryable=True,
                        prompt_version=policy.auditor_identity.get("prompt_version", "unknown"), response_version=policy.auditor_identity.get("response_version", "unknown"),
                        input_sha256=extraction_input_snapshot(ready[0][1])[1], claim_sha256=canonical_claim_sha256(c.claim)) for c in candidates}
                if quota:
                    representative = next((r for r in results.values() if r.provider_http_status == 429),
                        next((r for r in results.values() if r.outcome in ("invalid", "unavailable")), next(iter(results.values()))))
                    record_error(session_factory, quota, representative)
                representative = next((r for r in results.values() if r.outcome in ("unavailable", "invalid")),
                    next(iter(results.values())))
                if getattr(auditor, "config", None):
                    record_availability(session_factory, auditor, representative)
                for owned, article, claim in ready:
                    audit = results[str(owned.evaluation_id)]
                    if audit.provider_http_status == 429:
                        stop_dispatch = True
                    retry_at = None
                    error = None
                    if audit.retry_after_seconds or audit.provider_http_status == 429:
                        delay = audit.retry_after_seconds or 900
                        observation_deadline = claim.event_time_resolved + (timedelta(minutes=(policy.expiry_minutes or {}).get(claim.depth_canonical or "unknown", 120))
                            if claim.condition != "subsided" else ADMISSION_AGE)
                        provider_retry_at = require_utc(clock())+timedelta(seconds=delay)
                        retry_at = min(provider_retry_at, observation_deadline)
                        if audit.provider_http_status == 429 and observation_deadline < provider_retry_at:
                            error = "auditor_quota_evidence_due"
                    save(owned, article, claim, audit=audit, retry_at=retry_at, error=error,
                         retryable=audit.retryable)
                if on_progress:
                    from dataclasses import asdict
                    on_progress(asdict(summary))
    return summary
