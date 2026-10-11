"""Source/clock/scope/capability contracts, actual packaged model, no DB writes."""
from datetime import datetime, timedelta, timezone
import json
import hashlib
import shutil
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import get_current_user
from app.core.database import get_db
from app.main import app
from app.schemas.zone_prediction import ZonePrediction, ZonePredictionEvidence
from app.services import cross_location_prediction_service as service
from app.services.flood_followup_service import FollowupError

NOW=datetime(2026,10,8,15,tzinfo=timezone.utc)


@pytest.fixture
def source(monkeypatch):
    clock=NOW-timedelta(minutes=30)
    evidence=ZonePredictionEvidence(source_kind="original_citizen_observation",source_id=9,report_id=2,
        observed_at=clock,available_at=clock+timedelta(minutes=1))
    baseline=ZonePrediction(zone_id=9,state="estimated",city="Pasig",barangays=["Ugong"],reference=evidence,evaluated_at=NOW,
        prediction_as_of_at=evidence.available_at)
    metadata={"observed_at":clock.isoformat(),"geometry_sha256":"source-geometry",
        "prediction_features":{"schema_version":"flood_features_v1","recorded_at":evidence.available_at.isoformat(),
            "observed_at":clock.isoformat(),"depth_cm":40,"depth_basis":"reported_numeric_centimeters",
            "barangays":["Ugong"],"geometry_sha256":"source-geometry","errors":[]}}
    audit=SimpleNamespace(id=9,created_at=evidence.available_at,metadata_json=metadata)
    staff=SimpleNamespace(id=7,is_active=True,deleted_at=None,role=SimpleNamespace(name="Officer",permissions={"reports":"view","zones":"view"}))
    monkeypatch.setattr(service.zones,"predict_zone",lambda *a,**kw:baseline)
    monkeypatch.setattr(service.store,"comparison_source_audit",lambda *a:audit)
    return baseline,audit,staff


def test_unseen_location_comparison_uses_frozen_depth_and_stable_issuance(source):
    baseline,audit,staff=source
    result=service.compare_zone(object(),9,staff,now=NOW)
    assert result.status=="research_comparison" and result.depth_cm==40
    assert result.calculation.location_outcomes==0 and result.calculation.unseen_location_variance>0
    assert result.reference_at==baseline.reference.observed_at and result.source_observed_at==result.reference_at
    assert result.quantiles==service.compare_zone(object(),9,staff,now=NOW+timedelta(minutes=5)).quantiles
    assert result.selected_for_primary is False and result.changes_status_expiry_or_routing is False
    assert audit.metadata_json["prediction_features"]["depth_cm"]==40


@pytest.mark.parametrize("change",["missing","future_features","wrong_observation","geometry","location","range","missing_depth","bad_basis","multi","expired","inactive","needs_review","news"])
def test_unsupported_or_changed_evidence_abstains(source,change):
    baseline,audit,staff=source; f=audit.metadata_json["prediction_features"]
    if change=="missing":audit.metadata_json.pop("prediction_features")
    if change=="future_features":f["recorded_at"]=NOW.isoformat()
    if change=="wrong_observation":f["observed_at"]=NOW.isoformat()
    if change=="geometry":f["geometry_sha256"]="other"
    if change=="location":f["barangays"]=["Santolan"]
    if change=="range":f["depth_cm"]=100
    if change=="missing_depth":f["depth_cm"]=None
    if change=="bad_basis":f["depth_basis"]="guessed"
    if change=="multi":baseline.barangays=["Ugong","Santolan"]
    if change in {"expired","inactive","needs_review"}:baseline.state=change
    if change=="news":baseline.reference.source_kind="news_decision"
    result=service.compare_zone(object(),9,staff,now=NOW)
    assert result.status=="abstained" and result.reason and not result.quantiles


