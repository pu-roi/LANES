from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate

def create_notification(db: Session, notification_in: NotificationCreate, *, commit: bool = True) -> Notification:
    db_notification = Notification(
        user_id=notification_in.user_id,
        type=notification_in.type,
        message=notification_in.message,
        payload=notification_in.payload
    )
    db.add(db_notification)
    if commit:
        db.commit()
        db.refresh(db_notification)
    return db_notification

def get_notifications(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

def get_unread_count(db: Session, user_id: int):
    return db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).count()

def mark_as_read(db: Session, notification_id: int, user_id: int) -> Notification | None:
    db_notif = db.query(Notification).filter(
        Notification.id == notification_id, Notification.user_id == user_id,
    ).first()
    if db_notif:
        db_notif.is_read = True
        db.commit()
        db.refresh(db_notif)
    return db_notif

def mark_all_as_read(db: Session, user_id: int):
    db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).update({"is_read": True})
    db.commit()
    return True
