from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import Integer, String, DateTime, ForeignKey, Text, UniqueConstraint
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
    hidden_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    hidden_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    deleted_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    hidden_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[hidden_by_user_id])
    deleted_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[deleted_by_user_id])
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
    edit_history: Mapped[List["CommunityPostEditHistory"]] = relationship(
        "CommunityPostEditHistory",
        back_populates="post",
        cascade="all, delete-orphan",
        order_by="CommunityPostEditHistory.version",
    )


class CommunityPostEditHistory(Base):
    """Immutable before/after snapshots for a Community Feed post edit."""
    __tablename__ = "community_post_edit_history"
    __table_args__ = (UniqueConstraint("post_id", "version", name="uq_community_post_edit_history_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id", ondelete="CASCADE"), index=True)
    editor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_content: Mapped[str] = mapped_column(Text, nullable=False)
    previous_media_urls: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    previous_location_tag: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    previous_location_lat: Mapped[Optional[float]] = mapped_column(nullable=True)
    previous_location_lng: Mapped[Optional[float]] = mapped_column(nullable=True)
    updated_content: Mapped[str] = mapped_column(Text, nullable=False)
    updated_media_urls: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    updated_location_tag: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_location_lat: Mapped[Optional[float]] = mapped_column(nullable=True)
    updated_location_lng: Mapped[Optional[float]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    post: Mapped["CommunityPost"] = relationship("CommunityPost", back_populates="edit_history")
    editor: Mapped["User"] = relationship("User")


class CommunityPostReport(Base):
    __tablename__ = "community_post_reports"
    __table_args__ = (UniqueConstraint("post_id", "reporter_user_id", "status", name="uq_open_community_post_report"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id", ondelete="CASCADE"), index=True)
    reporter_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    reason: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    resolution_action: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    resolved_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
