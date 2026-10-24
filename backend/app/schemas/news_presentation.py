"""Plain-language presentation of stored evidence, without activation decisions."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class NewsVerificationIssue(BaseModel):
    field: Literal['location', 'road', 'water_level', 'flood_time', 'condition', 'source']
    label: str
    state: Literal['missing', 'uncertain', 'conflicting']
    code: str
    reason: str


class NewsFloodSummary(BaseModel):
    location: str
    area: str | None
    location_qualifier: str | None
    water_level: str
    passability: str = "Not stated in article"
    condition: str
    flood_time: datetime | None
    flood_time_label: Literal["Flood observed in article", "Flood reported in article", "Flood time in article",
                              "Floodwater subsided by", "Floodwater subsided in article"]
    map_status: str
    reading_status: Literal["reported_location", "needs_checking"]
    reading_reason: str | None
    verification_status: Literal['not_assessed', 'needs_verification', 'no_issues_recorded'] = 'not_assessed'
    verification_issues: list[NewsVerificationIssue] = Field(default_factory=list)
    placement_is_estimate: bool = False
