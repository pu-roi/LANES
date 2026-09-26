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
        assert rule == "unsupported_or_ambiguous_scale"
        assert "ambiguous_depth" in reasons


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
