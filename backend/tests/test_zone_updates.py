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


def editor_selection(**changes):
    from app.schemas.zone_update import ZoneObservationEditorRequest
    return ZoneObservationEditorRequest(fields=["depth"], reason="Verified the bridge approach against the attached evidence.", **changes)


def wet_payload(**changes):
    return ZoneObservationCreate(request_id=uuid4(), condition="still_flooded", observed_location="Bridge approach",
        description="Water is waist deep along the entire bridge.", depth="waist", **changes)


def test_individual_authors_and_repeat_author_are_never_combined(evidence_db):
    db, staff, witness, zone = evidence_db
    authors = [witness]
    for number in range(2):
        author = models.User(username=f"witness-{number}", email=f"witness-{number}@example.invalid", hashed_password="fixture", role_id=witness.role_id)
        db.add(author); authors.append(author)
    db.commit()
    ids = [service.submit(db, zone.id, author, wet_payload(), [])["id"] for author in [*authors, witness]]
    result = service.list_updates(db, zone.id, staff, 50, None)["updates"]
    assert len(result) == 4 and len({row["author_id"] for row in result}) == 3
    assert [row["id"] for row in result] == list(reversed(ids))
    service.review(db, zone.id, ids[1], staff, ZoneObservationReview(decision="dismissed", note="This witness observed a different street."))
    assert service.counts(db, [zone.id], staff) == {zone.id: 3}
    assert sum(row["review_state"] == "dismissed" for row in service.list_updates(db, zone.id, staff, 50, None)["updates"]) == 1


def test_editor_is_read_only_until_successful_atomic_save(evidence_db):
    from app.schemas.report import FloodAvoidanceZoneUpdate
    from app.services.zone_editor_service import save_zone
    db, staff, witness, zone = evidence_db
    row = service.submit(db, zone.id, witness, wet_payload(), [])
    before_version = zone.updated_at
    proposed = service.editor_proposal(db, zone.id, row["id"], staff, editor_selection())
    assert proposed["patch"] == {"depth_override": "waist", "severity_override": "high"}
    assert zone.depth == "knee" and zone.updated_at == before_version
    assert service.list_updates(db, zone.id, staff, 50, None)["updates"][0]["applications"] == []
    saved = save_zone(db, zone.id, staff, FloodAvoidanceZoneUpdate(**proposed["patch"],
        expected_updated_at=proposed["expected_updated_at"], community_update=proposed["community_update"]))
    assert saved.depth == "waist" and saved.severity == "high" and saved.updated_at != before_version
    result = service.list_updates(db, zone.id, staff, 50, None)["updates"][0]
    assert result["review_state"] == "pending"  # application and review remain distinct
    assert result["applications"][0]["fields"] == ["depth"]
    audit = db.scalar(select(AuditLog).where(AuditLog.action_type == "UPDATE_ZONE", AuditLog.target_id == zone.id))
    assert audit.metadata_json["before"]["depth"] == "knee"
    assert audit.metadata_json["after"]["depth"] == "waist"


def test_version_conflict_no_change_and_audit_failure_leave_no_application(evidence_db, monkeypatch):
    from app.schemas.report import FloodAvoidanceZoneUpdate
    from app.services import zone_editor_service as editor
    from sqlalchemy.exc import SQLAlchemyError
    db, staff, witness, zone = evidence_db
    row = service.submit(db, zone.id, witness, wet_payload(), [])
    proposed = service.editor_proposal(db, zone.id, row["id"], staff, editor_selection())
    stale = FloodAvoidanceZoneUpdate(**proposed["patch"], expected_updated_at=zone.updated_at-timedelta(seconds=1), community_update=proposed["community_update"])
    with pytest.raises(FollowupError, match="Another administrator"): editor.save_zone(db, zone.id, staff, stale)
    unchanged = FloodAvoidanceZoneUpdate(depth_override="knee", expected_updated_at=zone.updated_at, community_update=proposed["community_update"])
    with pytest.raises(FollowupError, match="None of the selected"): editor.save_zone(db, zone.id, staff, unchanged)
    def broken_audit(*args, **kwargs): raise SQLAlchemyError("simulated storage outage")
    monkeypatch.setattr(editor, "append_audit", broken_audit)
    with pytest.raises(FollowupError, match="could not be saved"):
        editor.save_zone(db, zone.id, staff, FloodAvoidanceZoneUpdate(**proposed["patch"], expected_updated_at=proposed["expected_updated_at"], community_update=proposed["community_update"]))
    db.refresh(zone)
    assert zone.depth == "knee"
    assert service.list_updates(db, zone.id, staff, 50, None)["updates"][0]["applications"] == []


