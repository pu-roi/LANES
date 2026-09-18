from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File, Request, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user_optional, get_current_user
from app.models.user import User
from app.schemas.post import (
    CommunityPostCreate,
    CommunityPostUpdate,
    CommunityPostReportCreate,
    CommunityPostDeletePayload,
    CommunityPostEditHistoryResponse,
    CommunityPostResponse,
    CommunityPostPaginatedResponse,
)
from app.schemas.audit import AuditLogCreate
from app.models.post import CommunityPostReport
from app.schemas.interaction import PostInteractionCreate, PostInteraction
from app.crud import post as crud_post
from app.crud import interaction as crud_interaction
from app.crud import notification as crud_notification
from app.crud import audit as crud_audit
from app.crud.user import get_user_display_name
from app.models.interaction import InteractionType
from app.schemas.notification import NotificationCreate
from app.models.notification import NotificationType
from app.services.cloudinary_service import upload_image

router = APIRouter()


@router.post("", response_model=CommunityPostResponse)
def create_post(
    request: Request,
    content: str = Form(...),
    location_tag: Optional[str] = Form(None),
    location_lat: Optional[float] = Form(None),
    location_lng: Optional[float] = Form(None),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a standalone community post with multiple images."""
    
    # Payload size check (100MB limit for video and high-res photo uploads)
    content_length = request.headers.get('content-length')
    if content_length:
        try:
            if int(content_length) > 100 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="Payload too large. Maximum size is 100MB.")
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
        location_tag=location_tag,
        location_lat=location_lat,
        location_lng=location_lng
    )
    post = crud_post.create_community_post(db=db, post_in=post_in, user_id=current_user.id)
    
    from app.crud import feed as crud_feed
    post_data = crud_feed.get_feed_post(db, post.id, user_id=current_user.id)
    if post_data:
        return post_data

    avatar_url = None
    if getattr(current_user, "profile", None) and not getattr(current_user.profile, "hide_profile_picture", False):
        avatar_url = current_user.profile.avatar_url
        
    return {
        "id": post.id,
        "user_id": post.user_id,
        "content": post.content,
        "media_urls": post.media_urls,
        "location_tag": post.location_tag,
        "location_lat": post.location_lat,
        "location_lng": post.location_lng,
        "flood_report_id": post.flood_report_id,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "author_name": get_user_display_name(current_user),
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


@router.get("/{post_id}/history", response_model=List[CommunityPostEditHistoryResponse])
def get_post_history(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Return public before/after versions for an existing Community Post."""
    from app.crud import feed as crud_feed

    user_id = current_user.id if current_user else None
    if not crud_feed.get_feed_post(db, post_id, user_id=user_id):
        raise HTTPException(status_code=404, detail="Post not found")
    return crud_post.get_post_edit_history(db, post_id)


@router.patch("/{post_id}", response_model=CommunityPostResponse)
def update_post(
    post_id: int,
    post_in: CommunityPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a post owned by the authenticated author and record its history."""
    post = crud_post.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    updated_post = crud_post.update_community_post(db, post, post_in, current_user.id)
    from app.crud import feed as crud_feed
    return crud_feed.get_feed_post(db, updated_post.id, user_id=current_user.id)


@router.post("/{post_id}/reports", status_code=201)
def report_post(
    post_id: int,
    payload: CommunityPostReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if payload.reason not in {"spam_scam", "misinformation", "harassment_hate", "explicit_violent", "other"}:
        raise HTTPException(status_code=422, detail="Invalid report reason")
    if payload.reason == "other" and not (payload.details or "").strip():
        raise HTTPException(status_code=422, detail="Explain the report reason")
    post = crud_post.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id == current_user.id:
        raise HTTPException(status_code=403, detail="You cannot report your own post")
    if db.query(CommunityPostReport).filter_by(post_id=post_id, reporter_user_id=current_user.id, status="open").first():
        raise HTTPException(status_code=409, detail="You already have an open report for this post")
    db.add(CommunityPostReport(
        post_id=post_id,
        reporter_user_id=current_user.id,
        reason=payload.reason,
        details=payload.details.strip() if payload.details else None
    ))
    db.commit()
    return {"message": "Report submitted for moderator review"}


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
    from app.crud import feed as crud_feed
    user_id = current_user.id if current_user else None
    return crud_feed.get_feed_posts(
        db=db,
        user_id=user_id,
        skip=skip,
        limit=limit
    )


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
                message="Someone liked your post.",
                payload={"post_id": post_id, "actor_id": current_user.id}
            ))

    return result


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    request: Request,
    payload: Optional[CommunityPostDeletePayload] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = crud_post.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    role_name = current_user.role.name if getattr(current_user, "role", None) else ""
    is_admin = role_name in {"Super Admin", "DRRM Officer", "Moderator"}
    if post.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")

    author_user_id = post.user_id
    crud_post.delete_post(db, post_id=post_id, deleted_by_user_id=current_user.id)

    # When staff/admin removes another user's post, notify author and create audit log
    if is_admin and author_user_id != current_user.id:
        reason_label_map = {
            "misinformation": "Misinformation / False Hazard Report",
            "spam_scam": "Spam, Scam, or Advertising",
            "harassment_hate": "Harassment, Hate Speech, or Hostility",
            "explicit_violent": "Explicit, Graphic, or Violent Content",
            "duplicate_outdated": "Duplicate or Outdated / Resolved Hazard",
            "other": "Community Guidelines Violation",
        }
        raw_reason = payload.reason if payload and payload.reason else "other"
        formatted_reason = reason_label_map.get(raw_reason, raw_reason)
        details = payload.details.strip() if payload and payload.details else None

        message = f"Your Community Feed post was removed by an administrator: {formatted_reason}."
        if details:
            message += f" Note: {details}"

        # 1. In-app notification for the author
        crud_notification.create_notification(db, NotificationCreate(
            user_id=author_user_id,
            type=NotificationType.SYSTEM,
            message=message,
            payload={
                "post_id": post_id,
                "action": "post_removed_by_admin",
                "reason": formatted_reason,
                "details": details,
                "admin_id": current_user.id,
            }
        ))

        # 2. Audit log entry for administrator accountability
        client_ip = request.client.host if request.client else None
        crud_audit.create_audit_log(
            db,
            audit_in=AuditLogCreate(
                admin_id=current_user.id,
                action_type="ADMIN_DELETE_POST",
                target_table="community_posts",
                target_id=post_id,
                metadata_json={
                    "post_id": post_id,
                    "author_id": author_user_id,
                    "reason": formatted_reason,
                    "details": details,
                },
                ip_address=client_ip,
            )
        )

    # 3. Real-time SSE broadcast so clients update live
    from app.core.sse import manager
    await manager.broadcast({
        "event": "feed_post_deleted",
        "data": {"post_id": post_id}
    })

    return {"message": "Post deleted", "id": post_id}
