"""Gemini compatibility never substitutes for strict source/evidence validation."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy.orm import sessionmaker

from app.schemas.news_audit import CompactBatchSelection
from app.services.news_claim_auditor import NewsClaimAuditor
from app.services.news_gemini_schema import gemini_response_schema, GEMINI_SCHEMA_PROFILES
from app.services.news_audit_quota_service import check_quota, quota_identity, dispatched, record_error, deadline, read_quota, save_quota
from app.services.news_audit_availability_service import record_availability, read_availability
from scripts.check_news_auditor import check_auditor
from tests.test_news_claim_auditor import inputs, evidence, auditor, reply
from tests.test_news_audit_reliability import timeout_result
from tests.test_news_automation import status_db


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


@pytest.mark.parametrize("profile", GEMINI_SCHEMA_PROFILES)
def test_projection_preserves_canonical_validation_and_required_fact_shape(profile):
    canonical = CompactBatchSelection.model_json_schema()
    before = deepcopy(canonical)
    projected = gemini_response_schema(canonical, profile)
    assert canonical == before and projected is not canonical
    assert all("pattern" not in n and "exclusiveMaximum" not in n for n in walk(projected))
    if profile == "inline":
        assert "$defs" not in projected and all("$ref" not in n for n in walk(projected))
        claim = projected["properties"]["results"]["items"]
        reference = claim["properties"]["place"]["properties"]["evidence"]["items"]
    else:
        claim = projected["$defs"]["CompactClaimSelection"]
        reference = projected["$defs"]["AuditEvidenceReference"]
        assert "$ref" in projected["properties"]["results"]["items"]
    assert set(claim["required"]) == {"candidate_id", "place", "status", "time", "depth", "access"}
    assert claim["additionalProperties"] is False
    assert reference["properties"]["option_index"]["maximum"] == 255
    assert reference["properties"]["option_index"]["minimum"] == 0
    assert projected["properties"]["results"].get("maxItems") == (8 if profile == "normalized" else None)
    assert before["$defs"]["AuditEvidenceReference"]["properties"]["option_index"]["exclusiveMaximum"] == 256


def test_projection_does_not_strip_properties_named_like_schema_keywords():
    schema = {"type": "object", "title": "annotation", "properties": {
        "pattern": {"type": "string", "pattern": "x"}, "title": {"type": "string"}}}
    result = gemini_response_schema(schema, "inline")
    assert set(result["properties"]) == {"pattern", "title"} and "title" not in result
    for bad in ({"$ref": "https://example.org/schema"},
                {"$defs": {"Loop": {"$ref": "#/$defs/Loop"}}, "$ref": "#/$defs/Loop"}):
        with pytest.raises(ValueError):
            gemini_response_schema(bad, "inline")


def test_profile_binding_changes_only_gemini_policy_and_not_openrouter_wire_schema():
    first = auditor("gemini")
    second = auditor("gemini", gemini_schema_profile="compact")
    assert first.policy_identity() != second.policy_identity()
    assert auditor().policy_identity() == auditor(gemini_schema_profile="inline").policy_identity()
    assert auditor("gemini", gemini_schema_profile="invalid").config.error_code() == "auditor_gemini_schema_profile_invalid"
    _, _, payload = auditor(gemini_schema_profile="inline")._request("{}")
    assert payload["response_format"]["json_schema"]["schema"] == CompactBatchSelection.model_json_schema()


@pytest.mark.asyncio
async def test_gemini_metadata_and_thinking_parts_do_not_pollute_json():
    claim, article = inputs()
    response = reply(evidence(claim, article), "gemini").json()
    parts = response["candidates"][0]["content"]["parts"]
    parts.insert(0, {"thought": True, "text": "private reasoning, not the audit JSON"})
    response.update(modelVersion="gemini-3.8-flash", usageMetadata={"promptTokenCount": 120, "candidatesTokenCount": 35})
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response))) as client:
        result = await auditor("gemini").audit(claim, article, client=client)
    assert result.outcome == "verified"
    assert result.transport.actual_model == "gemini-3.8-flash" and result.transport.finish_reason == "STOP"
    assert (result.transport.prompt_tokens, result.transport.completion_tokens) == (120, 35)
    assert result.provider_request_id == "fixture-request-2"
    assert "private reasoning" not in result.model_dump_json()


@pytest.mark.asyncio
@pytest.mark.parametrize("parts", [[{"thought": True, "text": "only thoughts"}],
                                  [{"thought": "true", "text": "{}"}], [{"functionCall": {}}]])
async def test_gemini_requires_final_text_json(parts):
    claim, article = inputs()
    response = reply(evidence(claim, article), "gemini").json()
    response["candidates"][0]["content"]["parts"] = parts
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response))) as client:
        result = await auditor("gemini").audit(claim, article, client=client)
    assert result.outcome == "invalid" and result.evidence is None


@pytest.mark.asyncio
@pytest.mark.parametrize("candidates", [[None], [42], ["text"], [[]]])
async def test_gemini_malformed_envelope_is_invalid_not_an_uncaught_exception(candidates):
    claim, article = inputs()
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"candidates": candidates}))) as client:
        result = await auditor("gemini").audit(claim, article, client=client)
    assert result.outcome == "invalid" and result.reason_code == "auditor_response_invalid"
    assert result.evidence is None


@pytest.mark.asyncio
@pytest.mark.parametrize("profile", GEMINI_SCHEMA_PROFILES)
@pytest.mark.parametrize("problem", ["index_bool", "index_large", "excess_evidence", "extra", "duplicate_id", "unknown_id", "excess_results"])
async def test_wire_projection_cannot_weaken_returned_result_validation(profile, problem):
    claim, article = inputs()
    row = {"candidate_id": "single", **evidence(claim, article)}
    for fact in ("place", "status", "time", "depth"):
        row[fact]["evidence"] = [{"option_index": 0}]
    if problem == "index_bool": row["place"]["evidence"] = [{"option_index": True}]
    if problem == "index_large": row["place"]["evidence"] = [{"option_index": 256}]
    if problem == "excess_evidence": row["place"]["evidence"] *= 13
    if problem == "extra": row["unrequested"] = "do not accept"
    if problem == "unknown_id": row["candidate_id"] = "foreign"
    rows = [row] * (9 if problem == "excess_results" else 2 if problem == "duplicate_id" else 1)
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: reply({"results": rows}, "gemini"))) as client:
        result = await auditor("gemini", gemini_schema_profile=profile).audit(claim, article, client=client)
    assert result.outcome == "invalid" and result.evidence is None


def test_account_identity_uses_selected_credential_without_changing_openrouter_identity():
    first = auditor("gemini", gemini_api_key="gemini-one")
    changed = auditor("gemini", gemini_api_key="gemini-two")
    irrelevant = auditor("gemini", gemini_api_key="gemini-one", openrouter_api_key="router-two", config_revision="2")
    assert quota_identity(first) != quota_identity(changed)
    assert quota_identity(first) == quota_identity(irrelevant)
    expected = "account-v2:" + hashlib.sha256(b"openrouter\0synthetic-router").hexdigest()
    assert quota_identity(auditor()) == expected


@pytest.mark.asyncio
async def test_gemini_cannot_replace_saved_openrouter_cooldowns(status_db):
    factory = sessionmaker(bind=status_db.get_bind())
    router = auditor()
    state = read_quota(status_db, identity=quota_identity(router))
    state.blocked_until = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    state.remaining = 0
    save_quota(factory, state)
    await check_quota(factory, auditor("gemini"))
    with factory() as db:
        preserved = read_quota(db, identity=quota_identity(router))
    assert preserved.blocked_until == state.blocked_until and preserved.remaining == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("profile", GEMINI_SCHEMA_PROFILES)
@pytest.mark.parametrize("problem", ["missing", "foreign_evidence", "wrong_type", "malformed", "truncated", "oversized"])
async def test_gemini_profiles_reject_incomplete_or_foreign_results(profile, problem):
    from tests.test_news_batch_audit import sample, rows
    candidates, article = sample(2)
    payload = rows(candidates, article)
    if problem == "missing": payload.pop()
    if problem == "foreign_evidence": payload[1]["place"]["evidence"] = payload[0]["place"]["evidence"]
    if problem == "wrong_type": payload[1]["status"]["confirmed"] = "true"
    if problem == "malformed": payload[1].pop("depth")
    response = reply({"results": payload}, "gemini")
    if problem == "truncated": response = httpx.Response(200, content=b'{"candidates":[')
    if problem == "oversized": response = httpx.Response(200, content=b" " * 65537)
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: response)) as client:
        results = await auditor("gemini", gemini_schema_profile=profile).audit_batch(candidates, article, client=client)
    assert results["1"].outcome != "verified" and results["1"].evidence is None
    if problem not in {"truncated", "oversized"}:
        assert results["0"].outcome == "verified"


@pytest.mark.asyncio
async def test_gemini_tracks_dispatch_and_account_cooldown_without_quota_http(status_db):
    factory = sessionmaker(bind=status_db.get_bind())
    service = auditor("gemini")
    calls = []
    def forbidden(request):
        calls.append(request)
        raise AssertionError("Gemini cannot call the OpenRouter quota endpoint")
    async with httpx.AsyncClient(transport=httpx.MockTransport(forbidden)) as client:
        state = await check_quota(factory, service, client=client)
        dispatched(factory, state, 8)
        assert state.used is state.limit is state.remaining is None
        assert state.request_count == 1 and state.claims_dispatched == 8
        result = timeout_result(provider_http_status=429).model_copy(update={"reason_code": "auditor_rate_limited", "retry_after_seconds": 120})
        record_error(factory, state, result)
        after = await check_quota(factory, auditor("gemini", model="backup", gemini_schema_profile="compact"), client=client)
        assert after.blocked_until == state.blocked_until and not calls


def test_permanent_request_error_cools_down_configuration_and_reports_gemini_state(status_db, monkeypatch):
    factory = sessionmaker(bind=status_db.get_bind())
    service = auditor("gemini")
    now = datetime.now(timezone.utc)
    result = timeout_result(provider_http_status=400).model_copy(update={"reason_code": "auditor_http_error"})
    state = record_availability(factory, service, result, now=now)
    assert deadline(state.blocked_until) == now + timedelta(minutes=60) and state.last_http_status == 400
    with factory() as db:
        assert read_availability(db, auditor("gemini", gemini_schema_profile="compact")).blocked_until is None
        assert read_availability(db, auditor("gemini", config_revision="repair-2")).blocked_until is None
    monkeypatch.setattr("app.services.news_claim_auditor.NewsClaimAuditor", lambda: service)
    from app.services.news_automation_service import read_news_automation
    status = read_news_automation(status_db)
    assert status.audit.state == "model_cooldown" and status.audit.http_status == 400
    assert status.audit.used is status.audit.limit is status.audit.remaining is None


def test_gemini_readiness_is_offline_unless_probe_is_explicit(monkeypatch):
    calls = []
    async def fake(self, claim, article):
        calls.append(article)
        assert claim.is_historical and claim.event_time_resolved.year == 2020
        return SimpleNamespace(evidence=object(), outcome="review", reason_code="historical_claim_evidence")
    monkeypatch.setattr(NewsClaimAuditor, "audit", fake)
    config = auditor("gemini").config
    assert asyncio.run(check_auditor(config))["status"] == "configuration_ok" and not calls
    result = asyncio.run(check_auditor(config, probe=True))
    assert result["status"] == "valid_response" and len(calls) == 1
    assert not result["database_access"] and not result["public_data_written"]
