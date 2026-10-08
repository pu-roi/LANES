"""Future public updates/reviews collect source inputs without creating dry truth."""
from datetime import datetime,timezone,timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func,select
from app.api.deps import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.audit import AuditLog
from app.schemas.zone_update import ZoneObservationCreate,ZoneObservationReview
from app.schemas.flood_followup import FloodFollowupCreate,FloodFollowupReviewCreate
from app.services import zone_update_service as updates
from app.services import flood_followup_service as followups
from app.services.flood_followup_service import FollowupError
from test_zone_prediction import zone_db,isolated_db
from test_operational_settings_postgres import citizen


def test_public_current_condition_snapshot_and_review_export_keep_missing_clock_and_spot_scope(zone_db):
    db,staff,zone,item,now=zone_db
    owner=item.user
    before=(zone.is_active,zone.expires_at,zone.updated_at)
    payload=ZoneObservationCreate(request_id=uuid4(),condition="no_floodwater",observed_location="Original road section",description="No water at this part of the street.")
    result=updates.submit(db,zone.id,owner,payload,[])
    assert result["observed_at"] is None
    assert result["prediction_features"]["depth_cm"] is None
    assert result["model_evidence"]["geometry_basis"]=="official_zone_context_only"
    updated=updates.review(db,zone.id,result["id"],staff,ZoneObservationReview(decision="reviewed",note="A source report for this spot only."))
    page=updates.model_evidence(db,zone.id,staff,50,None)
    entry=page["records"][0]
    assert entry["review_state"]=="reviewed" and entry["clock_basis"]=="submission_proxy_only"
    assert entry["source_author_id"]!=entry["reviewer_id"]
    assert "explicit_observation_clock_missing" in entry["qualification_blockers"]
    assert "not_whole_zone_clearance" in entry["scope"]
    assert not entry["training_admitted"] and not entry["physical_dry_label_generated"]
    assert "description" not in entry and "author_name" not in entry and "media_urls" not in entry
    db.refresh(zone);assert before==(zone.is_active,zone.expires_at,zone.updated_at)
    from types import SimpleNamespace
    commuter=SimpleNamespace(is_active=True,deleted_at=None,role=SimpleNamespace(name="Commuter",permissions={"reports":"full","zones":"full"}))
    with pytest.raises(FollowupError):updates.model_evidence(db,zone.id,commuter,50,None)


def test_model_export_keyset_and_native_capability_checks_are_read_only(zone_db):
    db,staff,zone,item,now=zone_db
    for _ in range(2):updates.submit(db,zone.id,item.user,ZoneObservationCreate(request_id=uuid4(),condition="still_flooded",depth="gutter",observed_location="Original road section",description="Water remains at the original road."),[])
    page=updates.model_evidence(db,zone.id,staff,1,None)
    assert page["next_before_id"]==page["records"][0]["observation_id"]
    older=updates.model_evidence(db,zone.id,staff,1,page["next_before_id"])
    assert older["records"][0]["observation_id"]<page["records"][0]["observation_id"]
    app.dependency_overrides[get_db]=lambda:db
    app.dependency_overrides[get_current_user]=lambda:staff
    count=db.scalar(select(func.count()).select_from(AuditLog))
    try:
        client=TestClient(app);path=f"/api/v1/admin/zones/{zone.id}/model-evidence"
        response=client.get(path)
        assert response.status_code==200 and response.headers["cache-control"]=="no-store"
        assert client.get(path+'?limit=101').status_code==422
        staff.role.permissions={"zones":"full"};db.flush()
        assert client.get(path).status_code==403
    finally:app.dependency_overrides.clear()
    assert db.scalar(select(func.count()).select_from(AuditLog))==count


def test_owner_followup_and_existing_export_preserve_actual_numeric_clocked_inputs(zone_db):
    db,staff,zone,item,now=zone_db
    item.city="Pasig";item.barangay="Maybunga";item.human_readable_location="Original road section";db.commit()
    observation=followups.submit_followup(db,item.id,item.user,FloodFollowupCreate(request_id=uuid4(),condition="still_flooded",
        observed_at=datetime.now(timezone.utc)-timedelta(minutes=1),depth_cm=12.5,evidence_text="Water remains on this same road section.",same_location_confirmed=True))
    assert observation.prediction_features["depth_cm"]==12.5
    assert observation.prediction_features["depth_basis"]=="reported_numeric_centimeters"
    followups.review_followup(db,observation.id,staff,FloodFollowupReviewCreate(decision="accepted",same_location_verified=True,evidence_text="Independent same-road evidence reviewed."))
    export=followups.export_staff_followups(db,staff)
    assert export.follow_ups[0].prediction_features==observation.prediction_features
    assert not export.training_admitted and not export.follow_ups[0].model_admitted
