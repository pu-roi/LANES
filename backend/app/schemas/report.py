from datetime import datetime
import struct
from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, field_serializer, field_validator, model_validator
from geoalchemy2.elements import WKBElement

from app.schemas.common import (
    PointGeometry,
    LineStringGeometry,
    MultiLineStringGeometry,
    PolygonGeometry,
    MultiPolygonGeometry,
    GeometryCollectionGeometry,
    parse_ewkb_point,
    parse_ewkb_linestring,
    parse_ewkb_multilinestring,
    parse_ewkb_polygon,
    serialize_utc_datetime,
)


from app.models.report import ReportSource, ReportSeverity, ReportStatus, HazardPresence, ReportRejectionReason
from app.services.flood_depth import normalize_flood_depth, severity_for_flood_depth

class SurveyData(BaseModel):
    passable_vehicles: Optional[str] = None
    hidden_hazards: HazardPresence = HazardPresence.UNSURE

class SurveyDataResponse(SurveyData):
    id: int
    report_id: int
    model_config = ConfigDict(from_attributes=True)


class FloodReportBase(BaseModel):
    raw_text: str
    source: ReportSource
    severity: ReportSeverity = ReportSeverity.MEDIUM
    depth: Optional[str] = None
    human_readable_location: Optional[str] = None
    barangay: Optional[str] = None
    city: Optional[str] = None
    is_public: bool = False
    is_bidirectional: bool = False

    @field_validator("depth", mode="before")
    @classmethod
    def normalize_depth(cls, value: Optional[str]) -> Optional[str]:
        return normalize_flood_depth(value)

    @model_validator(mode="after")
    def validate_depth_matches_severity(self) -> "FloodReportBase":
        if self.depth is not None and severity_for_flood_depth(self.depth) != self.severity:
            raise ValueError("Severity must match the selected flood depth.")
        return self


class FloodReportCreate(FloodReportBase):
    geometry: Optional[Union[PointGeometry, LineStringGeometry, MultiLineStringGeometry, PolygonGeometry, GeometryCollectionGeometry]] = None
    media_urls: list[str] = []
    user_id: Optional[int] = None
    survey_data: Optional[SurveyData] = None

    @field_validator("media_urls", mode="before")
    @classmethod
    def validate_media_urls(cls, v: Any) -> list[str]:
        return v if v is not None else []


class FloodReportResponse(FloodReportBase):
    id: int
    status: ReportStatus
    geometry: Optional[Union[PointGeometry, LineStringGeometry, MultiLineStringGeometry, PolygonGeometry, GeometryCollectionGeometry]] = None
    media_urls: list[str] = []
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    zone_id: Optional[int] = None
    event_id: Optional[int] = None
    survey: Optional[SurveyDataResponse] = None
    reporter_name: Optional[str] = "System"
    reporter_username: Optional[str] = None
    reporter_role: Optional[str] = None
    reporter_trust_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at", "approved_at")
    def serialize_report_datetimes(self, dt: Optional[datetime], _info):
        return serialize_utc_datetime(dt)

    @field_validator("media_urls", mode="before")
    @classmethod
    def validate_media_urls(cls, v: Any) -> list[str]:
        return v if v is not None else []

    @field_validator("geometry", mode="before")
    @classmethod
    def convert_geometry(cls, v: Any) -> Optional[Union[PointGeometry, LineStringGeometry, MultiLineStringGeometry]]:
        if isinstance(v, WKBElement):
            try:
                # Use raw bytes data from descriptor or data field
                data = bytes.fromhex(v.desc) if isinstance(v.desc, str) else bytes(v.data)
                byte_order = '<' if data[0] == 1 else '>'
                geom_type = struct.unpack(f"{byte_order}I", data[1:5])[0]
                pure_geom_type = geom_type & 0x0fffffff
                
                if pure_geom_type == 1:  # Point
                    coords = parse_ewkb_point(data)
                    return PointGeometry(type="Point", coordinates=coords)
                elif pure_geom_type == 2:  # LineString
                    coords = parse_ewkb_linestring(data)
                    return LineStringGeometry(type="LineString", coordinates=coords)
                elif pure_geom_type == 3:  # Polygon
                    coords = parse_ewkb_polygon(data)
                    return PolygonGeometry(type="Polygon", coordinates=coords)
                elif pure_geom_type == 5:  # MultiLineString
                    coords = parse_ewkb_multilinestring(data)
                    return MultiLineStringGeometry(type="MultiLineString", coordinates=coords)
            except Exception as e:
                # Log parser error and return None
                print(f"Warning: Failed parsing EWKB in validator: {e}")
                return None
            return None
        return v


