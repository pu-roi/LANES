"""Automatic source-bound research comparison; never selects a primary model."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.cross_location_prediction import CrossLocationCalculation, CrossLocationPrediction
from app.schemas.flood_subsidence import DurationQuantile
from app.services.cross_location_duration_model import CrossLocationArtifact, predict_cross_location
from app.services.flood_duration_model import DurationModelError
from app.services.philippine_location_service import get_philippine_location_service
from app.services import zone_prediction_service as zones
from app.crud import zone_prediction as store

BUNDLE_DIRECTORY = Path(__file__).resolve().parents[2]/"runtime_data/flood-duration"
MANIFEST_SCHEMA = "pasig-cross-location-bundle-v1"


def _json_file(path: Path, limit: int) -> tuple[dict[str, Any], bytes]:
    with path.open("rb") as handle:
        raw = handle.read(limit+1)
    if len(raw) > limit:
        raise DurationModelError("Cross-location bundle exceeds its read budget.")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise DurationModelError("Cross-location bundle must contain JSON objects.")
    return value, raw


def load_comparison() -> tuple[CrossLocationArtifact, dict[str, Any], str]:
    manifest, _ = _json_file(BUNDLE_DIRECTORY/"cross_location_manifest.json", 4096)
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise DurationModelError("Unsupported cross-location bundle manifest.")
    model, raw = _json_file(BUNDLE_DIRECTORY/"cross_location_aft.json", 65536)
    evaluation, report_raw = _json_file(BUNDLE_DIRECTORY/"cross_location_evaluation.json", 131072)
    checksum = hashlib.sha256(raw).hexdigest()
    if (checksum != manifest.get("model_sha256")
            or hashlib.sha256(report_raw).hexdigest() != manifest.get("evaluation_sha256")):
        raise DurationModelError("Cross-location bundle checksum differs.")
    artifact = CrossLocationArtifact.from_dict(model)
    locations = get_philippine_location_service()
    if any(locations.normalize_barangay_name(name, "Pasig") != name for name in artifact.location_outcomes):
        raise DurationModelError("Cross-location artifact uses unsupported location identities.")
    if (evaluation.get("schema_version") != "pasig-cross-location-evaluation-v1"
            or evaluation.get("selected_for_primary") is not False
            or evaluation.get("deployment_eligible") is not False
            or evaluation.get("production_training_admitted") != 0
            or evaluation.get("qualified_rows") != artifact.lineage["projection_count"]
            or evaluation.get("shared_outcomes") != artifact.lineage["shared_outcome_count"]
            or evaluation.get("input_sha256") != artifact.lineage.get("input_sha256")
            or evaluation.get("default_comparison_prior") != artifact.location_prior_sd
            or not isinstance(evaluation.get("selection_blockers"), list)
            or not evaluation["selection_blockers"]
            or any(not isinstance(v, str) or not v for v in evaluation["selection_blockers"])):
        raise DurationModelError("Cross-location model and evaluation lineage disagree.")
    selected = evaluation.get("artifacts", {}).get(str(artifact.location_prior_sd), {})
    if selected.get("sha256") != checksum:
        raise DurationModelError("Cross-location evaluation does not identify this candidate.")
    age_limit = artifact.lineage.get("reference_age_support_max_minutes")
    if type(age_limit) not in (int, float) or not math.isfinite(age_limit) or age_limit <= 0:
        raise DurationModelError("Cross-location reference support is invalid.")
    return artifact, evaluation, checksum


def _clock(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return result.astimezone(timezone.utc) if result.tzinfo and result.utcoffset() is not None else None


def compare_zone(db: Session, zone_id: int, user: User, *, now: datetime | None = None) -> CrossLocationPrediction:
    # Existing service owns authentication/capabilities, geometry/episode/stale gates.
    zones.require_staff_permission(user, write=False)
    zones.require_zone_reader(user, write=False)
    clock = now or datetime.now(timezone.utc)
    baseline = zones.predict_zone(db, zone_id, user, now=clock)
    return compare_resolved_zone(db, baseline, now=clock)


def compare_resolved_zone(db: Session, baseline: zones.ZonePrediction, *, now: datetime) -> CrossLocationPrediction:
    """Internal calculation shared with the audited expiry policy, without HTTP access."""
    clock, zone_id = now, baseline.zone_id
    result = CrossLocationPrediction(zone_id=zone_id)
    try:
        model, evaluation, checksum = load_comparison()
    except FileNotFoundError:
        return result.model_copy(update={"status": "model_unavailable", "reason": "The cross-location research model has not been provisioned."})
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        return result.model_copy(update={"status": "model_unavailable", "reason": "The cross-location model or evaluation failed validation; the baseline remains available."})
    result.model_sha256 = checksum
    result.qualified_rows = evaluation["qualified_rows"]
    result.shared_outcomes = evaluation["shared_outcomes"]
    result.trained_locations = sorted(model.location_outcomes)
    result.selection_blockers = evaluation["selection_blockers"]
    result.validation_summary = (f"{result.qualified_rows} conditional records share {result.shared_outcomes} subsidence summaries. "
        "Holdouts are incomplete and results vary; prospective accuracy is unverified. The baseline remains the primary estimate.")

    def abstain(reason: str) -> CrossLocationPrediction:
        return result.model_copy(update={"reason": reason})

    if baseline.state in {"inactive", "expired", "needs_review"}:
        return abstain("Current zone evidence is inactive, expired or awaiting review.")
    if baseline.city != "Pasig" or len(baseline.barangays) != 1:
        return abstain("A single verified Pasig locality is required; one depth cannot describe a multi-barangay footprint.")
    result.target_location = baseline.barangays[0]
    simulation = baseline.submission_simulation or baseline.registration_simulation
    source_kind, report_id = None, None
    if baseline.state == "estimated" and baseline.reference:
        if baseline.reference.source_kind == "news_decision":
            return abstain("This news reference has no qualified frozen numeric depth snapshot for the comparison.")
        audit_id = baseline.reference.source_id
        reference, issuance = baseline.reference.observed_at, baseline.prediction_as_of_at
        result.reference_basis = "observed_reference"
        source_kind, report_id = baseline.reference.source_kind, baseline.reference.report_id
    elif simulation and simulation.status == "research_estimate":
        is_submission = baseline.submission_simulation is not None
        audit_id = baseline.submission_audit_id if is_submission else baseline.registration_audit_id
        reference, issuance = simulation.reference_at, simulation.prediction_as_of_at
        result.reference_basis = "submission_proxy" if is_submission else "registration_proxy"
        source_kind = "submission_proxy" if is_submission else "registration_proxy"
        report_id = baseline.submission_report_id
        result.warnings.append("The reference is a recording-time simulation; actual flood observation time remains unknown.")
    else:
        return abstain("No eligible observed reference or unchanged recording-time simulation is available.")
    if audit_id is None or issuance is None:
        return abstain("The source audit and issuance clock are unavailable.")
    if source_kind != "registration_proxy" and report_id is None:
        return abstain("The chosen source is missing its report identity.")
    # Database errors propagate to the route's normal error handling.
    audit = store.comparison_source_audit(db, audit_id, source_kind, report_id or zone_id)
    if audit is None:
        return abstain("The selected immutable source record is unavailable.")
    data = audit.metadata_json or {}
    features = data.get("prediction_features")
    if not isinstance(features, dict) or features.get("schema_version") != "flood_features_v1":
        return abstain("No frozen depth features were captured with this source; current values are not backfilled.")
    recorded = _clock(features.get("recorded_at"))
    audit_clock = zones.utc(audit.created_at)
    observed = _clock(features.get("observed_at"))
    if (recorded is None or recorded > issuance or audit_clock > issuance
            or abs(recorded-audit_clock) > timedelta(minutes=1)):
        return abstain("The frozen features were not available at this reference and issuance.")
    if result.reference_basis == "observed_reference":
        if observed != reference or _clock(data.get("observed_at")) != reference or reference > recorded:
            return abstain("The frozen depth observation clock does not match the chosen wet reference.")
    elif features.get("observed_at") is not None or audit_clock != reference:
        return abstain("The recording-time proxy has incompatible source clocks.")
    locations = get_philippine_location_service()
    names = features.get("barangays")
    if (not isinstance(names, list) or len(names) != 1 or not isinstance(names[0], str)
            or locations.normalize_barangay_name(names[0], "Pasig") != result.target_location
            or features.get("errors") or not features.get("geometry_sha256")):
        return abstain("The source feature scope or locality is unresolved or differs from this zone.")
    if source_kind == "registration_proxy":
        zone = store.get_zone(db, zone_id)
        geometry_hash = hashlib.sha256(zones.to_shape(zone.geometry).wkb).hexdigest()
    elif source_kind == "accepted_owner_followup":
        geometry_hash = (data.get("location_snapshot") or {}).get("geometry_sha256")
    else:
        geometry_hash = data.get("geometry_sha256")
    if features["geometry_sha256"] != geometry_hash:
        return abstain("The frozen depth geometry does not match its qualified source.")
    depth, basis = features.get("depth_cm"), features.get("depth_basis")
    if type(depth) not in (int, float) or not math.isfinite(depth) or depth <= 0:
        return abstain("A positive frozen source depth is required; missing depth is not replaced.")
    if basis not in {"reported_numeric_centimeters", "reported_canonical_gauge_proxy"}:
        return abstain("The source depth basis is unsupported.")
    if basis == "reported_canonical_gauge_proxy":
        # An explicit scenario, never an observed numeric measurement/label.
        from app.services.flood_depth import get_flood_depth_measurement
        gauge = get_flood_depth_measurement(features.get("depth_gauge"))
        if gauge is None or gauge.centimeters != depth:
            return abstain("The frozen gauge conversion is inconsistent.")
        result.warnings.append("Depth is a canonical gauge proxy, not measured centimetres. This comparison is a proxy-depth simulation.")
    if not model.depth_min <= depth <= model.depth_max:
        return abstain(f"The source depth is outside the fitted {model.depth_min:g}–{model.depth_max:g} cm evidence range.")
    age = (issuance-reference).total_seconds()/60
    if not 0 <= age <= model.lineage["reference_age_support_max_minutes"]:
        return abstain("The reference age is outside the cross-location evidence support.")
    prediction = predict_cross_location(model, depth, result.target_location,
        elapsed_minutes=age, continuously_wet_confirmed=True)
    result.status = "research_comparison"
    result.depth_cm, result.depth_basis, result.source_audit_id = depth, basis, audit_id
    result.reference_at, result.prediction_as_of_at, result.source_observed_at = reference, issuance, observed
    result.calculation = CrossLocationCalculation(**{k: prediction[k] for k in CrossLocationCalculation.model_fields})
    result.quantiles = [DurationQuantile(quantile=r["quantile"], remaining_minutes=r["remaining_minutes"],
        estimated_reported_subsidence_at=issuance+timedelta(minutes=r["remaining_minutes"])) for r in prediction["quantiles"]]
    result.warnings.append("Intervals include approximate coefficient and unseen-location uncertainty; residual-scale and prior uncertainty are not fully included or calibrated.")
    return result
