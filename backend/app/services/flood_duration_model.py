"""Interval-aware lognormal AFT research kernel for reported subsidence.

This module cannot clear a flood report or change its evidence expiry. Artifacts
are shadow-only, and distribution quantiles are not statements of safe passage.
Callers own evidence qualification, outcome-independent reference selection,
group-balanced weights, geographic scope and release acceptance.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

import numpy as np
from scipy.optimize import minimize
from scipy.special import log_ndtr, ndtri_exp


SCHEMA_VERSION = "pasig-reported-subsidence-lognormal-aft-v1"
TARGET_VERSION = "remaining_time_from_supported_wet_reference_to_scope_matched_reported_subsidence_v1"
EXPERIMENT_TARGET_VERSION = "remaining_time_from_first_recorded_wet_to_reported_subsidence_continuity_assumed_v1"
PASSABILITY_TARGET_VERSION = "remaining_time_from_first_recorded_nonpassable_to_reported_light_vehicle_passability_continuity_assumed_v1"
SUPPORTED_TARGET_VERSIONS = frozenset((TARGET_VERSION, EXPERIMENT_TARGET_VERSION, PASSABILITY_TARGET_VERSION))
LOG_SCALE_LIMITS = (-8.0, 8.0)


class DurationModelError(ValueError):
    """Invalid model inputs, artifacts or numerical results."""


class ModelNotIdentifiableError(DurationModelError):
    """The evidence does not identify a finite, locally identifiable fit."""


def _finite(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise DurationModelError(f"{name} must be a finite number, not a boolean.")
    try:
        number = float(value)  # type: ignore[arg-type]
    except (ValueError, TypeError, OverflowError) as exc:
        raise DurationModelError(f"{name} must be a finite number.") from exc
    if not math.isfinite(number):
        raise DurationModelError(f"{name} must be finite.")
    return number


def _json_object(value: Mapping[str, Any], name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise DurationModelError(f"{name} must be a JSON object.")
    try:
        result = json.loads(json.dumps(dict(value), allow_nan=False))
    except (ValueError, TypeError, OverflowError) as exc:
        raise DurationModelError(f"{name} must contain only finite JSON values.") from exc
    return result


@dataclass(frozen=True)
class DurationObservation:
    """Bounds in minutes from an eligible wet reference; None means +infinity.

    Equal positive bounds denote an exact outcome. Zero lower bounds denote
    left-censored outcomes; positive unequal finite bounds denote intervals.
    A positive lower bound with no upper bound denotes right censoring.
    Weights must be supplied deliberately by the caller, including shared
    outcome and storm-group dependence adjustments.
    """

    lower_minutes: float
    upper_minutes: float | None
    weight: float
    features: Mapping[str, float | None] = field(default_factory=dict)
    observation_id: str = ""

    def __post_init__(self) -> None:
        lower = _finite(self.lower_minutes, "lower_minutes")
        upper = None if self.upper_minutes is None else _finite(self.upper_minutes, "upper_minutes")
        weight = _finite(self.weight, "weight")
        if lower < 0 or (upper is not None and (upper <= 0 or upper < lower)):
            raise DurationModelError("Bounds require 0 <= lower <= upper and a positive finite upper.")
        if upper is None and lower <= 0:
            raise DurationModelError("Right censoring requires a positive supported lower bound.")
        if weight <= 0:
            raise DurationModelError("Observation weight must be positive.")
        values: dict[str, float | None] = {}
        if not isinstance(self.features, Mapping):
            raise DurationModelError("Observation features must be a mapping.")
        for key, value in self.features.items():
            if not isinstance(key, str) or not key:
                raise DurationModelError("Feature names must be nonempty strings.")
            values[key] = None if value is None else _finite(value, f"feature {key}")
        object.__setattr__(self, "lower_minutes", lower)
        object.__setattr__(self, "upper_minutes", upper)
        object.__setattr__(self, "weight", weight)
        object.__setattr__(self, "features", MappingProxyType(values))


@dataclass(frozen=True)
class DurationModelArtifact:
    """Portable JSON model, with scaler fitted only on the supplied training set.

    Coefficients are ordered as intercept, standardized feature_names, then
    missing_indicator_features. Missing numeric values are imputed to the
    training mean, giving a standardized value of zero, alongside the indicator.
    """

    feature_names: tuple[str, ...]
    feature_means: tuple[float, ...]
    feature_scales: tuple[float, ...]
    missing_indicator_features: tuple[str, ...]
    coefficients: tuple[float, ...]
    scale: float
    lineage: Mapping[str, Any]
    fit_diagnostics: Mapping[str, Any]
    schema_version: str = SCHEMA_VERSION
    target_version: str = TARGET_VERSION
    shadow_only: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION or self.target_version not in SUPPORTED_TARGET_VERSIONS:
            raise DurationModelError("Unsupported duration artifact schema or target.")
        if self.shadow_only is not True:
            raise DurationModelError("This research kernel accepts only shadow-only artifacts.")
        names = tuple(self.feature_names)
        indicators = tuple(self.missing_indicator_features)
        if any(not isinstance(name, str) or not name for name in names):
            raise DurationModelError("Feature names must be nonempty strings.")
        if len(set(names)) != len(names) or len(set(indicators)) != len(indicators):
            raise DurationModelError("Feature names and missing indicators must be unique.")
        if not set(indicators).issubset(names):
            raise DurationModelError("Missing indicators must name fitted features.")
        means = tuple(_finite(value, "feature mean") for value in self.feature_means)
        scales = tuple(_finite(value, "feature scale") for value in self.feature_scales)
        coefficients = tuple(_finite(value, "coefficient") for value in self.coefficients)
        scale = _finite(self.scale, "scale")
        if len(means) != len(names) or len(scales) != len(names):
            raise DurationModelError("Scaler dimensions do not match feature names.")
        if any(value <= 0 for value in scales) or scale <= 0:
            raise DurationModelError("All feature scales and the lognormal scale must be positive.")
        if len(coefficients) != 1 + len(names) + len(indicators):
            raise DurationModelError("Coefficient dimensions do not match the fitted design.")
        object.__setattr__(self, "feature_names", names)
        object.__setattr__(self, "missing_indicator_features", indicators)
        object.__setattr__(self, "feature_means", means)
        object.__setattr__(self, "feature_scales", scales)
        object.__setattr__(self, "coefficients", coefficients)
        object.__setattr__(self, "scale", scale)
        object.__setattr__(self, "lineage", _json_object(self.lineage, "lineage"))
        object.__setattr__(self, "fit_diagnostics", _json_object(self.fit_diagnostics, "fit_diagnostics"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "target_version": self.target_version,
            "shadow_only": self.shadow_only,
            "feature_names": list(self.feature_names),
            "feature_means": list(self.feature_means),
            "feature_scales": list(self.feature_scales),
            "missing_indicator_features": list(self.missing_indicator_features),
            "coefficients": list(self.coefficients),
            "scale": self.scale,
            "lineage": dict(self.lineage),
            "fit_diagnostics": dict(self.fit_diagnostics),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> DurationModelArtifact:
        required = {
            "schema_version", "target_version", "shadow_only", "feature_names",
            "feature_means", "feature_scales", "missing_indicator_features",
            "coefficients", "scale", "lineage", "fit_diagnostics",
        }
        if not isinstance(payload, Mapping) or set(payload) != required:
            raise DurationModelError("Artifact has missing or unexpected fields.")
        for key in ("feature_names", "feature_means", "feature_scales", "missing_indicator_features", "coefficients"):
            if not isinstance(payload[key], (list, tuple)):
                raise DurationModelError(f"Artifact field {key} must be an array.")
        try:
            return cls(**dict(payload))
        except (TypeError, AttributeError, KeyError) as exc:
            raise DurationModelError("Invalid duration artifact structure.") from exc


def _log_difference(log_larger: float, log_smaller: float) -> float:
    """log(exp(a)-exp(b)), retaining precision in close tail probabilities."""
    if log_smaller == -math.inf:
        return log_larger
    if log_smaller >= log_larger:
        return -math.inf
    return log_larger + math.log(-math.expm1(log_smaller - log_larger))


def interval_log_likelihood(
    lower_minutes: float,
    upper_minutes: float | None,
    location: float,
    scale: float,
) -> float:
    """Log likelihood contribution for one validated lognormal observation.

    Inclusion of finite interval endpoints does not change continuous mass.
    Exact outcomes use a density, not zero-width interval probability.
    """
    item = DurationObservation(lower_minutes, upper_minutes, 1.0)
    location = _finite(location, "location")
    scale = _finite(scale, "scale")
    if scale <= 0:
        raise DurationModelError("Lognormal scale must be positive.")
    lower, upper = item.lower_minutes, item.upper_minutes
    if upper is not None and lower == upper:
        z = (math.log(lower) - location) / scale
        return -0.5 * z * z - math.log(scale) - math.log(lower) - 0.5 * math.log(2 * math.pi)
    if upper is None:
        return float(log_ndtr(-(math.log(lower) - location) / scale))
    z_upper = (math.log(upper) - location) / scale
    if lower == 0:
        return float(log_ndtr(z_upper))
    z_lower = (math.log(lower) - location) / scale
    if z_lower >= 0:
        return _log_difference(float(log_ndtr(-z_lower)), float(log_ndtr(-z_upper)))
    return _log_difference(float(log_ndtr(z_upper)), float(log_ndtr(z_lower)))


def _feature_row(artifact: DurationModelArtifact, features: Mapping[str, float | None]) -> np.ndarray:
    if set(features) != set(artifact.feature_names):
        raise DurationModelError("Prediction features must match all fitted feature names exactly.")
    values: list[float] = [1.0]
    for name, mean, scale in zip(artifact.feature_names, artifact.feature_means, artifact.feature_scales):
        value = features[name]
        if value is None and name not in artifact.missing_indicator_features:
            raise DurationModelError(f"Feature {name} was never missing during fitting; missing prediction is unsupported.")
        values.append(0.0 if value is None else (_finite(value, f"feature {name}") - mean) / scale)
    values.extend(float(features[name] is None) for name in artifact.missing_indicator_features)
    design = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(design)):
        raise DurationModelError("Feature standardization produced a nonfinite value.")
    return design


def _observed_hessian(objective: Callable[[np.ndarray], float], parameters: np.ndarray) -> np.ndarray:
    """Central differences of the normalized observed negative log likelihood."""
    size = len(parameters)
    result = np.empty((size, size), dtype=float)
    steps = 1e-4 * np.maximum(1.0, np.abs(parameters))
    center = objective(parameters)
    for i in range(size):
        ei = np.zeros(size)
        ei[i] = steps[i]
        result[i, i] = (objective(parameters + ei) - 2 * center + objective(parameters - ei)) / steps[i] ** 2
        for j in range(i):
            ej = np.zeros(size)
            ej[j] = steps[j]
            result[i, j] = result[j, i] = (
                objective(parameters + ei + ej) - objective(parameters + ei - ej)
                - objective(parameters - ei + ej) + objective(parameters - ei - ej)
            ) / (4 * steps[i] * steps[j])
    return result


def fit_lognormal_aft(
    observations: Sequence[DurationObservation],
    feature_names: Sequence[str] = (),
    *,
    lineage: Mapping[str, Any],
    target_version: str = TARGET_VERSION,
) -> DurationModelArtifact:
    """Fit a simple AFT model or reject a nonidentifiable evidence set.

    Local observed curvature is a numerical fit check, not proof of sufficient
    independent events, calibration, unbiased censoring or production accuracy.
    No duration bounds, synthetic outcomes, regularization or population prior
    are added to rescue unsupported training data.
    """
    rows = tuple(observations)
    names = tuple(feature_names)
    if target_version not in SUPPORTED_TARGET_VERSIONS:
        raise DurationModelError("Unsupported duration target version.")
    if not rows or any(not isinstance(row, DurationObservation) for row in rows):
        raise DurationModelError("Training requires validated DurationObservation records.")
    if any(not isinstance(name, str) or not name for name in names) or len(set(names)) != len(names):
        raise DurationModelError("Feature names must be unique nonempty strings.")
    if any(set(row.features) != set(names) for row in rows):
        raise DurationModelError("Every observation must provide exactly the requested features.")
    if not any(row.upper_minutes is not None for row in rows):
        raise ModelNotIdentifiableError("Only right-censored records cannot identify a duration distribution.")
    if not any(row.lower_minutes > 0 for row in rows):
        raise ModelNotIdentifiableError("Only upper bounds identify no positive duration location: likelihood improves toward zero duration.")
    means: list[float] = []
    scales: list[float] = []
    indicators: list[str] = []
    columns: list[np.ndarray] = [np.ones(len(rows))]
    for name in names:
        present = np.asarray([row.features[name] for row in rows if row.features[name] is not None], dtype=float)
        if not len(present):
            raise ModelNotIdentifiableError(f"Feature {name} has no observed training values.")
        mean, scale = float(np.mean(present)), float(np.std(present))
        if not math.isfinite(mean) or not math.isfinite(scale) or scale <= 0:
            raise ModelNotIdentifiableError(f"Feature {name} has no finite variation in training.")
        means.append(mean)
        scales.append(scale)
        columns.append(np.asarray([0.0 if row.features[name] is None else (float(row.features[name]) - mean) / scale for row in rows]))
        if any(row.features[name] is None for row in rows):
            indicators.append(name)
    columns.extend(np.asarray([float(row.features[name] is None) for row in rows]) for name in indicators)
    design = np.column_stack(columns)
    if not np.all(np.isfinite(design)) or np.linalg.matrix_rank(design) != design.shape[1]:
        raise ModelNotIdentifiableError("Training feature design is nonfinite or rank deficient.")
    parameter_count = design.shape[1] + 1
    if len(rows) < parameter_count:
        raise ModelNotIdentifiableError("Fewer likelihood contributions than fitted parameters.")
    raw_weights = np.asarray([row.weight for row in rows])
    # Scaling preserves the optimum without overflowing sums of user weights.
    scaled_weights = raw_weights / float(np.max(raw_weights))
    if np.any(scaled_weights == 0):
        raise DurationModelError("Observation weight ratios exceed finite numerical precision.")
    weights = scaled_weights / float(np.sum(scaled_weights))

    def objective(parameters: np.ndarray) -> float:
        if not np.all(np.isfinite(parameters)):
            return math.inf
        locations = design @ parameters[:-1]
        if not np.all(np.isfinite(locations)):
            return math.inf
        sigma = math.exp(float(parameters[-1]))
        contributions = np.asarray([
            interval_log_likelihood(row.lower_minutes, row.upper_minutes, float(mu), sigma)
            for row, mu in zip(rows, locations)
        ])
        if not np.all(np.isfinite(contributions)):
            return math.inf
        return -float(weights @ contributions)

    anchors = [math.log(row.upper_minutes if row.lower_minutes == 0 else row.lower_minutes) for row in rows]
    initial_location = float(np.median(anchors))
    candidates = []
    for location_shift, sigma in ((0.0, 0.5), (0.0, 1.0), (0.0, 2.0), (-1.0, 1.0), (1.0, 1.0)):
        start = np.zeros(parameter_count)
        start[0] = initial_location + location_shift
        start[-1] = math.log(sigma)
        result = minimize(
            objective, start, method="L-BFGS-B",
            bounds=[(None, None)] * (parameter_count - 1) + [LOG_SCALE_LIMITS],
            options={"maxiter": 2000, "ftol": 1e-12, "gtol": 1e-7},
        )
        if result.success and np.all(np.isfinite(result.x)) and math.isfinite(float(result.fun)):
            candidates.append(result)
    if not candidates:
        raise ModelNotIdentifiableError("No finite converged maximum-likelihood fit from multiple starts.")
    best = min(candidates, key=lambda item: float(item.fun))
    parameters = np.asarray(best.x)
    if min(abs(parameters[-1] - bound) for bound in LOG_SCALE_LIMITS) <= 1e-3:
        raise ModelNotIdentifiableError("Fit reached a numerical log-scale boundary; no duration fit is admitted.")
    hessian = _observed_hessian(objective, parameters)
    if not np.all(np.isfinite(hessian)):
        raise ModelNotIdentifiableError("Observed likelihood curvature is nonfinite.")
    eigenvalues = np.linalg.eigvalsh(hessian)
    if eigenvalues[-1] <= 0 or eigenvalues[0] <= max(1e-9, eigenvalues[-1] * 1e-7):
        raise ModelNotIdentifiableError("Observed likelihood is flat, indefinite or numerically nonidentifiable.")
    return DurationModelArtifact(
        feature_names=names, feature_means=tuple(means), feature_scales=tuple(scales),
        missing_indicator_features=tuple(indicators),
        coefficients=tuple(float(value) for value in parameters[:-1]),
        scale=math.exp(float(parameters[-1])), lineage=lineage, target_version=target_version,
        fit_diagnostics={
            "observation_count": len(rows), "parameter_count": parameter_count,
            "normalized_negative_log_likelihood": float(best.fun),
            "weight_policy": "caller_supplied_normalized_for_optimization",
            "converged_start_count": len(candidates), "attempted_start_count": 5,
            "observed_hessian_min_eigenvalue": float(eigenvalues[0]),
            "observed_hessian_condition_number": float(eigenvalues[-1] / eigenvalues[0]),
            "numerical_log_scale_limits": list(LOG_SCALE_LIMITS),
            "independent_event_sufficiency_established": False,
            "predictive_validation_established": False,
        },
    )


def predict_duration_distribution(
    artifact: DurationModelArtifact,
    features: Mapping[str, float | None],
    *,
    quantiles: Sequence[float] = (0.1, 0.5, 0.9),
    horizons_minutes: Sequence[float] = (),
    elapsed_minutes: float = 0.0,
    continuously_wet_confirmed: bool = False,
) -> dict[str, Any]:
    """Return shadow distribution estimates, optionally conditional on T > age.

    Time alone does not establish continuous flooding. Positive age therefore
    requires caller-qualified evidence supporting the continuity assumption.
    Horizons and returned remaining times are measured from the prediction time.
    This calculation does not establish an acceptable validation/release gate.
    """
    if not isinstance(artifact, DurationModelArtifact):
        raise DurationModelError("Prediction requires a validated DurationModelArtifact.")
    age = _finite(elapsed_minutes, "elapsed_minutes")
    if age < 0 or (age > 0 and continuously_wet_confirmed is not True):
        raise DurationModelError("Positive elapsed time requires explicit continuous-wet confirmation.")
    location = float(_feature_row(artifact, features) @ np.asarray(artifact.coefficients))
    if not math.isfinite(location):
        raise DurationModelError("Prediction location is nonfinite.")
    sigma = artifact.scale
    log_survival_age = 0.0 if age == 0 else float(log_ndtr(-(math.log(age) - location) / sigma))
    if not math.isfinite(log_survival_age):
        raise DurationModelError("Conditioning probability is not numerically supported.")
    estimates: list[dict[str, float]] = []
    for raw_q in quantiles:
        q = _finite(raw_q, "quantile")
        if not 0 < q < 1:
            raise DurationModelError("Distribution quantiles must lie strictly between zero and one.")
        z = -float(ndtri_exp(log_survival_age + math.log1p(-q)))
        log_total = location + sigma * z
        try:
            total = math.exp(log_total)
            remaining = total if age == 0 else age * math.expm1(log_total - math.log(age))
        except OverflowError as exc:
            raise DurationModelError("Predicted duration exceeds finite numerical range.") from exc
        if not math.isfinite(total) or total <= 0 or not math.isfinite(remaining) or remaining < 0:
            raise DurationModelError("Predicted duration is outside finite positive numerical range.")
        estimates.append({"quantile": q, "total_minutes": total, "remaining_minutes": remaining})
    probabilities: list[dict[str, float]] = []
    for raw_horizon in horizons_minutes:
        horizon = _finite(raw_horizon, "horizon_minutes")
        if horizon < 0:
            raise DurationModelError("Horizons must be nonnegative.")
        end = age + horizon
        if not math.isfinite(end):
            raise DurationModelError("Prediction horizon exceeds finite numerical range.")
        log_survival_end = 0.0 if end == 0 else float(log_ndtr(-(math.log(end) - location) / sigma))
        probability = -math.expm1(min(0.0, log_survival_end - log_survival_age))
        probabilities.append({"horizon_minutes": horizon, "probability_reported_subsidence": probability})
    return {
        "schema_version": artifact.schema_version, "target_version": artifact.target_version,
        "shadow_only": True, "elapsed_minutes": age,
        "conditioning": "continuous_wet_T_greater_than_age" if age > 0 else "none",
        "quantiles": estimates, "horizon_probabilities": probabilities,
        "physical_dry_or_passability_established": False,
    }
