"""Add community post reports.

Revision ID: c8a3d1f9e426
Revises: b4c2d91e7a30
"""
from alembic import op
import sqlalchemy as sa
revision = "c8a3d1f9e426"
down_revision = "b4c2d91e7a30"
branch_labels = None
depends_on = None
def upgrade():
    op.create_table("community_post_reports", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("post_id", sa.Integer(), sa.ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False), sa.Column("reporter_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("reason", sa.String(50), nullable=False), sa.Column("details", sa.Text()), sa.Column("status", sa.String(20), nullable=False, server_default="open"), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")), sa.UniqueConstraint("post_id", "reporter_user_id", "status", name="uq_open_community_post_report"))
    op.create_index("ix_community_post_reports_post_id", "community_post_reports", ["post_id"])
def downgrade():
    op.drop_index("ix_community_post_reports_post_id", table_name="community_post_reports"); op.drop_table("community_post_reports")
