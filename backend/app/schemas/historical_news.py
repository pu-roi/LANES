"""Validated additive projections; no persistence schema changes."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HistoricalNewsMetadata(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal['historical-import-v1'] = 'historical-import-v1'
    dataset_id: str = Field(pattern=r'^[a-z0-9][a-z0-9-]{0,99}$')
    observation_key: str = Field(pattern=r'^[a-f0-9]{64}$')
    disposition: Literal['historical_archive', 'active_demo']
    demonstration_session_id: str
    label: str
    article_id: int
    article_version_id: int
    source_article_version_id: int | None = None
    source_published_date: date | None = None
    run_id: int
    group_id: str
    source_url: str
    source_publisher: str
    source_excerpt: str
    canonical_road: str | None = None
    canonical_city: str | None = None
    canonical_barangay: str | None = None
    condition: str | None = None
    occurrence_date: date | None = None
    observed_at: datetime | None = None
    precision: Literal['unknown', 'date', 'instant']
    date_basis: str | None = None
    timezone_basis: str | None = None
    closure_basis: Literal['original_history', 'source_supported', 'assumed_two_hours', 'assumed_source_day_end', 'unknown', 'demo_administration']
    simulated_interval_minutes: int | None = None
    original_event_id: int | None = None
    original_zone_id: int | None = None
    geometry_sha256: str
    geometry_basis: Literal['estimated_road_corridor'] = 'estimated_road_corridor'
    assets_sha256: str
    input_fingerprint: str
    result_sha256: str
    pipeline_version: str
    imported_at: datetime

    @property
    def is_demo(self) -> bool:
        return self.disposition == 'active_demo'