def test_gauge_proxy_is_explicitly_a_simulation(source):
    _,audit,staff=source
    f=audit.metadata_json["prediction_features"]
    f.update(depth_cm=48.26,depth_basis="reported_canonical_gauge_proxy",depth_gauge="knee")
    result=service.compare_zone(object(),9,staff,now=NOW)
    assert result.status=="research_comparison" and any("proxy-depth simulation" in s for s in result.warnings)
    f["depth_cm"]=45
    assert service.compare_zone(object(),9,staff,now=NOW).status=="abstained"


def test_actual_zone_adapter_uses_approved_source_without_a_primary_model_change(monkeypatch):
    from geoalchemy2.shape import from_shape
    from shapely.geometry import LineString, box
    from app import models
    from app.crud import zone_update
    from app.schemas.flood_review_suggestion import WetEvidence
    from app.services.flood_location_service import get_flood_location_provider
    _,boundary=next((r,p) for r,p in get_flood_location_provider().records.values() if r.barangay=="Ugong")
    point=boundary.representative_point()
    area=box(point.x-.00001,point.y-.00001,point.x+.00001,point.y+.00001)
    line=LineString([(point.x-.000005,point.y),(point.x+.000005,point.y)])
    observed=NOW-timedelta(minutes=10)
    available=observed+timedelta(minutes=1)
    zone=models.FloodAvoidanceZone(id=9,event_id=2,geometry=from_shape(area,srid=4326),is_active=True,expires_at=None)
    report=models.FloodReport(id=2,zone_id=9,event_id=2,user_id=8,source=models.ReportSource.USER_REPORT,
        status=models.ReportStatus.APPROVED,geometry=from_shape(line,srid=4326),city="Pasig",barangay="Ugong")
    geometry_hash=hashlib.sha256(line.wkb).hexdigest()
    audit=SimpleNamespace(created_at=available,metadata_json={"observed_at":observed.isoformat(),"geometry_sha256":geometry_hash,
        "prediction_features":{"schema_version":"flood_features_v1","recorded_at":available.isoformat(),
            "observed_at":observed.isoformat(),"depth_cm":40,"depth_basis":"reported_numeric_centimeters",
            "barangays":["Ugong"],"geometry_sha256":geometry_hash,"errors":[]}})
    staff=SimpleNamespace(id=7,is_active=True,deleted_at=None,role=SimpleNamespace(name="Officer",permissions={"reports":"view","zones":"view"}))
    monkeypatch.setattr(service.store,"get_zone",lambda *a:zone)
    monkeypatch.setattr(service.store,"linked_reports",lambda *a:[report])
    monkeypatch.setattr(service.store,"nearby_report_count",lambda *a,**kw:0)
    monkeypatch.setattr(service.store,"comparison_source_audit",lambda *a:audit)
    monkeypatch.setattr(service.zones,"_wet_evidence",lambda *a:([WetEvidence(audit_id=9,observed_at=observed,available_at=available,
        provenance="original_citizen_observation")],None))
    monkeypatch.setattr(service.zones,"_pending_signal",lambda *a:False)
    monkeypatch.setattr(service.zones,"_news_evidence",lambda *a:([],[]))
    monkeypatch.setattr(zone_update,"observations",lambda *a,**kw:[])
    before=service.zones.predict_zone(object(),9,staff,now=NOW)
    comparison=service.compare_zone(object(),9,staff,now=NOW)
    after=service.zones.predict_zone(object(),9,staff,now=NOW+timedelta(minutes=1))
    assert comparison.status=="research_comparison" and comparison.target_location=="Ugong"
    assert before.quantiles==after.quantiles and before.prediction_as_of_at==comparison.prediction_as_of_at
    assert zone.is_active and zone.expires_at is None


