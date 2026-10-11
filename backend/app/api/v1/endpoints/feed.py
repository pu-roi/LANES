from typing import Annotated, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user_optional, get_current_user
from app.models.user import User
from app.models.report import ReportSeverity
from app.schemas.post import CommunityPostPaginatedResponse
from app.schemas.feed import CommunityFeedFilters, FeedSort, FeedDateRange, FeedFloodStatus, TopReportersResponse, VoteResponse, TrendingHotspotsResponse
from app.services.trending_hotspots_service import get_trending_hotspots
from app.schemas.interaction import PostInteractionCreate
from app.crud import feed as crud_feed
from app.crud import interaction as crud_interaction
from app.models.interaction import InteractionType
from app.services.community_feed_service import FeedLocationUnavailable, read_community_feed

router = APIRouter()

@router.get("", response_model=CommunityPostPaginatedResponse)
def get_feed(
    lat: Annotated[Optional[float], Query(ge=-90, le=90)] = None,
    lng: Annotated[Optional[float], Query(ge=-180, le=180)] = None,
    radius: Annotated[Optional[float], Query(gt=0, le=15000,
        description="Explicit radius in metres; omitted uses automatic 5-to-15 km discovery")] = None,
    skip: Annotated[int, Query(ge=0, le=2147483647)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    tab: Annotated[Literal["recent", "nearby"], Query()] = "recent",
    time_window_hours: Annotated[Optional[int], Query(ge=1, le=8760,
        description="Legacy rolling-hour constraint; never falls back outside the selected window")] = None,
    sort: Annotated[FeedSort, Query()] = "newest",
    date_range: Annotated[FeedDateRange, Query(description="Today uses the UTC calendar date")] = "all",
    flood_status: Annotated[FeedFloodStatus, Query()] = "all",
    severity: Annotated[Optional[ReportSeverity], Query()] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> CommunityPostPaginatedResponse:
    """Filter the complete public dataset before stable ordering and pagination."""
    if (lat is None) != (lng is None):
        raise HTTPException(422, "Provide both latitude and longitude.")
    try:
        return read_community_feed(db, current_user, lat=lat, lng=lng, radius=radius,
            skip=skip, limit=limit, tab=tab, time_window_hours=time_window_hours,
            filters=CommunityFeedFilters(sort=sort, date_range=date_range,
                flood_status=flood_status, severity=severity))
    except FeedLocationUnavailable as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/hotspots", response_model=TrendingHotspotsResponse)
def trending_hotspots(
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
) -> TrendingHotspotsResponse:
    """Public 24-hour place activity, expanding to 48 hours only when empty."""
    return get_trending_hotspots(db, limit=limit)


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
