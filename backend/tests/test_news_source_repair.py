"""Source repair preserves raw evidence and withdraws only exact disputed archives."""
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app import models
from app.services.news_source_repair import VERSION, superseded_event
from app.services.flood_event_service import build_flood_event_history_query
from app.services.spatial_browse_service import history_overview
from test_news_history_evidence import saved_news
from test_operational_settings_postgres import isolated_db


def test_superseded_news_archive_is_absent_from_cards_map_and_analytics_but_not_deleted(isolated_db):
    db, staff = isolated_db
    event, zone, version, run = saved_news(db, staff)
    before = deepcopy(run.result)
    assert build_flood_event_history_query(db).count() == 1
    db.add(models.FloodEventTimelineEntry(event_id=event.id, entry_type='news_source_superseded',
        occurred_at=datetime.now(timezone.utc), summary='Source corrected',
        snapshot_json={'schema_version':VERSION, 'replacement_run_id':999}))
    db.commit()
    assert build_flood_event_history_query(db).count() == 0
    assert db.get(models.FloodEvent,event.id) is not None
    assert db.get(models.FloodAvoidanceZone,zone.id) is not None
    assert run.result == before
    with pytest.raises(HTTPException) as caught:
        history_overview(db,event.id)
    assert caught.value.status_code == 409


def test_supersession_marker_requires_exact_schema_and_entry_type(isolated_db):
    db, staff = isolated_db
    event, _zone, _version, _run = saved_news(db, staff)
    db.add(models.FloodEventTimelineEntry(event_id=event.id, entry_type='unrelated',
        occurred_at=datetime.now(timezone.utc), summary='Unrelated', snapshot_json={'schema_version':VERSION}))
    db.commit()
    assert build_flood_event_history_query(db).count() == 1


def test_correlated_supersession_filters_zone_event_not_arbitrary_event():
    statement = select(models.FloodAvoidanceZone.id).where(~superseded_event(models.FloodAvoidanceZone.event_id))
    sql = str(statement.compile(dialect=postgresql.dialect(),compile_kwargs={'literal_binds':True}))
    assert 'flood_event_timeline_entries.event_id = flood_avoidance_zones.event_id' in sql


def test_repair_authority_rejects_changed_source_selection_before_delegating():
    from app.services.news_source_repair import validate_authority, SESSION, BODY
    from app.services.news_ner_durable.contracts import sha
    from app.services.news_ner_durable.resolution import ResolutionError
    p={'schema_version':VERSION,'session_id':SESSION,'allowed_operations':['ner'],'allowed_article_ids':[47],
       'source_version_id':140,'native_version_id':569,'source_body_sha256':BODY,'old_event_ids':[71,72,73,74,75],
       'active_output_allowed':False,'inputs':[{'article_id':47,'source_version_id':137,'body_sha256':BODY}]}
    with patch('app.services.news_source_repair.delegate') as called:
        with pytest.raises(ResolutionError, match='capture_invalid'):
            validate_authority(SimpleNamespace(policy=p,policy_sha256=sha(p)),None)
        called.assert_not_called()
