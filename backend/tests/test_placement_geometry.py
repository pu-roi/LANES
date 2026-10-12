"""Hazard display unions retain source bends and real gaps despite roundoff."""
import pytest
from shapely.geometry import LineString, Point

from app.services.noah_vector_catalog_service import metric_geometry
from app.services.placement_geometry_service import source_aligned_line_union


def test_whole_source_preserves_exact_border_vertices_without_inverse_scaling():
    from shapely.geometry import box
    source = LineString([(121.0017254, 14.6327076), (121.0023183, 14.6329815)])
    parent = box(121.0, 14.63, 121.01, 14.6329815)
    assert parent.covers(source)
    result = source_aligned_line_union(source, [source])
    assert list(result.coords) == list(source.coords) and parent.covers(result)


def test_partial_interval_retains_original_end_vertex_and_bends():
    source = LineString([(121.0,14.6),(121.001,14.601),(121.0023183,14.6329815)])
    fragment = LineString([(121.0005,14.6005),*list(source.coords)[1:]])
    result = source_aligned_line_union(source,[fragment])
    assert list(result.coords)[-2:] == list(source.coords)[-2:]
    assert result.coords[0][0] == pytest.approx(121.0005)


def test_coincident_diagonal_scenarios_do_not_duplicate_road_length():
    source = LineString([(121, 14.63), (121.001, 14.631), (121.002, 14.6305)])
    almost_same = LineString([(x + 1e-14, y - 1e-14) for x, y in source.coords])
    result = source_aligned_line_union(source, [source, almost_same])
    assert result.geom_type == "LineString"
    assert metric_geometry(result).length == pytest.approx(metric_geometry(source).length, abs=1e-6)
    assert len(result.coords) == 3


def test_separate_modeled_fragments_preserve_dry_gap():
    source = LineString([(121, 14.63), (121, 14.632)])
    result = source_aligned_line_union(source, [
        LineString([(121,14.63),(121,14.6305)]),
        LineString([(121,14.631),(121,14.632)]),
    ])
    assert result.geom_type == "MultiLineString" and len(result.geoms) == 2
    assert result.distance(Point(121,14.63075)) > 0


@pytest.mark.parametrize("fragment", [
    LineString([(121.00001,14.63),(121.00001,14.631)]),
    LineString([(121,14.63),(121.002,14.6305)]),
])
def test_outside_or_shortcut_fragment_cannot_be_snapped_onto_source(fragment):
    source = LineString([(121,14.63),(121.001,14.631),(121.002,14.6305)])
    with pytest.raises(ValueError):
        source_aligned_line_union(source, [fragment])