class FloodAvoidanceZoneBase(BaseModel):
    is_active: bool = True
    expires_at: Optional[datetime] = None


class FloodAvoidanceZoneCreate(FloodAvoidanceZoneBase):
    report_id: Optional[int] = None
    geometry: Union[PolygonGeometry, MultiPolygonGeometry]
    source_geometry: Optional[Union[LineStringGeometry, MultiLineStringGeometry]] = None
    curated_by_admin_id: Optional[int] = None

class FloodAvoidanceZoneUpdate(BaseModel):
    name: Optional[str] = None
    severity_override: Optional[ReportSeverity] = None
    depth_override: Optional[str] = None
    passable_vehicles_override: Optional[str] = None
    hidden_hazards_override: Optional[str] = None
    admin_notes: Optional[str] = None
    is_active: Optional[bool] = None
    # A zone persists its operational avoidance area as a Polygon. Road
    # centrelines are accepted here and buffered by the secured admin route.
    geometry: Optional[Union[LineStringGeometry, MultiLineStringGeometry, PolygonGeometry]] = None

    @field_validator("depth_override", mode="before")
    @classmethod
    def normalize_depth_override(cls, value: Optional[str]) -> Optional[str]:
        return normalize_flood_depth(value)

class FloodAvoidanceZoneCreateOfficial(BaseModel):
    name: Optional[str] = None
    # Create Zone accepts road-following lines as well as hand-drawn areas.
    # The official-zone endpoint buffers line geometries into persisted polygons.
    geometry: Union[LineStringGeometry, MultiLineStringGeometry, PolygonGeometry, MultiPolygonGeometry]
    severity_override: ReportSeverity
    depth_override: str
    passable_vehicles_override: Optional[str] = None
    hidden_hazards_override: Optional[str] = None
    admin_notes: Optional[str] = None
    is_active: bool = True

    @field_validator("depth_override", mode="before")
    @classmethod
    def normalize_depth_override(cls, value: str) -> str:
        normalized = normalize_flood_depth(value)
        if normalized is None:
            raise ValueError("Depth is required for an official flood zone.")
        return normalized

    @model_validator(mode="after")
    def validate_depth_matches_severity(self) -> "FloodAvoidanceZoneCreateOfficial":
        if severity_for_flood_depth(self.depth_override) != self.severity_override:
            raise ValueError("Severity must match the selected flood depth.")
        return self


class ZoneContributorResponse(BaseModel):
    report_id: int
    reporter_name: str
    reporter_username: Optional[str] = None
    reporter_role: Optional[str] = None
    reporter_trust_score: float = 100.0
    raw_text: str
    severity: str
    depth: Optional[str] = None
    created_at: datetime
    is_primary: bool = False
    geometry: Optional[Union[PointGeometry, LineStringGeometry, MultiLineStringGeometry, PolygonGeometry]] = None
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def serialize_contributor_datetimes(self, dt: datetime, _info):
        return serialize_utc_datetime(dt)

    @field_validator("geometry", mode="before")
    @classmethod
    def convert_geometry(cls, v: Any) -> Optional[Union[PointGeometry, LineStringGeometry, MultiLineStringGeometry]]:
        if isinstance(v, WKBElement):
            try:
                data = bytes.fromhex(v.desc) if isinstance(v.desc, str) else bytes(v.data)
                byte_order = '<' if data[0] == 1 else '>'
                geom_type = struct.unpack(f"{byte_order}I", data[1:5])[0]
                pure_geom_type = geom_type & 0x0fffffff
                
                if pure_geom_type == 1:  # Point
                    coords = parse_ewkb_point(data)
                    return PointGeometry(type="Point", coordinates=coords)
                elif pure_geom_type == 2:  # LineString
                    coords = parse_ewkb_linestring(data)
                    return LineStringGeometry(type="LineString", coordinates=coords)
                elif pure_geom_type == 5:  # MultiLineString
                    coords = parse_ewkb_multilinestring(data)
                    return MultiLineStringGeometry(type="MultiLineString", coordinates=coords)
            except Exception as e:
                print(f"Warning: Failed parsing contributor geometry EWKB: {e}")
                return None
        return v


