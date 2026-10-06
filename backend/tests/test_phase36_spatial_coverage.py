import pytest
from shapely.geometry import Point

from scripts.audit_phase36_metro_spatial_coverage import (
    assemble_boundary,
    point_in_ring,
    sample_city_points,
)


def test_boundary_assembly_preserves_inner_holes():
    outer = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    inner = [(3, 3), (7, 3), (7, 7), (3, 7), (3, 3)]

    boundary = assemble_boundary(
        42,
        "Example City",
        [(1, "outer"), (2, "inner")],
        {1: outer, 2: inner},
    )

    assert boundary.is_valid
    assert boundary.area == pytest.approx(84)
    assert boundary.covers(Point(1, 1))
    assert not boundary.covers(Point(5, 5))


def test_boundary_assembly_fails_closed_when_relation_way_is_missing():
    with pytest.raises(ValueError, match=r"relation 42 .* missing way 2"):
        assemble_boundary(42, "Example City", [(1, "outer"), (2, "outer")], {
            1: [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)],
        })


def test_city_grid_samples_only_points_inside_boundary():
    from shapely.geometry import box

    boundary = box(0, 0, 10, 10).difference(box(4, 4, 6, 6))
    points = sample_city_points(boundary, divisions=5)

    assert points
    assert all(boundary.covers(point) for point in points)
    assert not any(4 < point.x < 6 and 4 < point.y < 6 for point in points)


def test_point_in_ring_identifies_inside_and_outside_points():
    import numpy as np

    ring = np.asarray([(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)], dtype=float)
    points = [Point(2, 2), Point(5, 2), Point(-1, 2)]

    assert point_in_ring(points, ring).tolist() == [True, False, False]
