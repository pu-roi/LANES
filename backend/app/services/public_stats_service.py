"""Landing-page counts derived from the public map's active-zone selection."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.crud.report import get_active_avoidance_zones
from app.schemas.common import ensure_utc
from app.schemas.visitor import PublicStatsResponse
from app.services.visitor_analytics_service import get_visitor_summary


def get_public_stats(db: Session) -> PublicStatsResponse:
    # Count zones once, including official zones without a submitted report and
    # zones supported by multiple reports. Reuse the map's expiry/configuration clock.
    zones = get_active_avoidance_zones(db)
    from app.services.historical_news_metadata import event_metadata
    historical = event_metadata(db, [zone.event_id for zone in zones if zone.event_id])
    zones = [zone for zone in zones if zone.event_id not in historical or not historical[zone.event_id].is_demo]
    today = datetime.now(timezone.utc).date()
    return PublicStatsResponse(
        # Active map zones created on today's UTC date, counted once per zone.
        daily_verified_reports=sum(
            1 for zone in zones
            if zone.created_at and ensure_utc(zone.created_at).astimezone(timezone.utc).date() == today
        ),
        total_visitors=get_visitor_summary(db)["total_unique_visitors"],
    )
