"""Private read-only cross-location comparison contract."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.flood_subsidence import DurationQuantile


class CrossLocationCalculation(BaseModel):
    log_duration_location: float
    predictive_log_scale: float
    shared_depth_effect: float
    local_effect: float
    coefficient_variance: float
    unseen_location_variance: float
    location_outcomes: int
    transfer_basis: Literal["partial_pooling", "shared_depth_with_unseen_location_prior"]
    uncertainty_method: str


class CrossLocationPrediction(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())
    zone_id: int
    status: Literal["research_comparison", "abstained", "model_unavailable"] = "abstained"
    reason: str | None = None
    selected_for_primary: Literal[False] = False
    changes_status_expiry_or_routing: Literal[False] = False
    selection_blockers: list[str] = Field(default_factory=list)
    validation_summary: str | None = None
    model_sha256: str | None = None
    qualified_rows: int = 0
    shared_outcomes: int = 0
    trained_locations: list[str] = Field(default_factory=list)
    target_location: str | None = None
    depth_cm: float | None = None
    depth_basis: str | None = None
    reference_basis: Literal["observed_reference", "registration_proxy", "submission_proxy"] | None = None
    source_audit_id: int | None = None
    reference_at: datetime | None = None
    source_observed_at: datetime | None = None
    prediction_as_of_at: datetime | None = None
    quantiles: list[DurationQuantile] = Field(default_factory=list)
    calculation: CrossLocationCalculation | None = None
    warnings: list[str] = Field(default_factory=list)
