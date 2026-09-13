"""Add immutable Community Post edit history.

Revision ID: b4c2d91e7a30
Revises: 0d5f7a6b4c11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b4c2d91e7a30"
down_revision: Union[str, Sequence[str], None] = "0d5f7a6b4c11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "community_post_edit_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("editor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("previous_content", sa.Text(), nullable=False),
        sa.Column("previous_media_urls", postgresql.JSONB(), nullable=True),
        sa.Column("previous_location_tag", sa.String(length=255), nullable=True),
        sa.Column("previous_location_lat", sa.Float(), nullable=True),
        sa.Column("previous_location_lng", sa.Float(), nullable=True),
        sa.Column("updated_content", sa.Text(), nullable=False),
        sa.Column("updated_media_urls", postgresql.JSONB(), nullable=True),
        sa.Column("updated_location_tag", sa.String(length=255), nullable=True),
        sa.Column("updated_location_lat", sa.Float(), nullable=True),
        sa.Column("updated_location_lng", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("post_id", "version", name="uq_community_post_edit_history_version"),
    )
    op.create_index("ix_community_post_edit_history_post_id", "community_post_edit_history", ["post_id"])
    op.create_index("ix_community_post_edit_history_editor_user_id", "community_post_edit_history", ["editor_user_id"])


def downgrade() -> None:
    op.drop_index("ix_community_post_edit_history_editor_user_id", table_name="community_post_edit_history")
    op.drop_index("ix_community_post_edit_history_post_id", table_name="community_post_edit_history")
    op.drop_table("community_post_edit_history")
