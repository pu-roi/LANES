"""Read contracts for staff article browsing; no publication or review writes."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.news_candidate import NewsArticleSummary, NewsExtractionRunSummary
from app.schemas.news_presentation import NewsFloodSummary

BodyStatus = Literal["available", "missing", "error"]
ProcessingStatus = Literal["not_recorded", "pending", "processing", "completed", "retry_wait", "failed"]
ArticleOrder = Literal["recently_seen", "publication_newest"]


class NewsPublisherOption(BaseModel):
    id: str
    label: str


class NewsArticleListItem(BaseModel):
    id: int
    title: str
    excerpt: str
    canonical_url: str
    publisher_source_id: str
    publisher: str
    published_at: datetime | None
    last_seen_at: datetime
    body_status: BodyStatus
    article_error: str | None
    review_state: str
    processing_status: ProcessingStatus
    latest_run_id: int | None


class NewsArticlePage(BaseModel):
    items: list[NewsArticleListItem]
    total: int
    page: int
    page_size: int
    pages: int
    publishers: list[NewsPublisherOption]


class NewsCapturedInput(BaseModel):
    canonical_url: str
    publisher: str
    title: str
    excerpt: str = ""
    article_text: str | None = None
    published_at: datetime | None = None


class NewsArticleVersionSummary(BaseModel):
    id: int
    input_fingerprint: str
    input_snapshot: NewsCapturedInput
    created_at: datetime

    model_config = {"from_attributes": True}


class NewsArticleDetail(BaseModel):
    article: NewsArticleSummary
    publisher: str
    body_status: BodyStatus
    runs: list[NewsExtractionRunSummary]
    versions: list[NewsArticleVersionSummary]
    history_total: int
    history_limit: int
    flood_summaries: dict[int, list[NewsFloodSummary]]
    read_only: Literal[True] = True
