"""Real PostGIS coverage in a fresh disposable loopback database."""
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models.post import CommunityPost
from app.models.report import FloodReport
from app.models.role import Role
from app.models.user import User
from app.services.trending_hotspots_service import get_trending_hotspots

NOW = datetime.now(timezone.utc)


@pytest.fixture(scope="module")
def engine():
    value = os.getenv("LANES_HOTSPOTS_TEST_DATABASE_URL")
    if not value:
        pytest.skip("Fresh disposable loopback hotspot database required")
    url = make_url(value)
    assert url.host in ("localhost", "127.0.0.1", "::1")
    assert url.database.startswith("lanes_hotspots_test_")
    engine = create_engine(url)
    assert not inspect(engine).get_table_names(), "Refusing a nonempty database"
    from app.core.config import settings
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(settings, "DATABASE_URL", value)
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
        command.upgrade(config, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine):
    with Session(engine) as session:
        yield session
        session.rollback()


def user(db: Session, **changes) -> User:
    role = db.query(Role).first()
    if role is None:
        role = Role(name="hotspot-fixture", permissions={})
        db.add(role)
        db.flush()
    identity = uuid4().hex[:16]
    value = User(username=identity, email=f"{identity}@example.org", hashed_password="fixture",
                 role_id=role.id, **changes)
    db.add(value)
    db.flush()
    return value


def post(db: Session, author: User, name: str = "Ortigas Avenue, Pasig", hours: float = 0,
         latitude: float = 14.58, longitude: float = 121.08, **changes) -> CommunityPost:
    value = CommunityPost(user_id=author.id, content="Community activity", location_tag=name,
                          location_lat=latitude, location_lng=longitude,
                          created_at=NOW - timedelta(hours=hours), **changes)
    db.add(value)
    db.flush()
    return value


def hotspots(db: Session, limit: int = 10):
    return get_trending_hotspots(db, limit=limit, now=NOW).hotspots


def test_fresh_multiple_people_outweigh_old_volume_and_repeat_author_spam(db):
    a, b = user(db), user(db)
    for _ in range(10):
        post(db, a, "Older place", hours=18)
    post(db, b, "Older place", hours=18)
    post(db, a, "Fresh place", hours=1)
    post(db, b, "Fresh place", hours=1)
    for _ in range(12):
        post(db, a, "Single person")
    result = hotspots(db)
    assert [value.name for value in result] == ["Fresh place", "Older place"]
    assert result[1].post_count == 11
    assert result[1].contributor_count == 2
    assert len(hotspots(db, limit=1)) == 1


def test_normalizes_labels_but_separates_distant_same_name_places(db):
    a, b = user(db), user(db)
    post(db, a, "  Main   Road  ")
    post(db, b, "main road", latitude=14.5805)
    post(db, a, "MAIN ROAD", latitude=14.68)
    post(db, b, "Main Road", latitude=14.6805)
    result = hotspots(db)
    assert len(result) == 2
    assert sorted(value.post_count for value in result) == [2, 2]
    assert abs(result[0].latitude - result[1].latitude) > 0.09


def test_fallback_has_a_strict_48_hour_boundary_and_excludes_future_posts(db):
    a, b = user(db), user(db)
    for name, hours in [("Old", 48.001), ("Future", -1)]:
        post(db, a, name, hours=hours)
        post(db, b, name, hours=hours)
    assert get_trending_hotspots(db, now=NOW).window_hours == 48
    assert hotspots(db) == []
    post(db, a, "Boundary", hours=48)
    post(db, b, "Boundary", hours=48)
    result = get_trending_hotspots(db, now=NOW)
    assert result.window_hours == 48
    assert [value.name for value in result.hotspots] == ["Boundary"]
    expired = get_trending_hotspots(db, now=NOW + timedelta(seconds=1))
    assert expired.hotspots == []
    assert expired.window_hours == 48


