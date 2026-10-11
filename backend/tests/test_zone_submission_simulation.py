"""Transient source contracts and real catalog/model; no application DB writes."""
from datetime import datetime, timedelta, timezone
import hashlib
from types import SimpleNamespace

from fastapi.testclient import TestClient
from geoalchemy2.shape import from_shape
import pytest
from shapely.geometry import LineString
from shapely.ops import unary_union

from app import models
from app.api.deps import get_current_user
from app.core.database import get_db
from app.main import app
from app.services import zone_prediction_service as service
from app.services.flood_location_service import get_flood_location_provider
from app.services.flood_followup_service import FollowupError
from app.crud import zone_update

NOW = datetime.now(timezone.utc)


@pytest.fixture
def source(monkeypatch):
    provider = get_flood_location_provider()
    polygons = [p for r,p in provider.records.values() if r.barangay in {'San Nicolas','Santo Tomas'}]
    area = unary_union(polygons)
    p = polygons[0].representative_point()
    road = LineString([(p.x-.000001,p.y),(p.x+.000001,p.y)])
    zone = models.FloodAvoidanceZone(id=18, geometry=from_shape(area,srid=4326), event_id=18,
        is_active=True, updated_at=NOW-timedelta(minutes=31), expires_at=None)
    report = models.FloodReport(id=16, zone_id=18, event_id=18, user_id=55, city='Pasig',
        barangay='San Nicolas', source=models.ReportSource.USER_REPORT, status=models.ReportStatus.APPROVED,
        geometry=from_shape(road,srid=4326), created_at=NOW-timedelta(minutes=61),
        approved_at=NOW-timedelta(minutes=31), updated_at=NOW-timedelta(minutes=31))
    original = models.AuditLog(id=164, created_at=NOW-timedelta(minutes=60), metadata_json={
        'user_id':55,'observed_at':None,'road_validated':True,
        'geometry_sha256':hashlib.sha256(road.wkb).hexdigest()})
    approval = models.AuditLog(id=166, admin_id=7, created_at=NOW-timedelta(minutes=30),
        metadata_json={'report_id':16,'zone_id':18})
    staff = SimpleNamespace(id=7,is_active=True,deleted_at=None,role=SimpleNamespace(name='Officer',permissions={'reports':'view','zones':'view'}))
    monkeypatch.setattr(service.store,'get_zone',lambda *args:zone)
    monkeypatch.setattr(service.store,'linked_reports',lambda *args:[report])
    monkeypatch.setattr(service.store,'nearby_report_count',lambda *args,**kwargs:0)
    monkeypatch.setattr(service.store,'zone_has_edits',lambda *args:False)
    monkeypatch.setattr(service.store,'submission_approval',lambda *args:approval)
    monkeypatch.setattr(service.evidence_store,'original_observation',lambda *args:original)
    monkeypatch.setattr(service.evidence_store,'report_followups',lambda *args:[])
    monkeypatch.setattr(service,'_wet_evidence',lambda *args:([],None))
    monkeypatch.setattr(service,'_pending_signal',lambda *args:False)
    monkeypatch.setattr(service,'_news_evidence',lambda *args:([],[]))
    monkeypatch.setattr(zone_update,'observations',lambda *args,**kwargs:[])
    return zone,report,original,approval,staff


def test_submission_proxy_retains_both_names_real_clocks_and_stable_forecast(source):
    zone,report,original,approval,staff=source
    result=service.predict_zone(object(),18,staff,now=NOW)
    assert result.barangays==['San Nicolas','Santo Tomas']
    assert result.location_policy=='pooled_pasig_multi_barangay'
    assert result.state=='unavailable' and result.reference is None and not result.quantiles
    sim=result.submission_simulation
    assert sim.status=='research_estimate' and sim.input_provenance=='citizen_submission_proxy_simulation'
    assert sim.reference_at==original.created_at and sim.prediction_as_of_at==approval.created_at
    assert sim.calculation.elapsed_minutes==30 and sim.pooled_geographic_transfer
    assert (result.submission_report_id,result.submission_audit_id,result.submission_approval_audit_id)==(16,164,166)
    later=service.predict_zone(object(),18,staff,now=NOW+timedelta(minutes=5))
    assert later.submission_simulation.quantiles==sim.quantiles
    assert original.metadata_json['observed_at'] is None and zone.is_active and zone.expires_at is None
    assert not sim.changes_status_expiry_or_routing and not sim.confirms_physical_dryness_or_passability


