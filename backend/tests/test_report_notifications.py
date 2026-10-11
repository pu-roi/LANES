"""Exercise real PostgreSQL transactions; every test rolls back its outer transaction."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_current_user
from app.api.v1.endpoints import admin, notifications, reports
from app.core.database import engine, get_db
from app.crud.notification import get_notifications, get_unread_count
from app.crud.report import create_flood_report
from app.schemas.report import SurveyData
from app.services.flood_event_service import create_verified_event_with_zone, link_supporting_report, reject_report
from app.services.report_notification_service import stage_report_status_notification


@pytest.fixture
def moderation():
    # Never run this rollback-based fixture against a remote deployment.
    assert make_url(str(engine.url)).host in {"localhost", "127.0.0.1", "::1"}
    connection = engine.connect()
    outer = connection.begin()
    db = Session(bind=connection, join_transaction_mode="create_savepoint", autoflush=False)
    users = {}
    for name, role_name in (("owner", "Commuter"), ("other", "Commuter"),
                            ("admin", "Super Admin"), ("drrmo", "DRRM Officer")):
        role = db.query(models.Role).filter_by(name=role_name).first()
        if role is None:
            role = models.Role(name=role_name)
            db.add(role)
            db.flush()
        token = uuid4().hex
        users[name] = models.User(username=f"notification_{token}", email=f"{token}@example.test",
                                  hashed_password="test-only", role_id=role.id)
        db.add(users[name])
    db.flush()
    for name in ("owner", "other"):
        db.add(models.Profile(user_id=users[name].id, first_name="Notification", last_name="Tester"))
    db.commit()
    state = SimpleNamespace(user=users["owner"])
    app = FastAPI()
    app.include_router(admin.router, prefix="/admin")
    app.include_router(notifications.router, prefix="/notifications")
    app.include_router(reports.router, prefix="/reports")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: state.user
    try:
        with TestClient(app) as client:
            yield SimpleNamespace(db=db, users=users, state=state, client=client)
    finally:
        db.close()
        outer.rollback()
        connection.close()


def new_report(context, *, owner="owner"):
    return create_flood_report(context.db, schemas.FloodReportCreate(
        raw_text="Notification workflow flood report", source="direct_user", severity="medium",
        depth="knee", barangay="Maybunga", city="Pasig", is_public=False,
        user_id=context.users[owner].id if owner else None,
        survey_data=SurveyData(hidden_hazards="yes", passable_vehicles="heavy"),
    ))


POLYGON = {"type": "Polygon", "coordinates": [[[121.08, 14.57], [121.081, 14.57],
    [121.081, 14.571], [121.08, 14.571], [121.08, 14.57]]]}


@pytest.mark.parametrize("staff", ["admin", "drrmo"])
def test_queue_and_staff_approval_updates_are_owned_and_idempotent(moderation, staff):
    report = new_report(moderation)
    db, client = moderation.db, moderation.client
    pending = get_notifications(db, moderation.users["owner"].id)
    assert len(pending) == 1
    assert pending[0].payload == {"report_id": report.id, "action": "flood_report_under_review",
                                   "title": "Flood Report Under Review"}
    assert "awaiting review" in pending[0].message
    assert pending[0].is_read is False and pending[0].created_at.tzinfo is not None
    moderation.state.user = moderation.users[staff]
    # Viewing details never creates notifications.
    for _ in range(2):
        assert client.get(f"/admin/reports/detail/{report.id}").status_code == 200
    assert len(get_notifications(db, report.user_id)) == 1
    for _ in range(2):
        response = client.post(f"/admin/reports/{report.id}/approve", json={"custom_geometry": POLYGON})
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "approved"
    notices = get_notifications(db, report.user_id)
    assert {n.payload["action"] for n in notices} == {"flood_report_under_review", "flood_report_approved"}
    assert len(notices) == 2
    assert all(n.payload["report_id"] == report.id and not n.is_read for n in notices)
    assert get_notifications(db, moderation.users["other"].id) == []
    assert get_notifications(db, moderation.users[staff].id) == []
    assert moderation.users["owner"].profile.reports_approved == 1
    assert moderation.users["owner"].profile.trust_score == 55


def test_linked_and_automatic_approvals_use_the_same_notifications(moderation):
    event, zone = create_verified_event_with_zone(moderation.db,
        schemas.FloodAvoidanceZoneCreate(geometry=POLYGON), "medium", "knee")
    report = new_report(moderation)
    link_supporting_report(moderation.db, report, event, zone, acted_by_user_id=None)
    link_supporting_report(moderation.db, report, event, zone, acted_by_user_id=None)
    notices = get_notifications(moderation.db, report.user_id)
    assert len(notices) == 2
    approved = next(n for n in notices if n.payload["action"] == "flood_report_approved")
    assert "approved" in approved.message and "administrators" not in approved.message


def test_merged_evidence_notifies_each_original_owner(moderation):
    db = moderation.db
    event, zone = create_verified_event_with_zone(db,
        schemas.FloodAvoidanceZoneCreate(geometry=POLYGON), "medium", "knee")
    selected = [new_report(moderation), new_report(moderation, owner="other")]
    for report in selected:
        link_supporting_report(db, report, event, zone,
            acted_by_user_id=moderation.users["drrmo"].id, commit=False)
    db.commit()
    for report in selected:
        notices = get_notifications(db, report.user_id)
        assert len(notices) == 2
        assert all(n.payload["report_id"] == report.id for n in notices)
        assert {n.payload["action"] for n in notices} == {"flood_report_under_review", "flood_report_approved"}


def test_rejection_preserves_public_reason_and_hides_staff_notes(moderation):
    report = new_report(moderation)
    for _ in range(2):
        reject_report(moderation.db, report, models.ReportRejectionReason.INSUFFICIENT_EVIDENCE,
                      "Private staff note", moderation.users["admin"].id)
    notices = get_notifications(moderation.db, report.user_id)
    assert len(notices) == 2
    rejected = next(n for n in notices if n.payload["action"] == "flood_report_rejected")
    assert "insufficient supporting evidence" in rejected.message
    assert rejected.payload["rejection_reason"] == "insufficient_evidence"
    assert "Private staff note" not in str(rejected.payload) + rejected.message
    assert moderation.users["owner"].profile.reports_rejected == 1
    assert moderation.users["owner"].profile.trust_score == 40


def test_notification_and_report_access_are_owner_scoped(moderation):
    report = new_report(moderation)
    db, client = moderation.db, moderation.client
    notice = get_notifications(db, report.user_id)[0]
    moderation.state.user = moderation.users["other"]
    assert client.get("/notifications").json()["notifications"] == []
    assert client.post(f"/notifications/{notice.id}/read").status_code == 404
    db.refresh(notice)
    assert notice.is_read is False
    assert client.get(f"/reports/me/{report.id}").status_code == 404
    moderation.state.user = moderation.users["owner"]
    assert client.get(f"/reports/me/{report.id}").json()["survey"]["hidden_hazards"] == "yes"
    for _ in range(2):
        assert client.post(f"/notifications/{notice.id}/read").json()["is_read"] is True
    assert client.get("/notifications").json()["unread_count"] == 0
    report.deleted_at = datetime.now(timezone.utc)
    db.commit()
    assert client.get(f"/reports/me/{report.id}").status_code == 404
    assert client.get("/notifications").json()["total"] == 1


def test_unauthorized_or_invalid_approval_sends_no_update(moderation):
    report = new_report(moderation)
    client = moderation.client
    response = client.post(f"/admin/reports/{report.id}/approve", json={"custom_geometry": POLYGON})
    assert response.status_code == 403
    moderation.state.user = moderation.users["admin"]
    assert client.post(f"/admin/reports/{report.id}/approve", json={"action": "MERGE"}).status_code == 422
    assert len(get_notifications(moderation.db, report.user_id)) == 1
    moderation.db.refresh(report)
    assert report.status == models.ReportStatus.PENDING


def test_failed_notification_rolls_back_approval_and_submission(moderation, monkeypatch):
    report = new_report(moderation)
    owner_id = report.user_id
    def fail(*args, **kwargs):
        raise RuntimeError("Notification storage unavailable")
    monkeypatch.setattr("app.services.report_notification_service.create_notification", fail)
    with pytest.raises(RuntimeError, match="storage unavailable"):
        create_verified_event_with_zone(moderation.db,
            schemas.FloodAvoidanceZoneCreate(report_id=report.id, geometry=POLYGON),
            "medium", "knee", source_report=report, acted_by_user_id=moderation.users["admin"].id)
    moderation.db.refresh(report)
    assert report.status == models.ReportStatus.PENDING and report.event_id is None and report.zone_id is None
    assert len(get_notifications(moderation.db, owner_id)) == 1
    with pytest.raises(RuntimeError, match="storage unavailable"):
        new_report(moderation)
    assert moderation.db.query(models.FloodReport).filter_by(user_id=owner_id).count() == 1


def test_failed_commit_persists_neither_approval_nor_notification(moderation, monkeypatch):
    report = new_report(moderation)
    owner_id = report.user_id
    def fail_commit():
        raise RuntimeError("Commit failed")
    monkeypatch.setattr(moderation.db, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="Commit failed"):
        create_verified_event_with_zone(moderation.db,
            schemas.FloodAvoidanceZoneCreate(report_id=report.id, geometry=POLYGON),
            "medium", "knee", source_report=report, acted_by_user_id=moderation.users["admin"].id)
    moderation.db.refresh(report)
    assert report.status == models.ReportStatus.PENDING and report.event_id is None
    assert len(get_notifications(moderation.db, owner_id)) == 1


def test_notification_routes_require_a_session(moderation):
    report = new_report(moderation)
    notification = get_notifications(moderation.db, report.user_id)[0]
    moderation.client.app.dependency_overrides.pop(get_current_user)
    assert moderation.client.get("/notifications").status_code == 401
    assert moderation.client.post(f"/notifications/{notification.id}/read").status_code == 401
    assert moderation.client.get(f"/reports/me/{report.id}").status_code == 401
    assert moderation.client.post(f"/admin/reports/{report.id}/approve", json={"custom_geometry": POLYGON}).status_code == 401
    moderation.db.refresh(notification)
    assert notification.is_read is False


def test_duplicate_stage_and_ownerless_reports(moderation):
    report = new_report(moderation)
    for _ in range(2):
        stage_report_status_notification(moderation.db, report)
        moderation.db.commit()
    assert len(get_notifications(moderation.db, report.user_id)) == 1
    ownerless = new_report(moderation, owner=None)
    assert stage_report_status_notification(moderation.db, ownerless) is None


def test_existing_post_warning_and_read_all_remain_private(moderation):
    db = moderation.db
    from app.models.post import CommunityPost, CommunityPostReport
    post = CommunityPost(user_id=moderation.users["owner"].id, content="A community post")
    db.add(post)
    db.flush()
    complaint = CommunityPostReport(post_id=post.id, reporter_user_id=moderation.users["other"].id,
                                    reason="misinformation", status="open")
    db.add(complaint)
    db.commit()
    moderation.state.user = moderation.users["admin"]
    response = moderation.client.post(f"/admin/moderation/posts/{post.id}/resolve", json={"action": "warn"})
    assert response.status_code == 200, response.text
    owner_notices = get_notifications(db, post.user_id)
    assert len(owner_notices) == 1
    warning = owner_notices[0]
    assert warning.payload == {"post_id": post.id, "action": "warn", "reasons": ["Misinformation / False Hazard"]}
    assert "warned" in warning.message and "reporter_user_id" not in warning.payload
    assert moderation.client.post(f"/admin/moderation/posts/{post.id}/resolve", json={"action": "warn"}).status_code == 404
    moderation.state.user = moderation.users["owner"]
    assert moderation.client.post("/notifications/read-all").status_code == 200
    assert get_unread_count(db, post.user_id) == 0
    assert get_unread_count(db, moderation.users["other"].id) == 1
