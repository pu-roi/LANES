"""Versioned operational settings; arbitrary JSON is never accepted as policy."""
from datetime import datetime
from typing import Annotated, Any
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, ValidationInfo, field_validator
from app.services.flood_depth import FLOOD_DEPTH_MEASUREMENTS

DEPTH_KEYS = (*FLOOD_DEPTH_MEASUREMENTS, "unknown")
Minutes = Annotated[StrictInt, Field(ge=30, le=120)]


def default_sources() -> list[str]:
    from app.services.news_sources import load_news_sources
    return sorted(s.id for s in load_news_sources() if s.enabled and s.verified_at)


class OperationalSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    staff_road_buffer_metres: float = Field(default=25, ge=1, le=100, allow_inf_nan=False, strict=True)
    automatic_expiry_enabled: StrictBool = True
    pasig_ml_expiry_enabled: StrictBool = True
    evidence_expiry_minutes: dict[str, Minutes] = Field(default_factory=lambda: dict.fromkeys(DEPTH_KEYS, 120))
    news_unconfirmed_retention_hours: StrictInt = Field(default=24, ge=1, le=72)
    citizen_auto_approval_enabled: StrictBool = False
    citizen_min_trust: StrictInt = Field(default=75, ge=0, le=100)
    citizen_min_accuracy: StrictInt = Field(default=90, ge=0, le=100)
    citizen_min_human_reviews: StrictInt = Field(default=5, ge=1, le=100)
    news_collection_enabled: StrictBool = True
    news_processing_enabled: StrictBool = True
    news_publication_enabled: StrictBool = True
    news_collection_interval_minutes: StrictInt = 30
    news_source_ids: list[str] = Field(default_factory=default_sources, max_length=100)

    @field_validator("evidence_expiry_minutes")
    @classmethod
    def depths(cls, value: dict[str, int]) -> dict[str, int]:
        if set(value) != set(DEPTH_KEYS):
            raise ValueError("Provide every canonical depth and unknown depth.")
        return value

    @field_validator("news_collection_interval_minutes")
    @classmethod
    def interval(cls, value: int) -> int:
        if value not in (15, 30, 60):
            raise ValueError("Collection interval must be 15, 30 or 60 minutes.")
        return value

    @field_validator("news_source_ids")
    @classmethod
    def sources(cls, value: list[str], info: ValidationInfo) -> list[str]:
        # Persisted history may contain a publisher retired from the registry.
        # New writes still accept only currently verified publishers.
        history = bool(info.context and info.context.get("persisted_history"))
        if len(set(value)) != len(value) or (not history and not set(value).issubset(default_sources())):
            raise ValueError("Select distinct sources from the verified publisher registry.")
        return sorted(value)


class ConfigurationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: StrictInt = Field(ge=0)
    settings: OperationalSettings


class NewsStageHealth(BaseModel):
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    outcome: str = "not_recorded"
    counts: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class ConfigurationRuntime(BaseModel):
    last_started_at: datetime | None = None
    last_finished_at: datetime | None = None
    last_successful_at: datetime | None = None
    next_collection_at: datetime | None = None
    running: bool = False
    error_code: str | None = None
    stage_counts: dict[str, dict[str, int]] = Field(default_factory=dict)
    stage_outcomes: dict[str, str] = Field(default_factory=dict)
    stages: dict[str, NewsStageHealth] = Field(default_factory=dict)
    scheduler_tick_minutes: int = 15


class ConfigurationResponse(BaseModel):
    settings: OperationalSettings
    revision: int
    updated_at: datetime | None = None
    updated_by: int | None = None
    can_edit: bool
    depth_options: list[dict[str, str]]
    source_options: list[dict[str, str]]
    automatic_news_buffer_metres: float = 25
    supported_options: dict[str, Any] = Field(default_factory=lambda: {
        "configuration_schema": OperationalSettings.model_json_schema(), "collection_intervals_minutes": [15, 30, 60]})
    runtime: ConfigurationRuntime
