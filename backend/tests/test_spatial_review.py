"""Mixed review reads are bounded, source-aware and never publish historical evidence."""
from copy import deepcopy
import json
from datetime import timedelta
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.api import deps
from app.core.database import get_db
from app.main import app
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.services import spatial_review_service
from test_news_browsing import NOW, evidence_db, staff


@pytest.fixture
def review_db(evidence_db, monkeypatch):
    monkeypatch.setattr(spatial_review_service, "review_clock", lambda: NOW)
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    # SQLite evidence fixtures deliberately have no PostGIS tables. A minimal
    # report table exercises the actual union/pagination SQL without spatial writes.
    db.execute(text("CREATE TABLE flood_reports (id INTEGER PRIMARY KEY, status TEXT, deleted_at DATETIME, created_at DATETIME, human_readable_location TEXT, barangay TEXT, city TEXT, raw_text TEXT, severity TEXT, depth TEXT, geometry TEXT)"))
    for id, status, deleted in [(2, "pending", None), (90, "pending", None), (91, "approved", None), (92, "pending", NOW)]:
        db.execute(text("INSERT INTO flood_reports VALUES (:id, :status, :deleted, :created, 'Test road', NULL, 'Pasig', 'User evidence', 'medium', 'knee', NULL)"),
            {"id": id, "status": status, "deleted": deleted, "created": NOW})
    run = db.get(NewsExtractionRun, 2)
    result = deepcopy(db.get(NewsExtractionRun, 1).result)
    run.status = "completed"
    base = result["claims"][0]
    result["claims"] = [deepcopy(base), {**deepcopy(base), "condition": "receding"}, {**deepcopy(base), "raw_place_name": "Other road"}]
    for claim in result["claims"]:
        claim.update(action_type="flagged_review", action_rationale="Exact affected section is unresolved.", event_time_resolved=None)
    run.result = result
    db.commit()
    generator.close()
    evidence_db.clear()
    yield evidence_db
    assert evidence_db == [], "Queue/detail reads must not write or invoke publication"


@pytest.mark.asyncio
async def test_combined_queue_auth_filters_pagination_identity_and_detail(review_db):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        root = "/api/v1/admin/review/items"
        members_path = "/api/v1/admin/review/groups/user_report:2/members"
        for path in (root, root + "/news_claim:2:0", members_path):
            assert (await client.get(path)).status_code == 401
        app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(role=SimpleNamespace(name="Commuter"))
        assert (await client.get(root)).status_code == 403
        assert (await client.get(members_path)).status_code == 403
        staff()
        page = (await client.get(root, params={"page_size": 2})).json()
        assert page["counts"] == {"all": 4, "user_reports": 2, "news_claims": 2}
        assert page["total"] == 4 and page["pages"] == 2
        second = (await client.get(root, params={"page_size": 2, "page": 2})).json()
        assert {item["key"] for item in page["items"] + second["items"]} == {
            "user_report:2", "user_report:90", "news_claim:2:0", "news_claim:2:2"}
        for source, total in (("news_claims", 2), ("user_reports", 2)):
            response = await client.get(root, params={"source": source})
            assert response.status_code == 200, response.text
            assert response.json()["total"] == total
        assert (await client.get(root, params={"page": 999, "page_size": 2})).json()["page"] == 2
        detail = (await client.get(root + "/news_claim:2:0")).json()
        assert detail["is_current_review"] and detail["news"]["claim"]["action_type"] == "flagged_review"
        assert detail["news_actions_available"] is False and detail["report"] is None
        assert (await client.get(root + "/news_claim:1:0")).json()["is_current_review"] is False
        assert (await client.get(root + "/news_claim:999:0")).status_code == 404
        assert (await client.get(members_path)).status_code == 200
        assert (await client.get("/api/v1/admin/review/groups/user_report:999/members")).status_code == 404
        assert (await client.get(members_path, params={"page": 0})).status_code == 422
        for params in ({"source": "bogus"}, {"page": 0}, {"page_size": 101}):
            assert (await client.get(root, params=params)).status_code == 422
        for key in ("news_claim:2:-1", "news_claim:0:0", "user_report:0", "bogus:2"):
            assert (await client.get(root + "/" + key)).status_code == 422


