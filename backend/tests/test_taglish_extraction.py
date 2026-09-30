"""Unit and regression tests for Taglish NLP extraction service."""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.taglish_extraction_service import (
    extract_depth_from_text,
    extract_taglish_flood_facts,
    find_place_mentions,
    normalize_barangay_name,
    resolve_observation_time,
    split_sentences_with_offsets,
)


def test_psgc_barangay_normalization():
    assert normalize_barangay_name("Maybunga") == "Maybunga"
    assert normalize_barangay_name("Barangay Maybunga") == "Maybunga"
    assert normalize_barangay_name("Brgy. Sta. Lucia") == "Santa Lucia"
    assert normalize_barangay_name("Sta. Rosa") == "Santa Rosa"
    assert normalize_barangay_name("Sto. Tomas") == "Santo Tomas"
    assert normalize_barangay_name("Maybunnga") == "Maybunga"
    assert normalize_barangay_name("Brgy. Palatiw") == "Palatiw"
    assert normalize_barangay_name("pala") is None
    assert normalize_barangay_name("NonExistentBarangay") is None


def test_depth_canonical_mapping_all_levels():
    cases = [
        ("gutter-deep ang tubig", "gutter", "rule_gutter_deep"),
        ("abot-sakong ang baha", "gutter", "rule_gutter_deep"),
        ("half-knee deep water", "half-knee", "rule_half_knee_deep"),
        ("lampas sakong na ang tubig", "half-knee", "rule_half_knee_deep"),
        ("half-tire deep ang baha", "half-tire", "rule_half_tire_deep"),
        ("kalahati ng gulong", "half-tire", "rule_half_tire_deep"),
        ("knee-deep floodwaters", "knee", "rule_knee_deep"),
        ("lagpas tuhod ang baha", "knee", "rule_knee_deep"),
        ("tire-deep flood", "tires", "rule_tire_deep"),
        ("abot-gulong sa kalsada", "tires", "rule_tire_deep"),
        ("waist-deep floodwaters", "waist", "rule_waist_deep"),
        ("lagpas baywang ang tubig", "waist", "rule_waist_deep"),
        ("chest-deep levels", "chest", "rule_chest_deep"),
        ("abot-dibdib na baha", "chest", "rule_chest_deep"),
        ("neck-deep waters", "neck", "rule_neck_deep"),
        ("lagpas leeg na ang tubig", "neck", "rule_neck_deep"),
    ]
    for text, expected_canon, expected_rule in cases:
        raw, canon, rule, reasons = extract_depth_from_text(text)
        assert canon == expected_canon, f"Failed for '{text}': got {canon}, expected {expected_canon}"
        assert rule == expected_rule


def test_ambiguous_depth_mapping():
    cases = [
        "1 to 2 feet ang taas",
        "approximately 45 centimeters",
        "mataas na pagbaha sa lugar",
        "deep floodwaters in the street",
        "abot-bubong ang baha",
    ]
    for text in cases:
        raw, canon, rule, reasons = extract_depth_from_text(text)
        assert raw is not None, f"Expected raw depth extracted for '{text}'"
        assert canon is None, f"Expected canonical to be None for '{text}'"
        if " to " in text:
            assert rule == "numeric_depth_range"
            assert "depth_range_not_point_value" in reasons
        else:
            assert rule in ("unsupported_or_ambiguous_scale", "numeric_depth_without_exact_gauge")
            assert reasons


def _article_claims(title: str, text: str):
    return extract_taglish_flood_facts(NewsArticleExtractorInput(
        article_id=200, canonical_url="https://example.com/flood", publisher="Test News",
        title=title, article_text=text,
    )).claims


def test_gma_road_segment_and_observation_time():
    text = ("In Quezon City, floodwater was waist-deep on Sto. Domingo Avenue "
            "between Atok and Calamba Streets as of 1:12 p.m.")
    claims = _article_claims("Quezon City flooding", text)
    road = next(c for c in claims if c.raw_place_name == "Sto. Domingo Avenue")
    assert road.canonical_city == "Quezon City"
    assert road.road_segment_raw == "between Atok and Calamba Streets"
    assert road.depth_canonical == "waist"
    assert road.event_time_raw == "as of 1:12 p.m."
    assert road.event_time_kind == "observation"
    assert not any(c.canonical_city == "City of Calamba" for c in claims)


def test_explicit_observation_clock_resolves_from_aware_publication_time():
    article = NewsArticleExtractorInput(
        article_id=201, canonical_url="https://example.com/flood", publisher="Test News",
        title="Quezon City flooding",
        article_text="Floodwater was waist-deep on Sto. Domingo Avenue in Quezon City as of 4:30 p.m.",
        published_at=datetime(2026, 9, 28, 10, 0, tzinfo=timezone.utc),
    )
    road = next(c for c in extract_taglish_flood_facts(article).claims if c.raw_place_name == "Sto. Domingo Avenue")
    assert road.event_time_kind == "observation"
    assert road.event_time_resolved is not None
    assert road.event_time_resolved.isoformat() == "2026-09-28T16:30:00+08:00"


