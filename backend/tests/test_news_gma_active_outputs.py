"""Active-only identity, history isolation and strict source/placement boundaries."""
from copy import deepcopy
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.models.report import FloodAvoidanceZone
from app.services.news_gma_active_outputs import VERSION, DATASET, SESSION, HINTS, active_only_event, validate_authority
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_source_repair import BODY


def authority():
    trusted = SimpleNamespace(manifest={'model': 'unchanged'})
    policy = {'schema_version': VERSION, 'session_id': SESSION, 'dataset_id': DATASET,
        'allowed_operations': ['preview'], 'run_id': 388, 'native_version_id': 569, 'source_version_id': 140,
        'article_id': 47, 'source_body_sha256': BODY, 'coordinate_hints': deepcopy(HINTS),
        'provider_requests_allowed': 0, 'database_identity_sha256': 'fixture',
        'assets_sha256': sha(trusted.manifest)}
    return policy, trusted


def test_exact_authority_accepts_only_separate_operations(monkeypatch):
    monkeypatch.setattr('app.services.news_historical_processing.database_identity', lambda e: 'fixture')
    policy, trusted = authority()
    validate_authority(policy, sha(policy), None, trusted)
    policy['allowed_operations'] = ['apply']
    validate_authority(policy, sha(policy), None, trusted)


@pytest.mark.parametrize('field,value', [
    ('schema_version', 'paired-pilot-output-v1'), ('session_id', 'changed'), ('dataset_id', 'historical'),
    ('allowed_operations', ['preview', 'apply']), ('allowed_operations', ['resolve']), ('run_id', 380),
    ('native_version_id', 574), ('source_version_id', 137), ('article_id', 25), ('source_body_sha256', 'changed'),
    ('coordinate_hints', {}), ('provider_requests_allowed', 1), ('database_identity_sha256', 'changed'),
    ('assets_sha256', 'changed'),
])
def test_changed_grant_rejected_even_when_rehashed(monkeypatch, field, value):
    monkeypatch.setattr('app.services.news_historical_processing.database_identity', lambda e: 'fixture')
    policy, trusted = authority()
    policy[field] = value
    with pytest.raises(ResolutionError, match='authority_invalid'):
        validate_authority(policy, sha(policy), None, trusted)


def test_changed_hint_never_establishes_geometry(monkeypatch):
    monkeypatch.setattr('app.services.news_historical_processing.database_identity', lambda e: 'fixture')
    policy, trusted = authority()
    policy['coordinate_hints']['resolved-n10'][0] += .001
    with pytest.raises(ResolutionError):
        validate_authority(policy, sha(policy), None, trusted)


def test_sql_filter_correlates_exact_presentation_dataset():
    query = select(FloodAvoidanceZone.id).where(~active_only_event(FloodAvoidanceZone.event_id))
    sql = str(query.compile(dialect=postgresql.dialect(), compile_kwargs={'literal_binds': True}))
    assert 'flood_event_timeline_entries.event_id = flood_avoidance_zones.event_id' in sql
    assert DATASET in sql and 'active_demo' in sql and 'historical-import-v1' in sql


def test_hints_are_latitude_longitude_and_not_reversed():
    assert len(HINTS) == 3
    assert all(14 < lat < 15 and 120 < lon < 122 for lat, lon in HINTS.values())


from test_operational_settings_postgres import isolated_db


def test_active_only_is_excluded_from_history_and_direct_inspection(isolated_db):
    from datetime import datetime, timezone
    from fastapi import HTTPException
    from app.models.report import FloodEvent, FloodEventStatus, FloodEventTimelineEntry
    from app.services.flood_event_service import build_flood_event_history_query
    from app.services.spatial_browse_service import history_overview
    db, _staff = isolated_db
    now = datetime.now(timezone.utc)
    ordinary = FloodEvent(status=FloodEventStatus.ENDED, verified_at=now, ended_at=now, peak_severity='low')
    presentation = FloodEvent(status=FloodEventStatus.ACTIVE, verified_at=now, peak_severity='low')
    db.add_all([ordinary, presentation]); db.flush()
    db.add(FloodEventTimelineEntry(event_id=presentation.id, entry_type='historical_import', occurred_at=now,
        summary='Source road', snapshot_json={'schema_version': 'historical-import-v1',
            'dataset_id': DATASET, 'disposition': 'active_demo'}))
    db.commit()
    assert [e.id for e in build_flood_event_history_query(db).all()] == [ordinary.id]
    with pytest.raises(HTTPException) as caught:
        history_overview(db, presentation.id)
    assert caught.value.status_code == 404


def test_older_paired_dataset_behavior_is_preserved(isolated_db):
    from datetime import datetime, timezone
    from app.models.report import FloodEvent, FloodEventStatus, FloodEventTimelineEntry
    from app.services.flood_event_service import build_flood_event_history_query
    db, _staff = isolated_db
    now = datetime.now(timezone.utc)
    event = FloodEvent(status=FloodEventStatus.ACTIVE, verified_at=now, peak_severity='low')
    db.add(event); db.flush()
    db.add(FloodEventTimelineEntry(event_id=event.id, entry_type='historical_import', occurred_at=now,
        summary='Older paired dataset', snapshot_json={'schema_version': 'historical-import-v1',
            'dataset_id': 'older-paired-dataset', 'disposition': 'active_demo'}))
    db.commit()
    assert build_flood_event_history_query(db).count() == 1


def test_one_unresolved_location_blocks_the_entire_write(isolated_db, monkeypatch):
    from app.services.news_gma_active_outputs import active_outputs
    from app.services.news_historical_processing import database_identity
    from app.models.report import FloodEvent
    db, _staff = isolated_db
    engine = db.get_bind().engine
    policy, trusted = authority()
    policy.update(allowed_operations=['apply'], database_identity_sha256=database_identity(engine))
    rows = [{'group_id': target, 'outcome': 'unresolved' if i == 2 else 'geometry_qualified'}
            for i, target in enumerate(HINTS)]
    monkeypatch.setattr('app.services.news_gma_active_outputs.qualify', lambda *a, **kw: rows)
    before = db.query(FloodEvent).count()
    with pytest.raises(ResolutionError, match='all_three_must_qualify'):
        active_outputs(engine, policy, sha(policy), trusted, apply=True)
    assert db.query(FloodEvent).count() == before


def test_connected_authority_pins_original_assets_and_new_policy(monkeypatch):
    import hashlib
    from pathlib import Path
    from app.services.news_gma_active_outputs import CONNECTED_VERSION
    from app.services.news_connected_road_service import VERSION as ROAD_POLICY
    monkeypatch.setattr('app.services.news_historical_processing.database_identity',lambda e:'fixture')
    p,t=authority()
    p.update(schema_version=CONNECTED_VERSION,road_policy=ROAD_POLICY,placement_identity={'authenticated':True},
        saved_release_sha256='ca6befd3719e1882a37d9183bb933848e8545faa6a65da05f7956613221a961b',
        saved_assets_sha256=sha(t.manifest),road_code_sha256=hashlib.sha256(
            (Path(__file__).resolve().parents[1]/'app/services/news_connected_road_service.py').read_bytes()).hexdigest())
    validate_authority(p,sha(p),None,t)
    for field in ('road_policy','saved_release_sha256','saved_assets_sha256','road_code_sha256'):
        changed=deepcopy(p);changed[field]='changed'
        with pytest.raises(ResolutionError):validate_authority(changed,sha(changed),None,t)
