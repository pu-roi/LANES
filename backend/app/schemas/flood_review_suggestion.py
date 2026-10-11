"""Case-bound staff assistance, separate from operational clearance."""
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool

from app.schemas.flood_subsidence import DurationModelStatus, DurationQuantile


class ReviewSuggestionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    acknowledge_research_limitations: StrictBool
    assume_continuous_wet: StrictBool


class WetEvidence(BaseModel):
    audit_id: int
    review_id: int | None = None
    observed_at: datetime
    available_at: datetime
    provenance: Literal["original_citizen_observation", "accepted_owner_followup"]


class SavedReviewSuggestion(BaseModel):
    id: int
    report_id: int
    request_id: UUID
    issued_at: datetime
    issued_by: int
    suggested_review_at: datetime
    reference: WetEvidence
    latest_wet: WetEvidence
    location_snapshot: dict[str, Any]
    model: DurationModelStatus
    quantiles: list[DurationQuantile]
    assumed_continuous_wet: Literal[True] = True
    research_only: Literal[True] = True
    changes_status_expiry_or_routing: Literal[False] = False


class CaseReviewSuggestion(BaseModel):
    report_id: int
    location: str | None
    zone_id: int | None
    can_issue: bool
    ineligibility_reason: str | None
    reference: WetEvidence | None = None
    latest_wet: WetEvidence | None = None
    suggestion: SavedReviewSuggestion | None = None
    state: Literal["no_suggestion", "scheduled", "due", "evidence_changed", "followup_received", "evidence_stale", "case_closed"]
    state_reason: str | None = None
    evaluated_at: datetime


class ReviewSuggestionQueue(BaseModel):
    cases: list[CaseReviewSuggestion]
    next_before_id: int | None
    evaluated_at: datetime
    page_scanned: int
    research_only: Literal[True] = True
