from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_serializer, model_validator

from app.schemas.common import serialize_utc_datetime
from app.services.flood_depth import get_flood_depth_measurement, format_flood_depth
from app.models.report import (
    FloodEventLocationType,
    FloodEventStatus,
    ReportModerationOutcomeType,
    ReportRejectionReason,
    ReportSeverity,
)


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
