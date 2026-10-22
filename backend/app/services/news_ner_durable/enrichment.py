"""C3b derived read view and allowed placement fields before owned completion."""
from __future__ import annotations

from app.schemas.news_ner_result import parse_saved_result
from app.services.news_road_placement_service import get_news_road_placement_provider
from app.services.news_placement_preview_service import get_news_placement_preview_service
from .assets import TrustedAssets, placement_identity
from .contracts import RunEvidence, NerEvidenceError
from .read_projection import build_read_projection


def enrich_native_result(context: RunEvidence, result: object, trusted: TrustedAssets):
    if trusted.manifest['geography'].get('placement') != placement_identity():
        raise NerEvidenceError('ner_configuration_invalid')
    provider = get_news_road_placement_provider()
    preview = get_news_placement_preview_service()
    for claim in result.claims:
        claim.road_placement = provider.resolve(claim)
        claim.placement_preview = preview.preview(claim,claim.road_placement)
    result.read_projection = build_read_projection(context.source(),result,trusted.catalog)
    # Fresh inference/proposals/graph were already verified by build_native_result.
    # Only the three explicitly permitted enrichment fields are assigned here;
    # stored evidence is independently recomputed at operational source checking.
    return parse_saved_result('ner_rules_v1',result)
