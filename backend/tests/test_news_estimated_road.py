"""Checked modeled road estimates preserve locality, source lines and gaps."""
import pytest
from shapely.geometry import box, shape

from app.crud.news_publication import NewsPublicationError
from app.services.news_estimated_road_service import build_estimated_road_zone
from test_news_placement_preview import service
from test_news_road_placement import claim, ways, write_catalog


def test_estimate_uses_article_bounded_road_and_retains_existing_design_core(tmp_path):
    engine = service(tmp_path)
    estimate = build_estimated_road_zone(claim(), service=engine)
    assert estimate.geometry["type"] == "Polygon"
    assert estimate.evidence.buffer_radius_metres == 25.0
    core = shape(estimate.evidence.component_centerlines[0])
    assert shape(estimate.geometry).covers(core)
    assert engine.roads.locality_boundary(claim()).covers(shape(estimate.geometry))
    assert estimate.evidence.osm_catalog_sha256 == engine.roads.digest
    assert estimate.checksum == build_estimated_road_zone(claim(), service=engine).checksum


def test_separated_noah_sections_remain_separate_zones(tmp_path):
    hazard = box(120.999, 14.629, 121.001, 14.632).difference(box(120.9995, 14.6302, 121.0005, 14.6308))
    estimate = build_estimated_road_zone(claim(), service=service(tmp_path, polygon=hazard))
    assert estimate.geometry["type"] == "MultiPolygon"
    assert len(estimate.evidence.component_centerlines) == 2
    assert not shape(estimate.geometry).covers(shape({"type": "Point", "coordinates": [121, 14.6305]}))


@pytest.mark.parametrize("span", ["near Atok Street", "at the corner of Atok Street"])
def test_grounded_corner_automatically_generates_estimated_polygon_and_core(tmp_path, span):
    engine = service(tmp_path)
    evidence = claim(span=span)
    original = evidence.model_dump()
    preview = engine.preview(evidence)
    assert preview.status == "predicted_candidate" and preview.placement_kind == "predicted"
    assert preview.candidates[0].article_place_level == 2
    estimate = build_estimated_road_zone(evidence, service=engine)
    assert shape(estimate.geometry).is_valid
    assert shape(estimate.geometry).area > 0
    assert shape(estimate.geometry).covers(shape(estimate.evidence.component_centerlines[0]))
    assert engine.roads.locality_boundary(evidence).covers(shape(estimate.geometry))
    assert estimate.evidence.buffer_radius_metres == 25
    assert evidence.model_dump() == original


def test_corner_with_equally_supported_sides_stays_in_review(tmp_path):
    engine = service(tmp_path)
    roads = ways()
    roads[0]["nodes"].append((6,121,14.632))
    roads.append(dict(osm_id=40,name="Next Street",nodes=[(6,121,14.632),(7,121.001,14.632)]))
    engine.roads = write_catalog(tmp_path / "roads", roads)
    evidence = claim(span="near Calamba Street")
    preview = engine.preview(evidence)
    assert len(preview.candidates) == 2
    assert preview.selected_candidate_id is None
    with pytest.raises(NewsPublicationError, match="multiple_equally_supported_sections"):
        build_estimated_road_zone(evidence, service=engine)


@pytest.mark.parametrize("kind", ["broad", "no_overlap", "historic", "bridge", "gap"])
def test_incomplete_or_unsafe_estimates_cannot_activate(tmp_path, kind):
    polygon = box(120.98, 14.60, 120.99, 14.61) if kind == "no_overlap" else None
    if kind == "gap":
        polygon = box(120.999, 14.629, 121.001, 14.632).difference(box(120.9995, 14.63045, 121.0005, 14.63055))
    engine = service(tmp_path, polygon=polygon)
    evidence = claim(span=None) if kind == "broad" else claim(is_historical=True) if kind == "historic" else claim()
    if kind == "bridge":
        road_ways = ways()
        road_ways[0]["bridge"] = "yes"
        engine.roads = write_catalog(tmp_path / "roads", road_ways)
    with pytest.raises(NewsPublicationError):
        build_estimated_road_zone(evidence, service=engine)