class FloodAvoidanceZoneResponse(FloodAvoidanceZoneBase):
    id: int
    report_id: Optional[int] = None
    event_id: Optional[int] = None
    curated_by_admin_id: Optional[int] = None
    name: Optional[str] = None
    severity_override: Optional[ReportSeverity] = None
    depth_override: Optional[str] = None
    admin_notes: Optional[str] = None
    geometry: PolygonGeometry
    severity: str
    depth: Optional[str] = None
    report_geometry: Optional[Union[PointGeometry, LineStringGeometry, MultiLineStringGeometry, PolygonGeometry]] = None
    created_at: datetime
    updated_at: datetime
    
    report_text: Optional[str] = None
    report_source: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_role: Optional[str] = None
    reporter_trust_score: Optional[float] = None
    reporter_reports_submitted: Optional[int] = None
    reporter_reports_verified: Optional[int] = None
    
    passable_vehicles_override: Optional[str] = None
    hidden_hazards_override: Optional[str] = None
    merge_rationale: Optional[str] = None
    passable_vehicles: Optional[str] = None
    hidden_hazards: Optional[str] = None
    media_urls: Optional[list[str]] = None
    # Original public-report evidence is separate from media an administrator
    # later attaches directly to the operational zone.
    report_media_urls: Optional[list[str]] = None
    contributors: list[ZoneContributorResponse] = []

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at", "expires_at")
    def serialize_zone_datetimes(self, dt: Optional[datetime], _info):
        return serialize_utc_datetime(dt)

    @field_validator("geometry", mode="before")
    @classmethod
    def convert_geometry(cls, v: Any) -> Optional[PolygonGeometry]:
        if isinstance(v, WKBElement):
            try:
                data = bytes.fromhex(v.desc) if isinstance(v.desc, str) else bytes(v.data)
                coords = parse_ewkb_polygon(data)
                return PolygonGeometry(type="Polygon", coordinates=coords)
            except Exception as e:
                print(f"Warning: Failed parsing Polygon EWKB: {e}")
                return None
        return v

    @field_validator("report_geometry", mode="before")
    @classmethod
    def convert_report_geometry(cls, v: Any) -> Optional[Union[PointGeometry, LineStringGeometry, MultiLineStringGeometry, PolygonGeometry]]:
        if isinstance(v, WKBElement):
            try:
                data = bytes.fromhex(v.desc) if isinstance(v.desc, str) else bytes(v.data)
                byte_order = '<' if data[0] == 1 else '>'
                geom_type = struct.unpack(f"{byte_order}I", data[1:5])[0]
                pure_geom_type = geom_type & 0x0fffffff
                
                if pure_geom_type == 1:  # Point
                    coords = parse_ewkb_point(data)
                    return PointGeometry(type="Point", coordinates=coords)
                elif pure_geom_type == 2:  # LineString
                    coords = parse_ewkb_linestring(data)
                    return LineStringGeometry(type="LineString", coordinates=coords)
                elif pure_geom_type == 3:  # Polygon
                    coords = parse_ewkb_polygon(data)
                    return PolygonGeometry(type="Polygon", coordinates=coords)
                elif pure_geom_type == 5:  # MultiLineString
                    coords = parse_ewkb_multilinestring(data)
                    return MultiLineStringGeometry(type="MultiLineString", coordinates=coords)
            except Exception as e:
                print(f"Warning: Failed parsing report_geometry EWKB: {e}")
                return None
        return v


class FloodReportsPaginatedResponse(BaseModel):
    reports: list[FloodReportResponse]
    total: int


class AdminDashboardStats(BaseModel):
    total_pending_reports: int
    total_active_zones: int
    total_approved_today: int
    total_rejected_today: int
    total_users: int
    database_status: str


class ApproveReportRequest(BaseModel):
    action: str = "CREATE_NEW"  # "CREATE_NEW" or "MERGE"
    target_zone_id: Optional[int] = None
    custom_geometry: Optional[PolygonGeometry] = None
    buffer_radius: Optional[float] = None
    severity: Optional[ReportSeverity] = None
    depth: Optional[str] = None
    admin_notes: Optional[str] = None

    @field_validator("depth", mode="before")
    @classmethod
    def normalize_depth(cls, value: Optional[str]) -> Optional[str]:
        return normalize_flood_depth(value)

    @model_validator(mode="after")
    def validate_depth_matches_severity(self) -> "ApproveReportRequest":
        if self.depth is not None and self.severity is not None and severity_for_flood_depth(self.depth) != self.severity:
            raise ValueError("Severity must match the selected flood depth.")
        return self


class RejectFloodReportRequest(BaseModel):
    reason: ReportRejectionReason
    internal_note: Optional[str] = None

    @model_validator(mode="after")
    def require_note_for_other(self) -> "RejectFloodReportRequest":
        if self.reason == ReportRejectionReason.OTHER and not (self.internal_note and self.internal_note.strip()):
            raise ValueError("An internal note is required when rejection reason is 'other'.")
        return self


