"""Paraphrased September 9 source relationships and conservative evidence guards."""
from datetime import datetime

import pytest

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_presentation_service import claim_reading_reason
from app.services.taglish_extraction_service import extract_taglish_flood_facts


GMA_URL = "https://www.gmanetwork.com/news/topstories/metro/1001693/story/"


def extract(body: str, publication: str = "2026-09-09T17:03:00+08:00", url: str = "https://example.org/september9"):
    article = NewsArticleExtractorInput(
        article_id=-9, canonical_url=url,
        publisher="Paraphrased source fixture", title="Metro Manila flood report",
        article_text=body, published_at=datetime.fromisoformat(publication),
    )
    result = extract_taglish_flood_facts(article)
    for claim in result.claims:
        start, end = claim.evidence_sentence_offset
        assert body[start:end] == claim.evidence_sentence
        assert body[claim.place_char_start:claim.place_char_end] == claim.raw_place_name
    return article, result.claims


def test_explicit_gma_list_passability_and_city_validated_barangays():
    body = (
        "By GMA News Published September 9, 2026 9:19am\n"
        "Updated September 9, 2026 3:09pm\n"
        "Below is a list of flooded roads confirmed by local offices:\n"
        "Malabon City\n"
        "Rizal Ave Extn Brgy San Agustin - Gutter deep, Passable to all type of Vehicles as of 2:47 p.m.\n"
        "Tañong F. Sevilla Blvd. (Bayan) - Gutter deep, Passable to all type of Vehicles as of 2:47 p.m.\n"
        "Marikina City\n"
        "Marcos Highway Underloop - Gutter deep, Passable to all type of Vehicles as of 2:47 p.m."
    )
    publication = "2026-09-09T09:19:06+08:00"
    article, claims = extract(body, publication, GMA_URL)
    roads = [c for c in claims if c.canonical_road and claim_reading_reason(c) is None]
    assert len(roads) == 3
    assert [(c.canonical_road, c.canonical_barangay) for c in roads] == [
        ("Rizal Ave", "San Agustin"), ("F. Sevilla Blvd", "Tañong"), ("Marcos Highway", None),
    ]
    assert [c.canonical_city for c in roads] == ["City of Malabon", "City of Malabon", "City of Marikina"]
    assert all(c.depth_canonical == "gutter" and c.road_passability == "passable_all" for c in roads)
    assert all(c.event_time_resolved == datetime.fromisoformat("2026-09-09T14:47:00+08:00") for c in roads)
    assert article.published_at == datetime.fromisoformat(publication)


def test_coordinated_body_streets_and_unknown_facts():
    _, claims = extract(
        "España Boulevard, Blumentritt and other streets in Manila were flooded.\n"
        "N.S. Amoranto in Quezon City was also flooded."
    )
    roads = [c for c in claims if c.canonical_road and claim_reading_reason(c) is None]
    assert {c.canonical_road for c in roads} == {"España Boulevard", "Blumentritt", "N.S. Amoranto"}
    assert {c.canonical_city for c in roads if c.canonical_road != "N.S. Amoranto"} == {"City of Manila"}
    assert all(c.event_time_resolved is None and c.depth_raw is None and c.road_passability == "unknown" for c in roads)


def test_depthless_list_row_keeps_contiguous_scoped_evidence_and_own_facts():
    body = (
        "As of 4:30 p.m., agencies confirmed the following routes and areas affected by flooding:\n"
        "Passable with caution\nQuezon City\nBrgy. Dona Imelda\n"
        "Guirayan cor Baloy - 9 inches, ankle deep\n"
        "G. Araneta cor. Baloy (Southbound)"
    )
    _, claims = extract(body)
    road = next(c for c in claims if c.raw_place_name == "G. Araneta")
    assert claim_reading_reason(road) is None
    assert road.depth_raw is None  # Never borrow the prior row's measurement.
    assert road.road_passability == "passable_with_caution"
    assert road.canonical_barangay == "Doña Imelda"
    assert road.event_time_resolved == datetime.fromisoformat("2026-09-09T16:30:00+08:00")
    assert road.evidence_sentence == body
    assert "scoped_flood_list_evidence" in road.uncertainty_reasons


@pytest.mark.parametrize("intro", [
    "The following routes and areas may be affected by flooding:",
    "The following routes and areas were not affected by flooding:",
    "The following routes are used for flood prevention projects:",
    "The following routes are open (flooding was reported somewhere else):",
])
def test_unobserved_lists_cannot_admit_a_depthless_road(intro: str):
    _, claims = extract(f"{intro}\nQuezon City\nG. Araneta cor. Baloy (Southbound)")
    assert all(claim_reading_reason(c) is not None for c in claims)


