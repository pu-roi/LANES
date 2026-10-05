"""Community source rings and PSGC crosswalks are reviewed without repair."""
import json

import pytest
from shapely.geometry import box, shape

from app.services.barangay_boundary_service import BarangayBoundaryProvider, DEFAULT_DIRECTORY
from app.services.news_road_placement_service import NewsRoadPlacementProvider, DEFAULT_CATALOG_DIR
from scripts.build_news_barangay_catalog import pasig_reference, review_records, reviewed_polygon, DEFAULT_PSGC_REFERENCE
from scripts.provision_news_barangay_catalog import provision_catalog
from test_news_spatial_assets import provisioning_inputs
from test_news_road_placement import claim


def fixture_records(reference="137403029", name="Ugong", parent=None):
    references = {"137403029":{"name":"Ugong","psgc_code":"1381200029","city_municipality":"City of Pasig"}}
    references["1381200029"] = references["137403029"]
    coordinates = {1:[(121,14.6),(121.01,14.6),(121.01,14.61)],
        2:[(121.01,14.61),(121,14.61),(121,14.6)]}
    relations = [dict(relation_id=108731,tags={"name":name,"ref":reference},
        members=[("w",1,"outer"),("w",2,"outer")])]
    return relations, coordinates, references, parent if parent is not None else box(120.9,14.5,121.2,14.8)


@pytest.mark.parametrize("reference", ["137403029", "1381200029"])
def test_exact_legacy_and_current_psgc_references_preserve_identity(reference):
    accepted, excluded = review_records(*fixture_records(reference))
    assert not excluded and accepted[0]["psgc_code"] == "1381200029"
    assert accepted[0]["osm_relation_id"] == 108731
    assert accepted[0]["source_url"] == "https://www.openstreetmap.org/relation/108731"


@pytest.mark.parametrize("reference,name,reason", [
    ("137404126","Ugong","no_explicit_pasig_psgc_reference"),
    ("","Ugong","no_explicit_pasig_psgc_reference"),
    ("137403029","Ugong Norte","psgc_boundary_name_mismatch"),
])
def test_name_or_matching_digits_cannot_substitute_for_ref_parent_crosswalk(reference,name,reason):
    accepted, excluded = review_records(*fixture_records(reference,name))
    assert not accepted and excluded[0]["reason"] == reason


def test_duplicate_identity_never_selects_arbitrary_lower_relation_id():
    relations,coords,refs,parent = fixture_records()
    relations.append({**relations[0],"relation_id":108732})
    accepted, excluded = review_records(relations,coords,refs,parent)
    assert not accepted and len(excluded) == 2
    assert all(row["reason"] == "duplicate_barangay_identity" for row in excluded)


def test_parent_containment_failure_stays_explicit_without_clipping():
    accepted, excluded = review_records(*fixture_records(parent=box(121,14.6,121.005,14.61)))
    assert not accepted and excluded[0]["reason"] == "barangay_boundary_parent_mismatch"


def test_disconnected_source_polygons_and_holes_survive_review():
    members=[("w",1,"outer"),("w",2,"outer"),("w",3,"inner")]
    coordinates={1:list(box(121,14.6,121.01,14.61).exterior.coords),
        2:list(box(121.02,14.6,121.03,14.61).exterior.coords),
        3:list(box(121.002,14.602,121.004,14.604).exterior.coords)}
    polygon, reason = reviewed_polygon(members,coordinates)
    assert reason is None and polygon.geom_type == "MultiPolygon"
    assert len(polygon.geoms) == 2 and sum(len(part.interiors) for part in polygon.geoms) == 1


@pytest.mark.parametrize("failure", ["missing","unclosed","self_crossing","nested"])
def test_source_failures_cannot_be_repaired_into_valid_reviewed_polygons(failure):
    relations,coordinates,_,_ = fixture_records()
    if failure == "missing":
        coordinates.pop(2)
    elif failure == "unclosed":
        coordinates[2] = coordinates[2][:-1]
    elif failure == "self_crossing":
        coordinates[1]=[(121,14.6),(121.01,14.61),(121,14.61),(121.01,14.6),(121,14.6)]
    else:
        relations[0]["members"].append(("r",200,"outer"))
    polygon,reason=reviewed_polygon(relations[0]["members"],coordinates)
    assert polygon is None and reason


def test_bundled_reference_preserves_correspondence_codes_without_digit_inference():
    reference=pasig_reference(DEFAULT_PSGC_REFERENCE)
    assert reference["137403029"] == reference["1381200029"]
    assert reference["1381200029"]["name"] == "Ugong"
    assert "137404126" not in reference


def test_archived_source_can_remain_separate_from_small_runtime_assets(tmp_path):
    _,archive,output,roads=provisioning_inputs(tmp_path)
    receipt=provision_catalog(tmp_path / "reviewed",archive,output,roads,
        "https://example.org/synthetic-license","test-fixture-reviewer",copy_source_archive=False)
    assert receipt["source_archive_mode"] == "already_archived_separately"
    assert archive.exists() and not (output / "polygon_source.archive").exists()


def test_bundled_real_ugong_source_provenance_and_candidates_are_locality_bounded():
    boundaries=BarangayBoundaryProvider(DEFAULT_DIRECTORY)
    assert boundaries.error is None and boundaries.catalog.source_classification == "osm_community"
    assert "Automated review by Codex geometry agent" in boundaries.catalog.review_method
    roads=NewsRoadPlacementProvider(DEFAULT_CATALOG_DIR,boundaries)
    value=claim(span=None,raw_place_name="C5",canonical_road="C5",canonical_city="Pasig",canonical_barangay="Ugong")
    placement=roads.resolve(value)
    polygon=roads.barangay_boundary(value)
    assert placement.barangay_osm_relation_id == 108731
    assert placement.barangay_psgc_code == "1381200029"
    assert placement.barangay_source_classification == "osm_community"
    assert placement.barangay_source_url == "https://www.openstreetmap.org/relation/108731"
    assert placement.candidates and all(polygon.covers(shape(c.centerline_geojson)) for c in placement.candidates)
    assert not placement.proves_current_flood and not placement.may_affect_routing
    receipt=json.loads((DEFAULT_DIRECTORY / "review_receipt.json").read_bytes())
    assert receipt["accepted_records"] == len(boundaries.records) == 20
    missing=value.model_copy(update={"canonical_barangay":"Pinagbuhatan"})
    assert roads.resolve(missing).reason == "missing_valid_barangay_boundary"
