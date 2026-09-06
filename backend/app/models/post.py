from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CommunityPost(Base):
    """
    CommunityPost model for the community feed.
    Can be a standalone post, or a shared flood report.
    """
    __tablename__ = "community_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    flood_report_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("flood_reports.id", ondelete="CASCADE"), 
        nullable=True, 
        index=True
    )
    content: Mapped[str] = mapped_column(Text)
    media_urls: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    location_tag: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location_lat: Mapped[Optional[float]] = mapped_column(nullable=True)
    location_lng: Mapped[Optional[float]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User")
    report: Mapped[Optional["FloodReport"]] = relationship("FloodReport", back_populates="community_post")
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan"
    )
    interactions: Mapped[List["PostInteraction"]] = relationship(
        "PostInteraction",
        back_populates="post",
        cascade="all, delete-orphan"
    )
