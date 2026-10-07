"""Private witness observations about an existing operational zone."""
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID
from math import isfinite

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.services.flood_depth import normalize_flood_depth

Condition = Literal["still_flooded", "no_floodwater", "other_change"]
Vehicle = Literal["walk", "bicycle", "motorcycle", "light", "suv", "heavy"]


class ZoneObservationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: UUID
    condition: Condition
    observed_at: datetime | None = None
    observed_location: str | None = Field(default=None, min_length=3, max_length=300)
    road_start: list[float] | None = Field(default=None, min_length=2, max_length=2)
    road_end: list[float] | None = Field(default=None, min_length=2, max_length=2)
    start_label: str | None = Field(default=None, max_length=300)
    end_label: str | None = Field(default=None, max_length=300)
    is_bidirectional: bool = False
    description: str = Field(min_length=3, max_length=3000)
    depth: str | None = None
    passable_vehicles: list[Vehicle] | None = Field(default=None, max_length=6)
    hidden_hazards: Literal["yes", "no", "unsure"] = "unsure"
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)

    @field_validator("depth", mode="before")
    @classmethod
    def valid_depth(cls, value: str | None) -> str | None:
        return normalize_flood_depth(value)

    @field_validator("observed_at")
    @classmethod
    def valid_clock(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Observation time must include a timezone.")
        if value > datetime.now(timezone.utc):
            raise ValueError("Observation time cannot be in the future.")
        return value.astimezone(timezone.utc)

    @field_validator("road_start", "road_end")
    @classmethod
    def valid_road_point(cls, value: list[float] | None) -> list[float] | None:
        if value is not None and (not all(isfinite(number) for number in value)
                or not -180 <= value[0] <= 180 or not -90 <= value[1] <= 90):
            raise ValueError("Road coordinates must be finite longitude/latitude pairs.")
        return value

    @model_validator(mode="after")
    def coherent_observation(self) -> "ZoneObservationCreate":
        if (self.road_start is None) != (self.road_end is None):
            raise ValueError("Provide both road start and end.")
        if self.road_start is not None and self.road_start == self.road_end:
            raise ValueError("Road start and end must differ.")
        if self.road_start is None and self.observed_location is None:
            raise ValueError("Provide road endpoints or an observed location.")
        if self.condition == "no_floodwater" and self.depth is not None:
            raise ValueError("A no-floodwater observation cannot include a wet depth.")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Provide both latitude and longitude.")
        return self


class ZoneObservationReview(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    decision: Literal["reviewed", "dismissed"]
    note: str = Field(min_length=3, max_length=2000)
