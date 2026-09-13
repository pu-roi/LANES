"""Add post moderation resolution and soft-hide fields.

Revision ID: d1f6e2a9b730
Revises: c8a3d1f9e426
"""
from alembic import op
import sqlalchemy as sa
revision = "d1f6e2a9b730"
down_revision = "c8a3d1f9e426"
branch_labels = None
depends_on = None
def upgrade():
    op.add_column("community_posts", sa.Column("hidden_at", sa.DateTime(), nullable=True))
    op.add_column("community_posts", sa.Column("hidden_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_community_posts_hidden_at", "community_posts", ["hidden_at"])
    op.add_column("community_post_reports", sa.Column("resolution_action", sa.String(20), nullable=True))
    op.add_column("community_post_reports", sa.Column("resolved_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.add_column("community_post_reports", sa.Column("resolved_at", sa.DateTime(), nullable=True))
def downgrade():
    op.drop_column("community_post_reports", "resolved_at"); op.drop_column("community_post_reports", "resolved_by_user_id"); op.drop_column("community_post_reports", "resolution_action"); op.drop_index("ix_community_posts_hidden_at", table_name="community_posts"); op.drop_column("community_posts", "hidden_by_user_id"); op.drop_column("community_posts", "hidden_at")
