from datetime import datetime, date
from sqlalchemy import String, Integer, DateTime, Date, ForeignKey, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Profile(Base):
    """
    Profile model for storing personal and contact details of users.
    """
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    middle_initial: Mapped[str | None] = mapped_column(String(10), nullable=True)
    suffix: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contact_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    birthdate: Mapped[date | None] = mapped_column(Date, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # UI Preferences & Privacy
    cover_color: Mapped[str] = mapped_column(String(20), default="#3B82F6")
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    display_full_name: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Community Trust Metrics
    trust_score: Mapped[int] = mapped_column(Integer, default=50)
    reports_submitted: Mapped[int] = mapped_column(Integer, default=0)
    reports_approved: Mapped[int] = mapped_column(Integer, default=0)
    reports_rejected: Mapped[int] = mapped_column(Integer, default=0)
    accuracy_rate: Mapped[float] = mapped_column(Float, default=0.0)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")
    address: Mapped["Address"] = relationship("Address", back_populates="profile", uselist=False, cascade="all, delete-orphan")