def test_observation_clock_midnight_rollover_and_uncertain_dates():
    just_after_midnight = datetime(2026, 9, 28, 16, 15, tzinfo=timezone.utc)
    resolved = resolve_observation_time("as of 11:30 p.m.", "Flooding as of 11:30 p.m.", just_after_midnight)
    assert resolved is not None and resolved.isoformat() == "2026-09-28T23:30:00+08:00"
    assert resolve_observation_time("as of 5 a.m.", "Flooding as of 5 a.m.",
                                    datetime(2026, 9, 28, 10, 0, tzinfo=timezone.utc)) is None
    assert resolve_observation_time("as of 4:30 p.m.", "Flooding as of 4:30 p.m. yesterday",
                                    datetime(2026, 9, 28, 10, 0, tzinfo=timezone.utc)) is None
    assert resolve_observation_time("as of 4:30 p.m.", "Flooding as of 4:30 p.m. on Sunday",
                                    datetime(2026, 9, 28, 10, 0, tzinfo=timezone.utc)) is None
    assert resolve_observation_time("as of 4:30 p.m.", "Flooding as of 4:30 p.m. on Sept. 27",
                                    datetime(2026, 9, 28, 10, 0, tzinfo=timezone.utc)) is None
    assert resolve_observation_time("as of 4:30 p.m.", "Flooding as of 4:30 p.m.",
                                    datetime(2026, 9, 28, 10, 0)) is None
    assert resolve_observation_time("as of 13:30 p.m.", "Flooding as of 13:30 p.m.",
                                    just_after_midnight) is None


def test_report_clock_is_not_promoted_to_observation():
    article = NewsArticleExtractorInput(
        article_id=202, canonical_url="https://example.com/flood", publisher="Test News",
        title="Malabon flooding",
        article_text="At 4:30 p.m., Malabon officials reported waist-deep floodwaters along M.H. Del Pilar.",
        published_at=datetime(2026, 9, 28, 10, 0, tzinfo=timezone.utc),
    )
    road = next(c for c in extract_taglish_flood_facts(article).claims if c.raw_place_name == "M.H. Del Pilar")
    assert road.event_time_kind == "report"
    assert road.event_time_resolved is None


def test_inquirer_roads_keep_separate_measured_depths_and_unknown_time():
    text = ("Biak-na-Bato Street had flooding as high as 37 inches, WHILE Mauban Street "
            "had floodwater up to 19 inches.")
    claims = _article_claims("Quezon City flood update", text)
    roads = {c.raw_place_name: c for c in claims if c.place_type == "street"}
    assert set(roads) == {"Biak-na-Bato Street", "Mauban Street"}
    assert (roads["Biak-na-Bato Street"].depth_raw, roads["Biak-na-Bato Street"].depth_canonical) == ("as high as 37 inches", "waist")
    assert (roads["Mauban Street"].depth_raw, roads["Mauban Street"].depth_canonical) == ("up to 19 inches", "knee")
    assert all("upper_bound_depth" in c.uncertainty_reasons for c in roads.values())
    assert all(c.canonical_city == "Quezon City" and c.event_time_raw is None for c in roads.values())


def test_malabon_report_keeps_local_areas_and_collective_depth():
    text = ("At 7 p.m., Malabon officials reported thigh-deep floodwaters along M.H. Del Pilar "
            "in Maysilo, about 37 inches. Sitio 6 in Catmon, Dr. Lascano in Tugatog, "
            "and Central Market area in Tañong had floodwaters around 26 inches.")
    claims = _article_claims("Malabon flooded roads", text)
    by_name = {c.raw_place_name: c for c in claims}
    road = by_name["M.H. Del Pilar"]
    assert road.local_area_raw == "Maysilo"
    assert road.depth_raw == "about 37 inches" and road.depth_canonical == "waist"
    assert "approximate_depth" in road.uncertainty_reasons
    assert road.event_time_raw == "At 7 p.m."
    assert road.event_time_kind == "report"
    for name, area in (("Sitio 6", "Catmon"), ("Dr. Lascano", "Tugatog"), ("Central Market area", "Tañong")):
        claim = by_name[name]
        assert claim.local_area_raw == area
        assert claim.canonical_city == "City of Malabon"
        assert claim.depth_raw == "around 26 inches" and claim.depth_canonical == "tires"
        assert "approximate_depth" in claim.uncertainty_reasons
        assert claim.event_time_raw is None


def test_unmapped_thigh_and_depth_range_remain_uncertain():
    assert extract_depth_from_text("thigh-deep floodwater")[1] is None
    raw, canonical, _, reasons = extract_depth_from_text("10 to 19 inches")
    assert raw == "10 to 19 inches" and canonical is None
    assert "depth_range_not_point_value" in reasons
    raw, canonical, _, reasons = extract_depth_from_text("up to 19 inches")
    assert raw == "up to 19 inches" and canonical == "knee"
    assert "upper_bound_depth" in reasons


def test_road_list_inherits_shared_range_without_inventing_individual_depth():
    text = ("Other roads had floodwaters ranging from 10 to 19 inches. "
            "These included Maria Clara in Acacia; Burgos and Sto. Niño in Concepcion; "
            "Gov. Pascual near Robinsons in Tinajeros; and P. Aquino in Tonsuya.")
    claims = _article_claims("Malabon roads flooded", text)
    by_name = {c.raw_place_name: c for c in claims}
    assert {"Maria Clara", "Burgos", "Sto. Niño", "Gov. Pascual", "P. Aquino"} <= set(by_name)
    assert "Robinsons" not in by_name
    assert by_name["Burgos"].local_area_raw == "Concepcion"
    assert all(c.depth_raw == "10 to 19 inches" and c.depth_canonical is None for c in claims)
    assert all("shared_depth_range_not_individual_measurement" in c.uncertainty_reasons for c in claims)


