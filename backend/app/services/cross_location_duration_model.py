"""Fixed-prior partial pooling for conditional, read-only duration comparisons.

Shared-outcome weights form a composite likelihood, not independent events.
Curvature uncertainty is a conditional Laplace approximation with residual
scale and prior scales held fixed; it is not field-calibrated uncertainty.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import math
from typing import Any, Sequence

import numpy as np
from scipy.optimize import minimize

from app.services.flood_duration_model import (
    DurationModelArtifact, DurationModelError, DurationObservation,
    EXPERIMENT_TARGET_VERSION, ModelNotIdentifiableError, _observed_hessian,
    interval_log_likelihood, predict_duration_distribution,
)

SCHEMA = "pasig-cross-location-aft-v1"
UNCERTAINTY = "conditional_composite_laplace_coefficients_plus_unseen_location_prior"


def number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise DurationModelError(f"{name} must be a finite number.")
    return float(value)


@dataclass(frozen=True)
class CrossLocationObservation:
    observation_id: str
    location: str
    outcome_group: str
    episode: str
    depth_cm: float
    lower_minutes: float
    upper_minutes: float | None

    def __post_init__(self) -> None:
        for name in ("observation_id", "location", "outcome_group", "episode"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise DurationModelError(f"{name} must be a nonempty identity.")
        if not 0 < number(self.depth_cm, "depth_cm") <= 1000:
            raise DurationModelError("A positive supported depth is required.")
        DurationObservation(self.lower_minutes, self.upper_minutes, 1.0)


@dataclass(frozen=True)
class CrossLocationArtifact:
    depth_mean: float
    depth_scale: float
    depth_min: float
    depth_max: float
    locations: tuple[str, ...]
    coefficients: tuple[float, ...]
    coefficient_covariance: tuple[tuple[float, ...], ...]
    residual_scale: float
    location_prior_sd: float
    depth_prior_sd: float
    location_outcomes: dict[str, int]
    lineage: dict[str, Any]
    diagnostics: dict[str, Any]
    schema_version: str = SCHEMA
    target_version: str = EXPERIMENT_TARGET_VERSION
    uncertainty_method: str = UNCERTAINTY
    shadow_only: bool = True

    def __post_init__(self) -> None:
        if (self.schema_version != SCHEMA or self.target_version != EXPERIMENT_TARGET_VERSION
                or self.uncertainty_method != UNCERTAINTY or self.shadow_only is not True):
            raise DurationModelError("Unsupported cross-location artifact policy.")
        for name in ("depth_mean", "depth_scale", "depth_min", "depth_max", "residual_scale",
                     "location_prior_sd", "depth_prior_sd"):
            number(getattr(self, name), name)
        if (not 0 < self.depth_min <= self.depth_mean <= self.depth_max <= 1000
                or self.depth_scale <= 0 or self.residual_scale <= 0
                or not 0 <= self.location_prior_sd <= 2 or not 0 < self.depth_prior_sd <= 2):
            raise DurationModelError("Invalid cross-location scales or depth support.")
        if (len(set(self.locations)) != len(self.locations) or len(self.locations) > 30
                or any(not isinstance(v, str) or not v.strip() for v in self.locations)
                or (self.location_prior_sd == 0 and self.locations)):
            raise DurationModelError("Invalid cross-location identities.")
        size = 2 + len(self.locations)
        if len(self.coefficients) != size:
            raise DurationModelError("Cross-location coefficient dimensions differ.")
        for value in self.coefficients:
            number(value, "coefficient")
        covariance = np.asarray(self.coefficient_covariance, dtype=float)
        if (covariance.shape != (size, size) or not np.all(np.isfinite(covariance))
                or not np.allclose(covariance, covariance.T, atol=1e-8, rtol=1e-8)
                or np.linalg.eigvalsh(covariance)[0] <= 0):
            raise DurationModelError("Invalid positive-definite coefficient covariance.")
        if (not isinstance(self.location_outcomes, dict)
                or any(not isinstance(k, str) or type(v) is not int or v < 1
                       for k, v in self.location_outcomes.items())
                or not set(self.locations).issubset(self.location_outcomes)):
            raise DurationModelError("Invalid location evidence counts.")
        if (self.lineage.get("city") != "Pasig" or self.lineage.get("deployment_eligible") is not False
                or type(self.lineage.get("production_training_admitted")) is not int
                or self.lineage.get("production_training_admitted") != 0
                or self.lineage.get("prospective_validation_established") is not False):
            raise DurationModelError("Cross-location artifacts are conditional research only.")
        for name in ("projection_count", "shared_outcome_count"):
            if type(self.lineage.get(name)) is not int or self.lineage[name] < 2:
                raise DurationModelError("Missing cross-location evidence counts.")
        if self.lineage["shared_outcome_count"] > self.lineage["projection_count"]:
            raise DurationModelError("Outcomes exceed projections.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> CrossLocationArtifact:
        if not isinstance(value, dict) or set(value) != set(cls.__dataclass_fields__):
            raise DurationModelError("Missing or unexpected cross-location artifact fields.")
        try:
            return cls(**value)
        except (TypeError, KeyError, AttributeError, np.linalg.LinAlgError) as exc:
            raise DurationModelError("Malformed cross-location artifact.") from exc


def fit_cross_location(
    observations: Sequence[CrossLocationObservation], *, location_prior_sd: float = .35,
    depth_prior_sd: float = .5, lineage: dict[str, Any] | None = None,
) -> CrossLocationArtifact:
    """Fit a penalized composite likelihood; fixed prior scales are sensitivity inputs."""
    rows = tuple(observations)
    tau = number(location_prior_sd, "location_prior_sd")
    depth_sd = number(depth_prior_sd, "depth_prior_sd")
    if not 0 <= tau <= 2 or not 0 < depth_sd <= 2:
        raise DurationModelError("Unsupported prior scale.")
    if not rows or any(not isinstance(row, CrossLocationObservation) for row in rows):
        raise DurationModelError("Validated cross-location observations are required.")
    if len({row.observation_id for row in rows}) != len(rows):
        raise DurationModelError("Duplicate observation identities.")
    groups = Counter(row.outcome_group for row in rows)
    if len(groups) < 2 or not any(row.upper_minutes is not None for row in rows) or not any(row.lower_minutes > 0 for row in rows):
        raise ModelNotIdentifiableError("At least two outcome groups and two-sided duration support are required.")
    # Total contribution of each summary is one, not the number of projections.
    weights = np.asarray([1 / groups[row.outcome_group] for row in rows])
    depths = np.asarray([row.depth_cm for row in rows])
    mean = float(np.average(depths, weights=weights))
    spread = math.sqrt(float(np.average((depths - mean) ** 2, weights=weights)))
    # A constant-depth fold leaves the slope prior-driven; record it explicitly.
    scale = spread if spread > 1e-8 else 1.0
    locations = tuple(sorted({row.location for row in rows})) if tau else ()
    design = np.zeros((len(rows), 2 + len(locations)))
    design[:, 0] = 1
    design[:, 1] = (depths - mean) / scale
    for i, row in enumerate(rows):
        if locations:
            design[i, 2 + locations.index(row.location)] = 1

    def objective(parameters: np.ndarray) -> float:
        sigma = math.exp(float(parameters[-1]))
        contributions = [interval_log_likelihood(row.lower_minutes, row.upper_minutes, float(mu), sigma)
                         for row, mu in zip(rows, design @ parameters[:-1])]
        if not np.all(np.isfinite(contributions)):
            return math.inf
        penalty = .5 * (parameters[1] / depth_sd) ** 2 + .5 * parameters[-1] ** 2
        if locations:
            penalty += .5 * float(np.sum((parameters[2:-1] / tau) ** 2))
        return -float(weights @ np.asarray(contributions)) + penalty

    anchor = float(np.median([math.log(row.upper_minutes if row.lower_minutes == 0 else row.lower_minutes) for row in rows]))
    candidates = []
    for sigma in (.4, 1.0, 2.0):
        start = np.zeros(design.shape[1] + 1)
        start[0], start[-1] = anchor, math.log(sigma)
        result = minimize(objective, start, method="L-BFGS-B",
                          bounds=[(None, None)] * design.shape[1] + [(-5, 3)],
                          options={"maxiter": 1000, "ftol": 1e-11, "gtol": 1e-6})
        if result.success and np.all(np.isfinite(result.x)) and math.isfinite(result.fun):
            candidates.append(result)
    if not candidates:
        raise ModelNotIdentifiableError("Cross-location fitting did not converge.")
    best = min(candidates, key=lambda r: r.fun)
    if min(abs(float(best.x[-1]) - bound) for bound in (-5, 3)) < .001:
        raise ModelNotIdentifiableError("Cross-location residual scale reached a numerical boundary.")
    hessian = _observed_hessian(objective, best.x)
    eigenvalues = np.linalg.eigvalsh(hessian)
    if not np.all(np.isfinite(hessian)) or eigenvalues[0] <= max(1e-8, eigenvalues[-1] * 1e-8):
        raise ModelNotIdentifiableError("Unsupported cross-location curvature approximation.")
    # Conditional coefficient curvature: fitted residual scale remains fixed.
    covariance = np.linalg.inv(hessian[:-1, :-1])
    evidence_counts = {loc: len({row.outcome_group for row in rows if row.location == loc})
                       for loc in sorted({row.location for row in rows})}
    return CrossLocationArtifact(
        depth_mean=mean, depth_scale=scale, depth_min=float(min(depths)), depth_max=float(max(depths)),
        locations=locations, coefficients=tuple(float(v) for v in best.x[:-1]),
        coefficient_covariance=tuple(tuple(float(v) for v in row) for row in covariance),
        residual_scale=math.exp(float(best.x[-1])), location_prior_sd=tau, depth_prior_sd=depth_sd,
        location_outcomes=evidence_counts,
        lineage={**(lineage or {}), "city": "Pasig", "projection_count": len(rows),
                 "shared_outcome_count": len(groups), "production_training_admitted": 0,
                 "deployment_eligible": False, "prospective_validation_established": False},
        diagnostics={"objective": float(best.fun), "converged_starts": len(candidates),
                     "constant_depth_prior_driven": spread <= 1e-8,
                     "hessian_min_eigenvalue": float(eigenvalues[0]),
                     "weight_policy": "each_shared_summary_total_one",
                     "residual_and_prior_scale_uncertainty_included": False},
    )


def prediction_parameters(model: CrossLocationArtifact, depth_cm: float, location: str) -> dict[str, Any]:
    """Marginalize an unseen local effect; no nearest-location or precision substitution."""
    depth = number(depth_cm, "depth_cm")
    if not model.depth_min <= depth <= model.depth_max:
        raise DurationModelError("Depth outside the fitted evidence support.")
    if not isinstance(location, str) or not location.strip():
        raise DurationModelError("A target location identity is required.")
    x = np.zeros(len(model.coefficients))
    x[0], x[1] = 1, (depth - model.depth_mean) / model.depth_scale
    known = location in model.locations
    if known:
        x[2 + model.locations.index(location)] = 1
    local_variance = 0.0 if known else model.location_prior_sd ** 2
    parameter_variance = float(x @ np.asarray(model.coefficient_covariance) @ x)
    variance = parameter_variance + local_variance
    coefficients = np.asarray(model.coefficients)
    mu = float(x @ coefficients)
    sigma = math.sqrt(model.residual_scale ** 2 + variance)
    return {"log_duration_location": mu, "predictive_log_scale": sigma,
            "shared_depth_effect": float(x[1] * coefficients[1]),
            "local_effect": float(x[2:] @ coefficients[2:]),
            "coefficient_variance": parameter_variance, "unseen_location_variance": local_variance,
            "location_outcomes": model.location_outcomes.get(location, 0),
            "transfer_basis": "partial_pooling" if known else "shared_depth_with_unseen_location_prior",
            "uncertainty_method": UNCERTAINTY}


def predict_cross_location(
    model: CrossLocationArtifact, depth_cm: float, location: str, *, elapsed_minutes: float = 0,
    continuously_wet_confirmed: bool = False,
) -> dict[str, Any]:
    details = prediction_parameters(model, depth_cm, location)
    marginal = DurationModelArtifact((), (), (), (), (details["log_duration_location"],),
                                    details["predictive_log_scale"], {}, {}, target_version=EXPERIMENT_TARGET_VERSION)
    distribution = predict_duration_distribution(marginal, {}, elapsed_minutes=elapsed_minutes,
                                                 continuously_wet_confirmed=continuously_wet_confirmed,
                                                 horizons_minutes=(60, 120, 240))
    return {**details, **distribution, "selected_for_primary": False}
