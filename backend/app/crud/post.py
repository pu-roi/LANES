from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.post import CommunityPost, CommunityPostEditHistory
from app.schemas.post import CommunityPostCreate, CommunityPostUpdate

def create_community_post(db: Session, post_in: CommunityPostCreate, user_id: int):
    db_post = CommunityPost(
        user_id=user_id,
        flood_report_id=post_in.flood_report_id,
        content=post_in.content,
        media_urls=post_in.media_urls,
        location_tag=post_in.location_tag,
        location_lat=post_in.location_lat,
        location_lng=post_in.location_lng
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def get_post(db: Session, post_id: int):
    return db.query(CommunityPost).filter(CommunityPost.id == post_id).first()

def get_posts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(CommunityPost).order_by(CommunityPost.created_at.desc()).offset(skip).limit(limit).all()


def update_community_post(db: Session, post: CommunityPost, post_in: CommunityPostUpdate, editor_user_id: int) -> CommunityPost:
    last_version = (
        db.query(CommunityPostEditHistory.version)
        .filter(CommunityPostEditHistory.post_id == post.id)
        .order_by(CommunityPostEditHistory.version.desc())
        .first()
    )
    history = CommunityPostEditHistory(
        post_id=post.id,
        editor_user_id=editor_user_id,
        version=(last_version[0] + 1) if last_version else 1,
        previous_content=post.content,
        previous_media_urls=post.media_urls,
        previous_location_tag=post.location_tag,
        previous_location_lat=post.location_lat,
        previous_location_lng=post.location_lng,
        updated_content=post_in.content,
        updated_media_urls=post_in.media_urls,
        updated_location_tag=post_in.location_tag,
        updated_location_lat=post_in.location_lat,
        updated_location_lng=post_in.location_lng,
    )
    post.content = post_in.content
    post.media_urls = post_in.media_urls
    post.location_tag = post_in.location_tag
    post.location_lat = post_in.location_lat
    post.location_lng = post_in.location_lng
    db.add(history)
    db.commit()
    db.refresh(post)
    return post


def get_post_edit_history(db: Session, post_id: int) -> list[CommunityPostEditHistory]:
    return (
        db.query(CommunityPostEditHistory)
        .filter(CommunityPostEditHistory.post_id == post_id)
        .order_by(CommunityPostEditHistory.version.asc())
        .all()
    )

def soft_delete_post(db: Session, post_id: int, deleted_by_user_id: Optional[int] = None) -> Optional[CommunityPost]:
    db_post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if db_post:
        db_post.deleted_at = datetime.now(timezone.utc)
        db_post.deleted_by_user_id = deleted_by_user_id
        db.commit()
        db.refresh(db_post)
        return db_post
    return None

def delete_post(db: Session, post_id: int, deleted_by_user_id: Optional[int] = None):
    return soft_delete_post(db, post_id=post_id, deleted_by_user_id=deleted_by_user_id)

def restore_post(db: Session, post_id: int) -> Optional[CommunityPost]:
    db_post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if db_post:
        db_post.deleted_at = None
        db_post.deleted_by_user_id = None
        db_post.hidden_at = None
        db_post.hidden_by_user_id = None
        db.commit()
        db.refresh(db_post)
        return db_post
    return None

def hard_delete_post(db: Session, post_id: int) -> bool:
    db_post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if db_post:
        db.delete(db_post)
        db.commit()
        return True
    return False

def get_archived_posts(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    post_filter: str = "deleted",
    search: Optional[str] = None
) -> Tuple[List[CommunityPost], int]:
    from sqlalchemy.orm import joinedload
    from app.models.user import User

    query = db.query(CommunityPost)
    if post_filter == "deleted":
        query = query.filter(CommunityPost.deleted_at.is_not(None))
    elif post_filter == "hidden":
        query = query.filter(CommunityPost.hidden_at.is_not(None), CommunityPost.deleted_at.is_(None))
    else:
        query = query.filter(
            or_(CommunityPost.deleted_at.is_not(None), CommunityPost.hidden_at.is_not(None))
        )
    
    if search:
        query = query.filter(CommunityPost.content.ilike(f"%{search}%"))
        
    total = query.count()
    posts = (
        query.options(
            joinedload(CommunityPost.user).joinedload(User.profile),
            joinedload(CommunityPost.deleted_by).joinedload(User.profile),
            joinedload(CommunityPost.hidden_by).joinedload(User.profile),
        )
        .order_by(CommunityPost.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return posts, total
