"""Public snapshots never turn evidence expiry into physical clearance."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.news_publication import NewsDecisionSnapshot, NewsStaffDecisionRequest, PublicNewsAlert
from app.services.news_publication_service import public_projection, unconfirmed_retention_hours

NOW = datetime(2026, 10, 5, 3, tzinfo=timezone.utc)


def decision(*, state="active_alert", operation="evaluate", public=True):
    item = PublicNewsAlert(case_id=1, decision_id=2, revision=1, status="Active",
        location_label="C5", location_qualifier="Pasig City", depth_label="knee-deep",
        condition_label="Reported active flood", passability_label="Reported impassable to all vehicles",
        observed_at=NOW - timedelta(minutes=5), expires_at=NOW + timedelta(hours=1, minutes=55),
        updated_at=NOW, source_title="Flood news", source_publisher="Fixture News",
        source_url="https://example.org/flood", source_published_at=NOW, evidence_excerpt="C5 was flooded.")
    snapshot = NewsDecisionSnapshot(request_sha256="a" * 64, policy_fingerprint="b" * 64,
        claim_source_id=1, evaluation_id=1, input_sha256="c" * 64, claim_sha256="d" * 64,
        incident_identity="e" * 64, article_id=1, public=item if public else None,
        private_reason="Sensitive staff note, not public")
    return SimpleNamespace(id=2, case_id=1, revision=1, operation=operation, public_state=state,
        snapshot=snapshot.model_dump(mode="json"), observed_at=item.observed_at,
        expires_at=item.expires_at, decided_at=NOW)


def test_active_alert_has_no_operational_geometry_or_private_evidence():
    result = public_projection(decision(), NOW)
    assert result.status == "Active" and result.display_geojson is None
    assert result.affects_routing is False
    assert "Sensitive" not in result.model_dump_json()


@pytest.mark.parametrize("age", [2, 3, 25])
def test_expired_observation_is_unconfirmed_even_before_maintenance(age):
    result = public_projection(decision(), NOW + timedelta(hours=age))
    assert result.status == "Unconfirmed" and result.current_status_unknown
    assert result.depth_label.startswith("Last reported:")
    assert result.passability_label.startswith("Last report:")
    assert "clear" not in result.condition_label.lower()


def test_retention_hides_current_feed_but_keeps_last_known_detail():
    row = decision()
    later = row.expires_at + timedelta(hours=24)
    assert public_projection(row, later) is None
    assert public_projection(row, later, include_retained=True).status == "Unconfirmed"


def test_paused_expiry_preserves_original_public_evidence_after_deadline_and_retention():
    row = decision()
    original = dict(row.snapshot["public"])
    later = row.expires_at + timedelta(days=3)
    result = public_projection(row, later, automatic_expiry_enabled=False)
    assert result.status == "Active" and not result.current_status_unknown
    for field in ("source_url", "source_title", "source_publisher", "evidence_excerpt"):
        assert getattr(result, field) == original[field]
    assert result.observed_at == row.observed_at and result.expires_at == row.expires_at
    assert row.snapshot["public"] == original
    assert public_projection(row, later) is None


@pytest.mark.parametrize("state,operation,status", [
    ("expired", "expire", "Unconfirmed"), ("withdrawn", "reject", None),
    ("unpublished", "evaluate", None), ("withdrawn", "clear", "Cleared"),
])
def test_paused_expiry_does_not_revive_expired_withdrawn_private_or_cleared_decisions(state, operation, status):
    result = public_projection(decision(state=state, operation=operation), NOW + timedelta(hours=3),
        include_retained=True, automatic_expiry_enabled=False)
    assert (result.status if result else None) == status


def test_clearance_status_requires_clear_operation_and_preserves_last_wet_clock():
    row = decision(state="withdrawn", operation="clear")
    row.observed_at = NOW + timedelta(minutes=20)
    snapshot = NewsDecisionSnapshot.model_validate(row.snapshot)
    snapshot.public.cleared_at = row.observed_at
    row.snapshot = snapshot.model_dump(mode="json")
    result = public_projection(row, NOW + timedelta(hours=1))
    assert result.status == "Cleared" and result.observed_at == NOW - timedelta(minutes=5)
    assert result.cleared_at == NOW + timedelta(minutes=20)
    assert public_projection(row, NOW + timedelta(hours=25)) is None
    assert public_projection(row, NOW + timedelta(hours=25), include_retained=True).status == "Cleared"


@pytest.mark.parametrize("state", ["unpublished", "withdrawn"])
def test_rejected_and_private_cases_never_expose_previous_snapshot(state):
    assert public_projection(decision(state=state), NOW) is None


def test_projection_checks_snapshot_identity():
    row = decision()
    row.snapshot["public"]["case_id"] = 3
    assert public_projection(row, NOW) is None


def test_retention_config_is_display_only_bounded(monkeypatch):
    monkeypatch.setenv("LANES_NEWS_UNCONFIRMED_RETENTION_HOURS", "12")
    assert unconfirmed_retention_hours() == 12
    monkeypatch.setenv("LANES_NEWS_UNCONFIRMED_RETENTION_HOURS", "0")
    with pytest.raises(ValueError):
        unconfirmed_retention_hours()


def test_staff_requests_cannot_smuggle_geometry_or_untyped_flood_facts():
    from uuid import uuid4
    with pytest.raises(ValidationError):
        NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=1, operation="correct",
                                 reason="Correction", geometry={"type": "Polygon"})
    with pytest.raises(ValidationError):
        NewsStaffDecisionRequest(request_id=uuid4(), expected_revision=1, operation="defer",
                                 reason="Review later", deferred_until=NOW.replace(tzinfo=None))
