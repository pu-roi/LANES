"""Exact, opt-in removal of the superseded GMA test chain; never an HTTP action.

The operator must pin a preview, back it up and rehearse on a restored database.
Source evidence is exported privately before removal, not rewritten as corrected.
"""
from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.services.flood_data_reset import REVISION, digest, snapshot, target_identity

VERSION = 'gma-incorrect-capture-cleanup-v1'
SELECTION = {
    'news_claim_evaluations': tuple(range(150, 160)),
    'news_claim_sources': tuple(range(106, 111)),
    'news_claim_cases': tuple(range(106, 111)),
    'news_extraction_runs': (375, 376, 378, 379, 380),
    'news_article_versions': (137, 574),
    'flood_avoidance_zones': tuple(range(71, 76)),
    'flood_event_locations': (),
    'flood_event_timeline_entries': tuple(range(209, 219)),
    'flood_events': tuple(range(71, 76)),
}
OLD_BODY = 'a7b92b1ec22db882779dcc2d3f0d3dc153d834f325a00432a551d04357b57708'
GUARDS = {'news_claim_evaluations': 'news_claim_evaluations_finalized',
          'news_claim_sources': 'news_claim_sources_immutable'}


def selected_rows(connection: Connection) -> dict:
    """Fixed SQL identifiers; full rows are private recovery evidence only."""
    return {table: list(connection.scalars(text(
        f'SELECT to_jsonb(t) FROM public.{table} t WHERE '
        + ('event_id BETWEEN 71 AND 75' if table == 'flood_event_locations' else 'id = ANY(:ids)')
        + ' ORDER BY id'), {} if table == 'flood_event_locations' else {'ids': list(ids)}))
        for table, ids in SELECTION.items()}


def validate_selection(rows: dict) -> None:
    import hashlib
    for table, ids in SELECTION.items():
        if table == 'flood_event_locations':
            if len(rows[table]) != 15 or any(r['event_id'] not in range(71, 76) for r in rows[table]):
                raise ValueError('gma_cleanup_location_selection_changed')
        elif [r['id'] for r in rows[table]] != list(ids):
            raise ValueError('gma_cleanup_selection_changed:' + table)
    for version in rows['news_article_versions']:
        if version['article_id'] != 47 or hashlib.sha256(
                version['input_snapshot']['article_text'].encode('utf-8')).hexdigest() != OLD_BODY:
            raise ValueError('gma_cleanup_old_capture_changed')
    if any(r['article_version_id'] != 574 for r in rows['news_extraction_runs']):
        raise ValueError('gma_cleanup_old_run_changed')
    if any(r['extraction_run_id'] != 380 or r['case_id'] not in range(106, 111)
           for r in rows['news_claim_sources']):
        raise ValueError('gma_cleanup_source_changed')
    if any(r['claim_source_id'] not in range(106, 111) for r in rows['news_claim_evaluations']):
        raise ValueError('gma_cleanup_evaluation_changed')
    if any(z['event_id'] != z['id'] or z['is_active'] for z in rows['flood_avoidance_zones']):
        raise ValueError('gma_cleanup_zone_changed')
    if any(e['status'] != 'ended' for e in rows['flood_events']):
        raise ValueError('gma_cleanup_event_changed')
    for entry in rows['flood_event_timeline_entries']:
        if entry['event_id'] not in range(71, 76) or not (
            entry['entry_type'] == 'historical_import' and entry['snapshot_json'].get('run_id') == 380
            or entry['entry_type'] == 'news_source_superseded'
            and entry['snapshot_json'].get('old_run_id') == 380):
            raise ValueError('gma_cleanup_lineage_changed')


