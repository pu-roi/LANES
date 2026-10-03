"""Staff history DTOs omit actors, raw errors, article bodies and private notes."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FeedAttempt(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    source_id: str
    feed_url: str
    status: str
    checked_at: datetime
    error_code: str | None
    entries_seen: int
    candidates_saved: int
    body_errors: int
    scope_unresolved: int


class FallbackLead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ordinal: int
    article_url: str
    source_id: str | None
    retrieved_at: datetime | None
    retrieval_status: str
    error_code: str | None
    assessment: str | None


class TelemetryAttempt(BaseModel):
    id: int
    status: Literal["running", "completed", "failed", "interrupted"]
    started_at: datetime
    finished_at: datetime | None
    error_code: str | None
    trigger: str | None = None
    article_id: int | None = None
    retrieve_articles: bool | None = None
    retry_after_seconds: int | None = None
    feeds: list[FeedAttempt] = Field(default_factory=list)
    leads: list[FallbackLead] = Field(default_factory=list)


class NewsTelemetryPage(BaseModel):
    read_only: Literal[True] = True
    items: list[TelemetryAttempt]
    total: int
    page: int
    page_size: int
    pages: int
