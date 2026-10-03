"""Claim browsing keeps artifact ordinals separate and never infers lifecycle."""

from copy import deepcopy
from datetime import timedelta

import httpx
import pytest

from app.api import deps
from app.core.database import get_db
from app.main import app
from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_discovery_service import extraction_input_snapshot
from test_news_browsing import NOW, evidence_db, staff  # Reuse isolated evidence/auth fixtures.


@pytest.fixture
def result_db(evidence_db, request):
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    try:
        old = db.get(NewsExtractionRun, 1)
        result = deepcopy(old.result)
        result["extracted_at"] = NOW.isoformat()
        base = deepcopy(result["claims"][0])
        base.update(raw_place_name="Flood 100% here", canonical_city="City of Pasig", condition="active",
                    road_placement={"status": "unresolved", "reason": "no_reported_road"})
        result["claims"] = [base, {**deepcopy(base), "condition": "receding", "road_placement": None},
                            {**deepcopy(base), "raw_place_name": "Other road", "road_placement": {"status": "bounded_candidate", "reason": "one_candidate"}}]
        old.result = result
        newest = db.get(NewsExtractionRun, 2)
        variant = getattr(request, "param", "ready")
        if variant != "failed":
            newest.status = "completed"
            newest.result = deepcopy(result)
            newest.error_code = None
            if variant == "questionable":
                questionable = deepcopy(base)
                questionable.update(raw_place_name="Taguig", condition="unknown", depth_raw=None,
                    depth_formatted=None, road_passability="unknown", evidence_sentence="A flood-control project in Taguig was discussed.")
                newest.result["claims"] = [deepcopy(base), questionable,
                    {**deepcopy(base), "raw_place_name": "A whole article sentence mistaken for a place name. " * 4},
                    {**deepcopy(base), "is_forecast": True}, {**deepcopy(base), "is_negated": True},
                    {**deepcopy(base), "is_historical": True}]
            elif variant == "empty":
                newest.result["claims"] = []
            elif variant == "irrelevant":
                newest.result["claims"] = [{**deepcopy(base), "evidence_sentence": "Officials in Pasig City discussed flooding and drainage projects."}]
            elif variant == "caption":
                newest.result["claims"] = [{**deepcopy(base), "uncertainty_reasons": ["photo_caption_only"]}]
            elif variant == "metadata":
                newest.result["is_metadata_only"] = True
            elif variant == "errors":
                newest.result["errors"] = ["incomplete extraction"]
        source = NewsArticleExtractorInput(article_id=2, title="Original Philstar title", canonical_url="https://example.org/2",
            publisher="feedspot-05", published_at=NOW - timedelta(days=1), article_text="Original captured text")
        snapshot, fingerprint = extraction_input_snapshot(source)
        db.add(NewsArticleVersion(id=3, article_id=2, input_snapshot=snapshot, input_fingerprint=fingerprint, created_at=NOW))
        newer = deepcopy(result)
        newer.update(article_id=2, extracted_at=(NOW + timedelta(hours=1)).isoformat(), claims=[{**deepcopy(base), "raw_place_name": "Philstar place"}])
        db.add(NewsExtractionRun(id=3, article_version_id=3, pipeline_version="test-third", mode="rules_only", status="completed",
            attempt_count=1, result=newer, created_at=NOW, updated_at=NOW, completed_at=NOW))
        db.commit()
    finally:
        generator.close()
    baseline = len(evidence_db)
    yield evidence_db
    assert len(evidence_db) == baseline, "Result reads must not write"


