"""Source-aware inspection contracts; news decisions are not implemented here."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.news_results import NewsResultDetail
from app.schemas.report import FloodReportResponse

ReviewSource = Literal["all", "user_reports", "news_claims"]


class SpatialReviewMember(BaseModel):
    key: str
    source: Literal["user_report", "news_claim"]
    report_id: int | None = None
    run_id: int | None = None
    claim_index: int | None = None
    title: str
    location: str
    evidence: str
    review_reason: str
    queued_at: datetime
    severity: str | None = None
    depth: str | None = None
    city: str | None = None
    barangay: str | None = None


class SpatialReviewItem(SpatialReviewMember):
    member_count: int = 1
    members: list[SpatialReviewMember] = Field(default_factory=list)
    group_reason: str | None = None
    location_summary: str = ""
    area_summary: str = ""
    severity_levels: list[str] = Field(default_factory=list)
    depth_levels: list[str] = Field(default_factory=list)


class SpatialReviewFacets(BaseModel):
    cities: list[str] = Field(default_factory=list)
    barangays: list[str] = Field(default_factory=list)


class SpatialReviewPage(BaseModel):
    items: list[SpatialReviewItem]
    total: int
    page: int
    page_size: int
    pages: int
    counts: dict[str, int]
    item_total: int
    facets: SpatialReviewFacets = Field(default_factory=SpatialReviewFacets)
    read_only: Literal[True] = True


class SpatialReviewMembersPage(BaseModel):
    key: str
    group_reason: str | None = None
    items: list[SpatialReviewMember]
    total: int
    page: int
    page_size: int
    pages: int
    read_only: Literal[True] = True


class SpatialReviewDetail(BaseModel):
    key: str
    source: Literal["user_report", "news_claim"]
    is_current_review: bool
    report: FloodReportResponse | None = None
    news: NewsResultDetail | None = None
    news_actions_available: Literal[False] = False
