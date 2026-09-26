import pytest
from pydantic import ValidationError

from app import models, schemas


def test_report_depth_is_normalized_and_must_match_severity() -> None:
    report = schemas.FloodReportCreate(
        raw_text="Flooded road",
        source=models.ReportSource.USER_REPORT,
        severity=models.ReportSeverity.LOW,
        depth="Half-Knee",
    )
    assert report.depth == "half-knee"

    with pytest.raises(ValidationError, match="Severity must match"):
        schemas.FloodReportCreate(
            raw_text="Flooded road",
            source=models.ReportSource.USER_REPORT,
            severity=models.ReportSeverity.EXTREME,
            depth="gutter",
        )


def test_official_zone_requires_a_canonical_depth() -> None:
    geometry = schemas.PolygonGeometry(
        type="Polygon",
        coordinates=[[[121.0, 14.5], [121.1, 14.5], [121.1, 14.6], [121.0, 14.5]]],
    )
    with pytest.raises(ValidationError):
        schemas.FloodAvoidanceZoneCreateOfficial(
            geometry=geometry,
            severity_override=models.ReportSeverity.LOW,
        )

    zone = schemas.FloodAvoidanceZoneCreateOfficial(
        geometry=geometry,
        severity_override=models.ReportSeverity.EXTREME,
        depth_override="Neck & Above",
    )
    assert zone.depth_override == "neck"


def test_all_mmda_depth_measurements() -> None:
    from app.services.flood_depth import (
        FLOOD_DEPTH_MEASUREMENTS,
        get_flood_depth_measurement,
    )

    expected = {
        "gutter": (8.0, 0.20, 20.32, '8" (0.20m)', "PATV", models.ReportSeverity.LOW),
        "half-knee": (10.0, 0.25, 25.40, '10" (0.25m)', "PATV", models.ReportSeverity.LOW),
        "half-tire": (13.0, 0.33, 33.02, '13" (0.33m)', "NPLV", models.ReportSeverity.MEDIUM),
        "knee": (19.0, 0.48, 48.26, '19" (0.48m)', "NPLV", models.ReportSeverity.MEDIUM),
        "tires": (26.0, 0.66, 66.04, '26" (0.66m)', "NPATV", models.ReportSeverity.HIGH),
        "waist": (37.0, 0.94, 93.98, '37" (0.94m)', "NPATV", models.ReportSeverity.HIGH),
        "chest": (45.0, 1.14, 114.30, '45" (1.14m)', "NPATV", models.ReportSeverity.HIGH),
        "neck": (55.0, 1.40, 140.0, '55"+ (1.40m+)', "NPATV", models.ReportSeverity.EXTREME),
    }

    assert len(FLOOD_DEPTH_MEASUREMENTS) == 8
    for key, (inches, meters, cm, formatted, acc_class, severity) in expected.items():
        spec = get_flood_depth_measurement(key)
        assert spec is not None, f"Missing spec for {key}"
        assert spec.inches == inches
        assert spec.meters == meters
        assert spec.centimeters == cm
        assert spec.formatted == formatted
        assert spec.accessibility_class == acc_class
        assert spec.severity == severity


def test_format_flood_depth() -> None:
    from app.services.flood_depth import format_flood_depth

    assert format_flood_depth("knee") == 'Knee • 19" (0.48m)'
    assert format_flood_depth("half-tire") == 'Half-Tire • 13" (0.33m)'
    assert format_flood_depth("gutter") == 'Gutter • 8" (0.20m)'
    assert format_flood_depth(None) is None


def test_report_schema_populates_depth_measurements() -> None:
    report = schemas.FloodReportCreate(
        raw_text="Flooded intersection",
        source=models.ReportSource.USER_REPORT,
        severity=models.ReportSeverity.MEDIUM,
        depth="knee",
    )
    assert report.depth == "knee"
    assert report.depth_meters == 0.48
    assert report.depth_inches == 19.0
    assert report.depth_formatted == '19" (0.48m)'


def test_zone_response_populates_depth_measurements() -> None:
    from datetime import datetime, timezone

    geometry = schemas.PolygonGeometry(
        type="Polygon",
        coordinates=[[[121.0, 14.5], [121.1, 14.5], [121.1, 14.6], [121.0, 14.5]]],
    )
    now = datetime.now(timezone.utc)
    zone = schemas.FloodAvoidanceZoneResponse(
        id=1,
        geometry=geometry,
        severity="high",
        depth="waist",
        created_at=now,
        updated_at=now,
    )
    assert zone.depth_meters == 0.94
    assert zone.depth_inches == 37.0
    assert zone.depth_formatted == '37" (0.94m)'


def test_model_depth_properties() -> None:
    report = models.FloodReport(
        raw_text="Flooded street",
        source=models.ReportSource.USER_REPORT,
        severity=models.ReportSeverity.MEDIUM,
        depth="knee",
    )
    assert report.depth_meters == 0.48
    assert report.depth_inches == 19.0
    assert report.depth_formatted == 'Knee • 19" (0.48m)'

    zone = models.FloodAvoidanceZone(
        depth_override="gutter",
        severity_override=models.ReportSeverity.LOW,
    )
    assert zone.depth_meters == 0.20
    assert zone.depth_inches == 8.0
    assert zone.depth_formatted == 'Gutter • 8" (0.20m)'

    event = models.FloodEvent(
        peak_severity=models.ReportSeverity.HIGH,
        peak_depth="chest",
    )
    assert event.peak_depth_meters == 1.14
    assert event.peak_depth_inches == 45.0
    assert event.peak_depth_formatted == 'Chest • 45" (1.14m)'
