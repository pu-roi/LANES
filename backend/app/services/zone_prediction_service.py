"""Automatically resolve stored geometry/evidence; never mutate operational data."""
from datetime import datetime, timezone
import hashlib

from geoalchemy2.shape import to_shape
from shapely.errors import ShapelyError
from shapely.geometry import shape
from sqlalchemy.orm import Session

from app.crud import zone_prediction as store
from app.crud import flood_followup as evidence_store
from app.models.report import FloodAvoidanceZone, FloodReport, FloodEventStatus, ReportSource, ReportStatus
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.flood_subsidence import DurationPreviewRequest
from app.schemas.news_publication import NewsDecisionSnapshot
from app.schemas.zone_prediction import ZonePrediction, ZonePredictionEvidence
from app.services.flood_location_service import get_flood_location_provider
from app.services.flood_followup_service import FollowupError, require_staff_permission
from app.services.flood_review_suggestion_service import _clock, _pending_signal, _wet_evidence
from app.services.flood_subsidence_prediction_service import (
    load_research_model, model_status, preview_subsidence, research_barangay_name,
    pasig_prediction_barangays,
)
from app.services.news_publication_service import public_projection
from app.services.spatial_review_grouping import MAX_GROUP_DISTANCE_M, locality, utc
from app.services.zone_update_service import require_staff_permission as require_zone_reader
from app.services.flood_feature_service import capture_features


def feature_context(db: Session, zone_id: int, user: User) -> dict:
    require_staff_permission(user, write=False)
    require_zone_reader(user, write=False)
    zone = store.get_zone(db,zone_id)
    if zone is None:
        raise FollowupError(404,"Flood Zone not found.")
    depth = zone.depth_override if zone.depth_override is not None else zone.depth
    return capture_features(zone.geometry,depth,include_environment=True)


def resolve_location(zone: FloodAvoidanceZone) -> tuple[dict, list[str]]:
    provider = get_flood_location_provider()
    result = {"boundary_revision": provider.revision, "barangays": [], "city": None}
    try:
        if zone.geometry.srid != 4326:
            return result, ["The zone needs valid geometry in SRID 4326."]
        polygon = to_shape(zone.geometry)
        if polygon.is_empty or not polygon.is_valid or polygon.geom_type not in {"Polygon", "MultiPolygon"}:
            return result, ["The zone geometry is invalid."]
        point = polygon.representative_point()
        result["coordinates"] = (point.x, point.y)
        if provider.error:
            return result, ["The reviewed barangay boundary catalog is unavailable."]
        if not provider.city_boundary.covers(polygon):
            return result, ["The zone extends outside the reviewed Pasig city boundary."]
        # Resolve the entire authoritative avoidance boundary, not a guessed pin.
        covered = [record for record, boundary in provider.records.values() if boundary.covers(polygon)]
        if len(covered) == 1:
            result.update(city="Pasig" if locality(covered[0].city) == "pasig" else covered[0].city,
                barangays=[covered[0].barangay], location_policy="single_barangay")
            return result, []
        intersecting = [record for record, boundary in provider.records.values()
            if boundary.intersection(polygon).area > 0]
        result.update(city="Pasig" if intersecting and all(locality(r.city) == "pasig" for r in intersecting) else None,
            barangays=sorted({r.barangay for r in intersecting}))
        if intersecting and result["city"] == "Pasig":
            result["location_policy"] = "pooled_pasig_multi_barangay"
            return result, []
        return result, ["No reviewed barangay boundary covers this zone."]
    except (TypeError, ValueError, AttributeError, ShapelyError):
        return result, ["The zone geometry could not be validated."]


