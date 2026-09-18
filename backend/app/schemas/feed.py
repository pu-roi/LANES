from datetime import datetime
from typing import Optional, Union, Any
from pydantic import BaseModel, ConfigDict, field_validator, field_serializer
import struct
from geoalchemy2.elements import WKBElement

from app.schemas.common import PointGeometry, LineStringGeometry, parse_ewkb_point, parse_ewkb_linestring
from app.schemas.report import FloodReportBase

from app.models.report import ReportStatus

class FeedPostResponse(FloodReportBase):
    id: int
    status: ReportStatus
    geometry: Optional[Union[PointGeometry, LineStringGeometry]] = None
    image_url: Optional[str] = None
    created_at: datetime
    
    @field_serializer('created_at')
    def serialize_datetime(self, dt: datetime, _info):
        if dt.tzinfo is None:
            return dt.isoformat() + "Z"
        return dt.isoformat()
    
    # New feed-specific fields
    upvotes: int = 0
    downvotes: int = 0
    distance_meters: Optional[float] = None
    user_interaction: Optional[str] = None  # "upvote", "downvote", or None
    author_name: Optional[str] = None
    comment_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    @field_validator("geometry", mode="before")
    @classmethod
    def convert_geometry(cls, v: Any) -> Optional[Union[PointGeometry, LineStringGeometry]]:
        if isinstance(v, WKBElement):
            try:
                data = bytes.fromhex(v.desc) if isinstance(v.desc, str) else bytes(v.data)
                byte_order = '<' if data[0] == 1 else '>'
                geom_type = struct.unpack(f"{byte_order}I", data[1:5])[0]
                pure_geom_type = geom_type & 0x0fffffff
                
                if pure_geom_type == 1:
                    coords = parse_ewkb_point(data)
                    return PointGeometry(type="Point", coordinates=coords)
                elif pure_geom_type == 2:
                    coords = parse_ewkb_linestring(data)
                    return LineStringGeometry(type="LineString", coordinates=coords)
            except Exception as e:
                return None
        return v


class FeedPaginatedResponse(BaseModel):
    posts: list[FeedPostResponse]
    total: int
    has_more: bool


class TopReporter(BaseModel):
    """Schema representing a single entry in the Top Reporters leaderboard."""
    rank: int
    user_id: int
    username: str
    avatar_url: Optional[str] = None
    report_count: int

    model_config = ConfigDict(from_attributes=True)


class TopReportersResponse(BaseModel):
    """Schema for the paginated top reporters leaderboard response."""
    reporters: list[TopReporter]


class VoteResponse(BaseModel):
    """Schema for the authoritative response after voting on a post."""
    post_id: int
    upvotes: int
    downvotes: int
    net_score: int
    user_interaction: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

