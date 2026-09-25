"""Pydantic schemas for Taglish flood evidence extraction."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


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
    """Audit result from Gemini 1.5 Flash supporting double-check verification."""

    is_confirmed: bool
    status_classification: Literal["active", "rising", "receding", "subsided", "forecast", "negated", "unclear"] = "unclear"
    depth_confirmed: bool = False
    depth_discrepancy_note: str | None = None
    is_forecast: bool = False
    is_subsided: bool = False
    is_negated: bool = False
    audit_notes: str = ""


class RankedLocationCandidate(BaseModel):
    """Nationwide ranked geographic candidate with generated avoidance geometry."""

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

    geometry_geojson: dict | None = None  # Authoritative avoidance polygon GeoJSON
    source_geometry_geojson: dict | None = None  # Centreline / point GeoJSON
    representative_point: tuple[float, float] | None = None  # (lat, lng)

    is_auto_approvable: bool = False
    requires_staff_edit: bool = False


class ExtractedClaim(BaseModel):
    """An evidence-linked structured flood claim for a specific location."""

    raw_place_name: str
    canonical_barangay: str | None = None
    canonical_city: str | None = None
    canonical_province: str | None = None
    canonical_road: str | None = None
    island_group: str | None = None
    psgc_code: str | None = None

    place_type: PlaceType = "unknown"
    place_char_start: int
    place_char_end: int

    flood_mentioned: bool = True
    is_negated: bool = False
    is_forecast: bool = False
    is_historical: bool = False

    depth_raw: str | None = None
    depth_canonical: CanonicalDepth | None = None
    depth_rule: str | None = None

    condition: FloodCondition = "unknown"

    event_time_raw: str | None = None
    event_time_resolved: datetime | None = None

    evidence_sentence: str
    evidence_sentence_offset: tuple[int, int]

    uncertainty_reasons: list[str] = Field(default_factory=list)
    confidence_score: float = 1.0

    # Auto-approval and spatial geometry extensions
    action_type: str | None = None
    action_rationale: str | None = None
    ranked_location: RankedLocationCandidate | None = None


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
