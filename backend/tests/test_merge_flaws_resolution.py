from datetime import datetime, timezone, timedelta
import pytest
from geoalchemy2.elements import WKTElement
from app.models.report import FloodReport, ReportSeverity, ReportStatus, ReportSource
from app.services.merge_service import detect_conflicts, synthesize_merged_geometry
import app.services.merge_service as ms


@pytest.fixture(autouse=True)
def fast_valhalla_mock(monkeypatch):
    """Prevent network timeouts during automated testing."""
    def fake_route(start, end, **kwargs):
        return None
    monkeypatch.setattr(ms, "request_valhalla_route", fake_route)


def test_receding_water_trend_detected():
    """Flaw 2: When a newer report submitted >= 30m later indicates lower severity/depth,
    detect_conflicts should flag a receding_trend and suggest the newer value."""
    base_time = datetime(2026, 10, 23, 10, 0, tzinfo=timezone.utc)
    later_time = base_time + timedelta(minutes=75)

    rep_early = FloodReport(
        id=101,
        severity=ReportSeverity.HIGH,
        depth="waist",
        created_at=base_time,
        status=ReportStatus.PENDING,
        source=ReportSource.USER_REPORT,
        raw_text="Deep water",
    )
    rep_later = FloodReport(
        id=102,
        severity=ReportSeverity.LOW,
        depth="gutter",
        created_at=later_time,
        status=ReportStatus.PENDING,
        source=ReportSource.USER_REPORT,
        raw_text="Waters receding now",
    )

    conflicts = detect_conflicts(rep_early, rep_later)
    assert len(conflicts) >= 2

    sev_conflict = next((c for c in conflicts if c.field == "severity"), None)
    assert sev_conflict is not None
    assert sev_conflict.conflict_type == "receding_trend"
    assert sev_conflict.suggested_value == "low"
    assert "Receding flood trend detected" in sev_conflict.message

    depth_conflict = next((c for c in conflicts if c.field == "depth"), None)
    assert depth_conflict is not None
    assert depth_conflict.conflict_type == "receding_trend"
    assert depth_conflict.suggested_value == "gutter"


def test_standard_safety_peak_severity_when_rising_or_concurrent():
    """When a higher severity report comes in concurrently or as flood is rising,
    peak severity must be suggested."""
    base_time = datetime(2026, 10, 23, 10, 0, tzinfo=timezone.utc)
    later_time = base_time + timedelta(minutes=15)

    rep1 = FloodReport(
        id=201,
        severity=ReportSeverity.LOW,
        depth="ankle",
        created_at=base_time,
        status=ReportStatus.PENDING,
        source=ReportSource.USER_REPORT,
        raw_text="Shallow water",
    )
    rep2 = FloodReport(
        id=202,
        severity=ReportSeverity.HIGH,
        depth="waist",
        created_at=later_time,
        status=ReportStatus.PENDING,
        source=ReportSource.USER_REPORT,
        raw_text="Flood rising fast",
    )

    conflicts = detect_conflicts(rep1, rep2)
    sev_conflict = next((c for c in conflicts if c.field == "severity"), None)
    assert sev_conflict is not None
    assert sev_conflict.conflict_type == "discrepancy"
    # Must suggest higher severity for disaster safety
    assert sev_conflict.suggested_value == "high"


def test_synthesize_merged_geometry_for_point_reports():
    """Flaw 3: Point citizen reports should be synthesized into a LineString."""
    rep1 = FloodReport(
        id=301,
        status=ReportStatus.PENDING,
        source=ReportSource.USER_REPORT,
        raw_text="Point A",
        geometry=WKTElement("SRID=4326;POINT(121.0800 14.5700)", srid=4326),
    )
    rep2 = FloodReport(
        id=302,
        status=ReportStatus.PENDING,
        source=ReportSource.USER_REPORT,
        raw_text="Point B",
        geometry=WKTElement("SRID=4326;POINT(121.0820 14.5710)", srid=4326),
    )

    geom, is_bidi = synthesize_merged_geometry([rep1, rep2], db=None)
    assert geom is not None
    assert geom["type"] == "LineString"
    assert len(geom["coordinates"]) >= 2


def test_synthesize_merged_geometry_bridges_small_gap():
    """Flaw 1: Two disjoint LineStrings with a small gap (<= 150m) should be bridged into a continuous LineString."""
    # ~75m gap between 121.0810 and 121.0817 at latitude 14.57
    rep1 = FloodReport(
        id=401,
        status=ReportStatus.PENDING,
        source=ReportSource.USER_REPORT,
        raw_text="Section 1",
        geometry=WKTElement("SRID=4326;LINESTRING(121.0800 14.5700, 121.0810 14.5700)", srid=4326),
    )
    rep2 = FloodReport(
        id=402,
        status=ReportStatus.PENDING,
        source=ReportSource.USER_REPORT,
        raw_text="Section 2",
        geometry=WKTElement("SRID=4326;LINESTRING(121.0817 14.5700, 121.0827 14.5700)", srid=4326),
    )

    geom, is_bidi = synthesize_merged_geometry([rep1, rep2], db=None)
    assert geom is not None
    assert geom["type"] == "LineString", f"Expected bridged LineString, got {geom['type']}"


def test_synthesize_merged_geometry_keeps_large_gap_disconnected():
    """Lines separated by > 150m should remain MultiLineString for explicit admin boundary review."""
    # ~550m gap between 121.0810 and 121.0860
    rep1 = FloodReport(
        id=501,
        status=ReportStatus.PENDING,
        source=ReportSource.USER_REPORT,
        raw_text="Section far west",
        geometry=WKTElement("SRID=4326;LINESTRING(121.0800 14.5700, 121.0810 14.5700)", srid=4326),
    )
    rep2 = FloodReport(
        id=502,
        status=ReportStatus.PENDING,
        source=ReportSource.USER_REPORT,
        raw_text="Section far east",
        geometry=WKTElement("SRID=4326;LINESTRING(121.0860 14.5700, 121.0870 14.5700)", srid=4326),
    )

    geom, is_bidi = synthesize_merged_geometry([rep1, rep2], db=None)
    assert geom is not None
    assert geom["type"] == "MultiLineString"