def test_full_malabon_article_structure_keeps_every_reported_location_distinct():
    # Paraphrases the publisher's report while retaining its full location lists.
    text = (
        "At 7 p.m., Malabon responders reported thigh-deep floodwater along M.H. Del Pilar in Maysilo, about 37 inches. "
        "Sitio 6 in Catmon, Dr. Lascano in Tugatog, and Central Market area in Tañong had around 26 inches of floodwater and were not passable to all vehicles. "
        "Other roads were closed to light vehicles because floodwaters ranged from 10 to 19 inches. "
        "These included Maria Clara in Acacia; Burgos and Sto. Niño in Concepcion; Don Basilio in Hulong Duhat; Pampano in Longos; Sto. Niño in Muzon; Silver Swan in Panghulo; Rizal Avenue-Magsaysay in San Agustin; Tatawid Market in Santulan; M.H. Del Pilar in Tugatog and Tinajeros; Gov. Pascual near Robinsons in Tinajeros; and P. Aquino and Sanciangco in Tonsuya. "
        "Meanwhile, flooded roads remained passable to all vehicles, including portions of Gen. Luna, Gov. Pascual, M. Sioson, Naval, C. Arellano, Borromeo, Yanga, University Avenue, and other streets in Baritan, Bayan-Bayanan, Dampalit, Flores, Hulong Duhat, Ibaba, Longos, Maysilo, Potrero, San Agustin, and Santulan."
    )
    claims = _article_claims("Malabon flood report", text)
    named = [c for c in claims if c.place_type in ("street", "landmark")]
    assert len(named) == 26  # 1 primary road, 3 impassable sites, 14 light-vehicle closures, 8 passable roads
    assert len([c for c in claims if c.road_passability == "impassable_all"]) == 3
    light_closed = [c for c in claims if c.road_passability == "light_vehicle_closed"]
    assert len(light_closed) == 14
    assert {(c.raw_place_name, c.local_area_raw) for c in light_closed if c.raw_place_name == "M.H. Del Pilar"} == {
        ("M.H. Del Pilar", "Tugatog"), ("M.H. Del Pilar", "Tinajeros")
    }
    assert all(c.depth_raw == "10 to 19 inches" and c.depth_canonical is None for c in light_closed)
    passable_roads = [c for c in named if c.road_passability == "passable_all"]
    assert {c.raw_place_name for c in passable_roads} == {
        "Gen. Luna", "Gov. Pascual", "M. Sioson", "Naval", "C. Arellano", "Borromeo", "Yanga", "University Avenue"
    }
    assert all(c.depth_raw is None for c in passable_roads)
    area_claims = [c for c in claims if "unnamed_street_in_barangay" in c.uncertainty_reasons]
    assert len(area_claims) == 11
    assert all(c.place_type == "barangay" and c.road_passability == "passable_all" for c in area_claims)
    assert next(c for c in area_claims if c.raw_place_name == "Santulan").canonical_barangay is None
    assert not any(c.raw_place_name == "Robinsons" for c in claims)
    assert all(c.canonical_city == "City of Malabon" for c in claims)
    assert all(text[c.place_char_start:c.place_char_end] == c.raw_place_name for c in claims)


def test_sentence_split_protects_abbreviations_and_initials():
    text = (
        "Flooding along C. Raymundo Avenue in Rosario was reported. "
        "Brgy. Sta. Lucia experienced heavy rainfall at 2:00 P.M. today."
    )
    spans = split_sentences_with_offsets(text)
    assert len(spans) == 2
    assert spans[0][0].startswith("Flooding along C. Raymundo Avenue")
    assert spans[1][0].startswith("Brgy. Sta. Lucia")


def test_active_flood_extraction():
    inp = NewsArticleExtractorInput(
        article_id=101,
        canonical_url="https://example.com/test-101",
        publisher="Test News",
        title="Baha sa Pasig",
        excerpt="Binaha ang Barangay Maybunga sa Pasig City kaninang 2:00 PM, abot-tuhod ang tubig.",
        article_text="Binaha ang Barangay Maybunga sa Pasig City kaninang 2:00 PM, abot-tuhod ang tubig.",
    )
    res = extract_taglish_flood_facts(inp)
    assert len(res.claims) >= 1
    claim = next(c for c in res.claims if c.canonical_barangay == "Maybunga")
    assert claim.flood_mentioned is True
    assert claim.is_negated is False
    assert claim.depth_canonical == "knee"
    assert claim.depth_raw == "abot-tuhod"
    assert claim.condition == "active"
    assert claim.event_time_raw == "kaninang 2:00 PM"
    assert claim.evidence_sentence_offset[0] == 0


def test_negated_flood_extraction():
    inp = NewsArticleExtractorInput(
        article_id=102,
        canonical_url="https://example.com/test-102",
        publisher="Test News",
        title="Pasig Status",
        excerpt="Walang baha sa Barangay Kapitolyo at nananatiling passable sa lahat ng uri ng sasakyan.",
        article_text="Walang baha sa Barangay Kapitolyo at nananatiling passable sa lahat ng uri ng sasakyan.",
    )
    res = extract_taglish_flood_facts(inp)
    assert len(res.claims) >= 1
    claim = res.claims[0]
    assert claim.canonical_barangay == "Kapitolyo"
    assert claim.flood_mentioned is False
    assert claim.is_negated is True
    assert "negated_flood_report" in claim.uncertainty_reasons


def test_forecast_extraction():
    inp = NewsArticleExtractorInput(
        article_id=103,
        canonical_url="https://example.com/test-103",
        publisher="Test News",
        title="Weather Advisory",
        excerpt="Babala ng PAGASA: Posibleng bahain ang mababang lugar sa Santolan mamayang gabi.",
        article_text="Babala ng PAGASA: Posibleng bahain ang mababang lugar sa Santolan mamayang gabi.",
    )
    res = extract_taglish_flood_facts(inp)
    assert len(res.claims) >= 1
    claim = res.claims[0]
    assert claim.canonical_barangay == "Santolan"
    assert claim.flood_mentioned is False
    assert claim.is_forecast is True
    assert "forecast_or_warning_only" in claim.uncertainty_reasons


