"""Durable RSS checkpoints and publisher article evidence."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NewsFeedCheckpoint(Base):
    __tablename__ = "news_feed_checkpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    feed_url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    etag: Mapped[str | None] = mapped_column(Text)
    last_modified: Mapped[str | None] = mapped_column(Text)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    publisher_source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    article_text: Mapped[str | None] = mapped_column(Text)
    article_error: Mapped[str | None] = mapped_column(Text)
    content_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    review_state: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    feed_entries: Mapped[list["NewsArticleFeedEntry"]] = relationship(back_populates="article")


class NewsArticleFeedEntry(Base):
    __tablename__ = "news_article_feed_entries"
    __table_args__ = (
        UniqueConstraint("source_id", "feed_url", "feed_guid", name="uq_news_feed_entry_identity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    feed_url: Mapped[str] = mapped_column(Text, nullable=False)
    feed_guid: Mapped[str] = mapped_column(Text, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)
    article: Mapped[NewsArticle] = relationship(back_populates="feed_entries")


class NewsArticleVersion(Base):
    __tablename__ = "news_article_versions"
    __table_args__ = (
        UniqueConstraint("article_id", "input_fingerprint", name="uq_news_article_version_input"),
        CheckConstraint("length(input_fingerprint) = 64", name="input_hash_length"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("news_articles.id", ondelete="RESTRICT"), index=True)
    input_fingerprint: Mapped[str] = mapped_column(String(64))
    input_snapshot: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class NewsExtractionRun(Base):
    __tablename__ = "news_extraction_runs"
    __table_args__ = (
        UniqueConstraint("article_version_id", "pipeline_version", "mode", name="uq_news_extraction_run_identity"),
        CheckConstraint("mode = 'rules_only'", name="rules_only_mode"),
        CheckConstraint("status IN ('pending','processing','completed','retry_wait','failed')", name="processing_status"),
        CheckConstraint("attempt_count BETWEEN 0 AND 5", name="bounded_attempts"),
        CheckConstraint("(status = 'processing' AND lease_token IS NOT NULL AND lease_expires_at IS NOT NULL) OR "
                        "(status <> 'processing' AND lease_token IS NULL AND lease_expires_at IS NULL)", name="lease_state"),
        CheckConstraint("status <> 'completed' OR (result IS NOT NULL AND completed_at IS NOT NULL)", name="completed_result"),
        Index("ix_news_extraction_due", "status", "next_attempt_at", "lease_expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_version_id: Mapped[int] = mapped_column(ForeignKey("news_article_versions.id", ondelete="RESTRICT"), index=True)
    pipeline_version: Mapped[str] = mapped_column(String(100))
    mode: Mapped[str] = mapped_column(String(30), default="rules_only")
    status: Mapped[str] = mapped_column(String(30), default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_token: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(100))
    result: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
