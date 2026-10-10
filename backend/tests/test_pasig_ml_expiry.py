"""Real model deadlines and native lifecycle writes in a disposable PostGIS DB."""
from datetime import timedelta
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func, select

from app.api.deps import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.audit import AuditLog
from app.models.report import FloodEventStatus, FloodEventTimelineEntry
from app.schemas.configuration import ConfigurationUpdate
from app.services import configuration_service as settings
from app.services import pasig_ml_expiry_service as policy
from app.services.flood_event_service import expire_due_zones
from app.crud.report import get_active_avoidance_zones
from app.services.flood_routing_policy import get_active_flood_zones
from test_zone_prediction import zone_db
from test_operational_settings_postgres import isolated_db


def configure(db, staff, enabled=True, automatic=True):
    config = settings.read_configuration(db)
    config.pasig_ml_expiry_enabled, config.automatic_expiry_enabled = enabled, automatic
    revision = settings.configuration_response(db, can_edit=True).revision
    settings.save_configuration(db, ConfigurationUpdate(revision=revision, settings=config), actor_id=staff.id)


def test_model_deadline_replaces_timer_then_expires_zone_and_event(zone_db):
    db, staff, zone, report, now = zone_db
    fixed = zone.expires_at
    result = policy.apply_zone_policy(db, zone.id, now=now)
    db.commit()
    assert result['method'] in {'ml_pooled', 'ml_cross_location'}, result
    assert result['experimental'] and not result['accuracy_verified']
    assert result['expires_as'] == 'Unconfirmed' and result['quantile'] == .9
    assert zone.expires_at > fixed + timedelta(hours=10)
    deadline, edited = zone.expires_at, zone.updated_at
    count = db.scalar(select(func.count()).select_from(AuditLog))
    assert policy.apply_zone_policy(db, zone.id, now=now+timedelta(minutes=1)) == result
    db.commit()
    assert zone.expires_at == deadline and zone.updated_at == edited
    assert db.scalar(select(func.count()).select_from(AuditLog)) == count
    assert zone.id in {z.id for z in get_active_avoidance_zones(db, now=fixed+timedelta(minutes=1))}
    assert zone.id in {z.id for z in get_active_flood_zones(db)}
    assert expire_due_zones(db, deadline-timedelta(seconds=1)) == 0
    assert expire_due_zones(db, deadline+timedelta(seconds=1)) == 1
    assert not zone.is_active and zone.flood_event.status == FloodEventStatus.ENDED
    assert not get_active_avoidance_zones(db, now=deadline+timedelta(seconds=1))
    entry = db.scalar(select(FloodEventTimelineEntry).where(FloodEventTimelineEntry.event_id == zone.event_id,
        FloodEventTimelineEntry.entry_type == 'evidence_expired'))
    assert entry.snapshot_json['condition'] == 'Unconfirmed'
    assert 'not observed cleared' in entry.summary
    assert policy.apply_zone_policy(db, zone.id, now=deadline+timedelta(minutes=1)) is None


def test_disabling_ml_restores_original_fixed_deadline_and_reenabling_is_stable(zone_db):
    db, staff, zone, report, now = zone_db
    fixed = zone.expires_at
    policy.apply_zone_policy(db, zone.id, now=now); db.commit()
    model_deadline = zone.expires_at
    configure(db, staff, enabled=False)
    assert policy.apply_zone_policy(db, zone.id, now=now)['method'] == 'fixed'
    db.commit(); assert zone.expires_at == fixed
    configure(db, staff, enabled=True)
    assert policy.apply_zone_policy(db, zone.id, now=now)['method'].startswith('ml_')
    db.commit(); assert zone.expires_at == model_deadline


def test_global_pause_preserves_deadlines_and_prevents_maintenance(zone_db):
    db, staff, zone, report, now = zone_db
    policy.apply_zone_policy(db, zone.id, now=now); db.commit()
    deadline = zone.expires_at
    configure(db, staff, automatic=False)
    assert expire_due_zones(db, deadline+timedelta(minutes=1)) == 0
    assert zone.is_active and zone.expires_at == deadline
    configure(db, staff, automatic=True)
    assert expire_due_zones(db, deadline+timedelta(minutes=1)) == 1


