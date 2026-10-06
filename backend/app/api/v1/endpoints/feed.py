from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user_optional, get_current_user
from app.models.user import User
from app.schemas.post import CommunityPostPaginatedResponse
from app.schemas.feed import TopReportersResponse, VoteResponse
from app.schemas.interaction import PostInteractionCreate
from app.crud import feed as crud_feed
from app.crud import interaction as crud_interaction
from app.models.interaction import InteractionType
from app.services.geocoding_service import resolve_address_coordinates

router = APIRouter()

@router.get("", response_model=CommunityPostPaginatedResponse)
def get_feed(
    lat: Optional[float] = Query(None, description="User's latitude"),
    lng: Optional[float] = Query(None, description="User's longitude"),
    radius: Optional[float] = Query(5000, description="Radius in meters for nearby filtering"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    tab: str = Query("recent", pattern="^(recent|nearby)$"),
    time_window_hours: Optional[int] = Query(72, ge=1, description="Filter posts from the last N hours (defaults to 72h / 3 days)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Retrieve community feed.
    If tab='nearby', lat and lng are used. If missing, falls back to the user's
    registered profile address (primary), and then saved places (secondary).
    By default, 'recent' tab prioritizes posts from the last 72 hours (3 days) to match
    flood hazard lifecycles, falling back gracefully to latest posts if none exist in that window.
    """
    resolved_location_name = None
    if tab == "nearby" and (lat is None or lng is None):
        # 1. Primary Fallback: Registered address from user profile (Registration address)
        if current_user and getattr(current_user, "profile", None) and getattr(current_user.profile, "address", None):
            addr = current_user.profile.address
            resolved = resolve_address_coordinates(
                barangay=addr.barangay,
                city=addr.city_municipality,
                province=addr.province
            )
            if resolved:
                lat, lng = resolved
                resolved_location_name = f"Brgy. {addr.barangay}, {addr.city_municipality}"

        # 2. Secondary Fallback: User's saved places (e.g. Home bookmark)
        if (lat is None or lng is None) and current_user and getattr(current_user, "saved_places", None):
            sorted_places = sorted(
                current_user.saved_places,
                key=lambda p: (
                    0 if (p.name and p.name.strip().lower() == "home") else 1,
                    p.pin_order if p.pin_order is not None else 999
                )
            )
            if sorted_places:
                primary_place = sorted_places[0]
                lat = primary_place.latitude
                lng = primary_place.longitude
                resolved_location_name = primary_place.name or "Saved Place"

        if lat is None or lng is None:
            raise HTTPException(
                status_code=400,
                detail="Latitude and longitude must be provided for 'nearby' feed, or complete your registered address in your profile."
            )

    user_id = current_user.id if current_user else None

    feed_data = crud_feed.get_feed_posts(
        db=db,
        user_id=user_id,
        lat=lat,
        lng=lng,
        radius=radius,
        skip=skip,
        limit=limit,
        tab=tab,
        time_window_hours=time_window_hours if tab == "recent" else None
    )

    # If the 72h window yielded 0 posts (e.g., dry season or seed data),
    # gracefully fall back to latest available posts so the feed is never an empty screen.
    if tab == "recent" and feed_data["total"] == 0 and time_window_hours is not None:
        feed_data = crud_feed.get_feed_posts(
            db=db,
            user_id=user_id,
            lat=lat,
            lng=lng,
            radius=radius,
            skip=skip,
            limit=limit,
            tab=tab,
            time_window_hours=None
        )

    # Concentric radius expansion: if 5km yielded 0 posts, expand search up to 15km
    # so users in adjacent barangays don't encounter an artificial blank feed.
    expanded_radius = False
    if tab == "nearby" and feed_data["total"] == 0 and radius is not None and radius < 15000:
        expanded_data = crud_feed.get_feed_posts(
            db=db,
            user_id=user_id,
            lat=lat,
            lng=lng,
            radius=15000,
            skip=skip,
            limit=limit,
            tab=tab,
            time_window_hours=None
        )
        if expanded_data["total"] > 0:
            feed_data = expanded_data
            expanded_radius = True

    return CommunityPostPaginatedResponse(
        posts=feed_data["posts"],
        total=feed_data["total"],
        has_more=feed_data["has_more"],
        expanded_radius=expanded_radius,
        resolved_location_name=resolved_location_name
    )



@router.get("/leaderboard", response_model=TopReportersResponse)
def get_leaderboard(
    limit: int = Query(5, ge=1, le=20, description="Number of top reporters to return"),
    db: Session = Depends(get_db),
):
    """Retrieve the top community reporters leaderboard ranked by approved public report count."""
    reporters = crud_feed.get_top_reporters(db=db, limit=limit)
    return TopReportersResponse(reporters=reporters)


@router.post("/{post_id}/vote", response_model=VoteResponse)
def vote_post(
    post_id: int,
    interaction_in: PostInteractionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upvote or downvote a feed post.
    If the exact same interaction is sent, it will toggle (remove) it.
    If a different interaction is sent (e.g. upvote when previously downvoted), it will swap.
    Returns the authoritative fresh vote counts, net score, and active user interaction.
    """
    if interaction_in.post_id != post_id:
        raise HTTPException(status_code=400, detail="Post ID mismatch")

    if interaction_in.interaction_type not in [InteractionType.UPVOTE, InteractionType.DOWNVOTE]:
        raise HTTPException(status_code=400, detail="Invalid interaction type")

    crud_interaction.toggle_interaction(
        db=db,
        user_id=current_user.id,
        interaction_in=interaction_in
    )

    summary = crud_interaction.get_post_vote_summary(
        db=db,
        post_id=post_id,
        user_id=current_user.id
    )

    return summary
