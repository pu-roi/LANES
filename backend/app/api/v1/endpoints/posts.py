from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user_optional, get_current_user
from app.models.user import User
from app.schemas.post import CommunityPostCreate, CommunityPostResponse, CommunityPostPaginatedResponse, CommentCreate, CommentResponse
from app.schemas.interaction import PostInteractionCreate, PostInteraction
from app.crud import post as crud_post
from app.crud import interaction as crud_interaction
from app.crud import notification as crud_notification
from app.models.interaction import InteractionType
from app.schemas.notification import NotificationCreate
from app.models.notification import NotificationType

router = APIRouter()

from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File, Request
from app.services.cloudinary_service import upload_image

from typing import List

@router.post("", response_model=CommunityPostResponse)
def create_post(
    request: Request,
    content: str = Form(...),
    location_tag: Optional[str] = Form(None),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a standalone community post with multiple images."""
    
    # Payload size check (20MB limit)
    content_length = request.headers.get('content-length')
    if content_length:
        try:
            if int(content_length) > 20 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="Payload too large. Maximum size is 20MB.")
        except ValueError:
            pass

    media_urls = []
    
    # Filter out empty files (FastAPI sometimes sends empty UploadFile objects when no file is selected)
    valid_images = [img for img in images if img.filename]
    
    for image in valid_images:
        url = upload_image(image)
        if url:
            media_urls.append(url)
            
    post_in = CommunityPostCreate(
        content=content,
        media_urls=media_urls if media_urls else None,
        location_tag=location_tag
    )
    post = crud_post.create_community_post(db=db, post_in=post_in, user_id=current_user.id)
    
    avatar_url = None
    if getattr(current_user, "profile", None):
        avatar_url = current_user.profile.avatar_url
        
    return {
        **post.__dict__,
        "author_name": current_user.username,
        "author_avatar": avatar_url,
        "upvotes": 0,
        "downvotes": 0,
        "comment_count": 0,
        "user_interaction": None,
        "report": None
    }


@router.get("/me", response_model=CommunityPostPaginatedResponse)
def get_my_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve community posts authored by the current user."""
    from app.crud import feed as crud_feed
    return crud_feed.get_feed_posts(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        author_id=current_user.id
    )

@router.get("/{post_id}", response_model=CommunityPostResponse)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    from app.crud import feed as crud_feed
    user_id = current_user.id if current_user else None
    post_data = crud_feed.get_feed_post(db, post_id, user_id=user_id)
    if not post_data:
        raise HTTPException(status_code=404, detail="Post not found")
    return post_data

@router.get("/", response_model=CommunityPostPaginatedResponse)
def get_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Retrieve all posts for the community feed."""
    # Note: crud_post.get_posts should probably compute upvotes, comments, etc.
    # For now, let's keep it simple.
    posts = crud_post.get_posts(db=db, skip=skip, limit=limit)
    return {"posts": posts, "total": len(posts), "has_more": False}


@router.post("/{post_id}/vote", response_model=Optional[PostInteraction])
def vote_post(
    post_id: int,
    interaction_in: PostInteractionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upvote or downvote a feed post."""
    if interaction_in.post_id != post_id:
        raise HTTPException(status_code=400, detail="Post ID mismatch")
        
    result = crud_interaction.toggle_interaction(
        db=db, 
        user_id=current_user.id, 
        interaction_in=interaction_in
    )
    
    # Notify author if upvoted
    if result and result.interaction_type == InteractionType.UPVOTE:
        post = crud_post.get_post(db, post_id=post_id)
        if post and post.user_id != current_user.id:
            crud_notification.create_notification(db, NotificationCreate(
                user_id=post.user_id,
                type=NotificationType.LIKE,
                message=f"Someone liked your post.",
                payload={"post_id": post_id, "actor_id": current_user.id}
            ))

    return result

@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = crud_post.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    crud_post.delete_post(db, post_id)
    return {"message": "Post deleted"}
