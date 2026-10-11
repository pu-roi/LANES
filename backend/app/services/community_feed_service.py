"""Community discovery using the existing publication and Nearby location rules."""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.feed import CommunityFeedFilters, FeedDateRange
from app.schemas.post import CommunityPostPaginatedResponse
from app.services.geocoding_service import resolve_address_coordinates


class FeedLocationUnavailable(ValueError):
    pass


def publication_bounds(date_range: FeedDateRange, now: datetime) -> tuple[datetime | None, datetime | None]:
    """Calendar Today uses UTC; other periods are rolling windows from one clock."""
    now = now.astimezone(timezone.utc)
    if date_range == "all":
        return None, None
    if date_range == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0), now
    return now - timedelta(hours={"24h": 24, "3d": 72, "7d": 168}[date_range]), now


def read_community_feed(
    db: Session, current_user: User | None, *, lat: float | None, lng: float | None,
    radius: float | None, skip: int, limit: int, tab: str,
    filters: CommunityFeedFilters, time_window_hours: int | None = None,
) -> CommunityPostPaginatedResponse:
    from app.crud import feed as crud_feed

    resolved_location_name = None
    if tab == "nearby" and (lat is None or lng is None):
        if current_user and getattr(current_user, "profile", None) and getattr(current_user.profile, "address", None):
            addr = current_user.profile.address
            resolved = resolve_address_coordinates(barangay=addr.barangay,
                city=addr.city_municipality, province=addr.province)
            if resolved:
                lat, lng = resolved
                resolved_location_name = f"Brgy. {addr.barangay}, {addr.city_municipality}"
        if (lat is None or lng is None) and current_user and getattr(current_user, "saved_places", None):
            places = sorted(current_user.saved_places, key=lambda p: (
                0 if p.name and p.name.strip().lower() == "home" else 1,
                p.pin_order if p.pin_order is not None else 999))
            if places:
                lat, lng = places[0].latitude, places[0].longitude
                resolved_location_name = places[0].name or "Saved Place"
        if lat is None or lng is None:
            raise FeedLocationUnavailable("Latitude and longitude must be provided for 'nearby' feed, or complete your registered address in your profile.")

    options = dict(db=db, user_id=current_user.id if current_user else None,
        lat=lat, lng=lng, radius=radius if radius is not None else 5000,
        skip=skip, limit=limit, tab=tab, filters=filters,
        time_window_hours=time_window_hours)
    feed_data = crud_feed.get_feed_posts(**options)
    expanded_radius = False
    # Preserve automatic 5-to-15 km discovery only when no explicit radius was
    # selected. Never drop date/status/severity constraints to fill an empty page.
    if tab == "nearby" and radius is None and feed_data["total"] == 0:
        expanded = crud_feed.get_feed_posts(**{**options, "radius": 15000})
        if expanded["total"] > 0:
            feed_data, expanded_radius = expanded, True
    return CommunityPostPaginatedResponse(**feed_data, expanded_radius=expanded_radius,
        resolved_location_name=resolved_location_name)