def test_historical_flood_extraction():
    inp = NewsArticleExtractorInput(
        article_id=104,
        canonical_url="https://example.com/test-104",
        publisher="Test News",
        title="Typhoon Lookback",
        excerpt="Noong nakaraang taon sa Bagyong Carina, nalubog sa abot-leeg na baha ang Barangay Malinao.",
        article_text="Noong nakaraang taon sa Bagyong Carina, nalubog sa abot-leeg na baha ang Barangay Malinao.",
    )
    res = extract_taglish_flood_facts(inp)
    assert len(res.claims) >= 1
    claim = res.claims[0]
    assert claim.canonical_barangay == "Malinao"
    assert claim.flood_mentioned is False
    assert claim.is_historical is True
    assert claim.depth_canonical == "neck"
    assert "historical_reference_only" in claim.uncertainty_reasons


def test_multi_location_attribution():
    text = "Lubog sa abot-tuhod na baha ang Bagong Katipunan habang nananatiling walang baha sa Pineda kaninang 1 PM."
    inp = NewsArticleExtractorInput(
        article_id=105,
        canonical_url="https://example.com/test-105",
        publisher="Test News",
        title="Dual Status",
        excerpt=text,
        article_text=text,
    )
    res = extract_taglish_flood_facts(inp)
    claim_bk = next(c for c in res.claims if c.canonical_barangay == "Bagong Katipunan")
    claim_pin = next(c for c in res.claims if c.canonical_barangay == "Pineda")

    assert claim_bk.flood_mentioned is True
    assert claim_bk.is_negated is False
    assert claim_bk.depth_canonical == "knee"

    assert claim_pin.flood_mentioned is False
    assert claim_pin.is_negated is True


def test_metadata_only_lead_flagging():
    inp = NewsArticleExtractorInput(
        article_id=106,
        canonical_url="https://example.com/test-106",
        publisher="Test News",
        title="Binaha ang Caniogan abot-sakong",
        excerpt="Mabilis na umapaw ang tubig sa Caniogan kanina.",
        article_text=None,
    )
    res = extract_taglish_flood_facts(inp)
    assert res.is_metadata_only is True
    assert len(res.claims) >= 1
    assert any("metadata_only_lead" in c.uncertainty_reasons for c in res.claims)


def test_extraction_idempotency_and_determinism():
    inp = NewsArticleExtractorInput(
        article_id=107,
        canonical_url="https://example.com/test-107",
        publisher="Test News",
        title="Determinism Test",
        excerpt="Binaha ang Sagad abot-baywang.",
        article_text="Binaha ang Sagad abot-baywang kaninang 3 PM. Bumababa na ang tubig ngayon.",
    )
    res1 = extract_taglish_flood_facts(inp)
    res2 = extract_taglish_flood_facts(inp)

    assert len(res1.claims) == len(res2.claims)
    for c1, c2 in zip(res1.claims, res2.claims):
        assert c1.raw_place_name == c2.raw_place_name
        assert c1.canonical_barangay == c2.canonical_barangay
        assert c1.depth_canonical == c2.depth_canonical
        assert c1.condition == c2.condition
        assert c1.is_negated == c2.is_negated


def test_extracted_claim_populates_physical_measurements():
    inp = NewsArticleExtractorInput(
        article_id=108,
        canonical_url="https://example.com/test-108",
        publisher="Test News",
        title="Measurement Test",
        excerpt="Binaha ang Caniogan knee-deep.",
        article_text="Lagpas tuhod ang baha sa Caniogan dahil sa tuluy-tuloy na ulan.",
    )
    res = extract_taglish_flood_facts(inp)
    assert len(res.claims) >= 1
    claim = res.claims[0]
    assert claim.depth_canonical == "knee"
    assert claim.depth_meters == 0.48
    assert claim.depth_inches == 19.0
    assert '19" (0.48m)' in (claim.depth_formatted or "")


def test_pasig_historical_corridor_extraction():
    text = "Binaha ang Urbano Velasco Ave at Ortigas Ext sa Pasig kaninang hapon abot-gutter."
    inp = NewsArticleExtractorInput(
        article_id=109,
        canonical_url="https://example.com/test-109",
        publisher="Test News",
        title="Pasig Corridors",
        excerpt=text,
        article_text=text,
    )
    res = extract_taglish_flood_facts(inp)
    names = [c.raw_place_name for c in res.claims]
    assert any("Urbano Velasco" in n for n in names)
    assert any("Ortigas Ext" in n for n in names)
    c_urbano = next(c for c in res.claims if "Urbano Velasco" in c.raw_place_name)
    assert c_urbano.place_type == "street"
    assert c_urbano.depth_canonical == "gutter"


def test_nationwide_place_extraction_luzon():
    text = "Binaha ang MacArthur Highway sa San Fernando, Pampanga nang umabot sa gutter-deep ang tubig."
    inp = NewsArticleExtractorInput(
        article_id=110,
        canonical_url="https://example.com/test-110",
        publisher="Regional News",
        title="Pampanga Flood",
        excerpt=text,
        article_text=text,
    )
    res = extract_taglish_flood_facts(inp)
    assert len(res.claims) >= 2
    road_claim = next(c for c in res.claims if c.place_type == "street")
    assert "MacArthur Highway" in road_claim.raw_place_name
    assert road_claim.depth_canonical == "gutter"

    prov_claim = next((c for c in res.claims if c.place_type == "province"), None)
    city_claim = next((c for c in res.claims if c.place_type == "city"), None)
    assert prov_claim is not None or city_claim is not None


