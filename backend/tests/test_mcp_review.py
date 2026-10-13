"""Immutable review contracts: no real provider, database or publication calls."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.mcp_review import MCPAuditProposal
from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from app.services import mcp_review_service as service
from app.services.news_claim_auditor import canonical_input_sha256, canonical_claim_sha256
from tests.test_news_batch_audit import sample, rows


def record(candidates, article, run_id=10):
    return (SimpleNamespace(id=run_id, pipeline_version="frozen-v1", result={
        "claims": [c.claim.model_dump(mode="json") for c in candidates]}),
        SimpleNamespace(id=20, input_snapshot=article.model_dump(mode="json"),
                        input_fingerprint=canonical_input_sha256(article)))


@pytest.fixture
def saved(monkeypatch):
    candidates, article = sample(2)
    stored = record(candidates, article)
    monkeypatch.setattr(service, "saved_run", lambda db, run_id: stored if run_id == 10 else None)
    return candidates, article, stored


def proposal(saved):
    bundle = service.get_bundle(None, 10, (0, 1))
    candidates, article, _ = saved
    options = service.NewsClaimAuditor._batch_options(candidates, article.article_text)
    selections = rows(candidates, article)
    for i, row in enumerate(selections):
        row["candidate_id"] = f"run_10_claim_{i}"
        row.pop("claim_sha256")
        for name in ("place", "status", "time", "depth", "access"):
            row[name]["evidence"] = [{"option_index": options.index(span)} for span in row[name]["evidence"]]
    return {"bundle": bundle["reference"], "results": selections}


def parse(value):
    return MCPAuditProposal.model_validate_json(json.dumps(value))


def test_complete_preview_preserves_saved_claims_and_has_no_provider_dispatch(saved, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Provider dispatch is forbidden")
    monkeypatch.setattr(service.NewsClaimAuditor, "_request", forbidden)
    before = copy.deepcopy(saved[2][0].result)
    result = service.preview(None, parse(proposal(saved)))
    assert [r["outcome"] for r in result["results"]] == ["verified", "verified"]
    assert result["preview_only"] and not result["publication_permitted"] and not result["may_affect_routing"]
    assert result["model"] is None and saved[2][0].result == before


@pytest.mark.parametrize("problem", ["missing", "duplicate", "unknown", "changed_bundle"])
def test_invalid_batch_identity_rejects_entire_preview(saved, problem):
    value = proposal(saved)
    if problem == "missing": value["results"].pop()
    elif problem == "duplicate": value["results"][1]["candidate_id"] = value["results"][0]["candidate_id"]
    elif problem == "unknown": value["results"][1]["candidate_id"] = "other"
    else: value["bundle"]["bundle_sha256"] = "0" * 64
    with pytest.raises(service.MCPReviewError): service.preview(None, parse(value))


@pytest.mark.parametrize("problem", ["extra", "wrong_bool", "wrong_index", "excess_evidence", "malformed", "truncated"])
def test_strict_proposal_validation(saved, problem):
    value = proposal(saved)
    if problem == "extra": value["actor"] = 3
    elif problem == "wrong_bool": value["results"][0]["place"]["confirmed"] = "true"
    elif problem == "wrong_index": value["results"][0]["place"]["evidence"][0]["option_index"] = "0"
    elif problem == "excess_evidence": value["results"][0]["place"]["evidence"] *= 13
    elif problem == "malformed": value["results"][0].pop("depth")
    content = json.dumps(value)
    if problem == "truncated": content = content[:-5]
    with pytest.raises(ValidationError): MCPAuditProposal.model_validate_json(content)


@pytest.mark.parametrize("problem", ["absent_index", "foreign_evidence", "depth_mismatch", "observation_mismatch"])
def test_evidence_errors_never_verify_affected_claim(saved, problem):
    value = proposal(saved)
    fact = value["results"][1]
    if problem == "absent_index": fact["place"]["evidence"] = [{"option_index": 255}]
    elif problem == "foreign_evidence": fact["place"]["evidence"] = value["results"][0]["place"]["evidence"]
    elif problem == "depth_mismatch": fact["depth"]["raw"] = "19 inches"
    else: fact["time"]["observed_at"] = "2026-10-06T07:00:00Z"
    result = service.preview(None, parse(value))
    assert result["results"][0]["outcome"] == "verified"
    assert result["results"][1]["outcome"] == "invalid"


@pytest.mark.parametrize("indexes", [(), (0, 0), (-1,), tuple(range(9)), (999,)])
def test_bad_claim_indexes_are_rejected(saved, indexes):
    with pytest.raises(service.MCPReviewError): service.get_bundle(None, 10, indexes)


def test_changed_original_claim_invalidates_prior_bundle(saved):
    value = proposal(saved)
    saved[2][0].result["claims"][0]["depth_raw"] = "new evidence"
    with pytest.raises(service.MCPReviewError, match="identity_mismatch"):
        service.preview(None, parse(value))


def test_source_identity_mismatch_rejected(saved):
    saved[2][1].input_snapshot["title"] = "changed"
    with pytest.raises(service.MCPReviewError, match="source_identity_mismatch"):
        service.get_bundle(None, 10, (0,))


def test_bounded_evidence_is_refused_without_truncation(saved):
    article = saved[2][1].input_snapshot
    article["article_text"] += "x" * 200_000
    saved[2][1].input_fingerprint = canonical_input_sha256(NewsArticleExtractorInput.model_validate(article))
    with pytest.raises(service.MCPReviewError, match="oversized"):
        service.get_bundle(None, 10, (0,))


CASES = json.loads((Path(__file__).parent / "fixtures/mcp_saved_news.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_frozen_sources_and_original_claims_survive_framework_upgrade(case, monkeypatch):
    article = NewsArticleExtractorInput.model_validate(case["article"])
    from app.schemas.news_audit_batch import AuditCandidate
    candidates = tuple(AuditCandidate.model_validate(c) for c in case["candidates"])
    assert canonical_input_sha256(article) == case["input_sha256"]
    assert [canonical_claim_sha256(c.claim) for c in candidates] == case["claim_sha256"]
    monkeypatch.setattr(service, "saved_run", lambda *_: record(candidates, article))
    bundle = service.get_bundle(None, 10, tuple(range(len(candidates))))
    assert bundle["original_claims"] == [c.claim.model_dump(mode="json") for c in candidates]
    assert bundle["document"]["evidence_text"] == article.article_text.strip()
    assert len(bundle["document"]["candidates"]) == len(candidates)
    # Conservative host selections always remain a review, even for positive evidence.
    selections = []
    for i, c in enumerate(candidates):
        selections.append({"candidate_id": f"run_10_claim_{i}",
            "place": {"confirmed": False, "evidence": [], "raw_place_name": c.claim.raw_place_name,
                "canonical_city": c.claim.canonical_city, "canonical_barangay": c.claim.canonical_barangay},
            "status": {"confirmed": False, "evidence": [], "classification": "unclear",
                "contradictory": False, "historical": False},
            "time": {"confirmed": False, "evidence": [], "observed_at": None, "kind": "unspecified"},
            "depth": {"confirmed": False, "evidence": [], "canonical": None, "raw": None, "qualifiers": []},
            "access": {"confirmed": False, "evidence": [], "classification": "unknown"}})
    result = service.preview(None, parse({"bundle": bundle["reference"], "results": selections}))
    assert all(r["outcome"] == "review" for r in result["results"])
