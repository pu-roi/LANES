"""Read-only analytical placement; these contracts cannot activate a zone."""
from typing import Literal
from datetime import datetime

from pydantic import BaseModel, Field


class PlacementHistoryRow(BaseModel):
    source_year: str
    source_record_no: str
    barangay: str
    street: str
    landmark: str


class PlacementFragment(BaseModel):
    fragment_id: str
    centerline_geojson: dict
    approximate_length_m: float = Field(gt=0)
    return_period: Literal[5, 25, 100]
    hazard_class: Literal[1, 2, 3]
    noah_source_id: str
    noah_archive_sha256: str


class PlacementSection(BaseModel):
    candidate_id: str
    kind: Literal["reported_span", "road_section"]
    centerline_geojson: dict
    osm_way_ids: list[int]
    cross_streets: list[list[str]]
    ambiguous_carriageway: bool
    article_place_level: int = Field(ge=0, le=3)
    approximate_length_m: float = Field(ge=0)
    modeled_overlap_m: dict[int, dict[int, float]] = Field(default_factory=dict)
    modeled_overlap_fraction: dict[int, float] = Field(default_factory=dict)
    matching_history: list[PlacementHistoryRow] = Field(default_factory=list)
    modeled_fragments: list[PlacementFragment] = Field(default_factory=list, max_length=512)
    preview_geometry: dict | None = None
    fragment_status: Literal["available", "no_modeled_overlap", "source_unavailable"] = "source_unavailable"


class NewsPlacementPreview(BaseModel):
    status: Literal["predicted_candidate", "ambiguous", "unresolved", "source_unavailable"]
    reason: str
    selected_candidate_id: str | None = None
    placement_kind: Literal["reported", "predicted"] | None = None
    candidates: list[PlacementSection] = Field(default_factory=list, max_length=25)
    total_candidate_count: int = 0
    candidates_truncated: bool = False
    osm_source_id: str | None = None
    osm_catalog_sha256: str | None = None
    osm_snapshot_at: datetime | None = None
    city_relation_id: int | None = None
    barangay_catalog_sha256: str | None = None
    barangay_source_id: str | None = None
    barangay_psgc_code: str | None = None
    barangay_boundary_status: Literal["not_required", "available", "unavailable"] = "not_required"
    reported_severity: Literal["low", "medium", "high", "extreme"] | None = None
    noah_catalog_sha256: str | None = None
    noah_source_ids: dict[int, str] = Field(default_factory=dict)
    noah_attribution: str | None = None
    history_status: Literal["not_applicable", "available", "source_unavailable"] = "not_applicable"
    history_sha256: str | None = None
    unmatched_history: list[PlacementHistoryRow] = Field(default_factory=list)
    uncertainty_reasons: list[str] = Field(default_factory=list)
    proves_current_flood: Literal[False] = False
    may_affect_routing: Literal[False] = False
    read_only: Literal[True] = True
