"""Staff-facing source and feed-probe responses for news discovery."""

from datetime import date, datetime

from pydantic import BaseModel


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


class NewsDiscoveryRunSummary(BaseModel):
    probes: list[NewsFeedProbeResult]
    new_or_updated_candidates: int


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
