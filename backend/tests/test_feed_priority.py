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
