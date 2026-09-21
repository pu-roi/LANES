from datetime import date
from uuid import UUID

from pydantic import BaseModel


class VisitorActivityRequest(BaseModel):
    """Opaque, browser-generated identifier used only to deduplicate visits."""
    visitor_id: UUID


class PublicStatsResponse(BaseModel):
    daily_verified_reports: int
    total_visitors: int


class VisitorActivityResponse(PublicStatsResponse):
    recorded: bool


class VisitorTrendDay(BaseModel):
    date: date
    unique_visitors: int


class AdminVisitorAnalyticsResponse(BaseModel):
    total_unique_visitors: int
    visitors_today: int
    daily_unique_visitors: list[VisitorTrendDay]
