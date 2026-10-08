"""Research prediction contracts; separate from persistent flood-zone models."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DurationPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    city: str = Field(min_length=1, max_length=80)
    barangay: str = Field(min_length=1, max_length=80)
    reference_at: datetime
    prediction_as_of_at: datetime
    reference_policy: Literal["first_recorded_wet_in_episode"]
    acknowledge_research_limitations: bool = False
    assume_continuous_wet: bool = False
    allow_pooled_pasig_transfer: bool = False

    @field_validator("reference_at", "prediction_as_of_at")
    @classmethod
    def aware_clock(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Prediction clocks require a timezone offset.")
        return value

    @model_validator(mode="after")
    def chronological(self) -> "DurationPreviewRequest":
        if self.prediction_as_of_at < self.reference_at:
            raise ValueError("Prediction issuance cannot precede the wet reference.")
        return self


class DurationModelStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=("model_validate", "model_dump"))
    status: Literal["research_model_available", "model_unavailable"]
    algorithm: Literal["intercept_only_lognormal_aft"] = "intercept_only_lognormal_aft"
    model_fitted: bool
    research_only: Literal[True] = True
    deployment_eligible: Literal[False] = False
    target_version: str | None = None
    model_sha256: str | None = None
    projections: int = 0
    shared_outcomes: int = 0
    supported_barangays: list[str] = Field(default_factory=list)
    prediction_barangays: list[str] = Field(default_factory=list)
    geographic_policy: str = "training_cohort_only_unless_explicit_pooled_transfer"
    prospective_accuracy_established: Literal[False] = False
    learns_depth_or_location_effects: Literal[False] = False
    limitations: list[str] = Field(default_factory=list)


class DurationQuantile(BaseModel):
    quantile: float
    remaining_minutes: float
    estimated_reported_subsidence_at: datetime


class DurationHorizonProbability(BaseModel):
    horizon_minutes: float
    conditional_probability_reported_subsidence: float


class DurationPreviewResponse(BaseModel):
    status: Literal["research_estimate", "abstained"]
    model: DurationModelStatus
    reference_at: datetime
    prediction_as_of_at: datetime
    reference_policy: str
    input_provenance: Literal["staff_supplied_hypothetical_not_verified_case_evidence", "admin_registration_proxy_simulation"] = "staff_supplied_hypothetical_not_verified_case_evidence"
    assumed_continuous_wet: bool
    abstention_reason: str | None = None
    quantiles: list[DurationQuantile] = Field(default_factory=list)
    horizon_probabilities: list[DurationHorizonProbability] = Field(default_factory=list)
    changes_status_expiry_or_routing: Literal[False] = False
    confirms_physical_dryness_or_passability: Literal[False] = False
    pooled_geographic_transfer: bool = False


class PassabilityPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    city: str = Field(min_length=1, max_length=80)
    barangay: str = Field(min_length=1, max_length=80)
    reference_at: datetime
    prediction_as_of_at: datetime
    acknowledge_research_limitations: bool = False
    assume_continuous_nonpassability: bool = False
    allow_pooled_pasig_transfer: bool = False

    @model_validator(mode="after")
    def clocks(self) -> "PassabilityPreviewRequest":
        if any(value.tzinfo is None or value.utcoffset() is None for value in (self.reference_at, self.prediction_as_of_at)):
            raise ValueError("Passability prediction clocks require timezone offsets.")
        if self.prediction_as_of_at < self.reference_at:
            raise ValueError("Issuance precedes nonpassable reference.")
        return self


class PassabilityQuantile(BaseModel):
    quantile: float
    remaining_minutes: float
    estimated_reported_passability_at: datetime


class PassabilityPreview(BaseModel):
    status: Literal["research_estimate", "abstained"]
    model: DurationModelStatus
    reference_at: datetime
    prediction_as_of_at: datetime
    abstention_reason: str | None = None
    pooled_geographic_transfer: bool = False
    quantiles: list[PassabilityQuantile] = Field(default_factory=list)
    changes_status_expiry_or_routing: Literal[False] = False
    confirms_physical_dryness_or_safe_passage: Literal[False] = False
