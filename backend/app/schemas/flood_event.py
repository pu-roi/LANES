from app.schemas.historical_news import HistoricalNewsMetadata
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator, model_validator
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from shapely.errors import ShapelyError
from app.schemas.report import FloodAvoidanceZoneResponse
from app.schemas.common import PolygonGeometry, MultiPolygonGeometry

from app.schemas.common import serialize_utc_datetime
from app.services.flood_depth import get_flood_depth_measurement, format_flood_depth
from app.models.report import (
    FloodEventLocationType,
    FloodEventStatus,
    ReportModerationOutcomeType,
    ReportRejectionReason,
    ReportSeverity,
)


class HistoricalHeatmapPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]


class HistoricalHeatmapProperties(BaseModel):
    event_id: int
    zone_id: int
    weight: int


class HistoricalHeatmapFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: HistoricalHeatmapPoint
    properties: HistoricalHeatmapProperties


class HistoricalFloodZoneResponse(FloodAvoidanceZoneResponse):
    """History remains inspectable when a footprint is absent or multipart."""
    geometry: Optional[PolygonGeometry | MultiPolygonGeometry] = None

    @field_validator("geometry", mode="before")
    @classmethod
    def convert_geometry(cls, value: Any) -> Any:
        if isinstance(value, WKBElement):
            try:
                geometry = to_shape(value)
                return mapping(geometry) if not geometry.is_empty and geometry.is_valid and geometry.geom_type in {"Polygon", "MultiPolygon"} else None
            except (ValueError, TypeError, ShapelyError):
                return None
        return value


class FloodEventHistoryPage(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    pages: int
    page_size: int


class FloodEventLocationResponse(BaseModel):
    id: int
    location_type: FloodEventLocationType
    display_name: str
    normalized_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def serialize_location_datetimes(self, dt: datetime, _info):
        return serialize_utc_datetime(dt)


class FloodEventTimelineEntryResponse(BaseModel):
    id: int
    entry_type: str
    occurred_at: datetime
    summary: str
    snapshot_json: Optional[dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("occurred_at")
    def serialize_timeline_datetimes(self, dt: datetime, _info):
        return serialize_utc_datetime(dt)


class FloodEventResponse(BaseModel):
    origin: Literal['news', 'user', 'mixed', 'unknown'] = 'unknown'
    news_article_count: int = 0
    news_evidence_count: int = 0
    occurrence_date: str | None = None
    observed_at: str | None = None
    observation_precision: Literal['unknown', 'date', 'instant'] = 'unknown'
    closure_basis: str | None = None
    historical: HistoricalNewsMetadata | None = None
    duration_basis: str | None = None
    id: int
    status: FloodEventStatus
    first_reported_at: Optional[datetime] = None
    verified_at: datetime
    ended_at: Optional[datetime] = None
    peak_severity: ReportSeverity
    peak_depth: Optional[str] = None
    peak_depth_meters: Optional[float] = None
    peak_depth_inches: Optional[float] = None
    peak_depth_formatted: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def populate_peak_depth_measurements(self) -> "FloodEventResponse":
        if self.peak_depth and (self.peak_depth_meters is None or self.peak_depth_formatted is None):
            measurement = get_flood_depth_measurement(self.peak_depth)
            if measurement:
                if self.peak_depth_meters is None:
                    self.peak_depth_meters = measurement.meters
                if self.peak_depth_inches is None:
                    self.peak_depth_inches = measurement.inches
                if self.peak_depth_formatted is None:
                    self.peak_depth_formatted = measurement.formatted
        return self

    @field_serializer("first_reported_at", "verified_at", "ended_at", "created_at", "updated_at")
    def serialize_event_datetimes(self, dt: Optional[datetime], _info):
        return serialize_utc_datetime(dt)


class FloodReportModerationOutcomeResponse(BaseModel):
    id: int
    report_id: int
    outcome: ReportModerationOutcomeType
    rejection_reason: Optional[ReportRejectionReason] = None
    internal_note: Optional[str] = None
    event_id: Optional[int] = None
    zone_id: Optional[int] = None
    acted_by_user_id: Optional[int] = None
    acted_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("acted_at")
    def serialize_outcome_datetimes(self, dt: datetime, _info):
        return serialize_utc_datetime(dt)
