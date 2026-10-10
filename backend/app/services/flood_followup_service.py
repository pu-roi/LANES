"""Record and review private citizen claims without changing operational floods."""
from datetime import datetime, timezone
from typing import Any

from geoalchemy2.shape import to_shape
from shapely.errors import ShapelyError
from sqlalchemy.orm import Session

from app.crud import flood_followup as store
from app.models.audit import AuditLog
from app.models.report import FloodReport, ReportSource, ReportStatus
from app.models.user import User
from app.schemas.common import ensure_utc, serialize_utc_datetime
from app.schemas.flood_followup import (
    FloodFollowupCreate, FloodFollowupResponse, FloodFollowupReviewCreate,
    FloodFollowupReviewResponse, FloodFollowupsExportResponse,
    OwnerFloodFollowupsResponse, StaffFloodFollowupsResponse,
)
from app.services.citizen_approval_service import geometry_hash
from app.services.flood_feature_service import capture_features

CONTRACT_VERSION = 1
PASIG_CITY_ALIASES = frozenset({"pasig", "pasig city", "city of pasig"})


class FollowupError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def require_active_user(user: User) -> None:
    if not user.is_active or user.deleted_at is not None:
        raise FollowupError(403, "An active account is required.")


def require_staff_permission(user: User, *, write: bool) -> None:
    require_active_user(user)
    role = user.role
    permissions = getattr(role, "permissions", None)
    allowed = {"full"} if write else {"view", "full"}
    if (role is None or role.name == "Commuter" or not isinstance(permissions, dict)
            or permissions.get("reports") not in allowed):
        raise FollowupError(403, "Your role does not allow this follow-up action.")


def _owned_report(db: Session, report_id: int, user: User, *, lock: bool = False) -> FloodReport:
    require_active_user(user)
    report = store.get_report(db, report_id, lock=lock)
    if report is None or report.deleted_at is not None or report.user_id != user.id:
        raise FollowupError(404, "Report not found.")
    return report


def _ineligibility(report: FloodReport) -> str | None:
    if report.source != ReportSource.USER_REPORT:
        return "Follow-ups are available only for your citizen reports."
    if " ".join((report.city or "").casefold().split()) not in PASIG_CITY_ALIASES:
        return "Follow-ups currently cover reports in Pasig City."
    if report.status == ReportStatus.REJECTED:
        return "Rejected reports cannot receive follow-ups."
    if not (report.human_readable_location or "").strip() or report.geometry is None:
        return "The original report needs a recorded location and geometry."
    try:
        shape = to_shape(report.geometry)
        if getattr(report.geometry, "srid", None) != 4326 or shape.is_empty or not shape.is_valid:
            return "The original report needs valid location geometry in SRID 4326."
    except (TypeError, ValueError, ShapelyError):
        return "The original report geometry could not be validated."
    return None


def _location_snapshot(report: FloodReport) -> dict[str, Any]:
    return {"report_id": report.id, "city": report.city, "barangay": report.barangay,
        "human_readable_location": report.human_readable_location,
        "geometry_sha256": geometry_hash(report), "zone_id": report.zone_id, "event_id": report.event_id}


def _utc_string(value: datetime) -> str:
    return serialize_utc_datetime(ensure_utc(value).astimezone(timezone.utc))


def _original_provenance(db: Session, report: FloodReport) -> tuple[datetime | None, datetime | None, int | None]:
    # Only an explicitly recorded citizen observation is an original wet clock.
    # Report creation, zone expiry and event end never establish that observation.
    row = store.original_observation(db, report.id)
    if row is None:
        return None, None, None
    evidence = row.metadata_json or {}
    if evidence.get("user_id") != report.user_id or evidence.get("geometry_sha256") != geometry_hash(report):
        return None, None, None
    available_at = ensure_utc(row.created_at).astimezone(timezone.utc)
    value = evidence.get("observed_at")
    if not isinstance(value, str):
        return None, available_at, row.id
    try:
        observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None, available_at, row.id
    if observed.tzinfo is None or observed.utcoffset() is None:
        return None, available_at, row.id
    observed = observed.astimezone(timezone.utc)
    return (observed if observed <= datetime.now(timezone.utc) else None), available_at, row.id


