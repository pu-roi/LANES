"""Road homonyms cannot supply another province while retaining a grounded city."""
from datetime import datetime

import pytest

from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from app.services.nationwide_geometry_service import NationwideGeometryService
from app.services.news_discovery_service import extract_captured_news_article
from app.services.news_presentation_service import summarize_news_claim


def road(name: str, city: str | None, code: str | None, province: str | None = None) -> ExtractedClaim:
    evidence = f"Flooding affected {name}" + (f" in {city}" if city else "") + "."
    return ExtractedClaim(raw_place_name=name, canonical_road=name, canonical_city=city,
        canonical_province=province, psgc_code=code, place_type="street", condition="active",
        flood_mentioned=True, evidence_sentence=evidence, evidence_sentence_offset=(0, len(evidence)),
        place_char_start=evidence.index(name), place_char_end=evidence.index(name) + len(name))


@pytest.mark.parametrize("name,city,code", [
    ("Calamba", "Quezon City", "1381300000"),
    ("Samat", "Quezon City", "1381300000"),
    ("Sto. Domingo", "Quezon City", "1381300000"),
    ("Blumentritt", "City of Manila", "1380600000"),
])
def test_ncr_city_and_psgc_replace_homonym_province_and_island(name: str, city: str, code: str) -> None:
    claim = road(name, city, code)
    ranked = NationwideGeometryService().rank_and_generate_geometry(claim, claim.evidence_sentence)
    assert ranked.resolved_city == city and ranked.psgc_code == code
    assert ranked.resolved_province is None and ranked.island_group == "Luzon"
    assert ranked.resolved_barangay is None
    assert not ranked.is_auto_approvable


@pytest.mark.parametrize("city,code,province,island", [
    ("City of Calamba", "0403405000", "Laguna", "Luzon"),
    ("City of Cebu", "0730600000", "Cebu", "Visayas"),
    ("City of Davao", "1130700000", "Davao del Sur", "Mindanao"),
])
def test_real_provincial_parent_is_preserved(city: str, code: str, province: str, island: str) -> None:
    claim = road("Blumentritt", city, code, province)
    ranked = NationwideGeometryService().rank_and_generate_geometry(claim, claim.evidence_sentence)
    assert ranked.resolved_city == city and ranked.psgc_code == code
    assert ranked.resolved_province == province and ranked.island_group == island


def test_grounded_barangay_psgc_remains_authoritative_for_road_parent() -> None:
    claim = road("Calamba", "Quezon City", "1381300077")
    claim.canonical_barangay = "Santo Domingo"
    ranked = NationwideGeometryService().rank_and_generate_geometry(claim)
    assert ranked.psgc_code == claim.psgc_code
    assert ranked.resolved_barangay == "Santo Domingo"
    assert ranked.resolved_province is None and ranked.island_group == "Luzon"


def test_road_homonym_without_city_does_not_inherit_province_or_island() -> None:
    claim = road("Calamba", None, None)
    ranked = NationwideGeometryService().rank_and_generate_geometry(claim)
    assert ranked.resolved_road == "Calamba"
    assert ranked.resolved_city is ranked.resolved_province is ranked.island_group is ranked.psgc_code is None


@pytest.mark.asyncio
async def test_saved_processing_entry_and_card_area_keep_manila_out_of_negros() -> None:
    article = NewsArticleExtractorInput(article_id=-1, canonical_url="https://example.org/flood",
        publisher="Example", title="Flood report", published_at=datetime.fromisoformat("2026-09-09T21:24:42+08:00"),
        article_text="España Boulevard, Blumentritt and other streets in Manila were flooded.")
    result = await extract_captured_news_article(article)
    assert result.error is None
    claim = next(c for c in result.extraction.claims if c.canonical_road == "Blumentritt")
    assert claim.canonical_city == "City of Manila" and claim.psgc_code == "1380600000"
    assert claim.canonical_province is None and claim.island_group == "Luzon"
    assert summarize_news_claim(claim).area == "City of Manila"
