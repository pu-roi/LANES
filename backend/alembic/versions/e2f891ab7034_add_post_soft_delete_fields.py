"""add post soft delete fields

Revision ID: e2f891ab7034
Revises: 4389876f4499
Create Date: 2026-09-18 18:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e2f891ab7034'
down_revision: Union[str, Sequence[str], None] = '4389876f4499'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('community_posts', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('community_posts', sa.Column('deleted_by_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.create_index('ix_community_posts_deleted_at', 'community_posts', ['deleted_at'])


def downgrade() -> None:
    op.drop_index('ix_community_posts_deleted_at', table_name='community_posts')
    op.drop_column('community_posts', 'deleted_by_user_id')
    op.drop_column('community_posts', 'deleted_at')
