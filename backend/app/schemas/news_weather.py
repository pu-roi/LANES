"""Persisted scheduling signals, never flood observations or publication evidence."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class WeatherPoint(BaseModel):
    locality: str
    latitude: float
    longitude: float
    role: Literal["metro", "upstream"] = "metro"
    relevance: str = "Metro Manila representative sample"


class WeatherBulletin(BaseModel):
    identity: str
    issued_at: datetime
    valid_until: datetime
    relevant: bool
    locations: list[str] = Field(default_factory=list)


class WeatherProvider(BaseModel):
    name: str
    source_url: str
    checked_at: datetime
    status: Literal["quiet", "risk", "uncertain", "unavailable"]
    risk_locations: list[str] = Field(default_factory=list)
    bulletins: list[WeatherBulletin] = Field(default_factory=list)
    error_code: str | None = None


class AdaptiveDecision(BaseModel):
    interval_minutes: Literal[15, 30, 60]
    reason: str
    last_positive_at: datetime | None = None


class NewsWeatherController(BaseModel):
    catalog_version: str = "ncr-upstream-v1"
    last_tick_at: datetime | None = None
    providers: list[WeatherProvider] = Field(default_factory=list)
    last_positive_at: datetime | None = None
    dispatch_token: str | None = None
    active_flood_until: datetime | None = None
    dispatch_reserved_at: datetime | None = None
    dispatch_state: str = "idle"
    dispatch_operation: str | None = None
    dispatch_error: str | None = None
    last_dispatch_at: datetime | None = None
    last_tick_duration_ms: int = 0
    checks: int = 0
    provider_failures: int = 0
    worker_starts: int = 0


class NewsWeatherStatus(BaseModel):
    mode: str = "adaptive"
    catalog_version: str
    coverage_label: str = "Sampled Metro Manila and upstream coverage; not street-level rain detection"
    points: list[WeatherPoint]
    providers: list[WeatherProvider]
    effective_interval_minutes: int
    reason: str
    last_positive_at: datetime | None = None
    controller_heartbeat_at: datetime | None = None
    controller_stale: bool = True
    dispatch_state: str
    dispatch_error: str | None = None
    last_dispatch_at: datetime | None = None
    last_tick_duration_ms: int
    checks: int
    provider_failures: int
    worker_starts: int
