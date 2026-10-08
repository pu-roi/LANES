"""Staff review timing from recorded case evidence; never a clearance engine."""
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.crud import flood_followup as evidence_store
from app.crud import flood_review_suggestion as store
from app.crud.zone_update import OBSERVATION_ACTION as ZONE_OBSERVATION, REVIEW_ACTION as ZONE_REVIEW
from app.models.audit import AuditLog
from app.models.report import FloodReport, ReportStatus, FloodEventStatus
from app.models.user import User
from app.schemas.common import ensure_utc
from app.schemas.flood_review_suggestion import (
    CaseReviewSuggestion, ReviewSuggestionCreate, ReviewSuggestionQueue,
    SavedReviewSuggestion, WetEvidence,
)
from app.schemas.flood_subsidence import DurationPreviewRequest
from app.services.flood_followup_service import (
    FollowupError, _ineligibility, _location_snapshot, require_staff_permission,
)
from app.services.flood_subsidence_prediction_service import preview_subsidence


def _clock(value: Any, available_at: datetime, now: datetime) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if observed.tzinfo is None or observed.utcoffset() is None:
        return None
    observed = observed.astimezone(timezone.utc)
    return observed if observed <= available_at <= now else None


def _snapshot(report: FloodReport) -> dict[str, Any]:
    zone = report.avoidance_zone
    return {**_location_snapshot(report), "user_id": report.user_id,
        "report_status": report.status.value,
        "zone_version": ensure_utc(zone.updated_at).isoformat() if zone else None}


def _closed(report: FloodReport, now: datetime) -> bool:
    zone, event = report.avoidance_zone, report.flood_event
    return (report.deleted_at is not None or report.status == ReportStatus.REJECTED
        or (zone is not None and not zone.is_active
            and (zone.expires_at is None or ensure_utc(zone.expires_at) > now))
        or (event is not None and event.status != FloodEventStatus.ACTIVE))


def _wet_evidence(db: Session, report: FloodReport, now: datetime) -> tuple[list[WetEvidence], str | None]:
    wet: list[WetEvidence] = []
    original = evidence_store.original_observation(db, report.id)
    if original is not None:
        data = original.metadata_json or {}
        available = ensure_utc(original.created_at)
        observed = _clock(data.get("observed_at"), available, now)
        if (observed is not None and data.get("user_id") == report.user_id
                and data.get("geometry_sha256") == _location_snapshot(report)["geometry_sha256"]
                and data.get("road_validated") is True):
            wet.append(WetEvidence(audit_id=original.id, observed_at=observed,
                available_at=available, provenance="original_citizen_observation"))
    rows = evidence_store.report_followups(db, report.id)
    reviews = evidence_store.latest_reviews(db, [row.id for row in rows])
    snapshot = _location_snapshot(report)
    for row in rows:
        review = reviews.get(row.id)
        data = row.metadata_json
        if (review is None or review.metadata_json.get("decision") != "accepted"
                or review.metadata_json.get("same_location_verified") is not True
                or review.admin_id == data.get("user_id")
                or ensure_utc(review.created_at) > now or data.get("user_id") != report.user_id
                or data.get("location_snapshot") != snapshot):
            continue
        available = ensure_utc(row.created_at)
        observed = _clock(data.get("observed_at"), available, now)
        if observed is None:
            continue
        if data.get("condition") == "subsided":
            # A recovery/recurrence needs a separate episode decision; never
            # silently stretch the model across an accepted subsidence claim.
            return [], "An accepted subsided follow-up needs a clearance or episode review."
        if data.get("condition") == "still_flooded":
            wet.append(WetEvidence(audit_id=row.id, review_id=review.id,
                observed_at=observed, available_at=available, provenance="accepted_owner_followup"))
    wet.sort(key=lambda item: (item.observed_at, item.audit_id))
    return wet, None


def _evidence_signature(wet: list[WetEvidence]) -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in wet]


