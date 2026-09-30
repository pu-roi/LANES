"""Safety tests for news ingestion and public-zone activation.

Verifies:
  1. Auditor-confirmed news remains in review without verified geometry/time.
  2. Subsided flood ("humupa na") is strictly suppressed with zero created zones.
  3. Weather forecast ("posibleng bahain") is strictly suppressed with zero created zones.
  4. A stale auto_approved action cannot bypass the persistence boundary.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.models.news import NewsArticle
from app.models.report import FloodAvoidanceZone, FloodEvent, FloodReport, FloodEventStatus, ReportStatus
from app.schemas.news_extraction import ExtractedClaim, LLMAuditResult, NewsExtractionResult, RankedLocationCandidate
from app.services.news_auto_ingestion_service import (
    NewsAutoIngestionService,
    get_news_auto_ingestion_service,
)
from app.services.hybrid_extraction_service import HybridExtractionService


@pytest.fixture
def auto_ingestion_service() -> NewsAutoIngestionService:
    return get_news_auto_ingestion_service()


def test_conflicting_update_blocks_even_independently_verified_geometry():
    now = datetime.now(timezone.utc)
    claim = ExtractedClaim(
        raw_place_name="Araneta Avenue",
        canonical_city="Quezon City",
        road_segment_raw="Araneta Avenue corner Maria Clara",
        place_type="street",
        place_char_start=0,
        place_char_end=14,
        evidence_sentence="Araneta Avenue corner Maria Clara was flooded at 26 inches.",
        evidence_sentence_offset=(0, 58),
        flood_mentioned=True,
        depth_canonical="tires",
        condition="active",
        event_time_resolved=now,
        event_time_kind="observation",
        uncertainty_reasons=["contradictory_update"],
    )
    audit = LLMAuditResult(is_confirmed=True, status_classification="active", depth_confirmed=True)
    location = RankedLocationCandidate(
        raw_place_name="Araneta Avenue",
        resolved_city="Quezon City",
        precision_level="road",
        geometry_provenance="verified_segment",
        is_auto_approvable=True,
        requires_staff_edit=False,
        geometry_geojson={"type": "Polygon", "coordinates": []},
    )

    action, reason = HybridExtractionService().evaluate_claim_action(claim, audit, location, now)

    assert action == "flagged_review"
    assert "conflicting" in reason.lower()


def test_caption_and_metadata_only_cannot_activate_even_with_verified_geometry():
    now = datetime.now(timezone.utc)
    claim = ExtractedClaim(
        raw_place_name="UN Avenue",
        canonical_city="City of Manila",
        place_type="street",
        place_char_start=0,
        place_char_end=9,
        evidence_sentence="A photo shows flooding on UN Avenue.",
        evidence_sentence_offset=(0, 35),
        flood_mentioned=True,
        depth_canonical="knee",
        condition="active",
        event_time_resolved=now,
        event_time_kind="observation",
        uncertainty_reasons=["photo_caption_only"],
    )
    audit = LLMAuditResult(is_confirmed=True, status_classification="active", depth_confirmed=True)
    location = RankedLocationCandidate(
        raw_place_name="UN Avenue",
        resolved_city="City of Manila",
        precision_level="road",
        geometry_provenance="verified_segment",
        is_auto_approvable=True,
        requires_staff_edit=False,
        geometry_geojson={"type": "Polygon", "coordinates": []},
    )

    action, reason = HybridExtractionService().evaluate_claim_action(claim, audit, location, now)

    assert action == "flagged_review"
    assert "caption" in reason.lower()

    metadata_claim = claim.model_copy(update={"uncertainty_reasons": ["metadata_only_lead"]})
    action, reason = HybridExtractionService().evaluate_claim_action(metadata_claim, audit, location, now)
    assert action == "flagged_review"
    assert "metadata" in reason.lower()


@pytest.mark.asyncio
async def test_auditor_confirmation_does_not_create_public_zone(
    auto_ingestion_service: NewsAutoIngestionService,
    monkeypatch,
):
    """Article extraction may suggest a road but must not activate a zone."""
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
    with patch("app.services.news_auto_ingestion_service.create_verified_event_with_zone") as mock_create_event:
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

        assert result["auto_approved_claims"] == 0
        assert result["review_state"] == "flagged_review"
        assert result["created_event_ids"] == []
        assert article.review_state == "flagged_review"
        assert not mock_create_event.called
        mock_db.add.assert_not_called()
        mock_db.flush.assert_not_called()
        assert mock_db.commit.called


@pytest.mark.asyncio
async def test_forged_auto_approved_claim_cannot_write_public_records(
    auto_ingestion_service: NewsAutoIngestionService,
    monkeypatch,
):
    """A stale decision string is insufficient to cross the persistence boundary."""
    now = datetime.now(timezone.utc)
    claim = ExtractedClaim(
        raw_place_name="Sample Road",
        canonical_city="City of Pasig",
        place_type="street",
        place_char_start=0,
        place_char_end=11,
        evidence_sentence="Flood at Sample Road, knee deep.",
        evidence_sentence_offset=(0, 32),
        depth_canonical="knee",
        condition="active",
        event_time_resolved=now,
        action_type="auto_approved",
        ranked_location=RankedLocationCandidate(
            raw_place_name="Sample Road",
            precision_level="road",
            geometry_provenance="verified_segment",
            is_auto_approvable=True,
            geometry_geojson={"type": "Polygon", "coordinates": []},
        ),
    )

    async def forged_extraction(*args, **kwargs):
        return NewsExtractionResult(article_id=504, canonical_url="https://news.example.com/flood", is_metadata_only=False, processed_text_length=32, claims=[claim])

    monkeypatch.setattr(auto_ingestion_service.hybrid_service, "extract_hybrid", forged_extraction)
    article = NewsArticle(
        id=504,
        canonical_url="https://news.example.com/flood",
        publisher_source_id="gma-news",
        title="Sample Road flood",
        article_text=claim.evidence_sentence,
        published_at=now,
        review_state="pending",
    )
    mock_db = MagicMock()
    with patch("app.services.news_auto_ingestion_service.create_verified_event_with_zone") as create_event:
        result = await auto_ingestion_service.process_and_ingest_article(mock_db, article)

    assert result["flagged_claims"] == 1
    assert result["created_event_ids"] == []
    assert article.review_state == "flagged_review"
    mock_db.add.assert_not_called()
    create_event.assert_not_called()


@pytest.mark.parametrize(
    "failed_gate",
    [
        "missing_audit",
        "stale_publication",
        "stale_observation",
        "report_time_only",
        "passable_road",
        "contradictory_update",
        "metadata_only",
        "preview_geometry",
        "missing_city",
        "missing_depth",
    ],
)
@pytest.mark.asyncio
async def test_each_failed_activation_gate_writes_no_public_flood_data(
    failed_gate: str,
    auto_ingestion_service: NewsAutoIngestionService,
    monkeypatch,
):
    """A forged approval label cannot create a report, event, or routing zone."""
    now = datetime.now(timezone.utc)
    published_at = now - timedelta(minutes=5)
    claim = ExtractedClaim(
        raw_place_name="Sample Road",
        canonical_road="Sample Road",
        canonical_city="City of Pasig",
        place_type="street",
        place_char_start=9,
        place_char_end=20,
        evidence_sentence="Flood at Sample Road, knee deep.",
        evidence_sentence_offset=(0, 32),
        depth_canonical="knee",
        condition="active",
        event_time_resolved=now - timedelta(minutes=10),
        event_time_kind="observation",
        action_type="auto_approved",
        audit_result=LLMAuditResult(
            is_confirmed=True, status_classification="active", depth_confirmed=True,
        ),
        ranked_location=RankedLocationCandidate(
            raw_place_name="Sample Road",
            resolved_city="City of Pasig",
            precision_level="road",
            geometry_provenance="verified_segment",
            is_auto_approvable=True,
            requires_staff_edit=False,
            geometry_geojson={
                "type": "Polygon",
                "coordinates": [[[121.0, 14.5], [121.001, 14.5], [121.001, 14.501], [121.0, 14.501], [121.0, 14.5]]],
            },
        ),
    )

    if failed_gate == "missing_audit":
        claim.audit_result = None
    elif failed_gate == "stale_publication":
        published_at = now - timedelta(days=2)
    elif failed_gate == "stale_observation":
        claim.event_time_resolved = now - timedelta(days=2)
    elif failed_gate == "report_time_only":
        claim.event_time_kind = "report"
    elif failed_gate == "passable_road":
        claim.road_passability = "passable_all"
    elif failed_gate == "contradictory_update":
        claim.uncertainty_reasons.append("contradictory_update")
    elif failed_gate == "metadata_only":
        claim.uncertainty_reasons.append("metadata_only_lead")
    elif failed_gate == "preview_geometry":
        claim.ranked_location.geometry_provenance = "offline_anchor"
    elif failed_gate == "missing_city":
        claim.canonical_city = None
        claim.ranked_location.resolved_city = None
    elif failed_gate == "missing_depth":
        claim.depth_canonical = None

    async def forged_extraction(*args, **kwargs):
        return NewsExtractionResult(
            article_id=505,
            canonical_url="https://news.example.com/flood",
            is_metadata_only=failed_gate == "metadata_only",
            processed_text_length=len(claim.evidence_sentence),
            claims=[claim],
        )

    monkeypatch.setattr(auto_ingestion_service.hybrid_service, "extract_hybrid", forged_extraction)
    article = NewsArticle(
        id=505,
        canonical_url="https://news.example.com/flood",
        publisher_source_id="gma-news",
        title="Sample Road flood",
        article_text=claim.evidence_sentence,
        published_at=published_at,
        review_state="pending",
    )
    mock_db = MagicMock()
    with patch("app.services.news_auto_ingestion_service.create_verified_event_with_zone") as create_event:
        result = await auto_ingestion_service.process_and_ingest_article(mock_db, article)

    assert result["auto_approved_claims"] == 0
    assert result["created_event_ids"] == []
    assert article.review_state == "flagged_review"
    mock_db.add.assert_not_called()
    mock_db.flush.assert_not_called()
    create_event.assert_not_called()


@pytest.mark.asyncio
async def test_negated_claim_writes_no_public_flood_data(
    auto_ingestion_service: NewsAutoIngestionService,
    monkeypatch,
):
    now = datetime.now(timezone.utc)
    claim = ExtractedClaim(
        raw_place_name="Sample Road",
        canonical_city="City of Pasig",
        place_type="street",
        place_char_start=0,
        place_char_end=11,
        evidence_sentence="No flood was reported on Sample Road.",
        evidence_sentence_offset=(0, 37),
        flood_mentioned=False,
        is_negated=True,
        action_type="suppressed_negated",
    )

    async def negated_extraction(*args, **kwargs):
        return NewsExtractionResult(
            article_id=506,
            canonical_url="https://news.example.com/no-flood",
            is_metadata_only=False,
            processed_text_length=len(claim.evidence_sentence),
            claims=[claim],
        )

    monkeypatch.setattr(auto_ingestion_service.hybrid_service, "extract_hybrid", negated_extraction)
    article = NewsArticle(
        id=506,
        canonical_url="https://news.example.com/no-flood",
        publisher_source_id="gma-news",
        title="No flood on Sample Road",
        article_text=claim.evidence_sentence,
        published_at=now,
        review_state="pending",
    )
    mock_db = MagicMock()
    with patch("app.services.news_auto_ingestion_service.create_verified_event_with_zone") as create_event:
        result = await auto_ingestion_service.process_and_ingest_article(mock_db, article)

    assert result["suppressed_claims"] == 1
    assert result["auto_approved_claims"] == 0
    assert result["created_event_ids"] == []
    assert article.review_state == "suppressed"
    mock_db.add.assert_not_called()
    mock_db.flush.assert_not_called()
    create_event.assert_not_called()


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
        mock_db.add.assert_not_called()
        mock_db.flush.assert_not_called()


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
        mock_db.add.assert_not_called()
        mock_db.flush.assert_not_called()
