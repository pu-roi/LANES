"""Failure phases, immutable binding and real-clock recovery; no live provider."""
import asyncio
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy.orm import sessionmaker

from app.schemas.news_audit import AuditTransportDiagnostics, IndependentAuditResult
from app.services.news_claim_auditor import NewsClaimAuditor
from app.services.news_audit_availability_service import record_availability, read_availability
from app.services.news_audit_quota_service import check_quota, deadline
from tests.test_news_claim_auditor import inputs, auditor, reply
from tests.test_news_batch_audit import sample, rows
from tests.test_news_automation import status_db


class StalledBody(httpx.AsyncByteStream):
    closed = False

    async def __aiter__(self):
        yield b'{"id":"partial'
        await asyncio.sleep(2)

    async def aclose(self):
        self.closed = True


@pytest.mark.asyncio
async def test_headers_and_partial_body_survive_overall_timeout_and_close_stream():
    claim, article = inputs()
    body = StalledBody()
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200,
            headers={"x-generation-id": "gen-partial", "x-request-id": "gateway-one"}, stream=body))) as client:
        result = await NewsClaimAuditor(auditor().config, timeout_seconds=1).audit(claim, article, client=client)
        assert not client.is_closed
    assert result.reason_code == "auditor_timeout" and result.provider_http_status == 200
    assert result.provider_request_id == "gen-partial" and body.closed
    diagnostic = result.transport
    assert diagnostic.phase == "body" and diagnostic.timeout_kind == "overall"
    assert diagnostic.response_bytes == len(b'{"id":"partial')
    assert diagnostic.gateway_request_id == "gateway-one"
    assert diagnostic.timings_ms["first_body"] >= diagnostic.timings_ms["headers"]
    assert "body_complete" not in diagnostic.timings_ms
    assert 900 <= diagnostic.elapsed_ms <= 1500


@pytest.mark.asyncio
@pytest.mark.parametrize("exception,kind", [(httpx.ConnectTimeout, "connect"), (httpx.ReadTimeout, "read"),
    (httpx.WriteTimeout, "write"), (httpx.PoolTimeout, "pool")])
async def test_transport_timeout_subtypes_are_preserved_without_raw_errors(exception, kind):
    claim, article = inputs()
    def handler(request):
        raise exception("untrusted credential-shaped error")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await auditor().audit(claim, article, client=client)
    assert result.transport.phase == "headers" and result.transport.timeout_kind == kind
    assert "credential-shaped" not in result.model_dump_json()


@pytest.mark.asyncio
async def test_compact_reordered_replies_bind_hashes_and_reject_cross_road_evidence():
    candidates, article = sample(2)
    response = rows(candidates, article)
    for row in response:
        row.pop("claim_sha256")
    response[1]["place"]["evidence"] = response[0]["place"]["evidence"]
    envelope = json.loads(reply({"results": response[::-1]}).content)
    envelope.update(model="fixture/actual:free", usage={"prompt_tokens": 123, "completion_tokens": 42})
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=envelope))) as client:
        result = await auditor().audit_batch(candidates, article, client=client)
    assert result["0"].outcome == "verified" and result["1"].reason_code == "audit_place_evidence_missing"
    assert result["0"].evidence.claim_sha256 == result["0"].claim_sha256
    assert result["0"].transport.actual_model == "fixture/actual:free"
    assert result["0"].transport.phase == "complete" and result["0"].transport.completion_tokens == 42


def timeout_result(**updates):
    return IndependentAuditResult(outcome="unavailable", reason_code="auditor_timeout", retryable=True,
        prompt_version="fixture", response_version="fixture", input_sha256="a"*64, claim_sha256="b"*64, **updates)


@pytest.mark.asyncio
async def test_same_named_road_in_another_source_occurrence_cannot_approve_candidate():
    from tests.test_news_claim_auditor import evidence
    claim, article = inputs()
    original_length = len(article.article_text)
    article.article_text += "\n" + article.article_text
    response = evidence(claim, article)
    response.pop("claim_sha256")
    response["place"]["evidence"] = [{"start": original_length+1, "end": len(article.article_text),
        "quote": article.article_text[original_length+1:]}]
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: reply(response))) as client:
        result = await auditor().audit(claim, article, client=client)
    assert result.reason_code == "audit_place_occurrence_mismatch" and result.evidence is None


