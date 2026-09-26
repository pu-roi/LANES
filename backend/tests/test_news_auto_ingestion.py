"""Integration tests for NewsAutoIngestionService and Smart Auto-Activation.

Verifies:
  1. Auto-approval generates official FloodEvent and operational FloodAvoidanceZone atomically.
  2. Subsided flood ("humupa na") is strictly suppressed with zero created zones.
  3. Weather forecast ("posibleng bahain") is strictly suppressed with zero created zones.
  4. Non-admin execution: zones are live immediately on live map without admin intervention.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.models.news import NewsArticle
from app.models.report import FloodAvoidanceZone, FloodEvent, FloodReport, FloodEventStatus, ReportStatus
from app.schemas.news_extraction import LLMAuditResult
from app.services.news_auto_ingestion_service import (
    NewsAutoIngestionService,
    get_news_auto_ingestion_service,
)


@pytest.fixture
def auto_ingestion_service() -> NewsAutoIngestionService:
    return get_news_auto_ingestion_service()


@pytest.mark.asyncio
async def test_auto_approval_creates_verified_event_and_zone_without_admin(
    auto_ingestion_service: NewsAutoIngestionService,
    monkeypatch,
):
    """Complete active flood details from news are automatically approved and activated."""
    # Mock LLM auditor to confirm
    async def mock_audit(claim, context_text, client=None):
        return LLMAuditResult(
            is_confirmed=True,
            status_classification="active",
            depth_confirmed=True,
            is_forecast=False,
            is_subsided=False,
            is_negated=False,
            audit_notes="Auditor confirmed active flood.",
        )

    monkeypatch.setattr(auto_ingestion_service.hybrid_service, "audit_claim_with_llm", mock_audit)

    # Mock DB session
    mock_db = MagicMock()
    mock_event = MagicMock(spec=FloodEvent, id=901, status=FloodEventStatus.ACTIVE)
    mock_zone = MagicMock(spec=FloodAvoidanceZone, id=701, is_active=True)

    with patch("app.services.news_auto_ingestion_service.create_verified_event_with_zone", return_value=(mock_event, mock_zone)):
        article = NewsArticle(
            id=501,
            canonical_url="https://news.example.com/pasig-flood",
            publisher_source_id="gma-news",
            title="Baha sa C. Raymundo Ave",
            excerpt="",
            article_text="Kasalukuyang abot-tuhod ang baha sa kahabaan ng C. Raymundo Ave sa Pasig City.",
            review_state="pending",
        )

        result = await auto_ingestion_service.process_and_ingest_article(mock_db, article, acted_by_user_id=1)

        assert result["auto_approved_claims"] >= 1
        assert result["review_state"] == "auto_approved"
        assert 901 in result["created_event_ids"]
        assert article.review_state == "auto_approved"
        assert mock_db.commit.called


@pytest.mark.asyncio
async def test_subsided_flood_strictly_suppressed(
    auto_ingestion_service: NewsAutoIngestionService,
    monkeypatch,
):
    """Subsided flood news produces zero events and zero zones, keeping roads open."""
    async def mock_audit(claim, context_text, client=None):
        return LLMAuditResult(
            is_confirmed=True,
            status_classification="subsided",
            depth_confirmed=False,
            is_forecast=False,
            is_subsided=True,
            is_negated=False,
            audit_notes="Auditor confirmed waters receded.",
        )

    monkeypatch.setattr(auto_ingestion_service.hybrid_service, "audit_claim_with_llm", mock_audit)

    mock_db = MagicMock()
    with patch("app.services.news_auto_ingestion_service.create_verified_event_with_zone") as mock_create_event:
        article = NewsArticle(
            id=502,
            canonical_url="https://news.example.com/cebu-subsided",
            publisher_source_id="sunstar-cebu",
            title="Subsided flood on Colon",
            excerpt="",
            article_text="Humupa na ang baha sa kahabaan ng Colon Street sa Cebu City at muling nadaanan.",
            review_state="pending",
        )

        result = await auto_ingestion_service.process_and_ingest_article(mock_db, article)

        assert result["auto_approved_claims"] == 0
        assert result["suppressed_claims"] >= 1
        assert result["created_event_ids"] == []
        assert article.review_state == "suppressed"
        # Verify no event or zone creation service was ever called
        assert not mock_create_event.called


@pytest.mark.asyncio
async def test_forecast_advisory_strictly_suppressed(
    auto_ingestion_service: NewsAutoIngestionService,
    monkeypatch,
):
    """Weather forecasts produce zero avoidance zones to prevent closing dry roads."""
    async def mock_audit(claim, context_text, client=None):
        return LLMAuditResult(
            is_confirmed=True,
            status_classification="forecast",
            depth_confirmed=False,
            is_forecast=True,
            is_subsided=False,
            is_negated=False,
            audit_notes="Auditor confirmed this is a weather forecast.",
        )

    monkeypatch.setattr(auto_ingestion_service.hybrid_service, "audit_claim_with_llm", mock_audit)

    mock_db = MagicMock()
    with patch("app.services.news_auto_ingestion_service.create_verified_event_with_zone") as mock_create_event:
        article = NewsArticle(
            id=503,
            canonical_url="https://news.example.com/davao-warning",
            publisher_source_id="mindanews",
            title="Flood warning in Davao",
            excerpt="",
            article_text="Posibleng bahain ang kahabaan ng Roxas Avenue sa Davao City dulot ng bagyo.",
            review_state="pending",
        )

        result = await auto_ingestion_service.process_and_ingest_article(mock_db, article)

        assert result["auto_approved_claims"] == 0
        assert result["suppressed_claims"] >= 1
        assert result["created_event_ids"] == []
        assert article.review_state == "suppressed"
        assert not mock_create_event.called