def test_nationwide_place_extraction_visayas():
    text = "Lubog sa knee-deep na baha ang Colon Street sa Cebu City kaninang umaga."
    inp = NewsArticleExtractorInput(
        article_id=111,
        canonical_url="https://example.com/test-111",
        publisher="Visayas News",
        title="Cebu Flooding",
        excerpt=text,
        article_text=text,
    )
    res = extract_taglish_flood_facts(inp)
    assert len(res.claims) >= 1
    street_claim = next(c for c in res.claims if c.place_type == "street")
    assert "Colon Street" in street_claim.raw_place_name
    assert street_claim.depth_canonical == "knee"

    city_claim = next(c for c in res.claims if c.place_type == "city")
    assert "Cebu City" in city_claim.raw_place_name
    assert city_claim.island_group == "Visayas"


def test_nationwide_place_extraction_mindanao():
    text = "Nalubog sa waist-deep na baha ang Brgy. Matina Crossing sa Davao City dahil sa pag-apaw ng ilog."
    inp = NewsArticleExtractorInput(
        article_id=112,
        canonical_url="https://example.com/test-112",
        publisher="Mindanao News",
        title="Davao Flood",
        excerpt=text,
        article_text=text,
    )
    res = extract_taglish_flood_facts(inp)
    assert len(res.claims) >= 1
    bgy_claim = next(c for c in res.claims if c.place_type == "barangay")
    assert "Matina Crossing" in bgy_claim.raw_place_name
    assert bgy_claim.canonical_barangay == "Matina Crossing"
    assert bgy_claim.depth_canonical == "waist"
    assert bgy_claim.island_group == "Mindanao"
    assert bgy_claim.canonical_city == "City of Davao"


def test_metro_manila_article_list_headings_scope_city_barangay_and_passability():
    inp = NewsArticleExtractorInput(
        article_id=113,
        canonical_url="https://example.com/metro-manila-list",
        publisher="Test News",
        title="Flooded Metro Manila roads",
        article_text=(
            "Impassable to all types of vehicles\n"
            "Quezon City\n"
            "Brgy. Sienna\n"
            "Banawe St. - 26 inches, tire deep\n"
            "Passable with caution\n"
            "Manila\n"
            "Taft Avenue - 8 inches, gutter deep"
        ),
    )
    claims = extract_taglish_flood_facts(inp).claims
    banawe = next(claim for claim in claims if claim.raw_place_name == "Banawe St")
    taft = next(claim for claim in claims if claim.raw_place_name == "Taft Avenue")
    assert banawe.canonical_city == "Quezon City"
    assert banawe.canonical_barangay == "Sienna"
    assert banawe.depth_raw == "26 inches"
    assert banawe.road_passability == "impassable_all"
    assert taft.canonical_city == "City of Manila"
    assert taft.depth_raw == "8 inches"
    assert taft.road_passability == "passable_all"


def test_article_list_keeps_intersections_inline_barangays_and_report_time():
    inp = NewsArticleExtractorInput(
        article_id=114,
        canonical_url="https://example.com/intersections",
        publisher="Test News",
        title="Metro Manila road update",
        article_text=(
            "As of 4:30 p.m, flooding affected the following routes:\n"
            "Impassable to light vehicles\nQuezon City\n"
            "Brgy. Sienna, Don Jose St cor Sct Alcaraz St. - 19 inches\n"
            "Brgy. Sto. Domingo, NS Amoranto cor. Banawe - 10 inches"
        ),
    )
    claims = extract_taglish_flood_facts(inp).claims
    don_jose = next(c for c in claims if c.raw_place_name == "Don Jose St")
    amoranto = next(c for c in claims if c.raw_place_name == "NS Amoranto")
    assert don_jose.canonical_city == "Quezon City"
    assert don_jose.canonical_barangay == "Sienna"
    assert "Sct Alcaraz" in don_jose.road_segment_raw
    assert don_jose.depth_raw == "19 inches"
    assert don_jose.road_passability == "light_vehicle_closed"
    assert don_jose.event_time_raw == "As of 4:30 p.m"
    assert "Banawe" in amoranto.road_segment_raw
    assert amoranto.depth_raw == "10 inches"


def test_mixed_city_article_does_not_resolve_barangay_from_partial_city_word():
    inp = NewsArticleExtractorInput(
        article_id=115,
        canonical_url="https://example.com/mixed-city",
        publisher="Test News",
        title="Metro Manila flooding",
        article_text=(
            "As of 6:20 p.m., flooding was reported.\n"
            "In Manila, Rizal Avenue corner Bambang Street was flooded at 19 inches.\n"
            "In Malabon City, Barangay San Agustin and C. Arellano Street in Ibaba were flooded."
        ),
    )
    claims = extract_taglish_flood_facts(inp).claims
    rizal = next(c for c in claims if c.raw_place_name == "Rizal Avenue")
    san_agustin = next(c for c in claims if c.raw_place_name == "Barangay San Agustin")
    assert rizal.canonical_city == "City of Manila"
    assert rizal.road_segment_raw == "Rizal Avenue corner Bambang Street"
    assert san_agustin.canonical_city == "City of Malabon"
    assert san_agustin.canonical_barangay == "San Agustin"
    assert not any(c.raw_place_name == "Bambang" and c.place_type == "barangay" for c in claims)


