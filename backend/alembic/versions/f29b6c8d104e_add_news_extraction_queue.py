"""Add approved immutable article inputs and durable rules extraction queue.

Revision ID: f29b6c8d104e
Revises: a83c1d4e7b92
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f29b6c8d104e"
down_revision = "a83c1d4e7b92"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_article_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("input_fingerprint", sa.String(64), nullable=False),
        sa.Column("input_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("article_id", "input_fingerprint", name="uq_news_article_version_input"),
        sa.CheckConstraint("length(input_fingerprint) = 64", name=op.f("ck_news_article_versions_input_hash_length")),
    )
    op.create_index("ix_news_article_versions_article_id", "news_article_versions", ["article_id"])
    op.create_table(
        "news_extraction_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("article_version_id", sa.Integer(), sa.ForeignKey("news_article_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("pipeline_version", sa.String(100), nullable=False),
        sa.Column("mode", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("lease_token", postgresql.UUID(as_uuid=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(100)),
        sa.Column("result", postgresql.JSONB(none_as_null=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("article_version_id", "pipeline_version", "mode", name="uq_news_extraction_run_identity"),
        sa.CheckConstraint("mode = 'rules_only'", name=op.f("ck_news_extraction_runs_rules_only_mode")),
        sa.CheckConstraint("status IN ('pending','processing','completed','retry_wait','failed')", name=op.f("ck_news_extraction_runs_processing_status")),
        sa.CheckConstraint("attempt_count BETWEEN 0 AND 5", name=op.f("ck_news_extraction_runs_bounded_attempts")),
        sa.CheckConstraint("(status = 'processing' AND lease_token IS NOT NULL AND lease_expires_at IS NOT NULL) OR "
                           "(status <> 'processing' AND lease_token IS NULL AND lease_expires_at IS NULL)", name=op.f("ck_news_extraction_runs_lease_state")),
        sa.CheckConstraint("status <> 'completed' OR (result IS NOT NULL AND completed_at IS NOT NULL)", name=op.f("ck_news_extraction_runs_completed_result")),
    )
    op.create_index("ix_news_extraction_runs_article_version_id", "news_extraction_runs", ["article_version_id"])
    op.create_index("ix_news_extraction_due", "news_extraction_runs", ["status", "next_attempt_at", "lease_expires_at"])
    op.execute("""CREATE FUNCTION reject_news_version_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN RAISE EXCEPTION 'News article versions are immutable'; END; $$""")
    op.execute("""CREATE TRIGGER news_article_version_immutable BEFORE UPDATE ON news_article_versions
                  FOR EACH ROW EXECUTE FUNCTION reject_news_version_update()""")


def downgrade() -> None:
    op.drop_table("news_extraction_runs")
    op.drop_table("news_article_versions")
    op.execute("DROP FUNCTION reject_news_version_update()")
