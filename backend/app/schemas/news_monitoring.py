"""Saved pipeline state, distinct from unavailable collection-run history."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.news_browsing import BodyStatus, ProcessingStatus


class NewsRetrievalIssue(BaseModel):
    article_id: int
    title: str
    publisher: str
    body_status: BodyStatus
    article_error: str | None
    last_seen_at: datetime


class NewsMonitoringSummary(BaseModel):
    read_only: Literal[True] = True
    articles_total: int
    body_counts: dict[BodyStatus, int]
    latest_processing_counts: dict[ProcessingStatus, int]
    recent_retrieval_issues: list[NewsRetrievalIssue]
    issue_limit: int = 10
    discovery_history: Literal["recorded"] = "recorded"
    fallback_history: Literal["recorded"] = "recorded"
    collection_to_alert_delay: Literal["unavailable"] = "unavailable"