def test_suffixless_advisory_roads_keep_their_named_sections():
    inp = NewsArticleExtractorInput(
        article_id=116,
        canonical_url="https://example.com/road-list",
        publisher="Test News",
        title="NCR flood advisory",
        article_text=(
            "Other flooded roads in Quezon City included Araneta E. Rodriguez northbound and southbound, "
            "EDSA White Plains northbound, and Quezon Avenue near Capitol Medical Center, "
            "all of which were not passable to light vehicles."
        ),
    )
    roads = [c for c in extract_taglish_flood_facts(inp).claims if c.place_type == "street"]
    assert len(roads) == 3
    assert all(c.canonical_city == "Quezon City" and c.road_passability == "light_vehicle_closed" for c in roads)
    assert any(c.raw_place_name == "Araneta E. Rodriguez" and "southbound" in c.road_segment_raw for c in roads)
    assert any(c.raw_place_name == "EDSA" and "White Plains" in c.road_segment_raw for c in roads)
    assert any(c.raw_place_name == "Quezon Avenue" and c.local_area_raw == "Capitol Medical Center" for c in roads)


def test_advisory_keeps_reported_travel_direction():
    inp = NewsArticleExtractorInput(
        article_id=118,
        canonical_url="https://example.com/directions",
        publisher="Test News",
        title="Quezon City flooding",
        article_text=(
            "In Quezon City, A. Bonifacio Cloverleaf northbound and southbound were flooded at 26 inches.\n"
            "G. Araneta cor. Baloy (Southbound) had gutter-deep flooding."
        ),
    )
    claims = extract_taglish_flood_facts(inp).claims
    cloverleaf = next(c for c in claims if c.raw_place_name == "A. Bonifacio Cloverleaf")
    araneta = next(c for c in claims if c.raw_place_name == "G. Araneta")
    assert "northbound and southbound" in cloverleaf.road_segment_raw
    assert "Southbound" in araneta.road_segment_raw


def test_advisory_bullet_times_and_landmarks_stay_on_the_main_road():
    inp = NewsArticleExtractorInput(
        article_id=117,
        canonical_url="https://example.com/timed-list",
        publisher="Test News",
        title="NCR flood advisory",
        article_text=(
            "Flooding was reported as of 6:37 p.m. -- all passable:\n"
            "Manila\n"
            "-- 6:10 p.m. Roxas Blvd. Pedro Gil. Svc. Rd.\n"
            "-- 6:20 p.m. Roxas Blvd. US Embassy\n"
            "-- 4:23 p.m. Roxas Blvd Pedro Gil Service Road\n"
            "-- Taft Ave. - Quirino Ave., Malate; gutter-deep (8 inches)\n"
            "Parañaque City\n"
            "-- Dr. A Santos Ave. NB - Para\u00f1aque National High School (8 inches)\n"
            "-- 3 p.m. Dr A. Santos Ave.-KayTalices (8 inches)\n"
            "Malabon City\n"
            "-- 3:14 p.m. Gov. Pascual Ave. (Sitio 6) (4 inches) - subsided as of 4:40 p.m."
        ),
    )
    claims = extract_taglish_flood_facts(inp).claims
    roads = [c for c in claims if c.place_type == "street"]
    first = next(c for c in roads if c.event_time_raw == "6:10 p.m")
    embassy = next(c for c in roads if c.local_area_raw == "US Embassy")
    school_city = next(c for c in roads if c.local_area_raw == "KayTalices")
    malabon = next(c for c in roads if c.raw_place_name == "Gov. Pascual Ave")
    assert "Svc" in first.road_segment_raw
    assert first.event_time_kind == "report"
    assert first.condition == "active"
    assert embassy.event_time_raw == "6:20 p.m"
    service_road = next(c for c in roads if c.event_time_raw == "4:23 p.m")
    assert service_road.raw_place_name == "Roxas Blvd"
    assert service_road.local_area_raw == "Pedro Gil Service Road"
    assert school_city.canonical_city == "City of Parañaque"
    assert school_city.depth_raw == "8 inches"
    assert any(c.raw_place_name == "Taft Ave" and "Quirino Ave" in (c.road_segment_raw or "") for c in roads)
    assert any(c.raw_place_name == "Dr. A Santos Ave" and "National High School" in (c.road_segment_raw or "") for c in roads)
    assert malabon.local_area_raw == "Sitio 6"
    assert malabon.condition == "subsided"
    assert malabon.event_time_raw == "as of 4:40 p.m."
    assert not any(c.raw_place_name in {"Svc. Rd", "Sitio 6"} for c in claims)


def test_photo_caption_is_review_only_and_weather_places_are_skipped():
    inp = NewsArticleExtractorInput(
        article_id=119,
        canonical_url="https://example.com/caption",
        publisher="Test News",
        title="NCR flood list",
        article_text=(
            "Floodwaters affected UN Avenue corner Taft Avenue in Manila.\n"
            "The Philippine STAR/Edd Gumban\n"
            "MANILA, Philippines — Flooding was reported in Metro Manila.\n"
            "PAGASA declared an orange rainfall warning in Valenzuela and Malabon.\n"
            "Quezon City\n"
            "-- NS Amoranto cor Don Jose St. - 37 inches, waist deep"
        ),
    )
    claims = extract_taglish_flood_facts(inp).claims
    assert len([c for c in claims if c.place_type == "street"]) == 2
    caption = next(c for c in claims if c.raw_place_name == "UN Avenue")
    assert "photo_caption_only" in caption.uncertainty_reasons
    assert not any(c.raw_place_name in {"Valenzuela", "Malabon", "MANILA"} for c in claims)
    assert any(c.raw_place_name == "NS Amoranto" and c.canonical_city == "Quezon City" for c in claims)


