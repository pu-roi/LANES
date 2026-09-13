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


class CommunityPostUpdate(CommunityPostBase):
    """The complete editable Community Post state supplied by its author."""
    pass

class CommunityPostReportCreate(BaseModel):
    reason: str
    details: Optional[str] = None


class CommunityPostEditHistoryResponse(BaseModel):
    id: int
    post_id: int
    editor_user_id: int
    version: int
    previous_content: str
    previous_media_urls: Optional[List[str]] = None
    previous_location_tag: Optional[str] = None
    previous_location_lat: Optional[float] = None
    previous_location_lng: Optional[float] = None
    updated_content: str
    updated_media_urls: Optional[List[str]] = None
    updated_location_tag: Optional[str] = None
    updated_location_lat: Optional[float] = None
    updated_location_lng: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at')
    def serialize_history_datetime(self, dt: datetime, _info):
        return dt.isoformat() + "Z" if dt.tzinfo is None else dt.isoformat()


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
