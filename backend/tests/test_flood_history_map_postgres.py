from datetime import datetime, timezone
from types import SimpleNamespace

from geoalchemy2.shape import from_shape
import pytest
from shapely.geometry import Polygon, box
from sqlalchemy import event as sql_event

from app import models
from app.api.v1.endpoints.admin import list_flood_event_history
from test_operational_settings_postgres import isolated_db


def test_summary_http_reads_have_bounded_queries_and_match_detail_metrics(isolated_db):
    from fastapi.testclient import TestClient
    from app.api import deps
    from app.core.database import get_db
    from app.main import app
    from app.services.flood_event_service import get_event_metrics

    db, staff = isolated_db
    now = datetime.now(timezone.utc)
    for index in range(25):
        item = models.FloodEvent(status=models.FloodEventStatus.ENDED, verified_at=now,
            ended_at=now, peak_severity=models.ReportSeverity.HIGH)
        db.add(item); db.flush()
        zone = models.FloodAvoidanceZone(event_id=item.id, geometry=from_shape(box(121,14,121.001,14.001), srid=4326),
            is_active=False)
        db.add(zone); db.flush()
        for deleted in (False, True):
            db.add(models.FloodReport(event_id=item.id, zone_id=zone.id, user_id=staff.id,
                source=models.ReportSource.USER_REPORT, status=models.ReportStatus.APPROVED,
                severity=models.ReportSeverity.HIGH, raw_text="History evidence", deleted_at=now if deleted else None))
        db.add(models.FloodEventLocation(event_id=item.id, location_type=models.FloodEventLocationType.ROAD,
            display_name=f"History road {index}", normalized_name=f"history road {index}"))
    db.commit()
    statements = []
    def record(_connection, _cursor, statement, _parameters, _context, _many):
        statements.append(statement)
    connection = db.connection()
    sql_event.listen(connection, "before_cursor_execute", record)
    app.dependency_overrides[deps.get_current_active_admin] = lambda: staff
    app.dependency_overrides[get_db] = lambda: db
    try:
        client = TestClient(app)
        results = []
        for limit in (1, 25):
            db.expunge_all(); statements.clear()
            response = client.get(f"/api/v1/admin/flood-events/history?summary=true&limit={limit}")
            assert response.status_code == 200
            assert len(response.json()) == limit
            assert len(statements) <= 7, statements
            assert not any(s.lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE"} for s in statements)
            results = response.json()
        for row in results:
            assert row["evidence_count"] == row["supporting_report_count"] == row["reporter_count"] == 1
            assert "contributors" not in row["zones"][0]
            assert row["zones"][0]["geometry"]["type"] == "Polygon"
        first = results[0]
        metrics = get_event_metrics(db, db.get(models.FloodEvent, first["id"]))
        assert all(first[key] == value for key, value in metrics.items())
        page = client.get("/api/v1/admin/flood-events/history?summary=true&limit=250&page=1&page_size=20")
        assert page.status_code == 200 and page.json()["total"] == 25 and len(page.json()["items"]) == 20
    finally:
        app.dependency_overrides.pop(deps.get_current_active_admin, None)
        app.dependency_overrides.pop(get_db, None)
        sql_event.remove(connection, "before_cursor_execute", record)


def test_history_pages_are_bounded_stable_and_filter_before_paging(isolated_db):
    db, staff = isolated_db
    now = datetime.now(timezone.utc)
    events = []
    for index in range(23):
        item = models.FloodEvent(status=models.FloodEventStatus.ENDED, verified_at=now,
            ended_at=now, peak_severity=models.ReportSeverity.MEDIUM)
        db.add(item); db.flush()
        db.add(models.FloodEventLocation(event_id=item.id, location_type=models.FloodEventLocationType.ROAD,
            display_name=f"Page road {index}", normalized_name=f"page road {index}"))
        db.add(models.FloodEventLocation(event_id=item.id, location_type=models.FloodEventLocationType.CITY,
            display_name="Pasig", normalized_name="pasig"))
        if index % 3 == 0:
            db.add(models.FloodEventLocation(event_id=item.id, location_type=models.FloodEventLocationType.BARANGAY,
                display_name="Maybunga", normalized_name="maybunga"))
        events.append(item)
    db.commit()
    ids = [item.id for item in reversed(events)]
    first = list_flood_event_history(db=db, current_user=staff, page=1, limit=250)
    second = list_flood_event_history(db=db, current_user=staff, page=2, limit=250)
    assert first.total == second.total == 23 and first.pages == 2 and first.page_size == 20
    assert [item["id"] for item in first.items] == ids[:20]
    assert [item["id"] for item in second.items] == ids[20:]
    assert list_flood_event_history(db=db, current_user=staff, page=999).page == 2
    assert list_flood_event_history(db=db, current_user=staff, page=1, focus_event_id=ids[-1]).page == 2
    limited = list_flood_event_history(db=db, current_user=staff, page=2, limit=21)
    assert limited.total == 21 and len(limited.items) == 1
    multiple = list_flood_event_history(db=db, current_user=staff, page=2, page_size=5, multiple_places=True)
    assert multiple.total == 8 and len(multiple.items) == 3
    assert len(list_flood_event_history(db=db, current_user=staff, multiple_places=True)) == 8
    filtered = list_flood_event_history(db=db, current_user=staff, page=3, road="Page road 22")
    assert filtered.page == filtered.pages == filtered.total == 1 and filtered.items[0]["id"] == ids[0]
    empty = list_flood_event_history(db=db, current_user=staff, page=2, search="absent")
    assert empty.page == empty.pages == 1 and empty.total == 0 and empty.items == []


@pytest.mark.parametrize("parameters", [{"page": 0}, {"page_size": 0}, {"page_size": 21}, {"focus_event_id": 0}])
def test_history_page_validation_does_not_read_storage(parameters):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as error:
        list_flood_event_history(db=SimpleNamespace(), current_user=SimpleNamespace(), **parameters)
    assert error.value.status_code == 422


def test_history_heatmap_matches_filtered_records_and_preserves_zone_state(isolated_db):
    db, staff = isolated_db
    now = datetime.now(timezone.utc)
    events = []
    for index, severity in enumerate([models.ReportSeverity.LOW, models.ReportSeverity.EXTREME]):
        item = models.FloodEvent(status=models.FloodEventStatus.ACTIVE if index == 0 else models.FloodEventStatus.ENDED,
            verified_at=now, peak_severity=severity, ended_at=now if index else None)
        db.add(item); db.flush()
        polygon = box(121.08,14.57,121.081,14.571)
        geometry = polygon if index == 0 else Polygon(polygon.exterior.coords,
            holes=[box(121.0802,14.5702,121.0808,14.5708).exterior.coords])
        db.add(models.FloodAvoidanceZone(event_id=item.id, geometry=from_shape(geometry,srid=4326),
            is_active=index == 0, curated_by_admin_id=staff.id))
        db.add(models.FloodEventLocation(event_id=item.id, location_type=models.FloodEventLocationType.ROAD,
            display_name=f"Road {index}", normalized_name=f"road {index}"))
        events.append(item)
    db.commit()
    zones = db.query(models.FloodAvoidanceZone).order_by(models.FloodAvoidanceZone.id).all()
    original = [(z.id, z.is_active, z.updated_at, bytes(z.geometry.data)) for z in zones]
    statements = []
    def record(_connection, _cursor, statement, _parameters, _context, _many): statements.append(statement)
    connection = db.connection()
    sql_event.listen(connection, "before_cursor_execute", record)
    try:
        all_records = list_flood_event_history(db=db, current_user=staff)
        assert len(all_records) == 2
        page = list_flood_event_history(db=db, current_user=staff, page=1, page_size=1)
        assert page.total == page.pages == 2 and len(page.items) == 1
        for item in all_records:
            assert len(item["heatmap_features"]) == len(item["zones"]) == 1
            feature = item["heatmap_features"][0]
            assert feature["properties"] == {"event_id": item["id"], "zone_id": item["zones"][0]["id"],
                "weight": 1 if item["peak_severity"] == "low" else 5}
        ended = list_flood_event_history(db=db, current_user=staff, status_filter="ended", severity="extreme", road="Road 1")
        assert len(ended) == 1 and ended[0]["id"] == events[1].id
        assert len(ended[0]["zones"][0]["geometry"]["coordinates"]) == 2
        assert len(list_flood_event_history(db=db, current_user=staff, limit=1)) == 1
        assert list_flood_event_history(db=db, current_user=staff, road="unknown") == []
        db.expire_all()
        assert [(z.id,z.is_active,z.updated_at,bytes(z.geometry.data)) for z in zones] == original
        assert not any(s.lstrip().split()[0].upper() in {"INSERT","UPDATE","DELETE"} for s in statements)
    finally:
        sql_event.remove(connection, "before_cursor_execute", record)
