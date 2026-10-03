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