@pytest.mark.parametrize("change", [
    {"is_historical": True}, {"is_forecast": True}, {"is_negated": True},
    {"uncertainty_reasons": ["photo_caption_only"]}, {"uncertainty_reasons": ["location_context_only"]},
    {"action_type": "auto_approved"}, {"action_type": None}, {"condition": "subsided"},
    {"event_time_resolved": (NOW - timedelta(days=1)).isoformat()},
])
def test_news_exclusions_and_postgres_sql(review_db, change):
    from app.crud.spatial_review import review_rows
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    run = db.get(NewsExtractionRun, 2)
    result = deepcopy(run.result)
    result["claims"] = [{**result["claims"][0], **change}]
    run.result = result
    db.commit()
    review_db.clear()
    assert spatial_review_service.browse_spatial_review(db, source="news_claims", page=1, page_size=20).total == 0
    sql = str(review_rows(db, NOW).select().compile(dialect=postgresql.dialect()))
    assert "UNION ALL" in sql
    generator.close()


def test_newer_failure_does_not_fall_back_and_old_article_stays_out(review_db):
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    db.get(NewsExtractionRun, 2).status = "failed"
    db.commit()
    review_db.clear()
    page = spatial_review_service.browse_spatial_review(db, source="all", page=1, page_size=20)
    assert page.total == 2 and page.counts["news_claims"] == 0
    generator.close()


def test_reconstruction_admits_later_publication_but_keeps_observation_freshness(review_db):
    from app.crud.spatial_review import review_rows
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    run = db.get(NewsExtractionRun, 2)
    version = db.get(NewsArticleVersion, run.article_version_id)
    later = NOW + timedelta(hours=12)
    version.input_snapshot = {**version.input_snapshot, "published_at": later.isoformat()}
    result = deepcopy(run.result)
    result["claims"] = [{**result["claims"][0], "event_time_resolved": NOW.isoformat()}]
    run.result = result
    db.commit()
    review_db.clear()
    def news_count(**kwargs):
        rows = review_rows(db, NOW, **kwargs)
        return len(list(db.execute(select(rows).where(rows.c.source == "news_claim"))))
    assert news_count() == 0
    assert news_count(publication_admission_at=later) == 1
    result = deepcopy(run.result)
    result["claims"][0]["event_time_resolved"] = (NOW - timedelta(days=1)).isoformat()
    run.result = result
    db.commit()
    review_db.clear()
    assert news_count(publication_admission_at=later) == 0
    generator.close()


@pytest.mark.parametrize("publication,expected", [
    (NOW.isoformat(), 2), ((NOW - timedelta(hours=13)).isoformat(), 0),
    ((NOW + timedelta(hours=1)).isoformat(), 0), (None, 2),
])
def test_current_queue_clock_and_missing_observation_time(review_db, publication, expected):
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    version = db.get(NewsArticleVersion, 2)
    version.input_snapshot = {**version.input_snapshot, "published_at": publication}
    db.commit()
    review_db.clear()
    page = spatial_review_service.browse_spatial_review(db, source="news_claims", page=1, page_size=20)
    assert page.total == expected
    if publication is None:
        db.get(NewsArticle, 1).first_seen_at = NOW - timedelta(days=2)
        db.commit()
        review_db.clear()
        assert spatial_review_service.browse_spatial_review(db, source="news_claims", page=1, page_size=20).total == 0
    generator.close()


