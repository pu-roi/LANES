"""Filter full public datasets using local PostGIS, with no lasting test writes."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_current_user_optional, get_current_user
from app.api.v1.endpoints import feed, posts, reports
from app.core.database import engine, get_db
from app.crud.feed import get_feed_posts, get_feed_post
from app.crud import feed as crud_feed
from app.crud.report import get_active_avoidance_zones, restore_flood_avoidance_zone
from app.schemas.feed import CommunityFeedFilters
from app.services import configuration_service
from app.services.community_feed_service import publication_bounds
from app.services.flood_event_service import create_verified_event_with_zone, deactivate_zone_and_end_event_if_final

POLYGON = {"type": "Polygon", "coordinates": [[[121.08, 14.57], [121.081, 14.57],
    [121.081, 14.571], [121.08, 14.571], [121.08, 14.57]]]}


@pytest.fixture
def community(monkeypatch):
    assert make_url(str(engine.url)).host in {"localhost", "127.0.0.1", "::1"}
    connection = engine.connect()
    outer = connection.begin()
    db = Session(bind=connection, join_transaction_mode="create_savepoint", autoflush=False)
    policy = SimpleNamespace(automatic_expiry_enabled=True)
    monkeypatch.setattr(configuration_service, "read_configuration", lambda db: policy)
    role = db.query(models.Role).filter_by(name="Commuter").first()
    if role is None:
        role = models.Role(name="Commuter")
        db.add(role)
        db.flush()
    users = []
    for _ in range(2):
        token = uuid4().hex
        user = models.User(username=f"feed_filter_{token}", email=f"{token}@example.test",
                           hashed_password="test-only", role_id=role.id)
        db.add(user)
        users.append(user)
    db.commit()
    state = SimpleNamespace(user=None)
    app = FastAPI()
    app.include_router(feed.router, prefix="/feed")
    app.include_router(posts.router, prefix="/posts")
    app.include_router(reports.router, prefix="/reports")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user_optional] = lambda: state.user
    app.dependency_overrides[get_current_user] = lambda: state.user
    try:
        with TestClient(app) as client:
            yield SimpleNamespace(db=db, client=client, users=users, state=state, policy=policy)
    finally:
        db.close()
        outer.rollback()
        connection.close()


def post(context, *, age=0, report=None, lat=14.57, hidden=False):
    now = datetime.now(timezone.utc)
    row = models.CommunityPost(user_id=context.users[0].id, content="Filter regression post",
        flood_report_id=report.id if report else None, created_at=now - timedelta(hours=age),
        location_lat=lat, location_lng=121.08 if lat is not None else None,
        hidden_at=now if hidden else None)
    context.db.add(row)
    context.db.commit()
    return row


def report(context, *, status="approved", public=True, severity="high", active=True):
    row = models.FloodReport(user_id=context.users[0].id, raw_text="Public flood filter test",
        source=models.ReportSource.USER_REPORT, severity=models.ReportSeverity(severity),
        status=models.ReportStatus.PENDING, is_public=public, depth="waist")
    context.db.add(row)
    context.db.commit()
    if status == "approved":
        _, zone = create_verified_event_with_zone(context.db,
            schemas.FloodAvoidanceZoneCreate(geometry=POLYGON), severity, "waist",
            source_report=row, credit_reputation=False)
        if not active:
            deactivate_zone_and_end_event_if_final(context.db, zone)
    else:
        row.status = models.ReportStatus(status)
        context.db.commit()
    return row


def ids(context, **kwargs):
    return [p["id"] for p in get_feed_posts(context.db, author_id=context.users[0].id, **kwargs)["posts"]]


def isolate_api_author(context, monkeypatch):
    original = crud_feed.get_feed_posts
    def query(**kwargs):
        return original(**{**kwargs, "author_id": context.users[0].id})
    monkeypatch.setattr(crud_feed, "get_feed_posts", query)


@pytest.mark.parametrize("date_range,hours", [("24h", 24), ("3d", 72), ("7d", 168)])
def test_date_boundaries_are_inclusive_and_before_pagination(community, date_range, hours):
    now = datetime(2026, 10, 11, 0, 30, tzinfo=timezone.utc)
    rows = [post(community) for _ in range(4)]
    times = [now - timedelta(hours=hours, microseconds=1), now - timedelta(hours=hours),
             now - timedelta(seconds=1), now + timedelta(seconds=1)]
    for row, created in zip(rows, times):
        row.created_at = created
    community.db.commit()
    # SQL comparisons must not depend on the database session's local calendar.
    community.db.execute(text("SET LOCAL TIME ZONE 'Asia/Manila'"))
    for sort, expected in (("newest", [rows[2].id, rows[1].id]), ("oldest", [rows[1].id, rows[2].id])):
        filters = CommunityFeedFilters(date_range=date_range, sort=sort)
        assert ids(community, filters=filters, now=now) == expected
        first = get_feed_posts(community.db, author_id=community.users[0].id,
            filters=filters, now=now, limit=1)
        second = get_feed_posts(community.db, author_id=community.users[0].id,
            filters=filters, now=now, skip=1, limit=1)
        assert first["total"] == 2 and first["has_more"] and not second["has_more"]
        assert [first["posts"][0]["id"], second["posts"][0]["id"]] == expected


def test_today_uses_utc_and_all_time_includes_old_publications(community, monkeypatch):
    isolate_api_author(community, monkeypatch)
    now = datetime(2026, 10, 11, 0, 30, tzinfo=timezone.utc)
    old, today = post(community), post(community)
    old.created_at = datetime(2026, 10, 10, 23, 59, 59, tzinfo=timezone.utc)
    today.created_at = datetime.fromisoformat("2026-10-11T08:00:00+08:00")
    community.db.commit()
    assert ids(community, filters=CommunityFeedFilters(date_range="today"), now=now) == [today.id]
    assert ids(community, filters=CommunityFeedFilters(), now=now) == [today.id, old.id]
    assert publication_bounds("today", now)[0] == datetime(2026, 10, 11, tzinfo=timezone.utc)
    very_old = post(community, age=24 * 30)
    response = community.client.get("/feed?limit=100")
    assert response.status_code == 200, response.text
    assert very_old.id in {p["id"] for p in response.json()["posts"]}


def test_active_resolved_severity_and_date_combinations_use_persisted_lifecycle(community):
    active = report(community)
    ended = report(community, active=False)
    low = report(community, severity="low")
    active_post, ended_post = post(community, report=active), post(community, report=ended)
    post(community, report=low)
    expired = report(community)
    expired.avoidance_zone.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    post(community, report=expired)
    post(community, age=200, report=active)
    ordinary = post(community)
    community.db.commit()
    active_filter = CommunityFeedFilters(flood_status="active", severity="high", date_range="24h")
    assert ids(community, filters=active_filter) == [active_post.id]
    assert ids(community, filters=CommunityFeedFilters(flood_status="resolved", severity="high")) == [ended_post.id]
    active_zone_ids = {z.id for z in get_active_avoidance_zones(community.db)}
    assert active.zone_id in active_zone_ids and expired.zone_id not in active_zone_ids
    # Paused expiry uses exactly the map's existing eligibility policy.
    community.policy.automatic_expiry_enabled = False
    assert expired.zone_id in {p["report"].zone_id for p in get_feed_posts(community.db,
        author_id=community.users[0].id, filters=active_filter)["posts"]}
    assert ordinary.id not in ids(community, filters=active_filter)
    # Restoring a zone does not currently rewrite its event's ended flag.
    # Current map eligibility wins so Active and Resolved never overlap.
    restore_flood_avoidance_zone(community.db, ended.zone_id)
    assert ended_post.id in ids(community, filters=active_filter)
    assert ended_post.id not in ids(community, filters=CommunityFeedFilters(flood_status="resolved"))


@pytest.mark.parametrize("viewer", [None, 0, 1])
def test_public_feed_shares_pending_but_excludes_rejected_private_archived_or_hidden_reports(community, viewer):
    good = post(community, report=report(community))
    pending = post(community, report=report(community, status="pending"))
    blocked = [post(community, report=report(community, status="rejected"))]
    blocked.append(post(community, report=report(community, public=False)))
    archived = report(community)
    archived.deleted_at = datetime.now(timezone.utc)
    blocked.append(post(community, report=archived))
    blocked.append(post(community, hidden=True))
    community.db.commit()
    community.state.user = community.users[viewer] if viewer is not None else None
    for query in ("", "?sort=oldest", "?date_range=7d&severity=high", "?flood_status=active"):
        response = community.client.get('/feed' + query)
        assert response.status_code == 200, response.text
        result = {p["id"] for p in response.json()["posts"]}
        assert good.id in result and not result.intersection(p.id for p in blocked)
        assert (pending.id in result) == (query != "?flood_status=active")
    other_id = community.users[1].id
    assert get_feed_post(community.db, blocked[1].id, user_id=other_id) is None
    assert get_feed_post(community.db, blocked[0].id, user_id=community.users[0].id) is not None
    assert get_feed_post(community.db, pending.id, user_id=other_id)["report"].status == models.ReportStatus.PENDING
    # My Posts retains the owner's existing unpublished/hidden access only.
    community.state.user = community.users[0]
    own = community.client.get('/posts/me').json()
    assert {good.id, pending.id, *(p.id for p in blocked)} <= {p["id"] for p in own["posts"]}


@pytest.mark.parametrize("public", [False, True])
def test_report_submission_immediately_shares_only_when_selected(community, monkeypatch, public):
    from app.services import citizen_approval_service, report_locality_service
    monkeypatch.setattr(citizen_approval_service, "record_observation", lambda *args, **kwargs: None)
    monkeypatch.setattr(citizen_approval_service, "approve_citizen_report", lambda *args: "staff_review_required")
    monkeypatch.setattr(report_locality_service, "pasig_geometry_locality", lambda geometry: None)
    monkeypatch.setattr(reports, "upload_image", lambda file: "https://example.test/flood.jpg")
    isolate_api_author(community, monkeypatch)
    community.state.user = community.users[0]
    response = community.client.post("/reports", data={
        "raw_text": "Immediate community share regression", "source": "direct_user",
        "severity": "high", "depth": "waist", "is_public": str(public).lower(),
        "human_readable_location": "Test street", "barangay": "Test barangay", "city": "Test city",
        "geometry": '{"type":"Point","coordinates":[121.08,14.57]}',
    }, files={"media": ("flood.jpg", b"photo", "image/jpeg")})
    assert response.status_code == 201, response.text
    report_id = response.json()["id"]
    assert response.json()["status"] == "pending"
    saved = community.db.get(models.FloodReport, report_id)
    assert saved.zone_id is None and saved.event_id is None
    shared = community.db.query(models.CommunityPost).filter_by(flood_report_id=report_id).all()
    assert len(shared) == int(public)
    if public:
        community.state.user = None
        for query in ("", "?tab=nearby&lat=14.57&lng=121.08&radius=1000"):
            feed_response = community.client.get("/feed" + query)
            assert feed_response.status_code == 200, feed_response.text
            published = next(p for p in feed_response.json()["posts"] if p["id"] == shared[0].id)
            assert published["report"]["status"] == "pending"
            assert published["media_urls"] == ["https://example.test/flood.jpg"]
        assert community.client.get(f"/posts/{shared[0].id}").status_code == 200


def test_failed_community_share_rolls_back_report_and_notification(community, monkeypatch):
    from app.crud import post as crud_post
    from app.services import report_service
    import asyncio

    def fail_share(**kwargs):
        raise RuntimeError("Community share unavailable")

    monkeypatch.setattr(crud_post, "create_community_post", fail_share)
    text_content = "Rollback share regression"
    with pytest.raises(RuntimeError, match="Community share unavailable"):
        asyncio.run(report_service.process_new_report(db=community.db,
            user_id=community.users[0].id, raw_text=text_content,
            source="direct_user", severity="high", is_public=True))
    assert community.db.query(models.FloodReport).filter_by(raw_text=text_content).count() == 0
    assert community.db.query(models.Notification).filter_by(user_id=community.users[0].id).count() == 0


def test_explicit_nearby_radius_is_strict_and_auto_expansion_preserves_filters(community, monkeypatch):
    isolate_api_author(community, monkeypatch)
    eligible = post(community, age=4, lat=14.65)  # ~9 km away
    nearby_old = post(community, age=200, lat=14.65)
    query = "?tab=nearby&lat=14.57&lng=121.08&date_range=24h"
    auto = community.client.get('/feed' + query + '&limit=100').json()
    assert auto['expanded_radius'] is True
    assert [p['id'] for p in auto['posts']] == [eligible.id]
    for radius in (1000, 3000, 5000):
        response = community.client.get('/feed' + query + f'&radius={radius}&limit=100').json()
        assert response['expanded_radius'] is False
        assert eligible.id not in {p['id'] for p in response['posts']}
    ten = community.client.get('/feed' + query + '&radius=10000&limit=100').json()
    assert eligible.id in {p['id'] for p in ten['posts']}
    assert nearby_old.id not in {p['id'] for p in ten['posts']}


@pytest.mark.parametrize("query", ["sort=popular", "date_range=month", "flood_status=pending",
    "severity=unknown", "radius=0", "radius=-1", "radius=20000", "radius=nan",
    "lat=91&lng=121", "lat=14&lng=181", "lat=14", "skip=-1", "skip=999999999999999999999",
    "limit=101", "time_window_hours=99999999999999999"])
def test_invalid_filters_are_rejected(community, query):
    assert community.client.get('/feed?' + query).status_code == 422


def test_empty_selected_period_never_falls_back_to_older_posts(community, monkeypatch):
    isolate_api_author(community, monkeypatch)
    old = post(community, age=200)
    response = community.client.get('/feed?date_range=24h&limit=100')
    assert response.status_code == 200
    assert old.id not in {p['id'] for p in response.json()['posts']}
    assert response.json()['posts'] == [] and response.json()['total'] == 0
    assert community.client.get('/feed?tab=nearby').status_code == 400
