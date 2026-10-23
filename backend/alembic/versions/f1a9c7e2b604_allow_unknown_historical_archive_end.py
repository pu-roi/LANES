"""Allow unknown archive endpoints only with committed historical lineage.

Revision ID: f1a9c7e2b604
Revises: e8a6f1c2d903

Approved narrowly for Phase 1: ordinary ended events still require ended_at.
No timestamps are synthesized and no tables or columns are added.
"""
from alembic import op

revision = 'f1a9c7e2b604'
down_revision = 'e8a6f1c2d903'
branch_labels = None
depends_on = None

CONSTRAINT = 'ck_flood_events_ck_flood_events_status_ended_at'


def upgrade() -> None:
    op.drop_constraint(op.f(CONSTRAINT), 'flood_events', type_='check')
    op.create_check_constraint(op.f(CONSTRAINT), 'flood_events',
        "(status = 'active' AND ended_at IS NULL) OR status = 'ended'")
    op.execute("""
        CREATE FUNCTION lanes_check_historical_endpoint(target_id integer) RETURNS void
        LANGUAGE plpgsql AS $$
        DECLARE target_status text; target_end timestamptz;
        BEGIN
            SELECT status, ended_at INTO target_status, target_end FROM flood_events
                WHERE id = target_id FOR UPDATE;
            IF NOT FOUND OR target_status <> 'ended' OR target_end IS NOT NULL THEN
                RETURN;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM flood_event_timeline_entries
                WHERE event_id = target_id AND entry_type = 'historical_import'
                  AND snapshot_json->>'schema_version' = 'historical-import-v1'
                  AND snapshot_json->>'dataset_id' = 'capstone-september-2026-v1'
                  AND snapshot_json->>'disposition' = 'historical_archive'
                  AND snapshot_json->>'closure_basis' = 'unknown'
                  AND snapshot_json->>'precision' IN ('instant', 'date', 'unknown')
                  AND snapshot_json->>'observation_key' ~ '^[a-f0-9]{64}$'
                  AND snapshot_json->>'demonstration_session_id' ~
                      '^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
            ) THEN
                RAISE EXCEPTION 'Ended events require an endpoint or supported unknown-end historical archive lineage'
                    USING ERRCODE = '23514', CONSTRAINT = 'ck_flood_events_historical_endpoint';
            END IF;
        END $$;
        CREATE FUNCTION lanes_enforce_historical_endpoint() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_TABLE_NAME = 'flood_events' THEN
                PERFORM lanes_check_historical_endpoint(NEW.id);
            ELSE
                IF TG_OP <> 'INSERT' THEN
                    PERFORM lanes_check_historical_endpoint(OLD.event_id);
                END IF;
                IF TG_OP <> 'DELETE' THEN
                    PERFORM lanes_check_historical_endpoint(NEW.event_id);
                END IF;
            END IF;
            RETURN NULL;
        END $$;
        CREATE CONSTRAINT TRIGGER flood_events_historical_endpoint
            AFTER INSERT OR UPDATE ON flood_events DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE FUNCTION lanes_enforce_historical_endpoint();
        CREATE CONSTRAINT TRIGGER flood_timeline_historical_endpoint
            AFTER INSERT OR UPDATE OR DELETE ON flood_event_timeline_entries
            DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE FUNCTION lanes_enforce_historical_endpoint();
    """)


def downgrade() -> None:
    # Restore the original invariant before dropping its deferred replacement.
    # Existing unknown endpoints deliberately block downgrade instead of inventing dates.
    op.drop_constraint(op.f(CONSTRAINT), 'flood_events', type_='check')
    op.create_check_constraint(op.f(CONSTRAINT), 'flood_events',
        "(status = 'active' AND ended_at IS NULL) OR (status = 'ended' AND ended_at IS NOT NULL)")
    op.execute("""
        DROP TRIGGER flood_timeline_historical_endpoint ON flood_event_timeline_entries;
        DROP TRIGGER flood_events_historical_endpoint ON flood_events;
        DROP FUNCTION lanes_enforce_historical_endpoint();
        DROP FUNCTION lanes_check_historical_endpoint(integer);
    """)
