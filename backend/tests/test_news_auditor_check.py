"""Operator self-check must never call a paid model or publish fixture evidence."""
import asyncio
from types import SimpleNamespace

import pytest

from app.services.news_claim_auditor import AuditorConfig, NewsClaimAuditor
from scripts.check_news_auditor import check_auditor


def test_configuration_check_makes_no_provider_request(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Configuration inspection must not call a provider")
    monkeypatch.setattr(NewsClaimAuditor, "audit", forbidden)
    config = AuditorConfig(provider="openrouter", model="openrouter/free", openrouter_api_key="synthetic")
    result = asyncio.run(check_auditor(config))
    assert result["status"] == "configuration_ok" and not result["provider_request_made"]


@pytest.mark.parametrize("model", ["vendor/paid-model", "openrouter/auto", "openrouter/auto:free"])
def test_probe_refuses_every_model_except_explicit_free_router(monkeypatch, model):
    async def forbidden(*args, **kwargs):
        raise AssertionError("An unapproved model must not receive a request")
    monkeypatch.setattr(NewsClaimAuditor, "audit", forbidden)
    config = AuditorConfig(provider="openrouter", model=model, openrouter_api_key="synthetic")
    result = asyncio.run(check_auditor(config, probe=True))
    assert result["status"] == "configuration_error" and not result["provider_request_made"]


def test_opt_in_probe_uses_only_historical_synthetic_evidence(monkeypatch):
    calls = []
    async def synthetic_audit(self, claim, article):
        calls.append(article.canonical_url)
        assert self.timeout_seconds == 60
        assert claim.is_historical and claim.event_time_resolved.year == 2020
        assert article.publisher == "LANES synthetic self-test"
        return SimpleNamespace(evidence=object(), outcome="review", reason_code="historical_claim_evidence")
    monkeypatch.setattr(NewsClaimAuditor, "audit", synthetic_audit)
    config = AuditorConfig(provider="openrouter", model="openrouter/free", openrouter_api_key="synthetic")
    result = asyncio.run(check_auditor(config, probe=True, timeout_seconds=60))
    assert len(calls) == 1 and result["status"] == "valid_response" and result["outcome"] == "review"
    assert not result["database_access"] and not result["public_data_written"]
    assert result["timeout_seconds"] == 60


@pytest.mark.parametrize("timeout", [0, -1, 121, float("nan"), float("inf"), True])
def test_invalid_timeout_never_makes_a_provider_request(monkeypatch, timeout):
    async def forbidden(*args, **kwargs):
        raise AssertionError("An invalid timeout must not receive a request")
    monkeypatch.setattr(NewsClaimAuditor, "audit", forbidden)
    config = AuditorConfig(provider="openrouter", model="openrouter/free", openrouter_api_key="synthetic")
    result = asyncio.run(check_auditor(config, probe=True, timeout_seconds=timeout))
    assert result["reason"] == "auditor_timeout_invalid" and not result["provider_request_made"]
