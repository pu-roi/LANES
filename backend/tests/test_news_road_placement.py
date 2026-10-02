"""Article placement preserves bounds, source identity, and activation safety."""
import gzip
import hashlib
import json
from datetime import datetime, timezone

import pytest
from shapely.geometry import box, mapping

from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from app.services.news_road_placement_service import NewsRoadPlacementProvider


def ways() -> list[dict]:
    return [
        dict(osm_id=10, name="Santo Domingo Avenue", nodes=[(1,121,14.63),(2,121,14.6305),(3,121,14.631)]),
        dict(osm_id=20, name="Atok Street", nodes=[(4,120.999,14.63),(1,121,14.63)]),
        dict(osm_id=30, name="Calamba Street", nodes=[(3,121,14.631),(5,121.001,14.631)]),
    ]


def write_catalog(directory, road_ways=None, **changes):
    payload = dict(format_version=1, source_id="osm-ncr:fixture", snapshot_at="2026-09-27T00:56:56Z",
        osm_sha256="a"*64, attribution="OpenStreetMap contributors",
        cities=[dict(name="Quezon City", relation_id=106569, boundary=mapping(box(120.99,14.60,121.03,14.67)))],
        ways=road_ways or ways())
    payload.update(changes)
    blob=gzip.compress(json.dumps(payload).encode(),mtime=0)
    (directory/"roads.json.gz").write_bytes(blob)
    (directory/"manifest.json").write_text(json.dumps(dict(catalog_sha256=hashlib.sha256(blob).hexdigest())))
    return NewsRoadPlacementProvider(directory)


def claim(span="between Atok and Calamba Streets", **changes):
    values=dict(raw_place_name="Sto. Domingo Avenue", canonical_road="Sto. Domingo Avenue",
        canonical_city="Quezon City", road_segment_raw=span, place_type="street", place_char_start=0,
        place_char_end=19, evidence_sentence="Flooding on Sto. Domingo Avenue.", evidence_sentence_offset=(0,31))
    values.update(changes)
    return ExtractedClaim(**values)


def test_explicit_span_has_source_identified_centerline_and_no_activation(tmp_path):
    result=write_catalog(tmp_path).resolve(claim())
    assert result.status=="bounded_candidate" and result.total_candidate_count==1
    assert result.city_relation_id==106569 and result.snapshot_at.tzinfo
    assert result.catalog_sha256 and result.osm_sha256=="a"*64
    assert result.candidates[0].osm_way_ids==[10]
    assert result.candidates[0].centerline_geojson["coordinates"]==[[121,14.63],[121,14.6305],[121,14.631]]
    assert not result.may_affect_routing and not result.proves_current_flood


def test_broad_road_never_selects_even_a_single_mapped_section(tmp_path):
    result=write_catalog(tmp_path).resolve(claim(span=None))
    assert result.status=="ambiguous" and result.total_candidate_count==1
    assert result.reason=="reported_road_extent_unbounded"
    assert result.candidates[0].kind=="road_section"


@pytest.mark.parametrize("changes,reason",[
    ({"canonical_barangay":"Santo Domingo"},"missing_valid_barangay_boundary"),
    ({"canonical_city":"City of Pasig"},"reported_city_not_covered"),
    ({"canonical_road":None},"no_reported_road"),
    ({"road_segment_raw":"near Atok Street"},"missing_explicit_bounded_span"),
])
def test_missing_context_never_falls_back_to_whole_road(tmp_path,changes,reason):
    result=write_catalog(tmp_path).resolve(claim(**changes))
    assert result.status=="unresolved" and result.reason==reason and not result.candidates


def test_alternative_carriageway_is_not_hidden_by_shorter_path(tmp_path):
    roads=ways()+[dict(osm_id=11,name="Santo Domingo Avenue",nodes=[(1,121,14.63),(6,121.001,14.6305),(3,121,14.631)])]
    result=write_catalog(tmp_path,roads).resolve(claim())
    assert result.reason=="multiple_named_road_paths" and not result.candidates