@pytest.mark.parametrize("header", [
    "", "Updated September 9, 2026 8:00am\n",
    "Updated September 10, 2026 3:09pm\n",
    "Updated September 8, 2026 3:09pm\n",
    "Updated September 9, 2026 3:09pm\nUpdated September 9, 2026 3:10pm\n",
    "Updated September 9, 2026 25:09pm\n",
])
def test_invalid_update_headers_leave_later_clock_unresolved(header: str):
    _, claims = extract("By GMA News Published September 9, 2026 9:19am\n" + header
                        + "Marcos Highway in Marikina City was flooded as of 2:47 p.m.",
                        "2026-09-09T09:19:06+08:00", GMA_URL)
    road = next(c for c in claims if c.canonical_road == "Marcos Highway")
    assert road.event_time_raw == "as of 2:47 p.m."
    assert road.event_time_resolved is None


def test_update_header_does_not_resolve_a_future_observation_clock():
    _, claims = extract("By GMA News Published September 9, 2026 9:19am\n"
                        "Updated September 9, 2026 3:09pm\n"
                        "Marcos Highway in Marikina City was flooded as of 4:47 p.m.",
                        "2026-09-09T09:19:06+08:00", GMA_URL)
    road = next(c for c in claims if c.canonical_road == "Marcos Highway")
    assert road.event_time_resolved is None


def test_a_barangay_homonym_does_not_strip_aurora_road_name():
    _, claims = extract("Aurora Boulevard at Araneta Avenue in Quezon City was flooded.")
    assert any(c.canonical_road == "Aurora Boulevard" for c in claims)


def test_disqualified_row_interrupts_contiguous_list_evidence():
    _, claims = extract("As of 4:30 p.m., the following roads were flooded:\n"
                        "Pasig City\nOrtigas Avenue - water may rise\n"
                        "Shaw Boulevard - passable to all vehicles")
    road = next(c for c in claims if c.canonical_road == "Shaw Boulevard")
    assert claim_reading_reason(road) is not None
    assert "scoped_flood_list_evidence" not in road.uncertainty_reasons


@pytest.mark.parametrize("url, header", [
    ("https://example.org/news", "By GMA News Published September 9, 2026 9:19am\n"),
    ("https://www.gmanetwork.com.example.org/news", "By GMA News Published September 9, 2026 9:19am\n"),
    (GMA_URL, "By GMA News Published September 9, 2026 8:19am\n"),
    (GMA_URL, "A witness sent a later narrative statement.\n"),
])
def test_update_anchor_requires_gma_host_and_matching_original_header(url: str, header: str):
    _, claims = extract(header + "Updated September 9, 2026 3:09pm\n"
                        "Marcos Highway in Marikina City was flooded as of 2:47 p.m.",
                        "2026-09-09T09:19:06+08:00", url)
    road = next(c for c in claims if c.canonical_road == "Marcos Highway")
    assert road.event_time_raw == "as of 2:47 p.m."
    assert road.event_time_resolved is None


@pytest.mark.parametrize("intro", [
    "The following roads may be flooded:",
    "The following roads were flooded (in a drill):",
    "The following roads were not flooded:",
    "The following routes and areas were not affected by flooding:",
    "The following roads were flooded in 2020:",
    "The following roads are used for flood prevention projects:",
])
def test_measured_rows_retain_non_observation_list_context(intro: str):
    _, claims = extract(f"{intro}\nPasig City\nOrtigas Avenue - knee deep")
    road = next(c for c in claims if c.canonical_road == "Ortigas Avenue")
    assert road.depth_raw == "knee deep"
    assert road.depth_canonical == "knee"
    assert not road.flood_mentioned
    assert road.event_time_resolved is None
    assert claim_reading_reason(road) is not None
    assert "non_observation_list_context" in road.uncertainty_reasons


@pytest.mark.parametrize("boundary", [
    "Classes were suspended.\nShaw Boulevard in Mandaluyong City was flooded at gutter level.",
    "The following roads were flooded:\nMandaluyong City\nShaw Boulevard - gutter deep",
])
def test_non_observation_list_scope_resets_for_independent_observation(boundary: str):
    _, claims = extract("The following roads may be flooded:\nPasig City\nOrtigas Avenue - knee deep\n" + boundary)
    ortigas = next(c for c in claims if c.canonical_road == "Ortigas Avenue")
    shaw = next(c for c in claims if c.canonical_road == "Shaw Boulevard")
    assert claim_reading_reason(ortigas) is not None
    assert claim_reading_reason(shaw) is None
    assert shaw.flood_mentioned and not shaw.is_forecast and not shaw.is_historical and not shaw.is_negated


