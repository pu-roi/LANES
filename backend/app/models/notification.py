from datetime import datetime, timezone
from typing import Optional, Any
import enum
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NotificationType(str, enum.Enum):
    LIKE = "LIKE"
    COMMENT = "COMMENT"
    SYSTEM = "SYSTEM"


class Notification(Base):
    """
    Notification model for in-app alerts.
    """
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]))
    message: Mapped[str] = mapped_column(String(255))
    payload: Mapped[Any] = mapped_column(JSONB, nullable=False, default=dict)
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User")
