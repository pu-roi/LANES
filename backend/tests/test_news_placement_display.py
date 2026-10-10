"""One claim's drawing topology preserves alternatives and original evidence."""
import pytest
from shapely.geometry import LineString, MultiLineString, Point, mapping, shape

from app.schemas.news_placement import NewsPlacementPreview, PlacementSection
from app.services.news_placement_display_service import placement_display_sections, placement_display_zone, resolved_placement_display_zone


def candidate(identity: str, geometry: LineString | MultiLineString) -> PlacementSection:
    return PlacementSection(candidate_id=identity, kind="road_section", centerline_geojson=mapping(geometry),
                            preview_geometry=mapping(geometry), osm_way_ids=[], cross_streets=[],
                            ambiguous_carriageway=True, article_place_level=1, approximate_length_m=1)


def test_adjoining_sections_become_one_line_without_mutating_candidates():
    inputs = [candidate("a", LineString([(121, 14), (121.001, 14)])),
              candidate("b", LineString([(121.001, 14), (121.002, 14)]))]
    before = [item.model_dump() for item in inputs]
    result = placement_display_sections(inputs)
    assert len(result) == 1 and result[0].candidate_ids == ["a", "b"]
    assert shape(result[0].geometry).length == pytest.approx(.002)
    assert [item.model_dump() for item in inputs] == before


def test_repeated_and_reversed_coverage_is_drawn_once_with_all_identities():
    line = LineString([(121, 14), (121.001, 14), (121.002, 14)])
    result = placement_display_sections([candidate("a", line), candidate("b", LineString(list(line.coords)[::-1]))])
    assert len(result) == 1 and result[0].candidate_ids == ["a", "b"]
    assert shape(result[0].geometry).length == pytest.approx(line.length)


def test_parallel_carriageways_and_small_real_gap_remain_separate():
    first = MultiLineString([[(121, 14), (121.001, 14)], [(121.00100001, 14), (121.002, 14)]])
    second = LineString([(121, 14.0001), (121.002, 14.0001)])
    result = placement_display_sections([candidate("a", first), candidate("b", second)])
    assert len(result) == 3
    gap = Point(121.001000005, 14)
    assert all(not shape(item.geometry).covers(gap) for item in result)
    assert sorted(item.candidate_ids for item in result) == [["a"], ["a"], ["b"]]


def test_partial_coincident_coverage_is_not_repeated():
    result = placement_display_sections([candidate("a", LineString([(121, 14), (121.002, 14)])),
                                         candidate("b", LineString([(121.001, 14), (121.003, 14)]))])
    assert sum(shape(item.geometry).length for item in result) == pytest.approx(.003)
    assert result[0].candidate_ids == ["a", "b"]


def test_empty_modeled_geometry_produces_no_drawn_section():
    item = candidate("a", LineString([(121, 14), (121.001, 14)]))
    item.preview_geometry = None
    assert placement_display_sections([item]) == []


def test_two_layer_display_dissolves_parallel_halos_but_preserves_road_cores():
    from shapely.ops import unary_union
    from app.services.noah_vector_catalog_service import metric_geometry
    inputs = [candidate("a", LineString([(121, 14.58), (121.002, 14.58)])),
              candidate("b", LineString([(121, 14.58008), (121.002, 14.58008)]))]
    before = [item.model_dump() for item in inputs]
    sections = placement_display_sections(inputs)
    display = placement_display_zone(sections)
    core, halo = shape(display.core_geometry), shape(display.aura_geometry)
    assert core.geom_type == "MultiLineString" and len(core.geoms) == 2
    assert halo.geom_type == "Polygon" and halo.is_valid and halo.covers(core)
    expected = unary_union([metric_geometry(shape(item.geometry)).buffer(25) for item in sections])
    assert metric_geometry(halo).area == pytest.approx(expected.area)
    assert display.candidate_ids == ["a", "b"]
    assert [item.model_dump() for item in inputs] == before


def test_visual_halo_does_not_join_disconnected_road_cores():
    inputs = [candidate("a", MultiLineString([[(121, 14.58), (121.001, 14.58)],
                                              [(121.0011, 14.58), (121.002, 14.58)]]))]
    display = placement_display_zone(placement_display_sections(inputs))
    assert not shape(display.core_geometry).covers(Point(121.00105, 14.58))
    assert placement_display_zone([]) is None


def resolved_preview():
    selected = candidate("a", MultiLineString([[(121, 14.58), (121.001, 14.58)],
                                               [(121.0011, 14.58), (121.002, 14.58)]]))
    selected.ambiguous_carriageway = False
    selected.fragment_status = "available"
    other = candidate("b", LineString([(121, 14.58008), (121.002, 14.58008)]))
    return NewsPlacementPreview(status="predicted_candidate", reason="unique_ranked_prediction_not_verified_flood_extent",
                                selected_candidate_id="a", candidates=[selected, other])


def test_resolved_display_excludes_opposing_alternative_and_keeps_real_gap():
    preview = resolved_preview()
    before = preview.model_dump()
    display = resolved_placement_display_zone(preview)
    assert display.candidate_ids == ["a"]
    core = shape(display.core_geometry)
    assert core.equals(shape(preview.candidates[0].preview_geometry))
    assert not core.intersects(shape(preview.candidates[1].preview_geometry))
    assert not core.covers(Point(121.00105, 14.58))
    assert shape(display.aura_geometry).covers(core)
    assert preview.model_dump() == before


@pytest.mark.parametrize("updates", [
    {"status": "ambiguous", "selected_candidate_id": None},
    {"status": "source_unavailable"},
    {"status": "unresolved"},
    {"selected_candidate_id": "missing"},
    {"candidates_truncated": True},
    {"uncertainty_reasons": ["historical_claim_preview_only"]},
])
def test_unresolved_or_incomplete_placement_has_no_active_style_display(updates):
    preview = resolved_preview().model_copy(update=updates)
    assert resolved_placement_display_zone(preview) is None
    assert len(preview.candidates) == 2  # Inspection evidence remains available.


@pytest.mark.parametrize("updates", [
    {"ambiguous_carriageway": True}, {"article_place_level": 0},
    {"fragment_status": "source_unavailable"}, {"preview_geometry": None},
])
def test_ranked_selection_does_not_override_unresolved_carriageway_or_missing_geometry(updates):
    preview = resolved_preview()
    preview.candidates[0] = preview.candidates[0].model_copy(update=updates)
    assert resolved_placement_display_zone(preview) is None
