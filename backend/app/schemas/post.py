from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.report import FloodReportResponse
from app.models.interaction import InteractionType


class CommunityPostBase(BaseModel):
    content: str
    media_urls: Optional[List[str]] = None
    flood_report_id: Optional[int] = None
    location_tag: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None


class CommunityPostCreate(CommunityPostBase):
    pass


class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    user_id: int
    post_id: int
    created_at: datetime
    author_name: str
    author_avatar: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at')
    def serialize_datetime(self, dt: datetime, _info):
        if dt.tzinfo is None:
            return dt.isoformat() + "Z"
        return dt.isoformat()


class CommunityPostResponse(CommunityPostBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    # Extended Feed attributes
    author_name: str
    author_avatar: Optional[str] = None
    upvotes: int = 0
    downvotes: int = 0
    comment_count: int = 0
    user_interaction: Optional[InteractionType] = None
    
    # The attached flood report if any
    report: Optional[FloodReportResponse] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime, _info):
        if dt.tzinfo is None:
            return dt.isoformat() + "Z"
        return dt.isoformat()


class CommunityPostPaginatedResponse(BaseModel):
    posts: List[CommunityPostResponse]
    total: int
    has_more: bool
