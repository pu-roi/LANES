"""Rule-based evidence validation cannot spend credits or approve fabricated facts."""
import json
from pathlib import Path

import httpx
import pytest

from app.schemas.news_audit_batch import AuditCandidate
from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_claim_auditor import AuditorConfig, NewsClaimAuditor, canonical_claim_sha256
from app.services.hybrid_extraction_service import HybridExtractionService
from tests.test_news_september24_replay import article


def rules():
    return NewsClaimAuditor(AuditorConfig(provider="source_rules", model="source-rules-v1"))


@pytest.mark.asyncio
async def test_captured_roads_and_clearances_are_source_checked_without_http():
    source = article()
    extraction = await HybridExtractionService().extract_hybrid(source, mode="rules_only")
    candidates = tuple(AuditCandidate(candidate_id=str(i), claim=c) for i, c in enumerate(extraction.claims)
                       if c.place_type == "street")
    def forbidden(request):
        pytest.fail("Source rules attempted external inference")
    before = [canonical_claim_sha256(c.claim) for c in candidates]
    async with httpx.AsyncClient(transport=httpx.MockTransport(forbidden)) as client:
        results = await rules().audit_batch(candidates, source, client=client)
    assert len(results) == 5 and all(r.outcome == "verified" for r in results.values())
    assert all(r.provider == "source_rules" and r.provider_http_status is None for r in results.values())
    assert before == [canonical_claim_sha256(c.claim) for c in candidates]
    for result in results.values():
        for fact in (result.evidence.place, result.evidence.status, result.evidence.time,
                     result.evidence.depth, result.evidence.access):
            for span in fact.evidence:
                assert source.article_text[span.start:span.end] == span.quote


@pytest.mark.asyncio
@pytest.mark.parametrize("updates", [
    {"canonical_city": "Quezon City"}, {"depth_raw": "19-inch", "depth_canonical": "knee"},
    {"road_passability": "impassable_all"}, {"event_time_raw": "As of 9:00 p.m."},
    {"is_forecast": True}, {"place_char_start": 0},
])
async def test_altered_facts_or_source_offsets_never_verify(updates):
    source = article()
    claims = (await HybridExtractionService().extract_hybrid(source, mode="rules_only")).claims
    claim = next(c for c in claims if c.raw_place_name == "Boni Avenue").model_copy(update=updates)
    result = await rules().audit(claim, source)
    assert result.outcome != "verified"


@pytest.mark.asyncio
async def test_original_repeated_roads_preserve_parent_identity_and_prefer_measurement():
    cases = json.loads((Path(__file__).parent / "fixtures/mcp_saved_news.json").read_text(encoding="utf-8"))
    case = next(c for c in cases if len(c["candidates"]) == 8)
    source = NewsArticleExtractorInput.model_validate(case["article"])
    candidates = tuple(AuditCandidate.model_validate(c) for c in case["candidates"])
    result = await rules().audit_batch(candidates, source)
    assert len(result) == 8
    assert sum(r.outcome == "verified" for r in result.values()) == 8
    measured = result[candidates[-1].candidate_id].evidence.depth
    assert measured.raw == "19 inches" and measured.canonical == "knee"
    assert all(result[c.candidate_id].evidence.place.canonical_barangay == c.claim.canonical_barangay
               for c in candidates)


@pytest.mark.asyncio
@pytest.mark.parametrize("case_index", [3, 4])
async def test_original_ambiguous_and_negative_fixtures_stay_unverified(case_index):
    cases = json.loads((Path(__file__).parent / "fixtures/mcp_saved_news.json").read_text(encoding="utf-8"))
    case = cases[case_index]
    result = await rules().audit_batch(tuple(AuditCandidate.model_validate(c) for c in case["candidates"]),
                                     NewsArticleExtractorInput.model_validate(case["article"]))
    assert all(r.outcome != "verified" for r in result.values())


def test_rules_need_no_key_and_have_distinct_policy_identity():
    auditor = rules()
    assert auditor.config.error_code() is None
    assert auditor.policy_identity()["validation_mode"] == "source_rules"
    assert auditor.policy_identity()["prompt_version"] == "source-rules-v2-measurement-first"
    assert AuditorConfig(provider="source_rules", model="invented").error_code() is not None


def test_display_preserves_saved_evidence_without_decorative_bullets_or_added_ellipsis():
    from app.services.news_presentation_service import news_evidence_excerpt
    cases = json.loads((Path(__file__).parent / "fixtures/mcp_saved_news.json").read_text(encoding="utf-8"))
    claim = AuditCandidate.model_validate(cases[2]["candidates"][5]).claim
    original = canonical_claim_sha256(claim)
    excerpt = news_evidence_excerpt(claim)
    assert "West Riverside" in excerpt and "19 inches" in excerpt and "Damayan" in excerpt
    assert excerpt == claim.evidence_sentence.replace("\u25b6\ufe0f ", "")
    assert "\u25b6" not in excerpt and " … " not in excerpt
    assert len(excerpt) > 250
    assert canonical_claim_sha256(claim) == original


@pytest.mark.parametrize("text,raw,canonical", [
    ("Half knee-deep (19 inches)", "19 inches", "knee"),
    ("Knee-deep (8 inches)", "8 inches", "gutter"),
    ("Half knee-deep", "Half knee-deep", "half-knee"),
    ("Knee-deep (18 inches)", "18 inches", None),
    ("Half knee-deep (up to 19 inches)", "up to 19 inches", "knee"),
])
def test_shared_extractor_prefers_measurements_and_retains_qualifiers(text, raw, canonical):
    from app.services.taglish_extraction_service import extract_depth_from_text
    actual_raw, actual_canonical, _, reasons = extract_depth_from_text(text)
    assert (actual_raw, actual_canonical) == (raw, canonical)
    if "up to" in text:
        assert "upper_bound_depth" in reasons
    if "18 inches" in text:
        assert "numeric_depth_not_canonical" in reasons
