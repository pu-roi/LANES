"""Allow the separately approved native NER extraction mode; no backfill/activation.

Revision ID: e8a6f1c2d903
Revises: d7e4b9a21c60
"""
from alembic import op

revision = "e8a6f1c2d903"
down_revision = "d7e4b9a21c60"
branch_labels = None
depends_on = None

TABLE = "news_extraction_runs"
CONSTRAINT = "ck_news_extraction_runs_rules_only_mode"
# PostgreSQL's non-pretty canonical expressions for the unchanged varchar column.
# Refuse unexpected definitions rather than guessing how to migrate schema drift.
LEGACY_EXPRESSION = "((mode)::text = 'rules_only'::text)"
NATIVE_EXPRESSION = (
    "((mode)::text = ANY ((ARRAY['rules_only'::character varying, "
    "'ner_rules_v1'::character varying])::text[]))"
)


def _assert_constraint(expected: str) -> None:
    literal = expected.replace("'", "''")
    op.execute(f"""DO $news_ner_mode$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = '{TABLE}'::regclass
              AND c.conname = '{CONSTRAINT}' AND c.contype = 'c'
              AND c.convalidated AND c.conislocal AND NOT c.connoinherit
              AND c.conkey = ARRAY[
                  (SELECT attnum FROM pg_attribute
                   WHERE attrelid = '{TABLE}'::regclass AND attname = 'mode' AND NOT attisdropped)
              ]::smallint[]
              AND pg_get_expr(c.conbin, c.conrelid, false) = '{literal}'
        ) THEN
            RAISE EXCEPTION 'news_extraction_mode_constraint_drift: expected named validated mode check'
                USING ERRCODE = '23514';
        END IF;
    END;
    $news_ner_mode$""")


def _require_legacy_rows(operation: str) -> None:
    # The exclusive lock is already held. SQL guard also survives offline output.
    op.execute(f"""DO $news_ner_rows$
    BEGIN
        IF EXISTS (SELECT 1 FROM {TABLE} WHERE mode IS DISTINCT FROM 'rules_only') THEN
            RAISE EXCEPTION 'Cannot {operation} news extraction modes: non-rules-only rows exist; preserve NER history'
                USING ERRCODE = '23514';
        END IF;
    END;
    $news_ner_rows$""")


def upgrade() -> None:
    op.execute(f"LOCK TABLE {TABLE} IN ACCESS EXCLUSIVE MODE")
    _assert_constraint(LEGACY_EXPRESSION)
    _require_legacy_rows("upgrade")
    op.drop_constraint(op.f(CONSTRAINT), TABLE, type_="check")
    op.create_check_constraint(op.f(CONSTRAINT), TABLE, "mode IN ('rules_only', 'ner_rules_v1')")


def downgrade() -> None:
    op.execute(f"LOCK TABLE {TABLE} IN ACCESS EXCLUSIVE MODE")
    _assert_constraint(NATIVE_EXPRESSION)
    _require_legacy_rows("downgrade")
    op.drop_constraint(op.f(CONSTRAINT), TABLE, type_="check")
    op.create_check_constraint(op.f(CONSTRAINT), TABLE, "mode = 'rules_only'")
