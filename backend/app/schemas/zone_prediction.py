"""Read-only automatically resolved zone research predictions."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.flood_subsidence import DurationModelStatus, DurationQuantile
from app.schemas.flood_subsidence import DurationPreviewResponse


class ZonePredictionEvidence(BaseModel):
    source_kind: Literal["original_citizen_observation", "accepted_owner_followup", "news_decision"]
    source_id: int
    report_id: int | None = None
    observed_at: datetime
    available_at: datetime


class ZonePrediction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    zone_id: int
    state: Literal["estimated", "unavailable", "needs_review", "expired", "inactive"]
    reasons: list[str] = Field(default_factory=list)
    city: str | None = None
    barangays: list[str] = Field(default_factory=list)
    coordinates: tuple[float, float] | None = None
    boundary_revision: str | None = None
    nearby_report_count: int = 0
    evaluated_at: datetime
    prediction_as_of_at: datetime | None = None
    reference: ZonePredictionEvidence | None = None
    latest_wet: ZonePredictionEvidence | None = None
    evidence: list[ZonePredictionEvidence] = Field(default_factory=list)
    model: DurationModelStatus | None = None
    quantiles: list[DurationQuantile] = Field(default_factory=list)
    continuity_assumed: bool = False
    research_only: Literal[True] = True
    changes_status_expiry_or_routing: Literal[False] = False
    pooled_geographic_transfer: bool = False
    warnings: list[str] = Field(default_factory=list)
    registration_simulation: DurationPreviewResponse | None = None
    registration_audit_id: int | None = None
