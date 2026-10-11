"""Recent community activity; this ranking does not establish flood severity."""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.crud.trending_hotspots import read_trending_hotspots
from app.schemas.feed import TrendingHotspot, TrendingHotspotsResponse

WINDOW_HOURS = 24
FALLBACK_WINDOW_HOURS = 48
HALF_LIFE_HOURS = 6
MINIMUM_CONTRIBUTORS = 2
CLUSTER_RADIUS_METERS = 500


def get_trending_hotspots(
    db: Session, limit: int = 3, *, now: datetime | None = None,
) -> TrendingHotspotsResponse:
    as_of = now or datetime.now(timezone.utc)
    for window_hours in (WINDOW_HOURS, FALLBACK_WINDOW_HOURS):
        rows = read_trending_hotspots(
            db, now=as_of, cutoff=as_of - timedelta(hours=window_hours),
            half_life_hours=HALF_LIFE_HOURS, minimum_contributors=MINIMUM_CONTRIBUTORS,
            cluster_radius_meters=CLUSTER_RADIUS_METERS, limit=limit,
        )
        if rows:
            break
    return TrendingHotspotsResponse(
        hotspots=[TrendingHotspot(**row) for row in rows],
        window_hours=window_hours, as_of=as_of,
    )
