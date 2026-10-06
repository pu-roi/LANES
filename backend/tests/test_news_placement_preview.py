"""Exact hazard geometry, location scoping, immutable preview and access checks."""
import gzip
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from shapely.geometry import LineString, Polygon, box, mapping

from app.api import deps
from app.core.limiter import limiter
from app.main import app
from app.services.noah_vector_catalog_service import NoahAssetError, NoahManifest, NoahVectorCatalog, metric_geometry, tile_keys
from app.services.news_placement_preview_service import NewsPlacementPreviewService
from test_news_road_placement import claim, write_catalog
from test_news_results import result_db
from test_news_browsing import evidence_db, staff


def noah_catalog(directory: Path, polygon=None) -> NoahVectorCatalog:
    directory.mkdir(exist_ok=True)
    bounds, size = (120.98, 14.60, 121.04, 14.68), 0.02
    scenarios = {}
    polygon = box(120.98, 14.60, 121.04, 14.68) if polygon is None else polygon
    for period in (5, 25, 100):
        target = directory / str(period)
        target.mkdir(exist_ok=True)
        hashes = {}
        for key in tile_keys(bounds, size):
            x, y = (int(v) for v in key.split(":"))
            tile = box(x * size, y * size, (x + 1) * size, (y + 1) * size)
            area = polygon.intersection(tile)
            # Empty intersection may be a GeometryCollection; store an empty polygon.
            area = area if area.geom_type in {"Polygon", "MultiPolygon"} else Polygon()
            payload = {"1": mapping(Polygon()), "2": mapping(Polygon()), "3": mapping(area)}
            raw = gzip.compress(json.dumps(payload).encode(), mtime=0)
            (target / f"{key.replace(':', '_')}.json.gz").write_bytes(raw)
            hashes[key] = hashlib.sha256(raw).hexdigest()
        scenarios[period] = dict(source_id=f"noah-fixture-{period}", archive_sha256="b" * 64, tiles=hashes)
    manifest = NoahManifest(tile_size=size, bounds=bounds, attribution="Project NOAH contributors",
                            license="ODbL-1.0", scenarios=scenarios)
    (directory / "manifest.json").write_text(manifest.model_dump_json())
    return NoahVectorCatalog(directory)


def service(tmp_path, *, polygon=None, city="Quezon City"):
    road_dir = tmp_path / "roads"
    road_dir.mkdir()
    roads = write_catalog(road_dir, cities=[dict(name=city, relation_id=106569,
                          boundary=mapping(box(120.99, 14.60, 121.03, 14.67)))])
    noah = noah_catalog(tmp_path / "noah", polygon)
    history = tmp_path / "history.csv"
    history.write_text("source_year,source_record_no,barangay_canonical,street_normalized,landmark_normalized\n"
                       "2024,1,Rosario,Santo Domingo Avenue,Atok Street\n"
                       "2025,2,Other,Santo Domingo Avenue,Unmapped Place\n"
                       "2025,3,Rosario,G. Raymundo Avenue,Atok Street\n")
    return NewsPlacementPreviewService(roads, noah, history)


def test_exact_intersection_preserves_holes_and_never_uses_return_period_as_depth(tmp_path):
    outer = box(120.999, 14.629, 121.001, 14.632)
    hole = box(120.9995, 14.6303, 121.0005, 14.6307)
    provider = noah_catalog(tmp_path, outer.difference(hole))
    line = LineString([(121, 14.630), (121, 14.631)])
    results = provider.overlaps(line)
    length = metric_geometry(line).length
    for period in (5, 25, 100):
        assert results[period][3] == pytest.approx(length * 0.6, abs=0.001)
        assert results[period][1] == results[period][2] == 0


def test_preview_returns_disconnected_fragments_with_stable_scenario_provenance(tmp_path):
    outer = box(120.999, 14.629, 121.001, 14.632)
    hole = box(120.9995, 14.6303, 121.0005, 14.6307)
    engine = service(tmp_path, polygon=outer.difference(hole))
    evidence = claim(depth_canonical="knee")
    original = evidence.model_dump()
    preview = engine.preview(evidence)
    candidate = preview.candidates[0]
    display = candidate.preview_geometry
    assert display["type"] == "MultiLineString" and len(display["coordinates"]) == 2
    assert candidate.fragment_status == "available" and len(candidate.modeled_fragments) == 6
    gap = LineString([(121, 14.6304), (121, 14.6306)])
    from shapely.geometry import shape
    assert not shape(display).intersects(gap)
    assert preview.reported_severity == "medium"  # NOAH fixture has class 3, not reported high severity.
    assert evidence.model_dump() == original
    assert len({f.fragment_id for f in candidate.modeled_fragments}) == 6
    for f in candidate.modeled_fragments:
        assert f.noah_source_id == f"noah-fixture-{f.return_period}"
        assert f.noah_archive_sha256 == "b" * 64 and f.hazard_class == 3
    assert engine.preview(evidence).model_dump_json() == preview.model_dump_json()
    assert not preview.may_affect_routing and not preview.proves_current_flood


