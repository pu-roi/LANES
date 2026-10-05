"""Evidence-linked flood extraction with independent audit and review decisions.

Current geometry is a preview only, so active claims remain in staff review.
Forecast, negated, and subsided claims are suppressed from activation.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

import httpx

from app.schemas.news_extraction import (
    ExtractedClaim,
    LLMAuditResult,
    NewsArticleExtractorInput,
    NewsExtractionResult,
    RankedLocationCandidate,
)
from app.services.nationwide_geometry_service import (
    NationwideGeometryService,
    get_nationwide_geometry_service,
)
from app.services.philippine_location_service import (
    PhilippineLocationService,
    get_philippine_location_service,
)
from app.services.taglish_extraction_service import (
    extract_taglish_flood_facts,
)

from app.services.news_claim_auditor import AuditorConfig, NewsClaimAuditor

ExtractionMode = Literal["ensemble", "rules_only", "auditor_only"]
MAX_AUTO_ACTIVATION_AGE = timedelta(hours=12)


class HybridExtractionService:
    """Orchestrates rules extraction, independent evidence audit and preview geometry."""

    def __init__(
        self,
        location_service: Optional[PhilippineLocationService] = None,
        geometry_service: Optional[NationwideGeometryService] = None,
    ) -> None:
        self.location_service = location_service or get_philippine_location_service()
        self.geometry_service = geometry_service or get_nationwide_geometry_service()
        auditor_config = AuditorConfig.from_environment()
        self.openrouter_api_key = auditor_config.openrouter_api_key
        self.gemini_api_key = auditor_config.gemini_api_key

    async def audit_claim_with_llm(
        self,
        claim: ExtractedClaim,
        context_text: str | NewsArticleExtractorInput,
        client: Optional[httpx.AsyncClient] = None,
    ) -> LLMAuditResult:
        """Compatibility projection of the complete independent evidence audit.

        Durable evaluations call NewsClaimAuditor directly after extraction commits.
        A text-only legacy caller has no fabricated source timestamps or identity.
        """
        article = context_text if isinstance(context_text, NewsArticleExtractorInput) else NewsArticleExtractorInput(
            article_id=0, canonical_url="", publisher="", title="", article_text=context_text,
        )
        config = replace(AuditorConfig.from_environment(), openrouter_api_key=self.openrouter_api_key,
                         gemini_api_key=self.gemini_api_key)
        result = await NewsClaimAuditor(config).audit(claim, article, client=client)
        evidence = result.evidence
        verified = result.outcome == "verified"
        classification = evidence.status.classification if evidence else "unclear"
        return LLMAuditResult(
            is_confirmed=verified,
            status_classification=classification,
            place_confirmed=verified and evidence.place.confirmed,
            time_confirmed=verified and evidence.time.confirmed,
            depth_confirmed=verified and evidence.depth.confirmed,
            is_forecast=bool(evidence and evidence.status.confirmed and classification == "forecast"),
            is_subsided=bool(evidence and evidence.status.confirmed and classification == "subsided"),
            is_negated=bool(evidence and evidence.status.confirmed and classification == "negated"),
            audit_notes=result.reason_code,
            independent_audit=result,
        )

    def evaluate_claim_action(
        self,
        claim: ExtractedClaim,
        audit_result: Optional[LLMAuditResult] = None,
        ranked_location: Optional[RankedLocationCandidate] = None,
        article_published_at: Optional[datetime] = None,
    ) -> tuple[str, str]:
        """Return suppression or review unless every independent publish gate passes."""
        # 1. Safety Gate: Negated reports
        if claim.is_negated or (audit_result and audit_result.is_negated):
            return "suppressed_negated", "Report confirms no flooding occurred; discarded."

        # 2. Safety Gate: Forecasts & Predictions
        if claim.is_forecast or (audit_result and audit_result.is_forecast):
            return "suppressed_forecast", "Forecast or flood advisory only; suppressed to avoid closing dry roads."

        # 3. Safety Gate: Subsided / Receded waters
        if claim.condition == "subsided" or (audit_result and audit_result.is_subsided):
            return "suppressed_subsided", "Flood waters have already subsided/receded; suppressed to keep passable roads open."

        if "photo_caption_only" in claim.uncertainty_reasons:
            return "flagged_review", "Photo-caption evidence requires independent report and location review."

        if "metadata_only_lead" in claim.uncertainty_reasons:
            return "flagged_review", "Article body is unavailable; metadata alone cannot verify a road closure."

        if "contradictory_update" in claim.uncertainty_reasons:
            return "flagged_review", "This place has conflicting flood updates in the article; staff must reconcile them."

        if claim.road_passability == "passable_all":
            return "flagged_review", "Flooded road is reported passable; no avoidance closure is justified."
        if claim.road_passability == "passable_with_caution":
            return "flagged_review", "Road is reported passable with caution; vehicle applicability is unstated and no avoidance closure is justified."
        if claim.road_passability == "passable_unspecified":
            return "flagged_review", "Road is reported passable without specified vehicle types; no avoidance closure is justified."
        if claim.road_passability == "light_vehicle_closed":
            return "flagged_review", "Light-vehicle restriction needs vehicle-specific staff review."
        if claim.is_historical:
            return "flagged_review", "Historical flood evidence cannot establish a current closure."
        if not claim.flood_mentioned or claim.condition not in ("active", "rising"):
            return "flagged_review", "No clearly observed active flood for this place."
        if not audit_result or not audit_result.is_confirmed:
            return "flagged_review", "Independent auditor did not confirm this claim."
        if not audit_result.place_confirmed or not audit_result.time_confirmed:
            return "flagged_review", "Auditor did not confirm place and observation time."
        if audit_result.status_classification not in ("active", "rising") or not audit_result.depth_confirmed:
            return "flagged_review", "Auditor did not confirm active status and depth."
        if claim.depth_canonical is None or claim.event_time_resolved is None or claim.event_time_kind != "observation":
            return "flagged_review", "Canonical depth or explicit flood observation time is missing."
        observed_at = claim.event_time_resolved
        if observed_at.tzinfo is None:
            return "flagged_review", "Flood observation time has no timezone."
        if article_published_at is None or article_published_at.tzinfo is None:
            return "flagged_review", "Article publication time is unavailable or lacks a timezone."
        now = datetime.now(timezone.utc)
        if not (timedelta(0) <= now - observed_at <= MAX_AUTO_ACTIVATION_AGE):
            return "flagged_review", "Flood observation is stale or in the future."
        if not (timedelta(0) <= now - article_published_at <= MAX_AUTO_ACTIVATION_AGE):
            return "flagged_review", "Article publication is stale or in the future."

        precision_level = ranked_location.precision_level if ranked_location else "unresolved"
        if precision_level == "city":
            return "flagged_review", "Broad municipal mention without specific road segment; enqueued for staff map selection."
        if (
            not ranked_location
            or precision_level not in ("road", "landmark")
            or not claim.canonical_city
            or ranked_location.resolved_city != claim.canonical_city
            or not ranked_location.is_auto_approvable
            or ranked_location.requires_staff_edit
            or ranked_location.geometry_provenance != "verified_segment"
            or ranked_location.geometry_geojson is None
        ):
            return "flagged_review", "Affected road segment and geometry are not independently verified."

        return "auto_approved", "Recent active flood and exact geometry independently verified."

    async def extract_hybrid(
        self,
        article_input: NewsArticleExtractorInput,
        mode: ExtractionMode = "ensemble",
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> NewsExtractionResult:
        """Run multi-tier extraction pipeline:

        Step 1: Primary extraction via Tier 1 Deterministic Rules + PSGC Location Grounding.
        Step 2: Hierarchy resolution and preview geometry via NationwideGeometryService.
        Step 3: Independent verification against complete immutable article evidence.
        Step 4: Fail-closed decision (suppressed or flagged_review until verification gates exist).
        """
        # Step 1: Run Primary Deterministic Extraction (Tier 1 Rules + PSGC)
        result_tier1 = extract_taglish_flood_facts(article_input)
        article_text = article_input.article_text or article_input.excerpt or article_input.title

        if mode == "rules_only":
            for claim in result_tier1.claims:
                ranked_geo = self.geometry_service.rank_and_generate_geometry(claim, article_text)
                claim.ranked_location = ranked_geo
                claim.canonical_city = ranked_geo.resolved_city
                claim.canonical_province = ranked_geo.resolved_province
                claim.canonical_road = ranked_geo.resolved_road
                claim.island_group = ranked_geo.island_group
                claim.psgc_code = ranked_geo.psgc_code
                action, rationale = self.evaluate_claim_action(claim, ranked_location=ranked_geo, article_published_at=article_input.published_at)
                claim.action_type = action
                claim.action_rationale = rationale
                claim.uncertainty_reasons.append(f"action:{action}")
            return result_tier1

        # Step 2 & 3: For each candidate claim, run preview geometry and independent audit
        processed_claims: list[ExtractedClaim] = []

        for claim in result_tier1.claims:
            # Generate geometry and rank candidate location
            ranked_geo = self.geometry_service.rank_and_generate_geometry(claim, article_text)
            claim.ranked_location = ranked_geo
            claim.canonical_city = ranked_geo.resolved_city
            claim.canonical_province = ranked_geo.resolved_province
            claim.canonical_road = ranked_geo.resolved_road
            claim.island_group = ranked_geo.island_group
            claim.psgc_code = ranked_geo.psgc_code

            # Audit complete source evidence without changing durable extraction
            audit_result = await self.audit_claim_with_llm(claim, article_input, client=http_client)
            claim.audit_result = audit_result

            # Apply auditor safety classifications
            if audit_result.is_subsided:
                claim.condition = "subsided"
            elif audit_result.is_forecast:
                claim.is_forecast = True
            elif audit_result.is_negated:
                claim.is_negated = True

            # Evaluate auto-approval action
            action, rationale = self.evaluate_claim_action(claim, audit_result, ranked_geo, article_input.published_at)
            claim.action_type = action
            claim.action_rationale = rationale

            # This is a place-ranking heuristic, not a calibrated approval probability.
            claim.confidence_score = min(claim.confidence_score, ranked_geo.confidence_score)

            claim.uncertainty_reasons.append(f"action:{action}({rationale})")
            processed_claims.append(claim)

        return NewsExtractionResult(
            article_id=article_input.article_id,
            canonical_url=article_input.canonical_url,
            is_metadata_only=result_tier1.is_metadata_only,
            processed_text_length=result_tier1.processed_text_length,
            claims=processed_claims,
            extractor_version="hybrid-ensemble-auditor-v3.0",
            errors=result_tier1.errors,
        )


_hybrid_service: Optional[HybridExtractionService] = None


def get_hybrid_extraction_service() -> HybridExtractionService:
    """Return singleton instance of HybridExtractionService."""
    global _hybrid_service
    if _hybrid_service is None:
        _hybrid_service = HybridExtractionService()
    return _hybrid_service
