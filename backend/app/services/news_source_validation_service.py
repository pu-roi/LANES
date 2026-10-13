"""Credit-free source consistency checks, not independent or field verification.

Reparse the immutable article with the local Taglish rules, match the exact
occurrence, and retain bounded source spans for every supported fact. Ambiguous
claims remain review-only. Publication freshness and geometry gates stay owned
by the existing evaluation/publication services.
"""
from __future__ import annotations

from app.schemas.news_audit import (
    AuditEvidenceSpan, AuditedAccess, AuditedDepth, AuditedPlace, AuditedStatus,
    AuditedTime, IndependentAuditResult, ProviderClaimAudit,
)
from app.schemas.news_audit_batch import AuditCandidate
from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput

SOURCE_RULES_VERSION = "source-rules-v1"
SOURCE_POLICY_VERSION = "source-rules-v2-measurement-first"
SOURCE_RESPONSE_VERSION = "source-evidence-v2"


def validate_source_batch(candidates: tuple[AuditCandidate, ...], article: NewsArticleExtractorInput,
                          *, config_revision: str) -> dict[str, IndependentAuditResult]:
    from app.services.news_claim_auditor import (
        NewsClaimAuditor, AuditorConfig, canonical_claim_sha256, canonical_input_sha256,
        _classify, _normalized_place, _validate_evidence,
    )
    from app.services.news_evidence_policy import has_flood_observation, metro_manila_claim
    from app.services.taglish_extraction_service import extract_taglish_flood_facts

    identity = dict(provider="source_rules", model=SOURCE_RULES_VERSION,
                    prompt_version=SOURCE_POLICY_VERSION, response_version=SOURCE_RESPONSE_VERSION,
                    input_sha256=canonical_input_sha256(article))

    def result(claim: ExtractedClaim, reason: str, *, evidence: ProviderClaimAudit | None = None,
               outcome: str = "review") -> IndependentAuditResult:
        return IndependentAuditResult(outcome=outcome, reason_code=reason, evidence=evidence,
                                      claim_sha256=canonical_claim_sha256(claim), **identity)

    # Reuse immutable identity/size/offset bounds, without constructing an HTTP client.
    checker = NewsClaimAuditor(AuditorConfig(provider="source_rules", model=SOURCE_RULES_VERSION,
                                            config_revision=config_revision))
    try:
        checker.batch_document(candidates, article)
    except ValueError as exc:
        return {c.candidate_id: result(c.claim, str(exc), outcome="invalid") for c in candidates}
    body = (article.article_text or "").strip()
    parsed = extract_taglish_flood_facts(article)
    if parsed.errors or parsed.is_metadata_only:
        return {c.candidate_id: result(c.claim, "source_rules_incomplete_body") for c in candidates}
    options = checker._batch_options(candidates, body)
    spans = tuple(AuditEvidenceSpan(**option) for option in options)
    results: dict[str, IndependentAuditResult] = {}
    critical = {"photo_caption_only", "metadata_only_lead", "location_context_only",
                "contradictory_update", "city_context_ambiguous", "non_observation_list_context"}
    fact_fields = ("condition", "flood_mentioned", "is_forecast", "is_negated", "is_historical",
                   "event_time_kind", "event_time_raw", "event_time_resolved", "depth_raw",
                   "depth_canonical", "road_passability", "road_segment_raw", "local_area_raw", "place_type")
    for candidate in candidates:
        claim = candidate.claim
        matches = [p for p in parsed.claims if (p.raw_place_name, p.place_char_start, p.place_char_end)
                   == (claim.raw_place_name, claim.place_char_start, claim.place_char_end)]
        if len(matches) != 1:
            results[candidate.candidate_id] = result(claim, "source_rules_occurrence_unresolved")
            continue
        observed = matches[0]
        if (any(getattr(claim, field) != getattr(observed, field) for field in fact_fields)
                or any(_normalized_place(getattr(claim, field) or "")
                       != _normalized_place(getattr(observed, field) or "")
                       for field in ("canonical_city", "canonical_barangay"))):
            results[candidate.candidate_id] = result(claim, "source_rules_fact_disagreement")
            continue
        if (not metro_manila_claim(observed) or observed.is_forecast or observed.is_negated
                or observed.is_historical or critical.intersection(observed.uncertainty_reasons)
                or critical.intersection(claim.uncertainty_reasons)
                or observed.condition not in ("active", "rising", "receding", "subsided")
                or not has_flood_observation(observed.evidence_sentence)):
            results[candidate.candidate_id] = result(claim, "source_rules_unsupported_observation")
            continue

        # The parser's exact occurrence/context binding is required before any
        # surrounding quote may corroborate a fact. Quotes alone never pick a city.
        target = next((s for s in spans if s.start <= claim.place_char_start < claim.place_char_end <= s.end), None)
        if target is None:
            results[candidate.candidate_id] = result(claim, "source_rules_place_evidence_missing")
            continue
        place_spans = [target]
        for locality in (claim.canonical_city, claim.canonical_barangay):
            if locality and not any(_normalized_place(locality) in _normalized_place(s.quote) for s in place_spans):
                parent = next((s for s in spans if _normalized_place(locality) in _normalized_place(s.quote)), None)
                if parent is not None and parent not in place_spans:
                    place_spans.append(parent)
        time_span = next((s for s in spans if claim.event_time_raw and claim.event_time_raw in s.quote), None)
        time_supported = bool(time_span and claim.event_time_kind == "observation" and claim.event_time_resolved)
        time_spans = tuple(dict.fromkeys((time_span, target))) if time_span else ()
        bound = tuple(s for s in spans if s.start <= claim.place_char_start < claim.place_char_end <= s.end)
        depth_span = next((s for s in bound if claim.depth_raw and claim.depth_raw in s.quote), None)
        # The shared extractor selects explicit measurements before verbal
        # gauges. Re-parsing and exact fact matching above enforce that rule;
        # a paired descriptive label cannot override the reported measurement.
        access_supported = observed.road_passability != "unknown"
        audit = ProviderClaimAudit(
            claim_sha256=canonical_claim_sha256(claim),
            place=AuditedPlace(confirmed=True, evidence=tuple(place_spans), raw_place_name=claim.raw_place_name,
                              canonical_city=claim.canonical_city, canonical_barangay=claim.canonical_barangay),
            status=AuditedStatus(confirmed=True, evidence=(target,), classification=observed.condition,
                                contradictory=False, historical=False),
            time=AuditedTime(confirmed=time_supported, evidence=time_spans,
                            observed_at=claim.event_time_resolved.isoformat() if time_supported else None,
                            kind="observation" if time_supported else "unspecified"),
            depth=AuditedDepth(confirmed=depth_span is not None, evidence=(depth_span,) if depth_span else (),
                              canonical=claim.depth_canonical if depth_span else None,
                              raw=claim.depth_raw if depth_span else None, qualifiers=()),
            access=AuditedAccess(confirmed=access_supported, evidence=(target,) if access_supported else (),
                                classification=observed.road_passability),
        )
        reason = _validate_evidence(audit, claim, article, canonical_claim_sha256(claim))
        if reason:
            results[candidate.candidate_id] = result(claim, reason)
            continue
        outcome, reason = _classify(audit, claim)
        results[candidate.candidate_id] = result(claim, "source_rules_verified" if outcome == "verified" else reason,
                                               evidence=audit, outcome=outcome)
    return results
