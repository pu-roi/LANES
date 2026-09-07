import pytest
from app.services.geocoding_service import reverse_geocode_structured, _clean_barangay_name
from app.services.report_service import extract_representative_coordinates, process_new_report
from app.core.database import SessionLocal
from app.models.report import FloodReport, ReportStatus


def test_clean_barangay_name():
    assert _clean_barangay_name("Barangay Maybunga") == "Maybunga"
    assert _clean_barangay_name("Brgy. San Antonio") == "San Antonio"
    assert _clean_barangay_name("Brgy Kapitolyo") == "Kapitolyo"
    assert _clean_barangay_name("Ugong") == "Ugong"
    assert _clean_barangay_name(None) is None


def test_extract_representative_coordinates():
    # Point
    point_geom = {"type": "Point", "coordinates": [121.0842, 14.5746]}
    coords = extract_representative_coordinates(point_geom)
    assert coords is not None
    lat, lng = coords
    assert round(lat, 4) == 14.5746
    assert round(lng, 4) == 121.0842

    # LineString (3 points -> picks middle point)
    line_geom = {
        "type": "LineString",
        "coordinates": [
            [121.0800, 14.5700],
            [121.0850, 14.5750],
            [121.0900, 14.5800]
        ]
    }
    coords_line = extract_representative_coordinates(line_geom)
    assert coords_line is not None
    lat_mid, lng_mid = coords_line
    assert round(lat_mid, 4) == 14.5750
    assert round(lng_mid, 4) == 121.0850

    # MultiLineString
    multi_line = {
        "type": "MultiLineString",
        "coordinates": [
            [
                [121.0700, 14.5600],
                [121.0750, 14.5650]
            ]
        ]
    }
    coords_multi = extract_representative_coordinates(multi_line)
    assert coords_multi is not None
    lat_m, lng_m = coords_multi
    assert round(lat_m, 4) == 14.5650
    assert round(lng_m, 4) == 121.0750


@pytest.mark.asyncio
async def test_reverse_geocode_structured():
    # Known coordinates for C. Raymundo Avenue, Pasig
    lat, lng = 14.574655, 121.084252
    parsed = await reverse_geocode_structured(lat, lng)
    assert parsed is not None
    assert parsed.street is not None
    assert "Raymundo" in parsed.street or "Pasig" in (parsed.city or "")
    assert parsed.city is not None


@pytest.mark.asyncio
async def test_process_new_report_auto_geocoding():
    db = SessionLocal()
    created_report_id = None
    try:
        # Submit report with coordinates only (no street, barangay, or city)
        line_geom = {
            "type": "LineString",
            "coordinates": [
                [121.08378, 14.57376],
                [121.08425, 14.57465],
                [121.08489, 14.57596]
            ]
        }
        report = await process_new_report(
            db=db,
            raw_text="Test flooded road segment with auto geocoding",
            source="direct_user",
            severity="medium",
            is_public=False,
            geometry=line_geom
        )
        assert report is not None
        assert report.id is not None
        created_report_id = report.id

        # Verify automated location fields were saved
        saved = db.query(FloodReport).filter(FloodReport.id == report.id).first()
        assert saved is not None
        assert saved.human_readable_location is not None
        assert saved.barangay is not None
        assert saved.city is not None
        print(f"Created and verified report #{saved.id}: {saved.human_readable_location}, Brgy. {saved.barangay}, {saved.city}")
    finally:
        # Clean up test report
        if created_report_id:
            test_rep = db.query(FloodReport).filter(FloodReport.id == created_report_id).first()
            if test_rep:
                db.delete(test_rep)
                db.commit()
        db.close()
