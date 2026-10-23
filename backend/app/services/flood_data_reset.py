"""Explicit maintenance reset; no HTTP endpoint or automatic invocation.

Source captures, community content and account data are preserved. Callers must
provide a reviewed exact snapshot and a separately verified backup/rehearsal.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable

from sqlalchemy import text
from sqlalchemy.engine import Connection

REVISION = 'f1a9c7e2b604'
DELETE_ORDER = (
    'news_claim_zone_links', 'news_claim_decisions', 'news_claim_evaluations',
    'news_claim_sources', 'news_claim_cases', 'news_extraction_runs',
    'flood_report_moderation_outcomes', 'flood_report_surveys', 'flood_report_locations',
    'flood_reports', 'flood_avoidance_zones', 'flood_event_locations',
    'flood_event_timeline_entries', 'flood_events',
)
DELETE_GUARDS = {
    'news_claim_zone_links': 'news_claim_zone_links_immutable',
    'news_claim_decisions': 'news_claim_decisions_immutable',
    'news_claim_evaluations': 'news_claim_evaluations_finalized',
    'news_claim_sources': 'news_claim_sources_immutable',
}
NOTICE_FILTER = """COALESCE((n.payload->>'action' IN
    ('flood_report_under_review','flood_report_approved','flood_report_rejected')
    AND n.payload->>'report_id' IN (SELECT id::text FROM public.flood_reports)),false)"""


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def target_identity(connection: Connection) -> str:
    url = connection.engine.url
    return digest({'host': url.host, 'port': url.port, 'database': url.database,
                   'username': url.username})


def _name(value: str) -> str:
    if re.fullmatch(r'[a-z][a-z0-9_]*', value) is None:
        raise ValueError('reset_unexpected_identifier')
    return 'public."' + value + '"'


def snapshot(connection: Connection) -> dict:
    """Content-free row multisets plus exact FK/trigger/sequence definitions."""
    tables = list(connection.scalars(text(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")))
    if not set(DELETE_ORDER) <= set(tables):
        raise ValueError('reset_missing_tables')
    rows = {}
    for name in tables:
        expression = "to_jsonb(t)-'flood_report_id'" if name == 'community_posts' else 'to_jsonb(t)'
        if name == 'notifications':
            query = f"SELECT md5(to_jsonb(n)::text) FROM {_name(name)} n WHERE NOT ({NOTICE_FILTER})"
        else:
            query = f'SELECT md5(({expression})::text) FROM {_name(name)} t'
        values = sorted(connection.scalars(text(query)))
        rows[name] = {'count': len(values), 'sha256': digest(values)}
    triggers = [list(r) for r in connection.execute(text("""
        SELECT c.relname,t.tgname,t.tgenabled,pg_get_triggerdef(t.oid)
        FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
        JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE NOT t.tgisinternal AND n.nspname='public' ORDER BY 1,2"""))]
    constraints = [list(r) for r in connection.execute(text("""
        SELECT conrelid::regclass::text,conname,pg_get_constraintdef(oid),convalidated
        FROM pg_constraint WHERE connamespace='public'::regnamespace ORDER BY 1,2"""))]
    sequences = [list(r) for r in connection.execute(text("""
        SELECT sequencename,last_value,start_value,increment_by,min_value,max_value,cache_size,cycle
        FROM pg_sequences WHERE schemaname='public' ORDER BY sequencename"""))]
    notices = list(connection.scalars(text(f'SELECT n.id FROM public.notifications n WHERE {NOTICE_FILTER} ORDER BY n.id')))
    linked = list(connection.scalars(text(
        'SELECT id FROM public.community_posts WHERE flood_report_id IS NOT NULL ORDER BY id')))
    return {'revision': connection.scalar(text('SELECT version_num FROM public.alembic_version')),
            'rows': rows, 'triggers': triggers, 'constraints': constraints, 'sequences': sequences,
            'notification_ids': notices, 'detach_post_ids': linked}


def verify_preserved(before: dict, after: dict) -> None:
    if before['revision'] != after['revision'] or before['revision'] != REVISION:
        raise ValueError('reset_revision_changed')
    if set(before['rows']) != set(after['rows']):
        raise ValueError('reset_tables_changed')
    for name, fingerprint in before['rows'].items():
        if name in DELETE_ORDER:
            if after['rows'][name]['count'] != 0:
                raise ValueError('reset_target_not_empty:' + name)
        elif after['rows'][name] != fingerprint:
            raise ValueError('reset_preserved_rows_changed:' + name)
    for name in ('triggers', 'constraints', 'sequences'):
        if before[name] != after[name]:
            raise ValueError('reset_schema_or_sequence_changed:' + name)
    if after['notification_ids'] or after['detach_post_ids']:
        raise ValueError('reset_link_cleanup_incomplete')


def reset_in_transaction(connection: Connection, expected: dict, *,
                         expected_identity: str,
                         checkpoint: Callable[[str], None] | None = None) -> dict:
    """Caller owns BEGIN/COMMIT. Any failure must roll back the entire txn."""
    if connection.engine.dialect.name != 'postgresql' or target_identity(connection) != expected_identity:
        raise ValueError('reset_target_mismatch')
    if connection.scalar(text('SELECT current_database()')) != connection.engine.url.database:
        raise ValueError('reset_connected_database_mismatch')
    connection.execute(text("SET LOCAL lock_timeout='8000'"))
    connection.execute(text("SET LOCAL statement_timeout='60000'"))
    tables = sorted(expected['rows'])
    connection.execute(text('LOCK TABLE ' + ','.join(_name(t) for t in tables)
                            + ' IN SHARE ROW EXCLUSIVE MODE'))
    before = snapshot(connection)
    if before != expected or before['revision'] != REVISION:
        raise ValueError('reset_snapshot_changed')
    for table, trigger in DELETE_GUARDS.items():
        match = next((r for r in before['triggers'] if r[:2] == [table, trigger]), None)
        if match is None or match[2] != 'O':
            raise ValueError('reset_guard_state_unexpected')
    # SQL UPDATE deliberately avoids ORM cascades and timestamp onupdate hooks.
    detached = connection.execute(text(
        'UPDATE public.community_posts SET flood_report_id=NULL WHERE flood_report_id IS NOT NULL')).rowcount
    removed_notifications = connection.execute(text(
        f'DELETE FROM public.notifications n WHERE {NOTICE_FILTER}')).rowcount
    for table, trigger in DELETE_GUARDS.items():
        connection.execute(text(f'ALTER TABLE {_name(table)} DISABLE TRIGGER "{trigger}"'))
    deleted = {}
    for table in DELETE_ORDER:
        deleted[table] = connection.execute(text(f'DELETE FROM {_name(table)}')).rowcount
        if checkpoint is not None:
            checkpoint(table)
    for table, trigger in DELETE_GUARDS.items():
        connection.execute(text(f'ALTER TABLE {_name(table)} ENABLE TRIGGER "{trigger}"'))
    connection.execute(text('SET CONSTRAINTS ALL IMMEDIATE'))
    after = snapshot(connection)
    verify_preserved(before, after)
    return {'status': 'cleared', 'before_sha256': digest(before), 'after_sha256': digest(after),
            'deleted': deleted, 'detached_posts': detached,
            'removed_report_notifications': removed_notifications,
            'preserved': {t: v['count'] for t, v in after['rows'].items() if t not in DELETE_ORDER},
            'constraints_triggers_sequences_unchanged': True}
