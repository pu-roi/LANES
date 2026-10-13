"""Production must never use a public/default or transient per-process signing key."""
import pytest
from app.core import config


def test_development_defaults_are_distinct_runtime_secrets():
    first = config.Settings(_env_file=None)
    second = config.Settings(_env_file=None)
    # This test deliberately removes any inherited explicit environment binding.
    if "SECRET_KEY" in first.model_fields_set:
        pytest.skip("An explicit key is supplied by this test environment")
    assert first.SECRET_KEY != second.SECRET_KEY and len(first.SECRET_KEY) >= 32


@pytest.mark.parametrize("key", [None, "short"])
def test_production_rejects_missing_or_short_keys(monkeypatch, key):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    values = {"ENVIRONMENT": "production", "VALHALLA_URL": "https://router.example.org",
              "VALHALLA_AUDIENCE": "https://router.example.org"}
    if key is not None:
        values["SECRET_KEY"] = key
    monkeypatch.setattr(config, "settings", config.Settings(_env_file=None, **values))
    with pytest.raises(RuntimeError, match="private SECRET_KEY"):
        config.validate_production_routing_configuration()


def test_production_accepts_an_explicit_private_key(monkeypatch):
    monkeypatch.setattr(config, "settings", config.Settings(_env_file=None, ENVIRONMENT="production",
        VALHALLA_URL="https://router.example.org", VALHALLA_AUDIENCE="https://router.example.org",
        SECRET_KEY="synthetic-test-signing-material" * 2))
    config.validate_production_routing_configuration()
