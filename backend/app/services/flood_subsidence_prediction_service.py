"""Read-only staff research preview of the conditional Pasig baseline."""
from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from scipy.special import log_ndtr

from app.schemas.flood_subsidence import (
    DurationModelStatus, DurationPreviewRequest, DurationPreviewResponse,
    DurationQuantile, DurationHorizonProbability,
    DurationCalculation, DurationCalculationQuantile,
)
from app.services.flood_duration_model import DurationModelArtifact, DurationModelError, predict_duration_distribution

DEFAULT_MODEL = Path(__file__).resolve().parents[2] / "runtime_data/flood-duration/conditional_aft.json"
EXPERIMENT_TARGET = "remaining_time_from_first_recorded_wet_to_reported_subsidence_continuity_assumed_v1"


def load_research_model() -> tuple[DurationModelArtifact | None, str | None]:
    path = Path(os.getenv("LANES_FLOOD_DURATION_MODEL_PATH", str(DEFAULT_MODEL)))
    try:
        with path.open("rb") as handle:
            payload = handle.read(65_537)
    except FileNotFoundError:
        return None, None
    if len(payload) > 65_536:
        raise DurationModelError("Duration artifact exceeds the research loader limit.")
    checksum = hashlib.sha256(payload).hexdigest()
    expected = os.getenv("LANES_FLOOD_DURATION_MODEL_SHA256")
    if expected and checksum != expected:
        raise DurationModelError("Duration artifact checksum does not match server configuration.")
    artifact = DurationModelArtifact.from_dict(json.loads(payload))
    if (artifact.target_version != EXPERIMENT_TARGET or artifact.feature_names
            or artifact.lineage.get("city") != "Pasig"
            or artifact.lineage.get("deployment_eligible") is not False
            or artifact.lineage.get("continuity_assumption_required") is not True):
        raise DurationModelError("Artifact is incompatible with this conditional research preview.")
    lineage = artifact.lineage
    for name in ("projection_count", "shared_outcome_count"):
        if type(lineage.get(name)) is not int or lineage[name] <= 0:
            raise DurationModelError("Research lineage counts must be positive integers.")
    if lineage["shared_outcome_count"] > lineage["projection_count"]:
        raise DurationModelError("Research lineage outcome count exceeds projections.")
    for name in ("supported_barangays", "limitations"):
        values = lineage.get(name)
        if not isinstance(values, list) or not values or any(not isinstance(value, str) or not value for value in values):
            raise DurationModelError("Research lineage lists must contain nonempty strings.")
    if (not set(lineage["supported_barangays"]).issubset({"Maybunga", "Dela Paz", "Santolan", "Sta. Lucia"})
            or lineage.get("reference_policy") != "first_recorded_wet_in_outcome_selected_candidate_timeline"
            or type(lineage.get("production_training_admitted")) is not int
            or lineage["production_training_admitted"] != 0
            or lineage.get("prospective_availability_verified") is not False):
        raise DurationModelError("Artifact lineage does not match the conditional study policy.")
    age_limit = lineage.get("reference_age_support_max_minutes")
    if type(age_limit) not in (int, float) or not math.isfinite(age_limit) or age_limit <= 0:
        raise DurationModelError("Research reference-age support must be finite and positive.")
    return artifact, checksum


def model_status(artifact: DurationModelArtifact | None, checksum: str | None) -> DurationModelStatus:
    if artifact is None:
        return DurationModelStatus(status="model_unavailable", model_fitted=False,
                                   limitations=["research_artifact_not_provisioned"])
    return DurationModelStatus(status="research_model_available", model_fitted=True,
        target_version=artifact.target_version, model_sha256=checksum,
        projections=artifact.lineage["projection_count"], shared_outcomes=artifact.lineage["shared_outcome_count"],
        supported_barangays=artifact.lineage["supported_barangays"],
        prediction_barangays=pasig_prediction_barangays(),
        limitations=artifact.lineage["limitations"])


def pasig_prediction_barangays() -> list[str]:
    from app.services.philippine_location_service import get_philippine_location_service
    return sorted(get_philippine_location_service().get_pasig_barangays())


def research_barangay_name(value: str, supported: list[str]) -> str | None:
    """PSGC aliases resolve identity; they never expand the fitted cohort."""
    from app.services.philippine_location_service import get_philippine_location_service
    locations = get_philippine_location_service()
    canonical = locations.normalize_barangay_name(value, "Pasig")
    if canonical is None:
        return None
    return next((name for name in supported
        if locations.normalize_barangay_name(name, "Pasig") == canonical), None)


