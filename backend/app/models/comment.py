from datetime import datetime
from typing import Optional, List
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Comment(Base):
    """
    Comment model for user replies on community feed reports.
    """
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(String(250))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    upvotes: Mapped[int] = mapped_column(Integer, default=0)
    downvotes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    pinned_by: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    post: Mapped["CommunityPost"] = relationship("CommunityPost", back_populates="comments")
    parent: Mapped[Optional["Comment"]] = relationship("Comment", remote_side=[id], back_populates="replies")
    replies: Mapped[List["Comment"]] = relationship("Comment", back_populates="parent")
    interactions: Mapped[List["CommentInteraction"]] = relationship("CommentInteraction", back_populates="comment", cascade="all, delete-orphan")