@pytest.mark.asyncio
async def test_correct_road_and_barangay_without_city_heading_still_cannot_approve():
    from tests.test_news_claim_auditor import evidence
    claim, article = inputs()
    road = "Sample Road is flooded, knee-deep as of 10:55 AM on October 5, 2026."
    article.article_text = "Pasig City\nBarangay San Antonio\n" + road
    begin = article.article_text.index(road)
    claim.evidence_sentence = article.article_text
    claim.evidence_sentence_offset = (0,len(article.article_text))
    claim.place_char_start = begin
    claim.place_char_end = begin + len(claim.raw_place_name)
    response = evidence(claim,article)
    start = article.article_text.index("Barangay")
    response["place"]["evidence"] = [{"start":start,"end":len(article.article_text),"quote":article.article_text[start:]}]
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:reply(response))) as client:
        result = await auditor().audit(claim,article,client=client)
    assert result.reason_code == "audit_parent_locality_evidence_missing" and result.evidence is None


def test_two_failures_then_recovery_backoff_and_success_reset(status_db):
    factory = sessionmaker(bind=status_db.get_bind())
    service = auditor()
    now = datetime.now(timezone.utc)
    first = record_availability(factory, service, timeout_result(), now=now)
    assert first.blocked_until is None
    state = record_availability(factory, service, timeout_result(), now=now)
    assert deadline(state.blocked_until) == now + timedelta(minutes=15)
    for delay in (30, 60, 60):
        now = deadline(state.blocked_until)
        state = record_availability(factory, service, timeout_result(), now=now)
        assert deadline(state.blocked_until) == now + timedelta(minutes=delay)
    successful = timeout_result(provider_http_status=200).model_copy(update={"outcome": "verified", "reason_code": "claim_evidence_verified"})
    state = record_availability(factory, service, successful, now=deadline(state.blocked_until))
    assert state.blocked_until is None and state.consecutive_failures == state.recovery_failures == 0
    with factory() as db:
        assert read_availability(db, service) == state


@pytest.mark.asyncio
async def test_model_and_prompt_changes_do_not_bypass_account_quota_cooldown(status_db):
    factory = sessionmaker(bind=status_db.get_bind())
    first = auditor(model="fixture/one:free")
    second = auditor(model="fixture/two:free", config_revision="2")
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"data": {"free_model_daily_requests": {"used": 50, "limit": 50, "remaining": 0}}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        a = await check_quota(factory, first, client=client)
        b = await check_quota(factory, second, client=client)
    assert len(calls) == 1 and a.identity == b.identity and b.remaining == 0


def test_diagnostic_rejects_arbitrary_fields_names_and_out_of_bound_values():
    from pydantic import ValidationError
    for update in ({"raw_body": "SECRET"}, {"elapsed_ms": -1}, {"timings_ms": {"SECRET": 1}},
                   {"timings_ms": {"headers": 4_000_000}}, {"actual_model": "invalid\nheader"}):
        with pytest.raises(ValidationError):
            AuditTransportDiagnostics(**{"phase": "body", "elapsed_ms": 1, "candidate_count": 1, **update})


@pytest.mark.asyncio
@pytest.mark.parametrize("status,retryable", [(400, False), (503, True)])
async def test_error_body_disconnect_keeps_known_http_disposition(status, retryable):
    class DisconnectedBody(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield b'{"error":'
            raise httpx.ReadError("unsafe provider body")
    claim, article = inputs()
    async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda r: httpx.Response(status, stream=DisconnectedBody()))) as client:
        result = await auditor().audit(claim, article, client=client)
    assert result.provider_http_status == status and result.retryable is retryable
    assert result.transport.phase == "body" and result.transport.response_bytes == 9
    assert "first_body" in result.transport.timings_ms
    assert "unsafe provider" not in result.model_dump_json()