def test_long_pna_photo_caption_before_dateline_is_review_only():
    inp = NewsArticleExtractorInput(
        article_id=121,
        canonical_url="https://example.com/long-caption",
        publisher="Test News",
        title="Metro Manila flood report",
        article_text=(
            "Flooded roads. Riders cross flooded EDSA-Kamuning during heavy rain. "
            + ("The image shows rainfall across the region. " * 12)
            + "(PNA photo by Test Photographer)\n"
            "MANILA – Flooding was reported across Metro Manila.\n"
            "Quezon City\n"
            "-- Araneta Avenue corner Maria Clara was flooded at 26 inches."
        ),
    )
    claims = extract_taglish_flood_facts(inp).claims
    caption = next(c for c in claims if c.raw_place_name == "EDSA")
    assert "photo_caption_only" in caption.uncertainty_reasons
    assert any(c.raw_place_name == "Araneta Avenue" for c in claims)


def test_later_subsidence_flags_only_the_same_bounded_road_section():
    inp = NewsArticleExtractorInput(
        article_id=120,
        canonical_url="https://example.com/update",
        publisher="Test News",
        title="NCR flooding",
        article_text=(
            "In Quezon City, Araneta Avenue corner Maria Clara was flooded at 24 inches.\n"
            "Araneta Avenue corner Florentino was also flooded at 19 inches.\n"
            "Later, flooding at Araneta Avenue corner Maria Clara had subsided."
        ),
    )
    roads = [c for c in extract_taglish_flood_facts(inp).claims if c.raw_place_name == "Araneta Avenue"]
    maria = [c for c in roads if "Maria Clara" in (c.road_segment_raw or "")]
    florentino = next(c for c in roads if "Florentino" in (c.road_segment_raw or ""))
    assert len(maria) == 2
    assert all("contradictory_update" in c.uncertainty_reasons for c in maria)
    assert "contradictory_update" not in florentino.uncertainty_reasons


def test_multi_city_report_keeps_each_road_closure_and_time_local():
    inp = NewsArticleExtractorInput(
        article_id=122,
        canonical_url="https://example.com/multi-city-report",
        publisher="Test News",
        title="Floods in Metro Manila",
        article_text=(
            "Quezon City\n"
            "In Quezon City, waist-deep flooding on Sto. Domingo Avenue between Atok and Calamba Streets "
            "made the area no longer passable to vehicles as of 1:12 p.m.\n"
            "Regalado Highway in Barangay North Fairview was not passable to small vehicles "
            "due to flooding as of 12:24 p.m.\n"
            "Commonwealth Avenue had zero visibility due to heavy rain.\n"
            "Parañaque City\n"
            "In San Antonio Valley 2 in Barangay San Isidro, Parañaque City, "
            "the flood exceeded a man's height on Saturday morning.\n"
            "Manila\n"
            "Gutter-deep flooding was reported on Antipolo Street corner Jose Abad Santos Street "
            "in Tondo as of 12:44 p.m.\n"
            "Courtesy: Manila Public Information Office.\n"
            "Las Piñas City\n"
            "Pumps drained flooding at Zapote Junction and Alido Bridge on Saturday morning."
        ),
    )
    claims = extract_taglish_flood_facts(inp).claims
    sto_domingo = next(c for c in claims if c.raw_place_name == "Sto. Domingo Avenue")
    regalado = next(c for c in claims if c.raw_place_name == "Regalado Highway")
    valley = next(c for c in claims if c.raw_place_name == "San Antonio Valley 2")
    san_isidro = next(c for c in claims if c.raw_place_name == "Barangay San Isidro")
    antipolo = next(c for c in claims if c.raw_place_name == "Antipolo Street")
    zapote = next(c for c in claims if c.raw_place_name == "Zapote Junction")
    alido = next(c for c in claims if c.raw_place_name == "Alido Bridge")
    assert sto_domingo.road_passability == "impassable_all"
    assert regalado.road_passability == "light_vehicle_closed"
    assert valley.depth_canonical is None and "ambiguous_depth" in valley.uncertainty_reasons
    assert san_isidro.depth_raw != "2 in"
    assert san_isidro.event_time_raw is None
    assert antipolo.event_time_raw == "as of 12:44 p.m."
    assert not any(c.raw_place_name == "Commonwealth Avenue" for c in claims)
    assert not any(c.evidence_sentence.startswith("Courtesy:") for c in claims)
    assert zapote.canonical_city == alido.canonical_city == "City of Las Piñas"
    assert all(c.event_time_raw != "as of 12:44 p.m." for c in claims if "Zapote" in c.evidence_sentence)


def test_multi_city_sentence_assigns_each_location_its_local_city():
    inp = NewsArticleExtractorInput(
        article_id=129,
        canonical_url="https://example.com/multi-city-sites",
        publisher="Test News",
        title="Metro Manila flooding",
        article_text=(
            "Floodwaters hit Barangay Plainview, Mandaluyong City, and "
            "Caruncho Avenue, Pasig City."
        ),
    )

    claims = extract_taglish_flood_facts(inp).claims
    plainview = next(c for c in claims if c.raw_place_name == "Barangay Plainview")
    caruncho = next(c for c in claims if c.raw_place_name == "Caruncho Avenue")

    assert plainview.canonical_city == "City of Mandaluyong"
    assert caruncho.canonical_city == "City of Pasig"
    assert "city_context_ambiguous" not in caruncho.uncertainty_reasons


def test_multi_city_landmark_keeps_its_city_and_barangay_scope():
    inp = NewsArticleExtractorInput(
        article_id=130,
        canonical_url="https://example.com/multi-city-landmark",
        publisher="Test News",
        title="Metro Manila flooding",
        article_text=(
            "Floodwaters reached Maysilo Circle, Barangay Plainview, Mandaluyong City, "
            "as well as Caruncho Avenue, Pasig City."
        ),
    )

    claims = extract_taglish_flood_facts(inp).claims
    maysilo = next(c for c in claims if c.raw_place_name == "Maysilo Circle")
    caruncho = next(c for c in claims if c.raw_place_name == "Caruncho Avenue")

    assert maysilo.place_type == "landmark"
    assert maysilo.canonical_city == "City of Mandaluyong"
    assert maysilo.canonical_barangay == "Plainview"
    assert caruncho.canonical_city == "City of Pasig"
    assert caruncho.canonical_barangay is None