def test_missing_model_is_visible_fixed_fallback_and_db_errors_propagate(zone_db, monkeypatch):
    db, staff, zone, report, now = zone_db
    fixed = zone.expires_at
    def missing(*a, **kw):
        raise FileNotFoundError('fixture')
    monkeypatch.setattr(policy.predictions, 'resolve_zone_prediction', missing)
    assert policy.apply_zone_policy(db, zone.id, now=now)['method'] == 'fixed_fallback'
    db.commit(); assert zone.expires_at == fixed
    assert 'FileNotFoundError' in policy.expiry_status(db, zone.id)['reason']


def test_expiry_policy_http_permissions_are_private_and_read_only(zone_db):
    db, staff, zone, report, now = zone_db
    policy.apply_zone_policy(db, zone.id, now=now); db.commit()
    count = db.scalar(select(func.count()).select_from(AuditLog))
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: staff
    try:
        client = TestClient(app)
        path = f'/api/v1/admin/zones/{zone.id}/expiry-policy'
        response = client.get(path)
        assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
        assert response.json()['method'].startswith('ml_')
        assert client.post(path, json={}).status_code == 405
        staff.role.permissions = {'zones':'view'}
        assert client.get(path).status_code == 403
    finally:
        app.dependency_overrides.clear()
    assert db.scalar(select(func.count()).select_from(AuditLog)) == count


@pytest.mark.parametrize('city,state,expected', [('Pasig','needs_review','fixed_fallback'),
    ('Mandaluyong','estimated','fixed'), ('Pasig','inactive','fixed_fallback')])
def test_ineligible_estimates_do_not_supply_ml_deadlines(city,state,expected):
    result = SimpleNamespace(city=city,state=state,reasons=['Ineligible'],submission_simulation=None,
        registration_simulation=None)
    assert policy.choose_deadline(result,None,None)['method'] == expected


def test_new_frozen_numeric_depth_uses_cross_location_model(zone_db):
    db, staff, zone, report, now = zone_db
    source = db.scalar(select(AuditLog).where(AuditLog.action_type == 'CITIZEN_OBSERVATION', AuditLog.target_id == report.id))
    frozen = dict(source.metadata_json)
    features = dict(frozen['prediction_features'])
    features.update(recorded_at=now.isoformat(), depth_cm=38.1, depth_basis='reported_numeric_centimeters')
    frozen['prediction_features'] = features
    source.metadata_json = frozen
    db.commit()
    result = policy.apply_zone_policy(db, zone.id, now=now)
    assert result['method'] == 'ml_cross_location', result
    assert result['reference_basis'] == 'observed_reference'
    assert result['model_sha256']


def test_official_proxy_remains_labelled_and_toggle_does_not_destroy_source_clock(zone_db):
    db, staff, zone, report, now = zone_db
    report.zone_id = None
    zone.updated_at = now-timedelta(minutes=30, seconds=1)
    db.add(AuditLog(action_type='CREATE_OFFICIAL_ZONE', target_table='flood_avoidance_zones',
        target_id=zone.id, admin_id=staff.id, metadata_json={'zone_id':zone.id}, created_at=now-timedelta(minutes=30)))
    db.commit()
    result = policy.apply_zone_policy(db,zone.id,now=now)
    db.commit()
    assert result['method'] == 'ml_pooled' and result['reference_basis'] == 'registration_proxy'
    deadline = zone.expires_at
    configure(db,staff,enabled=False)
    policy.apply_zone_policy(db,zone.id,now=now); db.commit()
    configure(db,staff,enabled=True)
    assert policy.apply_zone_policy(db,zone.id,now=now)['reference_basis'] == 'registration_proxy'
    assert zone.expires_at == deadline


