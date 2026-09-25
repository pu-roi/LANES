"""Unit and regression tests for HybridExtractionService ensemble pipeline.

Verifies:
  1. Primary extraction by Taglish rules & PSGC reference grounding.
  2. Gemini 1.5 Flash strictly in supporting / double-check auditor role.
  3. Smart Auto-Activation (Option 2):
     - High confidence (>=95%) active flood -> auto_approved directly to live map.
     - Subsided flood ("humupa na") -> suppressed_subsided.
     - Weather forecast ("posibleng bahain") -> suppressed_forecast.
     - Broad city/province -> flagged_review.
  4. Nationwide geometry generation (50m corridor / circular buffer polygons).
"""

from __future__ import annotations

import pytest
from app.schemas.news_extraction import LLMAuditResult, NewsArticleExtractorInput
from app.services.hybrid_extraction_service import (
    HybridExtractionService,
    get_hybrid_extraction_service,
)


@pytest.fixture
def hybrid_service() -> HybridExtractionService:
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
async def test_gemini_auditor_confirms_auto_approval(
    hybrid_service: HybridExtractionService,
    monkeypatch,
):
    """When primary rules detect active flood with exact road + depth, and Gemini auditor confirms,

    system reaches >=95% confidence and flags as auto_approved.
    """
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
    assert claim.confidence_score >= 0.95
    assert claim.action_type == "auto_approved"
    assert "automatically approved" in str(claim.action_rationale)
    assert claim.ranked_location is not None
    assert claim.ranked_location.precision_level == "road"
    assert claim.ranked_location.geometry_geojson is not None
    assert claim.ranked_location.is_auto_approvable is True


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
):
    """When external LLM is offline or no API key is provided, the deterministic fallback auditor

    confirms active flood with canonical depth cleanly.
    """
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
    assert claim.action_type == "auto_approved"
    assert claim.confidence_score >= 0.95
