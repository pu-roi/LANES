"""Batch transport preserves per-claim evidence; never accesses a live provider."""
import json
from datetime import datetime, timezone

import httpx
import pytest

from app.schemas.news_audit_batch import AuditCandidate
from app.services.news_claim_auditor import safe_retry_seconds
from tests.test_news_claim_auditor import inputs, evidence, auditor, reply


def sample(count=8):
    original, article = inputs()
    claims, parts, cursor = [], [], 0
    for i in range(count):
        road = f"Sample Road {i}"
        body = original.evidence_sentence.replace("Sample Road", road)
        start = cursor + body.index(road)
        claim = original.model_copy(update={"raw_place_name": road, "canonical_road": road,
            "evidence_sentence": body, "evidence_sentence_offset": (cursor, cursor+len(body)),
            "place_char_start": start, "place_char_end": start+len(road)})
        claims.append(AuditCandidate(candidate_id=str(i), claim=claim))
        parts.append(body)
        cursor += len(body)+1
    article.article_text = "\n".join(parts)
    return tuple(claims), article


def rows(candidates, article):
    result = []
    for candidate in candidates:
        row = evidence(candidate.claim, article)
        begin, end = candidate.claim.evidence_sentence_offset
        for fact in ("place", "status", "time", "depth"):
            row[fact]["evidence"] = [{"start": begin, "end": end, "quote": article.article_text[begin:end]}]
        result.append({"candidate_id": candidate.candidate_id, **row})
    return result


@pytest.mark.asyncio
async def test_reordered_batch_verifies_separate_claims_and_sends_body_once():
    candidates, article = sample()
    responses = rows(candidates, article)[::-1]
    calls = []
    def handler(request):
        document = json.loads(json.loads(request.content)["messages"][1]["content"])
        assert "article_text" not in document["article"]
        assert document["evidence_text"] == article.article_text
        assert len(document["candidates"]) == 8
        calls.append(request)
        return reply({"results": responses})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await auditor().audit_batch(candidates, article, client=client)
    assert len(calls) == 1 and len(result) == 8
    assert all(result[c.candidate_id].outcome == "verified" for c in candidates)
    assert [result[c.candidate_id].evidence.place.raw_place_name for c in candidates] == [c.claim.raw_place_name for c in candidates]


@pytest.mark.asyncio
@pytest.mark.parametrize("problem", ["missing", "malformed", "foreign_evidence", "wrong_hash", "duplicate", "unknown"])
async def test_batch_failures_cannot_approve_other_claims(problem):
    candidates, article = sample(2)
    responses = rows(candidates, article)
    if problem == "missing":
        responses.pop()
    elif problem == "malformed":
        responses[1].pop("depth")
    elif problem == "foreign_evidence":
        responses[1]["place"]["evidence"] = responses[0]["place"]["evidence"]
    elif problem == "wrong_hash":
        responses[1]["claim_sha256"] = "0"*64
    elif problem == "duplicate":
        responses[1]["candidate_id"] = responses[0]["candidate_id"]
    elif problem == "unknown":
        responses[1]["candidate_id"] = "999"
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: reply({"results": responses}))) as client:
        result = await auditor().audit_batch(candidates, article, client=client)
    if problem in ("duplicate", "unknown"):
        assert all(r.outcome == "invalid" for r in result.values())
    else:
        assert result["0"].outcome == "verified"
        assert result["1"].outcome != "verified"
        assert result["1"].retryable == (problem == "missing")


@pytest.mark.parametrize("headers,expected", [
    ({"retry-after": "90"}, 90), ({"retry-after": "-1"}, None),
    ({"retry-after": "secret untrusted message"}, None),
    ({"retry-after": "999999999"}, 86400),
    ({"x-ratelimit-reset": "1767225720"}, 120),
    ({"retry-after": "Thu, 01 Jan 2026 00:01:00 GMT"}, 60),
])
def test_retry_headers_are_bounded_safe_delays(headers, expected):
    assert safe_retry_seconds(httpx.Headers(headers), now=datetime(2026, 1, 1, tzinfo=timezone.utc)) == expected
