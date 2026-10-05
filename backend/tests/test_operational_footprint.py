"""Unit tests for operational flood footprint validation."""
from __future__ import annotations

import pytest
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, mapping

from app.services.operational_footprint_service import (
    OperationalFootprintValidation,
    validate_operational_footprint,
)


def test_missing_or_invalid_syntax_rejected():
    res1 = validate_operational_footprint(None)
    assert not res1.is_eligible
    assert res1.reason_code == "missing_geometry"

    res2 = validate_operational_footprint({"invalid": "syntax"})
    assert not res2.is_eligible
    assert res2.reason_code == "invalid_geometry_syntax"


def test_linestring_and_point_rejected():
    line = LineString([(121.0, 14.5), (121.01, 14.51)])
    res_line = validate_operational_footprint(mapping(line), provenance_source="test_source")
    assert not res_line.is_eligible
    assert res_line.reason_code == "unsupported_geometry_type_linestring"

    point = Point(121.0, 14.5)
    res_pt = validate_operational_footprint(mapping(point), provenance_source="test_source")
    assert not res_pt.is_eligible
    assert res_pt.reason_code == "unsupported_geometry_type_point"


def test_invalid_topology_and_empty_rejected():
    # Self-intersecting polygon (bowtie)
    bowtie = Polygon([(0, 0), (1, 1), (0, 1), (1, 0), (0, 0)])
    res_inv = validate_operational_footprint(mapping(bowtie), provenance_source="test_source")
    assert not res_inv.is_eligible
    assert res_inv.reason_code == "invalid_topology"

    empty_poly = Polygon()
    res_emp = validate_operational_footprint(empty_poly, provenance_source="test_source")
    assert not res_emp.is_eligible
    assert res_emp.reason_code == "empty_geometry"


def test_missing_provenance_rejected_by_default():
    poly = Polygon([(121.06, 14.58), (121.061, 14.58), (121.061, 14.581), (121.06, 14.581), (121.06, 14.58)])
    res = validate_operational_footprint(mapping(poly))
    assert not res.is_eligible
    assert res.reason_code == "missing_geometry_provenance"

    # With allow_unverified=True
    res_unv = validate_operational_footprint(mapping(poly), allow_unverified=True)
    assert res_unv.is_eligible
    assert res_unv.reason_code == "verified_operational_footprint"


def test_locality_containment_verified():
    # Boundary encompassing Pasig area
    pasig_boundary = Polygon([(121.05, 14.55), (121.10, 14.55), (121.10, 14.60), (121.05, 14.60), (121.05, 14.55)])
    
    # Inside Pasig
    inside_poly = Polygon([(121.06, 14.58), (121.061, 14.58), (121.061, 14.581), (121.06, 14.581), (121.06, 14.58)])
    res_in = validate_operational_footprint(
        mapping(inside_poly),
        provenance_source="official_drrmo_shapefile",
        parent_boundary=pasig_boundary,
    )
    assert res_in.is_eligible
    assert res_in.reason_code == "verified_operational_footprint"
    assert res_in.area_sqm > 5000.0  # Approx 100m x 100m is ~10,000 sqm
    assert len(res_in.polygon_parts) == 1

    # Outside Pasig (e.g. QC)
    outside_poly = Polygon([(121.02, 14.65), (121.021, 14.65), (121.021, 14.651), (121.02, 14.651), (121.02, 14.65)])
    res_out = validate_operational_footprint(
        mapping(outside_poly),
        provenance_source="official_drrmo_shapefile",
        parent_boundary=pasig_boundary,
    )
    assert not res_out.is_eligible
    assert res_out.reason_code == "outside_parent_locality"


def test_multipolygon_splits_into_discrete_parts():
    poly1 = Polygon([(121.06, 14.58), (121.061, 14.58), (121.061, 14.581), (121.06, 14.581), (121.06, 14.58)])
    poly2 = Polygon([(121.07, 14.58), (121.071, 14.58), (121.071, 14.581), (121.07, 14.581), (121.07, 14.58)])
    multi = MultiPolygon([poly1, poly2])

    res = validate_operational_footprint(
        mapping(multi),
        provenance_source="official_drrmo_shapefile",
    )
    assert res.is_eligible
    assert res.reason_code == "verified_operational_footprint"
    assert len(res.polygon_parts) == 2
    # Both parts are individual Polygon GeoJSONs
    assert res.polygon_parts[0]["type"] == "Polygon"
    assert res.polygon_parts[1]["type"] == "Polygon"
