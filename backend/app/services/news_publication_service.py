"""Atomic source-labeled news alerts and evidence lifecycle; no guessed zones.

Each helper participates in its caller's transaction. Independent audit,
immutable input and current policy are rechecked before any public decision.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import re
from uuid import UUID, uuid5, NAMESPACE_URL

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.crud.news_evaluation import canonical_sha256, require_utc, validate_run
from app.crud.news_processing import utc_now
from app.crud.news_publication import (
    NewsPublicationError, append_decision, existing_request, latest_decision,
    lock_case, publication_lock, reserve_decision_id,
)
from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.audit import AuditLog
from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimEvaluation, NewsClaimSource, NewsClaimZoneLink
from app.models.report import FloodAvoidanceZone, FloodEvent, FloodEventStatus, FloodEventTimelineEntry, FloodReport, ReportStatus
from app.schemas.news_audit import IndependentAuditResult
from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from app.schemas.news_publication import NewsDecisionEffect, NewsDecisionSnapshot, NewsStaffDecisionRequest, PublicNewsAlert
from app.services.news_claim_auditor import canonical_claim_sha256, _classify, _validate_evidence
from app.services.news_evaluation_service import EvaluationPolicy, preliminary_reason, publication_is_current, source_is_approved
from app.services.news_sources import NewsSource, load_news_sources


class _PublicationSettings(BaseSettings):
    LANES_NEWS_UNCONFIRMED_RETENTION_HOURS: int = 24
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


def unconfirmed_retention_hours() -> int:
    value = _PublicationSettings().LANES_NEWS_UNCONFIRMED_RETENTION_HOURS
    if not 1 <= value <= 72:
        raise NewsPublicationError("invalid_unconfirmed_retention", 503)
    return value


def _safe(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    return re.sub(r"[\x00-\x1f\x7f]", " ", value).strip()[:limit]


def _incident(claim: ExtractedClaim) -> str:
    # Exact supported section identity; no geometric proximity, road-only
    # matching or sharing across different parent barangays.
    return canonical_sha256({"city": claim.canonical_city, "barangay": claim.canonical_barangay,
        "road": claim.canonical_road, "place": claim.raw_place_name,
        "section": claim.road_segment_raw, "local_area": claim.local_area_raw})


def _supported_section(claim: ExtractedClaim, article: NewsArticleExtractorInput) -> bool:
    body = (article.article_text or "").strip()
    return bool(claim.canonical_road and claim.canonical_city and claim.road_segment_raw
        and claim.road_segment_raw in body and claim.raw_place_name in claim.road_segment_raw
        and (not claim.local_area_raw or claim.local_area_raw in body))


def _clearance_supersedes(db: Session, claim: ExtractedClaim, article: NewsArticleExtractorInput) -> bool:
    """Historical observed clearance survives all later administrative choices."""
    return db.scalar(select(NewsClaimDecision.id).where(NewsClaimDecision.operation == "clear",
        NewsClaimDecision.snapshot["incident_identity"].astext == _incident(claim),
        NewsClaimDecision.snapshot["article_id"].as_integer() == article.article_id,
        NewsClaimDecision.observed_at >= claim.event_time_resolved).limit(1)) is not None


def _wet_supersedes(db: Session, claim: ExtractedClaim, article: NewsArticleExtractorInput) -> bool:
    return db.scalar(select(NewsClaimDecision.id).where(
        NewsClaimDecision.public_state.in_(("active_alert", "active_zone")),
        NewsClaimDecision.snapshot["incident_identity"].astext == _incident(claim),
        NewsClaimDecision.snapshot["article_id"].as_integer() == article.article_id,
        NewsClaimDecision.observed_at > claim.event_time_resolved).limit(1)) is not None


def _correction_checks(db: Session, case_id: int, evaluation_id: int, source: NewsClaimSource,
                       article: NewsArticleExtractorInput, claim: ExtractedClaim) -> None:
    if source.case_id != case_id or claim.condition not in ("active", "rising"):
        raise NewsPublicationError("correction_identity_mismatch")
    if _clearance_supersedes(db, claim, article) or _wet_supersedes(db, claim, article):
        raise NewsPublicationError("source_observation_superseded")
    consumed = db.scalar(select(NewsClaimDecision.id).where(NewsClaimDecision.evaluation_id == evaluation_id,
        NewsClaimDecision.case_id != case_id).limit(1))
    if consumed:
        raise NewsPublicationError("evaluation_already_consumed_by_other_case")
    related = db.scalar(select(NewsClaimDecision.id).join(NewsClaimCase, NewsClaimCase.id == NewsClaimDecision.case_id)
        .where(NewsClaimDecision.revision == NewsClaimCase.revision, NewsClaimDecision.case_id != case_id,
            NewsClaimDecision.snapshot["incident_identity"].astext == _incident(claim),
            NewsClaimDecision.snapshot["article_id"].as_integer() == article.article_id,
            NewsClaimDecision.public_state.in_(("active_alert", "active_zone", "expired", "withdrawn"))).limit(1))
    if related:
        raise NewsPublicationError("source_continuity_requires_review")


def _load(db: Session, evaluation_id: int, policy: EvaluationPolicy, now: datetime,
          sources: tuple[NewsSource, ...]) -> tuple[NewsClaimEvaluation, NewsClaimSource, NewsExtractionRun,
            NewsArticleVersion, NewsArticleExtractorInput, ExtractedClaim, IndependentAuditResult | None, str | None]:
    evaluation = db.get(NewsClaimEvaluation, evaluation_id)
    if evaluation is None:
        raise NewsPublicationError("evaluation_not_found", 404)
    source = db.get(NewsClaimSource, evaluation.claim_source_id)
    run = db.get(NewsExtractionRun, source.extraction_run_id)
    version = db.get(NewsArticleVersion, run.article_version_id)
    try:
        article, extraction = validate_run(run, version)
        claim = extraction.claims[source.claim_ordinal]
    except (ValueError, ValidationError, IndexError, TypeError, KeyError) as exc:
        raise NewsPublicationError("invalid_immutable_evidence") from exc
    if canonical_claim_sha256(claim) != source.claim_sha256:
        raise NewsPublicationError("claim_identity_mismatch")
    reason = None
    audit = None
    if evaluation.policy_fingerprint != policy.fingerprint or run.pipeline_version != policy.pipeline_version:
        reason = "publication_policy_changed"
    elif not source_is_approved(article, sources):
        reason = "unapproved_article_source"
    elif not publication_is_current(article, now):
        reason = "publication_outside_admission_window"
    elif evaluation.status != "completed":
        reason = (evaluation.error_code or "evaluation_failed") if evaluation.status == "failed" else "evaluation_not_completed"
    else:
        result = evaluation.result or {}
        if (result.get("policy_fingerprint") != policy.fingerprint
                or result.get("policy_identity") != policy.auditor_identity
                or result.get("input_sha256") != version.input_fingerprint
                or result.get("claim_sha256") != source.claim_sha256):
            reason = "evaluation_identity_mismatch"
        elif result.get("audit") is None:
            reason = result.get("reason_code") or "independent_audit_unavailable"
        else:
            try:
                audit = IndependentAuditResult.model_validate_json(json.dumps(result["audit"], allow_nan=False))
                if (audit.input_sha256 != version.input_fingerprint or audit.claim_sha256 != source.claim_sha256
                        or audit.provider != policy.auditor_identity.get("provider")
                        or audit.model != policy.auditor_identity.get("model")
                        or audit.prompt_version != policy.auditor_identity.get("prompt_version")
                        or audit.response_version != policy.auditor_identity.get("response_version")):
                    reason = "audit_identity_mismatch"
                elif audit.outcome != "verified" or audit.evidence is None:
                    reason = "independent_audit_not_verified"
                else:
                    reason = _validate_evidence(audit.evidence, claim, article, source.claim_sha256)
                    outcome, classification_reason = _classify(audit.evidence, claim)
                    if not reason and outcome != "verified":
                        reason = classification_reason
            except (ValidationError, ValueError, TypeError, KeyError):
                reason = "invalid_independent_audit"
    if not reason:
        reason = preliminary_reason(claim, now)
    if not reason and (audit is None or audit.evidence is None):
        reason = "independent_audit_unavailable"
    if reason and not re.fullmatch(r"[a-z][a-z0-9_]{0,99}", reason):
        reason = "invalid_evaluation_reason"
    return evaluation, source, run, version, article, claim, audit, reason


def _snapshot(source: NewsClaimSource, version: NewsArticleVersion, claim: ExtractedClaim,
              policy: EvaluationPolicy, digest: str, *, evaluation_id: int | None,
              previous: NewsClaimDecision | None = None, public: PublicNewsAlert | None = None,
              private_reason: str | None = None, target: int | None = None,
              deferred_until: datetime | None = None) -> NewsDecisionSnapshot:
    return NewsDecisionSnapshot(request_sha256=digest, policy_fingerprint=policy.fingerprint,
        claim_source_id=source.id, evaluation_id=evaluation_id, input_sha256=version.input_fingerprint,
        claim_sha256=source.claim_sha256, incident_identity=_incident(claim), article_id=version.article_id,
        public=public, private_reason=private_reason, target_case_id=target,
        previous_decision_id=previous.id if previous else None, deferred_until=deferred_until,
        unconfirmed_retention_hours=unconfirmed_retention_hours())


def _public(case: NewsClaimCase, decision_id: int, article: NewsArticleExtractorInput,
            claim: ExtractedClaim, audit: IndependentAuditResult, now: datetime,
            sources: tuple[NewsSource, ...]) -> PublicNewsAlert:
    publisher = next(source.publisher for source in sources if source.id == article.publisher)
    # Raw source depth and qualifiers only; no borrowing modeled severity.
    depth = _safe(claim.depth_raw, 500) if audit.evidence.depth.confirmed else None
    access = {"passable_all": "Reported passable to all vehicles", "passable_with_caution": "Reported passable with caution",
              "passable_unspecified": "Reported passable; vehicle types unspecified", "light_vehicle_closed": "Reported closed to light vehicles",
              "impassable_all": "Reported impassable to all vehicles", "unknown": "Vehicle passability unknown"}[claim.road_passability]
    if not audit.evidence.access.confirmed:
        access = "Vehicle passability unknown"
    return PublicNewsAlert(case_id=case.id, decision_id=decision_id, revision=case.revision + 1,
        status="Active", location_label=_safe(claim.raw_place_name, 250),
        location_qualifier=_safe(", ".join(value for value in (claim.canonical_barangay, claim.canonical_city, claim.road_segment_raw) if value), 500),
        depth_label=depth, condition_label="Reported rising flood" if claim.condition == "rising" else "Reported active flood",
        passability_label=access, observed_at=claim.event_time_resolved,
        expires_at=claim.event_time_resolved + timedelta(hours=2), updated_at=now,
        source_title=_safe(article.title, 500), source_publisher=_safe(publisher, 160),
        source_url=article.canonical_url, source_published_at=article.published_at,
        evidence_excerpt=_safe(claim.evidence_sentence, 700))


def public_projection(decision: NewsClaimDecision | None, now: datetime, *, include_retained: bool = False) -> PublicNewsAlert | None:
    now = require_utc(now)
    if decision is None or decision.public_state == "unpublished":
        return None
    snapshot = NewsDecisionSnapshot.model_validate(decision.snapshot)
    public = snapshot.public
    if public is None or public.case_id != decision.case_id or public.decision_id != decision.id or public.revision != decision.revision:
        return None
    if decision.operation == "clear":
        anchor = decision.observed_at
        if anchor is None or (not include_retained and now >= anchor + timedelta(hours=snapshot.unconfirmed_retention_hours)):
            return None
        return public.model_copy(update={"status": "Cleared", "current_status_unknown": False,
            "condition_label": "Reported cleared; vehicle passability remains separate", "updated_at": decision.decided_at})
    if decision.public_state == "withdrawn":
        return None
    expiry = decision.expires_at
    if expiry is None:
        return None
    if now >= expiry or decision.public_state == "expired":
        if not include_retained and now >= expiry + timedelta(hours=snapshot.unconfirmed_retention_hours):
            return None
        return public.model_copy(update={"status": "Unconfirmed", "current_status_unknown": True,
            "condition_label": "Last reported flooding; current condition unknown",
            "passability_label": "Last report: " + public.passability_label.removeprefix("Last report: "),
            "depth_label": "Last reported: " + public.depth_label.removeprefix("Last reported: ") if public.depth_label else None,
            "updated_at": decision.decided_at})
    return public.model_copy(update={"status": "Active", "current_status_unknown": False})


def _write(db: Session, case: NewsClaimCase, decision_id: int, request_id: UUID,
           snapshot: NewsDecisionSnapshot, now: datetime, *, actor_kind: str = "automatic", actor_id: int | None = None,
           operation: str = "evaluate", state: str = "unpublished", review: str = "needs_review",
           reason: str = "needs_independent_review", observed: datetime | None = None,
           expiry: datetime | None = None) -> NewsClaimDecision:
    # PostgreSQL JSON text adds spaces; enforce the database's representation
    # bound conservatively before INSERT so no partially flushed history leaks.
    if len(json.dumps(snapshot.model_dump(mode="json"), ensure_ascii=False, allow_nan=False).encode()) > 60_000:
        raise NewsPublicationError("decision_snapshot_oversized")
    decision = append_decision(db, case, decision_id=decision_id, request_id=request_id, actor_kind=actor_kind,
        actor_user_id=actor_id, operation=operation, public_state=state, review_state=review,
        reason_code=reason, snapshot=snapshot, observed_at=observed, expires_at=expiry, now=now)
    db.add(AuditLog(admin_id=actor_id, action_type="news_claim_decision", target_table="news_claim_cases",
        target_id=case.id, created_at=now, metadata_json={"decision_id": decision.id, "revision": decision.revision,
            "operation": operation, "public_state": state, "actor_kind": actor_kind, "reason_code": reason}))
    db.flush()
    return decision


def publish_completed_evaluation(db: Session, evaluation_id: int, *, policy: EvaluationPolicy, now: datetime,
                                 request_id: UUID | None = None, sources: tuple[NewsSource, ...] | None = None) -> NewsClaimDecision:
    now = require_utc(now)
    sources = sources if sources is not None else load_news_sources()
    request_id = request_id or uuid5(NAMESPACE_URL, f"lanes-news-evaluation:{evaluation_id}:{policy.fingerprint}")
    digest = canonical_sha256({"operation": "evaluate", "evaluation_id": evaluation_id, "policy": policy.fingerprint})
    publication_lock(db, canonical_sha256({"request_id": str(request_id)}))
    existing = existing_request(db, request_id, digest)
    if existing:
        return existing
    loaded = _load(db, evaluation_id, policy, now, sources)
    evaluation, source, run, version, article, claim, audit, reason = loaded
    publication_lock(db, _incident(claim))
    case = lock_case(db, source.case_id)
    previous = latest_decision(db, case.id)
    # A new policy may recover an automatic exception. A completed evaluation
    # must never undo staff choices, clearance, expiry or prior active support.
    if previous is not None and not (previous.public_state == "unpublished"
            and previous.actor_kind in ("automatic", "maintenance") and previous.operation == "evaluate"
            and previous.evaluation_id != evaluation_id):
        return previous
    decision_id = reserve_decision_id(db)
    if claim.condition == "subsided" and not reason:
        targets = list(db.scalars(select(NewsClaimDecision).join(NewsClaimCase, NewsClaimCase.id == NewsClaimDecision.case_id)
            .where(NewsClaimDecision.revision == NewsClaimCase.revision,
                NewsClaimDecision.case_id != case.id, NewsClaimDecision.public_state.in_(("active_alert", "active_zone", "expired")),
                NewsClaimDecision.snapshot["incident_identity"].astext == _incident(claim),
                NewsClaimDecision.snapshot["article_id"].as_integer() == article.article_id).order_by(NewsClaimCase.id)))
        if len(targets) == 1 and _supported_section(claim, article):
            target = targets[0]
            # The initial case lock is released only with the outer transaction;
            # all same-incident operations hold the shared advisory lock first.
            try:
                return clear_case_from_evaluation(db, target.case_id, evaluation_id,
                    expected_revision=target.revision, request_id=request_id, policy=policy, now=now, sources=sources,
                    _request_digest=digest)
            except NewsPublicationError as exc:
                reason = exc.code
        else:
            reason = "clearance_target_requires_verified_match"
    public = None
    if not reason and claim.condition in ("active", "rising"):
        if _clearance_supersedes(db, claim, article) or _wet_supersedes(db, claim, article):
            reason = "source_observation_superseded"
        repeated = db.scalar(select(NewsClaimDecision.id).where(NewsClaimDecision.case_id != case.id,
            NewsClaimDecision.public_state.in_(("active_alert", "active_zone")),
            NewsClaimDecision.snapshot["incident_identity"].astext == _incident(claim),
            NewsClaimDecision.snapshot["article_id"].as_integer() == article.article_id,
            NewsClaimDecision.observed_at == claim.event_time_resolved).limit(1))
        if repeated and not reason:
            reason = "source_observation_already_recorded"
        newer = db.scalar(select(NewsClaimDecision).join(NewsClaimCase, NewsClaimCase.id == NewsClaimDecision.case_id)
            .where(NewsClaimDecision.revision == NewsClaimCase.revision,
                NewsClaimDecision.case_id != case.id,
                NewsClaimDecision.snapshot["incident_identity"].astext == _incident(claim),
                NewsClaimDecision.snapshot["article_id"].as_integer() == article.article_id,
                NewsClaimDecision.observed_at >= claim.event_time_resolved,
                NewsClaimDecision.public_state.in_(("active_alert", "active_zone", "expired", "withdrawn")))
            .limit(1))
        if newer:
            reason = "source_observation_superseded"
        refresh_targets = list(db.scalars(select(NewsClaimDecision).join(NewsClaimCase, NewsClaimCase.id == NewsClaimDecision.case_id)
            .where(NewsClaimDecision.revision == NewsClaimCase.revision,
                NewsClaimDecision.case_id != case.id,
                NewsClaimDecision.public_state.in_(("active_alert", "active_zone", "expired")),
                NewsClaimDecision.snapshot["incident_identity"].astext == _incident(claim),
                NewsClaimDecision.snapshot["article_id"].as_integer() == article.article_id).order_by(NewsClaimCase.id)))
        if not reason and len(refresh_targets) == 1 and _supported_section(claim, article):
            target = refresh_targets[0]
            target_snapshot = NewsDecisionSnapshot.model_validate(target.snapshot)
            original_source = db.get(NewsClaimSource, target_snapshot.claim_source_id)
            original_run = db.get(NewsExtractionRun, original_source.extraction_run_id)
            original_article, original_result = validate_run(original_run, db.get(NewsArticleVersion, original_run.article_version_id))
            original_claim = original_result.claims[original_source.claim_ordinal]
            if (target.public_state != "active_zone" and target_snapshot.public is not None
                    and _supported_section(original_claim, original_article)
                    and target_snapshot.public.observed_at < claim.event_time_resolved
                    <= target_snapshot.public.observed_at + timedelta(hours=12)):
                target_case = lock_case(db, target.case_id)
                if target_case.revision != target.revision:
                    raise NewsPublicationError("stale_case_revision", 409, revision=target_case.revision)
                refreshed = _public(target_case, decision_id, article, claim, audit, now, sources)
                snapshot = _snapshot(source, version, claim, policy, digest, evaluation_id=evaluation.id,
                    previous=target, public=refreshed, target=target.case_id)
                return _write(db, target_case, decision_id, request_id, snapshot, now,
                    state="active_alert", review="resolved", reason="newer_matched_flood_observation",
                    observed=claim.event_time_resolved, expiry=refreshed.expires_at)
        # Same source lineage+qualified section needs explicit continuity before
        # another immutable case can publish or extend the first observation.
        duplicate = db.scalar(select(NewsClaimDecision).join(NewsClaimCase, NewsClaimCase.id == NewsClaimDecision.case_id)
            .where(NewsClaimDecision.revision == NewsClaimCase.revision,
                NewsClaimDecision.case_id != case.id, NewsClaimDecision.public_state.in_(("active_alert", "active_zone")),
                NewsClaimDecision.expires_at > now,
                NewsClaimDecision.snapshot["incident_identity"].astext == _incident(claim),
                NewsClaimDecision.snapshot["article_id"].as_integer() == article.article_id).limit(1))
        if duplicate and not reason:
            reason = "source_continuity_requires_review"
        if not reason:
            public = _public(case, decision_id, article, claim, audit, now, sources)
    snapshot = _snapshot(source, version, claim, policy, digest,
        evaluation_id=evaluation.id, public=public,
        private_reason=reason, previous=previous)
    return _write(db, case, decision_id, request_id, snapshot, now,
        actor_kind="automatic" if evaluation.status == "completed" else "maintenance",
        state="active_alert" if public else "unpublished", review="resolved" if public else "needs_review",
        reason="supported_flood_alert" if public else reason or "needs_independent_review",
        observed=claim.event_time_resolved if public else None, expiry=public.expires_at if public else None)


def _withdraw_support(db: Session, previous: NewsClaimDecision | None, now: datetime) -> None:
    if previous is None:
        return
    zone_ids = list(db.scalars(select(NewsClaimZoneLink.zone_id).where(NewsClaimZoneLink.decision_id == previous.id).order_by(NewsClaimZoneLink.zone_id)))
    event_ids = list(db.scalars(select(FloodAvoidanceZone.event_id).where(FloodAvoidanceZone.id.in_(zone_ids),
        FloodAvoidanceZone.event_id.is_not(None)).distinct().order_by(FloodAvoidanceZone.event_id)))
    # All shared event locks precede their zone locks; concurrent withdrawals
    # cannot each end an event while the other retains independently supported coverage.
    if event_ids:
        list(db.scalars(select(FloodEvent).where(FloodEvent.id.in_(event_ids)).order_by(FloodEvent.id).with_for_update()))
    for zone_id in zone_ids:
        zone = db.scalar(select(FloodAvoidanceZone).where(FloodAvoidanceZone.id == zone_id).with_for_update())
        creation = db.scalar(select(NewsClaimZoneLink).where(NewsClaimZoneLink.zone_id == zone_id, NewsClaimZoneLink.relation == "created"))
        if zone is None or creation is None or zone.curated_by_admin_id is not None:
            continue
        citizen = db.scalar(select(FloodReport.id).where(FloodReport.zone_id == zone_id,
            FloodReport.status == ReportStatus.APPROVED, FloodReport.deleted_at.is_(None)).limit(1))
        news = db.scalar(select(NewsClaimDecision.id).join(NewsClaimCase, NewsClaimCase.id == NewsClaimDecision.case_id)
            .join(NewsClaimZoneLink, NewsClaimZoneLink.decision_id == NewsClaimDecision.id)
            .where(NewsClaimZoneLink.zone_id == zone_id, NewsClaimDecision.revision == NewsClaimCase.revision,
                NewsClaimDecision.public_state == "active_zone", NewsClaimDecision.expires_at > now,
                NewsClaimDecision.case_id != previous.case_id).limit(1))
        if citizen or news:
            continue
        zone.is_active = False
        # Never clear finite expires_at to resurrect unsupported coverage.
        if zone.expires_at is None or zone.expires_at > now:
            zone.expires_at = now
        if zone.event_id:
            event = db.scalar(select(FloodEvent).where(FloodEvent.id == zone.event_id).with_for_update())
            db.flush()
            remaining = db.scalar(select(FloodAvoidanceZone.id).where(FloodAvoidanceZone.event_id == zone.event_id,
                FloodAvoidanceZone.is_active.is_(True),
                (FloodAvoidanceZone.expires_at.is_(None)) | (FloodAvoidanceZone.expires_at > now)).limit(1))
            if event and not remaining:
                event.status, event.ended_at = FloodEventStatus.ENDED, now
                db.add(FloodEventTimelineEntry(event_id=event.id, entry_type="news_support_ended", occurred_at=now,
                    summary="Eligible news support ended; current road condition remains separately recorded.",
                    snapshot_json={"zone_id": zone.id, "claim_case_id": previous.case_id}))


def clear_case_from_evaluation(db: Session, case_id: int, evaluation_id: int, *, expected_revision: int,
        request_id: UUID, policy: EvaluationPolicy, now: datetime, actor_user_id: int | None = None,
        reason: str | None = None, sources: tuple[NewsSource, ...] | None = None,
        _request_digest: str | None = None) -> NewsClaimDecision:
    now = require_utc(now)
    sources = sources if sources is not None else load_news_sources()
    digest = _request_digest or canonical_sha256({"operation": "clear", "case_id": case_id, "evaluation_id": evaluation_id,
        "expected_revision": expected_revision, "actor_user_id": actor_user_id, "reason": reason})
    publication_lock(db, canonical_sha256({"request_id": str(request_id)}))
    previous_request = existing_request(db, request_id, digest)
    if previous_request:
        return previous_request
    evaluation, source, run, version, article, claim, audit, failure = _load(db, evaluation_id, policy, now, sources)
    publication_lock(db, _incident(claim))
    case = lock_case(db, case_id)
    if case.revision != expected_revision:
        raise NewsPublicationError("stale_case_revision", 409, revision=case.revision)
    previous = latest_decision(db, case.id)
    if previous is None or previous.public_state not in ("active_alert", "active_zone", "expired"):
        raise NewsPublicationError("clearance_target_not_active_or_unconfirmed")
    saved = NewsDecisionSnapshot.model_validate(previous.snapshot)
    if (failure or claim.condition != "subsided" or audit is None
            or audit.evidence.status.classification != "subsided"):
        raise NewsPublicationError(failure or "clearance_not_independently_verified")
    if (saved.incident_identity != _incident(claim) or not _supported_section(claim, article)
            or saved.article_id != article.article_id):
        raise NewsPublicationError("clearance_target_identity_unproven")
    wet_source = db.get(NewsClaimSource, saved.claim_source_id)
    wet_run = db.get(NewsExtractionRun, wet_source.extraction_run_id)
    wet_article, wet_result = validate_run(wet_run, db.get(NewsArticleVersion, wet_run.article_version_id))
    if not _supported_section(wet_result.claims[wet_source.claim_ordinal], wet_article):
        raise NewsPublicationError("clearance_target_identity_unproven")
    if saved.public is None or saved.public.observed_at is None or claim.event_time_resolved <= saved.public.observed_at:
        raise NewsPublicationError("clearance_observation_not_newer")
    if claim.event_time_resolved - saved.public.observed_at > timedelta(hours=12):
        raise NewsPublicationError("clearance_incident_continuity_unproven")
    decision_id = reserve_decision_id(db)
    public = saved.public.model_copy(update={"decision_id": decision_id, "revision": case.revision + 1,
        "status": "Cleared", "cleared_at": claim.event_time_resolved, "updated_at": now,
        "source_title": _safe(article.title, 500), "source_url": article.canonical_url,
        "source_published_at": article.published_at, "evidence_excerpt": _safe(claim.evidence_sentence, 700),
        "condition_label": "Reported cleared; vehicle passability remains separate", "correction_note": None,
        "depth_label": None, "passability_label": "Vehicle passability unknown"})
    snapshot = _snapshot(source, version, claim, policy, digest, evaluation_id=evaluation.id,
        previous=previous, public=public, private_reason=reason, target=case.id)
    decision = _write(db, case, decision_id, request_id, snapshot, now,
        actor_kind="staff" if actor_user_id is not None else "automatic", actor_id=actor_user_id,
        operation="clear", state="withdrawn", review="resolved", reason="matched_clearance_observed",
        observed=claim.event_time_resolved, expiry=previous.expires_at)
    _withdraw_support(db, previous, now)
    return decision


def expire_case(db: Session, case_id: int, *, now: datetime) -> NewsClaimDecision | None:
    now = require_utc(now)
    publication_lock(db, canonical_sha256({"maintenance_case": case_id}))
    case = lock_case(db, case_id)
    previous = latest_decision(db, case.id)
    if previous is None or previous.public_state not in ("active_alert", "active_zone") or previous.expires_at > now:
        return None
    request_id = uuid5(NAMESPACE_URL, f"lanes-news-expiry:{case_id}:{previous.id}")
    digest = canonical_sha256({"operation": "expire", "case_id": case_id, "previous_decision_id": previous.id})
    decision_id = reserve_decision_id(db)
    saved = NewsDecisionSnapshot.model_validate(previous.snapshot)
    public = saved.public.model_copy(update={"decision_id": decision_id, "revision": case.revision + 1,
        "status": "Unconfirmed", "current_status_unknown": True, "updated_at": now,
        "condition_label": "Last reported flooding; current condition unknown"}) if saved.public else None
    snapshot = saved.model_copy(update={"request_sha256": digest, "previous_decision_id": previous.id, "public": public})
    decision = _write(db, case, decision_id, request_id, snapshot, now, actor_kind="maintenance",
        operation="expire", state="expired", review="resolved", reason="observation_evidence_expired",
        observed=previous.observed_at, expiry=previous.expires_at)
    _withdraw_support(db, previous, now)
    return decision


def preview_staff_decision(db: Session, case_id: int, request: NewsStaffDecisionRequest, *,
        policy: EvaluationPolicy, now: datetime, sources: tuple[NewsSource, ...] | None = None) -> NewsDecisionEffect:
    """Read-only effect preview; submission repeats every gate under locks."""
    now = require_utc(now)
    case = db.get(NewsClaimCase, case_id)
    if case is None:
        raise NewsPublicationError("claim_not_found", 404)
    if case.revision != request.expected_revision:
        raise NewsPublicationError("stale_case_revision", 409, revision=case.revision)
    previous = latest_decision(db, case_id)
    saved = NewsDecisionSnapshot.model_validate(previous.snapshot) if previous else None
    if request.operation in ("correct", "clear"):
        if request.evaluation_id is None:
            raise NewsPublicationError(f"{request.operation}_evaluation_required")
        sources = sources if sources is not None else load_news_sources()
        evaluation, source, run, version, article, claim, audit, reason = _load(db, request.evaluation_id, policy, now, sources)
        if reason:
            raise NewsPublicationError(reason)
        if request.operation == "correct":
            _correction_checks(db, case_id, request.evaluation_id, source, article, claim)
            return NewsDecisionEffect(public_state="active_alert", review_state="resolved", status="Active", reason_code="staff_correct")
        if previous is None or previous.public_state not in ("active_alert", "active_zone", "expired"):
            raise NewsPublicationError("clearance_target_not_active_or_unconfirmed")
        if claim.condition != "subsided" or audit.evidence.status.classification != "subsided":
            raise NewsPublicationError("clearance_not_independently_verified")
        if (saved.incident_identity != _incident(claim) or not _supported_section(claim, article)
                or saved.article_id != article.article_id):
            raise NewsPublicationError("clearance_target_identity_unproven")
        wet_source = db.get(NewsClaimSource, saved.claim_source_id)
        wet_run = db.get(NewsExtractionRun, wet_source.extraction_run_id)
        wet_article, wet_result = validate_run(wet_run, db.get(NewsArticleVersion, wet_run.article_version_id))
        if not _supported_section(wet_result.claims[wet_source.claim_ordinal], wet_article):
            raise NewsPublicationError("clearance_target_identity_unproven")
        if saved.public is None or saved.public.observed_at is None or claim.event_time_resolved <= saved.public.observed_at:
            raise NewsPublicationError("clearance_observation_not_newer")
        if claim.event_time_resolved - saved.public.observed_at > timedelta(hours=12):
            raise NewsPublicationError("clearance_incident_continuity_unproven")
        return NewsDecisionEffect(public_state="withdrawn", review_state="resolved", status="Cleared", reason_code="matched_clearance_observed")
    if request.operation == "defer":
        if request.deferred_until is None or not now < request.deferred_until <= now + timedelta(days=7):
            raise NewsPublicationError("invalid_deferred_until")
        return NewsDecisionEffect(public_state="withdrawn" if saved and saved.public else "unpublished",
            review_state="deferred", reason_code="staff_defer")
    if request.operation == "reopen":
        if previous is None or previous.public_state not in ("withdrawn", "unpublished", "expired"):
            raise NewsPublicationError("claim_cannot_reopen")
        return NewsDecisionEffect(public_state="unpublished", review_state="needs_review", reason_code="staff_reopen")
    return NewsDecisionEffect(public_state="withdrawn", review_state="resolved", reason_code="staff_reject")


def apply_staff_decision(db: Session, case_id: int, request: NewsStaffDecisionRequest, *, actor_user_id: int,
                         policy: EvaluationPolicy, now: datetime, sources: tuple[NewsSource, ...] | None = None) -> NewsClaimDecision:
    now = require_utc(now)
    digest = canonical_sha256({"case_id": case_id, "actor_user_id": actor_user_id,
        "request": request.model_dump(mode="json")})
    if request.operation == "clear":
        if request.evaluation_id is None:
            raise NewsPublicationError("clearance_evaluation_required")
        return clear_case_from_evaluation(db, case_id, request.evaluation_id, expected_revision=request.expected_revision,
            request_id=request.request_id, policy=policy, now=now, actor_user_id=actor_user_id, reason=request.reason,
            sources=sources, _request_digest=digest)
    publication_lock(db, canonical_sha256({"request_id": str(request.request_id)}))
    existing = existing_request(db, request.request_id, digest)
    if existing:
        return existing
    correction = None
    if request.operation == "correct":
        if request.evaluation_id is None:
            raise NewsPublicationError("correction_evaluation_required")
        sources = sources if sources is not None else load_news_sources()
        correction = _load(db, request.evaluation_id, policy, now, sources)
        publication_lock(db, _incident(correction[5]))
    case = lock_case(db, case_id)
    if case.revision != request.expected_revision:
        raise NewsPublicationError("stale_case_revision", 409, revision=case.revision)
    previous = latest_decision(db, case.id)
    source = db.scalar(select(NewsClaimSource).where(NewsClaimSource.case_id == case.id).order_by(NewsClaimSource.id.desc()).limit(1))
    if source is None:
        raise NewsPublicationError("claim_source_missing")
    run = db.get(NewsExtractionRun, source.extraction_run_id)
    version = db.get(NewsArticleVersion, run.article_version_id)
    article, extraction = validate_run(run, version)
    claim = extraction.claims[source.claim_ordinal]
    saved = NewsDecisionSnapshot.model_validate(previous.snapshot) if previous else None
    public = None
    state, review, evaluation_id = "unpublished", "needs_review", None
    if request.operation == "correct":
        evaluation, corrected_source, corrected_run, corrected_version, corrected_article, corrected_claim, audit, failure = correction
        if failure:
            raise NewsPublicationError(failure)
        _correction_checks(db, case.id, request.evaluation_id, corrected_source, corrected_article, corrected_claim)
        source, version, claim, article = corrected_source, corrected_version, corrected_claim, corrected_article
        evaluation_id = evaluation.id
        state, review = "active_alert", "resolved"
    elif request.operation == "defer":
        if request.deferred_until is None or not now < request.deferred_until <= now + timedelta(days=7):
            raise NewsPublicationError("invalid_deferred_until")
        state, review = "withdrawn" if saved and saved.public else "unpublished", "deferred"
    elif request.operation == "reject":
        state, review = "withdrawn", "resolved"
    elif request.operation == "reopen":
        if previous is None or previous.public_state not in ("withdrawn", "unpublished", "expired"):
            raise NewsPublicationError("claim_cannot_reopen")
        # Reopening is a review action; it cannot resurrect expired evidence.
    decision_id = reserve_decision_id(db)
    if request.operation == "correct":
        public = _public(case, decision_id, article, claim, audit, now, sources)
        public.correction_note = _safe(request.public_correction, 500)
    snapshot = _snapshot(source, version, claim, policy, digest, evaluation_id=evaluation_id,
        previous=previous, public=public, private_reason=request.reason,
        deferred_until=request.deferred_until if request.operation == "defer" else None)
    decision = _write(db, case, decision_id, request.request_id, snapshot, now, actor_kind="staff", actor_id=actor_user_id,
        operation=request.operation, state=state, review=review, reason=f"staff_{request.operation}",
        observed=public.observed_at if public else None, expiry=public.expires_at if public else None)
    _withdraw_support(db, previous, now)
    return decision


@dataclass
class PublicationSummary:
    published: int = 0
    needs_review: int = 0
    expired: int = 0
    cleared: int = 0
    skipped: list[dict] = field(default_factory=list)


def process_news_publications(session_factory: Callable[[], Session], *, policy: EvaluationPolicy,
                              limit: int = 50, clock: Callable[[], datetime] = utc_now,
                              sources: tuple[NewsSource, ...] | None = None) -> PublicationSummary:
    if not 1 <= limit <= 200:
        raise ValueError("Invalid publication limit")
    summary = PublicationSummary()
    with session_factory() as db:
        protected_case = exists(select(NewsClaimDecision.id).join(NewsClaimCase, NewsClaimCase.id == NewsClaimDecision.case_id)
            .where(NewsClaimCase.id == NewsClaimSource.case_id, NewsClaimDecision.revision == NewsClaimCase.revision,
                ~((NewsClaimDecision.public_state == "unpublished") &
                  NewsClaimDecision.actor_kind.in_(("automatic", "maintenance")) &
                  (NewsClaimDecision.operation == "evaluate"))))
        ids = list(db.scalars(select(NewsClaimEvaluation.id).join(NewsClaimSource,
            NewsClaimSource.id == NewsClaimEvaluation.claim_source_id).where(NewsClaimEvaluation.status.in_(("completed", "failed")),
            NewsClaimEvaluation.policy_fingerprint == policy.fingerprint,
            ~protected_case,
            ~exists(select(NewsClaimDecision.id).where(NewsClaimDecision.evaluation_id == NewsClaimEvaluation.id)))
            .order_by(NewsClaimEvaluation.id).limit(limit)))
    for evaluation_id in ids:
        try:
            with session_factory() as db, db.begin():
                decision = publish_completed_evaluation(db, evaluation_id, policy=policy, now=clock(), sources=sources)
                state = decision.public_state
                operation = decision.operation
            outcome = "cleared" if operation == "clear" else "published" if state == "active_alert" else "needs_review"
            setattr(summary, outcome, getattr(summary, outcome) + 1)
        except NewsPublicationError as exc:
            summary.skipped.append({"evaluation_id": evaluation_id, "reason_code": exc.code})
    with session_factory() as db:
        cases = list(db.scalars(select(NewsClaimCase.id).join(NewsClaimDecision, NewsClaimDecision.case_id == NewsClaimCase.id)
            .where(NewsClaimDecision.revision == NewsClaimCase.revision,
                NewsClaimDecision.public_state.in_(("active_alert", "active_zone")), NewsClaimDecision.expires_at <= clock())
            .order_by(NewsClaimCase.id).limit(limit)))
    for case_id in cases:
        with session_factory() as db, db.begin():
            if expire_case(db, case_id, now=clock()) is not None:
                summary.expired += 1
    return summary
