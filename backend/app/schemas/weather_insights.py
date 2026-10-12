"""Bounded public forecast explanations; no provider data in the public contract."""
from pydantic import BaseModel, ConfigDict, Field


class ForecastSlot(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    dt: int
    time: str = Field(max_length=80)
    temp: float = Field(ge=-100, le=100)
    pop: int = Field(ge=0, le=100)
    condition: str = Field(max_length=120)
    icon: str = Field(max_length=80)
    precip_mm: float | None = Field(default=0, ge=0, le=1000)
    showers_mm: float | None = Field(default=0, ge=0, le=1000)
    wind_kmh: float | None = Field(default=0, ge=0, le=1000)
    wind_dir: int | None = Field(default=0, ge=0, le=360)
    humidity_pct: int | None = Field(default=0, ge=0, le=100)


class WeatherInsightsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    forecast: list[ForecastSlot] = Field(min_length=1, max_length=72)
    location: str = Field(min_length=1, max_length=120)


class WeatherExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, str_strip_whitespace=True)
    storm_risk: str = Field(min_length=1, max_length=2000)
    environment: str = Field(min_length=1, max_length=2000)


class WeatherInsightsResponse(BaseModel):
    insights: WeatherExplanation
    model: str
