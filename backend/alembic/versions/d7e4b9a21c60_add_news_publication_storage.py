"""Approved five-table news publication storage; no backfill or activation.

Revision ID: d7e4b9a21c60
Revises: c5a7e9d2104f
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d7e4b9a21c60"
down_revision = "c5a7e9d2104f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("news_claim_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("revision >= 0", name="nonnegative_revision"),
    )
    op.create_table("news_claim_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("news_claim_cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("extraction_run_id", sa.Integer(), sa.ForeignKey("news_extraction_runs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("claim_ordinal", sa.Integer(), nullable=False),
        sa.Column("claim_sha256", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("extraction_run_id", "claim_ordinal", name="uq_news_claim_source_identity"),
        sa.CheckConstraint("claim_ordinal >= 0", name="nonnegative_ordinal"),
        sa.CheckConstraint("claim_sha256 ~ '^[0-9a-f]{64}$'", name="claim_hash"),
    )
    op.create_index("ix_news_claim_sources_case_id", "news_claim_sources", ["case_id"])
    op.create_index("ix_news_claim_sources_extraction_run_id", "news_claim_sources", ["extraction_run_id"])
    op.create_table("news_claim_evaluations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("claim_source_id", sa.Integer(), sa.ForeignKey("news_claim_sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("policy_fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("lease_token", postgresql.UUID(as_uuid=True)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(100)),
        sa.Column("result", postgresql.JSONB(none_as_null=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("claim_source_id", "policy_fingerprint", name="uq_news_claim_evaluation_identity"),
        sa.CheckConstraint("policy_fingerprint ~ '^[0-9a-f]{64}$'", name="policy_hash"),
        sa.CheckConstraint("status IN ('pending','processing','completed','retry_wait','failed')", name="evaluation_status"),
        sa.CheckConstraint("attempt_count BETWEEN 0 AND 5", name="bounded_attempts"),
        sa.CheckConstraint("(status = 'processing' AND lease_token IS NOT NULL AND lease_expires_at IS NOT NULL) OR "
                           "(status <> 'processing' AND lease_token IS NULL AND lease_expires_at IS NULL)", name="lease_state"),
        sa.CheckConstraint("status <> 'completed' OR (result IS NOT NULL AND completed_at IS NOT NULL)", name="completed_result"),
        sa.CheckConstraint("status <> 'failed' OR (error_code IS NOT NULL AND completed_at IS NOT NULL)", name="failed_result"),
        sa.CheckConstraint("status <> 'retry_wait' OR (next_attempt_at IS NOT NULL AND error_code IS NOT NULL)", name="retry_state"),
        sa.CheckConstraint("error_code IS NULL OR error_code ~ '^[a-z][a-z0-9_]{0,99}$'", name="safe_error_code"),
        sa.CheckConstraint("result IS NULL OR jsonb_typeof(result) = 'object'", name="result_object"),
    )
    op.create_index("ix_news_claim_evaluations_claim_source_id", "news_claim_evaluations", ["claim_source_id"])
    op.create_index("ix_news_claim_evaluation_due", "news_claim_evaluations", ["status", "next_attempt_at", "lease_expires_at"])
    op.create_table("news_claim_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("news_claim_cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evaluation_id", sa.Integer(), sa.ForeignKey("news_claim_evaluations.id", ondelete="RESTRICT")),
        sa.Column("actor_kind", sa.String(20), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("operation", sa.String(20), nullable=False),
        sa.Column("public_state", sa.String(20), nullable=False),
        sa.Column("review_state", sa.String(20), nullable=False),
        sa.Column("reason_code", sa.String(100), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("case_id", "revision", name="uq_news_claim_decision_revision"),
        sa.UniqueConstraint("request_id", name="uq_news_claim_decision_request"),
        sa.CheckConstraint("revision > 0", name="positive_revision"),
        sa.CheckConstraint("actor_kind IN ('automatic','staff','maintenance')", name="actor_kind"),
        sa.CheckConstraint("(actor_kind = 'staff' AND actor_user_id IS NOT NULL) OR "
                           "(actor_kind IN ('automatic','maintenance') AND actor_user_id IS NULL)", name="actor_identity"),
        sa.CheckConstraint("operation IN ('evaluate','correct','defer','reject','reopen','clear','expire')", name="operation"),
        sa.CheckConstraint("public_state IN ('unpublished','active_alert','active_zone','withdrawn','expired')", name="public_state"),
        sa.CheckConstraint("review_state IN ('needs_review','deferred','resolved')", name="review_state"),
        sa.CheckConstraint("reason_code ~ '^[a-z][a-z0-9_]{0,99}$'", name="safe_reason_code"),
        sa.CheckConstraint("jsonb_typeof(snapshot) = 'object' AND octet_length(snapshot::text) <= 65536", name="bounded_snapshot"),
        sa.CheckConstraint("public_state NOT IN ('active_alert','active_zone') OR "
                           "(observed_at IS NOT NULL AND expires_at IS NOT NULL AND expires_at > observed_at)", name="active_expiry"),
        sa.CheckConstraint("actor_kind <> 'automatic' OR operation <> 'evaluate' OR evaluation_id IS NOT NULL", name="automatic_evaluation"),
        sa.CheckConstraint("operation NOT IN ('reject','clear','expire') OR public_state NOT IN ('active_alert','active_zone')", name="inactive_operation"),
    )
    op.create_index("ix_news_claim_decisions_case_id", "news_claim_decisions", ["case_id"])
    op.create_index("ix_news_claim_decision_public_expiry", "news_claim_decisions", ["public_state", "expires_at"])
    op.create_table("news_claim_zone_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("decision_id", sa.Integer(), sa.ForeignKey("news_claim_decisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("zone_id", sa.Integer(), sa.ForeignKey("flood_avoidance_zones.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("relation", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("decision_id", "zone_id", name="uq_news_claim_zone_link"),
        sa.CheckConstraint("relation IN ('created','supported')", name="link_relation"),
    )
    op.create_index("ix_news_claim_zone_links_decision_id", "news_claim_zone_links", ["decision_id"])
    op.create_index("ix_news_claim_zone_links_zone_id", "news_claim_zone_links", ["zone_id"])
    op.create_index("uq_news_claim_zone_creation_owner", "news_claim_zone_links", ["zone_id"],
                    unique=True, postgresql_where=sa.text("relation = 'created'"))

    op.execute("""CREATE FUNCTION reject_news_publication_change() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        RAISE EXCEPTION 'News publication history is immutable: %', TG_TABLE_NAME USING ERRCODE = '23514';
    END; $$""")
    for table in ("news_claim_sources", "news_claim_decisions", "news_claim_zone_links"):
        op.execute(f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} "
                   "FOR EACH ROW EXECUTE FUNCTION reject_news_publication_change()")
    op.execute("""CREATE TRIGGER news_claim_evaluations_finalized BEFORE UPDATE OR DELETE ON news_claim_evaluations
        FOR EACH ROW WHEN (OLD.status IN ('completed', 'failed'))
        EXECUTE FUNCTION reject_news_publication_change()""")
    for table in ("news_claim_sources", "news_claim_evaluations", "news_claim_decisions", "news_claim_zone_links"):
        op.execute(f"CREATE TRIGGER {table}_no_truncate BEFORE TRUNCATE ON {table} "
                   "FOR EACH STATEMENT EXECUTE FUNCTION reject_news_publication_change()")

    op.execute("""CREATE FUNCTION check_news_automatic_evaluation() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.actor_kind = 'automatic' AND NEW.operation = 'evaluate' THEN
            PERFORM id FROM news_claim_evaluations WHERE id = NEW.evaluation_id AND status = 'completed' FOR SHARE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'Automatic evaluation requires a completed audit' USING ERRCODE = '23514';
            END IF;
        END IF;
        RETURN NEW;
    END; $$""")
    op.execute("""CREATE TRIGGER news_claim_decision_completed_audit BEFORE INSERT ON news_claim_decisions
        FOR EACH ROW EXECUTE FUNCTION check_news_automatic_evaluation()""")
    op.execute("""CREATE FUNCTION check_news_zone_link_decision() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        PERFORM id FROM news_claim_decisions WHERE id = NEW.decision_id AND public_state = 'active_zone' FOR SHARE;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Zone links require an active-zone decision' USING ERRCODE = '23514';
        END IF;
        RETURN NEW;
    END; $$""")
    op.execute("""CREATE TRIGGER news_claim_zone_link_state BEFORE INSERT ON news_claim_zone_links
        FOR EACH ROW EXECUTE FUNCTION check_news_zone_link_decision()""")


def downgrade() -> None:
    # Explicit destructive downgrade affects only the new publication records.
    # Release rollback should disable publication and preserve this history.
    for table in ("news_claim_zone_links", "news_claim_decisions", "news_claim_evaluations", "news_claim_sources", "news_claim_cases"):
        op.drop_table(table)
    op.execute("DROP FUNCTION check_news_zone_link_decision()")
    op.execute("DROP FUNCTION check_news_automatic_evaluation()")
    op.execute("DROP FUNCTION reject_news_publication_change()")
