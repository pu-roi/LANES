"""Offline stream, budget and conservative evidence acceptance tests."""
import asyncio
import json
from pathlib import Path

import httpx
import pytest

from app.services.chatgpt_plan_qualification import (
    QualificationError, audit_response, request_body, validate_selection,
)
from scripts.qualify_chatgpt_news import Budget
from scripts.qualify_news_gemini import load_cases


def completed(text='{"results": []}'):
    return {"type": "response.completed", "response": {"id": "resp_fixture", "model": "fixture-model",
        "status": "completed", "output": [{"type": "message", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": text}]}],
        "usage": {"input_tokens": 100, "output_tokens": 10}}}


def stream(*events):
    return b"".join(b"data: " + json.dumps(e).encode() + b"\r\n\r\n" for e in events)


def call(body, status=200):
    async def run():
        def handler(request):
            assert str(request.url) == "https://api.openai.com/v1/responses"
            return httpx.Response(status, content=body, headers={"x-request-id": "req_fixture"})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await audit_response(client, "synthetic-token", request_body("{}", "fixture-model"))
    return asyncio.run(run())


def test_request_contract_and_completed_stream():
    payload = request_body("{}", "fixture-model")
    assert payload["store"] is False and payload["stream"] is True
    assert not {"temperature", "max_output_tokens", "metadata", "background", "user"} & payload.keys()
    assert payload["input"][0]["role"] == "user"
    assert payload["text"]["format"]["strict"] is True
    text, metadata = call(stream({"type": "response.output_text.delta", "delta": "irrelevant"}, completed()))
    assert text == '{"results": []}'
    assert metadata["actual_model"] == "fixture-model" and metadata["input_tokens"] == 100


@pytest.mark.parametrize("body,expected", [
    (stream({"type": "response.output_text.delta", "delta": "{}"}), "stream_completion_missing"),
    (stream({"type": "response.failed", "response": {"error": {"code": "subscription_sharing_usage_limit_exceeded"}}}), "subscription_sharing_usage_limit_exceeded"),
    (stream(completed(), {"type": "response.failed", "response": {"error": {"code": "subscription_sharing_usage_unavailable"}}}), "subscription_sharing_usage_unavailable"),
    (stream({"type": "response.incomplete", "response": {}}), "response_incomplete"),
    (stream(completed(), completed()), "stream_completion_invalid"),
    (b'data: {"type":', "response_malformed"),
    (b'data: ' + b'x'*262145, "stream_event_oversized"),
    (stream(completed('x'*65537)), "response_oversized"),
], ids=["missing-complete", "quota-failed", "failed-after-complete", "incomplete", "duplicate-complete",
        "malformed-event", "oversized-event", "oversized-output"])
def test_failed_or_incomplete_stream_is_never_accepted(body, expected):
    with pytest.raises(QualificationError) as caught:
        call(body)
    assert caught.value.code == expected
    assert caught.value.http_status == 200


def test_http_error_is_safe_and_does_not_retry():
    with pytest.raises(QualificationError) as caught:
        call(json.dumps({"error": {"code": "subscription_sharing_user_not_eligible",
                                   "message": "private provider detail"}}).encode(), 403)
    assert caught.value.code == "subscription_sharing_user_not_eligible"
    assert caught.value.http_status == 403
    assert "private provider detail" not in str(caught.value)


def test_refusal_and_unknown_metadata():
    event = completed()
    event["response"]["output"][0]["content"] = [{"type": "refusal", "refusal": "no"}]
    with pytest.raises(QualificationError, match="response_refused_or_invalid"):
        call(stream(event))
    event = completed()
    del event["response"]["model"]
    del event["response"]["usage"]
    assert call(stream(event))[1]["actual_model"] is None


def test_commentary_never_becomes_the_final_selection():
    event = completed()
    event["response"]["output"][0]["phase"] = "final_answer"
    event["response"]["output"].insert(0, {"type": "message", "role": "assistant", "status": "completed",
        "phase": "commentary", "content": [{"type": "output_text", "text": "Untrusted preamble is not JSON."}]})
    assert call(stream(event))[0] == '{"results": []}'


def test_parser_failure_preserves_envelope_for_offline_investigation():
    event = completed()
    event["response"]["output"][0]["status"] = "incomplete"
    with pytest.raises(QualificationError) as caught:
        call(stream(event))
    assert caught.value.provider_response == event["response"]


def test_thin_completion_uses_finalized_item_events():
    completion = completed()
    item = completion["response"]["output"].pop()
    done = {"type": "response.output_item.done", "output_index": 0, "item": item}
    assert call(stream(done, completion))[0] == '{"results": []}'
    with pytest.raises(QualificationError, match="stream_completion_missing"):
        call(stream(done))
    with pytest.raises(QualificationError, match="stream_item_invalid"):
        call(stream(done, done, completion))


def test_transport_resume_preserves_used_attempt_and_never_accepts_account_failure(tmp_path):
    path = tmp_path / "ledger.json"
    budget = Budget(path, "identity", "fixture-model")
    entry = budget.reserve({"name": "first", "input_sha256": "source", "claim_sha256": []})
    entry.update(passed=False, http_status=200, error_code="response_message_invalid")
    budget.state.update(status="blocked", reason="response_message_invalid")
    budget.save()
    budget.close()
    resumed = Budget.resume_transport_repair(path, "identity", "fixture-model")
    assert len(resumed.state["attempts"]) == 1 and resumed.state["attempts"][0]["passed"] is False
    with pytest.raises(FileExistsError):
        Budget.resume_transport_repair(path, "identity", "fixture-model")
    resumed.state.update(status="blocked", reason="subscription_sharing_usage_limit_exceeded")
    resumed.save()
    resumed.close()
    with pytest.raises(QualificationError, match="transport_resume_not_permitted"):
        Budget.resume_transport_repair(path, "identity", "fixture-model")


def test_ledger_reserves_before_dispatch_and_cannot_reset(tmp_path):
    path = tmp_path / "ledger.json"
    budget = Budget(path, "identity", "fixture-model")
    for ordinal in range(5):
        budget.reserve({"name": str(ordinal), "input_sha256": "fixture", "claim_sha256": []})
        assert len(json.loads(path.read_text())["attempts"]) == ordinal + 1
    with pytest.raises(QualificationError, match="budget_exhausted"):
        budget.reserve({})
    with pytest.raises(FileExistsError):
        Budget(path, "new-identity", "different-model")
    budget.close()


@pytest.fixture
def negative():
    cases = load_cases(Path(__file__).parent / "fixtures/mcp_saved_news.json")
    case = cases[-1]
    candidate = case["candidates"][0]
    row = {"candidate_id": candidate.candidate_id,
        "place": {"confirmed": False, "evidence": [], "raw_place_name": candidate.claim.raw_place_name,
                  "canonical_city": None, "canonical_barangay": None},
        "status": {"confirmed": False, "evidence": [], "classification": "unclear", "contradictory": False, "historical": False},
        "time": {"confirmed": False, "evidence": [], "observed_at": None, "kind": "unspecified"},
        "depth": {"confirmed": False, "evidence": [], "canonical": None, "raw": None, "qualifiers": []},
        "access": {"confirmed": False, "evidence": [], "classification": "unknown"}}
    return case, row


def test_conservative_original_negative_is_review(negative):
    case, row = negative
    result = validate_selection(json.dumps({"results": [row]}), case)
    assert result[0]["outcome"] == "review" and result[0]["evidence"] is not None


@pytest.mark.parametrize("variant", ["duplicate", "unknown", "missing", "extra", "wrong_type", "index"])
def test_invalid_result_sets_or_fields_rejected(negative, variant):
    case, row = negative
    rows = [row]
    if variant == "duplicate": rows.append(row)
    if variant == "unknown": row["candidate_id"] = "other"
    if variant == "missing": rows = []
    if variant == "extra": row["unexpected"] = True
    if variant == "wrong_type": row["place"]["confirmed"] = "true"
    if variant == "index": row["place"]["evidence"] = [{"option_index": 256}]
    with pytest.raises((QualificationError, ValueError)):
        validate_selection(json.dumps({"results": rows}), case)