def test_expired_model_circuit_waits_for_a_real_probe_in_read_only_status(status_db, monkeypatch):
    from app.services.news_audit_availability_service import ModelAvailability, model_identity, AVAILABILITY_KEY
    from app.services.news_automation_service import read_news_automation
    from app.services.news_claim_auditor import NewsClaimAuditor
    from app.models.setting import SystemSetting
    service = NewsClaimAuditor()
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    state = ModelAvailability(blocked_until=past.isoformat(), consecutive_failures=2)
    status_db.add(SystemSetting(key=AVAILABILITY_KEY, value={model_identity(service):state.model_dump(mode="json")}))
    status_db.commit()
    assert read_news_automation(status_db).audit.state == "awaiting_model_check"
    assert read_availability(status_db, service).blocked_until == state.blocked_until


@pytest.mark.parametrize("value,expected", [("4", 4), ("8", 8)])
def test_supported_batch_profile_loads_from_real_environment_strings(monkeypatch, value, expected):
    from app.services.news_claim_auditor import AuditorConfig
    monkeypatch.setenv("LANES_NEWS_AUDITOR_BATCH_SIZE", value)
    assert AuditorConfig.from_environment().batch_size == expected


@pytest.mark.parametrize("value", ["0", "8.0", "16", "true"])
def test_invalid_environment_batch_profile_is_not_coerced(monkeypatch, value):
    from app.services.news_claim_auditor import AuditorConfig
    from pydantic import ValidationError
    monkeypatch.setenv("LANES_NEWS_AUDITOR_BATCH_SIZE", value)
    with pytest.raises(ValidationError):
        AuditorConfig.from_environment()


def test_full_runtime_pipeline_identity_fits_existing_storage_without_schema_change():
    from app.crud.news_processing import current_pipeline_version
    from app.models.news import NewsExtractionRun
    version = current_pipeline_version()
    assert len(version) <= NewsExtractionRun.__table__.c.pipeline_version.type.length
    assert len(version.rsplit(":", 1)[1]) == 64


def test_explicit_option_locators_cover_late_same_named_occurrence_without_preconfirming():
    from app.schemas.news_audit_batch import AuditCandidate
    claim, article = inputs()
    sentence = article.article_text
    article.article_text = sentence + "\n" + "Context only.\n"*300 + sentence
    begin = article.article_text.rindex(sentence)
    claim.evidence_sentence = article.article_text
    claim.evidence_sentence_offset = (0,len(article.article_text))
    claim.place_char_start = begin + sentence.index(claim.raw_place_name)
    claim.place_char_end = claim.place_char_start + len(claim.raw_place_name)
    document = json.loads(auditor().batch_document((AuditCandidate(candidate_id="late",claim=claim),),article))
    candidate = document["candidates"][0]
    assert candidate["source_occurrence"] == {"start":claim.place_char_start,"end":claim.place_char_end}
    assert candidate["source_option_indexes"] and 0 in candidate["source_option_indexes"]
    options = auditor()._batch_options((AuditCandidate(candidate_id="late",claim=claim),),article.article_text)
    assert all(options[i]["start"] <= claim.place_char_start < claim.place_char_end <= options[i]["end"]
        for i in candidate["source_option_indexes"])
    assert all(option["option_index"] == i for i,option in enumerate(document["evidence_options"]))
    assert "confirmed" not in candidate and "claim_sha256" not in candidate


def test_raw_measurement_without_mapped_gauge_keeps_explicit_unknown_in_wire():
    from app.schemas.news_audit_batch import AuditCandidate
    claim,article=inputs()
    claim.depth_raw="9 inches"
    claim.depth_canonical=None
    document=json.loads(auditor().batch_document((AuditCandidate(candidate_id="unknown",claim=claim),),article))
    assert document['candidates'][0]['claim']['depth_raw']=='9 inches'
    assert 'depth_canonical' in document['candidates'][0]['claim']
    assert document['candidates'][0]['claim']['depth_canonical'] is None


