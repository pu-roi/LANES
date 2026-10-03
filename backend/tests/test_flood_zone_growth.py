"""Actual PostGIS/API transactions, isolated by an outer rollback in local test DB."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4
import json

import httpx
import pytest
from geoalchemy2 import WKTElement
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app import models
from app.api import deps
from app.core.config import settings
from app.core.database import engine, get_db
from app.main import app
from scripts.seed_local_news_replay import require_local_test_database


@pytest.fixture
def growth_db(monkeypatch, request):
    require_local_test_database(settings.DATABASE_URL)
    from app.services import merge_service
    monkeypatch.setattr(merge_service, "trace_road_attributes", lambda *_args: None)
    connection = engine.connect()
    outer = connection.begin()
    db = Session(bind=connection, join_transaction_mode="create_savepoint")
    saved = dict(app.dependency_overrides)
    def cleanup():
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved)
        db.close()
        outer.rollback()
        connection.close()
    request.addfinalizer(cleanup)
    role = db.query(models.Role).filter(models.Role.name != "Commuter").first()
    if role is None:
        role = models.Role(name="Admin", permissions={})
        db.add(role)
        db.flush()
    token = uuid4().hex
    user = models.User(username=f"growth-{token}", email=f"growth-{token}@example.org",
        hashed_password="test-only", role_id=role.id, is_active=True)
    event = models.FloodEvent(status=models.FloodEventStatus.ACTIVE, peak_severity=models.ReportSeverity.MEDIUM,
        peak_depth="knee", verified_at=datetime.now(timezone.utc) - timedelta(hours=7))
    db.add_all([user, event])
    db.flush()
    zone = models.FloodAvoidanceZone(name="Existing supported extent", event_id=event.id,
        severity_override=models.ReportSeverity.MEDIUM, depth_override="knee", is_active=True,
        source_geometry=WKTElement("LINESTRING(121.0800 14.5700,121.0810 14.5700)", srid=4326),
        geometry=WKTElement("POLYGON((121.0799 14.5699,121.0811 14.5699,121.0811 14.5701,121.0799 14.5701,121.0799 14.5699))", srid=4326))
    db.add(zone)
    db.flush()
    report = models.FloodReport(user_id=user.id, raw_text="Flood now extends into Rosario",
        source=models.ReportSource.USER_REPORT, status=models.ReportStatus.PENDING,
        severity=models.ReportSeverity.MEDIUM, depth="knee", city="Pasig", barangay="Rosario",
        human_readable_location="Second Street", geometry=WKTElement("LINESTRING(121.0810 14.5700,121.0820 14.5700)", srid=4326))
    db.add(report)
    db.flush()
    post = models.CommunityPost(user_id=user.id, flood_report_id=report.id, content="Original flood evidence", media_urls=[])
    db.add(post)
    db.flush()
    # Establish fixture rows before each request's savepoint. The outer
    # transaction still rolls everything back when this test finishes.
    db.commit()
    original = db.scalar(select(func.ST_AsGeoJSON(zone.geometry)))
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[deps.get_current_active_admin] = lambda: user
    payload = {"primary_report_id": report.id, "merged_report_ids": [], "target_zone_id": zone.id,
        "merge_mode": "extend", "final_data": {"severity": "medium", "depth": "knee", "geometry": {
            "type": "LineString", "coordinates": [[121.081, 14.57], [121.082, 14.57]]},
            "buffer_radius": 25, "passable_vehicles": "heavy", "admin_notes": "Reviewed growth"}}
    yield SimpleNamespace(db=db, zone=zone, event=event, report=report, post=post, original=original, payload=payload)


@pytest.mark.asyncio
async def test_extension_preview_preserves_coverage_core_identity_and_repeat(growth_db):
    f = growth_db
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        preview = await client.post("/api/v1/admin/reports/merge-preview", json=f.payload)
        assert preview.status_code == 200, preview.text
        assert preview.json()["read_only"] and preview.json()["preserves_existing_coverage"]
        assert f.report.status == models.ReportStatus.PENDING
        merged = await client.post("/api/v1/admin/reports/merge", json=f.payload)
        assert merged.status_code == 200, merged.text
        f.db.refresh(f.zone)
        old = func.ST_SetSRID(func.ST_GeomFromGeoJSON(f.original), 4326)
        assert f.db.scalar(select(func.ST_Covers(f.zone.geometry, old)))
        assert json.loads(f.db.scalar(select(func.ST_AsGeoJSON(f.zone.geometry)))) == preview.json()["geometry"]
        assert f.db.scalar(select(func.ST_Length(func.ST_Transform(f.zone.source_geometry,32651)))) > 200
        assert f.report.event_id == f.event.id and f.report.zone_id == f.zone.id
        assert f.post.content == "Original flood evidence"
        assert f.db.query(models.FloodEventLocation).filter_by(event_id=f.event.id, display_name="Rosario").count() == 1
        assert (await client.post("/api/v1/admin/reports/merge", json=f.payload)).status_code == 200
        assert f.db.query(models.FloodReportModerationOutcome).filter_by(report_id=f.report.id).count() == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["corroborate", "add_section"])
async def test_evidence_link_or_separate_section_preserves_old_zone(growth_db, mode):
    f = growth_db
    f.payload["merge_mode"] = mode
    f.payload["final_data"]["geometry"]["coordinates"] = [[121.083,14.57],[121.084,14.57]]
    f.payload["final_data"].update(severity="high", depth="waist")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        result = await client.post("/api/v1/admin/reports/merge", json=f.payload)
        assert result.status_code == 200, result.text
        f.db.refresh(f.zone)
        assert f.db.scalar(select(func.ST_AsGeoJSON(f.zone.geometry))) == f.original
        assert f.report.event_id == f.event.id
        assert (f.report.zone_id != f.zone.id) == (mode == "add_section")
        assert f.zone.depth_override == "knee"
        if mode == "add_section":
            assert f.db.get(models.FloodAvoidanceZone, f.report.zone_id).depth_override == "waist"
        assert (await client.post("/api/v1/admin/reports/merge", json=f.payload)).status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", ["disconnected", "point", "empty", "one_vertex", "expired", "ended"])
async def test_invalid_growth_is_rejected_without_partial_writes(growth_db, invalid):
    f = growth_db
    if invalid == "disconnected":
        f.payload["final_data"]["geometry"]["coordinates"] = [[121.09,14.57],[121.091,14.57]]
    elif invalid == "point":
        f.payload["final_data"]["geometry"] = {"type":"Point","coordinates":[121.081,14.57]}
    elif invalid in {"empty", "one_vertex"}:
        f.payload["final_data"]["geometry"]["coordinates"] = [] if invalid == "empty" else [[121.081,14.57]]
    elif invalid == "expired":
        f.zone.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    else:
        f.event.status = models.FloodEventStatus.ENDED
        f.event.ended_at = datetime.now(timezone.utc)
    f.db.flush()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        result = await client.post("/api/v1/admin/reports/merge", json=f.payload)
        assert result.status_code in (409,422), result.text
        f.db.refresh(f.report)
        assert f.report.status == models.ReportStatus.PENDING
        assert f.db.query(models.FloodReportModerationOutcome).filter_by(report_id=f.report.id).count() == 0


def test_old_active_event_and_cross_road_zone_discovery(growth_db):
    from app.services.merge_service import find_active_zone_candidates
    f = growth_db
    assert f.zone.id in [row.zone_id for row in find_active_zone_candidates(f.report, f.db)]
    f.zone.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    f.db.flush()
    assert f.zone.id not in [row.zone_id for row in find_active_zone_candidates(f.report, f.db)]


@pytest.mark.asyncio
async def test_legacy_approval_extends_without_replacing_existing_coverage(growth_db):
    f = growth_db
    boundary = {"type": "Polygon", "coordinates": [[[121.081,14.5699],[121.082,14.5699],
        [121.082,14.5701],[121.081,14.5701],[121.081,14.5699]]]}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        result = await client.post(f"/api/v1/admin/reports/{f.report.id}/approve", json={
            "action":"MERGE", "target_zone_id":f.zone.id, "custom_geometry":boundary})
        assert result.status_code == 200, result.text
        f.db.refresh(f.zone)
        old = func.ST_SetSRID(func.ST_GeomFromGeoJSON(f.original), 4326)
        assert f.db.scalar(select(func.ST_Covers(f.zone.geometry, old)))
        assert f.report.event_id == f.event.id


@pytest.mark.asyncio
async def test_preview_requires_authentication_and_staff_role(growth_db):
    f = growth_db
    app.dependency_overrides.pop(deps.get_current_active_admin)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.post("/api/v1/admin/reports/merge-preview", json=f.payload)).status_code == 401
        app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Commuter"))
        assert (await client.post("/api/v1/admin/reports/merge-preview", json=f.payload)).status_code == 403
        assert f.report.status == models.ReportStatus.PENDING


@pytest.mark.asyncio
async def test_native_authenticated_queue_members_and_preview(growth_db):
    from app.core.security import create_access_token
    f = growth_db
    app.dependency_overrides.pop(deps.get_current_active_admin)
    headers = {"Authorization": "Bearer " + create_access_token({"sub":str(f.report.user_id)})}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test", headers=headers) as client:
        queue = await client.get("/api/v1/admin/review/items?source=user_reports")
        assert queue.status_code == 200, queue.text
        members = await client.get(f"/api/v1/admin/review/groups/user_report:{f.report.id}/members")
        assert members.status_code == 200, members.text
        assert f.report.id in [item["report_id"] for item in members.json()["items"]]
        preview = await client.post("/api/v1/admin/reports/merge-preview", json=f.payload)
        assert preview.status_code == 200, preview.text
        assert f.report.status == models.ReportStatus.PENDING


def test_report_extent_proposal_retains_branches_and_extensions():
    from app.services.merge_service import synthesize_merged_geometry
    from shapely.geometry import shape
    lines = [
        {"type":"LineString","coordinates":[[121.08,14.57],[121.081,14.57]]},
        {"type":"LineString","coordinates":[[121.081,14.57],[121.082,14.57]]},
        {"type":"LineString","coordinates":[[121.081,14.57],[121.081,14.571]]},
    ]
    proposal, _ = synthesize_merged_geometry([SimpleNamespace(geometry=g, is_bidirectional=False) for g in lines], None)
    assert proposal["type"] == "MultiLineString"
    assert all(shape(proposal).covers(shape(line)) for line in lines)


@pytest.mark.asyncio
async def test_failed_audit_rolls_back_boundary_and_report_outcome(growth_db, monkeypatch):
    from app import crud
    f = growth_db
    def fail_audit(*_args, **_kwargs):
        raise SQLAlchemyError("Test audit failure")
    monkeypatch.setattr(crud, "create_audit_log", fail_audit)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        result = await client.post("/api/v1/admin/reports/merge", json=f.payload)
        assert result.status_code == 500
        f.db.refresh(f.zone)
        f.db.refresh(f.report)
        assert f.report.status == models.ReportStatus.PENDING
        assert f.db.scalar(select(func.ST_AsGeoJSON(f.zone.geometry))) == f.original
        assert f.db.query(models.FloodReportModerationOutcome).filter_by(report_id=f.report.id).count() == 0
