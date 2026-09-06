from sqlalchemy.orm import Session
from app.models.post import CommunityPost
from app.schemas.post import CommunityPostCreate

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

def delete_post(db: Session, post_id: int):
    db_post = get_post(db, post_id)
    if db_post:
        db.delete(db_post)
        db.commit()
        return True
    return False
