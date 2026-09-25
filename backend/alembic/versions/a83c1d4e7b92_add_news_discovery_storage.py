"""add durable RSS discovery storage

Revision ID: a83c1d4e7b92
Revises: e7f2b3c9a014
Create Date: 2026-09-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a83c1d4e7b92"
down_revision = "e7f2b3c9a014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_feed_checkpoints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("feed_url", sa.Text(), nullable=False, unique=True),
        sa.Column("etag", sa.Text()),
        sa.Column("last_modified", sa.Text()),
        sa.Column("last_checked_at", sa.DateTime(timezone=True)),
        sa.Column("last_success_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
    )
    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("canonical_url", sa.Text(), nullable=False, unique=True),
        sa.Column("publisher_source_id", sa.String(length=100), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("fetched_at", sa.DateTime(timezone=True)),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("article_text", sa.Text()),
        sa.Column("article_error", sa.Text()),
        sa.Column("content_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("review_state", sa.String(length=30), nullable=False),
    )
    op.create_table(
        "news_article_feed_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("feed_url", sa.Text(), nullable=False),
        sa.Column("feed_guid", sa.Text(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_metadata", postgresql.JSONB()),
        sa.UniqueConstraint("source_id", "feed_url", "feed_guid", name="uq_news_feed_entry_identity"),
    )
    op.create_index("ix_news_article_feed_entries_article_id", "news_article_feed_entries", ["article_id"])


def downgrade() -> None:
    op.drop_index("ix_news_article_feed_entries_article_id", table_name="news_article_feed_entries")
    op.drop_table("news_article_feed_entries")
    op.drop_table("news_articles")
    op.drop_table("news_feed_checkpoints")