class NearbyZoneResponse(BaseModel):
    id: int
    severity: str
    depth: Optional[str] = None
    distance_meters: float
    created_at: datetime
    geometry: PolygonGeometry
    report_count: int = 1

    @field_serializer("created_at")
    def serialize_nearby_datetimes(self, dt: datetime, _info):
        return serialize_utc_datetime(dt)


class FloodAvoidanceZonesPaginatedResponse(BaseModel):
    zones: list[FloodAvoidanceZoneResponse]
    total: int


class AvoidanceZoneDeactivateBulkRequest(BaseModel):
    zone_ids: list[int]


class AvoidanceZoneUpdateRequest(BaseModel):
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class MergePendingReportsRequest(BaseModel):
    report_ids: list[int]

    @field_validator("report_ids")
    @classmethod
    def require_unique_report_ids(cls, value: list[int]) -> list[int]:
        if not value:
            raise ValueError("Select at least one pending report to merge.")
        if len(value) != len(set(value)):
            raise ValueError("A report can be selected only once per batch merge.")
        return value


class MergePendingReportsResponse(BaseModel):
    message: str
    merged_count: int
    zone_id: int


# =========================================================================
# Schemas for Intelligent Multi-Factor Merging (Decision #16 & Graph Grouping)
# =========================================================================

class MergeConflict(BaseModel):
    field: str  # "severity", "depth", "direction", "passable_vehicles"
    message: str
    suggested_value: Any


class MergeCandidateItem(BaseModel):
    report_id: int
    road_name: Optional[str] = None
    barangay: Optional[str] = None
    city: Optional[str] = None
    severity: str
    depth: Optional[str] = None
    passable_vehicles: Optional[str] = None
    hidden_hazards: Optional[str] = None
    reporter_username: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_trust_score: float = 100.0
    media_urls: Optional[list[str]] = None
    raw_text: Optional[str] = None
    reported_at: datetime
    geometry: Optional[Union[PointGeometry, LineStringGeometry, MultiLineStringGeometry, PolygonGeometry]] = None
    
    # Matching Metrics
    match_score: int  # 0 - 100
    match_reasons: list[str] = []
    is_crowd_consensus: bool = False
    osm_way_id: Optional[int] = None
    road_class: Optional[str] = None
    corridor_overlap_ratio: Optional[float] = None
    conflicts: list[MergeConflict] = []

    @field_serializer("reported_at")
    def serialize_candidate_datetimes(self, dt: datetime, _info):
        return serialize_utc_datetime(dt)


class MergeCandidatesListResponse(BaseModel):
    primary_report: FloodReportResponse
    candidates: list[MergeCandidateItem]
    total_candidates: int
    detected_conflicts: list[MergeConflict] = []
    suggested_merged_geometry: Optional[Union[LineStringGeometry, MultiLineStringGeometry, PolygonGeometry]] = None
    is_bidirectional_detected: bool = False


class MergedZoneFinalData(BaseModel):
    name: Optional[str] = None
    severity: str
    depth: str
    passable_vehicles: Optional[str] = None
    hidden_hazards: Optional[str] = None
    is_bidirectional: bool = False
    geometry: Union[PointGeometry, LineStringGeometry, MultiLineStringGeometry, PolygonGeometry]
    admin_notes: Optional[str] = None

    @field_validator("depth", mode="before")
    @classmethod
    def normalize_depth(cls, value: str) -> str:
        normalized = normalize_flood_depth(value)
        if normalized is None:
            raise ValueError("Depth is required for a verified flood zone.")
        return normalized

    @model_validator(mode="after")
    def validate_depth_matches_severity(self) -> "MergedZoneFinalData":
        expected = severity_for_flood_depth(self.depth)
        if self.severity != expected.value:
            raise ValueError("Severity must match the selected flood depth.")
        return self
    merge_rationale: Optional[str] = None
    buffer_radius: Optional[float] = 25.0


class MergeReportsRequest(BaseModel):
    primary_report_id: int
    merged_report_ids: list[int]
    target_zone_id: Optional[int] = None  # None = create new zone; int = merge into existing zone
    final_data: MergedZoneFinalData


class MergeReportsResponse(BaseModel):
    message: str
    zone_id: int
    zone_name: Optional[str] = None
    merged_count: int
    awarded_user_ids: list[int] = []
    zone: FloodAvoidanceZoneResponse