def test_news_original_timer_cannot_expire_a_zone_with_an_ml_deadline(zone_db):
    from uuid import uuid4
    from shapely.geometry import mapping
    from geoalchemy2.shape import to_shape
    from app.crud.news_publication import reserve_decision_id
    from app.crud.news_publication_read import operational_deadline
    from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimZoneLink
    from app.schemas.news_publication import NewsDecisionSnapshot, PublicNewsAlert
    from app.services.news_publication_service import expire_case, public_projection
    from app.services.news_zone_projection_service import zone_responses_with_news
    db, staff, zone, report, now = zone_db
    report.zone_id = None
    case = NewsClaimCase(revision=1); db.add(case); db.flush()
    observed = now-timedelta(minutes=30)
    decision = NewsClaimDecision(id=reserve_decision_id(db),case_id=case.id,revision=1,request_id=uuid4(),
        actor_kind='staff',actor_user_id=staff.id,operation='correct',public_state='active_zone',review_state='resolved',
        reason_code='verified_current_footprint',snapshot={},observed_at=observed,
        expires_at=now+timedelta(minutes=90),decided_at=now)
    public = PublicNewsAlert(case_id=case.id,decision_id=decision.id,revision=1,status='Active',
        location_label='Maybunga',condition_label='Reported flooding',passability_label='Unknown',
        observed_at=observed,expires_at=decision.expires_at,updated_at=now,source_title='Fixture',
        source_publisher='Fixture',source_url='https://example.com/flood',evidence_excerpt='Recorded wet observation',
        geometry_precision='operational_polygon',display_geojson=mapping(to_shape(zone.geometry)),affects_routing=True)
    decision.snapshot = NewsDecisionSnapshot(request_sha256='1'*64,policy_fingerprint='2'*64,
        claim_source_id=1,input_sha256='3'*64,claim_sha256='4'*64,incident_identity='5'*64,
        article_id=1,public=public,linked_zone_ids=[zone.id],geometry_reason='verified_incident_footprint').model_dump(mode='json')
    db.add(decision); db.flush()
    db.add(NewsClaimZoneLink(decision_id=decision.id,zone_id=zone.id,relation='created')); db.commit()
    frozen, fixed = dict(decision.snapshot), decision.expires_at
    result = policy.apply_zone_policy(db,zone.id,now=now); db.commit()
    assert result['method'] == 'ml_pooled', result
    effective = operational_deadline(db,decision)
    assert effective == zone.expires_at > fixed
    assert public_projection(decision,fixed+timedelta(seconds=1),expiry_override=effective).status == 'Active'
    assert expire_case(db,case.id,now=fixed+timedelta(seconds=1)) is None
    assert zone_responses_with_news(db,[zone])[0].news[0].expires_at == effective
    db.refresh(decision)
    assert decision.snapshot == frozen and decision.expires_at == fixed
    assert expire_due_zones(db,effective+timedelta(seconds=1)) == 1
    assert expire_case(db,case.id,now=effective+timedelta(seconds=1)).public_state == 'expired'


def test_explicit_staff_deadline_is_never_overwritten(zone_db):
    db, staff, zone, report, now = zone_db
    fixed = zone.expires_at
    db.add(AuditLog(action_type='UPDATE_ZONE',target_table='flood_avoidance_zones',target_id=zone.id,
        admin_id=staff.id,metadata_json={'expires_at':fixed.isoformat()},created_at=now)); db.commit()
    result = policy.apply_zone_policy(db,zone.id,now=now)
    assert result['method'] == 'fixed' and zone.expires_at == fixed
    assert 'staff deadline' in result['reason']


