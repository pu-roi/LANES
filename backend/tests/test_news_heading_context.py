"""Road-list context regressions from the September 9 indexed primary report."""
from datetime import datetime, timezone

import pytest

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.taglish_extraction_service import extract_taglish_flood_facts


def extract(body: str):
    article = NewsArticleExtractorInput(
        article_id=1, canonical_url="https://example.org/flood-list", publisher="Test",
        title="Flooded roads in Metro Manila", article_text=body,
        published_at=datetime(2026, 9, 9, 1, 19, tzinfo=timezone.utc),
    )
    return article, extract_taglish_flood_facts(article).claims


def test_city_clock_and_depth_headings_preserve_each_road_and_original_evidence():
    body = (
        "Below is a list of flooded areas:\n"
        "Quezon City (as of 8:55 a.m.)\n"
        "▶️ Tire-deep (26 inches)\nBrgy. Sienna\n"
        "- NS Amoranto cor Banawe St.\n- NS Amoranto cor Ubay St.\n"
        "▶️ Half knee-deep (19 inches)\nBrgy. Sto. Domingo (Matalahib)\n"
        "- NS Amoranto cor Banawe\n"
        "▶️ Gutter-deep (8 inches)\n"
        "- 48 Kapiligan\n- 29 Kapiligan\n- 42 Kapiligan\n"
        "- Calamba cor Don Jose\n- Samat cor Don Jose\n- Sto. Domingo cor. Calamba\n"
    )
    article, claims = extract(body)
    roads = [c for c in claims if c.place_type == "street"]
    assert len(roads) == 6
    addresses = [c for c in claims if c.raw_place_name in {"48 Kapiligan", "29 Kapiligan", "42 Kapiligan"}]
    assert len(addresses) == 3
    assert all(c.canonical_city == "Quezon City" and c.depth_raw == "8 inches" for c in addresses)
    assert all(c.canonical_city == "Quezon City" and c.psgc_code.startswith("13") for c in roads)
    assert [c.depth_raw for c in roads] == ["26 inches", "26 inches", "19 inches", "8 inches", "8 inches", "8 inches"]
    assert all(c.event_time_resolved == datetime(2026, 9, 9, 0, 55, tzinfo=timezone.utc) for c in roads)
    assert all(c.condition == "active" and c.flood_mentioned for c in roads)
    assert roads[0].canonical_barangay == "Sienna"
    assert roads[2].canonical_barangay == "Santo Domingo"
    assert "Banawe" in roads[0].road_segment_raw and "Banawe" in roads[2].road_segment_raw
    for c in roads:
        start, end = c.evidence_sentence_offset
        assert article.article_text[start:end] == c.evidence_sentence
        assert "Quezon City (as of 8:55 a.m.)" in c.evidence_sentence
        assert c.depth_raw in c.evidence_sentence
        assert article.article_text[c.place_char_start:c.place_char_end] == c.raw_place_name


def test_list_depth_and_clock_do_not_leak_into_another_city_or_narrative():
    _, claims = extract(
        "Below is a list of flooded areas:\nQuezon City (as of 8:55 a.m.)\n"
        "Tire-deep (26 inches)\nBrgy. Sienna\n- NS Amoranto cor Banawe St.\n"
        "Manila\n- Taft Avenue - gutter-deep\n"
        "Officials discussed road repairs for next month.\n"
        "In Pasig City, Caruncho Avenue was flooded."
    )
    amoranto = next(c for c in claims if c.canonical_road == "NS Amoranto")
    taft = next(c for c in claims if c.canonical_road == "Taft Avenue")
    caruncho = next(c for c in claims if c.canonical_road == "Caruncho Avenue")
    assert amoranto.depth_raw == "26 inches" and amoranto.event_time_resolved
    assert taft.canonical_city == "City of Manila" and taft.depth_canonical == "gutter"
    assert taft.event_time_resolved is None
    assert caruncho.canonical_city == "City of Pasig" and caruncho.depth_raw is None
    assert caruncho.event_time_resolved is None


@pytest.mark.parametrize("intro", [
    "The following roads may be flooded tomorrow:",
    "The following roads are not affected by flooding:",
    "The following flooded roads are part of a simulation:",
])
def test_depth_headings_do_not_override_non_observation_list_context(intro: str):
    _, claims = extract(intro + "\nQuezon City (as of 8:55 a.m.)\n"
                        "Waist-deep (37 inches)\nBrgy. Sienna\n- NS Amoranto cor Don Jose St.")
    road = next(c for c in claims if c.place_type == "street")
    assert road.depth_raw == "37 inches"
    assert not road.flood_mentioned and road.event_time_resolved is None


def test_inline_road_measurement_and_clock_override_group_headings():
    _, claims = extract(
        "Below is a list of flooded areas:\nQuezon City (as of 8:55 a.m.)\n"
        "Waist-deep (37 inches)\nBrgy. Sienna\n"
        "- NS Amoranto cor Don Jose St. - 8 inches as of 9:05 a.m.\n"
        "- NS Amoranto cor Palali St."
    )
    roads = [c for c in claims if c.place_type == "street"]
    assert roads[0].depth_raw == "8 inches" and roads[0].event_time_raw.lower() == "as of 9:05 a.m."
    assert roads[1].depth_raw == "37 inches" and roads[1].event_time_resolved.minute == 55


def test_heading_range_remains_a_range_and_clearance_overrides_wet_group():
    _, claims = extract(
        "Below is a list of flooded areas:\nQuezon City (as of 8:55 a.m.)\n"
        "Waist-deep (20-37 inches)\nBrgy. Sienna\n"
        "- NS Amoranto cor Don Jose St.\n"
        "- NS Amoranto cor Palali St. - floodwater subsided by 9:05 a.m."
    )
    roads = [c for c in claims if c.place_type == "street"]
    assert all(c.depth_raw == "20-37 inches" and c.depth_canonical is None for c in roads)
    assert "depth_range_not_point_value" in roads[0].uncertainty_reasons
    assert roads[1].condition == "subsided" and roads[1].event_time_raw.lower() == "by 9:05 a.m."
