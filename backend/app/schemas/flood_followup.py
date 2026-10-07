"""Private, structured same-location observations; review is not model admission."""
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_serializer, field_validator, model_validator

from app.schemas.common import ensure_utc, serialize_utc_datetime

FloodCondition = Literal["still_flooded", "subsided"]
ReviewState = Literal["pending", "accepted", "rejected"]


class EvidenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    evidence_text: str = Field(min_length=10, max_length=2000)


class FloodFollowupCreate(EvidenceInput):
    request_id: UUID
    condition: FloodCondition
    observed_at: datetime
    depth_cm: float | None = Field(default=None, ge=0, le=1000, allow_inf_nan=False, strict=True)
    source_url: str | None = Field(default=None, max_length=500)
    same_location_confirmed: StrictBool

    @field_validator("observed_at")
    @classmethod
    def validate_observation_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Observation time must include a timezone.")
        value = value.astimezone(timezone.utc)
        if value > datetime.now(timezone.utc):
            raise ValueError("Observation time cannot be in the future.")
        return value

    @field_validator("source_url", mode="before")
    @classmethod
    def normalize_source_url(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            parsed = urlsplit(value)
            valid = (parsed.scheme == "https" and bool(parsed.hostname)
                     and parsed.username is None and parsed.password is None
                     and not any(character.isspace() or ord(character) < 32 for character in value))
            _ = parsed.port
        except ValueError as exc:
            raise ValueError("Source URL must be a valid HTTPS URL without credentials.") from exc
        if not valid:
            raise ValueError("Source URL must be a valid HTTPS URL without credentials.")
        return value

    @model_validator(mode="after")
    def validate_condition(self) -> "FloodFollowupCreate":
        if not self.same_location_confirmed:
            raise ValueError("Confirm that the observation concerns the original location.")
        if self.condition == "subsided" and self.depth_cm is not None and self.depth_cm > 0:
            raise ValueError("A subsided observation cannot have a positive flood depth.")
        if self.condition == "still_flooded" and self.depth_cm == 0:
            raise ValueError("A still-flooded observation cannot have zero depth.")
        return self


class FloodFollowupReviewCreate(EvidenceInput):
    decision: Literal["accepted", "rejected"]
    same_location_verified: StrictBool

    @model_validator(mode="after")
    def validate_acceptance(self) -> "FloodFollowupReviewCreate":
        if self.decision == "accepted" and not self.same_location_verified:
            raise ValueError("Accepting requires verification of the original location.")
        return self


class FollowupLocationSnapshot(BaseModel):
    report_id: int
    city: str
    barangay: str | None
    human_readable_location: str
    geometry_sha256: str
    zone_id: int | None
    event_id: int | None


class FloodFollowupReviewResponse(BaseModel):
    id: int
    decision: Literal["accepted", "rejected"]
    reviewer_id: int
    reviewed_at: datetime
    evidence_text: str
    same_location_verified: bool

    @field_serializer("reviewed_at")
    def serialize_review_time(self, value: datetime) -> str:
        return serialize_utc_datetime(ensure_utc(value).astimezone(timezone.utc))


class FloodFollowupResponse(BaseModel):
    id: int
    request_id: UUID
    report_id: int
    user_id: int
    condition: FloodCondition
    observed_at: datetime
    submitted_at: datetime
    evidence_text: str
    depth_cm: float | None
    source_url: str | None
    same_location_confirmed: bool
    location_snapshot: FollowupLocationSnapshot
    original_observed_at: datetime | None
    original_available_at: datetime | None = None
    original_observation_audit_id: int | None = None
    review_state: ReviewState
    review: FloodFollowupReviewResponse | None
    source_claim_only: Literal[True] = True
    model_admitted: Literal[False] = False

    @field_serializer("observed_at", "submitted_at", "original_observed_at", "original_available_at")
    def serialize_followup_times(self, value: datetime | None) -> str | None:
        return (serialize_utc_datetime(ensure_utc(value).astimezone(timezone.utc))
                if value is not None else None)


class OwnerFloodFollowupsResponse(BaseModel):
    follow_ups: list[FloodFollowupResponse]
    can_submit: bool
    ineligibility_reason: str | None


class StaffFloodFollowupsResponse(BaseModel):
    follow_ups: list[FloodFollowupResponse]
    next_before_id: int | None


class FloodFollowupsExportResponse(StaffFloodFollowupsResponse):
    schema_version: Literal[1] = 1
    generated_at: datetime
    target_version: Literal["pasig_same_location_observation_v1"] = "pasig_same_location_observation_v1"
    training_admitted: Literal[False] = False

    @field_serializer("generated_at")
    def serialize_export_time(self, value: datetime) -> str:
        return serialize_utc_datetime(ensure_utc(value).astimezone(timezone.utc))
