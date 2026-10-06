"""Article and Pasig history must ground to the same bounded road section."""

from pathlib import Path

from shapely.geometry import Polygon

from app.schemas.news_extraction import ExtractedClaim
from app.services.article_road_context_service import match_article_road_context
from app.services.article_road_match_service import OSMRoadSection


HISTORY_CSV = Path(__file__).parent / "fixtures" / "pasig_context_rows.csv"
REAL_PASIG_CSV = Path(__file__).resolve().parents[2] / "data" / "flooded_areas_pasig_clean.csv"
CITY = Polygon([(120.99, 14.49), (121.01, 14.49), (121.01, 14.51), (120.99, 14.51)])


def claim(*, city: str = "Pasig", local: str | None = None,
          span: str | None = None, barangay: str | None = None) -> ExtractedClaim:
    return ExtractedClaim(
        raw_place_name="C. Raymundo Avenue", canonical_road="C. Raymundo Avenue",
        canonical_city=city, canonical_barangay=barangay, local_area_raw=local,
        road_segment_raw=span, place_char_start=0, place_char_end=18,
        evidence_sentence="Flooding on C. Raymundo Avenue", evidence_sentence_offset=(0, 30),
    )


def sections() -> list[OSMRoadSection]:
    return [OSMRoadSection(
        section_id="bernal-west", road_name="C. Raymundo Avenue",
        centerline_geojson={"type": "LineString", "coordinates": [[121.0, 14.5], [121.001, 14.5]]},
        osm_way_ids=(1,), end_cross_streets=(("Ortigas Avenue",), ("Bernal Street",)),
        source_id="test-osm",
    ), OSMRoadSection(
        section_id="bernal-east", road_name="C. Raymundo Avenue",
        centerline_geojson={"type": "LineString", "coordinates": [[121.001, 14.5], [121.002, 14.5]]},
        osm_way_ids=(2,), end_cross_streets=(("Bernal Street",), ("E. Santos Street",)),
        source_id="test-osm",
    ), OSMRoadSection(
        section_id="mercedes", road_name="C. Raymundo Avenue",
        centerline_geojson={"type": "LineString", "coordinates": [[121.002, 14.5], [121.003, 14.5]]},
        osm_way_ids=(3,), end_cross_streets=(("E. Santos Street",), ("Mercedes Avenue",)),
        source_id="test-osm",
    )]


def test_pasig_crossing_uses_only_matching_drrmo_place_rows() -> None:
    result = match_article_road_context(claim(local="near Bernal Street"), sections(), CITY, HISTORY_CSV)
    assert result.candidate_section_ids == ("bernal-west", "bernal-east")
    assert result.article_place_levels == {"bernal-west": 2, "bernal-east": 2}
    assert [row.source_record_no for row in result.historical_rows_by_section["bernal-west"]] == ["1"]
    assert [row.source_record_no for row in result.historical_rows_by_section["bernal-east"]] == ["1"]
    assert "3" in {row.source_record_no for row in result.unmatched_history_rows}


def test_non_pasig_article_never_uses_pasig_history() -> None:
    result = match_article_road_context(claim(city="Quezon City", local="near Bernal Street"),
                                        sections(), CITY, HISTORY_CSV)
    assert result.candidate_section_ids == ("bernal-west", "bernal-east")
    assert all(not rows for rows in result.historical_rows_by_section.values())


def test_actual_pasig_bernal_rows_ground_to_both_adjacent_sections() -> None:
    result = match_article_road_context(claim(local="near Bernal Street"), sections(), CITY, REAL_PASIG_CSV)
    for section_id in ("bernal-west", "bernal-east"):
        assert len(result.historical_rows_by_section[section_id]) == 3
        assert {row.barangay for row in result.historical_rows_by_section[section_id]} == {"Rosario"}


def test_explicit_span_requires_both_cross_streets_and_does_not_fall_back_to_hazard() -> None:
    matched = match_article_road_context(
        claim(span="between Ortigas Avenue and Bernal Street"), sections(), CITY)
    assert matched.candidate_section_ids == ("bernal-west",)
    assert matched.article_place_levels == {"bernal-west": 3}
    missing = match_article_road_context(
        claim(span="between Ortigas Avenue and Mercedes Avenue"), sections(), CITY)
    assert missing.candidate_section_ids == ()
    assert missing.reason == "reported_span_not_grounded"


def test_barangay_clue_requires_supplied_boundary_for_section_selection() -> None:
    no_boundary = match_article_road_context(claim(barangay="Rosario"), sections(), CITY)
    assert len(no_boundary.candidate_section_ids) == 3
    boundary = Polygon([(120.999, 14.499), (121.0011, 14.499),
                        (121.0011, 14.501), (120.999, 14.501)])
    with_boundary = match_article_road_context(
        claim(barangay="Rosario"), sections(), CITY, barangay_boundary=boundary)
    assert with_boundary.candidate_section_ids == ("bernal-west",)
    assert with_boundary.article_place_levels == {"bernal-west": 1}


def test_checked_city_boundary_excludes_outside_sections() -> None:
    narrow_city = Polygon([(120.999, 14.499), (121.0011, 14.499),
                           (121.0011, 14.501), (120.999, 14.501)])
    result = match_article_road_context(claim(), sections(), narrow_city)
    assert result.candidate_section_ids == ("bernal-west",)
