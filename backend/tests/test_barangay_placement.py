"""Reviewed asset identity, exact administrative clipping and gap preservation."""
import hashlib
import json

import pytest
from shapely.geometry import box, mapping, shape
from shapely import union_all

from app.services.barangay_boundary_service import BarangayBoundaryProvider
from app.services.news_road_placement_service import NewsRoadPlacementProvider
from app.services.news_placement_preview_service import NewsPlacementPreviewService
from test_news_road_placement import claim, write_catalog
from test_news_placement_preview import service


def boundary_catalog(directory, polygon=None, **changes):
    directory.mkdir(exist_ok=True)
    payload = dict(format_version=1, source_id="synthetic-reviewed-boundary", source_url="https://example.org/fixture",
        source_sha256="a" * 64, snapshot_at="2026-09-01T00:00:00Z", verified_at="2026-09-02T00:00:00Z",
        verified_by="fixture-reviewer", attribution="Synthetic geometry; not an official boundary",
        records=[dict(city="Pasig City", barangay="Ugong", psgc_code="1381200029",
            geometry=mapping(polygon if polygon is not None else box(120.999, 14.6302, 121.001, 14.6308)))])
    payload.update(changes)
    raw = json.dumps(payload).encode()
    (directory / "boundaries.json").write_bytes(raw)
    (directory / "manifest.json").write_text(json.dumps({"catalog_sha256": hashlib.sha256(raw).hexdigest()}))
    return BarangayBoundaryProvider(directory)


def test_barangay_clips_both_partial_and_disconnected_sections(tmp_path):
    initial = service(tmp_path, city="Pasig")
    boundary = union_all([box(120.999, 14.6301, 121.001, 14.6303), box(120.999, 14.6307, 121.001, 14.6309)])
    provider = boundary_catalog(tmp_path / "barangays", boundary)
    roads = NewsRoadPlacementProvider(initial.roads.directory, provider)
    evidence = claim(span=None, canonical_city="Pasig City", canonical_barangay="Ugong", local_area_raw="Barangay Ugong", depth_canonical="knee")
    placement = roads.resolve(evidence)
    assert placement.barangay_boundary_status == "available"
    assert placement.barangay_psgc_code == "1381200029" and placement.barangay_source_id == provider.catalog.source_id
    assert len(placement.candidates) == 2
    assert all(boundary.covers(shape(c.centerline_geojson)) for c in placement.candidates)
    assert all(c.cross_streets == [[], []] for c in placement.candidates)
    engine = NewsPlacementPreviewService(roads, initial.noah, initial.history_path)
    preview = engine.preview(evidence, placement)
    assert len(preview.candidates) == 2 and all(c.article_place_level == 1 for c in preview.candidates)
    assert preview.reported_severity == "medium"
    assert all(c.preview_geometry and c.modeled_fragments for c in preview.candidates)
    assert not preview.may_affect_routing and not preview.proves_current_flood
    assert engine.preview(evidence).model_dump() == preview.model_dump()


def test_reported_span_keeps_anchor_evidence_after_boundary_clipping(tmp_path):
    initial = service(tmp_path, city="Pasig")
    roads = NewsRoadPlacementProvider(initial.roads.directory, boundary_catalog(tmp_path / "barangays"))
    engine = NewsPlacementPreviewService(roads, initial.noah, initial.history_path)
    preview = engine.preview(claim(canonical_city="Pasig", canonical_barangay="Ugong"))
    assert preview.status == "predicted_candidate" and preview.placement_kind == "reported"
    assert preview.candidates[0].cross_streets == [[], []]
    assert preview.candidates[0].article_place_level == 3
    assert not preview.candidates[0].matching_history


@pytest.mark.parametrize("failure", ["checksum", "identity", "clock", "geometry", "duplicate", "parent", "missing", "outside"])
def test_invalid_or_missing_boundaries_never_broaden_to_city(tmp_path, failure):
    initial = service(tmp_path, city="Pasig")
    target = tmp_path / "barangays"
    changes = {}
    if failure == "clock":
        changes["verified_at"] = "2026-08-01T00:00:00Z"
    polygon = box(121.1, 14.63, 121.11, 14.64) if failure == "outside" else None
    provider = boundary_catalog(target, polygon, **changes)
    if failure in {"identity", "geometry", "duplicate", "parent"}:
        payload = json.loads((target / "boundaries.json").read_bytes())
        if failure == "identity": payload["records"][0]["psgc_code"] = "1381600030"
        if failure == "parent": payload["records"][0]["city"] = "Quezon City"
        if failure == "geometry": payload["records"][0]["geometry"] = {"type": "Point", "coordinates": [121, 14.63]}
        if failure == "duplicate": payload["records"] *= 2
        boundary_catalog(target, records=payload["records"])
    if failure == "checksum": (target / "boundaries.json").write_bytes(b"corrupt")
    if failure == "missing": (target / "boundaries.json").unlink()
    provider = BarangayBoundaryProvider(target)
    roads = NewsRoadPlacementProvider(initial.roads.directory, provider)
    result = roads.resolve(claim(span=None, canonical_city="Pasig", canonical_barangay="Ugong"))
    assert result.status == "unresolved" and not result.candidates
    assert result.barangay_boundary_status == "unavailable"
    assert result.reason in {"invalid_barangay_boundary_catalog", "missing_valid_barangay_boundary"}
