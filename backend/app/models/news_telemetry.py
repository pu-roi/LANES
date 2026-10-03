"""Approved operational telemetry; never public flood or routing state."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.news import utc_now


class AttemptColumns:
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    correlation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), default=uuid4, unique=True)
    status: Mapped[str] = mapped_column(String(20), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(100))


def attempt_constraints() -> tuple[CheckConstraint, ...]:
    return (
        CheckConstraint("status IN ('running','completed','failed','interrupted')", name="attempt_status"),
        CheckConstraint("(status = 'running' AND finished_at IS NULL) OR (status <> 'running' AND finished_at IS NOT NULL)", name="finish_state"),
        CheckConstraint("finished_at IS NULL OR finished_at >= started_at", name="time_order"),
    )


class NewsDiscoveryRun(AttemptColumns, Base):
    __tablename__ = "news_discovery_runs"
    __table_args__ = (*attempt_constraints(),
        CheckConstraint("trigger IN ('staff','collector')", name="trigger_kind"),
        CheckConstraint("(trigger = 'staff' AND actor_id IS NOT NULL) OR (trigger = 'collector' AND actor_id IS NULL)", name="trigger_actor"))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    trigger: Mapped[str] = mapped_column(String(20))


class NewsDiscoveryFeedRun(Base):
    __tablename__ = "news_discovery_feed_runs"
    __table_args__ = (
        UniqueConstraint("discovery_run_id", "source_id", "feed_url", name="uq_news_discovery_feed_attempt"),
        CheckConstraint("entries_seen >= 0 AND candidates_saved >= 0 AND body_errors >= 0 AND scope_unresolved >= 0", name="nonnegative_counts"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    discovery_run_id: Mapped[int] = mapped_column(ForeignKey("news_discovery_runs.id", ondelete="RESTRICT"), index=True)
    source_id: Mapped[str] = mapped_column(String(100))
    feed_url: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30))
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(100))
    entries_seen: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    candidates_saved: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    body_errors: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    scope_unresolved: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class NewsFallbackLookup(AttemptColumns, Base):
    __tablename__ = "news_fallback_lookups"
    __table_args__ = (*attempt_constraints(),
        CheckConstraint("length(content_fingerprint) = 64", name="fingerprint_length"),
        CheckConstraint("retry_after_seconds IS NULL OR retry_after_seconds >= 0", name="nonnegative_retry"))
    article_id: Mapped[int] = mapped_column(ForeignKey("news_articles.id", ondelete="RESTRICT"), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    content_fingerprint: Mapped[str] = mapped_column(String(64))
    retrieve_articles: Mapped[bool] = mapped_column(Boolean)
    retry_after_seconds: Mapped[int | None] = mapped_column(Integer)


class NewsFallbackLookupLead(Base):
    __tablename__ = "news_fallback_lookup_leads"
    __table_args__ = (
        UniqueConstraint("lookup_id", "ordinal", name="uq_news_fallback_lead_ordinal"),
        CheckConstraint("ordinal >= 0", name="nonnegative_ordinal"),
        CheckConstraint("retrieval_status IN ('not_requested','retrieved','failed')", name="retrieval_status"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lookup_id: Mapped[int] = mapped_column(ForeignKey("news_fallback_lookups.id", ondelete="RESTRICT"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    article_url: Mapped[str] = mapped_column(Text)
    source_id: Mapped[str | None] = mapped_column(String(100))
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieval_status: Mapped[str] = mapped_column(String(20))
    error_code: Mapped[str | None] = mapped_column(String(100))
    assessment: Mapped[str | None] = mapped_column(String(100))
