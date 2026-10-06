"""Atomic source-labeled news alerts and evidence lifecycle; no guessed zones.

Each helper participates in its caller's transaction. Independent audit,
immutable input and current policy are rechecked before any public decision.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
import json
import re
from uuid import UUID, uuid5, NAMESPACE_URL

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import exists, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from shapely.geometry import mapping
from shapely import get_srid
from geoalchemy2.shape import to_shape
from shapely.geometry.base import BaseGeometry

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
from app.schemas.common import PolygonGeometry
from app.schemas.report import FloodAvoidanceZoneCreate
from app.crud.report import create_flood_avoidance_zone
from app.schemas.news_audit import IndependentAuditResult
from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from app.schemas.news_publication import (
    NewsDecisionEffect, NewsDecisionSnapshot, NewsStaffDecisionRequest,
    OperationalFootprintProvenance, PublicNewsAlert,
)
from app.services.flood_event_service import create_verified_event_with_zone
from app.services.flood_depth import get_flood_depth_measurement
from app.services.operational_footprint_service import OperationalFootprintValidation, validate_operational_shape
from app.services.operational_footprint_evidence_service import (
    approve_news_footprint, context_for, get_incident_footprint_provider,
)
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
              deferred_until: datetime | None = None,
              geometry_reason: str = "operational_geometry_not_verified",
              linked_zone_ids: list[int] | None = None,
              operational_provenance: OperationalFootprintProvenance | None = None) -> NewsDecisionSnapshot:
    return NewsDecisionSnapshot(request_sha256=digest, policy_fingerprint=policy.fingerprint,
        claim_source_id=source.id, evaluation_id=evaluation_id, input_sha256=version.input_fingerprint,
        claim_sha256=source.claim_sha256, incident_identity=_incident(claim), article_id=version.article_id,
        public=public, private_reason=private_reason, target_case_id=target,
        previous_decision_id=previous.id if previous else None, deferred_until=deferred_until,
        unconfirmed_retention_hours=unconfirmed_retention_hours(),
        geometry_reason=geometry_reason,
        linked_zone_ids=linked_zone_ids or [], operational_provenance=operational_provenance)


def _public(case: NewsClaimCase, decision_id: int, article: NewsArticleExtractorInput,
            claim: ExtractedClaim, audit: IndependentAuditResult, now: datetime,
            sources: tuple[NewsSource, ...],
            *,
            geometry_precision: str = "text_only",
            display_geojson: dict | None = None,
            affects_routing: bool = False,
            geometry_basis: str | None = None) -> PublicNewsAlert:
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
        evidence_excerpt=_safe(claim.evidence_sentence, 700),
        geometry_precision=geometry_precision,
        display_geojson=display_geojson,
        affects_routing=affects_routing, geometry_basis=geometry_basis)


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
        return public.model_copy(update={"status": "Cleared", "current_status_unknown": False, "affects_routing": False,
            "condition_label": "Reported cleared; vehicle passability remains separate", "updated_at": decision.decided_at})
    if decision.public_state == "withdrawn":
        return None
    expiry = decision.expires_at
    if expiry is None:
        return None
    if now >= expiry or decision.public_state == "expired":
        if not include_retained and now >= expiry + timedelta(hours=snapshot.unconfirmed_retention_hours):
            return None
        return public.model_copy(update={"status": "Unconfirmed", "current_status_unknown": True, "affects_routing": False,
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
            if (target_snapshot.public is not None
                    and _supported_section(original_claim, original_article)
                    and target_snapshot.public.observed_at < claim.event_time_resolved
                    <= target_snapshot.public.observed_at + timedelta(hours=12)):
                target_case = lock_case(db, target.case_id)
                if target_case.revision != target.revision:
                    raise NewsPublicationError("stale_case_revision", 409, revision=target_case.revision)
                is_active_zone = (target.public_state == "active_zone")
                was_active_zone = is_active_zone
                linked_zones = list(db.scalars(select(NewsClaimZoneLink.zone_id).where(NewsClaimZoneLink.decision_id == target.id)
                    .order_by(NewsClaimZoneLink.zone_id)))
                supported_zone_ids: list[int] = []
                refresh_provenance = None
                refresh_failure = None
                if is_active_zone:
                    # A newer article observation cannot silently renew an old
                    # perimeter. Require current server-approved extent and the
                    # same measured metadata; changed extent/depth needs a new
                    # activation after the source alert is published.
                    context = _footprint_context(source, version, article, claim)
                    assets = get_incident_footprint_provider()
                    matches = [record for record in assets.records.values()
                        if all(getattr(record, key) == value for key, value in context.items())
                        and canonical_sha256(record.geometry) == canonical_sha256(target_snapshot.public.display_geojson)]
                    try:
                        binding = (target_snapshot.operational_provenance.binding
                                   if target_snapshot.operational_provenance else None)
                        estimated = binding is not None and binding.evidence_kind == "estimated_news_road"
                        if not linked_zones:
                            raise NewsPublicationError("operational_footprint_refresh_unverified")
                        if estimated:
                            from app.services.news_estimated_road_service import build_estimated_road_zone
                            corridor = build_estimated_road_zone(claim)
                            if canonical_sha256(corridor.geometry) != canonical_sha256(target_snapshot.public.display_geojson):
                                raise NewsPublicationError("estimated_road_extent_changed")
                            _, refresh_provenance = approve_news_footprint(db, corridor.geometry,
                                geometry_srid=4326, claim=claim, context=context, now=now,
                                source=corridor.source_id, checksum=corridor.checksum, estimated_road=True)
                        else:
                            if assets.error or len(matches) != 1:
                                raise NewsPublicationError("operational_footprint_refresh_unverified")
                            _, refresh_provenance = approve_news_footprint(db, matches[0].geometry,
                                geometry_srid=matches[0].srid, claim=claim, context=context, now=now,
                                record_id=matches[0].record_id, source=matches[0].source_id)
                        attributes = _operational_zone_attributes(claim, audit)
                        current_components = []
                        for index, zone_id in enumerate(linked_zones):
                            zone = db.get(FloodAvoidanceZone, zone_id)
                            if (zone is None or not zone.is_active or zone.expires_at is None or zone.expires_at <= now
                                    or any(getattr(zone, name) != value for name, value in attributes.items())):
                                raise NewsPublicationError("operational_footprint_refresh_unverified")
                            actual_geometry = to_shape(zone.geometry)
                            if get_srid(actual_geometry) != 4326:
                                raise NewsPublicationError("operational_footprint_refresh_unverified")
                            current_components.append(canonical_sha256(mapping(actual_geometry)))
                            if estimated and (zone.source_geometry is None or canonical_sha256(mapping(to_shape(zone.source_geometry)))
                                    != canonical_sha256(refresh_provenance.binding.estimated_road.component_centerlines[index])):
                                raise NewsPublicationError("estimated_road_centerline_changed")
                        if sorted(current_components) != sorted(refresh_provenance.binding.component_sha256):
                            raise NewsPublicationError("operational_footprint_refresh_unverified")
                    except NewsPublicationError as exc:
                        # Explicit text-only fallback preserves the report while
                        # withdrawing this case's unsupported operational links.
                        is_active_zone, refresh_provenance = False, None
                        refresh_failure = exc.code
                refreshed = _public(
                    target_case, decision_id, article, claim, audit, now, sources,
                    geometry_precision="operational_polygon" if is_active_zone else "text_only",
                    display_geojson=target_snapshot.public.display_geojson if is_active_zone else None,
                    affects_routing=is_active_zone,
                    geometry_basis=target_snapshot.public.geometry_basis if is_active_zone else None,
                )
                if is_active_zone and linked_zones:
                    for lz_id in linked_zones:
                        z_obj = db.get(FloodAvoidanceZone, lz_id)
                        if z_obj and z_obj.is_active:
                            z_obj.expires_at = refreshed.expires_at
                            supported_zone_ids.append(lz_id)
                snapshot = _snapshot(
                    source, version, claim, policy, digest, evaluation_id=evaluation.id,
                    previous=target, public=refreshed, target=target.case_id,
                    geometry_reason=target_snapshot.geometry_reason if is_active_zone else "operational_geometry_not_verified",
                    linked_zone_ids=linked_zones if is_active_zone else [],
                    operational_provenance=refresh_provenance if is_active_zone else None,
                    private_reason=refresh_failure,
                )
                decision = _write(db, target_case, decision_id, request_id, snapshot, now,
                    state="active_zone" if is_active_zone else "active_alert",
                    review="resolved", reason=("newer_observation_footprint_unverified" if refresh_failure
                                               else "newer_matched_flood_observation"),
                    observed=claim.event_time_resolved, expiry=refreshed.expires_at)
                # The existing DB trigger requires the active decision to exist
                # before support links are inserted. All writes remain atomic.
                for zone_id in supported_zone_ids:
                    db.add(NewsClaimZoneLink(decision_id=decision_id, zone_id=zone_id,
                                           relation="supported", created_at=now))
                if supported_zone_ids:
                    db.flush()
                if was_active_zone and not is_active_zone:
                    _withdraw_support(db, target, now)
                return decision
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


def _operational_zone_attributes(claim: ExtractedClaim, audit: IndependentAuditResult | None) -> dict[str, Any]:
    """Persist verified news measurements and restrictions, never inferred access."""
    if audit is None or audit.evidence is None:
        raise NewsPublicationError("independent_audit_unavailable")
    if claim.road_passability == "passable_all" or audit.evidence.access.classification == "passable_all":
        raise NewsPublicationError("reported_passable_to_all_vehicles")
    measurement = get_flood_depth_measurement(claim.depth_canonical)
    if measurement is None or not audit.evidence.depth.confirmed:
        raise NewsPublicationError("operational_depth_not_verified")
    if claim.road_passability != "unknown" and not audit.evidence.access.confirmed:
        raise NewsPublicationError("operational_access_not_verified")
    access = {
        "unknown": None,
        "light_vehicle_closed": "Light vehicles prohibited",
        "impassable_all": "No vehicles",
        "passable_with_caution": "Passable with caution; vehicle types unspecified",
        "passable_unspecified": "Passability reported; vehicle types unspecified",
    }[claim.road_passability]
    return {"severity_override": measurement.severity, "depth_override": measurement.key,
            "passable_vehicles_override": access}


def _footprint_context(source: NewsClaimSource, version: NewsArticleVersion,
                       article: NewsArticleExtractorInput, claim: ExtractedClaim) -> dict[str, Any]:
    return context_for(claim, article_id=article.article_id, input_sha256=version.input_fingerprint,
                       claim_sha256=source.claim_sha256, incident_identity=_incident(claim))


def _review_existing_zone(db: Session, zone_id: int, *, claim: ExtractedClaim, context: dict[str, Any],
                          zone_attributes: dict[str, Any],
                          actor_user_id: int | None, review_id: str, now: datetime) -> tuple[OperationalFootprintValidation, OperationalFootprintProvenance]:
    zone = db.get(FloodAvoidanceZone, zone_id)
    if not zone or not zone.is_active or (zone.expires_at is not None and zone.expires_at <= now):
        raise NewsPublicationError("invalid_operational_zone")
    # Relinking cannot renew coverage or silently leave stale routing metadata.
    # A different observed depth/access requires a newly reviewed footprint.
    if any(getattr(zone, name) != value for name, value in zone_attributes.items()):
        raise NewsPublicationError("operational_zone_metadata_mismatch")
    owners = db.scalars(select(NewsClaimDecision).join(NewsClaimZoneLink, NewsClaimZoneLink.decision_id == NewsClaimDecision.id)
        .where(NewsClaimZoneLink.zone_id == zone_id, NewsClaimDecision.snapshot["incident_identity"].astext == context["incident_identity"],
               NewsClaimDecision.snapshot["article_id"].as_integer() == context["article_id"]))
    geometry = to_shape(zone.geometry)
    if get_srid(geometry) != 4326:
        raise NewsPublicationError("unsupported_or_missing_geometry_srid")
    component_hash = canonical_sha256(mapping(geometry))
    proven_owner = False
    for owner in owners:
        proof = NewsDecisionSnapshot.model_validate(owner.snapshot).operational_provenance
        if (proof and proof.binding and proof.binding.article_id == context["article_id"]
                and proof.binding.incident_identity == context["incident_identity"]
                and component_hash in proof.binding.component_sha256):
            proven_owner = True
            break
    if not proven_owner:
        raise NewsPublicationError("operational_zone_incident_unverified")
    return approve_news_footprint(db, geometry, geometry_srid=4326,
        claim=claim, context=context, actor_user_id=actor_user_id, review_id=review_id, now=now)


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
                # The newly current decision may retain this same case's
                # support; only the withdrawn decision itself is excluded.
                NewsClaimDecision.id != previous.id).limit(1))
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
        previous=previous, public=public, private_reason=reason, target=case.id,
        operational_provenance=saved.operational_provenance)
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
        policy: EvaluationPolicy, now: datetime, sources: tuple[NewsSource, ...] | None = None,
        actor_user_id: int | None = None) -> NewsDecisionEffect:
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
            is_zone = request.operational_footprint is not None or request.operational_zone_id is not None
            context = _footprint_context(source, version, article, claim)
            if is_zone:
                zone_attributes = _operational_zone_attributes(claim, audit)
                if actor_user_id is None:
                    raise NewsPublicationError("unauthorized_footprint_review", 403)
            if request.operational_footprint is not None:
                approve_news_footprint(db, request.operational_footprint,
                    geometry_srid=request.operational_footprint_srid, claim=claim, context=context,
                    actor_user_id=actor_user_id, review_id=str(request.request_id), now=now)
            elif request.operational_zone_id:
                _review_existing_zone(db, request.operational_zone_id, claim=claim, context=context,
                                      zone_attributes=zone_attributes,
                                      actor_user_id=actor_user_id, review_id=str(request.request_id), now=now)
            return NewsDecisionEffect(
                public_state="active_zone" if is_zone else "active_alert",
                review_state="resolved",
                status="Active",
                reason_code="staff_correct",
                affects_routing=is_zone,
                linked_zone_ids=[request.operational_zone_id] if request.operational_zone_id else [],
            )
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
    linked_zone_ids: list[int] = []
    geom_reason = "operational_geometry_not_verified"
    display_geojson = None
    operational_provenance = None

    if request.operation == "correct":
        evaluation, corrected_source, corrected_run, corrected_version, corrected_article, corrected_claim, audit, failure = correction
        if failure:
            raise NewsPublicationError(failure)
        _correction_checks(db, case.id, request.evaluation_id, corrected_source, corrected_article, corrected_claim)
        source, version, claim, article = corrected_source, corrected_version, corrected_claim, corrected_article
        evaluation_id = evaluation.id

        is_zone = request.operational_footprint is not None or request.operational_zone_id is not None
        zone_attributes = _operational_zone_attributes(claim, audit) if is_zone else None
        state = "active_zone" if is_zone else "active_alert"
        review = "resolved"

        if request.operational_footprint is not None:
            val, operational_provenance = approve_news_footprint(db, request.operational_footprint,
                geometry_srid=request.operational_footprint_srid, claim=claim,
                context=_footprint_context(source, version, article, claim), actor_user_id=actor_user_id,
                review_id=str(request.request_id), now=now)
            geom_reason = "staff_reviewed_footprint"
            display_geojson = val.geojson

            sev_val = zone_attributes["severity_override"]
            event_obj = None
            expiry_time = claim.event_time_resolved + timedelta(hours=2)
            for idx, part in enumerate(val.polygon_parts):
                poly_in = PolygonGeometry(**part)
                zone_in = FloodAvoidanceZoneCreate(
                    geometry=poly_in,
                    is_active=True,
                    expires_at=expiry_time,
                )
                if idx == 0:
                    event_obj, created_zone = create_verified_event_with_zone(
                        db,
                        zone_in,
                        peak_severity=sev_val,
                        peak_depth=claim.depth_canonical,
                        acted_by_user_id=actor_user_id,
                        zone_attributes=zone_attributes,
                        commit=False,
                        first_reported_at=claim.event_time_resolved,
                    )
                    linked_zone_ids.append(created_zone.id)
                else:
                    created_zone = create_flood_avoidance_zone(db, zone_in, event_id=event_obj.id, commit=False)
                    for attribute, value in zone_attributes.items():
                        setattr(created_zone, attribute, value)
                    linked_zone_ids.append(created_zone.id)
        elif request.operational_zone_id:
            val, operational_provenance = _review_existing_zone(db, request.operational_zone_id, claim=claim,
                zone_attributes=zone_attributes,
                context=_footprint_context(source, version, article, claim), actor_user_id=actor_user_id,
                review_id=str(request.request_id), now=now)
            linked_zone_ids.append(request.operational_zone_id)
            display_geojson = val.geojson
            geom_reason = "staff_reviewed_footprint"
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
        public = _public(
            case, decision_id, article, claim, audit, now, sources,
            geometry_precision="operational_polygon" if state == "active_zone" else "text_only",
            display_geojson=display_geojson,
            affects_routing=(state == "active_zone"),
        )
        public.correction_note = _safe(request.public_correction, 500)
    snapshot = _snapshot(source, version, claim, policy, digest, evaluation_id=evaluation_id,
        previous=previous, public=public, private_reason=request.reason,
        deferred_until=request.deferred_until if request.operation == "defer" else None,
        geometry_reason=geom_reason, linked_zone_ids=linked_zone_ids, operational_provenance=operational_provenance)
    decision = _write(db, case, decision_id, request.request_id, snapshot, now, actor_kind="staff", actor_id=actor_user_id,
        operation=request.operation, state=state, review=review, reason=f"staff_{request.operation}",
        observed=public.observed_at if public else None, expiry=public.expires_at if public else None)

    if linked_zone_ids:
        rel = "created" if request.operational_footprint else "supported"
        for z_id in linked_zone_ids:
            db.add(NewsClaimZoneLink(decision_id=decision_id, zone_id=z_id, relation=rel, created_at=now))
        db.flush()

    _withdraw_support(db, previous, now)
    return decision


def require_geometry_review(db: Session, case_id: int, *, expected_revision: int,
        reason: str, now: datetime, asset_revision: str) -> None:
    """Queue a text alert for spatial review without inventing a routing extent."""
    case = lock_case(db, case_id)
    previous = latest_decision(db, case_id)
    if (case.revision != expected_revision or previous is None or previous.actor_kind != "automatic"
            or previous.operation != "evaluate" or previous.public_state != "active_alert"):
        return
    snapshot = NewsDecisionSnapshot.model_validate(previous.snapshot)
    if (previous.review_state == "needs_review" and snapshot.private_reason == reason
            and snapshot.estimated_road_review_revision == asset_revision):
        return
    digest = canonical_sha256({"operation": "geometry_review", "case_id": case_id,
                               "revision": expected_revision, "reason": reason})
    decision_id = reserve_decision_id(db)
    public = snapshot.public.model_copy(update={"decision_id": decision_id, "revision": case.revision + 1,
                                                "updated_at": now}) if snapshot.public else None
    snapshot = snapshot.model_copy(update={"request_sha256": digest, "private_reason": reason,
        "previous_decision_id": previous.id, "public": public, "estimated_road_review_revision": asset_revision})
    _write(db, case, decision_id, uuid5(NAMESPACE_URL, f"lanes-news-geometry-review:{digest}"), snapshot, now,
           state="active_alert", review="needs_review", reason="estimated_road_needs_review",
           observed=previous.observed_at, expiry=previous.expires_at)


def activate_estimated_road(db: Session, case_id: int, *, expected_revision: int,
        policy: EvaluationPolicy, now: datetime, sources: tuple[NewsSource, ...] | None = None) -> NewsClaimDecision:
    """Derive an estimate; the common transaction rechecks its audit and assets."""
    from app.services.news_estimated_road_service import build_estimated_road_zone
    previous = latest_decision(db, case_id)
    if previous is None:
        raise NewsPublicationError("claim_not_active_alert_or_zone")
    snapshot = NewsDecisionSnapshot.model_validate(previous.snapshot)
    sources = sources if sources is not None else load_news_sources()
    _, _, _, _, _, claim, _, failure = _load(db, snapshot.evaluation_id, policy, now, sources)
    if failure:
        raise NewsPublicationError(failure)
    estimated = build_estimated_road_zone(claim)
    return activate_operational_footprint(db, case_id, estimated.geometry,
        expected_revision=expected_revision, geometry_srid=4326, policy=policy, now=now,
        provenance_source=estimated.source_id, provenance_checksum=estimated.checksum,
        estimated_road=True, sources=sources)


def activate_operational_footprint(
    db: Session,
    case_id: int,
    footprint: Any,
    *,
    expected_revision: int,
    provenance_source: str,
    geometry_srid: int | None = None,
    evidence_record_id: str | None = None,
    provenance_checksum: str | None = None,
    parent_boundary: BaseGeometry | None = None,
    policy: EvaluationPolicy,
    now: datetime,
    actor_user_id: int | None = None,
    request_id: UUID | None = None,
    sources: tuple[NewsSource, ...] | None = None,
    estimated_road: bool = False,
) -> NewsClaimDecision:
    """Activate an operational flood footprint for a verified news claim atomically.

    Performs atomic creation of FloodEvent, FloodAvoidanceZone(s),
    NewsClaimZoneLink (relation='created'), and updates the decision to active_zone.
    MultiPolygons are split into distinct FloodAvoidanceZone records without bridging gaps.
    """
    now = require_utc(now)
    if type(expected_revision) is not int or expected_revision < 0:
        raise NewsPublicationError("invalid_expected_revision")
    if parent_boundary is not None and (
        not isinstance(parent_boundary, BaseGeometry) or parent_boundary.is_empty or not parent_boundary.is_valid
    ):
        raise NewsPublicationError("invalid_parent_boundary")
    val = validate_operational_shape(footprint, geometry_srid=geometry_srid, parent_boundary=parent_boundary)
    if not val.is_eligible:
        raise NewsPublicationError(val.reason_code)
    if not val.polygon_parts:
        raise NewsPublicationError("missing_operational_polygon_parts")
    try:
        provenance = OperationalFootprintProvenance(
            source=provenance_source,
            source_checksum=provenance_checksum,
            geometry_sha256=canonical_sha256(val.geojson),
            parent_boundary_sha256=canonical_sha256(mapping(parent_boundary)) if parent_boundary is not None else None,
        )
    except (ValidationError, ValueError, TypeError) as exc:
        raise NewsPublicationError("invalid_geometry_provenance") from exc
    digest = canonical_sha256({
        "operation": "activate_footprint", "case_id": case_id,
        "expected_revision": expected_revision, "actor_user_id": actor_user_id,
        "geometry_srid": geometry_srid, "evidence_record_id": evidence_record_id,
        "estimated_road": estimated_road,
        "provenance": provenance.model_dump(mode="json"),
        "policy_fingerprint": policy.fingerprint, "pipeline_version": policy.pipeline_version,
        "auditor_identity": policy.auditor_identity,
    })
    request_id = request_id or uuid5(NAMESPACE_URL, f"lanes-news-footprint:{digest}")
    publication_lock(db, canonical_sha256({"request_id": str(request_id)}))
    existing = existing_request(db, request_id, digest)
    if existing:
        return existing

    # Read immutable evidence before acquiring the shared incident lock, then
    # lock/recheck the case in the same order as publication and staff writes.
    previous = latest_decision(db, case_id)
    if previous is None or previous.public_state not in ("active_alert", "active_zone"):
        raise NewsPublicationError("claim_not_active_alert_or_zone")
    try:
        prev_snapshot = NewsDecisionSnapshot.model_validate(previous.snapshot)
    except ValidationError as exc:
        raise NewsPublicationError("invalid_decision_snapshot") from exc
    if prev_snapshot.evaluation_id is None:
        raise NewsPublicationError("activation_evaluation_required")
    sources = sources if sources is not None else load_news_sources()
    evaluation, source, run, version, article, claim, audit, failure = _load(
        db, prev_snapshot.evaluation_id, policy, now, sources,
    )
    if failure:
        raise NewsPublicationError(failure)
    if audit is None or audit.evidence is None:
        raise NewsPublicationError("independent_audit_unavailable")
    if (previous.evaluation_id != evaluation.id or prev_snapshot.claim_source_id != source.id
            or prev_snapshot.input_sha256 != version.input_fingerprint
            or prev_snapshot.claim_sha256 != source.claim_sha256
            or prev_snapshot.incident_identity != _incident(claim)
            or prev_snapshot.article_id != article.article_id
            or prev_snapshot.policy_fingerprint != policy.fingerprint):
        raise NewsPublicationError("activation_evidence_identity_mismatch")
    publication_lock(db, _incident(claim))
    case = lock_case(db, case_id)
    if case.revision != expected_revision:
        raise NewsPublicationError("stale_case_revision", 409, revision=case.revision)
    current = latest_decision(db, case.id)
    if current is None or current.id != previous.id or current.revision != case.revision:
        raise NewsPublicationError("stale_case_revision", 409, revision=case.revision)
    if (prev_snapshot.public is None or prev_snapshot.public.case_id != case.id
            or prev_snapshot.public.decision_id != previous.id
            or prev_snapshot.public.revision != case.revision
            or prev_snapshot.public.observed_at != claim.event_time_resolved
            or previous.observed_at != claim.event_time_resolved):
        raise NewsPublicationError("activation_evidence_identity_mismatch")
    if claim.condition not in ("active", "rising"):
        raise NewsPublicationError("claim_not_current_flood")
    if _clearance_supersedes(db, claim, article) or _wet_supersedes(db, claim, article):
        raise NewsPublicationError("source_observation_superseded")
    zone_attributes = _operational_zone_attributes(claim, audit)
    val, provenance = approve_news_footprint(db, footprint, geometry_srid=geometry_srid, claim=claim,
        context=_footprint_context(source, version, article, claim), now=now, actor_user_id=actor_user_id,
        review_id=str(request_id) if actor_user_id is not None else None, record_id=evidence_record_id,
        source=provenance_source, checksum=provenance_checksum, caller_parent=parent_boundary,
        estimated_road=estimated_road)

    decision_id = reserve_decision_id(db)
    sev_val = zone_attributes["severity_override"]
    expiry_time = claim.event_time_resolved + timedelta(hours=2)

    linked_zone_ids: list[int] = []
    event_obj = None
    for idx, part in enumerate(val.polygon_parts):
        poly_in = PolygonGeometry(**part)
        zone_in = FloodAvoidanceZoneCreate(
            geometry=poly_in,
            source_geometry=(provenance.binding.estimated_road.component_centerlines[idx]
                             if estimated_road else None),
            is_active=True,
            expires_at=expiry_time,
        )
        if idx == 0:
            event_obj, created_zone = create_verified_event_with_zone(
                db,
                zone_in,
                peak_severity=sev_val,
                peak_depth=claim.depth_canonical,
                acted_by_user_id=actor_user_id,
                zone_attributes=zone_attributes,
                commit=False,
                first_reported_at=claim.event_time_resolved,
            )
            linked_zone_ids.append(created_zone.id)
        else:
            created_zone = create_flood_avoidance_zone(db, zone_in, event_id=event_obj.id, commit=False)
            for attribute, value in zone_attributes.items():
                setattr(created_zone, attribute, value)
            linked_zone_ids.append(created_zone.id)

    public = _public(
        case, decision_id, article, claim, audit, now, sources,
        geometry_precision="operational_polygon",
        display_geojson=val.geojson,
        affects_routing=True,
        geometry_basis="estimated_road_corridor" if estimated_road else "verified_current_footprint",
    )
    snapshot = _snapshot(
        source, version, claim, policy, digest, evaluation_id=evaluation.id,
        previous=previous, public=public, target=case.id,
        geometry_reason=("estimated_road_corridor" if estimated_road else
                         "staff_reviewed_footprint" if actor_user_id is not None else "verified_incident_footprint"),
        linked_zone_ids=linked_zone_ids,
        operational_provenance=provenance,
    )
    decision = _write(db, case, decision_id, request_id, snapshot, now,
        actor_kind="staff" if actor_user_id is not None else "automatic",
        actor_id=actor_user_id,
        operation="correct" if actor_user_id is not None else "evaluate",
        state="active_zone", review="resolved",
        reason="estimated_road_corridor" if estimated_road else "verified_operational_footprint",
        observed=claim.event_time_resolved, expiry=expiry_time)

    for z_id in linked_zone_ids:
        db.add(NewsClaimZoneLink(decision_id=decision_id, zone_id=z_id, relation="created", created_at=now))
    db.flush()

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
            outcome = "cleared" if operation == "clear" else "published" if state in ("active_alert", "active_zone") else "needs_review"
            setattr(summary, outcome, getattr(summary, outcome) + 1)
        except NewsPublicationError as exc:
            summary.skipped.append({"evaluation_id": evaluation_id, "reason_code": exc.code})
        except SQLAlchemyError:
            summary.skipped.append({"evaluation_id": evaluation_id, "reason_code": "publication_storage_unavailable"})
    with session_factory() as db:
        cases = list(db.scalars(select(NewsClaimCase.id).join(NewsClaimDecision, NewsClaimDecision.case_id == NewsClaimCase.id)
            .where(NewsClaimDecision.revision == NewsClaimCase.revision,
                NewsClaimDecision.public_state.in_(("active_alert", "active_zone")), NewsClaimDecision.expires_at <= clock())
            .order_by(NewsClaimCase.id).limit(limit)))
    for case_id in cases:
        try:
            with session_factory() as db, db.begin():
                expired = expire_case(db, case_id, now=clock()) is not None
            if expired:
                summary.expired += 1
        except NewsPublicationError as exc:
            summary.skipped.append({"case_id": case_id, "reason_code": exc.code})
        except SQLAlchemyError:
            summary.skipped.append({"case_id": case_id, "reason_code": "maintenance_storage_unavailable"})
    return summary
