"""Bounded history reads and conditional, idempotent attempt finalization."""

from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.news_telemetry import NewsDiscoveryRun, NewsDiscoveryFeedRun, NewsFallbackLookup, NewsFallbackLookupLead

AttemptKind = Literal["discovery", "fallback"]


def interrupt_abandoned(db: Session, now: datetime) -> None:
    """Two hours exceeds bounded collection/lookup budgets; reads never mutate."""
    for model in (NewsDiscoveryRun, NewsFallbackLookup):
        db.execute(update(model).where(model.status == "running", model.started_at < now - timedelta(hours=2))
            .values(status="interrupted", finished_at=now, error_code="worker_interrupted"))


def finalize_attempt(db: Session, model: type[NewsDiscoveryRun] | type[NewsFallbackLookup],
                     id: int, *, status: str, now: datetime, error_code: str | None = None,
                     retry_after_seconds: int | None = None) -> bool:
    values = dict(status=status, finished_at=now, error_code=error_code)
    if model is NewsFallbackLookup:
        values["retry_after_seconds"] = retry_after_seconds
    result = db.execute(update(model).where(model.id == id, model.status == "running").values(**values))
    return result.rowcount == 1


def list_attempts(db: Session, kind: AttemptKind, page: int, page_size: int) -> tuple[list, list, int, int]:
    model, child, key = (NewsDiscoveryRun, NewsDiscoveryFeedRun, NewsDiscoveryFeedRun.discovery_run_id) if kind == "discovery" else (
        NewsFallbackLookup, NewsFallbackLookupLead, NewsFallbackLookupLead.lookup_id)
    total = db.scalar(select(func.count()).select_from(model)) or 0
    actual = min(page, max(1, (total + page_size - 1) // page_size))
    rows = list(db.scalars(select(model).order_by(model.started_at.desc(), model.id.desc())
        .offset((actual - 1) * page_size).limit(page_size)))
    ids = [row.id for row in rows]
    children = list(db.scalars(select(child).where(key.in_(ids)).order_by(child.id))) if ids else []
    return rows, children, total, actual
