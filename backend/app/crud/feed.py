from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, case, text, Float, String, and_, or_
from app.models.report import FloodReport
from app.models.interaction import PostInteraction
from app.models.user import User
from app.models.profile import Profile
from app.models.post import CommunityPost
from app.models.comment import Comment
from typing import Optional, List
from app.schemas.feed import TopReporter

def get_feed_posts(
    db: Session,
    user_id: Optional[int] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius: Optional[float] = None,
    skip: int = 0,
    limit: int = 20,
    tab: str = "recent",
    author_id: Optional[int] = None,
    time_window_hours: Optional[int] = None
):
    # Base query for community posts
    base_query = db.query(CommunityPost).outerjoin(FloodReport, CommunityPost.flood_report_id == FloodReport.id).filter(CommunityPost.deleted_at.is_(None))
    if user_id is None:
        base_query = base_query.filter(CommunityPost.hidden_at.is_(None))
    else:
        base_query = base_query.filter((CommunityPost.hidden_at.is_(None)) | (CommunityPost.user_id == user_id))
    if author_id:
        base_query = base_query.filter(CommunityPost.user_id == author_id)
    if time_window_hours is not None:
        cutoff = datetime.utcnow() - timedelta(hours=time_window_hours)
        base_query = base_query.filter(CommunityPost.created_at >= cutoff)

    # Subqueries for upvotes and downvotes
    upvotes_query = db.query(
        PostInteraction.post_id,
        func.count(PostInteraction.id).label("upvotes")
    ).filter(PostInteraction.interaction_type == "upvote").group_by(PostInteraction.post_id).subquery()

    downvotes_query = db.query(
        PostInteraction.post_id,
        func.count(PostInteraction.id).label("downvotes")
    ).filter(PostInteraction.interaction_type == "downvote").group_by(PostInteraction.post_id).subquery()

    # Subquery for comments
    comments_query = db.query(
        Comment.post_id,
        func.count(Comment.id).label("comment_count")
    ).group_by(Comment.post_id).subquery()

    # Subquery for current user interaction if user_id is provided
    user_interaction_sq = None
    if user_id:
        user_interaction_sq = db.query(
            PostInteraction.post_id,
            PostInteraction.interaction_type.label("user_interaction")
        ).filter(PostInteraction.user_id == user_id).subquery()

    # Build author name expression respecting display_full_name preference
    author_name_expr = case(
        (
            and_(
                func.coalesce(Profile.display_full_name, True).is_(True),
                Profile.first_name.isnot(None),
                func.trim(Profile.first_name) != ""
            ),
            func.trim(func.concat(Profile.first_name, text("' '"), func.coalesce(Profile.last_name, text("''"))))
        ),
        else_=func.coalesce(User.username, text("'Unknown'"))
    ).label("author_name")

    # Build author avatar expression respecting hide_profile_picture preference
    author_avatar_expr = case(
        (
            and_(
                Profile.avatar_url.isnot(None),
                func.coalesce(Profile.hide_profile_picture, False).is_(False)
            ),
            Profile.avatar_url
        ),
        else_=text("null")
    ).label("author_avatar")

    # Build the main select fields
    select_fields = [
        CommunityPost,
        func.coalesce(upvotes_query.c.upvotes, 0).label("upvotes"),
        func.coalesce(downvotes_query.c.downvotes, 0).label("downvotes"),
        author_name_expr,
        author_avatar_expr,
        func.coalesce(comments_query.c.comment_count, 0).label("comment_count"),
        FloodReport # to eager load the report if exists
    ]

    # Distance calculation if lat/lng are provided
    distance_col = None
    if lat is not None and lng is not None:
        # Create a PostGIS point for the user location
        user_pt = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)

        # Build a point from the post's own location_lat/lng (if available)
        post_pt = func.ST_SetSRID(
            func.ST_MakePoint(CommunityPost.location_lng, CommunityPost.location_lat), 4326
        )

        # Distance from flood report geometry (if the post has a linked report)
        report_distance = func.ST_Distance(
            func.cast(FloodReport.geometry, text("GEOGRAPHY")),
            func.cast(user_pt, text("GEOGRAPHY"))
        )

        # Distance from post's own location coordinates
        post_distance = func.ST_Distance(
            func.cast(post_pt, text("GEOGRAPHY")),
            func.cast(user_pt, text("GEOGRAPHY"))
        )

        # Prefer flood report geometry distance; fall back to post location distance
        distance_col = case(
            (CommunityPost.flood_report_id.isnot(None), report_distance),
            (
                and_(
                    CommunityPost.location_lat.isnot(None),
                    CommunityPost.location_lng.isnot(None)
                ),
                post_distance
            ),
            else_=func.cast(None, Float)
        ).label("distance_meters")
        select_fields.append(distance_col)

        if radius is not None and tab == "nearby":
            # Include posts that either:
            #   1. Have a linked flood report with geometry within the radius, OR
            #   2. Have post-level location_lat/lng within the radius
            # Posts with no location data at all are excluded.
            has_report_nearby = and_(
                CommunityPost.flood_report_id.isnot(None),
                func.ST_DWithin(
                    func.cast(FloodReport.geometry, text("GEOGRAPHY")),
                    func.cast(user_pt, text("GEOGRAPHY")),
                    radius
                )
            )
            has_post_location_nearby = and_(
                CommunityPost.location_lat.isnot(None),
                CommunityPost.location_lng.isnot(None),
                func.ST_DWithin(
                    func.cast(post_pt, text("GEOGRAPHY")),
                    func.cast(user_pt, text("GEOGRAPHY")),
                    radius
                )
            )
            base_query = base_query.filter(or_(has_report_nearby, has_post_location_nearby))
    else:
        # Placeholder for distance if no location is given
        select_fields.append(func.cast(None, Float).label("distance_meters"))

    if user_interaction_sq is not None:
        select_fields.append(user_interaction_sq.c.user_interaction)
    else:
        select_fields.append(func.cast(None, String).label("user_interaction"))

    # Join the subqueries
    query = base_query.with_entities(*select_fields)
    query = query.outerjoin(User, CommunityPost.user_id == User.id)
    query = query.outerjoin(Profile, User.id == Profile.user_id)
    query = query.outerjoin(upvotes_query, CommunityPost.id == upvotes_query.c.post_id)
    query = query.outerjoin(downvotes_query, CommunityPost.id == downvotes_query.c.post_id)
    query = query.outerjoin(comments_query, CommunityPost.id == comments_query.c.post_id)
    if user_interaction_sq is not None:
        query = query.outerjoin(user_interaction_sq, CommunityPost.id == user_interaction_sq.c.post_id)

    # ── Shared scoring components ──────────────────────────────────────────
    # Age in hours (floored at 0.01 to avoid division-by-zero for brand-new posts)
    age_hours = func.greatest(
        func.extract('epoch', func.now() - CommunityPost.created_at) / 3600.0,
        0.01
    )

    net_votes = func.greatest(
        func.coalesce(upvotes_query.c.upvotes, 0) - func.coalesce(downvotes_query.c.downvotes, 0),
        0
    )

    engagement_points = net_votes + (func.coalesce(comments_query.c.comment_count, 0) * 0.5)

    # Content-type boost: flood reports get a head start, location-tagged posts get a smaller one
    content_boost = case(
        (CommunityPost.flood_report_id.isnot(None), 3.0),
        (and_(
            CommunityPost.location_lat.isnot(None),
            CommunityPost.location_lng.isnot(None)
        ), 1.0),
        else_=0.0
    )

    # ── Ordering ─────────────────────────────────────────────────────────
    if tab == "nearby" and distance_col is not None:
        # Nearby: blend distance relevance (60%) with engagement (40%)
        effective_radius = func.coalesce(func.cast(radius, Float), 5000.0)
        distance_score = func.greatest(
            1.0 - (distance_col / effective_radius),
            0.0
        )

        nearby_engagement = engagement_points + content_boost
        # Log-scale engagement to prevent mega-upvoted posts from dominating distance
        nearby_engagement_norm = func.log(func.greatest(nearby_engagement, 1) + 1)

        nearby_score = (0.6 * distance_score) + (0.4 * nearby_engagement_norm)
        query = query.order_by(nearby_score.desc(), CommunityPost.created_at.desc())
    else:
        # Recent: HN-inspired hot score with civic boosts and gravity decay
        gravity = 1.5
        hot_score = (engagement_points + content_boost) / func.power(age_hours + 2, gravity)
        query = query.order_by(hot_score.desc())

    total = base_query.count()
    results = query.offset(skip).limit(limit).all()
    
    has_more = (skip + limit) < total

    # Format the results to match CommunityPostResponse
    posts = []
    for row in results:
        # Access elements by index or name
        post = row[0]
        upvotes = row[1]
        downvotes = row[2]
        author_name = row[3]
        author_avatar = row[4]
        comment_count = row[5]
        report = row[6]
        dist = row[7]
        u_int = row[8]
        
        # Convert ORM model to dictionary
        post_data = {
            **post.__dict__,
            "flood_report_id": post.flood_report_id,
            "upvotes": upvotes,
            "downvotes": downvotes,
            "distance_meters": dist,
            "user_interaction": u_int,
            "author_name": author_name,
            "author_avatar": author_avatar,
            "comment_count": comment_count,
            "report": report
        }
        posts.append(post_data)

    return {
        "posts": posts,
        "total": total,
        "has_more": has_more
    }