@pytest.mark.parametrize('change', ['pending','event','report_geometry','city','barangay','observed_clock',
    'source_owner','source_geometry','road_unvalidated','approval_actor','approval_zone','approval_report',
    'future_submission','report_edited','zone_edited','zone_edit_audit','owner_followup','public_update','too_old'])
@pytest.mark.parametrize('recover', [False, True])
def test_invalid_or_changed_inputs_cannot_supply_submission_simulation(source,monkeypatch,change,recover):
    zone,report,original,approval,staff=source
    if change=='pending':report.status=models.ReportStatus.PENDING
    if change=='event':report.event_id=None
    if change=='report_geometry':report.geometry=from_shape(LineString([(120,13),(120.01,13.01)]),srid=4326)
    if change=='city':report.city='Quezon City'
    if change=='barangay':report.barangay='Santolan'
    if change=='observed_clock':original.metadata_json['observed_at']=(NOW+timedelta(hours=1)).isoformat()
    if change=='source_owner':original.metadata_json['user_id']=999
    if change=='source_geometry':original.metadata_json['geometry_sha256']='changed'
    if change=='road_unvalidated':original.metadata_json['road_validated']=False
    if change=='approval_actor':approval.admin_id=None
    if change=='approval_zone':approval.metadata_json['zone_id']=17
    if change=='approval_report':approval.metadata_json['report_id']=99
    if change=='future_submission':original.created_at=NOW+timedelta(minutes=1)
    if change=='report_edited':report.updated_at=NOW
    if change=='zone_edited':zone.updated_at=NOW
    if change=='zone_edit_audit':monkeypatch.setattr(service.store,'zone_has_edits',lambda *args:True)
    if change=='owner_followup':monkeypatch.setattr(service.evidence_store,'report_followups',lambda *args:[object()])
    if change=='public_update':
        monkeypatch.setattr(zone_update,'observations',lambda *args,**kwargs:[SimpleNamespace(id=200,created_at=NOW)])
        monkeypatch.setattr(zone_update,'reviews',lambda *args:{})
    if change=='too_old':
        report.created_at=NOW-timedelta(minutes=2201);original.created_at=NOW-timedelta(minutes=2200)
    result=service.resolve_zone_prediction(object(),18,now=NOW,recover_issuance=recover)
    assert result.submission_simulation is None and not result.quantiles and result.reference is None


def test_late_submission_recovery_retains_current_checks_and_original_issuance(source):
    *_,staff=source
    original=service.predict_zone(object(),18,staff,now=NOW)
    later=NOW+timedelta(days=3)
    assert service.predict_zone(object(),18,staff,now=later).submission_simulation is None
    recovered=service.resolve_zone_prediction(object(),18,now=later,recover_issuance=True)
    assert recovered.submission_simulation.quantiles==original.submission_simulation.quantiles
    assert recovered.submission_simulation.prediction_as_of_at==original.submission_simulation.prediction_as_of_at
    assert recovered.reference is None and not recovered.changes_status_expiry_or_routing


@pytest.mark.parametrize('state',['inactive','expired'])
def test_closed_or_expired_zone_never_gets_a_proxy(source,state):
    zone,_,_,_,staff=source
    if state=='inactive':zone.is_active=False
    else:zone.expires_at=NOW
    result=service.predict_zone(object(),18,staff,now=NOW)
    assert result.state==state and result.submission_simulation is None


def test_private_route_serializes_proxy_and_keeps_read_permissions(source):
    *_,staff=source
    app.dependency_overrides[get_db]=lambda:SimpleNamespace(rollback=lambda:None)
    app.dependency_overrides[get_current_user]=lambda:staff
    try:
        client=TestClient(app)
        response=client.get('/api/v1/admin/zones/18/subsidence-prediction')
        assert response.status_code==200 and response.headers['cache-control']=='no-store'
        assert response.json()['submission_simulation']['input_provenance']=='citizen_submission_proxy_simulation'
        staff.role.permissions={'zones':'view'}
        assert client.get('/api/v1/admin/zones/18/subsidence-prediction').status_code==403
        client.close()
    finally:app.dependency_overrides.clear()
