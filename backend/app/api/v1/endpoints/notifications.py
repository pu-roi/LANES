from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationPaginatedResponse, NotificationResponse
from app.crud import notification as crud_notification

router = APIRouter()

@router.get("", response_model=NotificationPaginatedResponse)
def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve the current user's notifications."""
    notifs = crud_notification.get_notifications(db=db, user_id=current_user.id, skip=skip, limit=limit)
    unread_count = crud_notification.get_unread_count(db=db, user_id=current_user.id)
    return {
        "notifications": notifs,
        "total": len(notifs), # To fix: full count
        "unread_count": unread_count,
        "has_more": False
    }

@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notif = crud_notification.mark_as_read(db, notification_id)
    if not notif or notif.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif

@router.post("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    crud_notification.mark_all_as_read(db, current_user.id)
    return {"message": "All notifications marked as read"}