def get_top_reporters(
    db: Session,
    limit: int = 5
) -> List[TopReporter]:
    """Retrieve the top community reporters ranked by their approved, public report count."""
    top_avatar_expr = case(
        (
            and_(
                Profile.avatar_url.isnot(None),
                func.coalesce(Profile.hide_profile_picture, False).is_(False)
            ),
            Profile.avatar_url
        ),
        else_=text("null")
    ).label("avatar_url")

    results = (
        db.query(
            User.id.label("user_id"),
            User.username.label("username"),
            top_avatar_expr,
            func.count(FloodReport.id).label("report_count")
        )
        .join(FloodReport, FloodReport.user_id == User.id)
        .outerjoin(Profile, Profile.user_id == User.id)
        .filter(
            FloodReport.status == "approved",
            FloodReport.is_public == True,
            FloodReport.deleted_at.is_(None),
            User.deleted_at.is_(None),
            User.is_active == True
        )
        .group_by(User.id, User.username, Profile.avatar_url, Profile.hide_profile_picture)
        .order_by(func.count(FloodReport.id).desc())
        .limit(limit)
        .all()
    )

    reporters: List[TopReporter] = []
    for rank, row in enumerate(results, start=1):
        reporters.append(
            TopReporter(
                rank=rank,
                user_id=row.user_id,
                username=row.username,
                avatar_url=row.avatar_url,
                report_count=row.report_count,
            )
        )
    return reporters

