from datetime import date, datetime
from typing import Optional, Any
from sqlalchemy import Date, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuditLog(Base):
    """
    AuditLog model representing system activity audit trails.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    admin_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    action_type: Mapped[str] = mapped_column(String(50), index=True)
    target_table: Mapped[str] = mapped_column(String(50))
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    admin: Mapped[Optional["User"]] = relationship("User")

class VisitorCount(Base):
    """
    Simple model to track total site visitors for the landing page statistics.
    """
    __tablename__ = "visitor_counts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    total_visitors: Mapped[int] = mapped_column(Integer, default=0)


class VisitorDailyVisit(Base):
    """A privacy-preserving daily visitor record used for aggregate analytics."""
    __tablename__ = "visitor_daily_visits"
    __table_args__ = (
        UniqueConstraint("visit_date", "visitor_hash", name="uq_visitor_daily_visits_date_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # This is an HMAC of a browser-generated UUID, never the raw UUID or an IP address.
    visitor_hash: Mapped[str] = mapped_column(String(64), index=True)
    visit_date: Mapped[date] = mapped_column(Date, index=True)
    # When available, accounts are de-duplicated across devices in aggregate queries.
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