def exact_fingerprints(connection: Connection, *, exclude_selected: bool = False) -> dict:
    tables = list(connection.scalars(text(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")))
    result = {}
    for table in tables:
        # Table names come from PostgreSQL, never operator input.
        quoted = connection.dialect.identifier_preparer.quote(table)
        clause, args = '', {}
        if exclude_selected and table in SELECTION:
            clause = (' WHERE NOT (event_id BETWEEN 71 AND 75)' if table == 'flood_event_locations'
                      else ' WHERE NOT (id = ANY(:ids))')
            args = {} if table == 'flood_event_locations' else {'ids': list(SELECTION[table])}
        values = sorted(connection.scalars(text(f'SELECT md5(to_jsonb(t)::text) FROM public.{quoted} t' + clause), args))
        result[table] = {'count': len(values), 'sha256': digest(values)}
    return result


def preview(connection: Connection) -> dict:
    rows = selected_rows(connection)
    validate_selection(rows)
    state = snapshot(connection)
    if state['revision'] != REVISION:
        raise ValueError('gma_cleanup_schema_changed')
    return {'schema_version': VERSION, 'target_identity': target_identity(connection),
            'selected_sha256': digest(rows), 'counts': {t: len(r) for t, r in rows.items()},
            'protected': exact_fingerprints(connection, exclude_selected=True),
            'schema': {k: state[k] for k in ('revision', 'constraints', 'triggers', 'sequences')}}


def check_dependencies(connection: Connection, rows: dict) -> None:
    """Reject outside references even when their FK would SET NULL or CASCADE."""
    references = connection.execute(text("""
        SELECT child.relname AS child, parent.relname AS parent, ca.attname AS column
        FROM pg_constraint f JOIN pg_class child ON child.oid=f.conrelid
        JOIN pg_class parent ON parent.oid=f.confrelid
        JOIN pg_attribute ca ON ca.attrelid=f.conrelid AND ca.attnum=f.conkey[1]
        WHERE f.contype='f' AND array_length(f.conkey,1)=1
          AND parent.relnamespace='public'::regnamespace
    """)).mappings()
    quote = connection.dialect.identifier_preparer.quote
    for fk in references:
        if fk['parent'] not in rows:
            continue
        parent_ids = [r['id'] for r in rows[fk['parent']]]
        child_ids = [r['id'] for r in rows.get(fk['child'], [])]
        count = connection.scalar(text(f'SELECT count(*) FROM public.{quote(fk["child"])}'
            f' WHERE {quote(fk["column"])} = ANY(:parents) AND NOT (id = ANY(:children))'),
            {'parents': parent_ids, 'children': child_ids})
        if count:
            raise ValueError('gma_cleanup_unrelated_dependency:' + fk['child'])


def cleanup_in_transaction(connection: Connection, authority: dict, authority_sha256: str, *,
                           checkpoint: Callable[[str], None] | None = None) -> dict:
    """Caller owns the transaction. Rejected dependencies roll back every deletion."""
    if (digest(authority) != authority_sha256 or authority.get('schema_version') != VERSION
            or connection.dialect.name != 'postgresql'
            or target_identity(connection) != authority.get('target_identity')):
        raise ValueError('gma_cleanup_authority_invalid')
    connection.execute(text("SET LOCAL lock_timeout='8000'"))
    connection.execute(text("SET LOCAL statement_timeout='60000'"))
    tables = sorted(authority['protected'])
    connection.execute(text('LOCK TABLE ' + ','.join('public.' + connection.dialect.identifier_preparer.quote(t)
        for t in tables) + ' IN SHARE ROW EXCLUSIVE MODE'))
    rows = selected_rows(connection)
    if not any(rows.values()):
        return {'status': 'reused', 'deleted': {}, 'database_writes': 0}
    if preview(connection) != authority:
        raise ValueError('gma_cleanup_preview_changed')
    check_dependencies(connection, rows)
    # RESTRICT FKs catch new direct dependents. SET NULL/CASCADE must not change
    # any unrelated row: exact protected fingerprints are checked before commit.
    for table, guard in GUARDS.items():
        if not any(r[:3] == [table, guard, 'O'] for r in authority['schema']['triggers']):
            raise ValueError('gma_cleanup_guard_changed')
        connection.execute(text(f'ALTER TABLE public.{table} DISABLE TRIGGER {guard}'))
    deleted = {}
    for table, ids in SELECTION.items():
        actual_ids = [r['id'] for r in rows[table]]
        deleted[table] = connection.execute(text(f'DELETE FROM public.{table} WHERE id = ANY(:ids)'),
            {'ids': actual_ids}).rowcount
        if deleted[table] != authority['counts'][table]:
            raise ValueError('gma_cleanup_delete_count_changed')
        if checkpoint:
            checkpoint(table)
    for table, guard in GUARDS.items():
        connection.execute(text(f'ALTER TABLE public.{table} ENABLE TRIGGER {guard}'))
    connection.execute(text('SET CONSTRAINTS ALL IMMEDIATE'))
    state = snapshot(connection)
    if any(state[k] != authority['schema'][k] for k in authority['schema']):
        raise ValueError('gma_cleanup_schema_or_sequences_changed')
    if exact_fingerprints(connection) != authority['protected'] or any(selected_rows(connection).values()):
        raise ValueError('gma_cleanup_unrelated_rows_changed')
    return {'status': 'completed', 'deleted': deleted, 'database_writes': sum(deleted.values()),
            'preservation_verified': True, 'authority_sha256': authority_sha256}