def test_valid_place_crossing_quote_chunk_boundary_still_has_an_exact_locator():
    from app.schemas.news_audit_batch import AuditCandidate
    from app.services.news_claim_auditor import MAX_EVIDENCE_QUOTE_CHARACTERS
    claim,article=inputs()
    article.article_text='x'*(MAX_EVIDENCE_QUOTE_CHARACTERS-5)+claim.evidence_sentence
    claim.evidence_sentence=article.article_text
    claim.evidence_sentence_offset=(0,len(article.article_text))
    claim.place_char_start=article.article_text.index(claim.raw_place_name)
    claim.place_char_end=claim.place_char_start+len(claim.raw_place_name)
    candidates=(AuditCandidate(candidate_id='split',claim=claim),)
    document=json.loads(auditor().batch_document(candidates,article))
    assert 0 in document['candidates'][0]['source_option_indexes']
    offered=document['evidence_options'][0]['quote']
    assert claim.raw_place_name in offered and offered in article.article_text
    assert len(offered)<=MAX_EVIDENCE_QUOTE_CHARACTERS


def test_compact_locators_keep_distinct_labels_and_true_rule_flags_without_changing_claim():
    from app.schemas.news_audit_batch import AuditCandidate
    claim,article=inputs()
    before=claim.model_dump(mode='json')
    document=json.loads(auditor().batch_document((AuditCandidate(candidate_id='plain',claim=claim),),article))
    supplied=document['candidates'][0]['claim']
    assert supplied['raw_place_name']==claim.raw_place_name and supplied['condition']==claim.condition
    assert 'canonical_road' not in supplied and 'evidence_sentence_offset' not in supplied
    assert not any(flag in supplied for flag in ('is_forecast','is_negated','is_historical'))
    assert claim.model_dump(mode='json')==before
    claim.canonical_road='Distinct mapped road label'
    claim.is_forecast=claim.is_negated=claim.is_historical=True
    supplied=json.loads(auditor().batch_document((AuditCandidate(candidate_id='distinct',claim=claim),),article))['candidates'][0]['claim']
    assert supplied['canonical_road']==claim.canonical_road
    assert all(supplied[flag] is True for flag in ('is_forecast','is_negated','is_historical'))


def test_oversized_pipeline_revision_is_rejected_before_database_writes(monkeypatch):
    from app.crud import news_processing
    monkeypatch.setattr(news_processing, "PIPELINE_VERSION", "x"*100)
    with pytest.raises(ValueError, match="pipeline_identity_oversized"):
        news_processing.current_pipeline_version()


@pytest.mark.asyncio
@pytest.mark.parametrize("parent_text,reason", [("Sto. Domingo", "claim_evidence_verified"),
    ("Sto Domingo", "claim_evidence_verified"), ("Santo Domingo", "claim_evidence_verified"),
    ("Santa Domingo", "audit_parent_locality_evidence_missing"),
    ("Santo Tomas", "audit_parent_locality_evidence_missing")])
async def test_generic_santo_abbreviation_preserves_correct_parent_and_source_quotes(parent_text, reason):
    from tests.test_news_claim_auditor import evidence
    claim, article = inputs()
    body = claim.evidence_sentence.replace("Pasig City", "Quezon City, Brgy. " + parent_text)
    article.article_text = body
    claim = claim.model_copy(update={"canonical_city": "Quezon City", "canonical_barangay": "Santo Domingo",
        "evidence_sentence": body, "evidence_sentence_offset": (0, len(body))})
    response = evidence(claim, article)
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: reply(response))) as client:
        result = await auditor().audit(claim, article, client=client)
    assert result.reason_code == reason
    if result.evidence:
        assert parent_text in result.evidence.place.evidence[0].quote


@pytest.mark.asyncio
async def test_http_rejection_retains_safe_category_without_upstream_message():
    claim, article = inputs()
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(400,
        json={"error": {"message": "Invalid JSON schema NEVER_PERSIST_THIS", "metadata": {"raw": "SECRET"}}}))) as client:
        result = await auditor().audit(claim, article, client=client)
    assert result.reason_code == "auditor_http_error" and not result.retryable
    assert result.transport.error_category == "schema_rejected"
    assert "NEVER_PERSIST" not in result.model_dump_json() and "SECRET" not in result.model_dump_json()
