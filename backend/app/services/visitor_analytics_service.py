"""Privacy-preserving visitor measurement for LANES' own first-party analytics."""

from datetime import date, datetime, timedelta, timezone
import hashlib
import hmac
from typing import Optional
from uuid import UUID

from sqlalchemy import String, case, cast, func, literal
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit import VisitorDailyVisit
from app.schemas.common import ensure_utc


_AUTOMATED_USER_AGENT_MARKERS = (
    "bot", "crawler", "spider", "slurp", "headless", "facebookexternalhit",
    "preview", "wget", "curl", "python-requests",
)


def is_automated_user_agent(user_agent: Optional[str]) -> bool:
    """Reject known automated clients without using invasive browser fingerprinting."""
    normalized = (user_agent or "").lower()
    return any(marker in normalized for marker in _AUTOMATED_USER_AGENT_MARKERS)


def hash_visitor_identifier(visitor_id: UUID) -> str:
    """Convert a browser UUID into a non-reversible server-side analytics key."""
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        str(visitor_id).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def record_visitor_activity(
    db: Session,
    *,
    visitor_id: UUID,
    user_id: Optional[int],
    user_agent: Optional[str],
    now: Optional[datetime] = None,
) -> bool:
    """Record at most one browser activity row per UTC day and return whether it was accepted."""
    if is_automated_user_agent(user_agent):
        return False

    recorded_at = ensure_utc(now) or datetime.now(timezone.utc)
    visitor_hash = hash_visitor_identifier(visitor_id)
    visit_date = recorded_at.date()
    visit = (
        db.query(VisitorDailyVisit)
        .filter(
            VisitorDailyVisit.visit_date == visit_date,
            VisitorDailyVisit.visitor_hash == visitor_hash,
        )
        .one_or_none()
    )
    if visit is None:
        visit = VisitorDailyVisit(
            visit_date=visit_date,
            visitor_hash=visitor_hash,
            user_id=user_id,
            first_seen_at=recorded_at,
            last_seen_at=recorded_at,
        )
        db.add(visit)
    else:
        visit.last_seen_at = recorded_at
        # A signed-in visit upgrades only that day's anonymous browser record.
        if user_id is not None:
            visit.user_id = user_id

    db.commit()
    return True


def _logical_visitor_key():
    """Use accounts where known; otherwise retain the anonymous browser hash."""
    return case(
        (VisitorDailyVisit.user_id.is_not(None), literal("account:") + cast(VisitorDailyVisit.user_id, String)),
        else_=VisitorDailyVisit.visitor_hash,
    )


def get_visitor_summary(db: Session, *, today: Optional[date] = None) -> dict[str, int]:
    """Return de-duplicated lifetime and current-day first-party visitor counts."""
    current_day = today or datetime.now(timezone.utc).date()
    visitor_key = _logical_visitor_key()
    total_unique_visitors = db.query(func.count(func.distinct(visitor_key))).scalar() or 0
    visitors_today = (
        db.query(func.count(func.distinct(visitor_key)))
        .filter(VisitorDailyVisit.visit_date == current_day)
        .scalar()
        or 0
    )
    return {
        "total_unique_visitors": int(total_unique_visitors),
        "visitors_today": int(visitors_today),
    }


def get_visitor_analytics(
    db: Session,
    *,
    days: int = 30,
    today: Optional[date] = None,
) -> dict:
    """Return a gap-free daily trend for the protected administrator dashboard."""
    current_day = today or datetime.now(timezone.utc).date()
    start_day = current_day - timedelta(days=days - 1)
    visitor_key = _logical_visitor_key()
    rows = (
        db.query(
            VisitorDailyVisit.visit_date,
            func.count(func.distinct(visitor_key)).label("unique_visitors"),
        )
        .filter(VisitorDailyVisit.visit_date >= start_day)
        .group_by(VisitorDailyVisit.visit_date)
        .order_by(VisitorDailyVisit.visit_date)
        .all()
    )
    by_date = {row.visit_date: int(row.unique_visitors) for row in rows}
    summary = get_visitor_summary(db, today=current_day)
    return {
        **summary,
        "daily_unique_visitors": [
            {
                "date": start_day + timedelta(days=offset),
                "unique_visitors": by_date.get(start_day + timedelta(days=offset), 0),
            }
            for offset in range(days)
        ],
    }
