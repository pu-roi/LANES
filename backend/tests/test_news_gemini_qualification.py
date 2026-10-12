"""Shared qualification budget survives retries, process restarts and failures."""
import json

import httpx
import pytest

from scripts.qualify_news_gemini import QualificationBudget, BudgetTransport, BudgetExhausted
from scripts.qualify_news_gemini import qualify
from app.services.news_claim_auditor import canonical_claim_sha256, canonical_input_sha256
from tests.test_news_claim_auditor import auditor, reply
from tests.test_news_batch_audit import sample, rows


def test_budget_counts_before_dispatch_and_persists_across_restarts(tmp_path):
    path = tmp_path / "qualification.json"
    with QualificationBudget(path, "fixture") as budget:
        for index in range(7):
            assert budget.reserve({"profile": "normalized"}) == index
        with pytest.raises(FileExistsError):
            with QualificationBudget(path, "fixture"):
                pass
    with QualificationBudget(path, "fixture") as budget:
        for index in range(7, 12):
            assert budget.reserve({"profile": "compact", "model": "backup"}) == index
        with pytest.raises(BudgetExhausted):
            budget.reserve({"profile": "inline"})
        budget.stop("blocked", reason="budget_exhausted")
    with pytest.raises(ValueError, match="already_stopped"):
        with QualificationBudget(path, "fixture"):
            pass
    assert len(json.loads(path.read_text())["attempts"]) == 12
    assert not path.with_suffix(".lock").exists()


@pytest.mark.asyncio
async def test_transport_failure_still_counts_and_never_retries(tmp_path):
    calls = []
    async def unavailable(request):
        calls.append(request.method)
        raise httpx.ConnectError("synthetic failure")
    with QualificationBudget(tmp_path / "qualification.json", "fixture") as budget:
        transport = BudgetTransport(budget, {"case": "fixture"}, httpx.MockTransport(unavailable))
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(httpx.ConnectError):
                await client.post("https://generativelanguage.googleapis.com/v1beta/models/fixture:generateContent", json={})
            with pytest.raises(ValueError, match="not_allowed"):
                await client.get("https://generativelanguage.googleapis.com/")
        assert calls == ["POST"] and len(budget.state["attempts"]) == 1


def test_other_credential_or_fixture_cannot_reset_ledger(tmp_path):
    path = tmp_path / "qualification.json"
    with QualificationBudget(path, "fixture-one") as budget:
        budget.reserve({"case": "fixture"})
    with pytest.raises(ValueError, match="identity_mismatch"):
        with QualificationBudget(path, "fixture-two"):
            pass
    assert len(json.loads(path.read_text())["attempts"]) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [401, 402, 429])
async def test_account_failure_stops_all_profiles_and_models(tmp_path, monkeypatch, failure):
    calls = []
    def response(request):
        calls.append(request.url.path)
        return httpx.Response(failure, headers={"retry-after": "120"})
    monkeypatch.setattr("scripts.qualify_news_gemini.httpx.AsyncHTTPTransport", lambda **_: httpx.MockTransport(response))
    candidates, article = sample()
    case = {"name": "fixture", "candidates": candidates, "article": article,
            "input_sha256": canonical_input_sha256(article),
            "claim_sha256": [canonical_claim_sha256(c.claim) for c in candidates],
            "expected": {c.candidate_id: "verified" for c in candidates}}
    with QualificationBudget(tmp_path / "qualification.json", "fixture") as budget:
        await qualify(auditor("gemini").config, [case], budget)
        assert budget.state["status"] == "blocked" and budget.state["reason"] == "account_error"
        assert len(calls) == len(budget.state["attempts"]) == 1 and budget.state["blocked_until"]


@pytest.mark.asyncio
async def test_model_unavailability_uses_only_named_backup_with_same_budget(tmp_path, monkeypatch):
    calls = []
    candidates, article = sample()
    def response(request):
        calls.append(request.url.path)
        return httpx.Response(503) if len(calls) == 1 else reply({"results": rows(candidates, article)}, "gemini")
    monkeypatch.setattr("scripts.qualify_news_gemini.httpx.AsyncHTTPTransport", lambda **_: httpx.MockTransport(response))
    case = {"name": "fixture", "candidates": candidates, "article": article,
            "input_sha256": canonical_input_sha256(article),
            "claim_sha256": [canonical_claim_sha256(c.claim) for c in candidates],
            "expected": {c.candidate_id: "verified" for c in candidates}}
    with QualificationBudget(tmp_path / "qualification.json", "fixture") as budget:
        await qualify(auditor("gemini").config, [case], budget)
        assert budget.state["status"] == "qualified" and budget.state["model"] == "gemini-3.5-flash-lite"
        assert len(calls) == len(budget.state["attempts"]) == 2
