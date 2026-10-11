"""Bounded saved collection diagnostics; a GET never checks feeds or writes."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.news_telemetry import NewsDiscoveryRun, NewsDiscoveryFeedRun


def latest_collection_diagnostics(db: Session) -> tuple[NewsDiscoveryRun | None, dict[str, int]]:
    latest = db.scalar(select(NewsDiscoveryRun).where(NewsDiscoveryRun.trigger == "collector")
                       .order_by(NewsDiscoveryRun.started_at.desc(), NewsDiscoveryRun.id.desc()).limit(1))
    if latest is None:
        return None, {}
    feeds = list(db.scalars(select(NewsDiscoveryFeedRun).where(NewsDiscoveryFeedRun.discovery_run_id == latest.id)))
    return latest, {
        "feeds_checked": len(feeds),
        "feed_errors": sum(feed.status not in ("parsed", "unchanged", "empty") for feed in feeds),
        "entries_read": sum(feed.entries_seen for feed in feeds),
        "articles_saved_or_seen": sum(feed.candidates_saved for feed in feeds),
        "body_errors": sum(feed.body_errors for feed in feeds),
        "scope_unresolved": sum(feed.scope_unresolved for feed in feeds),
    }
