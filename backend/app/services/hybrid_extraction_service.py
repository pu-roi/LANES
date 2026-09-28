"""Evidence-linked flood extraction with independent audit and review decisions.

Current geometry is a preview only, so active claims remain in staff review.
Forecast, negated, and subsided claims are suppressed from activation.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional

import httpx

from app.schemas.news_extraction import (
    CanonicalDepth,
    ExtractedClaim,
    FloodCondition,
    LLMAuditResult,
    NewsArticleExtractorInput,
    NewsExtractionResult,
    PlaceType,
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

logger = logging.getLogger(__name__)

ExtractionMode = Literal["ensemble", "rules_only", "auditor_only"]
MAX_AUTO_ACTIVATION_AGE = timedelta(hours=12)


class HybridExtractionService:
    """Orchestrates multi-tier extraction, Gemini 1.5 Flash verification, and nationwide geometry generation."""

    def __init__(
        self,
        location_service: Optional[PhilippineLocationService] = None,
        geometry_service: Optional[NationwideGeometryService] = None,
    ) -> None:
        self.location_service = location_service or get_philippine_location_service()
        self.geometry_service = geometry_service or get_nationwide_geometry_service()
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    async def audit_claim_with_llm(
        self,
        claim: ExtractedClaim,
        context_text: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> LLMAuditResult:
        """Invoke Gemini 1.5 Flash strictly in a Supporting / Auditor role to double-check candidate claims.

        The LLM does NOT discover claims from scratch; it inspects the primary pipeline's
        candidate and determines whether the active flood, depth, and road are verified.
        """
        api_key = self.openrouter_api_key or self.gemini_api_key

        # Local rules cannot substitute for an independent confirmation.
        if not api_key:
            return self._deterministic_fallback_audit(claim, context_text)

        prompt = f"""You are a safety verification auditor for the LANES Philippine Flood Disaster Intelligence System.
The primary NLP detection engines (deterministic Taglish rules, 43k PSGC grounding, and NER) identified this candidate flood claim:
- Extracted Location: "{claim.raw_place_name}"
- Extracted Depth Gauge: "{claim.depth_canonical}" (Raw text: "{claim.depth_raw}")
- Extracted Condition: "{claim.condition}"
- Supporting Evidence Sentence: "{claim.evidence_sentence}"

Your supporting role is strictly to double-check and verify this candidate claim:
1. Is this claim explicitly supported by the text?
2. WATER STATUS SAFETY AUDIT:
   - Is water ACTIVELY FLOODED or RISING right now? -> status: "active" or "rising"
   - Has the flood SUBSIDED / RECEDED ("humupa na", "hupa na", "subsided", "cleared", "bumaba na")? -> status: "subsided"
   - Is this merely a WEATHER FORECAST or FLOOD ADVISORY ("posibleng bahain", "pinag-iingat", "asahan ang pagbaha")? -> status: "forecast"
   - Is it NEGATED ("walang baha", "passable sa lahat")? -> status: "negated"
3. DEPTH AUDIT:
   - Does the text verify depth gauge "{claim.depth_canonical}"?