def _later_signal(db: Session, report: FloodReport, issued_at: datetime) -> bool:
    # Untimed citizen zone updates still merit staff attention. They do not
    # become a wet reference or a model training outcome.
    followup = db.scalar(select(AuditLog.id).where(
        AuditLog.action_type == evidence_store.OBSERVATION_ACTION,
        AuditLog.target_table == "flood_reports", AuditLog.target_id == report.id,
        AuditLog.created_at > issued_at).limit(1))
    if followup is not None:
        return True
    if report.zone_id is None:
        return False
    return db.scalar(select(AuditLog.id).where(AuditLog.action_type == ZONE_OBSERVATION,
        AuditLog.target_table == "flood_avoidance_zones", AuditLog.target_id == report.zone_id,
        AuditLog.created_at > issued_at).limit(1)) is not None


def _pending_signal(db: Session, report: FloodReport) -> bool:
    review = aliased(AuditLog)
    for action, target, target_id, review_action in (
        (evidence_store.OBSERVATION_ACTION, "flood_reports", report.id, evidence_store.REVIEW_ACTION),
        (ZONE_OBSERVATION, "flood_avoidance_zones", report.zone_id, ZONE_REVIEW),
    ):
        if target_id is None:
            continue
        reviewed = select(review.id).where(review.action_type == review_action,
            review.target_table == "audit_logs", review.target_id == AuditLog.id).exists()
        if db.scalar(select(AuditLog.id).where(AuditLog.action_type == action,
            AuditLog.target_table == target, AuditLog.target_id == target_id, ~reviewed).limit(1)) is not None:
            return True
    return False


def _case(db: Session, report: FloodReport, user: User, now: datetime,
          saved: AuditLog | None = None) -> CaseReviewSuggestion:
    reason = _ineligibility(report)
    closed = _closed(report, now)
    zone = report.avoidance_zone
    stale = zone is not None and zone.expires_at is not None and ensure_utc(zone.expires_at) <= now
    wet, evidence_reason = _wet_evidence(db, report, now) if reason is None and not closed else ([], None)
    reason = reason or ("This case is closed." if closed else None)
    reason = reason or evidence_reason or ("A validated original observation or accepted still-flooded follow-up with an explicit observation time is required." if not wet else None)
    # These are study-scope checks; no claim of geographic validation.
    if reason is None and (report.barangay or "").strip().casefold() not in {"maybunga", "dela paz", "santolan", "sta. lucia"}:
        reason = "This barangay is outside the current experimental model scope."
    pending = _pending_signal(db, report)
    rows = store.suggestions(db, report.id) if saved is None else [saved]
    row = rows[0] if rows else None
    suggestion = SavedReviewSuggestion.model_validate(row.metadata_json["suggestion"]) if row else None
    state, state_reason = "no_suggestion", None
    if suggestion is not None:
        if closed:
            state, state_reason = "case_closed", "The operational case is closed; the saved suggestion is historical."
        elif (reason is not None or _snapshot(report) != suggestion.location_snapshot
                or row.metadata_json["evidence_signature"] != _evidence_signature(wet)):
            state, state_reason = "evidence_changed", "Case correspondence or reviewed evidence changed. Inspect it before using this suggestion."
        elif pending or _later_signal(db, report, suggestion.issued_at):
            state, state_reason = "followup_received", "A later citizen observation is available for review."
        elif stale:
            state, state_reason = "evidence_stale", "The evidence deadline has passed. Obtain a current condition update; expiry does not establish subsidence."
        elif suggestion.suggested_review_at <= now:
            state, state_reason = "due", "The suggested review time has arrived. Current evidence is still needed."
        else:
            state = "scheduled"
    return CaseReviewSuggestion(report_id=report.id, location=report.human_readable_location,
        zone_id=report.zone_id, can_issue=reason is None and not pending and not stale and user.role.permissions.get("reports") == "full",
        ineligibility_reason=reason or ("Review pending citizen observations before saving another suggestion." if pending else None)
            or ("Current operational evidence is stale. Review and refresh the case before another suggestion." if stale else None), reference=wet[0] if wet else None, latest_wet=wet[-1] if wet else None,
        suggestion=suggestion, state=state, state_reason=state_reason, evaluated_at=now)