def test_excess_fragmentation_returns_explicit_failure_without_partial_map(tmp_path):
    from shapely import union_all
    pieces = union_all([box(120.999, 14.63 + i * .001 / 180, 121.001,
                            14.63 + i * .001 / 180 + .0000025) for i in range(180)])
    preview = service(tmp_path, polygon=pieces).preview(claim())
    assert preview.status == "source_unavailable" and preview.reason == "noah_fragment_limit"
    assert preview.selected_candidate_id is None
    assert all(c.preview_geometry is None and c.modeled_fragments == []
               and c.fragment_status == "source_unavailable" for c in preview.candidates)


def test_unknown_depth_and_point_contact_never_invent_zone_severity(tmp_path):
    engine = service(tmp_path, polygon=box(121, 14.631, 121.001, 14.632))
    preview = engine.preview(claim())
    assert preview.reported_severity is None
    assert preview.candidates[0].fragment_status == "no_modeled_overlap"
    assert preview.candidates[0].preview_geometry is None
    assert preview.candidates[0].modeled_fragments == []


def test_tile_boundary_does_not_double_count(tmp_path):
    provider = noah_catalog(tmp_path)
    line = LineString([(121, 14.62), (121, 14.64)])
    assert provider.overlaps(line)[5][3] == pytest.approx(metric_geometry(line).length)


@pytest.mark.parametrize("failure", ["missing", "tampered", "extent"])
def test_missing_corrupt_and_uncovered_assets_are_not_zero_overlap(tmp_path, failure):
    provider = noah_catalog(tmp_path)
    line = LineString([(121, 14.630), (121, 14.631)])
    key = tile_keys(line.bounds, 0.02)[0].replace(":", "_")
    path = tmp_path / "5" / f"{key}.json.gz"
    if failure == "missing":
        path.unlink()
    elif failure == "tampered":
        path.write_bytes(b"bad")
    else:
        line = LineString([(122, 14.630), (122, 14.631)])
    with pytest.raises(NoahAssetError):
        provider.overlaps(line)


def test_reported_span_keeps_current_facts_and_source_identity(tmp_path):
    engine = service(tmp_path)
    evidence = claim(depth_raw="approximately 19 inches", condition="active", road_passability="passable_with_caution")
    original = deepcopy(evidence.model_dump())
    preview = engine.preview(evidence)
    assert preview.status == "predicted_candidate" and preview.placement_kind == "reported"
    assert len(preview.candidates) == 1
    assert preview.noah_catalog_sha256 and set(preview.noah_source_ids) == {5, 25, 100}
    assert preview.osm_catalog_sha256 == engine.roads.digest and preview.city_relation_id == 106569
    assert preview.history_status == "not_applicable" and preview.history_sha256 is None
    assert not preview.may_affect_routing and not preview.proves_current_flood
    assert evidence.model_dump() == original


def test_pasig_history_matches_road_and_crossing_without_inventing_events(tmp_path):
    engine = service(tmp_path, city="Pasig")
    preview = engine.preview(claim(canonical_city="City of Pasig"))
    assert preview.status == "predicted_candidate"
    assert preview.history_status == "available" and preview.history_sha256
    assert [row.source_record_no for row in preview.candidates[0].matching_history] == ["1"]
    assert [row.source_record_no for row in preview.unmatched_history] == ["2"]


def test_parent_city_qualifier_is_not_an_ungrounded_landmark(tmp_path):
    preview = service(tmp_path, city="Pasig").preview(claim(span=None,
        canonical_city="City of Pasig", local_area_raw="Pasig City"))
    assert preview.candidates and preview.reason != "local_place_not_grounded"
    assert all(c.article_place_level == 0 for c in preview.candidates)


def test_non_pasig_never_reads_historical_rows_even_same_road(tmp_path):
    engine = service(tmp_path)
    engine.history_path.unlink()
    preview = engine.preview(claim())
    assert preview.history_status == "not_applicable" and not preview.unmatched_history
    assert not preview.candidates[0].matching_history


def test_pasig_missing_history_remains_visible_and_unselected(tmp_path):
    initial = service(tmp_path, city="Pasig")
    engine = NewsPlacementPreviewService(initial.roads, initial.noah, tmp_path / "missing.csv")
    preview = engine.preview(claim(canonical_city="Pasig"))
    assert preview.history_status == "source_unavailable"
    assert preview.selected_candidate_id is None and preview.reason == "pasig_history_unavailable"
    assert preview.candidates[0].modeled_overlap_m


@pytest.mark.parametrize("changes", [{"is_forecast": True}, {"is_negated": True},
    {"uncertainty_reasons": ["photo_caption_only"]}, {"uncertainty_reasons": ["location_context_only"]}])
def test_non_observation_evidence_never_selects_a_section(tmp_path, changes):
    preview = service(tmp_path).preview(claim(**changes))
    assert preview.selected_candidate_id is None
    assert preview.reason == "claim_is_not_reported_flood_evidence"


