from datetime import datetime, timedelta
import pytest
from app.models.post import CommunityPost
from app.models.report import FloodReport
from app.schemas.post import CommunityPostResponse
from app.crud.feed import get_feed_posts
from app.core.database import SessionLocal


def test_feed_post_schema_includes_flood_report_id():
    """Verify that CommunityPostResponse supports flood_report_id."""
    post_dict = {
        "id": 101,
        "user_id": 1,
        "content": "Knee-deep flooding along Ortigas Ave",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "author_name": "Juan Dela Cruz",
        "flood_report_id": 42,
    }
    resp = CommunityPostResponse(**post_dict)
    assert resp.flood_report_id == 42
    assert resp.content == "Knee-deep flooding along Ortigas Ave"


def test_feed_regular_post_has_none_flood_report_id():
    """Verify that standard community chatter posts have flood_report_id as None."""
    post_dict = {
        "id": 102,
        "user_id": 1,
        "content": "Traffic is heavy near the mall today",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "author_name": "Maria Santos",
        "flood_report_id": None,
    }
    resp = CommunityPostResponse(**post_dict)
    assert resp.flood_report_id is None


def test_feed_post_schema_includes_distance_meters():
    """Verify that CommunityPostResponse supports distance_meters serialization."""
    post_dict = {
        "id": 103,
        "user_id": 1,
        "content": "Knee-deep flooding along Ortigas Ave",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "author_name": "Juan Dela Cruz",
        "distance_meters": 450.5,
    }
    resp = CommunityPostResponse(**post_dict)
    assert resp.distance_meters == 450.5


def test_feed_endpoint_nearby_fallback_saved_place():
    """Verify that get_feed falls back to user's saved place when lat/lng are omitted."""
    from unittest.mock import MagicMock
    from app.api.v1.endpoints.feed import get_feed
    from app.models.saved_place import SavedPlace

    mock_db = MagicMock()
    mock_user = MagicMock()

    home_place = SavedPlace(
        id=1,
        user_id=1,
        name="Home",
        icon="home",
        latitude=14.580,
        longitude=121.085,
        pin_order=1
    )
    work_place = SavedPlace(
        id=2,
        user_id=1,
        name="Work",
        icon="briefcase",
        latitude=14.550,
        longitude=121.050,
        pin_order=2
    )
    mock_user.id = 1
    mock_user.profile = None  # This case deliberately has no registered address.
    mock_user.saved_places = [work_place, home_place]

    # Mock crud_feed.get_feed_posts
    from app.crud import feed as crud_feed
    original_get_feed_posts = crud_feed.get_feed_posts
    captured_coords = {}

    def fake_get_feed_posts(**kwargs):
        captured_coords["lat"] = kwargs.get("lat")
        captured_coords["lng"] = kwargs.get("lng")
        captured_coords["tab"] = kwargs.get("tab")
        return {"posts": [], "total": 0, "has_more": False}

    crud_feed.get_feed_posts = fake_get_feed_posts
    try:
        res = get_feed(
            lat=None,
            lng=None,
            radius=5000,
            skip=0,
            limit=20,
            tab="nearby",
            time_window_hours=72,
            db=mock_db,
            current_user=mock_user
        )
        assert captured_coords["lat"] == 14.580
        assert captured_coords["lng"] == 121.085
        assert captured_coords["tab"] == "nearby"
    finally:
        crud_feed.get_feed_posts = original_get_feed_posts