def get_case(db: Session, report_id: int, user: User) -> CaseReviewSuggestion:
    require_staff_permission(user, write=False)
    report = evidence_store.get_report(db, report_id)
    if report is None or report.deleted_at is not None:
        raise FollowupError(404, "Report not found.")
    return _case(db, report, user, datetime.now(timezone.utc))


def issue_suggestion(db: Session, report_id: int, user: User,
                     payload: ReviewSuggestionCreate) -> CaseReviewSuggestion:
    require_staff_permission(user, write=True)
    report = evidence_store.get_report(db, report_id, lock=True)
    if report is None or report.deleted_at is not None:
        raise FollowupError(404, "Report not found.")
    rows = store.suggestions(db, report.id)
    request = payload.model_dump(mode="json")
    for row in rows:
        if row.metadata_json["request"]["request_id"] == request["request_id"]:
            if row.metadata_json["request"] != request or row.admin_id != user.id:
                raise FollowupError(409, "This request ID already belongs to another suggestion request.")
            result = _case(db, report, user, datetime.now(timezone.utc), saved=row)
            db.rollback()
            return result
    if len(rows) >= store.MAX_SUGGESTIONS_PER_REPORT:
        raise FollowupError(409, "This case has reached its limit of 100 saved suggestions.")
    if not payload.acknowledge_research_limitations or not payload.assume_continuous_wet:
        raise FollowupError(422, "Acknowledge the experimental limitations and uninterrupted wet episode assumption.")
    now = datetime.now(timezone.utc)
    case = _case(db, report, user, now)
    if not case.can_issue:
        raise FollowupError(409, case.ineligibility_reason or "This case cannot receive a suggestion.")
    preview = preview_subsidence(DurationPreviewRequest(city=report.city, barangay=report.barangay,
        reference_at=case.reference.observed_at, prediction_as_of_at=now,
        reference_policy="first_recorded_wet_in_episode", acknowledge_research_limitations=True,
        assume_continuous_wet=True), now=now)
    if preview.status != "research_estimate":
        raise FollowupError(409, f"No experimental suggestion is available: {preview.abstention_reason}.")
    median = next(item for item in preview.quantiles if item.quantile == 0.5)
    row = evidence_store.append_audit(db, action=store.SUGGESTION_ACTION, target_table="flood_reports",
        target_id=report.id, actor_id=user.id, metadata={}, created_at=now)
    suggestion = SavedReviewSuggestion(id=row.id, report_id=report.id, request_id=payload.request_id,
        issued_at=now, issued_by=user.id, suggested_review_at=median.estimated_reported_subsidence_at,
        reference=case.reference, latest_wet=case.latest_wet, location_snapshot=_snapshot(report),
        model=preview.model, quantiles=preview.quantiles)
    wet, _ = _wet_evidence(db, report, now)
    row.metadata_json = {"contract_version": 1, "request": request,
        "suggestion": suggestion.model_dump(mode="json"), "evidence_signature": _evidence_signature(wet)}
    db.flush()
    result = _case(db, report, user, now, saved=row)
    db.commit()
    return result


def review_queue(db: Session, user: User, *, limit: int = 25, before_id: int | None = None,
                 actionable_only: bool = True) -> ReviewSuggestionQueue:
    require_staff_permission(user, write=False)
    now = datetime.now(timezone.utc)
    rows = store.latest_page(db, limit=limit, before_id=before_id)
    has_more = len(rows) > limit
    rows = rows[:limit]
    cases = []
    for row in rows:
        report = evidence_store.get_report(db, row.target_id)
        if report is None or report.deleted_at is not None:
            continue
        case = _case(db, report, user, now, saved=row)
        if not actionable_only or case.state in {"due", "evidence_changed", "followup_received", "evidence_stale"}:
            cases.append(case)
    return ReviewSuggestionQueue(cases=cases, next_before_id=rows[-1].id if rows and has_more else None,
        evaluated_at=now, page_scanned=len(rows))
