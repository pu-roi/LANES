"""Approved F4b discovery/fallback telemetry, without historical backfill."""
from alembic import op
import sqlalchemy as sa

revision = "c5a7e9d2104f"
down_revision = "f29b6c8d104e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("news_discovery_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("correlation_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(100)),
        sa.CheckConstraint("status IN ('running','completed','failed','interrupted')", name="attempt_status"),
        sa.CheckConstraint("(status = 'running' AND finished_at IS NULL) OR (status <> 'running' AND finished_at IS NOT NULL)", name="finish_state"),
        sa.CheckConstraint("finished_at IS NULL OR finished_at >= started_at", name="time_order"),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("trigger", sa.String(20), nullable=False),
        sa.CheckConstraint("trigger IN ('staff','collector')", name="trigger_kind"),
        sa.CheckConstraint("(trigger = 'staff' AND actor_id IS NOT NULL) OR (trigger = 'collector' AND actor_id IS NULL)", name="trigger_actor"),
    )
    op.create_index("ix_news_discovery_runs_started_at", "news_discovery_runs", ["started_at"])
    op.create_table("news_discovery_feed_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("discovery_run_id", sa.Integer(), sa.ForeignKey("news_discovery_runs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_id", sa.String(100), nullable=False),
        sa.Column("feed_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("entries_seen", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("candidates_saved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("body_errors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scope_unresolved", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("discovery_run_id", "source_id", "feed_url", name="uq_news_discovery_feed_attempt"),
        sa.CheckConstraint("entries_seen >= 0 AND candidates_saved >= 0 AND body_errors >= 0 AND scope_unresolved >= 0", name="nonnegative_counts"),
    )
    op.create_index("ix_news_discovery_feed_runs_discovery_run_id", "news_discovery_feed_runs", ["discovery_run_id"])
    op.create_table("news_fallback_lookups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("correlation_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(100)),
        sa.CheckConstraint("status IN ('running','completed','failed','interrupted')", name="attempt_status"),
        sa.CheckConstraint("(status = 'running' AND finished_at IS NULL) OR (status <> 'running' AND finished_at IS NOT NULL)", name="finish_state"),
        sa.CheckConstraint("finished_at IS NULL OR finished_at >= started_at", name="time_order"),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("content_fingerprint", sa.String(64), nullable=False),
        sa.Column("retrieve_articles", sa.Boolean(), nullable=False),
        sa.Column("retry_after_seconds", sa.Integer()),
        sa.CheckConstraint("length(content_fingerprint) = 64", name="fingerprint_length"),
        sa.CheckConstraint("retry_after_seconds IS NULL OR retry_after_seconds >= 0", name="nonnegative_retry"),
    )
    op.create_index("ix_news_fallback_lookups_started_at", "news_fallback_lookups", ["started_at"])
    op.create_index("ix_news_fallback_lookups_article_id", "news_fallback_lookups", ["article_id"])
    op.create_table("news_fallback_lookup_leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lookup_id", sa.Integer(), sa.ForeignKey("news_fallback_lookups.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("article_url", sa.Text(), nullable=False),
        sa.Column("source_id", sa.String(100), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True)),
        sa.Column("retrieval_status", sa.String(20), nullable=False),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("assessment", sa.String(100), nullable=True),
        sa.UniqueConstraint("lookup_id", "ordinal", name="uq_news_fallback_lead_ordinal"),
        sa.CheckConstraint("ordinal >= 0", name="nonnegative_ordinal"),
        sa.CheckConstraint("retrieval_status IN ('not_requested','retrieved','failed')", name="retrieval_status"),
    )
    op.create_index("ix_news_fallback_lookup_leads_lookup_id", "news_fallback_lookup_leads", ["lookup_id"])


def downgrade() -> None:
    op.drop_table("news_fallback_lookup_leads")
    op.drop_table("news_fallback_lookups")
    op.drop_table("news_discovery_feed_runs")
    op.drop_table("news_discovery_runs")
