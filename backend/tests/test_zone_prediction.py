"""Native spatial resolution, recorded clocks, reviewed links and read-only HTTP."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient
from geoalchemy2.shape import from_shape
import pytest
from shapely.geometry import LineString, box, mapping
from sqlalchemy import func, select

from app import models
from app.api.deps import get_current_user
from app.crud.news_publication import reserve_decision_id
from app.core.database import get_db
from app.main import app
from app.models.audit import AuditLog
from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimZoneLink
from app.schemas.news_publication import NewsDecisionSnapshot, PublicNewsAlert
from app.services.flood_location_service import get_flood_location_provider
from app.services.citizen_approval_service import record_observation
from app.services.flood_followup_service import FollowupError
from app.services import zone_prediction_service as service
from test_operational_settings_postgres import isolated_db, citizen, report


def geometry(barangay="Maybunga"):
    provider = get_flood_location_provider()
    polygon = next(poly for record, poly in provider.records.values() if record.barangay == barangay)
    point = polygon.representative_point()
    square = box(point.x-0.0001, point.y-0.0001, point.x+0.0001, point.y+0.0001)
    assert polygon.covers(square)
    return square, LineString([(point.x-0.00002, point.y), (point.x+0.00002, point.y)])


@pytest.fixture
def zone_db(isolated_db):
    db, staff = isolated_db
    now = datetime.now(timezone.utc)
    area, line = geometry()
    event = models.FloodEvent(peak_severity=models.ReportSeverity.MEDIUM)
    db.add(event); db.flush()
    zone = models.FloodAvoidanceZone(geometry=from_shape(area, srid=4326), event_id=event.id,
        is_active=True, expires_at=now+timedelta(hours=2), created_at=now-timedelta(hours=4))
    db.add(zone); db.flush()
    owner = citizen(db, staff.role_id)
    item = report(db, owner, geometry=line)
    item.zone_id, item.event_id, item.status = zone.id, event.id, models.ReportStatus.APPROVED
    db.commit()
    record_observation(db, item, observed_at=now-timedelta(hours=1), road_validated=True, media_hashes=[])
    observation = db.scalar(select(AuditLog).where(AuditLog.action_type == "CITIZEN_OBSERVATION", AuditLog.target_id == item.id))
    observation.created_at = now
    db.commit()
    return db, staff, zone, item, now


def test_automatic_spatial_evidence_prediction_is_read_only(zone_db):
    db, staff, zone, item, now = zone_db
    original = (zone.is_active, zone.expires_at, zone.updated_at, item.updated_at,
        db.scalar(select(func.count()).select_from(AuditLog)))
    result = service.predict_zone(db, zone.id, staff, now=now)
    assert result.state == "estimated" and result.city == "Pasig" and result.barangays == ["Maybunga"], result.reasons
    assert result.reference.observed_at == now-timedelta(hours=1) != zone.created_at
    assert len(result.quantiles) == 3 and result.continuity_assumed
    assert result.calculation.prediction_as_of_at == result.prediction_as_of_at
    assert result.calculation.elapsed_minutes == pytest.approx(60)
    assert result.calculation.quantiles[1].estimated_reported_subsidence_at == result.quantiles[1].estimated_reported_subsidence_at
    assert result.reference.report_id == item.id and result.model.model_sha256
    assert not result.changes_status_expiry_or_routing
    refreshed = service.predict_zone(db, zone.id, staff, now=now+timedelta(minutes=1))
    assert result.quantiles == refreshed.quantiles
    assert result.prediction_as_of_at == refreshed.prediction_as_of_at
    db.flush(); db.refresh(zone); db.refresh(item)
    assert original == (zone.is_active, zone.expires_at, zone.updated_at, item.updated_at,
        db.scalar(select(func.count()).select_from(AuditLog)))


def test_blank_labels_resolve_from_geometry_without_database_changes(zone_db):
    db, staff, zone, item, now = zone_db
    item.city = item.barangay = item.human_readable_location = None
    db.commit()
    assert service.predict_zone(db, zone.id, staff, now=now).state == "estimated"
    db.refresh(item)
    assert item.city is item.barangay is item.human_readable_location is None


@pytest.mark.parametrize("change", ["missing_clock", "wrong_geometry", "wrong_event", "pending", "city_conflict", "barangay_conflict", "future_clock", "old_clock"])
def test_unqualified_inputs_do_not_become_predictions(zone_db, change):
    db, staff, zone, item, now = zone_db
    row = db.scalar(select(AuditLog).where(AuditLog.action_type == "CITIZEN_OBSERVATION", AuditLog.target_id == item.id))
    if change in {"missing_clock", "future_clock", "old_clock"}:
        row.metadata_json = {**row.metadata_json, "observed_at": None if change == "missing_clock" else
            (now+timedelta(hours=1) if change == "future_clock" else now-timedelta(days=3)).isoformat()}
    if change == "wrong_geometry": item.geometry = from_shape(geometry("Ugong")[1], srid=4326)
    if change == "wrong_event": item.event_id = None
    if change == "pending": item.status = models.ReportStatus.PENDING
    if change == "city_conflict": item.city = "Quezon City"
    if change == "barangay_conflict": item.barangay = "Santolan"
    db.commit()
    result = service.predict_zone(db, zone.id, staff, now=now)
    assert result.state != "estimated" and result.reasons and not result.quantiles


def test_nearby_report_is_discovered_but_not_borrowed(zone_db):
    db, staff, zone, item, now = zone_db
    item.zone_id = None; item.status = models.ReportStatus.PENDING; db.commit()
    result = service.predict_zone(db, zone.id, staff, now=now)
    assert result.nearby_report_count == 1 and not result.reference and not result.quantiles
    assert any("reviewed same-zone" in reason for reason in result.reasons)
    db.refresh(item); assert item.zone_id is None


@pytest.mark.parametrize("barangay,transfer", [("Ugong", True), ("Santa Lucia", False)])
def test_geographic_transfer_is_explicit_and_not_claimed_as_training(zone_db, barangay, transfer):
    db, staff, zone, item, now = zone_db
    area, line = geometry(barangay)
    zone.geometry = from_shape(area, srid=4326); item.geometry = from_shape(line, srid=4326); item.barangay = barangay
    db.commit()
    record_observation(db, item, observed_at=now-timedelta(minutes=20), road_validated=True, media_hashes=[])
    result = service.predict_zone(db, zone.id, staff, now=datetime.now(timezone.utc))
    assert result.barangays == [barangay]
    assert result.state == "estimated"
    assert result.pooled_geographic_transfer == transfer
    assert bool(result.warnings) == transfer
    if transfer: assert barangay not in result.model.supported_barangays


@pytest.mark.parametrize("state", ["expired", "inactive"])
def test_lifecycle_stops_prediction_without_clearing(zone_db, state):
    db, staff, zone, _, now = zone_db
    if state == "expired": zone.expires_at = now
    else: zone.is_active = False
    db.commit()
    result = service.predict_zone(db, zone.id, staff, now=now)
    assert result.state == state and not result.quantiles
    db.refresh(zone); assert zone.is_active == (state == "expired")


def test_new_untimed_public_evidence_stops_recalculation(zone_db):
    db, staff, zone, item, now = zone_db
    db.add(AuditLog(action_type="ZONE_PUBLIC_OBSERVATION", target_table="flood_avoidance_zones",
        target_id=zone.id, admin_id=item.user_id, metadata_json={"condition": "no_floodwater"}, created_at=now))
    db.commit()
    result = service.predict_zone(db, zone.id, staff, now=now)
    assert result.state == "needs_review" and not result.quantiles
    assert any("spot report" in reason for reason in result.reasons)
    assert zone.is_active


def test_location_catalog_failure_abstains_without_text_guess(zone_db, monkeypatch):
    db, staff, zone, _, now = zone_db
    monkeypatch.setattr(service, "get_flood_location_provider", lambda: SimpleNamespace(revision="bad", error="invalid", records={}))
    zone.admin_notes = "Flood in Santolan"; db.commit()
    result = service.predict_zone(db, zone.id, staff, now=now)
    assert result.state == "unavailable" and result.barangays == []


@pytest.mark.parametrize("geometry_reason", ["staff_reviewed_footprint", "verified_incident_footprint", "estimated_road_corridor"])
def test_current_linked_news_supplies_clock_without_citizen_report(zone_db, geometry_reason):
    db, staff, zone, item, now = zone_db
    item.zone_id = None; db.commit()
    case = NewsClaimCase(revision=1); db.add(case); db.flush()
    observed = now-timedelta(minutes=30)
    decision = NewsClaimDecision(id=reserve_decision_id(db), case_id=case.id, revision=1, request_id=uuid4(), actor_kind="staff",
        actor_user_id=staff.id, operation="correct", public_state="active_zone", review_state="resolved",
        reason_code="verified_current_footprint", snapshot={}, observed_at=observed,
        expires_at=now+timedelta(hours=1), decided_at=now)
    public = PublicNewsAlert(case_id=case.id, decision_id=decision.id, revision=1, status="Active",
        location_label="Maybunga", condition_label="Reported flooding", passability_label="Unknown",
        observed_at=observed, expires_at=decision.expires_at, updated_at=now, source_title="Fixture",
        source_publisher="Fixture", source_url="https://example.com/flood", evidence_excerpt="Recorded wet observation",
        geometry_precision="operational_polygon", display_geojson=mapping(geometry()[0]), affects_routing=True)
    decision.snapshot = NewsDecisionSnapshot(request_sha256="1"*64, policy_fingerprint="2"*64,
        claim_source_id=1, input_sha256="3"*64, claim_sha256="4"*64, incident_identity="5"*64,
        article_id=1, public=public, linked_zone_ids=[zone.id], geometry_reason=geometry_reason).model_dump(mode="json")
    db.add(decision); db.flush()
    db.add(NewsClaimZoneLink(decision_id=decision.id, zone_id=zone.id, relation="created")); db.commit()
    result = service.predict_zone(db, zone.id, staff, now=now)
    if geometry_reason == "estimated_road_corridor":
        assert result.state != "estimated" and not result.quantiles
        assert result.reference is None
        assert any("No qualified observation time" in reason for reason in result.reasons)
        return
    assert result.state == "estimated" and result.reference.source_kind == "news_decision"
    case.revision = 2
    next_decision = NewsClaimDecision(case_id=case.id, revision=2, request_id=uuid4(), actor_kind="staff",
        actor_user_id=staff.id, operation="correct", public_state="active_zone", review_state="needs_review",
        reason_code="pending_current_evidence", snapshot=decision.snapshot, observed_at=observed,
        expires_at=decision.expires_at, decided_at=now)
    db.add(next_decision); db.flush()
    db.add(NewsClaimZoneLink(decision_id=next_decision.id, zone_id=zone.id, relation="supported")); db.commit()
    assert service.predict_zone(db, zone.id, staff, now=now).state == "needs_review"


def test_active_zone_reader_uses_simulated_present_without_changing_expiry(zone_db):
    from app.crud.report import get_active_avoidance_zones
    db, _, zone, _, _ = zone_db
    simulated_at = datetime(2026, 9, 24, 8, tzinfo=timezone.utc)
    zone.expires_at = simulated_at + timedelta(hours=2)
    db.commit()
    assert zone.id not in [row.id for row in get_active_avoidance_zones(db)]
    assert zone.id in [row.id for row in get_active_avoidance_zones(db, now=simulated_at)]
    assert zone.id not in [row.id for row in get_active_avoidance_zones(db, now=zone.expires_at)]
    with pytest.raises(ValueError, match="timezone offset"):
        get_active_avoidance_zones(db, now=simulated_at.replace(tzinfo=None))
    db.refresh(zone)
    assert zone.expires_at == simulated_at + timedelta(hours=2) and zone.is_active


def test_authenticated_get_needs_both_read_permissions_and_has_no_writes(zone_db):
    db, staff, zone, _, now = zone_db
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: staff
    original = db.scalar(select(func.count()).select_from(AuditLog))
    try:
        client = TestClient(app, raise_server_exceptions=False)
        path = f"/api/v1/admin/zones/{zone.id}/subsidence-prediction"
        response = client.get(path)
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        assert response.json()["state"] == "estimated"
        assert client.post(path, json={}).status_code == 405
        assert client.get("/api/v1/admin/zones/999999/subsidence-prediction").status_code == 404
        for permissions in ({"reports": "full"}, {"zones": "full"}, {}):
            staff.role.permissions = permissions; db.flush()
            assert client.get(path).status_code == 403
    finally:
        app.dependency_overrides.clear()
    assert db.scalar(select(func.count()).select_from(AuditLog)) == original


def test_official_registration_is_separate_automatic_simulation_not_wet_evidence(zone_db):
    db, staff, zone, item, now = zone_db
    item.zone_id = None
    zone.updated_at = now-timedelta(hours=3, seconds=1)
    registration = AuditLog(action_type="CREATE_OFFICIAL_ZONE", target_table="flood_avoidance_zones",
        target_id=zone.id, admin_id=staff.id, metadata_json={"zone_id": zone.id}, created_at=now-timedelta(hours=3))
    db.add(registration); db.commit()
    before = (zone.expires_at, zone.is_active, db.scalar(select(func.count()).select_from(AuditLog)))
    result = service.predict_zone(db, zone.id, staff, now=now)
    assert result.state == "unavailable" and not result.reference and not result.quantiles
    assert result.registration_simulation.status == "research_estimate"
    assert result.registration_simulation.input_provenance == "admin_registration_proxy_simulation"
    assert result.registration_simulation.reference_at == registration.created_at
    assert result.registration_simulation.calculation.elapsed_minutes == 0
    assert result.registration_simulation.calculation.reference_at == registration.created_at
    assert result.registration_audit_id == registration.id
    later = service.predict_zone(db, zone.id, staff, now=now+timedelta(minutes=1))
    assert result.registration_simulation.quantiles == later.registration_simulation.quantiles
    assert before == (zone.expires_at, zone.is_active, db.scalar(select(func.count()).select_from(AuditLog)))
    db.add(AuditLog(action_type="UPDATE_ZONE", target_table="flood_avoidance_zones", target_id=zone.id,
        admin_id=staff.id, metadata_json={}, created_at=now)); db.commit()
    assert service.predict_zone(db, zone.id, staff, now=now).registration_simulation is None
