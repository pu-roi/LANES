"""Pydantic schemas for Taglish flood evidence extraction."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field
from app.schemas.news_placement import NewsPlacementPreview
from app.schemas.news_audit import IndependentAuditResult


CanonicalDepth = Literal[
    "gutter",
    "half-knee",
    "half-tire",
    "knee",
    "tires",
    "waist",
    "chest",
    "neck",
]

FloodCondition = Literal[
    "active",
    "rising",
    "receding",
    "subsided",
    "unknown",
]

PlaceType = Literal[
    "barangay",
    "street",
    "landmark",
    "city",
    "province",
    "unknown",
]


class NewsArticleExtractorInput(BaseModel):
    """Read-only extractor input from persisted news_articles or lead entries."""

    article_id: int
    canonical_url: str
    publisher: str
    title: str
    excerpt: str = ""
    article_text: str | None = None
    published_at: datetime | None = None
    fetched_at: datetime | None = None


class LLMAuditResult(BaseModel):
    """Backward-compatible hybrid projection; durable audits use strict evidence."""

    is_confirmed: bool
    status_classification: Literal["active", "rising", "receding", "subsided", "forecast", "negated", "unclear"] = "unclear"
    depth_confirmed: bool = False
    depth_discrepancy_note: str | None = None
    is_forecast: bool = False
    is_subsided: bool = False
    is_negated: bool = False
    audit_notes: str = ""
    place_confirmed: bool = False
    time_confirmed: bool = False
    independent_audit: IndependentAuditResult | None = None


class RankedLocationCandidate(BaseModel):
    """Nationwide ranked geographic suggestion; geometry may be preview-only."""

    raw_place_name: str
    resolved_province: str | None = None
    resolved_city: str | None = None
    resolved_barangay: str | None = None
    resolved_road: str | None = None
    resolved_landmark: str | None = None
    island_group: str | None = None
    psgc_code: str | None = None

    precision_level: Literal["road", "landmark", "barangay", "city", "unresolved"] = "unresolved"
    confidence_score: float = 0.0
    score_rationale: str = ""

    geometry_geojson: dict | None = None  # Preview polygon unless exact segment verified
    source_geometry_geojson: dict | None = None  # Suggested centreline / point GeoJSON
    representative_point: tuple[float, float] | None = None  # (lat, lng)
    geometry_provenance: Literal["none", "offline_anchor", "caller_coordinate", "verified_segment"] = "none"

    is_auto_approvable: bool = False
    requires_staff_edit: bool = False


class RoadPlacementCandidate(BaseModel):
    """Mapped centerline evidence; never an observed flood width or closure."""

    candidate_id: str
    kind: Literal["reported_span", "road_section"]
    centerline_geojson: dict
    osm_way_ids: list[int]
    cross_streets: list[list[str]] = Field(default_factory=list)
    approximate_length_m: float | None = None
    ambiguous_carriageway: bool = False


class RoadPlacementEvidence(BaseModel):
    status: Literal["bounded_candidate", "ambiguous", "unresolved", "source_unavailable"]
    reason: str
    source_id: str | None = None
    snapshot_at: datetime | None = None
    catalog_sha256: str | None = None
    osm_sha256: str | None = None
    city_relation_id: int | None = None
    barangay_catalog_sha256: str | None = None
    barangay_source_id: str | None = None
    barangay_psgc_code: str | None = None
    barangay_osm_relation_id: int | None = None
    barangay_source_url: str | None = None
    barangay_source_classification: Literal["osm_community", "reviewed_source"] | None = None
    barangay_boundary_status: Literal["not_required", "available", "unavailable"] = "not_required"
    candidates: list[RoadPlacementCandidate] = Field(default_factory=list, max_length=25)
    total_candidate_count: int = 0
    candidates_truncated: bool = False
    proves_current_flood: Literal[False] = False
    may_affect_routing: Literal[False] = False


class ExtractedClaim(BaseModel):
    """An evidence-linked structured flood claim for a specific location."""

    raw_place_name: str
    canonical_barangay: str | None = None
    canonical_city: str | None = None
    canonical_province: str | None = None
    canonical_road: str | None = None
    road_segment_raw: str | None = None
    local_area_raw: str | None = None
    island_group: str | None = None
    psgc_code: str | None = None

    place_type: PlaceType = "unknown"
    place_char_start: int
    place_char_end: int

    flood_mentioned: bool = True
    is_negated: bool = False
    is_forecast: bool = False
    is_historical: bool = False
    road_passability: Literal["passable_all", "passable_with_caution", "passable_unspecified", "light_vehicle_closed", "impassable_all", "unknown"] = "unknown"

    depth_raw: str | None = None
    depth_canonical: CanonicalDepth | None = None
    depth_rule: str | None = None
    depth_meters: float | None = None
    depth_inches: float | None = None
    depth_formatted: str | None = None

    condition: FloodCondition = "unknown"

    event_time_raw: str | None = None
    event_time_resolved: datetime | None = None
    event_time_kind: Literal["observation", "report", "unspecified"] = "unspecified"

    evidence_sentence: str
    evidence_sentence_offset: tuple[int, int]

    uncertainty_reasons: list[str] = Field(default_factory=list)
    confidence_score: float = 1.0

    # Auto-approval and spatial geometry extensions
    action_type: str | None = None
    action_rationale: str | None = None
    audit_result: LLMAuditResult | None = None
    ranked_location: RankedLocationCandidate | None = None
    road_placement: RoadPlacementEvidence | None = None
    placement_preview: NewsPlacementPreview | None = None


class NewsExtractionResult(BaseModel):
    """Full extraction result for an article, maintaining provenance and claims."""

    article_id: int
    canonical_url: str
    is_metadata_only: bool
    processed_text_length: int
    claims: list[ExtractedClaim] = Field(default_factory=list)
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    extractor_version: str = "taglish-rules-v1.0"
    errors: list[str] = Field(default_factory=list)