def _news_evidence(db: Session, zone: FloodAvoidanceZone, now: datetime, *, ignore_deadline: bool = False) -> tuple[list[ZonePredictionEvidence], list[str]]:
    current = store.current_news(db, zone.id)
    if len(current) > store.MAX_RECORDS:
        return [], ["This zone has too many source links to resolve automatically."]
    wet, reasons = [], []
    for decision in current:
        public = public_projection(decision, now, automatic_expiry_enabled=not ignore_deadline)
        if (public is None or public.status != "Active" or not public.affects_routing
                or decision.public_state != "active_zone" or decision.review_state != "resolved"):
            reasons.append("Linked news evidence is expired, closed or awaiting review.")
            continue
        snapshot = NewsDecisionSnapshot.model_validate(decision.snapshot)
        history = store.news_history(db, decision.case_id)
        if len(history) > store.MAX_RECORDS:
            reasons.append("This news episode has too much history to resolve automatically.")
            continue
        for row in history:
            if row.operation in {"clear", "expire", "reject", "reopen"}:
                break
            saved = NewsDecisionSnapshot.model_validate(row.snapshot)
            if saved.incident_identity != snapshot.incident_identity:
                break
            claim = saved.public
            if (row.public_state != "active_zone" or row.review_state != "resolved"
                    or zone.id not in saved.linked_zone_ids or claim is None or not claim.affects_routing
                    or saved.geometry_reason not in {"verified_incident_footprint", "staff_reviewed_footprint"}):
                continue
            if not claim.display_geojson or not shape(claim.display_geojson).covers(to_shape(zone.geometry)):
                reasons.append("Linked news geometry no longer matches the zone footprint.")
                break
            available = utc(row.decided_at)
            observed = _clock(row.observed_at.isoformat() if row.observed_at else None, available, now)
            if observed is not None and claim.observed_at == row.observed_at:
                wet.append(ZonePredictionEvidence(source_kind="news_decision", source_id=row.id,
                    observed_at=observed, available_at=available))
    return wet, reasons


def _submission_source(db: Session, report: FloodReport, zone: FloodAvoidanceZone,
                       now: datetime) -> tuple[AuditLog, AuditLog] | None:
    """Immutable untimed submission + matching approval; never an observed onset."""
    original = evidence_store.original_observation(db, report.id)
    approval = store.submission_approval(db, report.id)
    if original is None or approval is None or report.approved_at is None:
        return None
    data, decision = original.metadata_json or {}, approval.metadata_json or {}
    if (data.get("observed_at") is not None or data.get("user_id") != report.user_id
            or data.get("road_validated") is not True
            or data.get("geometry_sha256") != hashlib.sha256(to_shape(report.geometry).wkb).hexdigest()
            or approval.admin_id is None or decision.get("report_id") != report.id
            or decision.get("zone_id") != zone.id
            or not (utc(report.created_at) <= utc(original.created_at) <= utc(report.approved_at)
                    <= utc(approval.created_at) <= now)
            or utc(report.updated_at) > utc(approval.created_at)
            or utc(zone.updated_at) > utc(approval.created_at)
            or evidence_store.report_followups(db, report.id)):
        return None
    return original, approval


def predict_zone(db: Session, zone_id: int, user: User, *, now: datetime | None = None) -> ZonePrediction:
    require_staff_permission(user, write=False)
    require_zone_reader(user, write=False)
    return resolve_zone_prediction(db, zone_id, now=now)