@pytest.mark.parametrize("intro, observed", [
    ("As of 2:47 p.m., the following roads were flooded:", True),
    ("As of 2:47 p.m., the following roads may be flooded:", False),
])
def test_short_independent_narrative_ends_telegraphic_list_scope(intro: str, observed: bool):
    _, claims = extract(f"{intro}\nPasig City\nOrtigas Avenue - knee deep\n"
                        "Shaw Boulevard in Mandaluyong City was flooded at knee level.")
    ortigas = next(c for c in claims if c.canonical_road == "Ortigas Avenue")
    shaw = next(c for c in claims if c.canonical_road == "Shaw Boulevard")
    assert (claim_reading_reason(ortigas) is None) == observed
    assert claim_reading_reason(shaw) is None
    assert shaw.canonical_city == "City of Mandaluyong"
    assert shaw.event_time_raw is None and shaw.event_time_resolved is None
    assert not shaw.is_forecast and not shaw.is_historical and not shaw.is_negated


def test_bare_flooded_verb_ends_list_clock_scope():
    _, claims = extract("As of 2:47 p.m., the following roads were flooded:\n"
                        "Pasig City\nOrtigas Avenue - knee deep\n"
                        "Shaw Boulevard in Mandaluyong City flooded at waist level.")
    shaw = next(c for c in claims if c.canonical_road == "Shaw Boulevard")
    assert shaw.event_time_raw is None and shaw.event_time_resolved is None


@pytest.mark.parametrize("body, expected_depth, expected_clock", [
    ("Ortigas Avenue in Pasig City was flooded at knee level and Shaw Boulevard in Mandaluyong City was flooded at waist level.",
     ("knee", "waist"), (None, None)),
    ("Ortigas Avenue in Pasig City was flooded as of 2:00 p.m. and Shaw Boulevard in Mandaluyong City was flooded as of 3:00 p.m.",
     (None, None), ("14:00", "15:00")),
    ("Ortigas Avenue in Pasig City was flooded as of 2:00 p.m. and Shaw Boulevard in Mandaluyong City was flooded at waist level.",
     (None, "waist"), ("14:00", None)),
])
def test_independent_road_predicates_joined_by_and_keep_separate_facts(body, expected_depth, expected_clock):
    _, claims = extract(body)
    roads = [next(c for c in claims if c.canonical_road == road) for road in ("Ortigas Avenue", "Shaw Boulevard")]
    assert [c.canonical_city for c in roads] == ["City of Pasig", "City of Mandaluyong"]
    for claim, depth, clock in zip(roads, expected_depth, expected_clock):
        assert claim.depth_canonical == depth
        assert claim.event_time_resolved == (datetime.fromisoformat(f"2026-09-09T{clock}:00+08:00") if clock else None)


def test_shared_road_subjects_joined_by_and_keep_shared_facts():
    _, claims = extract("Ortigas Avenue and Shaw Boulevard in Pasig City were flooded at knee level as of 2:00 p.m.")
    roads = [c for c in claims if c.canonical_road]
    assert {c.canonical_road for c in roads} == {"Ortigas Avenue", "Shaw Boulevard"}
    assert all(c.depth_canonical == "knee" and c.event_time_resolved == datetime.fromisoformat("2026-09-09T14:00:00+08:00") for c in roads)


@pytest.mark.parametrize("qualifier", ["remained passable with caution", "was flooded in northbound and southbound lanes"])
def test_independent_and_split_preserves_previous_roads_conjoined_qualifier(qualifier: str):
    _, claims = extract("Ortigas Avenue in Pasig City was flooded at knee level and " + qualifier +
                        " and Shaw Boulevard in Mandaluyong City was flooded at waist level.")
    ortigas = next(c for c in claims if c.canonical_road == "Ortigas Avenue")
    shaw = next(c for c in claims if c.canonical_road == "Shaw Boulevard")
    assert ortigas.depth_canonical == "knee" and shaw.depth_canonical == "waist"
    assert ortigas.road_passability == ("passable_with_caution" if "caution" in qualifier else "unknown")
    assert shaw.road_passability == "unknown"


def test_three_independent_roads_joined_by_and_keep_their_own_facts():
    _, claims = extract("Ortigas Avenue in Pasig City was flooded at knee level and "
                        "Shaw Boulevard in Mandaluyong City was flooded at waist level and "
                        "Taft Avenue in Manila was flooded at gutter level.")
    roads = {c.canonical_road: c for c in claims if c.canonical_road}
    assert {r:c.depth_canonical for r,c in roads.items()} == {"Ortigas Avenue":"knee", "Shaw Boulevard":"waist", "Taft Avenue":"gutter"}
