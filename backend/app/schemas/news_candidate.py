"""Staff-facing source and feed-probe responses for news discovery."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field
from app.schemas.news_extraction import NewsExtractionResult


class NewsSourceSummary(BaseModel):
    id: str
    publisher: str
    article_domains: list[str]
    feed_urls: list[str]
    verified_at: date | None
    enabled: bool


class NewsFeedProbeResult(BaseModel):
    source_id: str
    publisher: str
    feed_url: str
    status: str
    http_status: int | None
    entry_count: int
    publisher_link_count: int
    newest_published_at: datetime | None
    etag: str | None = None
    last_modified: str | None = None
    error: str | None = None


class NewsSourceProbeResponse(BaseModel):
    source_id: str
    results: list[NewsFeedProbeResult]


class NewsFeedEntrySummary(BaseModel):
    source_id: str
    feed_url: str
    feed_guid: str
    first_seen_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}


class NewsArticleSummary(BaseModel):
    id: int
    canonical_url: str
    publisher_source_id: str
    title: str
    excerpt: str
    published_at: datetime | None
    fetched_at: datetime | None
    first_seen_at: datetime
    last_seen_at: datetime
    article_text: str | None
    article_error: str | None
    review_state: str
    feed_entries: list[NewsFeedEntrySummary]

    model_config = {"from_attributes": True}


class NewsSavedExtractionSummary(BaseModel):
    article_id: int
    article_url: str
    input_fingerprint: str
    read_only: Literal[True] = True
    extraction_mode: Literal["rules_only"] = "rules_only"
    extraction: NewsExtractionResult | None
    error: str | None = None


class NewsExtractionRunSummary(BaseModel):
    id: int
    article_version_id: int
    pipeline_version: str
    mode: Literal["rules_only"]
    status: Literal["pending", "processing", "completed", "retry_wait", "failed"]
    attempt_count: int
    next_attempt_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    result: NewsExtractionResult | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NewsProcessingOutcome(BaseModel):
    run_id: int
    article_id: int
    status: Literal["completed", "retry_wait", "failed", "lease_lost"]
    error_code: str | None


class NewsProcessingSummary(BaseModel):
    captured: int
    completed: int
    retry_wait: int
    failed: int
    lease_lost: int
    runs: list[NewsProcessingOutcome]


class OpenLeadRoadUpdate(BaseModel):
    city: str
    road: str
    decision: str
    previous_observed_at: datetime | None
    alternate_observed_at: datetime | None
    previous_depth: str | None
    alternate_depth: str | None
    previous_condition: str | None
    alternate_condition: str | None


class OpenLeadEventReview(BaseModel):
    status: str
    shared_places: list[str]
    shared_roads: list[str]
    conflicts: list[str]
    missing_evidence: list[str]
    duplicate_of: str | None = None
    road_updates: list[OpenLeadRoadUpdate] = Field(default_factory=list)


class OpenSearchHitSummary(BaseModel):
    url: str
    title: str
    seen_at: datetime | None
    relationship: str
    query_kind: str
    publisher_source_id: str | None = None
    article_text: str | None = None
    article_error: str | None = None
    fetched_at: datetime | None = None
    match_status: str = "unverified_index_lead"
    published_at: datetime | None = None
    event_review: OpenLeadEventReview | None = None


class OpenSearchLookupSummary(BaseModel):
    article_url: str
    searched_at: datetime
    evidence_status: str
    results: list[OpenSearchHitSummary]
    errors: list[str]
    retry_after_seconds: int | None = None


class NewsDiscoveryNotice(BaseModel):
    source_id: str
    article_url: str
    reason: str


class NewsDiscoveryRunSummary(BaseModel):
    probes: list[NewsFeedProbeResult]
    new_or_updated_candidates: int
    notices: list[NewsDiscoveryNotice] = Field(default_factory=list)


class NewsFeedCheckpointSummary(BaseModel):
    source_id: str
    feed_url: str
    last_checked_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None

    model_config = {"from_attributes": True}


class ManualNewsCandidateInput(BaseModel):
    title: str
    text: str
    source_url: str | None = None
    publisher: str = "Staff DRRMO / Social Post"
