"""migrate all timestamps to timestamptz

Revision ID: e7f2b3c9a014
Revises: c9f3e7a6b210
Create Date: 2026-09-22 11:43:00.000000

Converts every TIMESTAMP WITHOUT TIME ZONE column to TIMESTAMP WITH TIME ZONE.
Existing data is already stored in UTC, so PostgreSQL's AT TIME ZONE 'UTC' cast
is used to attach the timezone label without shifting any values.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7f2b3c9a014"
down_revision: Union[str, Sequence[str], None] = "c9f3e7a6b210"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_timestamptz(table: str, columns: list[str]) -> None:
    """ALTER each column from TIMESTAMP to TIMESTAMPTZ, preserving UTC values."""
    for col in columns:
        op.execute(
            f"ALTER TABLE {table} "
            f"ALTER COLUMN {col} TYPE TIMESTAMPTZ "
            f"USING {col} AT TIME ZONE 'UTC';"
        )


def _to_timestamp(table: str, columns: list[str]) -> None:
    """Revert each column from TIMESTAMPTZ back to plain TIMESTAMP (downgrade)."""
    for col in columns:
        op.execute(
            f"ALTER TABLE {table} "
            f"ALTER COLUMN {col} TYPE TIMESTAMP "
            f"USING {col} AT TIME ZONE 'UTC';"
        )


# ---------------------------------------------------------------------------
# Table → column mapping (upgrade only touches non-nullable check inline)
# ---------------------------------------------------------------------------

TABLES: dict[str, list[str]] = {
    "users": ["created_at", "deleted_at"],
    "roles": ["created_at"],
    "profiles": ["updated_at"],
    "saved_places": ["created_at"],
    "otp_verifications": ["expires_at", "created_at"],
    "notifications": ["created_at"],
    "audit_logs": ["created_at"],
    "visitor_daily_visits": ["first_seen_at", "last_seen_at"],
    "community_posts": [
        "created_at", "updated_at", "hidden_at", "deleted_at",
    ],
    "community_post_edit_history": ["created_at"],
    "community_post_reports": ["resolved_at", "created_at"],
    "comments": ["created_at", "edited_at"],
    "post_interactions": ["created_at"],
    "comment_interactions": ["created_at"],
    "flood_events": [
        "first_reported_at", "verified_at", "ended_at",
        "created_at", "updated_at",
    ],
    "flood_reports": [
        "created_at", "updated_at", "deleted_at", "approved_at",
    ],
    "flood_avoidance_zones": [
        "created_at", "updated_at", "expires_at",
    ],
    "flood_event_locations": ["created_at", "updated_at"],
    "flood_report_moderation_outcomes": ["acted_at"],
    "flood_event_timeline_entries": ["occurred_at"],
}


def upgrade() -> None:
    for table, columns in TABLES.items():
        _to_timestamptz(table, columns)


def downgrade() -> None:
    for table, columns in TABLES.items():
        _to_timestamp(table, columns)