@pytest.mark.parametrize("change",["checksum","node_conflict","naive_clock","duplicate_city"])
def test_bad_catalog_returns_visible_source_failure(tmp_path,change):
    roads=ways()
    options={}
    if change=="node_conflict": roads[1]["nodes"][-1]=(1,121.002,14.63)
    if change=="naive_clock":options["snapshot_at"]="2026-09-27T00:56:56"
    if change=="duplicate_city":options["cities"]=[dict(name="Quezon City",relation_id=106569,boundary=mapping(box(120.99,14.60,121.03,14.67)))]*2
    provider=write_catalog(tmp_path,roads,**options)
    if change=="checksum":(tmp_path/"roads.json.gz").write_bytes(b"changed")
    result=provider.resolve(claim())
    assert result.status=="source_unavailable" and not result.candidates


def test_missing_catalog_is_a_visible_coverage_gap(tmp_path):
    result=NewsRoadPlacementProvider(tmp_path).resolve(claim())
    assert result.status=="source_unavailable" and result.reason=="osm_catalog_not_configured"


@pytest.mark.parametrize("road",["Santo Domingo Avenue","Calamba Street"])
def test_missing_nodes_on_main_or_crossing_cannot_prove_unique_path(tmp_path,road):
    provider=write_catalog(tmp_path,incomplete_ways=[dict(osm_id=99,name=road,aliases=[])])
    result=provider.resolve(claim())
    assert result.reason=="incomplete_named_road_coverage" and not result.candidates


@pytest.mark.asyncio
async def test_actual_article_extraction_attaches_placement_to_evidence(tmp_path,monkeypatch):
    from app.services import news_road_placement_service
    from app.services.news_discovery_service import extract_captured_news_article
    from app.services.hybrid_extraction_service import HybridExtractionService
    provider=write_catalog(tmp_path)
    monkeypatch.setattr(news_road_placement_service,"get_news_road_placement_provider",lambda:provider)
    monkeypatch.setattr(HybridExtractionService,"audit_claim_with_llm",lambda *a,**k:pytest.fail("External audit invoked"))
    body="As of 10 AM, knee-deep flooding on Sto. Domingo Avenue between Atok and Calamba Streets in Quezon City."
    result=await extract_captured_news_article(NewsArticleExtractorInput(article_id=1,
        canonical_url="https://example.org/flood",publisher="fixture",title="Quezon City flood",article_text=body,
        published_at=datetime(2026,10,2,3,tzinfo=timezone.utc)))
    assert result.error is None
    bounded=[c for c in result.extraction.claims if c.road_placement.status=="bounded_candidate"]
    assert bounded and all(c.evidence_sentence in body for c in bounded)
    assert all(c.action_type!="auto_approved" for c in result.extraction.claims)


def test_map_revision_changes_processing_identity_without_rewriting_input(tmp_path,monkeypatch):
    from app.crud.news_processing import current_pipeline_version
    from app.services import news_road_placement_service
    first=write_catalog(tmp_path)
    monkeypatch.setattr(news_road_placement_service,"get_news_road_placement_provider",lambda:first)
    before=current_pipeline_version()
    second=write_catalog(tmp_path,snapshot_at="2026-10-01T00:00:00Z")
    monkeypatch.setattr(news_road_placement_service,"get_news_road_placement_provider",lambda:second)
    assert current_pipeline_version()!=before


def test_repaired_catalog_gets_new_revision_after_source_failure(tmp_path):
    failed = write_catalog(tmp_path)
    blob = (tmp_path/"roads.json.gz").read_bytes()
    (tmp_path/"roads.json.gz").write_bytes(b"broken")
    failed_revision = failed.revision
    assert failed_revision.startswith("bad-")
    (tmp_path/"roads.json.gz").write_bytes(blob)
    repaired = NewsRoadPlacementProvider(tmp_path)
    assert repaired.revision != failed_revision
    assert repaired.resolve(claim()).status == "bounded_candidate"
