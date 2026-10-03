"""Plain-language presentation of stored evidence, without activation decisions."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class NewsFloodSummary(BaseModel):
    location: str
    area: str | None
    location_qualifier: str | None
    water_level: str
    passability: str = "Not stated in article"
    condition: str
    flood_time: datetime | None
    flood_time_label: Literal["Flood observed in article", "Flood reported in article", "Flood time in article"]
    map_status: str
    reading_status: Literal["reported_location", "needs_checking"]
    reading_reason: str | None
