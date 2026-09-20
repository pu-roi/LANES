"""normalize flood depth gauge values

Revision ID: b8d4e1f5c902
Revises: f4e7c2a9b6d1
Create Date: 2026-09-21 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "b8d4e1f5c902"
down_revision: Union[str, Sequence[str], None] = "f4e7c2a9b6d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Earlier public forms stored display labels while official-zone forms stored
    # gauge IDs. Normalize persisted values without changing their severity.
    for table, column in (
        ("flood_reports", "depth"),
        ("flood_avoidance_zones", "depth_override"),
        ("flood_events", "peak_depth"),
    ):
        op.execute(
            f"UPDATE {table} SET {column} = CASE lower(trim({column})) "
            "WHEN 'neck & above' THEN 'neck' "
            f"ELSE lower(trim({column})) END "
            f"WHERE {column} IS NOT NULL"
        )

    # Legacy report-created zones rely on computed values. Persist the existing
    # report values as explicit official overrides where an unambiguous source
    # report is available, so every current zone records a flood level itself.
    op.execute(
        "UPDATE flood_avoidance_zones AS zone "
        "SET severity_override = report.severity, depth_override = report.depth "
        "FROM flood_reports AS report "
        "WHERE report.zone_id = zone.id "
        "AND zone.severity_override IS NULL "
        "AND zone.depth_override IS NULL "
        "AND report.id = ("
        "  SELECT candidate.id FROM flood_reports AS candidate "
        "  WHERE candidate.zone_id = zone.id "
        "  ORDER BY candidate.created_at ASC, candidate.id ASC LIMIT 1"
        ")"
    )


def downgrade() -> None:
    # Canonical IDs are deliberately retained; converting them back would
    # reintroduce the ambiguous display/storage split.
    pass
