"""Content-free fingerprints for detecting changes to pre-existing application rows."""
from __future__ import annotations

from sqlalchemy import text

PROTECTED_TABLES = ('users', 'profiles', 'flood_reports', 'flood_report_surveys',
    'flood_report_locations', 'flood_report_moderation_outcomes', 'flood_events', 'flood_avoidance_zones')


def protected_fingerprints(connection: object) -> dict:
    # Names are fixed constants. No table/SQL identifier comes from an operator.
    return {table: {str(row.id): row.fingerprint for row in connection.execute(text(
        f'SELECT id, md5(to_jsonb(t)::text) AS fingerprint FROM {table} AS t ORDER BY id'))}
        for table in PROTECTED_TABLES}


def verify_protected(before: dict, after: dict) -> None:
    from app.services.news_historical_processing import require
    require(set(before) == set(after) == set(PROTECTED_TABLES), 'historical_baseline_invalid')
    for table, rows in before.items():
        require(all(after[table].get(key) == value for key, value in rows.items()),
            'historical_existing_rows_changed')
