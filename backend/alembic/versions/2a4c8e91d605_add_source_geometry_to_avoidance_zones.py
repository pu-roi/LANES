"""Add original road geometry to avoidance zones.

Revision ID: 2a4c8e91d605
Revises: 33ec62de236d
Create Date: 2026-09-10 11:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry


revision: str = "2a4c8e91d605"
down_revision: Union[str, Sequence[str], None] = "33ec62de236d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Persist the route centreline for standalone admin line zones."""
    op.add_column(
        "flood_avoidance_zones",
        sa.Column(
            "source_geometry",
            Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove the persisted route centreline."""
    op.drop_column("flood_avoidance_zones", "source_geometry")
