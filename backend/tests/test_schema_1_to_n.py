import pytest
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import SessionLocal
from app import models, schemas, crud
from geoalchemy2.elements import WKTElement

def test_1_to_n_flood_avoidance_zone_relationships():
    """
    Test that multiple FloodReport records can link to a single FloodAvoidanceZone,
    and that the zone properties aggregate report metadata appropriately.
    """
    db: Session = SessionLocal()
    try:
        # 1. Create a dummy test user
        user = db.query(models.User).filter(models.User.username == "test_reporter_1n").first()
        if not user:
            user = models.User(
                username="test_reporter_1n",
                email="test_reporter_1n@lanes.ph",
                hashed_password="hashed_pw_test",
                role_id=1,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # 2. Create two separate FloodReports on the same road
        line_wkt = "SRID=4326;LINESTRING(121.070 14.580, 121.075 14.585)"
        report1 = models.FloodReport(
            user_id=user.id,
            raw_text="Flood near Tiendesitas - knee deep",
            source=models.ReportSource.USER_REPORT,
            severity=models.ReportSeverity.MEDIUM,
            depth="Knee",
            status=models.ReportStatus.PENDING,
            barangay="Ugong",
            geometry=WKTElement(line_wkt, srid=4326)
        )
        report2 = models.FloodReport(
            user_id=user.id,
            raw_text="Tiendesitas heavy flood - waist deep",
            source=models.ReportSource.USER_REPORT,
            severity=models.ReportSeverity.HIGH,
            depth="Waist",
            status=models.ReportStatus.PENDING,
            barangay="Ugong",
            geometry=WKTElement(line_wkt, srid=4326)
        )
        db.add_all([report1, report2])
        db.commit()
        db.refresh(report1)
        db.refresh(report2)

        # 3. Create a single Avoidance Zone linked to Report 1
        poly_coords = [
            [121.070, 14.580],
            [121.075, 14.580],
            [121.075, 14.585],
            [121.070, 14.585],
            [121.070, 14.580]
        ]
        poly_geom = schemas.PolygonGeometry(type="Polygon", coordinates=[poly_coords])
        zone_in = schemas.FloodAvoidanceZoneCreate(
            report_id=report1.id,
            geometry=poly_geom,
            curated_by_admin_id=user.id
        )
        zone = crud.create_flood_avoidance_zone(db, zone_in)
        assert zone is not None
        assert zone.id is not None
        assert zone.curated_by_admin_id == user.id

        # Refresh report 1
        db.refresh(report1)
        assert report1.zone_id == zone.id
        assert report1.status == models.ReportStatus.APPROVED

        # 4. Merge Report 2 into the existing Zone
        report2.zone_id = zone.id
        report2.status = models.ReportStatus.APPROVED
        report2.approved_at = datetime.utcnow()
        db.commit()

        # 5. Assert 1:N Relationship Integrity
        db.refresh(zone)
        assert len(zone.reports) == 2
        assert report1 in zone.reports
        assert report2 in zone.reports

        # 6. Assert zone severity picks highest severity (HIGH > MEDIUM)
        assert zone.severity == "high"
        assert zone.reporter_name == "test_reporter_1n"

        # 7. Cleanup
        db.delete(report1)
        db.delete(report2)
        db.delete(zone)
        db.delete(user)
        db.commit()
        
    finally:
        db.close()