def test_one_current_place_keeps_24_hours_without_filling_from_older_places(db):
    a, b = user(db), user(db)
    for author in (a, b):
        post(db, author, "Current place", hours=24)
        post(db, author, "Older place", hours=30)
    result = get_trending_hotspots(db, now=NOW)
    assert result.window_hours == 24
    assert [value.name for value in result.hotspots] == ["Current place"]
    expanded = get_trending_hotspots(db, now=NOW + timedelta(seconds=1))
    assert expanded.window_hours == 48
    assert {value.name for value in expanded.hotspots} == {"Current place", "Older place"}
    post(db, a, "New activity")
    post(db, b, "New activity")
    refreshed = get_trending_hotspots(db, now=NOW)
    assert refreshed.window_hours == 24
    assert {value.name for value in refreshed.hotspots} == {"Current place", "New activity"}


def test_fallback_keeps_distinct_people_recency_and_privacy_gates(db):
    a, b = user(db), user(db)
    post(db, a, "Mixed ages", hours=1)
    post(db, b, "Mixed ages", hours=25)
    for _ in range(12):
        post(db, a, "Older volume", hours=40)
        post(db, a, "Single person", hours=30)
    post(db, b, "Older volume", hours=40)
    for author in (a, b):
        post(db, author, "Hidden older", hours=30, hidden_at=NOW)
        post(db, author, "Deleted older", hours=30, deleted_at=NOW)
        post(db, author, "Missing location", hours=30, latitude=None, longitude=None)
    result = get_trending_hotspots(db, now=NOW)
    assert result.window_hours == 48
    assert [value.name for value in result.hotspots] == ["Mixed ages", "Older volume"]
    assert result.hotspots[0].contributor_count == 2
    assert result.hotspots[1].post_count == 13


def test_nonpublic_posts_accounts_and_missing_or_invalid_locations_are_excluded(db):
    a, b = user(db), user(db)
    for name, changes in [("Hidden", {"hidden_at": NOW}), ("Deleted", {"deleted_at": NOW}),
                          ("Unlocated", {"latitude": None, "longitude": None}),
                          ("Invalid", {"latitude": 100}), ("Unnamed", {})]:
        post(db, a, "  " if name == "Unnamed" else name, **changes)
        post(db, b, "  " if name == "Unnamed" else name, **changes)
    for author in [user(db, is_active=False), user(db, deleted_at=NOW)]:
        post(db, author, "Account excluded")
        post(db, a, "Account excluded")
    assert hotspots(db) == []


def test_linked_report_privacy_age_status_and_geometry(db):
    a, b = user(db), user(db)
    for name, changes in [("Private", {"is_public": False}), ("Rejected", {"status": "rejected"}),
                          ("Deleted report", {"deleted_at": NOW}),
                          ("Old reshared", {"created_at": NOW - timedelta(days=3)}),
                          ("Current pending", {}), ("Current approved", {"status": "approved"})]:
        for author in [a, b]:
            fields = dict(user_id=author.id, raw_text="Fixture", source="direct_user", severity="low",
                          status="pending", is_public=True, created_at=NOW,
                          human_readable_location=name,
                          geometry="SRID=4326;LINESTRING(121.08 14.58,121.081 14.581)")
            fields.update(changes)
            report = FloodReport(**fields)
            db.add(report)
            db.flush()
            post(db, author, "Barangay tag", latitude=None, longitude=None, flood_report_id=report.id)
    result = hotspots(db)
    assert {value.name for value in result} == {"Current pending", "Current approved"}
    assert all(14.58 <= value.latitude <= 14.581 and 121.08 <= value.longitude <= 121.081 for value in result)


@pytest.mark.parametrize("age,expected_window", [(0, 24), (30, 48)])
def test_public_api_contract_and_limit_validation(db, age, expected_window):
    post(db, user(db), hours=age)
    post(db, user(db), hours=age)
    app.dependency_overrides[get_db] = lambda: db
    try:
        client = TestClient(app)
        response = client.get("/api/v1/feed/hotspots?limit=1")
        assert response.status_code == 200
        payload = response.json()
        assert payload["window_hours"] == expected_window
        assert payload["as_of"]
        assert len(payload["hotspots"]) == 1
        assert payload["hotspots"][0]["post_count"] == 2
        assert "user_id" not in payload["hotspots"][0]
        assert client.get("/api/v1/feed/hotspots?limit=0").status_code == 422
        assert client.get("/api/v1/feed/hotspots?limit=11").status_code == 422
    finally:
        app.dependency_overrides.pop(get_db, None)