def get_feed_post(
    db: Session,
    post_id: int,
    user_id: Optional[int] = None
):
    # Base query for community post
    base_query = db.query(CommunityPost).filter(CommunityPost.id == post_id, CommunityPost.deleted_at.is_(None)).outerjoin(FloodReport, CommunityPost.flood_report_id == FloodReport.id)
    if user_id is None:
        base_query = base_query.filter(CommunityPost.hidden_at.is_(None))
    else:
        base_query = base_query.filter((CommunityPost.hidden_at.is_(None)) | (CommunityPost.user_id == user_id))

    # Subqueries for upvotes and downvotes
    upvotes_query = db.query(
        PostInteraction.post_id,
        func.count(PostInteraction.id).label("upvotes")
    ).filter(PostInteraction.interaction_type == "upvote").group_by(PostInteraction.post_id).subquery()

    downvotes_query = db.query(
        PostInteraction.post_id,
        func.count(PostInteraction.id).label("downvotes")
    ).filter(PostInteraction.interaction_type == "downvote").group_by(PostInteraction.post_id).subquery()

    # Subquery for comments
    comments_query = db.query(
        Comment.post_id,
        func.count(Comment.id).label("comment_count")
    ).group_by(Comment.post_id).subquery()

    # Subquery for current user interaction if user_id is provided
    user_interaction_sq = None
    if user_id:
        user_interaction_sq = db.query(
            PostInteraction.post_id,
            PostInteraction.interaction_type.label("user_interaction")
        ).filter(PostInteraction.user_id == user_id).subquery()

    # Build author name expression respecting display_full_name preference
    author_name_expr = case(
        (
            and_(
                func.coalesce(Profile.display_full_name, True).is_(True),
                Profile.first_name.isnot(None),
                func.trim(Profile.first_name) != ""
            ),
            func.trim(func.concat(Profile.first_name, text("' '"), func.coalesce(Profile.last_name, text("''"))))
        ),
        else_=func.coalesce(User.username, text("'Unknown'"))
    ).label("author_name")

    # Build author avatar expression respecting hide_profile_picture preference
    author_avatar_expr = case(
        (
            and_(
                Profile.avatar_url.isnot(None),
                func.coalesce(Profile.hide_profile_picture, False).is_(False)
            ),
            Profile.avatar_url
        ),
        else_=text("null")
    ).label("author_avatar")

    # Build the main select fields
    select_fields = [
        CommunityPost,
        func.coalesce(upvotes_query.c.upvotes, 0).label("upvotes"),
        func.coalesce(downvotes_query.c.downvotes, 0).label("downvotes"),
        author_name_expr,
        author_avatar_expr,
        func.coalesce(comments_query.c.comment_count, 0).label("comment_count"),
        FloodReport # to eager load the report if exists
    ]

    # No distance logic needed for a single post view by ID unless requested, we just return null for distance
    select_fields.append(func.cast(None, Float).label("distance_meters"))

    if user_interaction_sq is not None:
        select_fields.append(user_interaction_sq.c.user_interaction)
    else:
        select_fields.append(func.cast(None, String).label("user_interaction"))

    # Join the subqueries
    query = base_query.with_entities(*select_fields)
    query = query.outerjoin(User, CommunityPost.user_id == User.id)
    query = query.outerjoin(Profile, User.id == Profile.user_id)
    query = query.outerjoin(upvotes_query, CommunityPost.id == upvotes_query.c.post_id)
    query = query.outerjoin(downvotes_query, CommunityPost.id == downvotes_query.c.post_id)
    query = query.outerjoin(comments_query, CommunityPost.id == comments_query.c.post_id)
    if user_interaction_sq is not None:
        query = query.outerjoin(user_interaction_sq, CommunityPost.id == user_interaction_sq.c.post_id)

    row = query.first()
    if not row:
        return None

    # Format the results to match CommunityPostResponse
    post = row[0]
    upvotes = row[1]
    downvotes = row[2]
    author_name = row[3]
    author_avatar = row[4]
    comment_count = row[5]
    report = row[6]
    dist = row[7]
    u_int = row[8]
    
    # Convert ORM model to dictionary
    post_data = {
        **post.__dict__,
        "upvotes": upvotes,
        "downvotes": downvotes,
        "distance_meters": dist,
        "user_interaction": u_int,
        "author_name": author_name,
        "author_avatar": author_avatar,
        "comment_count": comment_count,
        "report": report
    }

    return post_data