def test_unknown_clearance_mismatched_zone_and_permission_gates(evidence_db):
    from app.schemas.zone_update import ZoneObservationEditorRequest
    from app.schemas.report import FloodAvoidanceZoneUpdate
    from app.services.zone_editor_service import save_zone
    db, staff, witness, zone = evidence_db
    dry = service.submit(db, zone.id, witness, payload(), [])
    for fields in [["depth"], ["passable_vehicles"], ["hidden_hazards"], ["geometry"]]:
        with pytest.raises(FollowupError): service.editor_proposal(db, zone.id, dry["id"], staff, ZoneObservationEditorRequest(fields=fields, reason="Scope verified"))
    with pytest.raises(FollowupError): service.editor_proposal(db, zone.id + 999, dry["id"], staff, editor_selection())
    with pytest.raises(FollowupError): service.editor_proposal(db, zone.id, dry["id"], witness, editor_selection())
    with pytest.raises(FollowupError): save_zone(db, zone.id, witness, FloodAvoidanceZoneUpdate(depth_override="waist"))
    role = models.Role(name="Zone-reader", permissions={"zones": "view"}); db.add(role); db.flush()
    reader = models.User(username="zone-reader", email="reader@example.invalid", hashed_password="fixture", role_id=role.id); db.add(reader); db.commit()
    assert service.list_updates(db, zone.id, reader, 50, None)["can_review"] is False
    with pytest.raises(FollowupError): save_zone(db, zone.id, reader, FloodAvoidanceZoneUpdate(depth_override="waist"))
    mine = service.submit(db, zone.id, staff, wet_payload(), [])
    with pytest.raises(FollowupError, match="own observation"): service.editor_proposal(db, zone.id, mine["id"], staff, editor_selection())


def test_dismissed_evidence_and_invalid_severity_cannot_be_applied(evidence_db):
    from app.schemas.report import FloodAvoidanceZoneUpdate
    from app.services.zone_editor_service import save_zone
    db, staff, witness, zone = evidence_db
    row = service.submit(db, zone.id, witness, wet_payload(), [])
    service.review(db, zone.id, row["id"], staff, ZoneObservationReview(decision="dismissed", note="Wrong road in description"))
    with pytest.raises(FollowupError, match="dismissed"): service.editor_proposal(db, zone.id, row["id"], staff, editor_selection())
    with pytest.raises(FollowupError, match="Severity must match"): save_zone(db, zone.id, staff, FloodAvoidanceZoneUpdate(depth_override="waist", severity_override="low"))
    db.refresh(zone); assert zone.depth == "knee"


