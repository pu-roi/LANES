"""Read-only staff zone queue; no persistence or publication changes."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.report import FloodAvoidanceZoneResponse
from app.schemas.spatial_review import SpatialReviewFacets

ZoneSource = Literal["all", "user_reports", "news", "official", "other"]


class ZoneQueueItem(BaseModel):
    zone_id: int
    member_count: int
    location: str
    area_summary: str
    sources: list[str]
    severity_levels: list[str]
    depth_levels: list[str]
    evidence: str
    queued_at: datetime
    group_reason: str
    bounds: tuple[float, float, float, float] | None = None


class ZoneQueuePage(BaseModel):
    items: list[ZoneQueueItem]
    zones: list[FloodAvoidanceZoneResponse] = Field(default_factory=list)
    total: int
    item_total: int
    counts: dict[str, int]
    facets: SpatialReviewFacets
    page: int
    pages: int
    page_size: int
    read_only: Literal[True] = True


class ZoneMembersPage(BaseModel):
    zone_total: int | None = None
    zone_id: int
    zones: list[FloodAvoidanceZoneResponse]
    total: int
    page: int
    pages: int
    page_size: int
    group_reason: str
    read_only: Literal[True] = True