def test_native_postgres_query_shape_without_fetching_backlog():
    from app.crud.spatial_review import review_rows
    from unittest.mock import Mock
    db = Mock()
    db.get_bind.return_value.dialect.name = "postgresql"
    sql = str(review_rows(db, NOW).select().compile(dialect=postgresql.dialect()))
    assert "jsonb_array_elements" in sql and "UNION ALL" in sql
    assert "max(news_extraction_runs.id)" in sql
    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_search_matches_any_member_without_splitting_cross_boundary_group(review_db):
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    for id, road, city, barangay, severity, depth, longitude in [
        (2, "Alpha Road", "Pasig", "Maybunga", "medium", "knee", 121.08),
        (90, "Beta Road", "Cainta", "Rosario", "high", "waist", 121.0802),
    ]:
        db.execute(text("UPDATE flood_reports SET human_readable_location=:road, city=:city, barangay=:barangay, severity=:severity, depth=:depth, geometry=:geometry WHERE id=:id"),
            dict(id=id, road=road, city=city, barangay=barangay, severity=severity, depth=depth,
                geometry=json.dumps({"type": "Point", "coordinates": [longitude, 14.58]})))
    db.commit()
    review_db.clear()
    staff()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        root = "/api/v1/admin/review/items"
        for filters in ({"q": "report #90"}, {"q": "  BETA   ROSARIO  "}, {"city": "City of Cainta", "barangay": "Rosario", "severity": "high"}):
            response = await client.get(root, params={"source": "user_reports", "page": 99, "page_size": 1, **filters})
            assert response.status_code == 200, response.text
            result = response.json()
            assert result["total"] == 1 and result["item_total"] == 2 and result["page"] == 1
            card = result["items"][0]
            assert card["key"] == "user_report:2" and card["member_count"] == 2
            assert {row["report_id"] for row in card["members"]} == {2, 90}
            assert card["severity_levels"] == ["medium", "high"]
            assert set(card["depth_levels"]) == {"knee", "waist"}
            assert card["location_summary"] == "Alpha Road · Beta Road"
            assert "Rosario, Cainta" in card["area_summary"]
            assert result["counts"]["all"] == 4
        # City and barangay must belong to the same member, not different members.
        result = (await client.get(root, params={"source": "user_reports", "city": "Cainta", "barangay": "Maybunga"})).json()
        assert result["items"] == [] and result["item_total"] == 0
        assert result["facets"] == {"cities": ["Cainta", "Pasig"], "barangays": ["Rosario"]}
        members = (await client.get("/api/v1/admin/review/groups/user_report:90/members")).json()
        assert members["key"] == "user_report:2" and members["total"] == 2
    generator.close()


@pytest.mark.asyncio
async def test_queue_search_is_global_before_pagination_and_validated(review_db):
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    for id in range(100, 400):
        db.execute(text("INSERT INTO flood_reports VALUES (:id, 'pending', NULL, :created, 'Another road', 'Test barangay', 'Other city', :evidence, 'low', 'ankle', NULL)"),
            {"id": id, "created": NOW - timedelta(minutes=id), "evidence": "Find this distant page" if id == 399 else "Other evidence"})
    db.commit()
    review_db.clear()
    staff()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        root = "/api/v1/admin/review/items"
        result = (await client.get(root, params={"q": "distant page", "page_size": 1})).json()
        assert result["total"] == 1 and result["items"][0]["report_id"] == 399
        assert result["counts"]["user_reports"] == 302
        assert (await client.get(root, params={"q": "%"})).json()["total"] == 0
        result = (await client.get(root, params={"source": "news_claims", "severity": "unknown"})).json()
        assert result["total"] == 2
        assert (await client.get(root, params={"source": "news_claims", "severity": "high"})).json()["total"] == 0
        for filters in ({"q": "x" * 121}, {"city": "x" * 101}, {"barangay": "x" * 101}, {"severity": "bogus"}):
            assert (await client.get(root, params=filters)).status_code == 422
    generator.close()


@pytest.mark.asyncio
async def test_storage_failure_is_not_a_clear_queue(review_db, monkeypatch):
    from app.api.v1.endpoints import admin_review
    from sqlalchemy.exc import SQLAlchemyError
    def fail(*args, **kwargs):
        raise SQLAlchemyError("unavailable")
    monkeypatch.setattr(admin_review, "browse_spatial_review", fail)
    staff()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/admin/review/items")
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"]
