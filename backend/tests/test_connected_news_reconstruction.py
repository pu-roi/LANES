"""Connected-demo guards and input provenance; no database writes or services."""
import json
from types import SimpleNamespace

import pytest
from sqlalchemy.engine import make_url

from scripts import reconstruct_connected_news as command


def test_database_confirmation_fails_before_session(monkeypatch):
    from app.core.config import settings
    from app.core.database import engine
    configured = make_url("postgresql://operator:secret@cloud.example/lanes")
    monkeypatch.setattr(settings, "DATABASE_URL", configured.render_as_string(hide_password=False))
    monkeypatch.setattr(engine, "url", configured)
    def forbidden_session():
        raise AssertionError("Database session opened before target confirmation")
    monkeypatch.setattr(command, "SessionLocal", forbidden_session)
    with pytest.raises(ValueError, match="database confirmation"):
        command.require_connected_target("another_database")


@pytest.mark.parametrize("environment,provider,expiry,error", [
    ("production", "source_rules", False, "development environment"),
    ("development", "gemini", False, "credit-free source_rules"),
    ("development", "source_rules", True, "Disable automatic expiry"),
])
def test_presentation_preconditions(monkeypatch, tmp_path, environment, provider, expiry, error):
    from app.core.config import settings
    from app.core.database import engine
    configured = make_url("postgresql://operator:secret@cloud.example/lanes")
    monkeypatch.setattr(settings, "DATABASE_URL", configured.render_as_string(hide_password=False))
    monkeypatch.setattr(settings, "ENVIRONMENT", environment)
    monkeypatch.setattr(engine, "url", configured)
    monkeypatch.setattr(command, "SCENARIO_PATH", tmp_path / "scenario.json")
    monkeypatch.setattr(command.NewsClaimAuditor, "policy_identity", lambda _: {"provider": provider, "configured": True})
    class ReadSession:
        def __enter__(self):
            return self
        def __exit__(self, *_):
            pass
    monkeypatch.setattr(command, "SessionLocal", ReadSession)
    monkeypatch.setattr(command, "read_configuration", lambda _: SimpleNamespace(automatic_expiry_enabled=expiry))
    with pytest.raises(ValueError, match=error):
        command.require_connected_target("lanes")


def test_retains_both_scenarios_and_repeat_has_no_duplicates(tmp_path, monkeypatch):
    destination = tmp_path / "scenario.local.json"
    monkeypatch.setattr(command, "SCENARIO_PATH", destination)
    monkeypatch.setattr(command, "database_identity", lambda: "same-database")
    def receipt(name, day, identity):
        return dict(scenario=name, at=f"2026-09-{day}T09:56:00+08:00", source_url=f"https://publisher.example/{name}",
                    article_id=identity, run_id=identity, case_ids=[identity], zone_ids=[identity])
    command.retain_scenarios(receipt("september24", "24", 24))
    command.retain_scenarios(receipt("september9", "09", 9))
    command.retain_scenarios(receipt("september9", "09", 9))
    saved = json.loads(destination.read_text())
    assert saved["zone_ids"] == saved["case_ids"] == [9, 24]
    assert set(saved["scenarios"]) == {"september24", "september9"}
    assert saved["at"] == "2026-09-24T09:56:00+08:00"


def test_refuses_to_replace_another_database_scenario(tmp_path, monkeypatch):
    destination = tmp_path / "scenario.local.json"
    original = json.dumps({"database_identity": "other-database"})
    destination.write_text(original)
    monkeypatch.setattr(command, "SCENARIO_PATH", destination)
    monkeypatch.setattr(command, "database_identity", lambda: "same-database")
    with pytest.raises(ValueError, match="another database"):
        command.retain_scenarios({})
    assert destination.read_text() == original


def test_september9_input_preserves_measurements_and_publication(tmp_path, monkeypatch):
    body = "Published September 9, 2026 9:19am\nSanto Domingo: half knee-deep (19 inches)."
    path = tmp_path / "preserved.txt"
    path.write_text(body, encoding="utf-8")
    url, admission, at, _, spec, source = command.scenario_inputs("september9")
    monkeypatch.setattr(command, "scenario_inputs", lambda _: (url, admission, at, path, spec, source))
    feeds = (SimpleNamespace(feed_urls=("https://publisher.example/rss",)),)
    requests = []
    with command.reconstruction_client("september9", feeds, requests) as publisher:
        rss = publisher.get(feeds[0].feed_urls[0]).text
        html = publisher.get(url).text
        assert "09:19:06" in rss
        assert "half knee-deep (19 inches)." in html
        assert "Published September 9, 2026 9:19am" in html
        with pytest.raises(RuntimeError, match="uncaptured"):
            publisher.get("https://publisher.example/missing")
    assert path.read_text(encoding="utf-8") == body
