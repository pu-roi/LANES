"""add hide_profile_picture to profile

Revision ID: 4389876f4499
Revises: d1f6e2a9b730
Create Date: 2026-09-17 21:39:41.327029

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4389876f4499'
down_revision: Union[str, Sequence[str], None] = 'd1f6e2a9b730'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('profiles', sa.Column('hide_profile_picture', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('profiles', 'hide_profile_picture')