def test_missing_corrupted_and_ineligible_bundle_do_not_replace_baseline(source,monkeypatch,tmp_path):
    _,_,staff=source
    original=service.BUNDLE_DIRECTORY
    monkeypatch.setattr(service,"BUNDLE_DIRECTORY",tmp_path)
    assert service.compare_zone(object(),9,staff,now=NOW).status=="model_unavailable"
    for name in ("cross_location_manifest.json","cross_location_aft.json","cross_location_evaluation.json"):
        shutil.copyfile(original/name,tmp_path/name)
    (tmp_path/"cross_location_aft.json").write_text('{}',encoding="utf-8")
    assert service.compare_zone(object(),9,staff,now=NOW).status=="model_unavailable"
    shutil.copyfile(original/"cross_location_aft.json",tmp_path/"cross_location_aft.json")
    report=json.loads((tmp_path/"cross_location_evaluation.json").read_text())
    report["selected_for_primary"]=True
    raw=json.dumps(report).encode()
    (tmp_path/"cross_location_evaluation.json").write_bytes(raw)
    manifest=json.loads((tmp_path/"cross_location_manifest.json").read_text())
    manifest["evaluation_sha256"]=hashlib.sha256(raw).hexdigest()
    (tmp_path/"cross_location_manifest.json").write_text(json.dumps(manifest))
    assert service.compare_zone(object(),9,staff,now=NOW).status=="model_unavailable"


@pytest.mark.parametrize("proxy",["submission","registration"])
def test_recording_proxy_retains_unknown_observation_clock(source,monkeypatch,proxy):
    from app.schemas.flood_subsidence import DurationPreviewResponse, DurationModelStatus
    from geoalchemy2.shape import from_shape
    from shapely.geometry import box
    baseline,audit,staff=source
    reference=baseline.reference.observed_at
    features=audit.metadata_json["prediction_features"]
    features.update(observed_at=None,recorded_at=reference.isoformat())
    audit.metadata_json["observed_at"]=None
    audit.created_at=reference
    sim=DurationPreviewResponse(status="research_estimate",model=DurationModelStatus(status="research_model_available",model_fitted=True),
        reference_at=reference,prediction_as_of_at=reference,reference_policy="proxy",assumed_continuous_wet=True)
    baseline.state="unavailable";baseline.reference=None
    if proxy=="submission":
        baseline.submission_simulation=sim;baseline.submission_audit_id=9;baseline.submission_report_id=2
    else:
        baseline.registration_simulation=sim;baseline.registration_audit_id=9
        geom=box(121,14,121.001,14.001)
        features["geometry_sha256"]=hashlib.sha256(geom.wkb).hexdigest()
        monkeypatch.setattr(service.store,"get_zone",lambda *a:SimpleNamespace(geometry=from_shape(geom,srid=4326)))
    result=service.compare_zone(object(),9,staff,now=NOW)
    assert result.status=="research_comparison" and result.source_observed_at is None
    assert result.reference_basis==proxy+"_proxy" and result.prediction_as_of_at==reference
    assert any("actual flood observation time remains unknown" in w for w in result.warnings)


@pytest.mark.parametrize("permissions",[{"reports":"view"},{"zones":"view"},{}])
def test_both_read_capabilities_are_required(source,permissions):
    _,_,staff=source;staff.role.permissions=permissions
    with pytest.raises(FollowupError) as exc:
        service.compare_zone(object(),9,staff,now=NOW)
    assert exc.value.status_code==403


def test_private_api_serializes_comparison_and_surfaces_database_failure(source,monkeypatch):
    _,_,staff=source
    app.dependency_overrides[get_db]=lambda:SimpleNamespace(rollback=lambda:None)
    app.dependency_overrides[get_current_user]=lambda:staff
    try:
        client=TestClient(app)  # Do not enter production startup/seeding/retention.
        response=client.get('/api/v1/admin/zones/9/cross-location-prediction')
        assert response.status_code==200 and response.headers['cache-control']=='no-store'
        assert response.json()['selected_for_primary'] is False
        def failure(*args): raise SQLAlchemyError("private source parameters")
        monkeypatch.setattr(service.store,"comparison_source_audit",failure)
        response=client.get('/api/v1/admin/zones/9/cross-location-prediction')
        assert response.status_code==503 and 'private source' not in response.text
        client.close()
    finally:
        app.dependency_overrides.clear()
