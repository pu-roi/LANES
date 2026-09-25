"""Durable RSS checkpoints and publisher article evidence."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
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
