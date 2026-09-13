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

def delete_post(db: Session, post_id: int):
    db_post = get_post(db, post_id)
    if db_post:
        db.delete(db_post)
        db.commit()
        return True
    return False
