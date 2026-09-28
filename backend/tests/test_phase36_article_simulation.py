"""Offline acceptance checks for the three full-article news simulations."""

import json

from scripts.simulate_phase36_articles import EXPECTED_SITES_PATH, evaluate_expected_sites


def test_expected_site_inventory_has_each_article():
    """The live simulation has an explicit inventory for each selected article."""
    fixture = json.loads(EXPECTED_SITES_PATH.read_text(encoding="utf-8"))

    assert {case_id: len(case["sites"]) for case_id, case in fixture.items()} == {
        "philstar-sep-09": 27,
        "pna-aug-17": 16,
        "pna-aug-08": 8,
    }


def test_expected_site_rejects_wrong_city_or_depth():
    expected = {"sample": {"sites": [{"location": "Calamba Street", "city": "Quezon City", "depth_raw": "37 inches"}]}}
    result = [{"id": "sample", "claims": [{"road_segment": "Calamba St.", "city": "City of Calamba", "depth_raw": "19 inches"}]}]

    assert not evaluate_expected_sites(result, expected)
    assert result[0]["matched_site_count"] == 0
    assert result[0]["missing_sites"][0]["location"] == "Calamba Street"


def test_expected_sites_require_distinct_claims():
    expected = {"sample": {"sites": [{"location": "Flood Road"}, {"location": "Flood Road"}]}}
    result = [{"id": "sample", "claims": [{"road_segment": "Flood Road"}]}]

    assert not evaluate_expected_sites(result, expected)
    assert result[0]["matched_site_count"] == 1