@pytest.mark.asyncio
async def test_results_guard_filters_order_and_separate_claims(result_db):
    from types import SimpleNamespace
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        paths = ["/api/v1/admin/news/results", "/api/v1/admin/news/results/1/0"]
        for path in paths:
            assert (await client.get(path)).status_code == 401
        app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Commuter"))
        for path in paths:
            assert (await client.get(path)).status_code == 403
        staff()
        async def read(**params):
            response = await client.get(paths[0], params=params)
            assert response.status_code == 200, response.text
            return response.json()
        page = await read(page_size=2)
        assert page["total"] == 4 and page["pages"] == 2
        assert [item["key"] for item in page["items"]] == ["3:0", "2:0"]
        second = await read(page_size=2, page=2)
        assert [item["key"] for item in second["items"]] == ["2:1", "2:2"]
        assert (await read(page_size=2, page=999))["page"] == 2
        assert [item["key"] for item in (await read(order="publication_newest"))["items"]] == ["2:0", "2:1", "2:2", "3:0"]
        assert (await read(condition="receding"))["items"][0]["key"] == "2:1"
        assert (await read(placement="not_recorded"))["items"][0]["key"] == "2:1"
        assert (await read(placement="bounded_candidate"))["items"][0]["key"] == "2:2"
        assert (await read(publisher="feedspot-05"))["total"] == 1
        assert (await read(search="100%"))["total"] == 2
        assert (await read(search="_"))["total"] == 0
        assert (await read(search="pasig"))["total"] == 4
        assert (await read(search="missing"))["items"] == []
        assert "article_text" not in page["items"][0]
        assert "candidates" not in page["items"][0]["claim"]["road_placement"]
        assert page["scope"] == "latest_reported_locations" and page["read_only"]
        for params in [{"page_size":51}, {"page":0}, {"search":"x"*201}, {"condition":"approved"}, {"placement":"active_zone"}, {"order":"bogus"}]:
            assert (await client.get(paths[0], params=params)).status_code == 422


@pytest.mark.asyncio
async def test_result_detail_uses_artifact_capture_and_unavailable_lifecycle(result_db):
    staff()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/admin/news/results/1/1")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["item"]["key"] == "1:1"
        assert data["item"]["title"] == data["captured_input"]["title"] == "Older headline"
        assert "abot-tuhod" in data["captured_input"]["article_text"]
        assert data["claim"]["raw_place_name"] == "Flood 100% here"
        assert data["claim"]["condition"] == "receding"
        assert data["item"]["summary"]["condition"] == "Water receding"
        assert data["item"]["summary"]["map_status"] == "Map location not checked"
        assert data["item"]["captured_at"].startswith("2026-10-02")
        assert data["lifecycle_status"] == "not_available" and data["read_only"] is True
        for path in ["1/999", "2/999", "999/0"]:
            assert (await client.get("/api/v1/admin/news/results/"+path)).status_code == 404
        assert (await client.get("/api/v1/admin/news/results/1/-1")).status_code == 422


@pytest.mark.asyncio
async def test_result_storage_errors_are_sanitized(result_db, monkeypatch):
    from sqlalchemy.exc import OperationalError
    from app.api.v1.endpoints import admin_news
    staff()
    def fail(*args, **kwargs):
        raise OperationalError("private DB connection", {}, Exception("private details"))
    monkeypatch.setattr(admin_news, "browse_news_results", fail)
    monkeypatch.setattr(admin_news, "read_news_result", fail)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        for path in ["/api/v1/admin/news/results", "/api/v1/admin/news/results/1/0"]:
            response = await client.get(path)
            assert response.status_code == 503
            assert response.json()["detail"] == "News result storage is unavailable"
            assert "private" not in response.text


@pytest.mark.parametrize("flags, expected", [({}, "Flooding reported"), ({"is_forecast": True}, "Forecast only"), ({"is_negated": True}, "No flooding reported"), ({"is_historical": True}, "Historical flood reference")])
def test_plain_summary_preserves_missing_flood_time_and_source_qualifiers(flags, expected):
    from app.schemas.news_extraction import ExtractedClaim
    from app.services.news_presentation_service import summarize_news_claim
    claim = ExtractedClaim(raw_place_name="Ortigas Avenue", canonical_city="City of Pasig", place_char_start=0,
        place_char_end=14, evidence_sentence="Flooding reported along Ortigas Avenue.", evidence_sentence_offset=(0, 46),
        condition="active", event_time_kind="unspecified", road_segment_raw="between two intersections", **flags)
    summary = summarize_news_claim(claim)
    assert summary.location == "Ortigas Avenue · between two intersections" and summary.area == "City of Pasig"
    assert summary.location_qualifier is None
    assert summary.water_level == "Not stated in article"
    assert summary.flood_time is None and summary.flood_time_label == "Flood time in article"
    assert summary.condition == expected


