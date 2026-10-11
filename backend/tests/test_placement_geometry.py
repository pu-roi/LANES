"""Hazard display unions retain source bends and real gaps despite roundoff."""
import pytest
from shapely.geometry import LineString, Point

from app.services.noah_vector_catalog_service import metric_geometry
from app.services.placement_geometry_service import source_aligned_line_union


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
