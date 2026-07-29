from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.post import CommunityPost
from app.models.comment import Comment
from app.models.interaction import CommentInteraction, InteractionType
from app.models.notification import NotificationType
from app.schemas.notification import NotificationCreate
from app.crud import notification as crud_notification

router = APIRouter()


class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None


class CommentEdit(BaseModel):
    content: str


class CommentResponse(BaseModel):
    """Response schema for a single comment."""
    id: int
    content: str
    created_at: datetime
    edited_at: Optional[datetime] = None
    author_name: str
    parent_id: Optional[int]
    upvotes: int
    downvotes: int
    user_interaction: Optional[str] = None
    is_deleted: bool = False
    is_pinned: bool = False
    pinned_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VoteCommentRequest(BaseModel):
    type: InteractionType


def _build_comment_response(
    c: Comment,
    user_interactions: dict,
    is_deleted_override: bool = False,
) -> dict:
    """Build a comment response dict, redacting content when soft-deleted."""
    if c.is_deleted or is_deleted_override:
        return {
            "id": c.id,
            "content": "[deleted]",
            "created_at": c.created_at,
            "edited_at": None,
            "author_name": "[deleted]",
            "parent_id": c.parent_id,
            "upvotes": c.upvotes,
            "downvotes": c.downvotes,
            "user_interaction": user_interactions.get(c.id),
            "is_deleted": True,
            "is_pinned": c.is_pinned,
            "pinned_by": c.pinned_by,
        }
    return {
        "id": c.id,
        "content": c.content,
        "created_at": c.created_at,
        "edited_at": c.edited_at,
        "author_name": c.user.username if c.user else "Unknown User",
        "parent_id": c.parent_id,
        "upvotes": c.upvotes,
        "downvotes": c.downvotes,
        "user_interaction": user_interactions.get(c.id),
        "is_deleted": False,
        "is_pinned": c.is_pinned,
        "pinned_by": c.pinned_by,
    }


@router.get("/{post_id}/comments", response_model=List[CommentResponse])
def get_comments(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve all comments for a post."""
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .all()
    )

    user_interactions: dict = {}
    if current_user:
        interactions = db.query(CommentInteraction).filter(
            CommentInteraction.user_id == current_user.id,
            CommentInteraction.comment_id.in_([c.id for c in comments]),
        ).all()
        for inter in interactions:
            user_interactions[inter.comment_id] = inter.interaction_type.value

    return [_build_comment_response(c, user_interactions) for c in comments]


@router.post("/{post_id}/comments", response_model=CommentResponse)
def create_comment(
    post_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new top-level or nested comment on a post."""
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if comment_in.parent_id:
        parent = db.query(Comment).filter(Comment.id == comment_in.parent_id).first()
        if not parent or parent.post_id != post_id:
            raise HTTPException(status_code=400, detail="Invalid parent comment")

    db_comment = Comment(
        user_id=current_user.id,
        post_id=post_id,
        content=comment_in.content,
        parent_id=comment_in.parent_id,
    )

    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    # Notify post author or parent comment author
    target_user_id = post.user_id
    if comment_in.parent_id:
        parent_comment = db.query(Comment).filter(Comment.id == comment_in.parent_id).first()
        if parent_comment:
            target_user_id = parent_comment.user_id

    if target_user_id != current_user.id:
        msg = "Someone replied to your comment." if comment_in.parent_id else "Someone commented on your post."
        crud_notification.create_notification(
            db,
            NotificationCreate(
                user_id=target_user_id,
                type=NotificationType.COMMENT,
                message=msg,
                payload={"post_id": post_id, "actor_id": current_user.id, "comment_id": db_comment.id},
            ),
        )

    return {
        "id": db_comment.id,
        "content": db_comment.content,
        "created_at": db_comment.created_at,
        "edited_at": None,
        "author_name": current_user.username,
        "parent_id": db_comment.parent_id,
        "upvotes": 0,
        "downvotes": 0,
        "user_interaction": None,
        "is_deleted": False,
        "is_pinned": False,
        "pinned_by": None,
    }


@router.patch("/comments/{comment_id}", response_model=CommentResponse)
def edit_comment(
    comment_id: int,
    edit_in: CommentEdit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Edit the content of a comment. Only the author can edit."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
    if comment.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot edit a deleted comment")

    comment.content = edit_in.content
    comment.edited_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)

    return _build_comment_response(comment, {})


@router.post("/comments/{comment_id}/pin")
def pin_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle the pinned state of a comment. Allowed for: post author, and non-Commuter roles (admins)."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    post = db.query(CommunityPost).filter(CommunityPost.id == comment.post_id).first()
    is_post_author = post and post.user_id == current_user.id
    is_admin = current_user.role.name != "Commuter"

    if not is_post_author and not is_admin:
        raise HTTPException(status_code=403, detail="Only the post author or admins can pin comments")

    comment.is_pinned = not comment.is_pinned
    comment.pinned_by = current_user.username if comment.is_pinned else None
    db.commit()

    return {"is_pinned": comment.is_pinned, "pinned_by": comment.pinned_by}


@router.post("/comments/{comment_id}/vote")
def vote_comment(
    comment_id: int,
    vote_in: VoteCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upvote or downvote a comment, with toggle support."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    interaction = db.query(CommentInteraction).filter(
        CommentInteraction.user_id == current_user.id,
        CommentInteraction.comment_id == comment_id,
    ).first()

    if interaction:
        if interaction.interaction_type == vote_in.type:
            # Toggle off
            if vote_in.type == InteractionType.UPVOTE:
                comment.upvotes -= 1
            else:
                comment.downvotes -= 1
            db.delete(interaction)
        else:
            # Switch vote
            if vote_in.type == InteractionType.UPVOTE:
                comment.upvotes += 1
                comment.downvotes -= 1
            else:
                comment.upvotes -= 1
                comment.downvotes += 1
            interaction.interaction_type = vote_in.type
    else:
        # New vote
        new_interaction = CommentInteraction(
            user_id=current_user.id,
            comment_id=comment_id,
            interaction_type=vote_in.type,
        )
        db.add(new_interaction)
        if vote_in.type == InteractionType.UPVOTE:
            comment.upvotes += 1
        else:
            comment.downvotes += 1

    db.commit()
    return {"message": "Vote registered"}


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a comment. If it has replies, perform a soft delete (marks as deleted,
    preserves the reply chain). Otherwise hard-deletes the row.
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    has_replies = db.query(Comment).filter(Comment.parent_id == comment_id).first() is not None
    if has_replies:
        comment.is_deleted = True
        comment.content = "[deleted]"
        db.commit()
    else:
        db.delete(comment)
        db.commit()

    return {"message": "Comment deleted successfully"}


@router.get("/users/search")
def search_users(
    q: str = Query(..., min_length=1, max_length=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search usernames by prefix for @mention autocomplete. Requires login."""
    users = (
        db.query(User.username)
        .filter(User.username.ilike(f"{q}%"), User.is_active == True)
        .order_by(User.username)
        .limit(8)
        .all()
    )
    return {"usernames": [u.username for u in users]}
