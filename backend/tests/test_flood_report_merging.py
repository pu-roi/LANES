import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.api import deps
from app.core.database import SessionLocal
from app import models, schemas
from geoalchemy2.elements import WKTElement

def override_admin():
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.username == "admin").first()
    if not user:
        user = models.User(
            username="admin",
            email="admin@lanes.ph",
            hashed_password="hashed_placeholder",
            role_id=1,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()
    return user

app.dependency_overrides[deps.get_current_active_admin] = override_admin
app.dependency_overrides[deps.get_current_user] = override_admin

client = TestClient(app)

def test_intelligent_merge_engine_and_feed_immutability():
    db: Session = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == "merge_tester").first()
        if not user:
            user = models.User(
                username="merge_tester",
                email="merge_tester@lanes.ph",
                hashed_password="pw",
                role_id=1,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            profile = models.Profile(user_id=user.id, first_name="Merge", last_name="Tester", trust_score=50)
            db.add(profile)
            db.commit()

        geom1_wkt = "SRID=4326;LINESTRING(121.0945 14.5820, 121.0965 14.5840)"
        geom2_wkt = "SRID=4326;LINESTRING(121.0950 14.5825, 121.0970 14.5845)"

        rep1 = models.FloodReport(
            user_id=user.id,
            raw_text="Flood along Amang Rodriguez Ave knee deep",
            source=models.ReportSource.USER_REPORT,
            severity=models.ReportSeverity.MEDIUM,
            depth="knee",
            status=models.ReportStatus.PENDING,
            barangay="Manggahan",
            city="Pasig City",
            is_public=True,
            geometry=WKTElement(geom1_wkt, srid=4326),
        )

        rep2 = models.FloodReport(
            user_id=user.id,
            raw_text="High water level on Amang Rodriguez Avenue",
            source=models.ReportSource.USER_REPORT,
            severity=models.ReportSeverity.HIGH,
            depth="waist",
            status=models.ReportStatus.PENDING,
            barangay="Manggahan",
            city="Pasig City",
            is_public=True,
            geometry=WKTElement(geom2_wkt, srid=4326),
        )

        db.add_all([rep1, rep2])
        db.commit()
        db.refresh(rep1)
        db.refresh(rep2)

        post1 = models.CommunityPost(
            user_id=user.id,
            flood_report_id=rep1.id,
            content="Flood along Amang Rodriguez Ave knee deep",
            media_urls=[]
        )
        post2 = models.CommunityPost(
            user_id=user.id,
            flood_report_id=rep2.id,
            content="High water level on Amang Rodriguez Avenue",
            media_urls=[]
        )
        db.add_all([post1, post2])
        db.commit()
        db.refresh(post1)
        db.refresh(post2)

        post1_id = post1.id
        post2_id = post2.id

        resp_cand = client.get(f"/api/v1/admin/reports/merge-candidates?report_id={rep1.id}")
        assert resp_cand.status_code == 200
        data_cand = resp_cand.json()
        assert "candidates" in data_cand
        assert len(data_cand["candidates"]) >= 1

        cand_entry = next((c for c in data_cand["candidates"] if c["report_id"] == rep2.id), None)
        assert cand_entry is not None
        assert cand_entry["match_score"] > 0
        assert len(cand_entry["match_reasons"]) > 0

        merge_payload = {
            "primary_report_id": rep1.id,
            "merged_report_ids": [rep2.id],
            "final_data": {
                "severity": "high",
                "depth": "waist",
                "passable_vehicles": "heavy",
                "hidden_hazards": "yes",
                "is_bidirectional": True,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [121.0945, 14.5820],
                        [121.0970, 14.5845]
                    ]
                },
                "admin_notes": "Merged reports from community reporters",
                "merge_rationale": "High corridor overlap and name match",
                "buffer_radius": 25.0
            }
        }

        resp_merge = client.post("/api/v1/admin/reports/merge", json=merge_payload)
        assert resp_merge.status_code == 200
        merge_result = resp_merge.json()
        assert merge_result["zone_id"] is not None
        assert merge_result["merged_count"] == 2
        zone_id = merge_result["zone_id"]

        db.refresh(rep1)
        db.refresh(rep2)
        assert rep1.status == models.ReportStatus.APPROVED
        assert rep2.status == models.ReportStatus.APPROVED
        assert rep1.zone_id == zone_id
        assert rep2.zone_id == zone_id

        stored_post1 = db.query(models.CommunityPost).filter(models.CommunityPost.id == post1_id).first()
        stored_post2 = db.query(models.CommunityPost).filter(models.CommunityPost.id == post2_id).first()
        assert stored_post1 is not None
        assert stored_post2 is not None
        assert stored_post1.flood_report_id == rep1.id
        assert stored_post2.flood_report_id == rep2.id
        assert stored_post1.content == "Flood along Amang Rodriguez Ave knee deep"
        assert stored_post2.content == "High water level on Amang Rodriguez Avenue"

        zone = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone_id).first()
        assert zone is not None
        assert zone.passable_vehicles_override == "heavy"
        assert zone.hidden_hazards_override == "yes"
        assert zone.merge_rationale == "High corridor overlap and name match"
        assert zone.severity_override == models.ReportSeverity.HIGH

    finally:
        db.close()