def _response(row: AuditLog, review: AuditLog | None) -> FloodFollowupResponse:
    metadata = row.metadata_json
    review_response = None
    if review is not None:
        reviewed = review.metadata_json
        review_response = FloodFollowupReviewResponse(id=review.id,
            decision=reviewed["decision"], reviewer_id=reviewed["reviewer_id"],
            reviewed_at=review.created_at, evidence_text=reviewed["evidence_text"],
            same_location_verified=reviewed["same_location_verified"])
    return FloodFollowupResponse(id=row.id, request_id=metadata["request_id"],
        report_id=row.target_id, user_id=metadata["user_id"], condition=metadata["condition"],
        observed_at=metadata["observed_at"], submitted_at=row.created_at,
        evidence_text=metadata["evidence_text"], depth_cm=metadata["depth_cm"],
        source_url=metadata["source_url"], same_location_confirmed=metadata["same_location_confirmed"],
        location_snapshot=metadata["location_snapshot"], original_observed_at=metadata["original_observed_at"],
        original_available_at=metadata.get("original_available_at"),
        original_observation_audit_id=metadata.get("original_observation_audit_id"),
        review_state=review_response.decision if review_response else "pending", review=review_response,
        prediction_features=metadata.get("prediction_features"))


def list_owner_followups(db: Session, report_id: int, user: User) -> OwnerFloodFollowupsResponse:
    report = _owned_report(db, report_id, user)
    rows = store.report_followups(db, report.id)
    reviews = store.latest_reviews(db, [row.id for row in rows])
    reason = _ineligibility(report)
    if reason is None and len(rows) >= store.MAX_FOLLOWUPS_PER_REPORT:
        reason = "This report has reached its limit of 100 follow-ups."
    return OwnerFloodFollowupsResponse(follow_ups=[_response(row, reviews.get(row.id)) for row in rows],
        can_submit=reason is None, ineligibility_reason=reason)


def submit_followup(db: Session, report_id: int, user: User,
                    payload: FloodFollowupCreate) -> FloodFollowupResponse:
    # Serialize all submissions on the report: both request reuse and the bound
    # are enforced before the single audit append in the same transaction.
    report = _owned_report(db, report_id, user, lock=True)
    submitted = payload.model_dump(mode="json")
    submitted["observed_at"] = _utc_string(payload.observed_at)
    existing = store.find_request(db, report.id, str(payload.request_id))
    if existing is not None:
        if any(existing.metadata_json.get(key) != value for key, value in submitted.items()):
            raise FollowupError(409, "This request ID was already used with different observation details.")
        response = _response(existing, store.latest_reviews(db, [existing.id]).get(existing.id))
        db.rollback()  # Release the serialization lock; no retry writes.
        return response
    reason = _ineligibility(report)
    if reason is not None:
        raise FollowupError(409, reason)
    if len(store.report_followups(db, report.id)) >= store.MAX_FOLLOWUPS_PER_REPORT:
        raise FollowupError(409, "This report has reached its limit of 100 follow-ups.")
    now = datetime.now(timezone.utc)
    if payload.observed_at > now:
        raise FollowupError(422, "Observation time cannot be in the future.")
    original_clock, original_available_at, original_audit_id = _original_provenance(db, report)
    if original_clock is not None and payload.observed_at < original_clock:
        raise FollowupError(422, "A follow-up cannot precede the original recorded observation.")
    metadata = {**submitted, "contract_version": CONTRACT_VERSION, "user_id": user.id,
        "submitted_at": _utc_string(now), "location_snapshot": _location_snapshot(report),
        "original_observed_at": _utc_string(original_clock) if original_clock else None,
        "original_available_at": _utc_string(original_available_at) if original_available_at else None,
        "original_observation_audit_id": original_audit_id,
        "source_claim_only": True, "model_admitted": False}
    metadata["prediction_features"]=capture_features(report.geometry,None,observed_at=payload.observed_at,
        now=now,measured_depth_cm=payload.depth_cm)
    row = store.append_audit(db, action=store.OBSERVATION_ACTION, target_table="flood_reports",
        target_id=report.id, actor_id=user.id, metadata=metadata, created_at=now)
    response = _response(row, None)
    db.commit()
    return response


