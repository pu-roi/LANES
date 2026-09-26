"""Transactional Auto-Ingestion and Smart Activation Service for Trusted News.

When a news report contains complete, verified active flood details:
  1. Primary Taglish NLP + PSGC rules detect location and canonical depth.
  2. Gemini 1.5 Flash confirms in supporting role (>=95% confidence).
  3. This service AUTOMATICALLY creates the verified FloodReport, official
     FloodEvent, and operational FloodAvoidanceZone (50m polygon) without admin intervention.

When a report is a forecast or subsided flood:
  - Strictly suppressed; no active avoidance zone is created, keeping dry roads open.

When a report is incomplete or ambiguous:
  - Enqueued with pre-rendered geometry for 1-click staff review.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.crud.report import create_flood_avoidance_zone
from app.models.news import NewsArticle
from app.models.report import ReportSeverity, ReportSource, ReportStatus
from app.schemas.common import LineStringGeometry, PolygonGeometry
from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from app.schemas.report import FloodAvoidanceZoneCreate
from app.services.flood_depth import (
    format_flood_depth,
    severity_for_flood_depth,
)
from app.services.flood_event_service import create_verified_event_with_zone
from app.services.hybrid_extraction_service import (
    HybridExtractionService,
    get_hybrid_extraction_service,
)

logger = logging.getLogger(__name__)


class NewsAutoIngestionService:
    """Executes Smart Auto-Activation or moderation queue placement."""

    def __init__(self, hybrid_service: Optional[HybridExtractionService] = None) -> None:
        self.hybrid_service = hybrid_service or get_hybrid_extraction_service()

    async def process_and_ingest_article(
        self,
        db: Session,
        article: NewsArticle,
        client: Optional[httpx.AsyncClient] = None,
        acted_by_user_id: int = 1,
    ) -> dict[str, Any]:
        """Extract facts, audit with Gemini 1.5 Flash, and execute Smart Auto-Activation."""
        extractor_input = NewsArticleExtractorInput(
            article_id=article.id,
            canonical_url=article.canonical_url,
            publisher=article.publisher_source_id,
            title=article.title,
            excerpt=article.excerpt or "",
            article_text=article.article_text,
            published_at=article.published_at,
            fetched_at=article.fetched_at,
        )

        extraction_result = await self.hybrid_service.extract_hybrid(extractor_input, http_client=client)

        auto_approved_count = 0
        suppressed_count = 0
        flagged_count = 0
        created_events: list[int] = []

        for claim in extraction_result.claims:
            action = claim.action_type or "flagged_review"

            if action == "auto_approved" and claim.ranked_location and claim.ranked_location.geometry_geojson:
                # 1. Complete details verified -> SMART AUTO-ACTIVATION
                try:
                    poly_geom = PolygonGeometry(**claim.ranked_location.geometry_geojson)
                    src_geom = None
                    if (
                        claim.ranked_location.source_geometry_geojson
                        and claim.ranked_location.source_geometry_geojson.get("type") == "LineString"
                    ):
                        src_geom = LineStringGeometry(**claim.ranked_location.source_geometry_geojson)

                    zone_input = FloodAvoidanceZoneCreate(
                        geometry=poly_geom,
                        source_geometry=src_geom,
                        is_active=True,
                    )

                    depth_str = claim.depth_canonical or "knee"
                    severity = severity_for_flood_depth(depth_str)

                    # Build PostGIS geometry clause for report point/polygon
                    geojson_str = poly_geom.model_dump_json()
                    geometry_clause = func.ST_SetSRID(func.ST_GeomFromGeoJSON(geojson_str), 4326)

                    # Create verified flood report
                    db_report = models.FloodReport(
                        raw_text=claim.evidence_sentence,
                        source=ReportSource.MANUAL_SEEDER,
                        source_url=article.canonical_url,
                        severity=severity,
                        depth=depth_str,
                        status=ReportStatus.APPROVED,
                        human_readable_location=claim.canonical_road or claim.raw_place_name,
                        barangay=claim.canonical_barangay,
                        city=claim.canonical_city or "City of Pasig",
                        geometry=geometry_clause,
                        is_public=True,
                    )
                    db.add(db_report)
                    db.flush()

                    formatted_depth = format_flood_depth(depth_str) or depth_str
                    event, zone = create_verified_event_with_zone(
                        db=db,
                        zone_input=zone_input,
                        peak_severity=severity,
                        peak_depth=depth_str,
                        acted_by_user_id=acted_by_user_id,
                        source_report=db_report,
                        zone_attributes={
                            "name": f"Auto-Activated: {claim.canonical_road or claim.raw_place_name} ({formatted_depth})",
                            "admin_notes": f"Ingested from {article.publisher_source_id} via Smart Auto-Activation. {claim.action_rationale}",
                        },
                    )

                    auto_approved_count += 1
                    created_events.append(event.id)
                    logger.info("Smart Auto-Activation: Event %d and Zone %d created for %s", event.id, zone.id, claim.raw_place_name)
                except Exception as exc:
                    logger.error("Failed to auto-activate claim %s: %s", claim.raw_place_name, exc)
                    flagged_count += 1

            elif action in ("suppressed_subsided", "suppressed_forecast", "suppressed_negated"):
                suppressed_count += 1
                logger.info("Claim suppressed (%s): %s", action, claim.raw_place_name)

            else:
                flagged_count += 1

        # Update article review state
        if auto_approved_count > 0:
            article.review_state = "auto_approved"
        elif suppressed_count > 0 and flagged_count == 0:
            article.review_state = "suppressed"
        elif flagged_count > 0:
            article.review_state = "flagged_review"

        db.commit()

        return {
            "article_id": article.id,
            "review_state": article.review_state,
            "auto_approved_claims": auto_approved_count,
            "suppressed_claims": suppressed_count,
            "flagged_claims": flagged_count,
            "created_event_ids": created_events,
            "total_claims": len(extraction_result.claims),
        }


_auto_ingestion_service: Optional[NewsAutoIngestionService] = None


def get_news_auto_ingestion_service() -> NewsAutoIngestionService:
    """Return singleton instance of NewsAutoIngestionService."""
    global _auto_ingestion_service
    if _auto_ingestion_service is None:
        _auto_ingestion_service = NewsAutoIngestionService()
    return _auto_ingestion_service
