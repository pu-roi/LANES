"""Displayed depth must not invent measured precision from gauge normalization."""
from datetime import datetime

import pytest

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_presentation_service import summarize_news_claim
from app.services.taglish_extraction_service import extract_taglish_flood_facts


@pytest.mark.parametrize("reported", [
    "approximately 8 inches", "about 8 inches", "up to 8 inches",
    "gutter-deep", "8 inches", "10-inch", "8 to 10 inches",
])
def test_display_preserves_reported_depth_and_qualifiers(reported: str) -> None:
    body = f"Flooding of {reported} affected Quirino Avenue in Manila."
    article = NewsArticleExtractorInput(article_id=-24, canonical_url="https://example.org/flood",
        publisher="Paraphrased fixture", title="Reported flooding", article_text=body,
        published_at=datetime.fromisoformat("2026-09-25T04:41:00+08:00"))
    claims = extract_taglish_flood_facts(article).claims
    road = next(claim for claim in claims if claim.canonical_road == "Quirino Avenue")
    assert road.depth_raw == reported
    original = road.model_dump()
    assert summarize_news_claim(road).water_level == reported
    assert road.model_dump() == original, "Presentation must not rewrite saved measurements"


def test_old_formatted_only_claims_keep_their_available_label() -> None:
    article = NewsArticleExtractorInput(article_id=-1, canonical_url="https://example.org/flood",
        publisher="Fixture", title="Flood report", article_text="Gutter-deep flooding affected Quirino Avenue in Manila.")
    road = next(c for c in extract_taglish_flood_facts(article).claims if c.canonical_road == "Quirino Avenue")
    label = road.depth_formatted
    assert label
    road.depth_raw = None
    assert summarize_news_claim(road).water_level == label
    road.depth_formatted = None
    assert summarize_news_claim(road).water_level == "Not stated in article"


@pytest.mark.parametrize("wording,label", [
    ("by 3:20 p.m.", "Floodwater subsided by"),
    ("as of 3:20 p.m.", "Floodwater subsided in article"),
])
def test_clearance_clock_preserves_status_and_by_bound(wording: str, label: str) -> None:
    article = NewsArticleExtractorInput(article_id=-1, canonical_url="https://example.org/clearance",
        publisher="Fixture", title="Road update",
        article_text=f"Flooding along East Avenue in Quezon City cleared {wording}",
        published_at=datetime.fromisoformat("2026-09-24T17:00:00+08:00"))
    road = next(c for c in extract_taglish_flood_facts(article).claims if c.canonical_road == "East Avenue")
    assert road.condition == "subsided" and road.event_time_resolved is not None
    summary = summarize_news_claim(road)
    assert summary.flood_time_label == label
    assert summary.flood_time == road.event_time_resolved
