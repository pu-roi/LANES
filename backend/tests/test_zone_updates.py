"""Schema and native PostGIS acceptance for private Active Zone evidence."""
from datetime import datetime, timedelta, timezone
from io import BytesIO
from uuid import uuid4

from fastapi import UploadFile
from fastapi.testclient import TestClient
from geoalchemy2.shape import from_shape, to_shape
from pydantic import ValidationError
import pytest
from shapely.geometry import Polygon, LineString
from starlette.datastructures import Headers
from sqlalchemy import select, func

from app import models
from app.api.deps import get_current_user
from app.core.database import get_db
from app.crud.audit import get_audit_logs
from app.crud.zone_update import OBSERVATION_ACTION
from app.main import app
from app.models.audit import AuditLog
from app.schemas.zone_update import ZoneObservationCreate, ZoneObservationReview
from app.services import zone_update_service as service
from app.services.flood_followup_service import FollowupError


def payload(**changes):
    return ZoneObservationCreate(request_id=uuid4(), condition="no_floodwater",
        observed_at=datetime.now(timezone.utc) - timedelta(minutes=1), observed_location="Eastbound bridge approach",
        description="No visible water at the bridge approach", **changes)


@pytest.mark.parametrize("changes", [
    {"depth": "knee"}, {"latitude": 14.5}, {"latitude": 200, "longitude": 121},
])
def test_invalid_clearance_and_location(changes):
    with pytest.raises(ValidationError): payload(**changes)


@pytest.mark.parametrize("clock", [datetime.now(), datetime.now(timezone.utc) + timedelta(days=1)])
def test_rejects_unknown_timezone_and_future(clock):
    with pytest.raises(ValidationError):
        ZoneObservationCreate(request_id=uuid4(), condition="still_flooded", observed_at=clock,
            observed_location="Bridge", description="Water is rising")


@pytest.fixture
def evidence_db(settings_factory):
    engine = settings_factory.kw["bind"]
    with engine.connect() as connection:
        transaction = connection.begin()
        db = settings_factory(bind=connection, join_transaction_mode="create_savepoint")
        role = models.Role(name="Zone-test-staff", permissions={"zones": "full"})
        commuter = models.Role(name="Commuter", permissions={})
        db.add_all([role, commuter]); db.flush()
        staff = models.User(username="zone-staff", email="zone-staff@example.invalid", hashed_password="fixture", role_id=role.id)
        witness = models.User(username="zone-witness", email="zone-witness@example.invalid", hashed_password="fixture", role_id=commuter.id)
        zone = models.FloodAvoidanceZone(geometry=from_shape(Polygon([(121.08,14.57),(121.081,14.57),(121.081,14.571),(121.08,14.57)]), srid=4326),
            is_active=True, name="Test bridge", depth_override="knee", severity_override=models.ReportSeverity.MEDIUM)
        db.add_all([staff,witness,zone]); db.commit()
        try: yield db, staff, witness, zone
        finally: db.close(); transaction.rollback()


def test_submit_retry_counts_review_and_private_audit(evidence_db):
    db, staff, witness, zone = evidence_db
    original = (zone.is_active, zone.depth_override, zone.updated_at, zone.expires_at)
    data = payload()
    first = service.submit(db, zone.id, witness, data, [])
    again = service.submit(db, zone.id, witness, data, [])
    assert first["id"] == again["id"]
    assert service.counts(db, [zone.id], staff) == {zone.id: 1}
    assert service.list_updates(db, zone.id, staff, 50, None)["updates"][0]["review_state"] == "pending"
    assert service.counts(db, [zone.id], staff) == {zone.id: 1}  # opening is not reviewing
    with pytest.raises(FollowupError): service.list_updates(db, zone.id, witness, 50, None)
    with pytest.raises(FollowupError): service.counts(db, [zone.id], witness)
    logs, _ = get_audit_logs(db)
    assert all(row.action_type != OBSERVATION_ACTION for row in logs)
    review = ZoneObservationReview(decision="reviewed", note="Retain zone; this covers only one spot.")
    result = service.review(db, zone.id, first["id"], staff, review)
    assert result["review_state"] == "reviewed"
    assert service.review(db, zone.id, first["id"], staff, review)["review_state"] == "reviewed"
    assert service.counts(db, [zone.id], staff) == {}
    db.refresh(zone)
    assert (zone.is_active, zone.depth_override, zone.updated_at, zone.expires_at) == original


def test_inactive_zone_upload_failure_and_self_review(evidence_db, monkeypatch):
    db, staff, witness, zone = evidence_db
    zone.is_active = False; db.commit()
    with pytest.raises(FollowupError, match="no longer active"): service.submit(db, zone.id, witness, payload(), [])
    db.rollback(); zone.is_active = True; db.commit()
    media = UploadFile(BytesIO(b"\xff\xd8\xfffixture"), filename="test.jpg", headers=Headers({"content-type":"image/jpeg"}))
    monkeypatch.setattr(service, "upload_image", lambda file: None)
    with pytest.raises(FollowupError, match="not submitted"): service.submit(db, zone.id, witness, payload(), [media])
    db.rollback()
    assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action_type == OBSERVATION_ACTION)) == 0
    mine = service.submit(db, zone.id, staff, payload(), [])
    with pytest.raises(FollowupError, match="own observation"):
        service.review(db, zone.id, mine["id"], staff, ZoneObservationReview(decision="dismissed", note="My own observation"))


