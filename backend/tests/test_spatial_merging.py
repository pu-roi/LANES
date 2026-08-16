import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.api import deps
from app.core.database import SessionLocal
from app import models, schemas
from geoalchemy2.elements import WKTElement

# Override admin dependencies
def override_admin():
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.username == "admin").first()
    db.close()
    return user

app.dependency_overrides[deps.get_current_active_admin] = override_admin
app.dependency_overrides[deps.get_current_user] = override_admin

client = TestClient(app)

def test_spatial_moderation_merging_and_trust_scores():
    db: Session = SessionLocal()
    try:
        # 1. Create two test commuter accounts
        user_a = db.query(models.User).filter(models.User.username == "commuter_a").first()
        if not user_a:
            user_a = models.User(username="commuter_a", email="commuter_a@lanes.ph", hashed_password="pw", role_id=1, is_active=True)
            db.add(user_a)
            db.commit()
            db.refresh(user_a)
            profile_a = models.Profile(user_id=user_a.id, first_name="Commuter", last_name="A", trust_score=50)
            db.add(profile_a)
            db.commit()

        user_b = db.query(models.User).filter(models.User.username == "commuter_b").first()
        if not user_b:
            user_b = models.User(username="commuter_b", email="commuter_b@lanes.ph", hashed_password="pw", role_id=1, is_active=True)
            db.add(user_b)
            db.commit()
            db.refresh(user_b)
            profile_b = models.Profile(user_id=user_b.id, first_name="Commuter", last_name="B", trust_score=50)
            db.add(profile_b)
            db.commit()

        # 2. Submit Report 1 from User A
        line_wkt = "SRID=4326;LINESTRING(121.070 14.580, 121.075 14.585)"
        rep1 = models.FloodReport(
            user_id=user_a.id,
            raw_text="Ortigas flood report A",
            source=models.ReportSource.USER_REPORT,
            severity=models.ReportSeverity.MEDIUM,
            depth="Gutter",
            status=models.ReportStatus.PENDING,
            barangay="Ugong",
            geometry=WKTElement(line_wkt, srid=4326)
        )
        # Submit Report 2 from User B on overlapping segment
        rep2 = models.FloodReport(
            user_id=user_b.id,
            raw_text="Ortigas flood report B",
            source=models.ReportSource.USER_REPORT,
            severity=models.ReportSeverity.HIGH,
            depth="Waist",
            status=models.ReportStatus.PENDING,
            barangay="Ugong",
            geometry=WKTElement(line_wkt, srid=4326)
        )
        db.add_all([rep1, rep2])
        db.commit()
        db.refresh(rep1)
        db.refresh(rep2)

        # 3. Approve Report 1 as CREATE_NEW
        resp1 = client.post(
            f"/api/v1/admin/reports/{rep1.id}/approve",
            json={"action": "CREATE_NEW", "buffer_radius": 0.0002}
        )
        assert resp1.status_code == 200
        db.refresh(rep1)
        created_zone_id = rep1.zone_id
        assert created_zone_id is not None

        # Verify User A trust score credited (+5)
        db.refresh(user_a.profile)
        assert user_a.profile.trust_score == 55
        assert user_a.profile.reports_approved == 1

        # 4. Check Nearby Zones API for Report 2
        nearby_resp = client.get(f"/api/v1/admin/zones/nearby?report_id={rep2.id}&max_distance_meters=500")
        assert nearby_resp.status_code == 200
        nearby_zones = nearby_resp.json()
        assert len(nearby_zones) >= 1
        assert any(z["id"] == created_zone_id for z in nearby_zones)

        # 5. Merge Report 2 into the existing Zone
        resp2 = client.post(
            f"/api/v1/admin/reports/{rep2.id}/approve",
            json={"action": "MERGE", "target_zone_id": created_zone_id}
        )
        assert resp2.status_code == 200
        db.refresh(rep2)
        assert rep2.zone_id == created_zone_id

        # Verify User B trust score credited (+5) upon merge
        db.refresh(user_b.profile)
        assert user_b.profile.trust_score == 55
        assert user_b.profile.reports_approved == 1

        # 6. Verify Avoidance Zone reflects both reports
        zone = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == created_zone_id).first()
        assert zone is not None
        assert len(zone.reports) == 2
        assert zone.severity == "high"

        # 7. Cleanup
        db.delete(rep1)
        db.delete(rep2)
        db.delete(zone)
        db.delete(user_a.profile)
        db.delete(user_b.profile)
        db.delete(user_a)
        db.delete(user_b)
        db.commit()

    finally:
        db.close()
