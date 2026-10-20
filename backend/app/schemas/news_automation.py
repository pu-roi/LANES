"""Read-only operational status, separate from source evidence and flood claims."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.configuration import NewsCycleSummary, NewsStageHealth
from app.schemas.news_weather import NewsWeatherStatus


class NewsAuditDiagnostics(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    state: str = "not_recorded"
    validation_mode: Literal["llm", "source_rules"] = "llm"
    checked_at: datetime | None = None
    next_check_at: datetime | None = None
    used: int | None = None
    limit: int | None = None
    remaining: int | None = None
    request_count: int = 0
    claims_dispatched: int = 0
    http_status: int | None = None
    error_code: str | None = None
    model_next_check_at: datetime | None = None
    failure_phase: str | None = None
    timeout_kind: str | None = None
    elapsed_ms: int | None = None
    actual_model: str | None = None
    boundary_qualified: int | None = None
    boundary_expected: int | None = None
    boundary_missing: int | None = None
    boundary_error: str | None = None


class NewsAutomationStatus(BaseModel):
    read_only: bool = True
    checked_at: datetime
    state: str
    status_label: str
    running: bool
    current_stage: str | None = None
    stage_label: str | None = None
    stage_started_at: datetime | None = None
    last_progress_at: datetime | None = None
    collection_enabled: bool
    processing_enabled: bool
    publication_enabled: bool
    enabled_sources: int
    collection_interval_minutes: int
    scheduler_tick_target_minutes: int
    next_collection_due_at: datetime | None = None
    collection_overdue: bool = False
    last_started_at: datetime | None = None
    last_finished_at: datetime | None = None
    last_successful_at: datetime | None = None
    last_cycle: NewsCycleSummary | None = None
    recent_cycles: list[NewsCycleSummary] = Field(default_factory=list, max_length=10)
    stages: dict[str, NewsStageHealth] = Field(default_factory=dict)
    latest_collection_at: datetime | None = None
    feed_counts: dict[str, int] = Field(default_factory=dict)
    queue_counts: dict[str, int] = Field(default_factory=dict)
    error_code: str | None = None
    weather: NewsWeatherStatus | None = None
    audit: NewsAuditDiagnostics | None = None
