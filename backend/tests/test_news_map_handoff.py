"""Saved news handoffs follow source lineage, not proximity or current page."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from geoalchemy2.shape import from_shape
from shapely.geometry import box
from sqlalchemy import event as sql_event
from sqlalchemy.exc import SQLAlchemyError

from app import models
from app.api import deps
from app.core.database import get_db
from app.main import app
from app.services import news_map_handoff_service as service
from app.services.configuration_service import CONFIG_KEY
from app.models.setting import SystemSetting
from app.schemas.configuration import OperationalSettings
from test_operational_settings_postgres import isolated_db


def test_native_handoff_matches_run_and_group_and_current_active_policy(isolated_db):
    db, _staff = isolated_db
    now = datetime.now(timezone.utc)
    zones = []
    for run, group, active, deadline in [(401, "resolved-n5", True, None),
            (401, "resolved-n7", True, None), (402, "resolved-n5", True, None),
            (401, "resolved-n5", False, None), (401, "resolved-n5", True, now-timedelta(minutes=1))]:
        incident = models.FloodEvent(peak_severity=models.ReportSeverity.LOW)
        db.add(incident); db.flush()
        zone = models.FloodAvoidanceZone(event_id=incident.id, geometry=from_shape(box(121,14.5,121.001,14.501), srid=4326),
            is_active=active, expires_at=deadline)
        db.add(zone)
        db.add(models.FloodEventTimelineEntry(event_id=incident.id, entry_type="historical_import", summary="Fixture source link",
            snapshot_json={"schema_version": "historical-import-v1", "run_id": run, "group_id": group}))
        zones.append(zone)
    db.commit()
    writes = []
    def capture(_connection, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().split()[0].upper() in {"UPDATE", "INSERT", "DELETE"}:
            writes.append(statement)
    bind = db.get_bind()
    sql_event.listen(bind, "before_cursor_execute", capture)
    try:
        assert service.linked_active_zone_ids(db, 401, None, "resolved-n5") == [zones[0].id]
        assert service.linked_active_zone_ids(db, 401, None, "resolved-n7") == [zones[1].id]
        assert service.linked_active_zone_ids(db, 999, None, "resolved-n5") == []
        assert service.linked_active_zone_ids(db, 401, None, None) == []
        assert writes == []
    finally:
        sql_event.remove(bind, "before_cursor_execute", capture)
    config = OperationalSettings(automatic_expiry_enabled=False)
    db.add(SystemSetting(key=CONFIG_KEY, value={"revision": 1, "settings": config.model_dump(mode="json")}))
    db.commit()
    assert service.linked_active_zone_ids(db, 401, None, "resolved-n5") == [zones[0].id, zones[4].id]


@pytest.mark.asyncio
@pytest.mark.parametrize("native,ordinal", [(False, 3), (True, 3), (True, None)])
async def test_map_target_validates_saved_identity_and_exposes_only_linked_zone(monkeypatch, native, ordinal):
    item = SimpleNamespace(claim_index=ordinal, group_id="resolved-n5")
    monkeypatch.setattr(service, "read_news_result", lambda db, run, ordinal: SimpleNamespace(item=item) if ordinal == 3 else None)
    monkeypatch.setattr(service, "read_native_group", lambda db, run, group, labels: SimpleNamespace(item=item) if group == "resolved-n5" else None)
    calls = []
    def linked(db, run, ordinal, group):
        calls.append((run, ordinal, group))
        return [92, 93]
    monkeypatch.setattr(service, "linked_active_zone_ids", linked)
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[deps.get_current_active_admin] = lambda: object()
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://fixture") as client:
            url = "/api/v1/admin/news/results/401/map-target"
            params = {"group_id": "resolved-n5"} if native else {"claim_index": 3}
            response = await client.get(url, params=params)
            assert response.status_code == 200, response.text
            assert response.json() == {"zone_id": 92, "claim_index": ordinal, "read_only": True}
            assert calls == [(401, ordinal, "resolved-n5")]
            assert (await client.get(url)).status_code == 422
            assert (await client.get(url, params={"group_id": "resolved-n5", "claim_index": 3})).status_code == 422
            assert (await client.get(url, params={"claim_index": 99})).status_code == 404
            monkeypatch.setattr(service, "linked_active_zone_ids", lambda *args: [])
            assert (await client.get(url, params=params)).json()["zone_id"] is None
            def unavailable(*args):
                raise SQLAlchemyError("private database diagnostic")
            monkeypatch.setattr(service, "linked_active_zone_ids", unavailable)
            failed = await client.get(url, params=params)
            assert failed.status_code == 503 and "private database" not in failed.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_map_target_requires_staff_session():
    app.dependency_overrides[get_db] = lambda: None
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://fixture") as client:
            assert (await client.get("/api/v1/admin/news/results/401/map-target?claim_index=0")).status_code == 401
    finally:
        app.dependency_overrides.clear()
