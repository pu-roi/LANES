from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List
from sqlalchemy import String, Integer, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Role(Base):
    """
    Role model representing specific administrative permission configurations.
    """
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    # JSONB column to store permissions for each section (e.g. {"reports": "full", "zones": "view"})
    permissions: Mapped[Any] = mapped_column(JSON, default=dict)
    
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="role",
    )