def test_proposed_road_geometry_handoff_and_empty_survey(evidence_db, monkeypatch):
    from app.schemas.zone_update import ZoneObservationEditorRequest
    from app.schemas.report import FloodAvoidanceZoneUpdate
    from app.services.zone_editor_service import save_zone
    db, staff, witness, zone = evidence_db
    geometry = {"type":"LineString", "coordinates":[[121.08,14.57],[121.081,14.571]]}
    monkeypatch.setattr(service, "build_road_segment_preview", lambda **kw: {"coverage_geometry":geometry,"validation_status":"validated","road_type":"LOCAL","message":"Verified road proposal"})
    row = service.submit(db, zone.id, witness, wet_payload(road_start=geometry["coordinates"][0], road_end=geometry["coordinates"][1], passable_vehicles=[], hidden_hazards="yes"), [])
    selection = ZoneObservationEditorRequest(fields=["geometry", "passable_vehicles", "hidden_hazards"], reason="Road, hazards and vehicle evidence verified")
    proposed = service.editor_proposal(db, zone.id, row["id"], staff, selection)
    saved = save_zone(db, zone.id, staff, FloodAvoidanceZoneUpdate(**proposed["patch"], expected_updated_at=proposed["expected_updated_at"], community_update=proposed["community_update"]))
    assert to_shape(saved.source_geometry).geom_type == "LineString"
    assert to_shape(saved.geometry).geom_type == "Polygon"
    assert saved.passable_vehicles_override == "" and saved.hidden_hazards_override == "yes"
    assert set(service.list_updates(db, zone.id, staff, 50, None)["updates"][0]["applications"][0]["fields"]) == {"geometry", "passable_vehicles", "hidden_hazards"}


def test_editor_and_save_http_routes_use_authorized_version_and_source_projection(evidence_db):
    from app.models.report import FloodReport, ReportStatus, ReportSource
    db, staff, witness, zone = evidence_db
    report = FloodReport(raw_text="Original citizen submission", source=ReportSource.USER_REPORT,
        severity=models.ReportSeverity.MEDIUM, depth="knee", status=ReportStatus.APPROVED,
        zone_id=zone.id, user_id=witness.id, human_readable_location="Maybunga bridge")
    db.add(report); zone.admin_notes = "Operational description"; db.commit(); db.expire_all()
    row = service.submit(db, zone.id, witness, wet_payload(), [])
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: staff
    try:
        with TestClient(app) as client:
            details = client.get(f"/api/v1/admin/zones/{zone.id}")
            assert details.json()["original_report_text"] == "Original citizen submission"
            assert details.json()["report_text"] == "Operational description"
            path = f"/api/v1/admin/zones/{zone.id}/updates/{row['id']}/editor"
            response = client.post(path, json=editor_selection().model_dump(mode="json"))
            assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
            proposal = response.json()
            saved = client.put(f"/api/v1/admin/zones/{zone.id}", json={**proposal["patch"], "expected_updated_at": proposal["expected_updated_at"], "community_update": proposal["community_update"]})
            assert saved.status_code == 200 and saved.json()["depth"] == "waist"
            app.dependency_overrides[get_current_user] = lambda: witness
            assert client.post(path, json=editor_selection().model_dump(mode="json")).status_code == 403
            assert client.put(f"/api/v1/admin/zones/{zone.id}", json={"depth_override":"waist"}).status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_event_peak_timeline_and_edit_rollback_together(evidence_db, monkeypatch):
    from app.schemas.report import FloodAvoidanceZoneUpdate
    from app.services import zone_editor_service as editor
    from sqlalchemy.exc import SQLAlchemyError
    db, staff, witness, zone = evidence_db
    event = models.FloodEvent(status=models.FloodEventStatus.ACTIVE, verified_at=datetime.now(timezone.utc),
        peak_severity=models.ReportSeverity.MEDIUM, peak_depth="knee")
    db.add(event); db.flush(); zone.event_id = event.id; db.commit()
    row = service.submit(db, zone.id, witness, wet_payload(), [])
    proposed = service.editor_proposal(db, zone.id, row["id"], staff, editor_selection())
    def broken_audit(*args, **kwargs): raise SQLAlchemyError("audit outage")
    monkeypatch.setattr(editor, "append_audit", broken_audit)
    with pytest.raises(FollowupError): editor.save_zone(db, zone.id, staff, FloodAvoidanceZoneUpdate(**proposed["patch"],
        expected_updated_at=proposed["expected_updated_at"], community_update=proposed["community_update"]))
    db.refresh(zone); db.refresh(event)
    assert zone.depth == "knee" and event.peak_depth == "knee" and event.peak_severity == models.ReportSeverity.MEDIUM
    assert db.scalar(select(func.count()).select_from(models.FloodEventTimelineEntry).where(models.FloodEventTimelineEntry.event_id == event.id)) == 0
