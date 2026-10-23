"""Shared SQL and Python policy for saved historical/demo lineage."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Date, case, cast, func, select
from sqlalchemy.orm import Session

from app.models.report import FloodEvent, FloodEventTimelineEntry as Timeline
from app.schemas.historical_news import HistoricalNewsMetadata

DATASET = 'capstone-september-2026-v1'
DEMO_LABEL = 'Historical demonstration — September 2026'
ENTRY = 'historical_import'


def import_rows() -> Any:
    return select(Timeline).where(Timeline.entry_type == ENTRY,
        Timeline.snapshot_json['schema_version'].as_string() == 'historical-import-v1')


def metadata_field(name: str, event_column: Any = None) -> Any:
    column = FloodEvent.id if event_column is None else event_column
    return select(Timeline.snapshot_json[name].as_string()).where(
        Timeline.event_id == column, Timeline.entry_type == ENTRY,
        Timeline.snapshot_json['schema_version'].as_string() == 'historical-import-v1'
    ).order_by(Timeline.id.desc()).limit(1).correlate_except(Timeline).scalar_subquery()


def metadata_snapshot(event_column: Any = None) -> Any:
    column = FloodEvent.id if event_column is None else event_column
    return select(Timeline.snapshot_json).where(
        Timeline.event_id == column, Timeline.entry_type == ENTRY,
        Timeline.snapshot_json['schema_version'].as_string() == 'historical-import-v1'
    ).order_by(Timeline.id.desc()).limit(1).correlate_except(Timeline).scalar_subquery()


def demo_event(event_column: Any = None) -> Any:
    column = FloodEvent.id if event_column is None else event_column
    return select(Timeline.id).where(Timeline.event_id == column, Timeline.entry_type == ENTRY,
        Timeline.snapshot_json['schema_version'].as_string() == 'historical-import-v1',
        Timeline.snapshot_json['disposition'].as_string() == 'active_demo').correlate_except(Timeline).exists()


def occurrence_day() -> Any:
    from app.services.news_history_evidence import legacy_news_instant, news_timing_event
    imported = metadata_field('dataset_id').is_not(None) & news_timing_event()
    return case((imported, cast(metadata_field('occurrence_date'), Date)),
                (news_timing_event(), cast(func.timezone('Asia/Manila', legacy_news_instant()), Date)),
                else_=func.date(FloodEvent.verified_at))


def observed_duration_eligible() -> Any:
    # Imported intervals are source/assumption based, not verification-to-end observations.
    from app.services.news_history_evidence import news_timing_event
    return ~news_timing_event()


def event_metadata(db: Session, ids: list[int]) -> dict[int, HistoricalNewsMetadata]:
    if not ids:
        return {}
    rows = db.scalars(import_rows().where(Timeline.event_id.in_(ids)).order_by(Timeline.id))
    result = {}
    for row in rows:
        # Invalid stored lineage is an error, never a silent downgrade to a real flood.
        result[row.event_id] = HistoricalNewsMetadata.model_validate(row.snapshot_json)
    return result


def public_metadata(value: HistoricalNewsMetadata | None) -> dict | None:
    return value.model_dump(mode='json') if value else None


def history_values(value: dict, metadata: HistoricalNewsMetadata | None) -> dict:
    if metadata is None:
        return value
    return {**value, 'historical': public_metadata(metadata), 'duration_seconds': None,
            'duration_minutes': None, 'duration_basis': metadata.closure_basis}


def record_demo_deactivation(db: Session, event_id: int, zone_id: int, now: datetime) -> None:
    metadata = event_metadata(db, [event_id]).get(event_id)
    if metadata and metadata.is_demo:
        db.add(Timeline(event_id=event_id, entry_type='historical_demo_deactivated', occurred_at=now,
            summary='Historical demonstration deactivated; source flood clearance is not inferred.',
            snapshot_json={'schema_version': 'historical-demo-action-v1', 'zone_id': zone_id,
                'demonstration_session_id': metadata.demonstration_session_id}))
