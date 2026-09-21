"""add privacy preserving visitor analytics

Revision ID: c9f3e7a6b210
Revises: b8d4e1f5c902
Create Date: 2026-09-21 17:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9f3e7a6b210"
down_revision: Union[str, Sequence[str], None] = "b8d4e1f5c902"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "visitor_daily_visits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("visitor_hash", sa.String(length=64), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("visit_date", "visitor_hash", name="uq_visitor_daily_visits_date_hash"),
    )
    op.create_index("ix_visitor_daily_visits_visitor_hash", "visitor_daily_visits", ["visitor_hash"])
    op.create_index("ix_visitor_daily_visits_visit_date", "visitor_daily_visits", ["visit_date"])
    op.create_index("ix_visitor_daily_visits_user_id", "visitor_daily_visits", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_visitor_daily_visits_user_id", table_name="visitor_daily_visits")
    op.drop_index("ix_visitor_daily_visits_visit_date", table_name="visitor_daily_visits")
    op.drop_index("ix_visitor_daily_visits_visitor_hash", table_name="visitor_daily_visits")
    op.drop_table("visitor_daily_visits")
