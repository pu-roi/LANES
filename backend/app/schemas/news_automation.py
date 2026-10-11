"""Read-only operational status, separate from source evidence and flood claims."""
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.configuration import NewsCycleSummary, NewsStageHealth
from app.schemas.news_weather import NewsWeatherStatus


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
    stages: dict[str, NewsStageHealth] = Field(default_factory=dict)
    latest_collection_at: datetime | None = None
    feed_counts: dict[str, int] = Field(default_factory=dict)
    queue_counts: dict[str, int] = Field(default_factory=dict)
    error_code: str | None = None
    weather: NewsWeatherStatus | None = None
