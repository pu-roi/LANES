"""Native case evidence, HTTP access, immutable persistence and follow-up acceptance."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from geoalchemy2.shape import from_shape
from pydantic import ValidationError
import pytest
from shapely.geometry import LineString, Polygon
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app import models
from app.api.deps import get_current_user
from app.core.database import get_db
from app.crud.audit import get_audit_logs
from app.crud.flood_review_suggestion import SUGGESTION_ACTION
from app.main import app
from app.models.audit import AuditLog
from app.schemas.flood_followup import FloodFollowupCreate, FloodFollowupReviewCreate
from app.schemas.flood_review_suggestion import ReviewSuggestionCreate
from app.schemas.zone_update import ZoneObservationCreate, ZoneObservationReview
from app.services import flood_followup_service as followups
from app.services import flood_review_suggestion_service as service
from app.services import zone_update_service as updates
from app.services.citizen_approval_service import record_observation
from test_operational_settings_postgres import isolated_db, citizen, report


@pytest.fixture
def case_db(isolated_db):
    db, staff = isolated_db
    owner = citizen(db, staff.role_id)
    other = citizen(db, staff.role_id)
    item = report(db, owner)
    record_observation(db, item, observed_at=datetime.now(timezone.utc) - timedelta(hours=2), road_validated=True, media_hashes=[])
    return db, staff, owner, other, item


def request(**changes):
    return ReviewSuggestionCreate(request_id=uuid4(), acknowledge_research_limitations=True,
        assume_continuous_wet=True).model_copy(update=changes)


def observation(condition="still_flooded", **changes):
    data = dict(request_id=uuid4(), condition=condition,
        observed_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        evidence_text="I checked the same road section and recorded its water condition.",
        same_location_confirmed=True)
    return FloodFollowupCreate(**{**data, **changes})


def review(decision="accepted"):
    return FloodFollowupReviewCreate(decision=decision, evidence_text="Independent source and saved road section checked.", same_location_verified=True)


def count(db, action=SUGGESTION_ACTION):
    return db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action_type == action))


def test_case_uses_observation_not_submission_and_keeps_operations(case_db):
    db, staff, owner, _, item = case_db
    original = (item.status, item.updated_at, item.zone_id, item.event_id, owner.profile.trust_score)
    first = service.issue_suggestion(db, item.id, staff, request())
    assert first.state == "scheduled"
    saved = first.suggestion
    assert saved.reference.observed_at < saved.reference.available_at < saved.issued_at
    assert saved.model.model_sha256 and saved.model.learns_depth_or_location_effects is False
    assert saved.suggested_review_at > saved.issued_at
    assert len(saved.quantiles) == 3
    assert saved.changes_status_expiry_or_routing is False
    db.refresh(item); db.refresh(owner.profile)
    assert (item.status, item.updated_at, item.zone_id, item.event_id, owner.profile.trust_score) == original
    assert service.get_case(db, item.id, staff).suggestion == saved
    logs, _ = get_audit_logs(db)
    assert not any(row.action_type == SUGGESTION_ACTION for row in logs)
    assert get_audit_logs(db, action_type=SUGGESTION_ACTION) == ([], 0)


def test_retry_keeps_calculation_and_conflicts_on_changed_request(case_db):
    db, staff, _, other, item = case_db
    payload = request()
    first = service.issue_suggestion(db, item.id, staff, payload)
    assert service.issue_suggestion(db, item.id, staff, payload).suggestion == first.suggestion
    assert count(db) == 1
    for actor, data in [(other, payload), (staff, payload.model_copy(update={"assume_continuous_wet": False}))]:
        with pytest.raises(followups.FollowupError) as error:
            service.issue_suggestion(db, item.id, actor, data)
        assert error.value.status_code == 409
        db.rollback()
    item.geometry = from_shape(LineString([(121.1, 14.57), (121.11, 14.571)]), srid=4326)
    db.commit()
    retried = service.issue_suggestion(db, item.id, staff, payload)
    assert retried.suggestion == first.suggestion and retried.state == "evidence_changed"
    assert not retried.can_issue and count(db) == 1


@pytest.mark.parametrize("problem", ["missing_clock", "naive_clock", "future_clock", "wrong_owner", "wrong_geometry", "unvalidated", "outside_city", "outside_barangay", "rejected", "old_age"])
def test_abstains_without_fabricating_evidence(case_db, problem):
    db, staff, _, _, item = case_db
    row = db.scalar(select(AuditLog).where(AuditLog.action_type == "CITIZEN_OBSERVATION", AuditLog.target_id == item.id))
    data = dict(row.metadata_json)
    if problem == "missing_clock": data["observed_at"] = None
    if problem == "naive_clock": data["observed_at"] = "2026-10-07T08:00:00"
    if problem == "future_clock": data["observed_at"] = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    if problem == "wrong_owner": data["user_id"] = -1
    if problem == "wrong_geometry": data["geometry_sha256"] = "wrong"
    if problem == "unvalidated": data["road_validated"] = False
    if problem == "outside_city": item.city = "Quezon City"
    if problem == "outside_barangay": item.barangay = "Unsupported"
    if problem == "rejected": item.status = models.ReportStatus.REJECTED
    if problem == "old_age": data["observed_at"] = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
    row.metadata_json = data; db.commit()
    with pytest.raises(followups.FollowupError) as error:
        service.issue_suggestion(db, item.id, staff, request())
    assert error.value.status_code == 409
    db.rollback()
    assert count(db) == 0


def test_followup_retry_owner_review_export_and_provenance(case_db):
    db, staff, owner, other, item = case_db
    payload = observation()
    first = followups.submit_followup(db, item.id, owner, payload)
    assert first.original_observed_at is not None and first.original_available_at is not None
    assert first.review_state == "pending" and not first.model_admitted
    assert followups.submit_followup(db, item.id, owner, payload).id == first.id
    with pytest.raises(followups.FollowupError) as error:
        followups.list_owner_followups(db, item.id, other)
    assert error.value.status_code == 404
    with pytest.raises(followups.FollowupError) as error:
        followups.review_followup(db, first.id, owner, review())
    assert error.value.status_code == 403
    db.rollback()
    with pytest.raises(followups.FollowupError):
        service.issue_suggestion(db, item.id, staff, request())
    db.rollback()
    accepted = followups.review_followup(db, first.id, staff, review())
    assert accepted.review_state == "accepted"
    with pytest.raises(followups.FollowupError) as error:
        followups.review_followup(db, first.id, staff, review())
    assert error.value.status_code == 409
    db.rollback()
    exported = followups.export_staff_followups(db, staff)
    assert not exported.training_admitted and exported.follow_ups[0].id == first.id
    case = service.issue_suggestion(db, item.id, staff, request())
    assert case.suggestion.latest_wet.audit_id == first.id
    assert case.suggestion.reference.audit_id == first.original_observation_audit_id
    assert case.suggestion.latest_wet.review_id == accepted.review.id
    assert all(row.action_type not in {"FLOOD_FOLLOWUP_OBSERVATION", "FLOOD_FOLLOWUP_REVIEW", SUGGESTION_ACTION} for row in get_audit_logs(db)[0])


def test_missing_original_clock_uses_accepted_timed_wet_followup(case_db):
    db, staff, owner, _, item = case_db
    original = db.scalar(select(AuditLog).where(AuditLog.action_type == "CITIZEN_OBSERVATION", AuditLog.target_id == item.id))
    original.metadata_json = {**original.metadata_json, "observed_at": None}; db.commit()
    assert not service.get_case(db, item.id, staff).can_issue
    followup = followups.submit_followup(db, item.id, owner, observation())
    followups.review_followup(db, followup.id, staff, review())
    saved = service.issue_suggestion(db, item.id, staff, request()).suggestion
    assert saved.reference.audit_id == followup.id and saved.reference.provenance == "accepted_owner_followup"


@pytest.mark.parametrize("change", ["geometry", "event", "zone", "place"])
def test_changed_correspondence_cannot_accept_old_followup(case_db, change):
    db, staff, owner, _, item = case_db
    first = followups.submit_followup(db, item.id, owner, observation())
    if change == "geometry": item.geometry = from_shape(LineString([(121.08, 14.58), (121.081, 14.581)]), srid=4326)
    if change == "place": item.human_readable_location = "Different road"
    if change == "event":
        event = models.FloodEvent(peak_severity=models.ReportSeverity.MEDIUM); db.add(event); db.flush(); item.event_id = event.id
    if change == "zone":
        zone = models.FloodAvoidanceZone(geometry=from_shape(Polygon([(121.08,14.57),(121.081,14.57),(121.081,14.571),(121.08,14.57)]), srid=4326)); db.add(zone); db.flush(); item.zone_id = zone.id
    db.commit()
    with pytest.raises(followups.FollowupError) as error: followups.review_followup(db, first.id, staff, review())
    assert error.value.status_code == 409
    db.rollback()
    assert followups.list_owner_followups(db, item.id, owner).follow_ups[0].review_state == "pending"


def test_later_followup_invalidates_saved_suggestion_and_subsidence_needs_clearance(case_db):
    db, staff, owner, _, item = case_db
    first = service.issue_suggestion(db, item.id, staff, request())
    obs = followups.submit_followup(db, item.id, owner, observation("subsided"))
    pending = service.get_case(db, item.id, staff)
    assert pending.state == "followup_received" and not pending.can_issue
    followups.review_followup(db, obs.id, staff, review())
    current = service.get_case(db, item.id, staff)
    assert current.state == "evidence_changed" and not current.can_issue
    assert current.suggestion == first.suggestion
    assert item.status == models.ReportStatus.PENDING  # accepting evidence is not clearance


def test_due_time_queues_latest_only_without_clearing(case_db, monkeypatch):
    db, staff, _, _, item = case_db
    first = service.issue_suggestion(db, item.id, staff, request())
    second = service.issue_suggestion(db, item.id, staff, request())
    assert second.suggestion.id > first.suggestion.id
    instant = second.suggestion.suggested_review_at + timedelta(minutes=1)
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None): return instant
    monkeypatch.setattr(service, "datetime", Clock)
    queue = service.review_queue(db, staff, limit=1)
    assert queue.cases[0].state == "due" and queue.cases[0].suggestion.id == second.suggestion.id
    assert queue.next_before_id is None
    assert service.review_queue(db, staff, before_id=second.suggestion.id, actionable_only=False).cases == []
    assert item.status == models.ReportStatus.PENDING


def test_untimed_public_zone_update_is_review_signal_not_wet_reference(case_db):
    db, staff, owner, _, item = case_db
    zone = models.FloodAvoidanceZone(geometry=from_shape(Polygon([(121.08,14.57),(121.081,14.57),(121.081,14.571),(121.08,14.57)]), srid=4326), is_active=True)
    db.add(zone); db.flush(); item.zone_id = zone.id; db.commit()
    original = (zone.is_active, zone.updated_at, zone.expires_at)
    first = service.issue_suggestion(db, item.id, staff, request())
    update = updates.submit(db, zone.id, owner, ZoneObservationCreate(request_id=uuid4(), condition="no_floodwater", observed_location="Same reported road", description="The road has no visible water now."), [])
    current = service.get_case(db, item.id, staff)
    assert current.state == "followup_received" and not current.can_issue
    assert current.reference == first.reference
    assert service.review_queue(db, staff).cases[0].report_id == item.id
    updates.review(db, zone.id, update["id"], staff, ZoneObservationReview(decision="reviewed", note="Partial evidence checked."))
    assert service.get_case(db, item.id, staff).state == "followup_received"
    assert (zone.is_active, zone.updated_at, zone.expires_at) == original


def test_evidence_expiry_keeps_review_signal_without_claiming_clearance(case_db, monkeypatch):
    db, staff, _, _, item = case_db
    now = datetime.now(timezone.utc)
    zone = models.FloodAvoidanceZone(geometry=from_shape(Polygon([(121.08,14.57),(121.081,14.57),(121.081,14.571),(121.08,14.57)]), srid=4326), is_active=True, expires_at=now + timedelta(minutes=10))
    db.add(zone); db.flush(); item.zone_id = zone.id; db.commit()
    saved = service.issue_suggestion(db, item.id, staff, request()).suggestion
    instant = now + timedelta(minutes=11)
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None): return instant
    monkeypatch.setattr(service, "datetime", Clock)
    case = service.get_case(db, item.id, staff)
    assert case.state == "evidence_stale" and not case.can_issue
    assert case.suggestion == saved and service.review_queue(db, staff).cases[0].state == "evidence_stale"
    assert zone.is_active and zone.expires_at == now + timedelta(minutes=10)


@pytest.mark.parametrize("permission,role_name,active", [("view", "Staff", True), ("full", "Commuter", True), ("none", "Staff", True), ("full", "Staff", False)])
def test_http_permissions_and_private_headers(case_db, permission, role_name, active):
    db, staff, _, _, item = case_db
    staff.role.permissions = {"reports": permission}; staff.role.name = role_name; staff.is_active = active; db.commit()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: staff
    try:
        with TestClient(app) as client:
            path = f"/api/v1/admin/reports/{item.id}/review-suggestion"
            allowed = permission == "view" and role_name != "Commuter" and active
            response = client.get(path)
            assert response.status_code == (200 if allowed else 403)
            assert response.headers["cache-control"] == "no-store"
            assert client.post(path, json=request().model_dump(mode="json")).status_code == 403
            assert client.get("/api/v1/admin/flood-review-suggestions").status_code == (200 if allowed else 403)
            app.dependency_overrides.pop(get_current_user)
            assert client.get(path).status_code == 401
    finally: app.dependency_overrides.clear()


def test_http_model_storage_errors_are_visible_and_atomic(case_db, monkeypatch):
    db, staff, _, _, item = case_db
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: staff
    try:
        with TestClient(app) as client:
            path = f"/api/v1/admin/reports/{item.id}/review-suggestion"
            monkeypatch.setenv("LANES_FLOOD_DURATION_MODEL_SHA256", "wrong")
            assert client.post(path, json=request().model_dump(mode="json")).status_code == 503
            assert count(db) == 0
            monkeypatch.delenv("LANES_FLOOD_DURATION_MODEL_SHA256")
            monkeypatch.setattr(service.evidence_store, "append_audit", lambda *args, **kwargs: (_ for _ in ()).throw(SQLAlchemyError("private details")))
            response = client.post(path, json=request().model_dump(mode="json"))
            assert response.status_code == 503 and "private details" not in response.text
            assert count(db) == 0
    finally: app.dependency_overrides.clear()


def test_followup_http_owner_staff_export_and_immutable_review(case_db):
    db, staff, owner, other, item = case_db
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: owner
    try:
        with TestClient(app) as client:
            path = f"/api/v1/reports/{item.id}/follow-ups"
            payload = observation().model_dump(mode="json")
            response = client.post(path, json=payload)
            assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
            fid = response.json()["id"]
            assert client.post(path, json=payload).json()["id"] == fid
            assert client.get(path).json()["follow_ups"][0]["id"] == fid
            app.dependency_overrides[get_current_user] = lambda: other
            assert client.get(path).status_code == 404
            app.dependency_overrides[get_current_user] = lambda: staff
            review_path = f"/api/v1/admin/flood-follow-ups/{fid}/review"
            assert client.get("/api/v1/admin/flood-follow-ups?limit=1").json()["follow_ups"][0]["id"] == fid
            assert client.post(review_path, json=review().model_dump(mode="json")).status_code == 200
            assert client.post(review_path, json=review().model_dump(mode="json")).status_code == 409
            exported = client.get("/api/v1/admin/flood-follow-ups/export").json()
            assert not exported["training_admitted"] and exported["follow_ups"][0]["review_state"] == "accepted"
            staff.role.permissions = {"reports":"view"}; db.commit()
            assert client.get("/api/v1/admin/flood-follow-ups/export").status_code == 200
            assert client.post(review_path, json=review().model_dump(mode="json")).status_code == 403
    finally: app.dependency_overrides.clear()


def test_queue_pagination_preserves_empty_filtered_page(case_db):
    db, staff, owner, _, item = case_db
    old = service.issue_suggestion(db, item.id, staff, request())
    second_report = report(db, owner)
    record_observation(db, second_report, observed_at=datetime.now(timezone.utc) - timedelta(hours=1), road_validated=True, media_hashes=[])
    new = service.issue_suggestion(db, second_report.id, staff, request())
    obs = followups.submit_followup(db, item.id, owner, observation())
    first_page = service.review_queue(db, staff, limit=1)
    assert first_page.cases == [] and first_page.next_before_id == new.suggestion.id
    page = service.review_queue(db, staff, limit=1, before_id=first_page.next_before_id)
    assert page.cases[0].report_id == item.id and page.cases[0].suggestion.id == old.suggestion.id
    assert page.next_before_id is None and obs.id > new.suggestion.id


@pytest.mark.parametrize("data", [{"assume_continuous_wet": "yes"}, {"acknowledge_research_limitations": 1}, {"reference_at": "2026-10-07T00:00:00Z"}])
def test_client_cannot_inject_evidence_or_coerce_assumptions(data):
    with pytest.raises(ValidationError): ReviewSuggestionCreate.model_validate({**request().model_dump(mode="json"), **data})


def test_concurrent_followup_submission_and_suggestion_retry(settings_factory):
    # Committed disposable fixtures are required for two independent connections.
    with settings_factory() as db:
        role = models.Role(name="concurrency-" + uuid4().hex, permissions={"reports":"full"})
        db.add(role); db.commit()
        staff = citizen(db, role.id); owner = citizen(db, role.id)
        item = report(db, owner)
        record_observation(db, item, observed_at=datetime.now(timezone.utc)-timedelta(hours=1), road_validated=True, media_hashes=[])
        report_id, owner_id, staff_id = item.id, owner.id, staff.id
    payload = observation()
    def submit(_):
        with settings_factory() as db:
            return followups.submit_followup(db, report_id, db.get(models.User, owner_id), payload).id
    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(submit, range(2)))
    assert ids[0] == ids[1]
    with settings_factory() as db:
        followups.review_followup(db, ids[0], db.get(models.User, staff_id), review())
    suggestion_payload = request()
    def issue(_):
        with settings_factory() as db:
            return service.issue_suggestion(db, report_id, db.get(models.User, staff_id), suggestion_payload).suggestion
    with ThreadPoolExecutor(max_workers=2) as pool:
        saved = list(pool.map(issue, range(2)))
    assert saved[0] == saved[1]
