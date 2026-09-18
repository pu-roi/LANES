import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.main import app
from app.api import deps
from app import models
from app.models.report import ReportSeverity, ReportSource, ReportStatus

def override_get_current_active_admin(db: Session = deps.Depends(deps.get_db)):
    admin_user = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin_user:
        role = db.query(models.Role).filter(models.Role.name == "Super Admin").first()
        if not role:
            role = models.Role(name="Super Admin", permissions={"all": "manage"}, is_template=True)
            db.add(role)
            db.commit()
            db.refresh(role)
        admin_user = models.User(username="admin", email="admin@test.com", hashed_password="hash", role_id=role.id, is_active=True)
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
    return admin_user

app.dependency_overrides[deps.get_current_active_admin] = override_get_current_active_admin
client = TestClient(app)

def test_spatial_report_archive_lifecycle(db_session: Session):
    admin = override_get_current_active_admin(db_session)
    
    # 1. Create a test pending report
    report = models.FloodReport(
        raw_text="Test flood for archive lifecycle",
        source=ReportSource.CITIZEN,
        severity=ReportSeverity.HIGH,
        status=ReportStatus.PENDING,
        user_id=admin.id
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    report_id = report.id

    try:
        # 2. Reject the report via admin endpoint
        reject_resp = client.post(f"/api/v1/admin/reports/{report_id}/reject")
        assert reject_resp.status_code == 200
        rejected_data = reject_resp.json()
        assert rejected_data["status"] == "rejected"

        # Verify deleted_at is set in database
        db_session.expire_all()
        reloaded = db_session.query(models.FloodReport).filter(models.FloodReport.id == report_id).first()
        assert reloaded.deleted_at is not None
        assert reloaded.status == ReportStatus.REJECTED

        # 3. Verify it appears in archived reports query
        archived_resp = client.get("/api/v1/admin/reports/all?archived=true")
        assert archived_resp.status_code == 200
        archived_ids = [r["id"] for r in archived_resp.json()["reports"]]
        assert report_id in archived_ids

        # Verify it does NOT appear in active reports query
        active_resp = client.get("/api/v1/admin/reports/all?archived=false")
        assert active_resp.status_code == 200
        active_ids = [r["id"] for r in active_resp.json()["reports"]]
        assert report_id not in active_ids

        # 4. Restore the report
        restore_resp = client.post(f"/api/v1/admin/reports/{report_id}/restore")
        assert restore_resp.status_code == 200
        restored_data = restore_resp.json()
        assert restored_data["status"] == "pending"

        db_session.expire_all()
        restored = db_session.query(models.FloodReport).filter(models.FloodReport.id == report_id).first()
        assert restored.deleted_at is None
        assert restored.status == ReportStatus.PENDING

        # 5. Permanently delete the report
        perm_resp = client.delete(f"/api/v1/admin/reports/{report_id}/permanent")
        assert perm_resp.status_code == 200

        db_session.expire_all()
        deleted = db_session.query(models.FloodReport).filter(models.FloodReport.id == report_id).first()
        assert deleted is None

    finally:
        # Cleanup
        db_session.query(models.FloodReport).filter(models.FloodReport.id == report_id).delete()
        db_session.commit()


def test_spatial_zone_archive_lifecycle(db_session: Session):
    admin = override_get_current_active_admin(db_session)
    
    # 1. Create a dummy polygon zone
    poly_wkt = "POLYGON((121.0 14.5, 121.1 14.5, 121.1 14.6, 121.0 14.6, 121.0 14.5))"
    geom_clause = func.ST_SetSRID(func.ST_GeomFromText(poly_wkt), 4326)
    
    zone = models.FloodAvoidanceZone(
        name="Test Archive Zone",
        geometry=geom_clause,
        is_active=True,
        curated_by_admin_id=admin.id
    )
    db_session.add(zone)
    db_session.commit()
    db_session.refresh(zone)
    zone_id = zone.id

    try:
        # 2. Deactivate zone via admin endpoint
        deact_resp = client.patch(f"/api/v1/admin/zones/{zone_id}/deactivate")
        assert deact_resp.status_code == 200
        assert deact_resp.json()["is_active"] is False

        # 3. Verify it appears in archived zones list
        archived_resp = client.get("/api/v1/admin/zones/all?archived=true")
        assert archived_resp.status_code == 200
        archived_zone_ids = [z["id"] for z in archived_resp.json()["zones"]]
        assert zone_id in archived_zone_ids

        # Verify it does NOT appear when active_only=true
        active_resp = client.get("/api/v1/admin/zones/all?active_only=true")
        assert active_resp.status_code == 200
        active_zone_ids = [z["id"] for z in active_resp.json()["zones"]]
        assert zone_id not in active_zone_ids

        # 4. Restore zone
        restore_resp = client.post(f"/api/v1/admin/zones/{zone_id}/restore")
        assert restore_resp.status_code == 200
        assert restore_resp.json()["is_active"] is True

        db_session.expire_all()
        reloaded_zone = db_session.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone_id).first()
        assert reloaded_zone.is_active is True

        # 5. Permanently delete zone
        perm_resp = client.delete(f"/api/v1/admin/zones/{zone_id}/permanent")
        assert perm_resp.status_code == 200

        db_session.expire_all()
        deleted_zone = db_session.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone_id).first()
        assert deleted_zone is None

    finally:
        # Cleanup
        db_session.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone_id).delete()
        db_session.commit()
