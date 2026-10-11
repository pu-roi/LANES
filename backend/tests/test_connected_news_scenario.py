"""Source fidelity, scoped expiry and publication boundaries for local replay."""
from datetime import datetime, timedelta, timezone
import json

import pytest
from sqlalchemy import create_engine, literal, select

from app.core.config import settings
from app.services import local_news_scenario_service as scenario
from app.services.news_evaluation_service import EvaluationPolicy, publication_is_current
from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_publication_service import public_projection
from tests.test_news_publication_lifecycle import decision, NOW


@pytest.fixture
def scenario_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(scenario, "SCENARIO_PATH", tmp_path / "scenario.json")
    monkeypatch.setattr(scenario, "database_identity", lambda: "connected-db")
    content = {"database_identity": "connected-db", "at": NOW.isoformat(), "case_ids": [1], "zone_ids": [23]}
    scenario.SCENARIO_PATH.write_text(json.dumps(content), encoding="utf-8")
    return content


def test_historical_projection_preserves_original_source_fields(scenario_file):
    row = decision()
    original = row.snapshot["public"].copy()
    result = public_projection(row, NOW + timedelta(days=30))
    assert result.status == "Active"
    for field in ("evidence_excerpt", "observed_at", "expires_at", "source_title", "source_publisher", "source_url", "source_published_at"):
        assert result.model_dump(mode="json")[field] == original[field]
    assert row.snapshot["public"] == original
    other = decision()
    other.case_id = 2
    other.snapshot["public"]["case_id"] = 2
    assert public_projection(other, NOW + timedelta(days=30)) is None


def test_scenario_clock_does_not_revive_withdrawn_or_expired_decision(scenario_file):
    assert public_projection(decision(state="withdrawn"), NOW + timedelta(days=30)) is None
    result = public_projection(decision(state="expired"), NOW + timedelta(days=30))
    assert result.status == "Unconfirmed" and not result.affects_routing


@pytest.mark.parametrize("identity,active,expected", [(23, True, True), (23, False, False), (99, True, False)])
def test_zone_eligibility_uses_selected_clock_and_respects_deactivation(scenario_file, identity, active, expected):
    real_now = NOW + timedelta(days=30)
    with create_engine("sqlite://").connect() as db:
        clock = scenario.sql_clock(literal(identity), "zone", literal(real_now))
        visible = db.scalar(select(literal(active) & (literal(NOW + timedelta(hours=2)) > clock)))
    assert bool(visible) is expected


@pytest.mark.parametrize("environment,binding", [("production", "connected-db"), ("development", "other-db")])
def test_production_and_other_database_ignore_scenario(scenario_file, environment, binding, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", environment)
    monkeypatch.setattr(scenario, "database_identity", lambda: binding)
    assert scenario.scoped_clock(1, "case", NOW + timedelta(days=30)) == NOW + timedelta(days=30)
    assert scenario.read_scenario() is None


def test_connected_admission_requires_context_exact_source_and_clock(monkeypatch, tmp_path):
    from app.core.database import engine
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "DATABASE_URL", engine.url.render_as_string(hide_password=False))
    monkeypatch.setattr(scenario, "SCENARIO_PATH", tmp_path / "absent.json")
    published = NOW + timedelta(hours=12)
    article = NewsArticleExtractorInput(article_id=1, canonical_url="https://example.org/original", publisher="fixture", title="Original", published_at=published)
    with scenario.connected_reconstruction(article.canonical_url, published):
        policy = EvaluationPolicy("a" * 64, "fixture", {}, publication_admission_at=published)
        assert publication_is_current(article, NOW, policy)
        assert not publication_is_current(article.model_copy(update={"canonical_url":"https://example.org/other"}), NOW, policy)
        assert not scenario.admits_connected_reconstruction(published + timedelta(minutes=1))
    assert not scenario.admits_connected_reconstruction(published)
    assert not publication_is_current(article, NOW)


def test_connected_admission_unavailable_in_production(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    with pytest.raises(ValueError):
        with scenario.connected_reconstruction("https://example.org/original", NOW):
            pass
