from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.interaction import PostInteraction, InteractionType
from app.schemas.interaction import PostInteractionCreate

def get_interaction(db: Session, user_id: int, post_id: int):
    return db.query(PostInteraction).filter(
        and_(
            PostInteraction.user_id == user_id,
            PostInteraction.post_id == post_id
        )
    ).first()

def toggle_interaction(db: Session, user_id: int, interaction_in: PostInteractionCreate):
    existing = get_interaction(db, user_id, interaction_in.post_id)
    
    if existing:
        if existing.interaction_type == interaction_in.interaction_type:
            # Toggle off if it's the exact same type
            db.delete(existing)
            db.commit()
            return None
        else:
            # Switch interaction type (e.g. upvote to downvote)
            existing.interaction_type = interaction_in.interaction_type
            db.commit()
            db.refresh(existing)
            return existing
            
    # Create new
    db_obj = PostInteraction(
        user_id=user_id,
        post_id=interaction_in.post_id,
        interaction_type=interaction_in.interaction_type
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_post_vote_summary(db: Session, post_id: int, user_id: Optional[int] = None):
    upvotes = db.query(func.count(PostInteraction.id)).filter(
        PostInteraction.post_id == post_id,
        PostInteraction.interaction_type == InteractionType.UPVOTE
    ).scalar() or 0

    downvotes = db.query(func.count(PostInteraction.id)).filter(
        PostInteraction.post_id == post_id,
        PostInteraction.interaction_type == InteractionType.DOWNVOTE
    ).scalar() or 0

    user_interaction = None
    if user_id:
        interaction = db.query(PostInteraction).filter(
            PostInteraction.post_id == post_id,
            PostInteraction.user_id == user_id
        ).first()
        if interaction:
            user_interaction = interaction.interaction_type.value if hasattr(interaction.interaction_type, "value") else str(interaction.interaction_type)

    return {
        "post_id": post_id,
        "upvotes": upvotes,
        "downvotes": downvotes,
        "net_score": upvotes - downvotes,
        "user_interaction": user_interaction,
    }

