"""Read-only identities refer to a claim's ordinal in a stored extraction run."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.news_browsing import NewsCapturedInput, NewsPublisherOption
from app.schemas.news_extraction import ExtractedClaim, FloodCondition
from app.schemas.news_presentation import NewsFloodSummary
from app.schemas.news_placement import NewsPlacementPreview

PlacementFilter = Literal["bounded_candidate", "ambiguous", "unresolved", "source_unavailable", "not_recorded"]
ResultOrder = Literal["extraction_newest", "publication_newest"]


class NewsResultPlacement(BaseModel):
    status: str
    reason: str


class NewsResultClaim(BaseModel):
    raw_place_name: str
    canonical_city: str | None = None
    canonical_barangay: str | None = None
    canonical_road: str | None = None
    depth_raw: str | None = None
    depth_formatted: str | None = None
    condition: FloodCondition = "unknown"
    event_time_resolved: datetime | None = None
    event_time_kind: Literal["observation", "report", "unspecified"] = "unspecified"
    evidence_sentence: str
    uncertainty_reasons: list[str] = Field(default_factory=list)
    is_historical: bool = False
    is_forecast: bool = False
    is_negated: bool = False
    road_passability: str = "unknown"
    action_type: str | None = None
    road_placement: NewsResultPlacement | None = None


class NewsResultItem(BaseModel):
    key: str
    run_id: int
    claim_index: int
    article_id: int
    article_version_id: int
    title: str
    publisher_source_id: str
    publisher: str
    published_at: datetime | None = None
    extracted_at: datetime | None = None
    captured_at: datetime
    saved_at: datetime
    claim: NewsResultClaim
    summary: NewsFloodSummary


class NewsResultPage(BaseModel):
    items: list[NewsResultItem]
    total: int
    page: int
    page_size: int
    pages: int
    publishers: list[NewsPublisherOption]
    scope: Literal["latest_reported_locations"] = "latest_reported_locations"
    read_only: Literal[True] = True


class NewsResultDetail(BaseModel):
    item: NewsResultItem
    claim: ExtractedClaim
    captured_input: NewsCapturedInput
    input_fingerprint: str
    pipeline_version: str
    extraction_errors: list[str]
    is_metadata_only: bool
    lifecycle_status: Literal["not_available"] = "not_available"
    read_only: Literal[True] = True


class NewsResultPlacementPreview(BaseModel):
    """Current catalog computation from immutable claim evidence; never stored by GET."""
    run_id: int
    claim_index: int
    input_fingerprint: str
    evidence_pipeline_version: str
    placement_revision: str
    claim: ExtractedClaim
    preview: NewsPlacementPreview
    read_only: Literal[True] = True
