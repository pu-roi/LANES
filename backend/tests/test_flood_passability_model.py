"""Real source-bound transport fit, target separation and explicit pooled transfer."""
from datetime import datetime, timedelta, timezone
import hashlib
import json

import pytest

from app.schemas.flood_subsidence import DurationPreviewRequest, PassabilityPreviewRequest
from app.services.flood_duration_model import PASSABILITY_TARGET_VERSION
from app.services import flood_passability_prediction_service as transport
from app.services import flood_subsidence_prediction_service as subsidence
from scripts.train_pasig_passability import candidates, build, RUNTIME

NOW = datetime(2026, 10, 8, 1, tzinfo=timezone.utc)


def request(**changes):
    return PassabilityPreviewRequest(**{"city": "Pasig", "barangay": "Ugong", "reference_at": NOW-timedelta(hours=1),
        "prediction_as_of_at": NOW, "acknowledge_research_limitations": True,
        "assume_continuous_nonpassability": True, **changes})


def test_source_bound_fit_uses_nine_projections_two_summaries_without_dry_label_imputation(tmp_path):
    rows, hashes = candidates()
    assert len(rows) == 9 and len({r["shared_outcome_group"] for r in rows}) == 2
    ugong = next(r for r in rows if r["barangay"] == "Ugong")
    assert ugong["first_nonpassable_at"] == "2024-10-24T21:15:00+08:00"
    assert ugong["last_nonpassable_at"] == "2024-10-25T01:00:00+08:00"
    assert (ugong["lower_minutes"], ugong["upper_minutes"]) == (225, 315)
    assert all(not r["subsidence_label_admitted"] and not r["production_training_admitted"] for r in rows)
    before = subsidence.DEFAULT_MODEL.read_bytes(), RUNTIME.read_bytes()
    report = build(tmp_path, None)
    assert report["target_version"] == PASSABILITY_TARGET_VERSION and not report["observed_labels_imputed"]
    assert any(r["state"] == "unidentifiable" for r in report["summary_group_sensitivity"])
    assert (subsidence.DEFAULT_MODEL.read_bytes(), RUNTIME.read_bytes()) == before
    assert hashes and "Ugong" in report["training_barangays"]


def test_actual_passability_fit_has_distinct_output_and_no_safe_passage_claim():
    result = transport.preview_passability(request(), now=NOW)
    assert result.status == "research_estimate" and len(result.quantiles) == 3
    assert result.model.target_version == PASSABILITY_TARGET_VERSION
    assert "Ugong" in result.model.supported_barangays and len(result.model.prediction_barangays) == 30
    assert not result.confirms_physical_dryness_or_safe_passage and not result.changes_status_expiry_or_routing
    assert all(q.estimated_reported_passability_at > NOW for q in result.quantiles)
    assert not result.pooled_geographic_transfer


@pytest.mark.parametrize("changes,reason", [
    ({"assume_continuous_nonpassability": False}, "continuous_nonpassability_research_assumption_required"),
    ({"acknowledge_research_limitations": False}, "continuous_nonpassability_research_assumption_required"),
    ({"city": "Taguig"}, "outside_pasig_scope"),
    ({"barangay": "Invented place", "allow_pooled_pasig_transfer": True}, "unknown_pasig_barangay"),
    ({"barangay": "Santa Rosa"}, "outside_passability_training_cohort"),
    ({"prediction_as_of_at": NOW+timedelta(minutes=2)}, "future_issuance_time"),
    ({"reference_at": NOW-timedelta(days=2)}, "reference_age_exceeds_passability_evidence_support"),
])
def test_abstention_preserves_reason_without_quantiles(changes, reason):
    result = transport.preview_passability(request(**changes), now=NOW)
    assert result.abstention_reason == reason and not result.quantiles


def test_both_models_can_transfer_to_known_pasig_geography_without_claiming_training():
    result = transport.preview_passability(request(barangay="Santa Rosa", allow_pooled_pasig_transfer=True), now=NOW)
    assert result.status == "research_estimate" and result.pooled_geographic_transfer
    result = subsidence.preview_subsidence(DurationPreviewRequest(city="Pasig", barangay="Ugong",
        reference_at=NOW-timedelta(hours=1), prediction_as_of_at=NOW, reference_policy="first_recorded_wet_in_episode",
        acknowledge_research_limitations=True, assume_continuous_wet=True, allow_pooled_pasig_transfer=True), now=NOW)
    assert result.status == "research_estimate" and result.pooled_geographic_transfer
    assert "Ugong" not in result.model.supported_barangays and len(result.model.prediction_barangays) == 30


def test_bad_or_wrong_target_artifact_is_rejected_and_missing_abstains(tmp_path, monkeypatch):
    path = tmp_path/"model.json"
    monkeypatch.setenv("LANES_FLOOD_PASSABILITY_MODEL_PATH", str(path))
    assert transport.preview_passability(request(), now=NOW).abstention_reason == "passability_model_unavailable"
    path.write_bytes(RUNTIME.read_bytes())
    monkeypatch.setenv("LANES_FLOOD_PASSABILITY_MODEL_SHA256", "wrong")
    with pytest.raises(ValueError, match="checksum"): transport.load_passability_model()
    monkeypatch.delenv("LANES_FLOOD_PASSABILITY_MODEL_SHA256")
    data = json.loads(subsidence.DEFAULT_MODEL.read_text(encoding="utf-8"))
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="Incompatible"): transport.load_passability_model()


def test_passability_api_actual_permission_dependencies_no_store_and_sanitized_error(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.v1.endpoints.flood_duration import router
    from app.api.deps import get_current_user
    from types import SimpleNamespace
    app = FastAPI(); app.include_router(router)
    staff = SimpleNamespace(is_active=True, role=SimpleNamespace(name="Staff", permissions={"reports": "view"}))
    app.dependency_overrides[get_current_user] = lambda: staff
    client = TestClient(app)
    assert client.get("/passability-model").status_code == 200
    response = client.post("/passability-preview", json=request().model_dump(mode="json"))
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    staff.role.name = "Commuter"
    assert client.get("/passability-model").status_code == 403
    staff.role.name = "Staff"
    monkeypatch.setenv("LANES_FLOOD_PASSABILITY_MODEL_PATH", str(subsidence.DEFAULT_MODEL))
    response = client.get("/passability-model")
    assert response.status_code == 503 and "artifact" in response.json()["detail"]
