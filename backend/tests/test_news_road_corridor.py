"""Road-level estimates preserve lane evidence and cannot invent lane closures."""
from copy import deepcopy

import pytest
from shapely.geometry import LineString, box, mapping, shape

from app.crud.news_publication import NewsPublicationError
from app.schemas.news_placement import PlacementSection
from app.services.news_road_corridor_service import bounded_road_corridors
from app.services.news_estimated_road_service import build_estimated_road_zone
from app.services.noah_vector_catalog_service import metric_geometry
from test_news_placement_preview import noah_catalog, service
from test_news_road_placement import claim, ways, write_catalog


def candidate(identity, x):
    core = mapping(LineString([(x, 14.63), (x, 14.631)]))
    return PlacementSection(candidate_id=identity, kind="road_section", centerline_geojson=core,
        osm_way_ids=[10 if identity == "left" else 11], cross_streets=[["Atok Street"], ["Calamba Street"]],
        ambiguous_carriageway=True, article_place_level=2, approximate_length_m=110,
        modeled_overlap_m={p: {1: 0, 2: 0, 3: 110} for p in (5, 25, 100)},
        preview_geometry=core, fragment_status="available")


def test_parallel_road_corridor_retains_exact_originals_and_provenance():
    originals = [candidate("left", 121), candidate("right", 121.00008)]
    before = deepcopy(originals)
    corridor, = bounded_road_corridors(originals)
    assert originals == before
    assert corridor.carriageway_candidate_ids == ["left", "right"]
    assert corridor.centerline_geojson["type"] == "MultiLineString"
    assert shape(corridor.centerline_geojson).equals(
        shape({"type": "MultiLineString", "coordinates": [item.centerline_geojson["coordinates"] for item in originals]}))
    assert not corridor.ambiguous_carriageway


@pytest.mark.parametrize("problem", ["far", "third", "crossed", "anchors", "mislocated_anchors", "no_overlap"])
def test_unresolved_paths_cannot_be_reclassified_as_one_corridor(problem):
    members = [candidate("left", 121), candidate("right", 121.00008)]
    if problem == "far": members[1] = candidate("right", 121.002)
    if problem == "third": members.append(candidate("third", 121.00004))
    if problem == "crossed":
        members[1].centerline_geojson = mapping(LineString([(120.99999, 14.63), (121.00001, 14.631)]))
    if problem == "anchors": members[1].cross_streets[1] = ["Other Street"]
    if problem == "mislocated_anchors": members[1].cross_streets.reverse()
    if problem == "no_overlap": members[1].fragment_status = "no_modeled_overlap"
    assert bounded_road_corridors(members) == []


def parallel_engine(tmp_path):
    engine = service(tmp_path)
    roads = ways() + [
        dict(osm_id=11, name="Santo Domingo Avenue", nodes=[(11,121.00008,14.63),(13,121.00008,14.631)]),
        dict(osm_id=21, name="Atok Street", nodes=[(14,121.0002,14.63),(11,121.00008,14.63)]),
        dict(osm_id=31, name="Calamba Street", nodes=[(13,121.00008,14.631),(15,121.0002,14.631)])]
    engine.roads = write_catalog(tmp_path / "roads", roads)
    return engine


def test_verified_passable_estimate_dissolves_halo_once_and_keeps_both_source_cores(tmp_path):
    engine = parallel_engine(tmp_path)
    evidence = claim(span="at the corner of Atok Street", road_passability="passable_all")
    preview = engine.preview(evidence)
    assert len(preview.candidates) == 3  # Both originals remain, plus the corridor.
    assert sum(bool(c.carriageway_candidate_ids) for c in preview.candidates) == 1
    estimate = build_estimated_road_zone(evidence, service=engine)
    assert estimate.geometry["type"] == "Polygon"  # One stored halo, not stacked polygons.
    assert len(estimate.evidence.component_centerlines) == 1
    assert estimate.evidence.component_centerlines[0]["type"] == "MultiLineString"
    assert len(estimate.evidence.carriageway_candidate_ids) == 2
    assert estimate.evidence.policy_version == "news-estimated-road-v2"
    assert shape(estimate.geometry).covers(shape(estimate.evidence.component_centerlines[0]))


@pytest.mark.parametrize("access", ["unknown", "passable_unspecified", "impassable_all"])
def test_unspecified_lane_location_must_not_close_both_directions(tmp_path, access):
    engine = parallel_engine(tmp_path)
    evidence = claim(span="at the corner of Atok Street", road_passability=access)
    with pytest.raises(NewsPublicationError, match="estimated_corridor_access_unresolved"):
        build_estimated_road_zone(evidence, service=engine)


def test_direction_specific_claim_is_not_expanded_to_both_carriageways(tmp_path):
    preview = parallel_engine(tmp_path).preview(claim(span="westbound near Atok Street"))
    assert preview.selected_candidate_id is None and not preview.candidates


def test_broad_road_name_cannot_use_corridor_grouping_to_invent_location(tmp_path):
    preview = parallel_engine(tmp_path).preview(claim(span=None))
    assert preview.selected_candidate_id is None
    assert all(not item.carriageway_candidate_ids for item in preview.candidates)


@pytest.mark.parametrize("both", [False, True])
def test_modeled_lane_gap_is_preserved_and_full_road_gap_blocks_activation(tmp_path, both):
    engine = parallel_engine(tmp_path)
    gap = box(120.9999 if both else 121.00004, 14.63045, 121.0002, 14.63055)
    engine.noah = noah_catalog(tmp_path / "gapped-noah", box(120.99,14.60,121.03,14.67).difference(gap))
    evidence = claim(span="at the corner of Atok Street", road_passability="passable_all")
    if both:
        with pytest.raises(NewsPublicationError, match="estimated_road_corridors_would_bridge_gap"):
            build_estimated_road_zone(evidence, service=engine)
    else:
        estimate = build_estimated_road_zone(evidence, service=engine)
        core = shape(estimate.evidence.component_centerlines[0])
        assert metric_geometry(core).distance(metric_geometry(LineString([(121.00008,14.63046),(121.00008,14.63054)]))) > 1
        assert metric_geometry(core).distance(metric_geometry(LineString([(121,14.63046),(121,14.63054)]))) < .00001
        assert estimate.geometry["type"] == "Polygon"
