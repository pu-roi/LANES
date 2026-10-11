"""Unit and regression tests for HybridExtractionService ensemble pipeline.

Verifies:
  1. Primary extraction by Taglish rules & PSGC reference grounding.
  2. Independent auditor strictly in supporting / double-check role.
  3. Fail-closed activation decisions:
     - Auditor-confirmed active flood without verified segment/time -> staff review.
     - Subsided flood ("humupa na") -> suppressed_subsided.
     - Weather forecast ("posibleng bahain") -> suppressed_forecast.
     - Broad city/province -> flagged_review.
  4. Nationwide geometry generation (50m corridor / circular buffer polygons).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from app.schemas.news_extraction import ExtractedClaim, LLMAuditResult, NewsArticleExtractorInput, RankedLocationCandidate
from app.services.hybrid_extraction_service import (
    HybridExtractionService,
    get_hybrid_extraction_service,
)


@pytest.fixture
def hybrid_service(monkeypatch) -> HybridExtractionService:
    monkeypatch.setenv("LANES_NEWS_AUDITOR_PROVIDER", "")
    monkeypatch.setenv("LANES_NEWS_AUDITOR_MODEL", "")
    return get_hybrid_extraction_service()


@pytest.mark.asyncio
async def test_hybrid_rules_only_mode(hybrid_service: HybridExtractionService):
    article = NewsArticleExtractorInput(
        article_id=101,
        canonical_url="https://example.com/test1",
        publisher="GMA News",
        title="Baha sa Maybunga, Pasig City",
        article_text="Binaha ang Barangay Maybunga sa Pasig City, abot-tuhod ang tubig kanina.",
    )
    result = await hybrid_service.extract_hybrid(article, mode="rules_only")

    assert len(result.claims) >= 1
    claim = result.claims[0]
    assert claim.canonical_barangay == "Maybunga"
    assert claim.depth_canonical == "knee"
    assert claim.is_negated is False
    assert claim.ranked_location is not None
    assert claim.ranked_location.geometry_geojson is not None


@pytest.mark.asyncio
async def test_gemini_auditor_cannot_approve_preview_geometry(
    hybrid_service: HybridExtractionService,
    monkeypatch,
):
    """An auditor confirmation does not verify a road segment or observation time."""
    async def mock_audit_claim_with_llm(claim, context_text, client=None):
        return LLMAuditResult(
            is_confirmed=True,
            status_classification="active",
            depth_confirmed=True,
            is_forecast=False,
            is_subsided=False,
            is_negated=False,
            audit_notes="Gemini auditor confirmed active road flooding at knee depth.",
        )

    monkeypatch.setattr(hybrid_service, "audit_claim_with_llm", mock_audit_claim_with_llm)

    article = NewsArticleExtractorInput(
        article_id=102,
        canonical_url="https://example.com/test2",
        publisher="Inquirer.net",
        title="Flood along C. Raymundo Ave, Pasig",
        article_text="Kasalukuyang lagpas-tuhod ang baha sa kahabaan ng C. Raymundo Ave sa Pasig City dahil sa malakas na ulan.",
    )
    result = await hybrid_service.extract_hybrid(article, mode="ensemble")

    assert len(result.claims) >= 1
    claim = result.claims[0]
    assert claim.depth_canonical == "knee"
    assert claim.action_type == "flagged_review"
    assert claim.ranked_location is not None
    assert claim.ranked_location.precision_level == "road"
    assert claim.ranked_location.geometry_geojson is not None
    assert claim.ranked_location.is_auto_approvable is False
    assert claim.ranked_location.geometry_provenance == "offline_anchor"


@pytest.mark.asyncio
async def test_gemini_auditor_suppresses_subsided_flood(
    hybrid_service: HybridExtractionService,
    monkeypatch,
):
    """When news states flood has already subsided ('humupa na'), auditor strictly suppresses it

    to prevent closing dry, passable roads.
    """
    async def mock_audit_claim_with_llm(claim, context_text, client=None):
        return LLMAuditResult(
            is_confirmed=True,
            status_classification="subsided",
            depth_confirmed=False,
            is_forecast=False,
            is_subsided=True,
            is_negated=False,
            audit_notes="Gemini auditor confirmed waters have already receded.",
        )

    monkeypatch.setattr(hybrid_service, "audit_claim_with_llm", mock_audit_claim_with_llm)

    article = NewsArticleExtractorInput(
        article_id=103,
        canonical_url="https://example.com/test3",
        publisher="SunStar Cebu",
        title="Flood Subsided on Colon Street",
        article_text="Humupa na ang baha sa Colon Street kaninang hapon at passable na sa lahat ng sasakyan.",
    )
    result = await hybrid_service.extract_hybrid(article, mode="ensemble")

    assert len(result.claims) >= 1
    claim = result.claims[0]
    assert claim.condition == "subsided"
    assert claim.action_type == "suppressed_subsided"
    assert "subsided" in str(claim.action_rationale).lower()
    assert claim.ranked_location.is_auto_approvable is False


@pytest.mark.asyncio
async def test_gemini_auditor_suppresses_weather_forecast(
    hybrid_service: HybridExtractionService,
    monkeypatch,
):
    """When news contains a weather forecast or flood warning ('posibleng bahain'),

    auditor strictly suppresses it so predictions do not close active roads.
    """
    async def mock_audit_claim_with_llm(claim, context_text, client=None):
        return LLMAuditResult(
            is_confirmed=True,
            status_classification="forecast",
            depth_confirmed=False,
            is_forecast=True,
            is_subsided=False,
            is_negated=False,
            audit_notes="Gemini auditor confirmed this is a weather forecast only.",
        )

    monkeypatch.setattr(hybrid_service, "audit_claim_with_llm", mock_audit_claim_with_llm)

    article = NewsArticleExtractorInput(
        article_id=104,
        canonical_url="https://example.com/test4",
        publisher="Rappler",
        title="PAGASA Flood Warning",
        article_text="Posibleng bahain ang mabababang lugar sa Barangay Rosario dahil sa paparating na bagyo.",
    )
    result = await hybrid_service.extract_hybrid(article, mode="ensemble")

    assert len(result.claims) >= 1
    claim = result.claims[0]
    assert claim.is_forecast is True
    assert claim.action_type == "suppressed_forecast"
    assert "forecast" in str(claim.action_rationale).lower()


@pytest.mark.asyncio
async def test_ambiguous_city_only_flagged_for_staff_review(
    hybrid_service: HybridExtractionService,
):
    """Broad city-only mention without specific street must be flagged for staff review,

    preventing accidental closure of an entire city.
    """
    article = NewsArticleExtractorInput(
        article_id=105,
        canonical_url="https://example.com/test5",
        publisher="ABS-CBN News",
        title="Baha sa Pasig City",
        article_text="Binaha ang ilang lugar sa Pasig City kahapon.",
    )
    result = await hybrid_service.extract_hybrid(article, mode="ensemble")

    for claim in result.claims:
        if claim.ranked_location and claim.ranked_location.precision_level == "city":
            assert claim.action_type == "flagged_review"
            assert claim.ranked_location.is_auto_approvable is False


@pytest.mark.asyncio
async def test_hybrid_fallback_deterministic_auditor(
    hybrid_service: HybridExtractionService,
    monkeypatch,
):
    """A missing external audit cannot independently confirm an active claim."""
    monkeypatch.setattr(hybrid_service, "openrouter_api_key", "")
    monkeypatch.setattr(hybrid_service, "gemini_api_key", "")
    article = NewsArticleExtractorInput(
        article_id=106,
        canonical_url="https://example.com/test6",
        publisher="GMA News",
        title="Aktibong baha sa C. Raymundo",
        article_text="Kasalukuyang abot-tuhod ang baha sa kahabaan ng C. Raymundo Ave sa Pasig City.",
    )
    result = await hybrid_service.extract_hybrid(article, mode="ensemble")

    assert len(result.claims) >= 1
    claim = result.claims[0]
    assert claim.depth_canonical == "knee"
    assert claim.action_type == "flagged_review"


def test_activation_requires_independent_audit_recent_observation_and_verified_segment(
    hybrid_service: HybridExtractionService,
):
    now = datetime.now(timezone.utc)
    claim = ExtractedClaim(
        raw_place_name="Sample Road",
        place_type="street",
        place_char_start=0,
        place_char_end=11,
        evidence_sentence="Flood at Sample Road, knee deep.",
        evidence_sentence_offset=(0, 32),
        depth_canonical="knee",
        condition="active",
        event_time_resolved=now - timedelta(minutes=10),
        event_time_kind="observation",
        canonical_city="City of Pasig",
    )
    location = RankedLocationCandidate(
        raw_place_name="Sample Road",
        precision_level="road",
        resolved_city="City of Pasig",
        geometry_geojson={"type": "Polygon", "coordinates": []},
        geometry_provenance="verified_segment",
        is_auto_approvable=True,
    )
    audit = LLMAuditResult(is_confirmed=True, status_classification="active", depth_confirmed=True, place_confirmed=True, time_confirmed=True)
    published = now - timedelta(minutes=5)

    assert hybrid_service.evaluate_claim_action(claim, audit, location, published)[0] == "auto_approved"
    legacy_audit = audit.model_copy(update={"place_confirmed": False, "time_confirmed": False})
    assert hybrid_service.evaluate_claim_action(claim, legacy_audit, location, published)[0] == "flagged_review"
    assert hybrid_service.evaluate_claim_action(claim, None, location, published)[0] == "flagged_review"
    assert hybrid_service.evaluate_claim_action(claim, audit, location.model_copy(update={"geometry_provenance": "offline_anchor"}), published)[0] == "flagged_review"
    assert hybrid_service.evaluate_claim_action(claim, audit, location, None)[0] == "flagged_review"
    assert hybrid_service.evaluate_claim_action(claim.model_copy(update={"event_time_resolved": None}), audit, location, published)[0] == "flagged_review"
    assert hybrid_service.evaluate_claim_action(claim.model_copy(update={"event_time_kind": "report"}), audit, location, published)[0] == "flagged_review"
    assert hybrid_service.evaluate_claim_action(claim.model_copy(update={"is_historical": True}), audit, location, published)[0] == "flagged_review"
    assert hybrid_service.evaluate_claim_action(claim, audit, location, now - timedelta(days=2))[0] == "flagged_review"
    assert hybrid_service.evaluate_claim_action(claim.model_copy(update={"road_passability": "passable_all"}), audit, location, published)[0] == "flagged_review"
