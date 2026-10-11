"""No DB or synthetic outcome is admitted by the offline pairing tool."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import hashlib

import pytest

from app.services.recession_dataset_service import EpisodeReview, qualify_recession_episodes
from scripts.build_recession_dataset import build

NOW = datetime(2026, 10, 10, 15, tzinfo=timezone.utc)


def observation(identity, condition, minutes):
    observed = NOW + timedelta(minutes=minutes)
    return {"id": identity, "request_id": f"00000000-0000-0000-0000-{identity:012d}",
        "report_id": 1, "user_id": 10, "condition": condition,
        "observed_at": observed.isoformat(), "submitted_at": (observed+timedelta(minutes=1)).isoformat(),
        "evidence_text": "PRIVATE source text excluded from outputs", "depth_cm": 12.5 if condition == "still_flooded" else 0,
        "source_url": "https://example.invalid/private", "same_location_confirmed": True,
        "location_snapshot": {"report_id": 1, "city": "Pasig", "barangay": "Maybunga",
            "human_readable_location": "PRIVATE section", "geometry_sha256": "a"*64, "zone_id": 2, "event_id": 3},
        "original_observed_at": None, "review_state": "accepted",
        "review": {"id": identity+100, "decision": "accepted", "reviewer_id": 20,
            "reviewed_at": (observed+timedelta(minutes=2)).isoformat(),
            "evidence_text": "PRIVATE reviewed source", "same_location_verified": True},
        "prediction_features": {"recorded_at": (observed+timedelta(minutes=1)).isoformat(),
            "observed_at": observed.isoformat(), "depth_cm": 12.5, "depth_basis": "reported_numeric_centimeters",
            "geometry_sha256": "a"*64, "coordinates": [121.07,14.58],
            "boundary_revision": "fixture-reviewed-source", "barangays": ["Maybunga"], "errors": []}}


def inputs(clear=True):
    records = [observation(1,"still_flooded",-120), observation(2,"still_flooded",-60),
        observation(3,"subsided" if clear else "still_flooded",-30)]
    envelope = {"schema_version": 1, "selection": {"review_state":"all", "first_before_id":None},
        "pages": [{"schema_version":1,"generated_at":NOW.isoformat(),"follow_ups":records[::-1],"next_before_id":None}]}
    rule = {"episode_id":"episode-1","reference_id":1,"endpoint_id":3,"reviewer_id":30,
        "reviewed_at":NOW.isoformat(),"sample_kind":"field_verified",
        "same_section_verified":True,"continuity_verified":True}
    return envelope, rule


def qualify(envelope, rule):
    return qualify_recession_episodes(envelope,[EpisodeReview.model_validate(rule)],now=NOW)


def test_reviewed_interval_uses_frozen_first_depth_and_actual_observed_bounds():
    envelope, rule = inputs()
    result = qualify(envelope,rule)
    row = result["candidates"][0]
    assert (row["lower_minutes"],row["upper_minutes"],row["depth_cm"]) == (60,90,12.5)
    assert row["censoring"] == "interval" and not row["lower_inclusive"] and row["upper_inclusive"]
    assert row["outcome_available_at"] == NOW.isoformat() and row["storm_group"] is None
    assert not row["production_training_admitted"] and not row["true_onset_known"]
    assert not result["changes_status_expiry_or_routing"]
    assert "PRIVATE" not in json.dumps(result) and "example.invalid" not in json.dumps(result)


def test_reviewed_wet_endpoint_produces_right_censoring_without_inventing_clearance():
    envelope,rule=inputs(False)
    row=qualify(envelope,rule)["candidates"][0]
    assert row["lower_minutes"] == 90 and row["upper_minutes"] is None and row["censoring"] == "right"


@pytest.mark.parametrize("key,value,blocker",[
    ("sample_kind","test","test_or_unverified_field_observations"),
    ("sample_kind","unclassified","test_or_unverified_field_observations"),
    ("same_section_verified",False,"section_or_episode_continuity_not_reviewed"),
    ("continuity_verified",False,"section_or_episode_continuity_not_reviewed"),
    ("reviewer_id",10,"episode_reviewer_is_source_author"),
    ("reviewed_at",(NOW+timedelta(minutes=1)).isoformat(),"episode_review_is_future_dated"),
    ("reference_id",900,"selected_observation_not_in_complete_export"),
])
def test_human_episode_gates_do_not_auto_accept_test_or_unreviewed_samples(key,value,blocker):
    envelope,rule=inputs();rule[key]=value
    result=qualify(envelope,rule)
    assert result["candidates"] == [] and blocker in result["qualification"][0]["blockers"]


@pytest.mark.parametrize("change,blocker",[
    ("pending","independent_accepted_source_review_missing"),
    ("self_review","independent_accepted_source_review_missing"),
    ("geometry","section_or_episode_snapshot_changed"),
    ("intervening_clearance","intervening_clearance_or_recurrence"),
    ("zero_wet","condition_depth_conflict"),
    ("late_submission","endpoint_already_observed_at_simulated_issuance"),
    ("missing_depth","frozen_numeric_depth_and_pasig_features_unqualified"),
    ("late_feature","frozen_numeric_depth_and_pasig_features_unqualified"),
    ("multiple_localities","frozen_numeric_depth_and_pasig_features_unqualified"),
])
def test_scope_review_clock_depth_and_recurrence_guards(change,blocker):
    envelope,rule=inputs();first=envelope["pages"][0]["follow_ups"][-1];middle=envelope["pages"][0]["follow_ups"][1]
    if change=="pending":middle.update(review_state="pending",review=None)
    if change=="self_review":middle["review"]["reviewer_id"]=10
    if change=="geometry":middle["location_snapshot"]["geometry_sha256"]="b"*64
    if change=="intervening_clearance":middle.update(condition="subsided",depth_cm=0)
    if change=="zero_wet":middle["depth_cm"]=0
    if change=="late_submission":
        first["submitted_at"]=(NOW-timedelta(minutes=21)).isoformat()
        first["review"]["reviewed_at"]=(NOW-timedelta(minutes=20)).isoformat()
    if change=="missing_depth":first["depth_cm"]=None
    if change=="late_feature":first["prediction_features"]["recorded_at"]=NOW.isoformat()
    if change=="multiple_localities":first["prediction_features"]["barangays"]=["Maybunga","Ugong"]
    result=qualify(envelope,rule)
    assert not result["candidates"] and blocker in result["qualification"][0]["blockers"]


def test_complete_pagination_and_omitted_pending_page_are_checked():
    envelope,rule=inputs();page=envelope["pages"][0];rows=page["follow_ups"]
    page.update(follow_ups=rows[:2],next_before_id=2)
    with pytest.raises(ValueError,match="incomplete"):qualify(envelope,rule)
    envelope["pages"].append({**deepcopy(page),"follow_ups":rows[2:],"next_before_id":None})
    assert len(qualify(envelope,rule)["candidates"]) == 1
    envelope["selection"]["review_state"]="accepted"
    with pytest.raises(ValueError,match="all-review-state"):qualify(envelope,rule)


def test_no_episode_reviews_returns_collection_gap_instead_of_auto_pairing():
    envelope,_=inputs()
    result=qualify_recession_episodes(envelope,[],now=NOW)
    assert result["candidates"] == [] and result["reports_without_episode_review"] == [1]


def test_duplicate_rule_and_later_claim_cannot_silently_duplicate_or_censor_outcome():
    envelope,rule=inputs()
    result=qualify_recession_episodes(envelope,[EpisodeReview.model_validate(rule)]*2,now=NOW)
    assert not result["candidates"]
    envelope,rule=inputs(False)
    envelope["pages"][0]["follow_ups"].insert(0,observation(4,"subsided",-10))
    result=qualify(envelope,rule)
    assert not result["candidates"] and "later_claim_requires_censoring_or_episode_review" in result["qualification"][0]["blockers"]


def test_naive_observation_is_rejected_before_temporal_pairing():
    envelope,rule=inputs()
    envelope["pages"][0]["follow_ups"][-1]["observed_at"]="2026-10-10T13:00:00"
    with pytest.raises(ValueError,match="available"):qualify(envelope,rule)


def test_cli_output_is_sanitized_hashed_and_cannot_overwrite(tmp_path):
    envelope,rule=inputs();export=tmp_path/"export.json";reviews=tmp_path/"reviews.json"
    export.write_text(json.dumps(envelope),encoding="utf-8");reviews.write_text(json.dumps([rule]),encoding="utf-8")
    out=tmp_path/"new-result"
    summary=build(export,reviews,out)
    result=json.loads((out/"dataset.json").read_text())
    assert summary["conditional_research_candidates"]==1 and set(result["input_sha256"])=={"export","episode_reviews"}
    assert "PRIVATE" not in json.dumps(result) and not result["production_training_admitted"]
    with pytest.raises(ValueError,match="overwritten"):build(export,reviews,out)


def test_original_inputs_are_preserved_and_feature_boolean_is_not_numeric_depth():
    envelope,rule=inputs();before=deepcopy(envelope)
    qualify(envelope,rule)
    assert envelope == before
    first=envelope["pages"][0]["follow_ups"][-1]
    first["depth_cm"]=1;first["prediction_features"]["depth_cm"]=True
    result=qualify(envelope,rule)
    assert not result["candidates"] and "frozen_numeric_depth_and_pasig_features_unqualified" in result["qualification"][0]["blockers"]


def test_retrospective_review_qualifies_hindcast_evidence_without_inventing_issued_forecast():
    envelope,rule=inputs();first=envelope["pages"][0]["follow_ups"][-1]
    first["review"]["reviewed_at"]=(NOW-timedelta(minutes=10)).isoformat()
    row=qualify(envelope,rule)["candidates"][0]
    assert not row["actual_issued_forecast"]
    assert row["simulated_prediction_issuance_at"] == first["submitted_at"]
    assert row["reference_reviewed_at"] == first["review"]["reviewed_at"]


def test_lineage_hashes_the_exact_bytes_qualified_even_if_input_changes(tmp_path,monkeypatch):
    from scripts import build_recession_dataset as module
    envelope,_=inputs();export=tmp_path/"export.json"
    initial=json.dumps(envelope).encode();export.write_bytes(initial)
    original=module.qualify_recession_episodes
    def mutate_after_qualification(envelope,rules):
        result=original(envelope,rules)
        export.write_text('{"changed_during_build": true}',encoding="utf-8")
        return result
    monkeypatch.setattr(module,"qualify_recession_episodes",mutate_after_qualification)
    module.build(export,None,tmp_path/"result")
    result=json.loads((tmp_path/"result/dataset.json").read_text())
    assert result["source_observations"]==3
    assert result["input_sha256"]["export"]==hashlib.sha256(initial).hexdigest()
    assert result["input_sha256"]["export"]!=hashlib.sha256(export.read_bytes()).hexdigest()
