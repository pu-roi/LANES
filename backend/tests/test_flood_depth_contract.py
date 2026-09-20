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
