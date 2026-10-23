"""Bounded staff browsing contracts; no persistence models."""
from typing import Any, Literal
from datetime import datetime, date
from pydantic import BaseModel, Field
from app.schemas.flood_event import FloodEventResponse, FloodEventLocationResponse


class MapFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any]
    properties: dict[str, Any]


class MapPage(BaseModel):
    features: list[MapFeature] = Field(default_factory=list)
    heatmap_features: list[MapFeature] = Field(default_factory=list)
    bounds: tuple[float, float, float, float] | None = None
    total: int = 0
    mapped_count: int = 0
    unmapped_count: int = 0
    viewport_count: int = 0
    next_cursor: int | None = None


class ZoneCount(BaseModel):
    total: int


class HistoryCard(FloodEventResponse):
    locations: list[FloodEventLocationResponse]
    duration_seconds: int | None
    duration_minutes: int | None
    evidence_count: int
    supporting_report_count: int
    reporter_count: int
    zone_count: int
    active_zone_count: int
    location_count: int


class HistoryRecordsPage(BaseModel):
    items: list[HistoryCard]
    total: int
    page: int
    pages: int
    page_size: int


class HistoryInspection(HistoryCard):
    media_count: int
    reports: list[dict[str, Any]] = Field(default_factory=list)
    zones: list[dict[str, Any]] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)


class InspectionPage(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    pages: int
    page_size: int


class HistoryNewsSource(BaseModel):
    article_id: int
    article_version_id: int
    run_id: int
    claim_index: int | None
    group_id: str | None
    title: str | None
    publisher: str | None
    source_url: str | None
    published_at: datetime | None
    published_date: date | None = None
    captured_text_available: bool
    excerpt: str | None
    observed_at: datetime | None
    occurrence_date: date | None
    precision: Literal['instant', 'date', 'unknown']
    road: str | None
    city: str | None
    barangay: str | None
    depth_raw: str | None
    depth_normalized: str | None
    passability: str | None
    condition: str | None
    extraction_mode: str
    extraction_status: str
    completed_at: datetime | None
    pipeline_version: str
    geometry_basis: str | None
    geometry_provenance: dict[str, Any] | None
    closure_basis: str