def test_newest_first_clearing_update_flags_the_older_same_section_only():
    inp = NewsArticleExtractorInput(
        article_id=123,
        canonical_url="https://example.com/latest-first",
        publisher="Test News",
        title="Manila flood updates",
        article_text=(
            "Manila\n"
            "Along Taft Avenue from Pedro Gil was subsided as of 4 p.m.\n"
            "Earlier, Along Taft Avenue from Pedro Gil was flooded.\n"
            "Taft Avenue corner Quirino Avenue was also flooded."
        ),
    )
    roads = [c for c in extract_taglish_flood_facts(inp).claims if c.place_type == "street"]
    pedro_gil = [c for c in roads if "Pedro Gil" in (c.road_segment_raw or "")]
    quirino = next(c for c in roads if "Quirino" in (c.road_segment_raw or ""))
    assert len(pedro_gil) == 2
    assert all("contradictory_update" in c.uncertainty_reasons for c in pedro_gil)
    assert "contradictory_update" not in quirino.uncertainty_reasons


def test_agency_status_list_keeps_road_names_out_of_city_matching():
    inp = NewsArticleExtractorInput(
        article_id=124,
        canonical_url="https://example.com/agency-status-list",
        publisher="Test News",
        title="Metro Manila flood road status",
        article_text=(
            "The agency released the following road status update as of 4:35 p.m.:\n"
            "Manila City\n"
            "Espana Antipolo to Quintos (eastbound/westbound) - subsided as of 3:20 p.m.\n"
            "Quezon City\n"
            "Along Araneta between Quezon Ave. and E. Rodriguez - gutter deep; passable to all vehicles\n"
            "Araneta E. Rodriguez (southbound/northbound) - gutter deep; passable to all vehicles\n"
            "EDSA Aurora Tunnel (northbound/southbound) - gutter deep; passable to all vehicles\n"
            "As of 2:16 p.m., flooding along EDSA-Santolan was reported."
        ),
    )
    claims = extract_taglish_flood_facts(inp).claims
    roads = [c for c in claims if c.place_type == "street"]
    assert any(c.raw_place_name.startswith("Espana Antipolo") and c.canonical_city == "City of Manila" for c in roads)
    assert any(c.raw_place_name.startswith("Araneta between") and c.canonical_city == "Quezon City" for c in roads)
    assert any(c.raw_place_name.startswith("Araneta E. Rodriguez") and c.canonical_city == "Quezon City" for c in roads)
    aurora = next(c for c in roads if c.raw_place_name == "EDSA" and "Aurora Tunnel" in (c.road_segment_raw or ""))
    assert aurora.event_time_raw == "as of 4:35 p.m."
    assert any(c.raw_place_name == "EDSA" and c.canonical_city is None for c in roads)
    assert not any(c.canonical_city in {"City of Antipolo", "Rodriguez"} for c in claims)


def test_accented_publisher_spelling_connects_only_the_same_cleared_site():
    inp = NewsArticleExtractorInput(
        article_id=125,
        canonical_url="https://example.com/damaged-spelling",
        publisher="Test News",
        title="Manila flood road status",
        article_text=(
            "Manila City\n"
            "Espa\u00f1a Maceda - subsided as of 3:24 p.m.\n"
            "Earlier, the following areas were flooded:\n"
            "Manila City\n"
            "Espana Maceda - gutter deep; passable to all vehicles\n"
            "Espana Antipolo - gutter deep; passable to all vehicles"
        ),
    )
    claims = extract_taglish_flood_facts(inp).claims
    maceda = [c for c in claims if "Maceda" in c.raw_place_name]
    antipolo = next(c for c in claims if "Antipolo" in c.raw_place_name)
    assert len(maceda) == 2
    assert all("contradictory_update" in c.uncertainty_reasons for c in maceda)
    assert "contradictory_update" not in antipolo.uncertainty_reasons


def test_earlier_advisory_with_recorded_flood_is_an_observation():
    inp = NewsArticleExtractorInput(
        article_id=126,
        canonical_url="https://example.com/earlier-advisory",
        publisher="Test News",
        title="Metro Manila flood report",
        article_text=(
            "In an earlier advisory around 1 p.m., gutter-deep flooding was also recorded "
            "at EDSA Shaw Tunnel in Mandaluyong City."
        ),
    )
    edsa = next(c for c in extract_taglish_flood_facts(inp).claims if c.raw_place_name == "EDSA")
    assert edsa.condition == "active"
    assert not edsa.is_forecast
    assert edsa.canonical_city == "City of Mandaluyong"


def test_maynila_caption_keeps_cross_street_in_city_of_manila():
    inp = NewsArticleExtractorInput(
        article_id=127,
        canonical_url="https://example.com/manila-caption",
        publisher="Test News",
        title="Metro Manila flood report",
        article_text=(
            "Manila\n"
            "As of 12:44 PM, gutter-deep ang baha sa Antipolo St. cor. Jose Abad Santos St. "
            "sa Tondo, Maynila ngayong Sabado."
        ),
    )
    claims = extract_taglish_flood_facts(inp).claims
    road = next(c for c in claims if c.raw_place_name == "Antipolo St.")
    assert road.canonical_city == "City of Manila"
    assert "Jose Abad Santos St." in (road.road_segment_raw or "")
    assert not any(c.canonical_city == "Jose Abad Santos" for c in claims)


