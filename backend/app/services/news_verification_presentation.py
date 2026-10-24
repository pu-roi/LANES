"""Read-only field review needs; source consistency never proves field conditions."""
from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from pydantic import BaseModel

from app.schemas.news_presentation import NewsFloodSummary, NewsVerificationIssue


def with_verification(summary: NewsFloodSummary, claim: BaseModel | Mapping[str, Any], *,
                      estimated_placement: bool = False, source_state: str | None = None,
                      depth_scope: str | None = None) -> NewsFloodSummary:
    raw = claim.model_dump(mode='json') if isinstance(claim, BaseModel) else dict(claim)
    issues: dict[str, NewsVerificationIssue] = {}
    labels = {'location': 'Location', 'road': 'Street / road', 'water_level': 'Water level / depth',
              'flood_time': 'Flood time', 'condition': 'Flood condition', 'source': 'Source evidence'}

    def add(field: str, state: str, code: str, reason: str) -> None:
        issues[field] = NewsVerificationIssue(field=field, label=labels[field], state=state, code=code, reason=reason)

    placement = raw.get('road_placement') or {}
    estimated = estimated_placement or summary.placement_is_estimate
    if not raw.get('canonical_city'):
        add('location', 'missing', 'city_unresolved', 'The city was not resolved. Check the location and its city in the source.')
    elif estimated:
        add('location', 'uncertain', 'estimated_extent', 'An estimated zone is plotted. Its exact flooded section and extent still need verification.')
    elif placement.get('status') == 'ambiguous':
        add('location', 'uncertain', 'ambiguous_location', 'Several possible road sections were recorded. Confirm the affected section; any plotted estimate is not an exact flood boundary.')
    elif placement.get('status') == 'bounded_candidate':
        add('location', 'uncertain', 'suggested_location', 'A map suggestion is available. Confirm the exact affected section before treating it as verified.')
    elif placement.get('status') == 'source_unavailable':
        add('location', 'uncertain', 'map_data_unavailable', 'Map data was unavailable for this extraction. Check the location when the data is available.')
    else:
        add('location', 'uncertain', 'location_unresolved', 'The exact affected location has not been established in the saved placement evidence.')

    road_expected = (raw.get('place_type') == 'street' or raw.get('road_segment_raw')
                     or re.search(r'\b(?:street|st\.?|road|rd\.?|avenue|ave\.?|alley|highway|boulevard)\b',
                                  raw.get('raw_place_name') or '', re.I))
    if road_expected and not raw.get('canonical_road'):
        add('road', 'missing', 'road_unresolved', 'The source mentions a road or section, but its street identity was not resolved. Review the original wording and locality.')

    uncertainty = set(raw.get('uncertainty_reasons') or [])
    audit = raw.get('audit_result') or {}
    independent = (audit.get('independent_audit') or {}).get('evidence') or {}
    if not (raw.get('depth_raw') or raw.get('depth_formatted') or '').strip():
        add('water_level', 'missing', 'depth_missing', 'No water level or depth wording was saved from the article. Check the source; do not infer a depth from the hazard map.')
    elif audit.get('depth_discrepancy_note'):
        add('water_level', 'conflicting', 'depth_conflict', 'The saved depth check found a discrepancy. Compare the reported measurement with the source passage.')
    elif not (raw.get('depth_raw') or '').strip():
        add('water_level', 'uncertain', 'depth_wording_missing', 'Only a normalized depth is available. Check the source wording before treating it as a reported measurement.')
    elif (any('depth' in code for code in uncertainty)
          or independent.get('depth', {}).get('confirmed') is False
          or (audit and audit.get('depth_confirmed') is False)):
        add('water_level', 'uncertain', 'depth_unconfirmed', 'The saved depth evidence is uncertain or was not confirmed by its source check. Review the reported wording and measurement.')
    elif depth_scope == 'shared':
        add('water_level', 'uncertain', 'shared_depth', 'The article gives one depth for several locations. Confirm its applicability to this location; no individual measurement was supplied.')
    if not raw.get('event_time_resolved'):
        add('flood_time', 'missing', 'flood_time_missing', 'The flood time was not resolved. Article publication time alone does not establish when this location flooded.')
    elif any('time' in code for code in uncertainty):
        add('flood_time', 'uncertain', 'flood_time_uncertain', 'The extraction recorded uncertainty about the flood time. Check the time wording in the source.')
    if raw.get('condition', 'unknown') == 'unknown':
        add('condition', 'uncertain', 'condition_unclear', 'The saved evidence does not clearly establish the flood condition at this location.')
    if summary.reading_reason:
        add('source', 'uncertain', 'source_needs_checking', summary.reading_reason)
    if source_state == 'different_capture':
        add('source', 'conflicting', 'source_capture_changed', 'The current saved article differs from this observation’s source version. Compare the original evidence before using it.')
    elif source_state == 'current_unavailable':
        add('source', 'uncertain', 'current_source_unavailable', 'The current article body is unavailable. Review the saved extraction evidence.')
    return summary.model_copy(update={'verification_status': 'needs_verification' if issues else 'no_issues_recorded',
        'verification_issues': list(issues.values()), 'placement_is_estimate': estimated,
        **({'map_status': 'Estimated zone plotted; exact flood extent needs verification'} if estimated else {})})


def detail_with_verification(detail: Any) -> Any:
    """Use the full saved claim even when a lightweight group item omits fields."""
    raw: dict[str, Any] = {}
    result = getattr(detail, 'result', None)
    ordinal = detail.item.claim_index
    if result is not None and ordinal is not None and 0 <= ordinal < len(result.claims):
        raw.update(result.claims[ordinal].model_dump(mode='json'))
    raw.update(detail.claim.model_dump(mode='json'))
    review = detail.source_review
    summary = with_verification(detail.item.summary, raw, source_state=review.state if review else None,
                                depth_scope=getattr(detail, 'depth_scope', None))
    return detail.model_copy(update={'item': detail.item.model_copy(update={'summary': summary})})
