"""Event inspection must accept both persisted no-photo representations."""
from datetime import datetime, timezone
import json
import os

from fastapi.testclient import TestClient
from geoalchemy2.shape import from_shape
import pytest
from shapely.geometry import box
from sqlalchemy import cast, literal, select, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import DataError

from app import models
from app.api import deps
from app.core.database import get_db
from app.main import app
from app.services.spatial_browse_service import history_overview, media_array_length
from test_operational_settings_postgres import isolated_db


@pytest.fixture
def history_db(request):
    if not os.environ.get('LANES_SETTINGS_TEST_DATABASE_URL'):
        if os.environ.get('LANES_REQUIRE_HISTORY_MEDIA_TESTS') == '1':
            pytest.fail('Mandatory history media database configuration is missing')
        pytest.skip('Owned disposable PostGIS database required')
    return request.getfixturevalue('isolated_db')


def event_and_zone(db):
    now = datetime.now(timezone.utc)
    event = models.FloodEvent(status=models.FloodEventStatus.ENDED, verified_at=now,
        ended_at=now, peak_severity=models.ReportSeverity.LOW)
    db.add(event); db.flush()
    zone = models.FloodAvoidanceZone(event_id=event.id, is_active=False,
        geometry=from_shape(box(121, 14.5, 121.001, 14.501), srid=4326), media_urls=None)
    db.add(zone); db.flush()
    return event, zone


@pytest.mark.parametrize('value,expected', [
    (None, 0), ([], 0), (['https://example.invalid/one.jpg'], 1),
    (['https://example.invalid/one.jpg', 'https://example.invalid/two.jpg'], 2),
])
@pytest.mark.parametrize('table', ['flood_reports', 'flood_avoidance_zones'])
def test_persisted_media_values_count_without_rewriting_rows(history_db, value, expected, table):
    db, staff = history_db
    event, zone = event_and_zone(db)
    record_id = zone.id
    if table == 'flood_reports':
        report = models.FloodReport(event_id=event.id, zone_id=zone.id, user_id=staff.id,
            source=models.ReportSource.USER_REPORT, raw_text='Fixture evidence',
            severity=models.ReportSeverity.LOW, status=models.ReportStatus.APPROVED)
        db.add(report); db.flush(); record_id = report.id
    db.execute(text('UPDATE ' + table + ' SET media_urls=CAST(:v AS jsonb) WHERE id=:id'),
               {'v': json.dumps(value), 'id': record_id})
    db.commit()
    before = db.scalar(text('SELECT media_urls::text FROM ' + table + ' WHERE id=:id'), {'id': record_id})
    assert history_overview(db, event.id)['media_count'] == expected
    assert db.scalar(text('SELECT media_urls::text FROM ' + table + ' WHERE id=:id'), {'id': record_id}) == before


@pytest.mark.parametrize('table', ['flood_reports', 'flood_avoidance_zones'])
def test_sql_null_media_reproduces_empty_inspection(history_db, table):
    db, staff = history_db
    event, zone = event_and_zone(db)
    record_id = zone.id
    if table == 'flood_reports':
        report = models.FloodReport(event_id=event.id, zone_id=zone.id, user_id=staff.id,
            source=models.ReportSource.USER_REPORT, raw_text='Fixture evidence',
            severity=models.ReportSeverity.LOW, status=models.ReportStatus.APPROVED)
        db.add(report); db.flush(); record_id = report.id
    db.execute(text('UPDATE ' + table + ' SET media_urls=NULL WHERE id=:id'), {'id': record_id})
    db.commit()
    assert history_overview(db, event.id)['media_count'] == 0


def test_mixed_zone_and_report_arrays_exclude_deleted_reports(history_db):
    db, staff = history_db
    event, zone = event_and_zone(db)
    zone.media_urls = ['https://example.invalid/zone.jpg']
    for value, deleted in [(None, False), ([], False), (['https://example.invalid/report.jpg'], False),
                            (['https://example.invalid/deleted.jpg'], True)]:
        db.add(models.FloodReport(event_id=event.id, zone_id=zone.id, user_id=staff.id,
            source=models.ReportSource.USER_REPORT, raw_text='Fixture evidence',
            severity=models.ReportSeverity.LOW, status=models.ReportStatus.APPROVED,
            media_urls=value, deleted_at=datetime.now(timezone.utc) if deleted else None))
    db.commit()
    assert history_overview(db, event.id)['media_count'] == 2


@pytest.mark.parametrize('value', ['"invalid"', '42', '{}', 'true'])
def test_malformed_non_array_is_not_silently_normalized(history_db, value):
    db, _ = history_db
    with pytest.raises(DataError):
        with db.begin_nested():
            db.scalar(select(media_array_length(cast(literal(value), JSONB))))


def test_http_inspection_accepts_json_null_without_report_rows(history_db):
    db, staff = history_db
    event, zone = event_and_zone(db)
    db.commit()
    assert db.scalar(text('SELECT jsonb_typeof(media_urls) FROM flood_avoidance_zones WHERE id=:id'),
                     {'id': zone.id}) == 'null'
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[deps.get_current_active_admin] = lambda: staff
    try:
        client = TestClient(app)
        response = client.get(f'/api/v1/admin/flood-events/{event.id}/inspection')
        assert response.status_code == 200, response.text
        assert response.json()['media_count'] == 0
        for collection in ['zones', 'reports', 'timeline', 'locations', 'news_sources']:
            response = client.get(f'/api/v1/admin/flood-events/{event.id}/inspection/{collection}')
            assert response.status_code == 200, response.text
        assert db.scalar(text('SELECT jsonb_typeof(media_urls) FROM flood_avoidance_zones WHERE id=:id'),
                         {'id': zone.id}) == 'null'
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(deps.get_current_active_admin, None)
