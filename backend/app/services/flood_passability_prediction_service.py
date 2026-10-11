"""Research transport recovery, separate from physical subsidence or route writes."""
import hashlib
import json
import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.schemas.flood_subsidence import PassabilityPreviewRequest, PassabilityPreview, PassabilityQuantile
from app.services.flood_duration_model import DurationModelArtifact, DurationModelError, PASSABILITY_TARGET_VERSION, predict_duration_distribution
from app.services.flood_subsidence_prediction_service import model_status, pasig_prediction_barangays, research_barangay_name

DEFAULT_MODEL = Path(__file__).resolve().parents[2] / "runtime_data/flood-duration/passability_aft.json"


def load_passability_model() -> tuple[DurationModelArtifact | None, str | None]:
    path = Path(os.getenv("LANES_FLOOD_PASSABILITY_MODEL_PATH", str(DEFAULT_MODEL)))
    try:
        with path.open("rb") as handle:
            data = handle.read(65537)
    except FileNotFoundError:
        return None, None
    if len(data) > 65536:
        raise DurationModelError("Passability artifact exceeds size limit")
    checksum = hashlib.sha256(data).hexdigest()
    expected = os.getenv("LANES_FLOOD_PASSABILITY_MODEL_SHA256")
    if expected and checksum != expected:
        raise DurationModelError("Passability artifact checksum mismatch")
    artifact = DurationModelArtifact.from_dict(json.loads(data))
    lineage = artifact.lineage
    if (artifact.target_version != PASSABILITY_TARGET_VERSION or artifact.feature_names
            or lineage.get("city") != "Pasig" or lineage.get("deployment_eligible") is not False
            or lineage.get("continuity_assumption_required") is not True
            or lineage.get("production_training_admitted") != 0
            or lineage.get("prospective_availability_verified") is not False):
        raise DurationModelError("Incompatible passability research artifact")
    for key in ("projection_count", "shared_outcome_count"):
        if type(lineage.get(key)) is not int or lineage[key] <= 0:
            raise DurationModelError("Invalid passability lineage counts")
    if lineage["shared_outcome_count"] > lineage["projection_count"]:
        raise DurationModelError("Shared outcomes exceed projections")
    for key in ("supported_barangays", "limitations"):
        if not isinstance(lineage.get(key), list) or not lineage[key] or any(not isinstance(v, str) or not v for v in lineage[key]):
            raise DurationModelError("Invalid passability lineage lists")
    if any(research_barangay_name(name, pasig_prediction_barangays()) is None for name in lineage["supported_barangays"]):
        raise DurationModelError("Unknown passability training geography")
    age = lineage.get("reference_age_support_max_minutes")
    if type(age) not in (int, float) or not math.isfinite(age) or age <= 0:
        raise DurationModelError("Invalid passability age support")
    return artifact, checksum


def preview_passability(request: PassabilityPreviewRequest, *, now: datetime | None = None) -> PassabilityPreview:
    artifact, checksum = load_passability_model()
    result = PassabilityPreview(status="abstained", model=model_status(artifact, checksum),
        reference_at=request.reference_at, prediction_as_of_at=request.prediction_as_of_at)
    def abstain(reason: str) -> PassabilityPreview:
        return result.model_copy(update={"abstention_reason": reason})
    if artifact is None:
        return abstain("passability_model_unavailable")
    if not request.acknowledge_research_limitations or not request.assume_continuous_nonpassability:
        return abstain("continuous_nonpassability_research_assumption_required")
    if request.city.strip().casefold() not in {"pasig", "pasig city", "city of pasig"}:
        return abstain("outside_pasig_scope")
    if research_barangay_name(request.barangay, pasig_prediction_barangays()) is None:
        return abstain("unknown_pasig_barangay")
    in_cohort = research_barangay_name(request.barangay, result.model.supported_barangays) is not None
    if not in_cohort and not request.allow_pooled_pasig_transfer:
        return abstain("outside_passability_training_cohort")
    result.pooled_geographic_transfer = not in_cohort
    if request.prediction_as_of_at > (now or datetime.now(timezone.utc)) + timedelta(minutes=1):
        return abstain("future_issuance_time")
    age = (request.prediction_as_of_at-request.reference_at).total_seconds()/60
    if age > artifact.lineage["reference_age_support_max_minutes"]:
        return abstain("reference_age_exceeds_passability_evidence_support")
    distribution = predict_duration_distribution(artifact, {}, elapsed_minutes=age, continuously_wet_confirmed=True)
    return result.model_copy(update={"status": "research_estimate", "quantiles": [PassabilityQuantile(
        quantile=row["quantile"], remaining_minutes=row["remaining_minutes"],
        estimated_reported_passability_at=request.prediction_as_of_at+timedelta(minutes=row["remaining_minutes"]))
        for row in distribution["quantiles"]]})
