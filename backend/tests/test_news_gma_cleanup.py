"""The maintenance selection must never grow to include corrected or manual data."""
from copy import deepcopy
import hashlib

import pytest

from app.services import news_gma_cleanup as service


def fixture_rows(monkeypatch):
    rows = {table: [{'id': i} for i in ids] for table, ids in service.SELECTION.items()}
    rows['flood_event_locations'] = [{'id': i, 'event_id': 71 + i // 3} for i in range(15)]
    monkeypatch.setattr(service, 'OLD_BODY', hashlib.sha256(b'fixture capture').hexdigest())
    for r in rows['news_article_versions']:
        r.update(article_id=47, input_snapshot={'article_text': 'fixture capture'})
    for r in rows['news_extraction_runs']:
        r['article_version_id'] = 574
    for r in rows['news_claim_sources']:
        r.update(extraction_run_id=380, case_id=r['id'])
    for r in rows['news_claim_evaluations']:
        r['claim_source_id'] = 106 + (r['id'] - 150) % 5
    for r in rows['flood_events']:
        r['status'] = 'ended'
    for r in rows['flood_avoidance_zones']:
        r.update(event_id=r['id'], is_active=False)
    for i, r in enumerate(rows['flood_event_timeline_entries']):
        r.update(event_id=71 + i % 5, entry_type='historical_import' if i < 5 else 'news_source_superseded',
                 snapshot_json={'run_id': 380} if i < 5 else {'old_run_id': 380})
    return rows


def test_exact_old_chain_passes(monkeypatch):
    service.validate_selection(fixture_rows(monkeypatch))


@pytest.mark.parametrize('table', list(service.SELECTION))
def test_missing_or_extra_rows_reject(monkeypatch, table):
    rows = fixture_rows(monkeypatch)
    rows[table].pop()
    with pytest.raises(ValueError, match='selection'):
        service.validate_selection(rows)


@pytest.mark.parametrize('table,field,value', [
    ('news_article_versions', 'article_id', 25),
    ('news_extraction_runs', 'article_version_id', 569),
    ('news_claim_sources', 'extraction_run_id', 388),
    ('news_claim_sources', 'case_id', 111),
    ('news_claim_evaluations', 'claim_source_id', 111),
    ('flood_avoidance_zones', 'is_active', True),
    ('flood_avoidance_zones', 'event_id', 76),
    ('flood_events', 'status', 'active'),
    ('flood_event_timeline_entries', 'event_id', 76),
])
def test_changed_ownership_or_lifecycle_rejects(monkeypatch, table, field, value):
    rows = fixture_rows(monkeypatch)
    rows[table][0][field] = value
    with pytest.raises(ValueError):
        service.validate_selection(rows)


def test_corrected_capture_cannot_be_deleted_by_body_alias(monkeypatch):
    rows = fixture_rows(monkeypatch)
    rows['news_article_versions'][0]['input_snapshot']['article_text'] = 'corrected article'
    with pytest.raises(ValueError, match='old_capture_changed'):
        service.validate_selection(rows)
