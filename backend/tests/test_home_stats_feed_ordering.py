"""Public-map consistency and chronological feed queries against local PostGIS.

Every write is contained in an outer transaction and rolled back after the test.
"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_current_user_optional
from app.api.v1.endpoints import public, reports
from app.core.database import engine, get_db
from app.core.limiter import limiter
from app.models.interaction import InteractionType
from app.crud.feed import get_feed_posts
from app.crud.report import create_flood_report, get_active_avoidance_zones
from app.services.flood_event_service import create_verified_event_with_zone, link_supporting_report
from app.services import configuration_service, public_stats_service

POLYGON = {"type": "Polygon", "coordinates": [[[121.08, 14.57], [121.081, 14.57],
    [121.081, 14.571], [121.08, 14.571], [121.08, 14.57]]]}


@pytest.fixture
def context(monkeypatch):
    assert make_url(str(engine.url)).host in {"localhost", "127.0.0.1", "::1"}
    connection = engine.connect()
    outer = connection.begin()
    db = Session(bind=connection, join_transaction_mode="create_savepoint", autoflush=False)
    policy = SimpleNamespace(automatic_expiry_enabled=True)
    monkeypatch.setattr(configuration_service, "read_configuration", lambda _db: policy)
    users = []
    for name in ("Commuter", "Super Admin", "DRRM Officer"):
        role = db.query(models.Role).filter_by(name=name).first()
        if role is None:
            role = models.Role(name=name)
            db.add(role)
            db.flush()
        token = uuid4().hex
        user = models.User(username=f"home_feed_{token}", email=f"{token}@example.test",
                           hashed_password="test-only", role_id=role.id)
        db.add(user)
        users.append(user)
    db.commit()
    app = FastAPI()
    app.state.limiter = limiter
    app.include_router(public.router, prefix="/public")
    app.include_router(reports.router, prefix="/reports")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user_optional] = lambda: None
    try:
        with TestClient(app) as client:
            yield SimpleNamespace(db=db, users=users, client=client, policy=policy)
    finally:
        db.close()
        outer.rollback()
        connection.close()


def submitted(context, status="pending"):
    report = create_flood_report(context.db, schemas.FloodReportCreate(
        raw_text="Home statistics test", source="direct_user", severity="medium",
        depth="knee", is_public=False, user_id=context.users[0].id,
    ))
    report.status = models.ReportStatus(status)
    context.db.commit()
    return report


def zone(context, *, source_report=None, staff=None):
    return create_verified_event_with_zone(context.db,
        schemas.FloodAvoidanceZoneCreate(geometry=POLYGON,
            curated_by_admin_id=staff.id if staff else None), "medium", "knee",
        source_report=source_report, credit_reputation=False)[1]


def test_home_and_visit_counts_match_map_for_all_sources_and_merged_reports(context):
    initial_ids = {z.id for z in get_active_avoidance_zones(context.db)}
    user_zone = zone(context, source_report=submitted(context))
    official = [zone(context, staff=u) for u in context.users[1:]]
    # Multiple approved supporting reports must not count the same map zone twice.
    extra = submitted(context)
    link_supporting_report(context.db, extra, user_zone.flood_event, user_zone,
                           acted_by_user_id=context.users[1].id, credit_reputation=False)
    submitted(context, "pending")
    submitted(context, "rejected")
    submitted(context, "approved")  # No operational zone: not visible on the map.
    expected = initial_ids | {user_zone.id, *(z.id for z in official)}
    map_response = context.client.get("/reports/active-zones")
    assert map_response.status_code == 200, map_response.text
    assert {z["id"] for z in map_response.json()} == expected
    stats = context.client.get("/public/stats").json()
    today = datetime.now(timezone.utc).date()
    today_zones = [z for z in map_response.json()
        if datetime.fromisoformat(z["created_at"].replace("Z", "+00:00")).astimezone(timezone.utc).date() == today]
    assert stats["daily_verified_reports"] == len(today_zones)
    response = context.client.post("/public/visits", json={"visitor_id": str(uuid4())},
        headers={"user-agent": "Mozilla/5.0 Chrome/120.0"})
    assert response.status_code == 200, response.text
    assert response.json()["daily_verified_reports"] == len(today_zones)
    assert response.json()["total_visitors"] >= stats["total_visitors"]


def test_zone_expiry_deactivation_and_older_active_zones_follow_map_policy(context):
    baseline = public_stats_service.get_public_stats(context.db).daily_verified_reports
    older = zone(context)
    older.created_at = datetime.now(timezone.utc) - timedelta(days=2)
    expired = zone(context)
    expired.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    inactive = zone(context)
    inactive.is_active = False
    context.db.commit()
    stats = public_stats_service.get_public_stats(context.db)
    assert stats.daily_verified_reports == baseline
    assert older.id in {z.id for z in get_active_avoidance_zones(context.db)}
    # Pausing expiry must affect homepage and map identically without rewriting deadlines.
    context.policy.automatic_expiry_enabled = False
    stats = public_stats_service.get_public_stats(context.db)
    today = datetime.now(timezone.utc).date()
    assert stats.daily_verified_reports == sum(1 for z in get_active_avoidance_zones(context.db)
        if z.created_at.astimezone(timezone.utc).date() == today)
    assert expired.id in {z.id for z in get_active_avoidance_zones(context.db)}
    assert inactive.id not in {z.id for z in get_active_avoidance_zones(context.db)}


def test_daily_api_boundary_is_explicit_utc_at_midnight(monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 11, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(public_stats_service, "datetime", Clock)
    # Local-calendar dates differ, but the legacy daily field uses UTC consistently.
    zones = [SimpleNamespace(created_at=datetime.fromisoformat(value)) for value in
        ("2026-10-11T07:59:59+08:00", "2026-10-11T08:00:00+08:00")]
    monkeypatch.setattr(public_stats_service, "get_active_avoidance_zones", lambda db: zones)
    monkeypatch.setattr(public_stats_service, "get_visitor_summary", lambda db: {"total_unique_visitors": 3})
    stats = public_stats_service.get_public_stats(None)
    assert stats.daily_verified_reports == 1 and stats.total_visitors == 3


@pytest.mark.parametrize("tab", ["recent", "nearby"])
def test_feed_is_newest_first_with_stable_pages_despite_distance_votes_edits(context, tab):
    db, user = context.db, context.users[0]
    now = datetime.now(timezone.utc)
    posts = []
    for age, latitude in ((5, 14.57001), (1, 14.58), (1, 14.59), (0, 15.0), (0, None)):
        post = models.CommunityPost(user_id=user.id, content="Chronological feed test",
            created_at=now - timedelta(hours=age), updated_at=now,
            location_lat=latitude, location_lng=121.08 if latitude is not None else None)
        db.add(post)
        posts.append(post)
    db.flush()
    old, first_tie, second_tie, outside, unlocated = posts
    db.add(models.PostInteraction(user_id=user.id, post_id=old.id,
        interaction_type=InteractionType.UPVOTE))
    for _ in range(10):
        db.add(models.Comment(user_id=user.id, post_id=old.id, content="Old popular post"))
    db.commit()
    options = dict(db=db, user_id=user.id, author_id=user.id, tab=tab,
                   lat=14.57, lng=121.08, radius=5000)
    expected = [second_tie.id, first_tie.id, old.id] if tab == "nearby" else [
        unlocated.id, outside.id, second_tie.id, first_tie.id, old.id]
    result = get_feed_posts(**options)
    assert [p["id"] for p in result["posts"]] == expected
    oldest = next(p for p in result["posts"] if p["id"] == old.id)
    assert oldest["upvotes"] == 1 and oldest["comment_count"] == 10
    pages = [get_feed_posts(**options, skip=i, limit=2) for i in range(0, len(expected), 2)]
    assert [p["id"] for page in pages for p in page["posts"]] == expected
    assert pages[0]["has_more"] and not pages[-1]["has_more"]
    assert all(page["total"] == len(expected) for page in pages)
    # Fresh eligible publications appear first; refreshing old content does not promote it.
    fresh = models.CommunityPost(user_id=user.id, content="Latest flood update",
        created_at=now + timedelta(seconds=1), location_lat=14.58, location_lng=121.08)
    db.add(fresh)
    old.updated_at = now + timedelta(seconds=2)
    db.commit()
    assert [p["id"] for p in get_feed_posts(**options)["posts"]] == [fresh.id, *expected]