Respond ONLY with valid JSON:
{{
  "is_confirmed": true,
  "status_classification": "active" | "rising" | "receding" | "subsided" | "forecast" | "negated" | "unclear",
  "depth_confirmed": true,
  "depth_discrepancy_note": null,
  "is_forecast": false,
  "is_subsided": false,
  "is_negated": false,
  "audit_notes": "concise explanation"
}}
"""
        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=10.0)
            should_close = True

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "google/gemini-flash-1.5",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
            }
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            if resp.status_code == 200:
                data = resp.json()
                raw_content = data["choices"][0]["message"]["content"].strip()
                raw_content = re.sub(r"^```(?:json)?\s*", "", raw_content)
                raw_content = re.sub(r"\s*```$", "", raw_content)
                parsed = json.loads(raw_content)
                return LLMAuditResult(
                    is_confirmed=parsed.get("is_confirmed") is True,
                    status_classification=parsed.get("status_classification", "unclear"),
                    depth_confirmed=parsed.get("depth_confirmed") is True,
                    depth_discrepancy_note=parsed.get("depth_discrepancy_note"),
                    is_forecast=parsed.get("is_forecast") is True,
                    is_subsided=parsed.get("is_subsided") is True,
                    is_negated=parsed.get("is_negated") is True,
                    audit_notes=parsed.get("audit_notes", "External audit response parsed."),
                )
            logger.warning("Gemini audit returned HTTP %d; claim requires staff review", resp.status_code)
        except Exception as exc:
            logger.warning("Gemini audit unavailable; claim requires staff review: %s", exc)
        finally:
            if should_close:
                await client.aclose()

        return self._deterministic_fallback_audit(claim, context_text)

    def _deterministic_fallback_audit(self, claim: ExtractedClaim, context_text: str) -> LLMAuditResult:
        """Classify locally when external audit is unavailable, without confirming."""
        lower_evidence = f"{claim.evidence_sentence} {context_text}".lower()

        # Check subsidence / receded waters
        subsided_terms = ("humupa na", "hupa na", "nagsubside", "subsided", "bumaba na ang tubig", "cleared")
        if claim.condition == "subsided" or any(t in lower_evidence for t in subsided_terms):
            return LLMAuditResult(
                is_confirmed=False,
                status_classification="subsided",
                depth_confirmed=False,
                is_forecast=False,
                is_subsided=True,
                is_negated=False,
                audit_notes="Local rules classified water as subsided; independent audit unavailable.",
            )

        # Check forecast / prediction
        forecast_terms = ("posibleng bahain", "maaaring bumaha", "asahan ang pagbaha", "pinag-iingat sa baha", "flood advisory", "forecast")
        if claim.is_forecast or any(t in lower_evidence for t in forecast_terms):
            return LLMAuditResult(
                is_confirmed=False,
                status_classification="forecast",
                depth_confirmed=False,
                is_forecast=True,
                is_subsided=False,
                is_negated=False,
                audit_notes="Local rules classified this as a forecast; independent audit unavailable.",
            )

        # Check negation
        if claim.is_negated or "walang baha" in lower_evidence or "passable sa lahat" in lower_evidence:
            return LLMAuditResult(
                is_confirmed=False,
                status_classification="negated",
                depth_confirmed=False,
                is_forecast=False,
                is_subsided=False,
                is_negated=True,
                audit_notes="Local rules classified this as negated; independent audit unavailable.",
            )

        # Active observed flood with confirmed depth
        return LLMAuditResult(
            is_confirmed=False,
            status_classification="rising" if claim.condition == "rising" else "active",
            depth_confirmed=claim.depth_canonical is not None,
            is_forecast=False,
            is_subsided=False,
            is_negated=False,
            audit_notes="Local rules detected flooding; independent audit unavailable, so staff review is required.",
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
        if claim.road_passability == "light_vehicle_closed":
            return "flagged_review", "Light-vehicle restriction needs vehicle-specific staff review."
        if claim.is_historical:
            return "flagged_review", "Historical flood evidence cannot establish a current closure."
        if not claim.flood_mentioned or claim.condition not in ("active", "rising"):
            return "flagged_review", "No clearly observed active flood for this place."
        if not audit_result or not audit_result.is_confirmed:
            return "flagged_review", "Independent auditor did not confirm this claim."
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
        Step 3: Double-check verification via Gemini 1.5 Flash auditor (supporting role).
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

        # Step 2 & 3: For each candidate claim, run Nationwide Geometry & Gemini 1.5 Flash Auditor
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

            # Invoke Gemini 1.5 Flash in Supporting / Auditor Role
            audit_result = await self.audit_claim_with_llm(claim, article_text, client=http_client)
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
            extractor_version="hybrid-ensemble-auditor-v2.0",
            errors=result_tier1.errors,
        )


_hybrid_service: Optional[HybridExtractionService] = None


def get_hybrid_extraction_service() -> HybridExtractionService:
    """Return singleton instance of HybridExtractionService."""
    global _hybrid_service
    if _hybrid_service is None:
        _hybrid_service = HybridExtractionService()
    return _hybrid_service
