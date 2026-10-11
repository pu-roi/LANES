"""Source-backed route aliases and fail-closed offline asset provisioning."""
import hashlib
import json
from types import SimpleNamespace

import pytest
from shapely.geometry import box

from scripts.audit_news_spatial_assets import audit_assets
from scripts.build_news_osm_catalog import NamedRoads, RoadRoutes
from scripts.provision_news_barangay_catalog import provision_catalog
from test_barangay_placement import boundary_catalog
from test_news_placement_preview import service
from test_news_road_placement import claim, ways, write_catalog


@pytest.mark.parametrize("name", ["C5", "C-5", "C5 Road", "C-5 Road"])
def test_road_route_membership_supplies_source_backed_c5_alias(tmp_path, name):
    road_ways = ways()
    road_ways[0].update(name="E. Rodriguez Jr. Avenue",
        route_references=[dict(relation_id=417210, reference="C-5")])
    result = write_catalog(tmp_path, road_ways).resolve(claim(span=None, canonical_road=name))
    assert result.total_candidate_count == 1
    assert result.candidates[0].osm_way_ids == [10]
    assert result.status == "ambiguous" and result.reason == "reported_road_extent_unbounded"
    assert not result.may_affect_routing and not result.proves_current_flood


def test_road_route_alias_also_matches_explicit_article_span(tmp_path):
    road_ways = ways()
    road_ways[0].update(name="E. Rodriguez Jr. Avenue",
        route_references=[dict(relation_id=417210, reference="C-5")])
    result = write_catalog(tmp_path, road_ways).resolve(claim(canonical_road="C5"))
    assert result.status == "bounded_candidate" and result.candidates[0].kind == "reported_span"
    assert not result.may_affect_routing


def test_route_alias_with_missing_nodes_stays_unresolved(tmp_path):
    provider = write_catalog(tmp_path, incomplete_ways=[dict(osm_id=99, name="E. Rodriguez Jr. Avenue",
        route_references=[dict(relation_id=417210, reference="C-5")])])
    result = provider.resolve(claim(span=None, canonical_road="C5"))
    assert result.reason == "incomplete_named_road_coverage" and not result.candidates


def test_collector_uses_only_explicit_road_route_references():
    handler = RoadRoutes()
    member = SimpleNamespace(type="w", ref=10, role="")
    for kind, reference, identity in [("bus", "C5", 1), ("road", "C-5;N11", 2), ("road", "", 3)]:
        handler.relation(SimpleNamespace(id=identity, tags={"type":"route", "route":kind, "ref":reference},
            members=[member, SimpleNamespace(type="r", ref=11, role="")]))
    assert handler.references == {10:[dict(relation_id=2, reference="C-5"), dict(relation_id=2, reference="N11")]}


def test_named_road_builder_retains_membership_without_inventing_way_name():
    handler = NamedRoads({10:[dict(relation_id=417210, reference="C-5")]})
    nodes = [SimpleNamespace(ref=index, lon=121.0, lat=14.63 + index / 10000,
        location=SimpleNamespace(valid=lambda:True)) for index in (1, 2)]
    handler.way(SimpleNamespace(id=10, tags={"highway":"primary", "name":"E. Rodriguez Jr. Avenue"}, nodes=nodes))
    assert handler.ways[0]["name"] == "E. Rodriguez Jr. Avenue"
    assert handler.ways[0]["route_references"] == [dict(relation_id=417210, reference="C-5")]
    assert handler.ways[0]["aliases"] == []


def test_source_coverage_audit_never_promotes_centerline_to_flood_footprint(tmp_path):
    provider = write_catalog(tmp_path)
    result = audit_assets(provider, "Quezon City", "Santo Domingo Avenue")
    assert result["ways_with_positive_length_in_city"] == 1
    assert result["barangay_error"] == "missing_valid_barangay_boundary"
    assert not result["operational_flood_geometry_ready"]
    assert not result["placement"]["may_affect_routing"]


def test_asset_audit_identifies_only_matching_route_reference_relations(tmp_path):
    road_ways = ways()
    road_ways[0].update(name="E. Rodriguez Jr. Avenue", route_references=[
        dict(relation_id=417210, reference="C-5"),dict(relation_id=13853157, reference="11")])
    result = audit_assets(write_catalog(tmp_path,road_ways), "Quezon City", "C5")
    assert result["route_reference_relations"] == [417210]


def provisioning_inputs(tmp_path, outside=False):
    initial = service(tmp_path, city="Pasig")
    archive = tmp_path / "original.geojson"
    archive.write_bytes(b"synthetic source fixture; never install in runtime")
    directory = tmp_path / "reviewed"
    provider = boundary_catalog(directory, box(121.1,14.63,121.11,14.64) if outside else None,
        source_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
    return provider, archive, tmp_path / "version", initial.roads.directory


def test_provisioning_verifies_source_and_parent_before_new_snapshot(tmp_path):
    boundaries, archive, output, roads = provisioning_inputs(tmp_path)
    receipt = provision_catalog(tmp_path / "reviewed", archive, output, roads,
        "https://example.org/synthetic-license", "test-fixture-reviewer")
    assert receipt["catalog_sha256"] == boundaries.digest and receipt["verified_record_count"] == 1
    assert (output / "polygon_source.archive").read_bytes() == archive.read_bytes()
    assert not receipt["may_affect_routing"]
    from app.services.barangay_boundary_service import BarangayBoundaryProvider
    assert BarangayBoundaryProvider(output).digest == boundaries.digest
    with pytest.raises(ValueError, match="new version"):
        provision_catalog(tmp_path / "reviewed", archive, output, roads,
            "https://example.org/synthetic-license", "test-fixture-reviewer")


@pytest.mark.parametrize("failure", ["source_hash", "parent", "license", "reviewer", "catalog"])
def test_provisioning_failure_never_installs_partial_or_broader_boundary(tmp_path, failure):
    boundaries, archive, output, roads = provisioning_inputs(tmp_path, outside=failure == "parent")
    license_url, reviewer = "https://example.org/synthetic-license", "test-fixture-reviewer"
    if failure == "source_hash":
        archive.write_bytes(b"changed source")
    if failure == "license":
        license_url = ""
    if failure == "reviewer":
        reviewer = " "
    if failure == "catalog":
        (tmp_path / "reviewed" / "manifest.json").write_text(json.dumps({"catalog_sha256":"0" * 64}))
    with pytest.raises(ValueError):
        provision_catalog(tmp_path / "reviewed", archive, output, roads, license_url, reviewer)
    assert not output.exists()


def test_route_membership_cannot_move_road_into_different_city(tmp_path):
    road_ways = ways()
    road_ways[0].update(name="E. Rodriguez Jr. Avenue",
        route_references=[dict(relation_id=417210, reference="C-5")],
        nodes=[(11,121.2,14.63),(12,121.2,14.631)])
    result = audit_assets(write_catalog(tmp_path,road_ways), "Quezon City", "C5")
    assert result["road_name_matches"] == 1 and result["ways_with_positive_length_in_city"] == 0
    assert not result["placement"]["candidates"]