def list_staff_followups(db: Session, user: User, *, review_state: str = "pending",
                        limit: int = 50, before_id: int | None = None) -> StaffFloodFollowupsResponse:
    require_staff_permission(user, write=False)
    if review_state not in {"pending", "accepted", "rejected", "all"}:
        raise FollowupError(422, "Invalid follow-up review state.")
    if not 1 <= limit <= 100 or (before_id is not None and before_id < 1):
        raise FollowupError(422, "Use a limit between 1 and 100 and a positive pagination ID.")
    rows = store.staff_followups(db, review_state, limit, before_id)
    has_more = len(rows) > limit
    rows = rows[:limit]
    reviews = store.latest_reviews(db, [row.id for row in rows])
    return StaffFloodFollowupsResponse(follow_ups=[_response(row, reviews.get(row.id)) for row in rows],
        next_before_id=rows[-1].id if has_more and rows else None)


def review_followup(db: Session, followup_id: int, user: User,
                    payload: FloodFollowupReviewCreate) -> FloodFollowupResponse:
    require_staff_permission(user, write=True)
    row = store.get_followup(db, followup_id, lock=True)
    if row is None:
        raise FollowupError(404, "Follow-up not found.")
    metadata = row.metadata_json
    if user.id == metadata["user_id"]:
        raise FollowupError(403, "You cannot review your own follow-up.")
    if store.latest_reviews(db, [row.id]).get(row.id) is not None:
        raise FollowupError(409, "This follow-up already has an immutable review.")
    report = store.get_report(db, row.target_id, lock=True)
    if payload.decision == "accepted":
        if (report is None or report.deleted_at is not None or _ineligibility(report) is not None
                or _location_snapshot(report) != metadata["location_snapshot"]):
            raise FollowupError(409, "The original report location or event link changed; this claim cannot be accepted.")
    now = datetime.now(timezone.utc)
    review_metadata = {**payload.model_dump(mode="json"), "contract_version": CONTRACT_VERSION,
        "followup_id": row.id, "report_id": row.target_id, "reviewer_id": user.id,
        "reviewed_at": _utc_string(now), "source_claim_only": True, "model_admitted": False}
    review = store.append_audit(db, action=store.REVIEW_ACTION, target_table="audit_logs",
        target_id=row.id, actor_id=user.id, metadata=review_metadata, created_at=now)
    original_event_id = metadata["location_snapshot"]["event_id"]
    if payload.decision == "accepted" and original_event_id is not None:
        condition = "still flooded" if metadata["condition"] == "still_flooded" else "subsided"
        # Preserve only safe traceability on the readable timeline. The private
        # citizen text, source URL and staff review evidence stay in audit logs.
        store.append_timeline(db, event_id=original_event_id,
            observed_at=datetime.fromisoformat(metadata["observed_at"].replace("Z", "+00:00")),
            summary=f"Staff reviewed a same-location citizen claim: {condition}. Operational status is unchanged.",
            snapshot={"followup_id": row.id, "report_id": row.target_id,
                "condition": metadata["condition"], "observed_at": metadata["observed_at"],
                "reviewed_at": _utc_string(now), "source_claim_only": True, "model_admitted": False})
    response = _response(row, review)
    if report is not None and report.zone_id is not None:
        from app.services.pasig_ml_expiry_service import apply_zone_policy
        apply_zone_policy(db, report.zone_id, now=now)
    db.commit()
    return response


def export_staff_followups(db: Session, user: User, *, review_state: str = "all",
                          limit: int = 100, before_id: int | None = None) -> FloodFollowupsExportResponse:
    page = list_staff_followups(db, user, review_state=review_state, limit=limit, before_id=before_id)
    return FloodFollowupsExportResponse(generated_at=datetime.now(timezone.utc),
        follow_ups=page.follow_ups, next_before_id=page.next_before_id)
