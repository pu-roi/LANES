"""Locality points ground estimates without replacing road/NOAH evidence."""
import pytest
from shapely.geometry import box, shape

from app.crud.news_publication import NewsPublicationError
from app.services.news_estimated_road_service import build_estimated_road_zone
from test_news_placement_preview import service
from test_news_road_placement import claim, ways, write_catalog


def locality(**changes):
    row = dict(osm_node_id=900, name="Sitio Sais", aliases=["Sitio 6"], place="neighbourhood",
        city="Quezon City", quarter="Fixture Quarter", longitude=121.0005, latitude=14.6304)
    row.update(changes)
    return row


def road_network():
    rows = ways()
    rows[0]["nodes"].append((6, 121, 14.632))
    rows.append(dict(osm_id=40, name="Next Street", nodes=[(6,121,14.632),(7,121.001,14.632)]))
    return rows


def anchored_service(tmp_path, places=None, *, polygon=None, grade=None, **changes):
    engine = service(tmp_path, polygon=polygon)
    directory = tmp_path / "anchored"
    directory.mkdir()
    network = road_network()
    network[0].update(grade or {})
    engine.roads = write_catalog(directory, network, localities=places or [locality()], **changes)
    return engine


@pytest.mark.parametrize("reference", ["Sitio 6", "Sitio Sais", "Sitio Anim", "Sitio Six"])
def test_source_aliases_find_a_bounded_road_estimate_without_manual_coordinates(tmp_path, reference):
    engine = anchored_service(tmp_path)
    evidence = claim(span=None, local_area_raw=reference)
    before = evidence.model_dump()
    placement = engine.roads.resolve(evidence)
    assert placement.locality_anchor.osm_node_id == 900
    assert placement.total_candidate_count == 1
    assert placement.locality_anchor.distance_metres > 25  # Not a flood-width buffer.
    assert not placement.proves_current_flood and not placement.may_affect_routing
    preview = engine.preview(evidence, placement)
    assert preview.status == "predicted_candidate"
    assert preview.candidates[0].article_place_level == 2
    assert preview.locality_anchor == placement.locality_anchor
    estimate = build_estimated_road_zone(evidence, service=engine)
    assert shape(estimate.geometry).is_valid
    assert estimate.evidence.buffer_radius_metres == 25
    assert shape(estimate.geometry).covers(shape(estimate.evidence.component_centerlines[0]))
    assert evidence.model_dump() == before


def test_same_name_in_other_city_is_not_used(tmp_path):
    engine = anchored_service(tmp_path)
    evidence = claim(span=None, local_area_raw="Sitio 6", canonical_city="Malabon")
    assert engine.roads.resolve(evidence).reason == "reported_city_not_covered"


@pytest.mark.parametrize("changes", [dict(city="Malabon"), dict(longitude=121.2),
    dict(place="city"), dict(osm_node_id=-1), dict(latitude=float("nan"))])
def test_invalid_locality_catalog_cannot_be_used(tmp_path, changes):
    provider = write_catalog(tmp_path, localities=[locality(**changes)])
    assert provider.resolve(claim(span=None, local_area_raw="Sitio 6")).status == "source_unavailable"


def test_same_city_duplicate_localities_remain_ambiguous(tmp_path):
    engine = anchored_service(tmp_path, [locality(), locality(osm_node_id=901, quarter="Other Quarter")])
    evidence = claim(span=None, local_area_raw="Sitio 6")
    placement = engine.roads.resolve(evidence)
    assert placement.reason == "locality_anchor_ambiguous"
    assert not placement.candidates


@pytest.mark.parametrize("reference", ["Sitio 5", "Sitio 60", "Sitio 6-A", "Sitio 6 near Missing Street"])
def test_other_numbers_and_extra_qualifiers_are_not_discarded(tmp_path, reference):
    engine = anchored_service(tmp_path)
    assert engine.roads.resolve(claim(span=None, local_area_raw=reference)).reason == "local_place_not_grounded"