def resolve_zone_prediction(db: Session, zone_id: int, *, now: datetime | None = None,
                            ignore_deadline: bool = False,
                            recover_issuance: bool = False) -> ZonePrediction:
    """Validate current sources; expiry alone may recover their original forecast.

    Recovery never moves the qualification clock into the past. The preview
    still validates reference-to-issuance age using the recorded source clocks.
    Public research callers retain their current-evidence staleness checks.
    """
    zone = store.get_zone(db, zone_id)
    if zone is None:
        raise FollowupError(404, "Flood Zone not found.")
    clock = now or datetime.now(timezone.utc)
    location, reasons = resolve_location(zone)
    result = ZonePrediction(zone_id=zone.id, state="unavailable", evaluated_at=clock, **location)
    if result.coordinates is None:
        return result.model_copy(update={"reasons": reasons})
    if not zone.is_active or (zone.flood_event and zone.flood_event.status != FloodEventStatus.ACTIVE):
        return result.model_copy(update={"state": "inactive", "reasons": ["The flood zone or incident is inactive."]})
    if not ignore_deadline and zone.expires_at is not None and utc(zone.expires_at) <= clock:
        return result.model_copy(update={"state": "expired", "reasons": ["Zone evidence has expired; current flood conditions need confirmation."]})
    artifact, checksum = load_research_model()
    result.model = model_status(artifact, checksum)
    if artifact is None:
        reasons.append("The backend research model is unavailable.")
    names = [research_barangay_name(name, pasig_prediction_barangays()) for name in result.barangays]
    barangay = names[0] if names and all(names) else None
    if result.location_policy == "pooled_pasig_multi_barangay":
        result.warnings = ["Shared Pasig estimate across these barangays; separate street or barangay effects are not learned, and local accuracy is unverified."]
    if result.city and locality(result.city) != "pasig":
        reasons.append("This location is outside the Pasig model scope.")
    if artifact and barangay is None:
        reasons.append("The zone needs recognized Pasig barangay identities.")
    reports = store.linked_reports(db, zone.id)
    result.nearby_report_count = store.nearby_report_count(db, zone, distance_metres=MAX_GROUP_DISTANCE_M)
    wet, evidence_reasons, submissions = [], [], []
    if len(reports) > store.MAX_RECORDS:
        evidence_reasons.append("This zone has too many report links to resolve automatically.")
        reports = []
    for report in reports:
        if (report.status != ReportStatus.APPROVED or report.source != ReportSource.USER_REPORT
                or report.event_id != zone.event_id or zone.event_id is None
                or report.geometry is None or report.geometry.srid != 4326
                or not to_shape(zone.geometry).covers(to_shape(report.geometry))):
            evidence_reasons.append("A linked report needs reviewed matching geometry and incident correspondence.")
            continue
        if report.city and result.city and locality(report.city) != locality(result.city):
            evidence_reasons.append("A report's recorded city conflicts with the zone geometry.")
            continue
        if (report.barangay and names and research_barangay_name(report.barangay, pasig_prediction_barangays()) not in names):
            evidence_reasons.append("A report's recorded barangay conflicts with the zone geometry.")
            continue
        observations, rejection = _wet_evidence(db, report, clock)
        if rejection:
            evidence_reasons.append(rejection)
        if _pending_signal(db, report):
            evidence_reasons.append("New citizen evidence needs review before recalculating this episode.")
        if not observations and not rejection:
            source = _submission_source(db, report, zone, clock)
            if source is not None:
                submissions.append((source[0], source[1], report.id))
        wet.extend(ZonePredictionEvidence(source_kind=item.provenance, source_id=item.audit_id,
            report_id=report.id, observed_at=item.observed_at, available_at=item.available_at) for item in observations)
    news, news_reasons = (_news_evidence(db, zone, clock, ignore_deadline=True) if ignore_deadline
                         else _news_evidence(db, zone, clock))
    wet.extend(news)
    evidence_reasons.extend(news_reasons)
    # Public spot observations are review signals, not whole-zone duration labels.
    from app.crud import zone_update as updates
    rows = updates.observations(db, zone.id, limit=store.MAX_RECORDS)
    reviews = updates.reviews(db, [row.id for row in rows]) if rows else {}
    latest_available = max((item.available_at for item in wet), default=None)
    if any((reviews.get(row.id) is None or reviews[row.id].metadata_json.get("decision") != "dismissed")
            and (latest_available is None or utc(row.created_at) >= latest_available) for row in rows):
        evidence_reasons.append("A later public condition update needs episode review; a spot report does not establish whole-zone clearance.")
    wet.sort(key=lambda item: (item.observed_at, item.source_kind, item.source_id))
    result.evidence = wet
    result.reference, result.latest_wet = (wet[0], wet[-1]) if wet else (None, None)
    if not wet:
        reasons.append("No qualified observation time is recorded for this zone; creation time is not a flood observation.")
        if result.nearby_report_count:
            reasons.append("Nearby reports were found, but require a reviewed same-zone and same-episode link before use.")
    reasons.extend(evidence_reasons)
    if reasons:
        # An unchanged official registration can exercise the model automatically,
        # but remains a separately labelled proxy simulation, not zone evidence.
        missing_clock = "No qualified observation time is recorded for this zone; creation time is not a flood observation."
        only_missing = all(reason == missing_clock or reason.startswith("Nearby reports were found") for reason in reasons)
        if not wet and not evidence_reasons and only_missing and artifact and barangay:
            if submissions and not store.zone_has_edits(db, zone):
                original, approval, report_id = min(submissions, key=lambda row: (utc(row[0].created_at), row[0].id))
                if recover_issuance or (clock-utc(original.created_at)).total_seconds()/60 <= artifact.lineage["reference_age_support_max_minutes"]:
                    simulation = preview_subsidence(DurationPreviewRequest(city=result.city, barangay=barangay,
                        footprint_barangays=result.barangays, reference_at=utc(original.created_at),
                        prediction_as_of_at=utc(approval.created_at), reference_policy="first_recorded_wet_in_episode",
                        acknowledge_research_limitations=True, assume_continuous_wet=True,
                        allow_pooled_pasig_transfer=True), now=clock)
                    if simulation.status == "research_estimate":
                        result.submission_simulation = simulation.model_copy(update={
                            "input_provenance": "citizen_submission_proxy_simulation",
                            "reference_policy": "citizen_submission_proxy_not_observed_onset"})
                        result.submission_audit_id, result.submission_report_id = original.id, report_id
                        result.submission_approval_audit_id = approval.id
            # An invalid/timed linked report must not fall back to an unrelated registration.
            if reports or result.submission_simulation is not None:
                return result.model_copy(update={"reasons": list(dict.fromkeys(reasons))})
            registration = store.unchanged_official_registration(db, zone)
            if (registration is not None and registration.admin_id is not None
                    and (registration.metadata_json or {}).get("zone_id") == zone.id
                    and utc(zone.updated_at) <= utc(registration.created_at) <= clock
                    and (recover_issuance or (clock-utc(registration.created_at)).total_seconds()/60 <= artifact.lineage["reference_age_support_max_minutes"])):
                simulation = preview_subsidence(DurationPreviewRequest(city=result.city, barangay=barangay,
                    footprint_barangays=result.barangays,
                    reference_at=utc(registration.created_at), prediction_as_of_at=utc(registration.created_at),
                    reference_policy="first_recorded_wet_in_episode", acknowledge_research_limitations=True,
                    assume_continuous_wet=True, allow_pooled_pasig_transfer=True), now=clock)
                result.registration_simulation = simulation.model_copy(update={
                    "input_provenance": "admin_registration_proxy_simulation",
                    "reference_policy": "admin_registration_proxy_not_observed_onset"})
                result.registration_audit_id = registration.id
        return result.model_copy(update={"reasons": list(dict.fromkeys(reasons)), "state": "needs_review" if evidence_reasons else "unavailable"})
    # Anchor issuance to recorded evidence availability. Display refreshes must
    # not recondition on hypothetical continued flooding and move the deadline.
    issuance = max(item.available_at for item in wet)
    age_clock = issuance if recover_issuance else clock
    if (age_clock-wet[0].observed_at).total_seconds()/60 > artifact.lineage["reference_age_support_max_minutes"]:
        return result.model_copy(update={"reasons": ["The recorded observation is older than the model's supported reference age."]})
    preview = preview_subsidence(DurationPreviewRequest(city=result.city, barangay=barangay,
        footprint_barangays=result.barangays,
        reference_at=wet[0].observed_at, prediction_as_of_at=issuance,
        reference_policy="first_recorded_wet_in_episode", acknowledge_research_limitations=True,
        assume_continuous_wet=True, allow_pooled_pasig_transfer=True), now=clock)
    if preview.status != "research_estimate":
        reason = {"reference_age_exceeds_experimental_evidence_support": "The recorded observation is older than the model's supported reference age."}.get(
            preview.abstention_reason, "The model cannot estimate from the recorded evidence.")
        return result.model_copy(update={"reasons": [reason]})
    return result.model_copy(update={"state": "estimated", "quantiles": preview.quantiles,
        "calculation": preview.calculation,
        "model": preview.model, "continuity_assumed": True,
        "prediction_as_of_at": issuance,
        "pooled_geographic_transfer": preview.pooled_geographic_transfer,
        "warnings": result.warnings or (["Pooled Pasig transfer: this barangay has no subsidence outcomes in the training cohort; location accuracy is unverified."] if preview.pooled_geographic_transfer else [])})
