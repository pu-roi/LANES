"""Read-only identities refer to a claim's ordinal in a stored extraction run."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.news_browsing import NewsCapturedInput, NewsNativeCapturedInput, NewsPublisherOption
from app.schemas.news_ner_result import NewsNerResult, NerProjectedClaim
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
    result_kind: Literal['legacy_claim'] = 'legacy_claim'
    processing_method: Literal['rules_only'] = 'rules_only'
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


class NewsNativeResultItem(NewsResultItem):
    result_kind: Literal['ner_group'] = 'ner_group'
    processing_method: Literal['ner_rules_v1'] = 'ner_rules_v1'
    group_id: str
    claim_index: int | None


class NewsResultPage(BaseModel):
    items: list[NewsNativeResultItem | NewsResultItem]
    total: int
    page: int
    page_size: int
    pages: int
    publishers: list[NewsPublisherOption]
    scope: Literal["latest_reported_locations"] = "latest_reported_locations"
    read_only: Literal[True] = True


class NewsResultLifecycle(BaseModel):
    state: Literal['not_projected','not_evaluated','evaluation_pending','evaluation_failed','evaluated',
                   'unpublished','active_alert','active_zone','withdrawn','expired']
    case_id: int | None = None
    evaluation_id: int | None = None
    decision_id: int | None = None
    review_state: str | None = None
    reason_code: str | None = None


class NewsSourceReview(BaseModel):
    """Current collection body and immutable extraction input remain separate."""
    state: Literal['matching_capture', 'different_capture', 'current_unavailable']
    current_input: NewsCapturedInput | None = None
    current_fetched_at: datetime | None = None
    selected_captured_at: datetime


class NewsResultDetail(BaseModel):
    source_review: NewsSourceReview | None = None
    item: NewsNativeResultItem | NewsResultItem
    claim: NerProjectedClaim | ExtractedClaim
    captured_input: NewsNativeCapturedInput | NewsCapturedInput
    input_fingerprint: str
    pipeline_version: str
    extraction_errors: list[str]
    is_metadata_only: bool
    lifecycle_status: Literal["not_available"] = "not_available"
    lifecycle: NewsResultLifecycle | None = None
    read_only: Literal[True] = True


class NewsNativeGroupDetail(BaseModel):
    source_review: NewsSourceReview | None = None
    supporting_passages: list[str] = Field(default_factory=list)
    depth_scope: Literal['shared', 'individual', 'unknown'] = 'unknown'
    historical_outputs: list[dict] = Field(default_factory=list)
    claim: NewsResultClaim
    extraction_errors: list[str] = Field(default_factory=list)
    is_metadata_only: Literal[False] = False
    item: NewsNativeResultItem
    group: dict
    result: NewsNerResult
    captured_input: NewsNativeCapturedInput
    input_fingerprint: str
    pipeline_version: str
    lifecycle: NewsResultLifecycle
    read_only: Literal[True] = True


class NewsResultPlacementPreview(BaseModel):
    """Current catalog computation from immutable claim evidence; never stored by GET."""
    run_id: int
    claim_index: int
    input_fingerprint: str
    evidence_pipeline_version: str
    placement_revision: str
    claim: NerProjectedClaim | ExtractedClaim
    preview: NewsPlacementPreview
    read_only: Literal[True] = True


class NewsMapTarget(BaseModel):
    zone_id: int | None = None
    claim_index: int | None = None
    read_only: Literal[True] = True