def test_summary_keeps_article_flood_clock_separate():
    from app.schemas.news_extraction import ExtractedClaim
    from app.services.news_presentation_service import summarize_news_claim
    claim = ExtractedClaim(raw_place_name="Ortigas", place_char_start=0, place_char_end=7,
        evidence_sentence="At 4 PM, knee-deep flooding was reported in Ortigas.", evidence_sentence_offset=(0, 51),
        condition="active", depth_raw="knee-deep", depth_formatted="Knee-deep (0.5 m)", event_time_kind="observation",
        event_time_resolved=NOW - timedelta(hours=2))
    summary = summarize_news_claim(claim)
    assert summary.flood_time == NOW - timedelta(hours=2)
    assert summary.flood_time_label == "Flood observed in article"
    assert summary.water_level == "Knee-deep (0.5 m)"


@pytest.mark.asyncio
async def test_legacy_false_results_are_filtered_before_pages_and_preserved_in_history(evidence_db):
    """Old stored active flags must not bypass the corrected evidence policy."""
    from app.schemas.news_extraction import ExtractedClaim
    from app.services.news_presentation_service import claim_reading_reason
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    try:
        old = db.get(NewsExtractionRun, 1)
        base = deepcopy(old.result["claims"][0])
        cases = [
            ("Quezon City", "City of Quezon", "1381300000", "The basin in Quezon City helps mitigate localized flooding during heavy rains."),
            ("Quezon City", "City of Quezon", "1381300000", "The school in Quezon City is regularly submerged during heavy downpours."),
            ("Manila", "City of Manila", "1380600000", "DPWH is constructing drainage facilities at UP-PGH in Manila to help address flooding."),
            ("Bangkok", None, None, "Bangkok residents waded through waist-deep flooding."),
            ("interior", "San Jacinto", "0504119009", "The interior ministry said residents were flooded."),
            ("Unknown site", None, None, "Flooding was reported at an unknown site."),
            # A conflicting PSGC code cannot be overridden by a city label.
            ("Laguna Street", "City of Pasig", "0504119009", "Streets are flooded in Pasig City."),
            ("Laguna Street", "City of Pasig", "1381400000", "A basin was installed to prevent flooding, but streets are flooded on Laguna Street in Pasig City."),
        ]
        claims = [{**deepcopy(base), "raw_place_name": place, "canonical_city": city,
                   "psgc_code": code, "evidence_sentence": sentence, "condition": "active",
                   "depth_raw": None, "depth_formatted": None} for place, city, code, sentence in cases]
        run = db.get(NewsExtractionRun, 2)
        run.status = "completed"
        run.result = {**deepcopy(old.result), "claims": claims}
        db.commit()
        assert [claim_reading_reason(ExtractedClaim.model_validate(c)) is None for c in claims] == [False] * 7 + [True]
    finally:
        generator.close()
    baseline = len(evidence_db)
    staff()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/admin/news/results", params={"page_size": 1, "page": 9})
        assert response.status_code == 200, response.text
        page = response.json()
        assert page["total"] == 1 and page["pages"] == 1 and page["page"] == 1
        assert page["items"][0]["key"] == "2:7"
        collection = (await client.get("/api/v1/admin/news/collection", params={"status": "all", "publisher": "feedspot-01"})).json()["items"][0]
        assert collection["location_count"] == 1 and collection["questionable_count"] == 7
        for index in range(7):
            history = await client.get(f"/api/v1/admin/news/results/2/{index}")
            assert history.status_code == 200
            assert history.json()["item"]["summary"]["reading_status"] == "needs_checking"
    assert len(evidence_db) == baseline


