"""Bounded staff browsing contracts; no persistence models."""
from typing import Any, Literal
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
    duration_seconds: int
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
