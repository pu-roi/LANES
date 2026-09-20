"""add flood event history domain

Revision ID: f4e7c2a9b6d1
Revises: e2f891ab7034
Create Date: 2026-09-20 22:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql


revision: str = "f4e7c2a9b6d1"
down_revision: Union[str, Sequence[str], None] = "e2f891ab7034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    event_status = sa.Enum("active", "ended", name="floodeventstatus", native_enum=False, length=20)
    severity = sa.Enum("low", "medium", "high", "extreme", name="reportseverity", native_enum=False, length=50)
    location_type = sa.Enum("road", "barangay", "city", name="floodeventlocationtype", native_enum=False, length=20)
    moderation_outcome = sa.Enum("approved", "linked", "rejected", name="reportmoderationoutcometype", native_enum=False, length=20)
    rejection_reason = sa.Enum(
        "insufficient_evidence", "incorrect_location_or_details", "false_spam_or_malicious",
        "outside_coverage_area", "withdrawn", "other",
        name="reportrejectionreason", native_enum=False, length=50,
    )

    op.create_table(
        "flood_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", event_status, nullable=False, server_default="active"),
        sa.Column("first_reported_at", sa.DateTime(), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("peak_severity", severity, nullable=False),
        sa.Column("peak_depth", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "(status = 'active' AND ended_at IS NULL) OR (status = 'ended' AND ended_at IS NOT NULL)",
            name="ck_flood_events_status_ended_at",
        ),
    )
    op.create_index("ix_flood_events_status_verified_at", "flood_events", ["status", "verified_at"])
    op.create_index("ix_flood_events_ended_at", "flood_events", ["ended_at"])

    op.add_column("flood_reports", sa.Column("event_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_flood_reports_event_id", "flood_reports", "flood_events", ["event_id"], ["id"], ondelete="RESTRICT"
    )
    op.create_index("ix_flood_reports_event_id", "flood_reports", ["event_id"])

    op.add_column("flood_avoidance_zones", sa.Column("event_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_flood_avoidance_zones_event_id", "flood_avoidance_zones", "flood_events", ["event_id"], ["id"], ondelete="RESTRICT"
    )
    op.create_index("ix_flood_avoidance_zones_event_id_is_active", "flood_avoidance_zones", ["event_id", "is_active"])

    op.create_table(
        "flood_event_locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("flood_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("location_type", location_type, nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("geometry", Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("event_id", "location_type", "normalized_name", name="uq_flood_event_locations_event_type_name"),
    )
    op.create_index("ix_flood_event_locations_event_id", "flood_event_locations", ["event_id"])
    op.create_index("ix_flood_event_locations_type_name", "flood_event_locations", ["location_type", "normalized_name"])
    op.create_index("ix_flood_event_locations_geometry", "flood_event_locations", ["geometry"], postgresql_using="gist")

    op.create_table(
        "flood_report_moderation_outcomes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("flood_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("outcome", moderation_outcome, nullable=False),
        sa.Column("rejection_reason", rejection_reason, nullable=True),
        sa.Column("internal_note", sa.String(length=1000), nullable=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("flood_events.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("zone_id", sa.Integer(), sa.ForeignKey("flood_avoidance_zones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("acted_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("acted_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "(outcome = 'rejected' AND rejection_reason IS NOT NULL) OR "
            "(outcome != 'rejected' AND rejection_reason IS NULL)",
            name="ck_flood_report_outcome_reason",
        ),
        sa.CheckConstraint(
            "rejection_reason IS NULL OR rejection_reason != 'other' OR internal_note IS NOT NULL",
            name="ck_flood_report_other_rejection_note",
        ),
    )
    op.create_index("ix_flood_report_moderation_outcomes_report_acted", "flood_report_moderation_outcomes", ["report_id", "acted_at"])
    op.create_index("ix_flood_report_moderation_outcomes_event_id", "flood_report_moderation_outcomes", ["event_id"])

    op.create_table(
        "flood_event_timeline_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("flood_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entry_type", sa.String(length=50), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("snapshot_json", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_flood_event_timeline_entries_event_occurred", "flood_event_timeline_entries", ["event_id", "occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_flood_event_timeline_entries_event_occurred", table_name="flood_event_timeline_entries")
    op.drop_table("flood_event_timeline_entries")

    op.drop_index("ix_flood_report_moderation_outcomes_event_id", table_name="flood_report_moderation_outcomes")
    op.drop_index("ix_flood_report_moderation_outcomes_report_acted", table_name="flood_report_moderation_outcomes")
    op.drop_table("flood_report_moderation_outcomes")

    op.drop_index("ix_flood_event_locations_geometry", table_name="flood_event_locations")
    op.drop_index("ix_flood_event_locations_type_name", table_name="flood_event_locations")
    op.drop_index("ix_flood_event_locations_event_id", table_name="flood_event_locations")
    op.drop_table("flood_event_locations")

    op.drop_index("ix_flood_avoidance_zones_event_id_is_active", table_name="flood_avoidance_zones")
    op.drop_constraint("fk_flood_avoidance_zones_event_id", "flood_avoidance_zones", type_="foreignkey")
    op.drop_column("flood_avoidance_zones", "event_id")

    op.drop_index("ix_flood_reports_event_id", table_name="flood_reports")
    op.drop_constraint("fk_flood_reports_event_id", "flood_reports", type_="foreignkey")
    op.drop_column("flood_reports", "event_id")

    op.drop_index("ix_flood_events_ended_at", table_name="flood_events")
    op.drop_index("ix_flood_events_status_verified_at", table_name="flood_events")
    op.drop_table("flood_events")