def test_first_late_worker_recovers_cached_null_registration_then_retains_history(zone_db):
    db, staff, zone, report, now = zone_db
    report.zone_id = None
    recorded = now-timedelta(days=3)
    zone.created_at, zone.updated_at, zone.expires_at = recorded-timedelta(seconds=2), recorded-timedelta(seconds=1), None
    db.add(AuditLog(action_type='CREATE_OFFICIAL_ZONE', target_table='flood_avoidance_zones',
        target_id=zone.id, admin_id=staff.id, metadata_json={'zone_id':zone.id}, created_at=recorded))
    db.commit()
    expected = policy.predictions.resolve_zone_prediction(db, zone.id, now=recorded)
    quantiles = expected.registration_simulation.quantiles
    deadline = next(q.estimated_reported_subsidence_at for q in quantiles if q.quantile == .9)
    assert deadline < now
    assert policy.predictions.resolve_zone_prediction(db,zone.id,now=now).registration_simulation is None
    db.add(AuditLog(action_type=policy.ACTION,target_table='flood_avoidance_zones',target_id=zone.id,
        metadata_json={'policy_version':'pasig-experimental-ml-expiry-v1',
            'source_signature':policy._source_signature(db,zone),'ml_enabled':True,'deadline':None,
            'method':'fixed_fallback','fixed_deadline':None},created_at=now-timedelta(minutes=1)))
    db.commit()
    edited = zone.updated_at
    assert policy.expiry_status(db,zone.id)['method'] == 'pending_sync'
    recovered = policy.apply_zone_policy(db,zone.id,now=now); db.commit()
    assert recovered['method']=='ml_pooled' and recovered['reference_basis']=='registration_proxy'
    assert recovered['prediction_as_of_at']==recorded.isoformat()
    assert zone.expires_at==deadline and zone.updated_at==edited
    count = db.scalar(select(func.count()).select_from(AuditLog))
    assert policy.apply_zone_policy(db,zone.id,now=now+timedelta(minutes=1))==recovered
    db.commit()
    assert db.scalar(select(func.count()).select_from(AuditLog))==count
    assert expire_due_zones(db,now)==1
    assert not zone.is_active and zone.flood_event.status==FloodEventStatus.ENDED
    status = policy.expiry_status(db,zone.id)
    assert status['quantiles']==recovered['quantiles'] and not status['zone_is_active']
    app.dependency_overrides[get_db]=lambda:db
    app.dependency_overrides[get_current_user]=lambda:staff
    try:
        response=TestClient(app).get(f'/api/v1/admin/zones/{zone.id}/expiry-policy')
        assert response.status_code==200 and len(response.json()['quantiles'])==3
        assert response.json()['zone_is_active'] is False
    finally:
        app.dependency_overrides.clear()


def test_late_approved_submission_recovers_without_inventing_observation(zone_db):
    db, staff, zone, report, now = zone_db
    original = db.scalar(select(AuditLog).where(AuditLog.action_type=='CITIZEN_OBSERVATION',
        AuditLog.target_id==report.id))
    submitted = now-timedelta(days=2)
    approved = submitted+timedelta(minutes=1)
    original.created_at = submitted
    original.metadata_json = {**original.metadata_json,'observed_at':None}
    report.created_at, report.approved_at, report.updated_at = submitted-timedelta(seconds=1), approved, approved
    zone.created_at, zone.updated_at, zone.expires_at = approved, approved, None
    db.add(AuditLog(action_type='APPROVE_REPORT',target_table='flood_reports',target_id=report.id,
        admin_id=staff.id,metadata_json={'report_id':report.id,'zone_id':zone.id},created_at=approved+timedelta(seconds=1)))
    db.commit()
    recovered = policy.apply_zone_policy(db,zone.id,now=now); db.commit()
    assert recovered['method']=='ml_pooled' and recovered['reference_basis']=='submission_proxy', recovered
    assert zone.expires_at<now and original.metadata_json['observed_at'] is None
    assert len(policy.expiry_status(db,zone.id)['quantiles'])==3
    assert expire_due_zones(db,now)==1


@pytest.mark.parametrize('changed', ['zone_edit', 'public_update'])
def test_late_official_recovery_cannot_ignore_current_evidence(zone_db,changed):
    db, staff, zone, report, now = zone_db
    report.zone_id=None
    recorded=now-timedelta(days=3)
    zone.created_at,zone.updated_at,zone.expires_at=recorded-timedelta(seconds=2),recorded-timedelta(seconds=1),None
    db.add(AuditLog(action_type='CREATE_OFFICIAL_ZONE',target_table='flood_avoidance_zones',target_id=zone.id,
        admin_id=staff.id,metadata_json={'zone_id':zone.id},created_at=recorded))
    if changed=='zone_edit':
        db.add(AuditLog(action_type='UPDATE_ZONE',target_table='flood_avoidance_zones',target_id=zone.id,
            admin_id=staff.id,metadata_json={'depth':'waist'},created_at=now))
    else:
        from app.crud import zone_update
        # The current signal is in existing audit storage; no historical clock
        # substitution may hide it from the operational resolver.
        db.add(AuditLog(action_type=zone_update.OBSERVATION_ACTION,target_table='flood_avoidance_zones',target_id=zone.id,
            admin_id=staff.id,metadata_json={},created_at=now))
    db.commit()
    result=policy.apply_zone_policy(db,zone.id,now=now); db.commit()
    assert result['method']=='fixed_fallback' and zone.expires_at is None