def test_incomplete_candidates_and_missing_barangay_boundary_stay_unresolved(tmp_path):
    engine = service(tmp_path)
    evidence = claim()
    roads = engine.roads.resolve(evidence)
    roads.candidates_truncated = True
    roads.total_candidate_count = 26
    preview = engine.preview(evidence, roads)
    assert preview.selected_candidate_id is None and preview.reason == "candidate_set_truncated"
    assert engine.preview(claim(canonical_barangay="Rosario")).reason == "missing_valid_barangay_boundary"


def test_unavailable_noah_preserves_candidates_and_error(tmp_path):
    original = service(tmp_path)
    engine = NewsPlacementPreviewService(original.roads, NoahVectorCatalog(tmp_path / "missing"))
    preview = engine.preview(claim())
    assert preview.status == "source_unavailable" and preview.candidates
    assert preview.reason == "noah_catalog_not_configured"
    assert preview.selected_candidate_id is None


def test_source_revision_fits_storage_and_changes_without_changing_article(tmp_path, monkeypatch):
    from app.crud.news_processing import current_pipeline_version
    from app.services import news_placement_preview_service, news_road_placement_service
    engine = service(tmp_path)
    monkeypatch.setattr(news_road_placement_service, "get_news_road_placement_provider", lambda: engine.roads)
    monkeypatch.setattr(news_placement_preview_service, "get_news_placement_preview_service", lambda: engine)
    before = current_pipeline_version()
    assert len(before) <= 100
    engine.noah.digest = "c" * 64
    noah_changed = current_pipeline_version()
    assert noah_changed != before
    engine.history_digest = "d" * 64
    assert current_pipeline_version() != noah_changed


def test_corrupt_asset_revision_recovers_with_same_manifest_after_repair(tmp_path):
    initial = noah_catalog(tmp_path)
    valid = initial.revision
    path = next((tmp_path / "5").glob("*.json.gz"))
    raw = path.read_bytes()
    path.write_bytes(b"broken")
    assert NoahVectorCatalog(tmp_path).revision != valid
    path.write_bytes(raw)
    assert NoahVectorCatalog(tmp_path).revision == valid


def test_missing_history_columns_are_visible_for_pasig(tmp_path):
    initial = service(tmp_path, city="Pasig")
    initial.history_path.write_text("unrelated,columns\n1,2\n")
    engine = NewsPlacementPreviewService(initial.roads, initial.noah, initial.history_path)
    preview = engine.preview(claim(canonical_city="Pasig"))
    assert preview.history_status == "source_unavailable"
    assert preview.selected_candidate_id is None


def test_zero_modeled_overlap_is_not_current_safety_or_selected_road(tmp_path):
    preview = service(tmp_path, polygon=Polygon()).preview(claim(span=None))
    assert preview.selected_candidate_id is None
    assert preview.reason == "no_modeled_overlap_or_explicit_span"
    assert not preview.proves_current_flood and not preview.may_affect_routing


@pytest.mark.asyncio
async def test_saved_extraction_attaches_typed_preview_without_auditor(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    from app.schemas.news_extraction import NewsArticleExtractorInput
    from app.services import news_placement_preview_service, news_road_placement_service
    from app.services.news_discovery_service import extract_captured_news_article
    from app.services.hybrid_extraction_service import HybridExtractionService
    engine = service(tmp_path)
    monkeypatch.setattr(news_road_placement_service, "get_news_road_placement_provider", lambda: engine.roads)
    monkeypatch.setattr(news_placement_preview_service, "get_news_placement_preview_service", lambda: engine)
    monkeypatch.setattr(HybridExtractionService, "audit_claim_with_llm", lambda *a, **k: pytest.fail("Auditor invoked"))
    body = "As of 10 AM, knee-deep flooding on Sto. Domingo Avenue between Atok and Calamba Streets in Quezon City."
    result = await extract_captured_news_article(NewsArticleExtractorInput(article_id=1,
        canonical_url="https://example.org/test", publisher="fixture", title="Flood", article_text=body,
        published_at=datetime(2026, 10, 2, 3, tzinfo=timezone.utc)))
    assert result.error is None
    selected = [c for c in result.extraction.claims if c.placement_preview.selected_candidate_id]
    assert selected and all(c.depth_canonical == "knee" for c in selected)
    assert all(c.action_type != "auto_approved" for c in result.extraction.claims)


@pytest.mark.asyncio
async def test_preview_endpoint_auth_identity_and_no_database_writes(result_db):
    path = "/api/v1/admin/news/results/1/0/placement"
    baseline = len(result_db)
    limiter.reset()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get(path)).status_code == 401
        app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Commuter"))
        assert (await client.get(path)).status_code == 403
        staff()
        response = await client.get(path)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["run_id"] == 1 and payload["claim_index"] == 0 and payload["read_only"]
        assert payload["evidence_pipeline_version"] == "test-old"
        assert payload["claim"]["raw_place_name"] == "Flood 100% here"
        assert payload["preview"]["reason"] == "no_reported_road"
        limiter.reset()
        assert (await client.get("/api/v1/admin/news/results/999/0/placement")).status_code == 404
        assert (await client.get("/api/v1/admin/news/results/1/999/placement")).status_code == 404
        assert (await client.get("/api/v1/admin/news/results/0/0/placement")).status_code == 422
    assert len(result_db) == baseline
