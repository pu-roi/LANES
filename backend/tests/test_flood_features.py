"""Model inputs preserve unknown clocks/measurements and provider/source failures."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, func
from app.models.audit import AuditLog
from app.services import flood_feature_service as features
from app.services import zone_prediction_service
from app.services.citizen_approval_service import record_observation
from test_zone_prediction import zone_db, isolated_db

NOW=datetime(2026,10,8,3,15,tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def clear_environment_cache():
    features._cache.clear()
    yield
    features._cache.clear()


def provider(path,params):
    if path=="elevation":return {"elevation":[14.0]}
    return {"hourly_units":{"precipitation":"mm"},"utc_offset_seconds":0,"latitude":14.5,"longitude":121,
        "hourly":{"time":[f"2026-10-08T0{h}:00" for h in range(5)],"precipitation":[0,1,2,3,999]}}


def test_environment_uses_only_prior_hours_preserves_coarse_grid_and_cache_independence(monkeypatch):
    requests=[]
    def fake(path,params):requests.append(path);return provider(path,params)
    monkeypatch.setattr(features,"_json_request",fake)
    data=features.environment_context(121.077,14.583,NOW)
    assert data["elevation_m"]==14 and data["rainfall_previous_3h_mm"]==6
    assert data["rainfall_interval_end"]=="2026-10-08T03:00:00+00:00"
    assert data["rainfall_grid_coordinates"]==[121,14.5] and not data["is_street_measurement"]
    assert data["hydraulic_drainage_capacity"] is None
    data["elevation_m"]=999
    assert features.environment_context(121.077,14.583,NOW)["elevation_m"]==14
    assert requests==["elevation","forecast"]


def test_provider_failure_is_visible_and_never_substituted_with_zero(monkeypatch):
    def unavailable(path,params):raise ValueError("unavailable")
    monkeypatch.setattr(features,"_json_request",unavailable)
    data=features.environment_context(121.077,14.583,NOW)
    assert data["elevation_m"] is data["rainfall_previous_3h_mm"] is None
    assert len(data["errors"])==2


def test_fractional_rainfall_sum_has_stable_source_precision(monkeypatch):
    def fractional(path,params):
        data=provider(path,params)
        if path=="forecast":data["hourly"]["precipitation"]=[0,.1,.2,.3,999]
        return data
    monkeypatch.setattr(features,"_json_request",fractional)
    assert features.environment_context(121.077,14.583,NOW)["rainfall_previous_3h_mm"]==.6


@pytest.mark.parametrize("value", [False,float("nan"),None,"12"])
def test_invalid_elevation_is_missing_rather_than_a_numeric_model_feature(monkeypatch,value):
    monkeypatch.setattr(features,"_json_request",lambda path,params:{"elevation":[value]} if path=="elevation" else provider(path,params))
    result=features.environment_context(121.077,14.583,NOW)
    assert result["elevation_m"] is None and result["errors"]


def test_future_report_features_are_frozen_without_new_inputs_or_provider_calls(zone_db,monkeypatch):
    db,staff,zone,item,now=zone_db
    def forbidden(*args,**kwargs):raise AssertionError("Report submission must not wait for weather")
    monkeypatch.setattr(features,"_json_request",forbidden)
    record_observation(db,item,observed_at=None,road_validated=True,media_hashes=[])
    audit=db.scalar(select(AuditLog).where(AuditLog.action_type=="CITIZEN_OBSERVATION",AuditLog.target_id==item.id).order_by(AuditLog.id.desc()))
    snapshot=audit.metadata_json["prediction_features"]
    assert snapshot["observed_at"] is None and audit.metadata_json["observed_at"] is None
    assert snapshot["coordinates"] and snapshot["barangays"]==["Maybunga"]
    assert snapshot["depth_basis"]=="reported_canonical_gauge_proxy"
    assert not snapshot["is_training_label"] and not snapshot["changes_status_expiry_or_routing"]
    assert snapshot["environment"]["status"]=="not_captured"
    assert item.status.value=="approved" and zone.is_active


def test_authorized_context_reads_are_read_only_and_preserve_missing_observation(zone_db,monkeypatch):
    db,staff,zone,item,now=zone_db
    monkeypatch.setattr(features,"_json_request",provider)
    # Provider series must match the actual issuance hour for this native request.
    monkeypatch.setattr(features,"environment_context",lambda lon,lat,clock:{"elevation_m":14,"errors":[],"captured_at":clock.isoformat()})
    before=db.scalar(select(func.count()).select_from(AuditLog)),zone.expires_at,zone.is_active
    result=zone_prediction_service.feature_context(db,zone.id,staff)
    assert result["observed_at"] is None and result["coordinates"] and result["environment"]["elevation_m"]==14
    assert before==(db.scalar(select(func.count()).select_from(AuditLog)),zone.expires_at,zone.is_active)
    staff.role.permissions={"reports":"view"};db.flush()
    from app.services.flood_followup_service import FollowupError
    with pytest.raises(FollowupError):zone_prediction_service.feature_context(db,zone.id,staff)


def test_native_feature_endpoint_preserves_capabilities_no_store_and_operational_state(zone_db,monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import get_db
    from app.api.deps import get_current_user
    db,staff,zone,_,now=zone_db
    monkeypatch.setattr(features,"environment_context",lambda lon,lat,clock:{"elevation_m":None,"errors":["Provider unavailable."]})
    app.dependency_overrides[get_db]=lambda:db
    app.dependency_overrides[get_current_user]=lambda:staff
    before=(zone.is_active,zone.expires_at,db.scalar(select(func.count()).select_from(AuditLog)))
    try:
        client=TestClient(app)
        path=f"/api/v1/admin/zones/{zone.id}/prediction-features"
        response=client.get(path)
        assert response.status_code==200 and response.headers["cache-control"]=="no-store"
        assert response.json()["environment"]["errors"]==["Provider unavailable."]
        assert client.post(path,json={}).status_code==405
        assert client.get("/api/v1/admin/zones/999999/prediction-features").status_code==404
        staff.role.permissions={"reports":"view"};db.flush()
        assert client.get(path).status_code==403
    finally:app.dependency_overrides.clear()
    assert before==(zone.is_active,zone.expires_at,db.scalar(select(func.count()).select_from(AuditLog)))


def test_numeric_followup_depth_is_not_replaced_by_an_old_gauge(zone_db):
    db,staff,zone,item,now=zone_db
    snapshot=features.capture_features(item.geometry,None,observed_at=now,measured_depth_cm=12.5)
    assert snapshot["depth_cm"]==12.5 and snapshot["depth_basis"]=="reported_numeric_centimeters"
    assert features.capture_features(item.geometry,None)["depth_cm"] is None


def test_cache_captured_after_an_observation_record_cannot_be_backdated_into_it(zone_db):
    db,staff,zone,item,now=zone_db
    raw=features.capture_features(item.geometry,item.depth,now=now)
    point=raw["coordinates"]
    key=(round(point[0],3),round(point[1],3),now.strftime("%Y-%m-%dT%H"))
    features._cache[key]=(now,{"captured_at":(now+timedelta(seconds=1)).isoformat(),"elevation_m":99})
    frozen=features.capture_features(item.geometry,item.depth,now=now)
    assert frozen["environment"]["status"]=="not_captured"