def preview_subsidence(request: DurationPreviewRequest, *, now: datetime | None = None) -> DurationPreviewResponse:
    artifact, checksum = load_research_model()
    response = DurationPreviewResponse(status="abstained", model=model_status(artifact, checksum),
        reference_at=request.reference_at, prediction_as_of_at=request.prediction_as_of_at,
        reference_policy=request.reference_policy, assumed_continuous_wet=request.assume_continuous_wet)
    def abstain(reason: str) -> DurationPreviewResponse:
        return response.model_copy(update={"abstention_reason": reason})
    if artifact is None:
        return abstain("research_model_unavailable")
    if not request.acknowledge_research_limitations:
        return abstain("conditional_research_assumptions_not_acknowledged")
    if request.city.strip().casefold() not in {"pasig", "pasig city", "city of pasig"}:
        return abstain("outside_pasig_research_scope")
    names = request.footprint_barangays or [request.barangay]
    if any(research_barangay_name(name, pasig_prediction_barangays()) is None for name in names):
        return abstain("barangay_not_represented_in_conditional_experiment")
    in_cohort = all(research_barangay_name(name, artifact.lineage["supported_barangays"]) is not None for name in names)
    if not in_cohort:
        if not request.allow_pooled_pasig_transfer:
            return abstain("barangay_not_represented_in_conditional_experiment")
        response.pooled_geographic_transfer = True
    clock = now or datetime.now(timezone.utc)
    if request.prediction_as_of_at > clock + timedelta(minutes=1):
        return abstain("future_issuance_time")
    age = (request.prediction_as_of_at - request.reference_at).total_seconds() / 60
    if age > 0 and not request.assume_continuous_wet:
        return abstain("elapsed_time_requires_explicit_uninterrupted_episode_assumption")
    if age > artifact.lineage["reference_age_support_max_minutes"]:
        # This experiment's largest supplied upper endpoint; a scope check,
        # never a statement that floods must end within this period.
        return abstain("reference_age_exceeds_experimental_evidence_support")
    result = predict_duration_distribution(artifact, {}, elapsed_minutes=age,
        continuously_wet_confirmed=request.assume_continuous_wet, horizons_minutes=(60, 120, 240))
    return response.model_copy(update={"status": "research_estimate", "abstention_reason": None,
        "calculation": _calculation_details(artifact, request, result),
        "quantiles": [DurationQuantile(quantile=item["quantile"], remaining_minutes=item["remaining_minutes"],
            estimated_reported_subsidence_at=request.prediction_as_of_at + timedelta(minutes=item["remaining_minutes"]))
            for item in result["quantiles"]],
        "horizon_probabilities": [DurationHorizonProbability(horizon_minutes=item["horizon_minutes"],
            conditional_probability_reported_subsidence=item["probability_reported_subsidence"])
            for item in result["horizon_probabilities"]]})


def _calculation_details(artifact: DurationModelArtifact, request: DurationPreviewRequest,
                         result: dict) -> DurationCalculation:
    """Explain the kernel's returned values without changing its forecasts."""
    age = result["elapsed_minutes"]
    mu, sigma = artifact.coefficients[0], artifact.scale
    log_survival = 0.0 if age == 0 else float(log_ndtr(-(math.log(age)-mu)/sigma))
    before_anchor = -math.expm1(log_survival)
    rows = []
    for item in result["quantiles"]:
        hours, minutes = divmod(round(item["remaining_minutes"]), 60)
        display = f"{hours}h {minutes}m" if hours else f"{minutes}m"
        rows.append(DurationCalculationQuantile(**{key: item[key] for key in
            ("quantile", "remaining_minutes", "total_minutes")},
            adjusted_probability=before_anchor + item["quantile"]*math.exp(log_survival),
            normal_score=(math.log(item["total_minutes"])-mu)/sigma,
            remaining_duration_display=display,
            estimated_reported_subsidence_at=request.prediction_as_of_at+timedelta(minutes=item["remaining_minutes"])))
    return DurationCalculation(reference_at=request.reference_at, prediction_as_of_at=request.prediction_as_of_at,
        elapsed_minutes=age, log_duration_location=mu, log_duration_scale=sigma,
        probability_before_anchor=before_anchor, quantiles=rows)
