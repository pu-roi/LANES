"""Policy validation, evidence clocks and authenticated settings contracts."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.schemas.configuration import OperationalSettings, ConfigurationUpdate
from app.services.configuration_service import evidence_deadline
from app.api.v1.endpoints.settings import require_view, retired_write
from app.services.news_evaluation_service import evaluation_policy
from app.services.news_claim_auditor import NewsClaimAuditor


@pytest.mark.parametrize("change", [
    {"surprise": True}, {"citizen_min_trust": 101}, {"citizen_min_human_reviews": 0},
    {"news_collection_interval_minutes": 20}, {"news_collection_interval_minutes": True},
    {"news_processing_enabled": "false"}, {"staff_road_buffer_metres": float("nan")},
    {"news_source_ids": ["unverified"]}, {"evidence_expiry_minutes": {"knee": 120}},
    {"news_unconfirmed_retention_hours": 73},
    {"automatic_expiry_enabled": "false"}, {"automatic_expiry_enabled": 0},
    {"pasig_ml_expiry_enabled": "false"}, {"pasig_ml_expiry_enabled": 0},
])
def test_invalid_policy_cannot_be_saved(change):
    with pytest.raises(ValidationError):
        OperationalSettings.model_validate({**OperationalSettings().model_dump(), **change})


def test_deadlines_use_observation_and_depth_not_received_time():
    config = OperationalSettings()
    config.evidence_expiry_minutes["knee"] = 30
    observed = datetime(2026, 10, 7, tzinfo=timezone.utc)
    assert evidence_deadline(config, observed, "Knee") == observed + timedelta(minutes=30)
    assert evidence_deadline(config, observed, None) == observed + timedelta(hours=2)
    config.automatic_expiry_enabled = False
    assert evidence_deadline(config, observed, "Knee") == observed + timedelta(minutes=30)


def test_legacy_settings_default_to_enabled():
    assert OperationalSettings.model_validate({}).automatic_expiry_enabled is True
    assert OperationalSettings.model_validate({}).pasig_ml_expiry_enabled is True


@pytest.mark.parametrize("role", [None, SimpleNamespace(permissions={}), SimpleNamespace(permissions={"settings": "none"})])
def test_missing_permissions_fail_with_403(role):
    with pytest.raises(HTTPException) as error:
        require_view(SimpleNamespace(role=role))
    assert error.value.status_code == 403


def test_retired_writes_are_actionable_and_permission_checked():
    with pytest.raises(HTTPException) as error:
        retired_write(SimpleNamespace(role=SimpleNamespace(permissions={"settings": "full"})))
    assert error.value.status_code == 410


def test_evidence_changes_version_evaluation_but_switches_do_not():
    auditor = NewsClaimAuditor()
    config = OperationalSettings()
    baseline = evaluation_policy(auditor, config)
    config.news_publication_enabled = False
    assert evaluation_policy(auditor, config).fingerprint == baseline.fingerprint
    config.automatic_expiry_enabled = False
    assert evaluation_policy(auditor, config).fingerprint == baseline.fingerprint
    config.evidence_expiry_minutes["knee"] = 30
    assert evaluation_policy(auditor, config).fingerprint != baseline.fingerprint