@pytest.mark.parametrize("result_db, expected_locations, expected_status, questionable", [
    ("failed", 0, "processing_failed", 0), ("questionable", 1, "needs_checking", 5),
    ("empty", 0, "excluded", 0), ("irrelevant", 0, "excluded", 0), ("caption", 0, "excluded", 0), ("metadata", 0, "needs_checking", 3),
    ("errors", 0, "needs_checking", 3), ("ready", 3, "ready", 0),
], indirect=["result_db"])
@pytest.mark.asyncio
async def test_collection_and_main_list_share_newest_evidence_gate(result_db, expected_locations, expected_status, questionable):
    staff()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        main = (await client.get("/api/v1/admin/news/results", params={"publisher": "feedspot-01"})).json()
        assert main["total"] == expected_locations
        assert all(item["run_id"] == 2 and item["summary"]["reading_status"] == "reported_location" for item in main["items"])
        response = await client.get("/api/v1/admin/news/collection", params={"status": "all", "publisher": "feedspot-01"})
        assert response.status_code == 200, response.text
        data = response.json()
        item = data["items"][0]
        assert item["collection_status"] == expected_status
        assert item["location_count"] == expected_locations and item["questionable_count"] == questionable
        assert "article_text" not in item
        assert data["counts"][expected_status] >= 1 and data["read_only"]
        attention = (await client.get("/api/v1/admin/news/collection", params={"publisher": "feedspot-01"})).json()
        assert attention["total"] == (0 if expected_status in {"ready", "excluded"} else 1)
        # Even when the newest attempt fails, older evidence stays accessible in history.
        assert (await client.get("/api/v1/admin/news/results/1/0")).status_code == 200


@pytest.mark.asyncio
async def test_collection_guard_literal_search_pagination_and_errors(result_db, monkeypatch):
    from types import SimpleNamespace
    from sqlalchemy.exc import OperationalError
    from app.api.v1.endpoints import admin_news
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        path = "/api/v1/admin/news/collection"
        assert (await client.get(path)).status_code == 401
        app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Commuter"))
        assert (await client.get(path)).status_code == 403
        staff()
        page = (await client.get(path, params={"status": "all", "page_size": 2, "page": 999})).json()
        assert page["total"] == 3 and page["page"] == 2 and page["items"][0]["id"] == 1
        assert (await client.get(path, params={"status": "all", "search": "100%"})).json()["total"] == 1
        assert (await client.get(path, params={"search": "_"})).json()["total"] == 0
        for params in [{"status": "approved"}, {"page_size": 51}, {"page": 0}, {"search": "x" * 201}]:
            assert (await client.get(path, params=params)).status_code == 422
        def fail(*args, **kwargs):
            raise OperationalError("private connection", {}, Exception("private details"))
        monkeypatch.setattr(admin_news, "browse_news_collection", fail)
        response = await client.get(path)
        assert response.status_code == 503 and response.json()["detail"] == "News collection storage is unavailable"
        assert "private" not in response.text


def test_specific_intersection_heading_and_unknown_facts():
    from app.schemas.news_extraction import ExtractedClaim
    from app.services.news_presentation_service import summarize_news_claim
    claim = ExtractedClaim(raw_place_name="NS Amoranto", road_segment_raw="NS Amoranto cor Don Jose St.",
        canonical_barangay="Sienna", canonical_city="Quezon City", local_area_raw="Sienna",
        place_char_start=0, place_char_end=11, evidence_sentence="Flooding was reported along NS Amoranto cor Don Jose St.",
        evidence_sentence_offset=(0, 54), condition="active")
    summary = summarize_news_claim(claim)
    assert summary.location == "NS Amoranto cor Don Jose St."
    assert summary.area == "Sienna, Quezon City" and summary.location_qualifier is None
    assert summary.reading_status == "reported_location"
    assert summary.water_level == "Not stated in article" and summary.flood_time is None
    # A neighbourhood qualifier must not replace a reported road when no segment is saved.
    broad_road = claim.model_copy(update={"road_segment_raw": None})
    assert summarize_news_claim(broad_road).location == "NS Amoranto"
