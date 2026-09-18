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
    If tab='nearby', lat and lng are required.
    By default, 'recent' tab prioritizes posts from the last 72 hours (3 days) to match
    flood hazard lifecycles, falling back gracefully to latest posts if none exist in that window.
    """
    if tab == "nearby" and (lat is None or lng is None):
        raise HTTPException(
            status_code=400, 
            detail="Latitude and longitude must be provided for 'nearby' feed."
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
    
    return feed_data


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

