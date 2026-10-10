"""Independent, durable claim auditing after extraction; no public/domain writes."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json

import httpx
from pydantic import ValidationError
from sqlalchemy import case, exists, func, select
from sqlalchemy.orm import Session

from app.crud.news_evaluation import (
    bind_completed_run, canonical_sha256, claim_due_evaluation, finish_owned_evaluation,
    require_utc, validate_run,
)
from app.crud.news_processing import current_pipeline_version, utc_now
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimEvaluation, NewsClaimSource
from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput, NewsExtractionResult
from app.services.news_claim_auditor import NewsClaimAuditor, canonical_claim_sha256
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


async def evaluate_news_claims(session_factory: Callable[[], Session], *, limit: int = 50,
                               run_id: int | None = None, auditor: NewsClaimAuditor | None = None,
                               policy: EvaluationPolicy | None = None,
                               client: httpx.AsyncClient | None = None, obey_configuration: bool = False,
                               sources: tuple[NewsSource, ...] | None = None,
                               clock: Callable[[], datetime] = utc_now) -> EvaluationSummary:
    if not 1 <= limit <= 200:
        raise ValueError("Evaluation limit must be between 1 and 200")
    auditor = auditor if auditor is not None else NewsClaimAuditor()
    policy = policy if policy is not None else evaluation_policy(auditor)
    sources = sources if sources is not None else load_news_sources()
    summary = EvaluationSummary()
    visited: list[int] = []
    for _ in range(limit):
        with session_factory() as db, db.begin():
            if obey_configuration:
                from app.services.configuration_service import read_configuration, selected_news_sources
                if not read_configuration(db).news_processing_enabled:
                    break
                sources = selected_news_sources(db, sources)
                if not sources:
                    break
            parameters = {"run_id": run_id, "exclude_evaluation_ids": tuple(visited)}
            if obey_configuration:
                parameters["source_ids"] = tuple(source.id for source in sources)
            owned = claim_due_evaluation(db, require_utc(clock()), policy_fingerprint=policy.fingerprint, **parameters)
        if owned is None:
            break
        visited.append(owned.evaluation_id)
        if owned.exhausted:
            summary.failed += 1
            summary.evaluations.append({"evaluation_id": owned.evaluation_id, "status": "failed",
                                        "error_code": "lease_expired_exhausted"})
            continue
        error_code, retryable, result = None, False, None
        try:
            article = NewsArticleExtractorInput.model_validate(owned.input_snapshot)
            extraction = NewsExtractionResult.model_validate(owned.extraction_result)
            claim = extraction.claims[owned.claim_ordinal]
            if (extraction_input_snapshot(article)[1] != owned.input_fingerprint
                    or canonical_claim_sha256(claim) != owned.claim_sha256):
                error_code = "immutable_evidence_mismatch"
            elif not source_is_approved(article, sources) or not publication_is_current(article, require_utc(clock()), policy):
                error_code = "source_admission_changed"
            elif auditor.policy_identity() != policy.auditor_identity or current_pipeline_version() != policy.pipeline_version:
                error_code = "evaluation_policy_changed"
            else:
                reason = preliminary_reason(claim, require_utc(clock()), policy)
                audit = None
                if reason is None:
                    # The claim transaction has committed; no DB lock/connection is held here.
                    audited = await auditor.audit(claim, article, client=client)
                    if (audited.input_sha256 != owned.input_fingerprint
                            or audited.claim_sha256 != owned.claim_sha256):
                        error_code = "audit_evidence_mismatch"
                    elif audited.outcome in ("unavailable", "invalid"):
                        error_code, retryable = audited.reason_code, audited.retryable
                    else:
                        audit = audited.model_dump(mode="json")
                        reason = audited.reason_code
                if error_code is None:
                    result = {"schema_version": EVALUATION_POLICY_VERSION,
                              "policy_fingerprint": owned.policy_fingerprint,
                              "policy_identity": policy.auditor_identity,
                              "publication_admission_at": policy.publication_admission_at.isoformat() if policy.publication_admission_at else None,
                              "input_sha256": owned.input_fingerprint, "claim_sha256": owned.claim_sha256,
                              "reason_code": reason, "audit": audit,
                              "publication_permitted": False, "may_affect_routing": False}
        except (ValidationError, ValueError, IndexError, TypeError, KeyError):
            error_code = "invalid_evaluation_evidence"
        except Exception:
            # Provider exceptions never expose credentials/body or undo extraction.
            error_code, retryable = "auditor_exception", True
        now = require_utc(clock())
        if result is not None and (auditor.policy_identity() != policy.auditor_identity
                                  or current_pipeline_version() != policy.pipeline_version):
            result, error_code = None, "evaluation_policy_changed"
        if result is not None:
            # Preserve a confirmation while recording freshness lost during an audit.
            result["freshness_reason_at_completion"] = (
                "publication_outside_admission_window" if not publication_is_current(article, now, policy)
                else preliminary_reason(claim, now, policy))
            if len(json.dumps(result, ensure_ascii=False, allow_nan=False).encode()) > 65536:
                result, error_code, retryable = None, "evaluation_result_oversized", False
        with session_factory() as db, db.begin():
            saved = finish_owned_evaluation(db, owned, now, result=result, error_code=error_code, retryable=retryable)
        status = ("lease_lost" if not saved else "retry_wait" if error_code and retryable and owned.attempt_count < 5
                  else "failed" if error_code else "completed")
        setattr(summary, status, getattr(summary, status) + 1)
        summary.evaluations.append({"evaluation_id": owned.evaluation_id, "case_id": owned.case_id,
                                    "status": status, "error_code": error_code})
    return summary