def test_an_unmapped_crossing_cannot_be_bypassed_with_a_locality_point(tmp_path):
    engine = anchored_service(tmp_path)
    placement = engine.roads.resolve(claim(span="near Missing Street", local_area_raw="Sitio 6"))
    assert placement.reason == "local_place_not_grounded" and not placement.candidates


def test_far_source_point_does_not_select_another_part_of_the_city(tmp_path):
    engine = anchored_service(tmp_path, [locality(longitude=121.02)])
    placement = engine.roads.resolve(claim(span=None, local_area_raw="Sitio 6"))
    assert placement.reason == "locality_anchor_too_far_from_reported_road"
    assert not placement.candidates


def test_equal_sections_remain_ambiguous_under_existing_noah_rules(tmp_path):
    engine = anchored_service(tmp_path, [locality(latitude=14.631)])
    evidence = claim(span=None, local_area_raw="Sitio 6")
    preview = engine.preview(evidence)
    assert len(preview.candidates) == 2
    assert preview.reason == "multiple_equally_supported_sections"
    with pytest.raises(NewsPublicationError):
        build_estimated_road_zone(evidence, service=engine)


@pytest.mark.parametrize("tamper", ["id", "distance", "geometry", "subset"])
def test_supplied_anchor_or_geometry_cannot_grant_specificity(tmp_path, tamper):
    engine = anchored_service(tmp_path, [locality(latitude=14.631)])
    evidence = claim(span=None, local_area_raw="Sitio 6")
    placement = engine.roads.resolve(evidence).model_copy(deep=True)
    if tamper == "id":
        placement.locality_anchor.osm_node_id = 901
    elif tamper == "distance":
        placement.locality_anchor.distance_metres = 1
    elif tamper == "subset":
        placement.candidates = placement.candidates[:1]
    else:
        placement.candidates[0].centerline_geojson["coordinates"][0][0] += 0.001
    assert engine.preview(evidence, placement).reason == "placement_source_mismatch"


def test_catalog_locality_change_updates_processing_identity(tmp_path):
    first = write_catalog(tmp_path, localities=[locality()])
    revision = first.revision
    second = write_catalog(tmp_path, localities=[locality(latitude=14.6305)])
    assert second.revision != revision


def test_locality_point_cannot_replace_missing_noah_overlap(tmp_path):
    engine = anchored_service(tmp_path, polygon=box(121.01, 14.64, 121.02, 14.65))
    evidence = claim(span=None, local_area_raw="Sitio 6")
    assert engine.roads.resolve(evidence).locality_anchor is not None
    with pytest.raises(NewsPublicationError):
        build_estimated_road_zone(evidence, service=engine)


@pytest.mark.parametrize("grade", [dict(bridge="yes"), dict(tunnel="yes"), dict(layer="1")])
def test_locality_point_cannot_override_road_elevation_checks(tmp_path, grade):
    engine = anchored_service(tmp_path, grade=grade)
    with pytest.raises(NewsPublicationError, match="named_road_sections_not_found|estimated_road_elevation_unresolved"):
        build_estimated_road_zone(claim(span=None, local_area_raw="Sitio 6"), service=engine)


def test_empty_optional_anchor_preserves_legacy_claim_hash(tmp_path):
    import hashlib
    import json
    from app.schemas.news_extraction import ExtractedClaim
    from app.services.news_claim_auditor import canonical_claim_sha256

    engine = service(tmp_path)
    evidence = claim()
    evidence.road_placement = engine.roads.resolve(evidence)
    evidence.placement_preview = engine.preview(evidence)
    legacy = evidence.model_dump(mode="json")
    legacy["road_placement"].pop("locality_anchor", None)
    legacy["placement_preview"].pop("locality_anchor", None)
    digest = hashlib.sha256(json.dumps(legacy,ensure_ascii=False,sort_keys=True,
        separators=(",", ":"),allow_nan=False).encode()).hexdigest()
    assert canonical_claim_sha256(ExtractedClaim.model_validate(legacy)) == digest
