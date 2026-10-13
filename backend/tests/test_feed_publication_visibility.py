"""Exercise the shared feed/detail visibility predicate without PostGIS."""
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, select, text

from app.crud.feed import public_report_clause
from app.models.post import CommunityPost
from app.models.report import FloodReport, ReportStatus
from app.services import report_service, citizen_approval_service


def test_explicit_sharing_is_independent_of_report_approval() -> None:
    engine = create_engine("sqlite://")
    # Only columns read by the real predicate are needed in this disposable DB.
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE flood_reports (id INTEGER, is_public BOOLEAN, status TEXT, deleted_at TEXT)"))
        connection.execute(text("CREATE TABLE community_posts (id INTEGER, flood_report_id INTEGER)"))
        connection.execute(text("INSERT INTO flood_reports VALUES "
            "(1, 1, 'pending', NULL), (2, 1, 'approved', NULL), "
            "(3, 1, 'rejected', NULL), (4, 0, 'pending', NULL), "
            "(5, 0, 'approved', NULL), (6, 1, 'pending', 'archived')"))
        connection.execute(text("INSERT INTO community_posts VALUES "
            "(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, NULL), (8, 999)"))
        query = select(CommunityPost.id).outerjoin(FloodReport,
            CommunityPost.flood_report_id == FloodReport.id).where(public_report_clause()).order_by(CommunityPost.id)
        assert list(connection.scalars(query)) == [1, 2, 7]
        connection.execute(text("UPDATE flood_reports SET status='rejected' WHERE id=1"))
        assert list(connection.scalars(query)) == [2, 7]
    engine.dispose()


@pytest.mark.parametrize("public", [False, True])
def test_submission_commits_requested_share_before_separate_map_review(monkeypatch, public: bool) -> None:
    from app.crud import post as crud_post
    saved = SimpleNamespace(id=123, status=ReportStatus.PENDING)
    db = Mock()
    create_report = Mock(return_value=saved)
    create_post = Mock()
    monkeypatch.setattr(report_service, "create_flood_report", create_report)
    monkeypatch.setattr(crud_post, "create_community_post", create_post)
    monkeypatch.setattr(citizen_approval_service, "record_observation", Mock())

    def review(session, report_id):
        db.commit.assert_called_once()
        assert create_post.call_count == int(public)
        return "staff_review_required"

    monkeypatch.setattr(citizen_approval_service, "approve_citizen_report", review)
    result = asyncio.run(report_service.process_new_report(db=db, raw_text="Flood observation",
        source="direct_user", severity="high", is_public=public, user_id=7,
        media_urls=["https://example.test/photo.jpg"]))
    assert result.status == ReportStatus.PENDING
    db.rollback.assert_not_called()
    assert create_report.call_args.kwargs["commit"] is False
    if public:
        payload = create_post.call_args.kwargs
        assert payload["commit"] is False and payload["user_id"] == 7
        assert payload["post_in"].flood_report_id == 123
        assert payload["post_in"].media_urls == ["https://example.test/photo.jpg"]


def test_share_failure_reaches_caller_and_prevents_map_review(monkeypatch) -> None:
    from app.crud import post as crud_post
    db = Mock()
    monkeypatch.setattr(report_service, "create_flood_report", Mock(return_value=SimpleNamespace(id=123)))
    monkeypatch.setattr(crud_post, "create_community_post", Mock(side_effect=RuntimeError("Share failed")))
    review = Mock()
    monkeypatch.setattr(citizen_approval_service, "approve_citizen_report", review)
    with pytest.raises(RuntimeError, match="Share failed"):
        asyncio.run(report_service.process_new_report(db=db, raw_text="Flood observation",
            source="direct_user", severity="high", is_public=True, user_id=7))
    db.rollback.assert_called_once()
    db.commit.assert_not_called()
    review.assert_not_called()
