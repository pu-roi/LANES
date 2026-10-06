"""Staff collection monitoring over existing evidence; no schema changes."""

from typing import Literal

from pydantic import BaseModel

from app.schemas.news_browsing import NewsArticleListItem, NewsPublisherOption

CollectionStatus = Literal["ready", "needs_checking", "excluded", "no_locations", "waiting", "processing", "processing_failed", "retrieval_failed", "missing_text"]
CollectionFilter = Literal["attention", "all", "ready", "needs_checking", "excluded", "no_locations", "waiting", "processing", "processing_failed", "retrieval_failed", "missing_text"]


class NewsCollectionItem(NewsArticleListItem):
    collection_status: CollectionStatus
    collection_label: str
    collection_reason: str
    location_count: int
    questionable_count: int


class NewsCollectionPage(BaseModel):
    items: list[NewsCollectionItem]
    total: int
    page: int
    page_size: int
    pages: int
    publishers: list[NewsPublisherOption]
    counts: dict[CollectionStatus, int]
    read_only: Literal[True] = True
