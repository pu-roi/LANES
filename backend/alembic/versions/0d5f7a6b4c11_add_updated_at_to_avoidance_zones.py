"""Add zone update timestamp for collaborative edit drafts.

Revision ID: 0d5f7a6b4c11
Revises: 2a4c8e91d605
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0d5f7a6b4c11"
down_revision: Union[str, Sequence[str], None] = "2a4c8e91d605"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "flood_avoidance_zones",
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    op.drop_column("flood_avoidance_zones", "updated_at")
