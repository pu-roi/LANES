"""Unit tests for operational flood footprint validation."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from shapely import set_srid
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, mapping

from app.services.operational_footprint_service import (
    OperationalFootprintValidation,
    validate_operational_footprint,
    validate_operational_shape,
)
from app.crud.news_evaluation import canonical_sha256
from app.schemas.news_publication import OperationalFootprintBinding, OperationalFootprintProvenance


def internal_proof(geometry, parent):
    parts = validate_operational_shape(mapping(geometry), geometry_srid=4326).polygon_parts
    binding = OperationalFootprintBinding(evidence_kind="staff_review", record_id="fixture-review", actor_user_id=1,
        article_id=1, input_sha256="a"*64, claim_sha256="b"*64, incident_identity="c"*64,
        observed_at=datetime(2026,10,5,tzinfo=timezone.utc), city="City of Pasig", srid=4326,
        boundary_revision="fixture", component_sha256=[canonical_sha256(part) for part in parts])
    return OperationalFootprintProvenance(source="staff:1", source_checksum="d"*64,
        geometry_sha256=canonical_sha256(mapping(geometry)), parent_boundary_sha256=canonical_sha256(mapping(parent)), binding=binding)


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
    res = validate_operational_footprint(mapping(poly), geometry_srid=4326)
    assert not res.is_eligible
    assert res.reason_code == "missing_geometry_provenance"

    # With allow_unverified=True
    res_unv = validate_operational_footprint(mapping(poly), allow_unverified=True, geometry_srid=4326)
    assert not res_unv.is_eligible
    assert res_unv.reason_code == "unverified_geometry_provenance"


def test_locality_containment_verified():
    # Boundary encompassing Pasig area
    pasig_boundary = Polygon([(121.05, 14.55), (121.10, 14.55), (121.10, 14.60), (121.05, 14.60), (121.05, 14.55)])
    pasig_boundary = set_srid(pasig_boundary, 4326)
    
    # Inside Pasig
    inside_poly = Polygon([(121.06, 14.58), (121.061, 14.58), (121.061, 14.581), (121.06, 14.581), (121.06, 14.58)])
    res_in = validate_operational_footprint(
        mapping(inside_poly),
        provenance_source="official_drrmo_shapefile",
        parent_boundary=pasig_boundary,
        geometry_srid=4326, trusted_provenance=internal_proof(inside_poly, pasig_boundary),
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
        geometry_srid=4326,
    )
    assert not res_out.is_eligible
    assert res_out.reason_code == "outside_parent_locality"


def test_multipolygon_splits_into_discrete_parts():
    poly1 = Polygon([(121.06, 14.58), (121.061, 14.58), (121.061, 14.581), (121.06, 14.581), (121.06, 14.58)])
    poly2 = Polygon([(121.07, 14.58), (121.071, 14.58), (121.071, 14.581), (121.07, 14.581), (121.07, 14.58)])
    multi = MultiPolygon([poly1, poly2])
    parent = set_srid(Polygon([(121.05,14.55),(121.1,14.55),(121.1,14.6),(121.05,14.6)]),4326)

    res = validate_operational_footprint(
        mapping(multi),
        provenance_source="official_drrmo_shapefile",
        geometry_srid=4326, parent_boundary=parent, trusted_provenance=internal_proof(multi,parent),
    )
    assert res.is_eligible
    assert res.reason_code == "verified_operational_footprint"
    assert len(res.polygon_parts) == 2
    # Both parts are individual Polygon GeoJSONs
    assert res.polygon_parts[0]["type"] == "Polygon"
    assert res.polygon_parts[1]["type"] == "Polygon"


@pytest.mark.parametrize("srid", [None, 0, 3857, True])
def test_explicit_wgs84_declaration_required(srid):
    polygon = Polygon([(121.06,14.58),(121.061,14.58),(121.061,14.581),(121.06,14.581)])
    result = validate_operational_shape(mapping(polygon), geometry_srid=srid)
    assert not result.is_eligible and result.reason_code == "unsupported_or_missing_geometry_srid"


@pytest.mark.parametrize("actual", [0,3857])
def test_shapely_srid_cannot_be_relabelled(actual):
    polygon = set_srid(Polygon([(121.06,14.58),(121.061,14.58),(121.061,14.581),(121.06,14.581)]),actual)
    assert not validate_operational_shape(polygon, geometry_srid=4326).is_eligible


@pytest.mark.parametrize("case", ["partial_overlap","hole","outside_component","unknown_parent_srid"])
def test_full_parent_coverage_is_required(case):
    outer = [(121.05,14.55),(121.1,14.55),(121.1,14.6),(121.05,14.6)]
    parent = set_srid(Polygon(outer),4326)
    polygon = Polygon([(121.099,14.58),(121.11,14.58),(121.11,14.59),(121.099,14.59)])
    reason = "outside_parent_locality"
    if case == "hole":
        parent = set_srid(Polygon(outer, [[(121.06,14.57),(121.08,14.57),(121.08,14.59),(121.06,14.59)]]),4326)
        polygon = Polygon([(121.061,14.58),(121.062,14.58),(121.062,14.581),(121.061,14.581)])
    elif case == "outside_component":
        polygon = MultiPolygon([Polygon([(121.06,14.58),(121.061,14.58),(121.061,14.581),(121.06,14.581)]),polygon])
    elif case == "unknown_parent_srid":
        parent, reason = set_srid(parent,0), "invalid_parent_boundary"
    result = validate_operational_shape(mapping(polygon), geometry_srid=4326,parent_boundary=parent)
    assert not result.is_eligible and result.reason_code == reason


def test_touching_parent_boundary_preserves_geometry():
    parent = set_srid(Polygon([(121.05,14.55),(121.1,14.55),(121.1,14.6),(121.05,14.6)]),4326)
    polygon = Polygon([(121.05,14.58),(121.051,14.58),(121.051,14.581),(121.05,14.581)])
    result = validate_operational_shape(mapping(polygon),geometry_srid=4326,parent_boundary=parent)
    assert result.is_eligible and result.geometry.equals(polygon)


def test_tiny_disconnected_part_is_rejected_instead_of_dropped():
    polygon = Polygon([(121.06,14.58),(121.061,14.58),(121.061,14.581),(121.06,14.581)])
    tiny = Polygon([(121.07,14.58),(121.070000001,14.58),(121.070000001,14.580000001),(121.07,14.580000001)])
    result = validate_operational_shape(mapping(MultiPolygon([polygon,tiny])),geometry_srid=4326)
    assert not result.is_eligible and result.reason_code == "zero_or_negligible_component_area"


@pytest.mark.parametrize("case", ["crs","z","label","checksum","no_parent"])
def test_geometry_metadata_is_not_evidence(case):
    polygon = Polygon([(121.06,14.58),(121.061,14.58),(121.061,14.581),(121.06,14.581)])
    value = mapping(polygon)
    options = dict(geometry_srid=4326)
    if case == "crs": value["crs"] = {"name":"EPSG:4326"}
    elif case == "z": value = mapping(Polygon([(121.06,14.58,1),(121.061,14.58,1),(121.061,14.581,1),(121.06,14.581,1)]))
    elif case == "label": options["provenance_source"] = "official-current-flood"
    elif case == "checksum": options.update(provenance_source="official",provenance_checksum="a"*64)
    else:
        parent = set_srid(polygon.buffer(.01),4326)
        options["trusted_provenance"] = internal_proof(polygon,parent)
    assert not validate_operational_footprint(value, **options).is_eligible


def test_component_count_is_bounded():
    from shapely.geometry import box
    polygons = [box(121.06+i*.002,14.58,121.061+i*.002,14.581) for i in range(26)]
    result = validate_operational_shape(mapping(MultiPolygon(polygons)),geometry_srid=4326)
    assert not result.is_eligible and result.reason_code == "operational_component_limit"


def test_coordinate_count_is_bounded():
    from math import sin,cos,pi
    polygon = Polygon([(121.06+.001*cos(2*pi*i/10001),14.58+.001*sin(2*pi*i/10001)) for i in range(10001)])
    result = validate_operational_shape(mapping(polygon),geometry_srid=4326)
    assert not result.is_eligible and result.reason_code == "operational_geometry_size_limit"
