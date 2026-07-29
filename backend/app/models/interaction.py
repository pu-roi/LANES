from datetime import datetime
import enum
from sqlalchemy import Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InteractionType(str, enum.Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"


class PostInteraction(Base):
    """
    PostInteraction model for tracking upvotes and downvotes on community feed reports.
    """
    __tablename__ = "post_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id", ondelete="CASCADE"), index=True)
    interaction_type: Mapped[InteractionType] = mapped_column(Enum(InteractionType, native_enum=True, name="interactiontype_enum"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User")
    post: Mapped["CommunityPost"] = relationship("CommunityPost", back_populates="interactions")

class CommentInteraction(Base):
    """
    CommentInteraction model for tracking upvotes and downvotes on comments.
    """
    __tablename__ = "comment_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), index=True)
    interaction_type: Mapped[InteractionType] = mapped_column(Enum(InteractionType, native_enum=True, name="interactiontype_enum"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User")
    comment: Mapped["Comment"] = relationship("Comment", back_populates="interactions")