def test_media_size_type_and_success(evidence_db, monkeypatch):
    db, staff, witness, zone = evidence_db
    for data, mime in [(b"<svg>unsafe</svg>", "image/svg+xml"), (b"a" * (service.MAX_BYTES + 1), "image/jpeg")]:
        file = UploadFile(BytesIO(data), filename="file", headers=Headers({"content-type":mime}))
        with pytest.raises(FollowupError): service.submit(db, zone.id, witness, payload(), [file])
        db.rollback()
    monkeypatch.setattr(service, "upload_image", lambda file: "https://example.org/evidence.jpg")
    file = UploadFile(BytesIO(b"\xff\xd8\xfffixture"), filename="photo.jpg", headers=Headers({"content-type":"image/jpeg"}))
    result = service.submit(db, zone.id, witness, payload(), [file])
    assert result["media_urls"] == ["https://example.org/evidence.jpg"]


def test_authenticated_routes_and_existing_zone_reader(evidence_db):
    db, staff, witness, zone = evidence_db
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: witness
    try:
        with TestClient(app) as client:
            data = payload().model_dump(mode="json")
            import json
            reply = client.post(f"/api/v1/zones/{zone.id}/updates", data={"body":json.dumps(data)})
            assert reply.status_code == 200
            assert reply.headers["cache-control"] == "no-store"
            assert client.get(f"/api/v1/admin/zones/{zone.id}/updates").status_code == 403
            assert client.get(f"/api/v1/zones/{zone.id}/update-context").json()["start"] is None
            app.dependency_overrides[get_current_user] = lambda: staff
            assert client.get(f"/api/v1/admin/zones/{zone.id}").status_code == 200
            assert client.get(f"/api/v1/admin/zones/{zone.id}/updates").json()["updates"][0]["condition"] == "no_floodwater"
            app.dependency_overrides.pop(get_current_user)
            assert client.post(f"/api/v1/zones/{zone.id}/updates", data={"body":json.dumps(data)}).status_code == 401
            assert client.get(f"/api/v1/zones/{zone.id}/update-context").status_code == 401
    finally: app.dependency_overrides.clear()


@pytest.mark.parametrize("road", [
    {"road_start": [121, 14]},
    {"road_start": [181, 14], "road_end": [121, 14]},
    {"road_start": [121, 14], "road_end": [121, 14]},
    {"road_start": [float("nan"), 14], "road_end": [121, 14]},
])
def test_invalid_proposed_endpoints(road):
    with pytest.raises(ValidationError): payload(**road)


def test_zone_road_context_and_proposed_extent_without_inferred_clock(evidence_db, monkeypatch):
    db, staff, witness, zone = evidence_db
    zone.source_geometry = from_shape(LineString([(121.08, 14.57), (121.081, 14.571)]), srid=4326)
    db.commit()
    context = service.update_context(db, zone.id, witness)
    assert context["start"] == [121.08, 14.57]
    assert context["end"] == [121.081, 14.571]
    original_geometry = to_shape(zone.geometry).wkt
    calls = []
    def preview(**kwargs):
        calls.append(kwargs)
        return {"coverage_geometry": {"type": "LineString", "coordinates": [kwargs["start"], kwargs["end"]]},
            "validation_status": "validated", "road_type": "LOCAL", "message": "Verified proposed road"}
    monkeypatch.setattr(service, "build_road_segment_preview", preview)
    data = ZoneObservationCreate(request_id=uuid4(), condition="still_flooded", depth="waist",
        description="Flood now extends farther along this road", road_start=context["start"],
        road_end=[121.082,14.572], start_label="Bridge start", end_label="New end")
    response = service.submit(db, zone.id, witness, data, [])
    assert response["observed_at"] is None and response["observation_time_recorded"] is False
    assert response["proposed_extent"]["geometry"]["coordinates"][-1] == [121.082,14.572]
    assert calls[0]["end"] == [121.082,14.572]
    assert service.list_updates(db, zone.id, staff, 50, None)["updates"][0]["road_end"] == [121.082,14.572]
    db.refresh(zone)
    assert to_shape(zone.geometry).wkt == original_geometry
    assert zone.depth_override == "knee"


def test_proposed_extent_preview_failure_preserves_no_partial_observation(evidence_db, monkeypatch):
    db, staff, witness, zone = evidence_db
    def unavailable(**kwargs): raise RuntimeError("Road service unavailable")
    monkeypatch.setattr(service, "build_road_segment_preview", unavailable)
    data = payload(road_start=[121.08,14.57], road_end=[121.082,14.572])
    with pytest.raises(FollowupError, match="not submitted"):
        service.submit(db, zone.id, witness, data, [])
    db.rollback()
    assert service.counts(db, [zone.id], staff) == {}


def test_restricted_staff_conflicting_retry_and_wrong_zone(evidence_db):
    db, staff, witness, zone = evidence_db
    data = payload()
    submitted = service.submit(db, zone.id, witness, data, [])
    changed = data.model_copy(update={"description": "Changed claim using the same request identifier"})
    with pytest.raises(FollowupError, match="different details"): service.submit(db, zone.id, witness, changed, [])
    db.rollback()
    with pytest.raises(FollowupError, match="not found"):
        service.review(db, zone.id + 1000, submitted["id"], staff, ZoneObservationReview(decision="reviewed", note="Wrong target"))
    db.rollback()
    staff.role.permissions = {"zones": "view"}; db.commit()
    assert service.list_updates(db, zone.id, staff, 50, None)["can_review"] is False
    with pytest.raises(FollowupError, match="Spatial Operations"):
        service.review(db, zone.id, submitted["id"], staff, ZoneObservationReview(decision="reviewed", note="View only role"))
