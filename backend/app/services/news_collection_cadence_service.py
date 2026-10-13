"""Shared quarter-hour cadence; original collection timestamps stay intact."""
from datetime import datetime, timedelta, timezone


def scheduler_slot(at: datetime) -> datetime:
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("Scheduling clocks require a timezone")
    utc = at.astimezone(timezone.utc)
    return utc.replace(minute=(utc.minute // 15) * 15, second=0, microsecond=0)


def next_collection_due(previous: datetime, interval_minutes: int) -> datetime:
    if interval_minutes not in (15, 30, 60):
        raise ValueError("Unsupported adaptive collection interval")
    return scheduler_slot(previous) + timedelta(minutes=interval_minutes)


def collection_is_due(previous: datetime | None, now: datetime, interval_minutes: int) -> bool:
    scheduler_slot(now)  # Validate before accepting a first collection.
    return previous is None or (previous <= now and now >= next_collection_due(previous, interval_minutes))
