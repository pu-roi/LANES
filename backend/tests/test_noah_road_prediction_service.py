"""NOAH overlap ranks bounded sections without implying current flood certainty."""

from pathlib import Path

import pytest
from shapely.geometry import LineString

from app.services.noah_road_prediction_service import (
    RoadSectionEvidence,
    rank_noah_road_sections,
)


ARCHIVES = {5: Path("5.zip"), 25: Path("25.zip"), 100: Path("100.zip")}


def section(section_id: str, x: float, *, article_level: int = 0,
            history_rows: int = 0, bounded: bool = True) -> RoadSectionEvidence:
    return RoadSectionEvidence(
        section_id=section_id, metric_centerline=LineString([(x, 0), (x + 100, 0)]),
        osm_source_id="metro-manila-osm-test", article_place_level=article_level,
        matching_drrmo_rows=history_rows, bounded_road_section=bounded,
    )


def overlap(path: Path, line: LineString) -> dict[int, float]:
    # Each section is the same length; modeled coverage differs.
    covered = 80.0 if line.bounds[0] == 0 else 20.0
    return {1: covered, 2: 0.0, 3: 0.0}


def test_noah_can_rank_one_bounded_section_of_a_long_named_road() -> None:
    result = rank_noah_road_sections(
        [section("near-Bernal", 0), section("near-Mercedes", 200)], ARCHIVES, overlap,
    )
    assert result.predicted_section_id == "near-Bernal"
    assert result.reason == "unique_ranked_prediction_not_verified_flood_extent"
    assert [item.section_id for item in result.ranked_sections] == ["near-Bernal", "near-Mercedes"]
    assert result.ranked_sections[0].modeled_overlap_fraction == {5: 0.8, 25: 0.8, 100: 0.8}


def test_explicit_article_span_outweighs_hazard_only_section() -> None:
    result = rank_noah_road_sections(
        [section("reported-span", 200, article_level=3), section("hazard-heavy", 0)],
        ARCHIVES, overlap,
    )
    assert result.predicted_section_id == "reported-span"
    assert result.ranked_sections[0].modeled_overlap_fraction[5] == 0.2


def test_equal_support_and_arbitrary_windows_remain_unselected() -> None:
    equal = rank_noah_road_sections(
        [section("first", 0), section("second", 0)], ARCHIVES, overlap,
    )
    assert equal.predicted_section_id is None
    assert equal.reason == "multiple_equally_supported_sections"
    window = rank_noah_road_sections(
        [section("100m-junction-window", 0, bounded=False)], ARCHIVES, overlap,
    )
    assert window.predicted_section_id is None
    assert window.reason == "top_section_has_arbitrary_bounds"


def test_missing_or_inconsistent_hazard_source_fails_closed() -> None:
    with pytest.raises(ValueError, match="All three"):
        rank_noah_road_sections([section("one", 0)], {5: Path("5.zip")}, overlap)
    with pytest.raises(ValueError, match="exceed road length"):
        rank_noah_road_sections(
            [section("one", 0)], ARCHIVES,
            lambda path, line: {1: 80.0, 2: 80.0, 3: 0.0},
        )


def test_road_only_claim_without_noah_overlap_stays_unresolved() -> None:
    result = rank_noah_road_sections(
        [section("one", 0)], ARCHIVES,
        lambda path, line: {1: 0.0, 2: 0.0, 3: 0.0},
    )
    assert result.predicted_section_id is None
    assert result.reason == "no_modeled_overlap_or_explicit_span"


def test_higher_noah_class_breaks_equal_coverage_without_changing_reported_depth() -> None:
    def class_overlap(path: Path, line: LineString) -> dict[int, float]:
        return {1: 0.0, 2: 0.0, 3: 100.0} if line.bounds[0] == 0 else {
            1: 0.0, 2: 100.0, 3: 0.0,
        }

    result = rank_noah_road_sections(
        [section("modeled-high", 0), section("modeled-medium", 200)],
        ARCHIVES, class_overlap,
    )
    assert result.predicted_section_id == "modeled-high"
    assert result.ranked_sections[0].average_class_fraction[3] == 1.0
