from datetime import datetime
from app.schemas.report import (
    FloodReportResponse,
    FloodAvoidanceZoneResponse,
    ZoneContributorResponse,
    NearbyZoneResponse,
    MergeCandidateItem,
)
from app.schemas.flood_event import (
    FloodEventResponse,
    FloodEventLocationResponse,
    FloodEventTimelineEntryResponse,
    FloodReportModerationOutcomeResponse,
)
from app.schemas.audit import AuditLogResponse
from app.models.report import ReportStatus, ReportSeverity, ReportSource, FloodEventStatus
from app.schemas.common import PolygonGeometry


def test_flood_report_response_utc_serialization():
    dt = datetime(2026, 9, 22, 2, 54, 0)
    report = FloodReportResponse(
        id=1,
        raw_text="Flood at Emerald Ave",
        source=ReportSource.USER_REPORT,
        severity=ReportSeverity.HIGH,
        status=ReportStatus.PENDING,
        created_at=dt,
        updated_at=dt,
        approved_at=dt,
    )
    dumped = report.model_dump(mode="json")
    assert dumped["created_at"] == "2026-09-22T02:54:00Z"
    assert dumped["updated_at"] == "2026-09-22T02:54:00Z"
    assert dumped["approved_at"] == "2026-09-22T02:54:00Z"


def test_flood_avoidance_zone_response_utc_serialization():
    dt = datetime(2026, 9, 22, 2, 54, 0)
    geom = PolygonGeometry(type="Polygon", coordinates=[[[121.0, 14.5], [121.1, 14.5], [121.1, 14.6], [121.0, 14.5]]])
    zone = FloodAvoidanceZoneResponse(
        id=10,
        geometry=geom,
        severity="high",
        created_at=dt,
        updated_at=dt,
        expires_at=dt,
    )
    dumped = zone.model_dump(mode="json")
    assert dumped["created_at"] == "2026-09-22T02:54:00Z"
    assert dumped["updated_at"] == "2026-09-22T02:54:00Z"
    assert dumped["expires_at"] == "2026-09-22T02:54:00Z"


def test_zone_contributor_response_utc_serialization():
    dt = datetime(2026, 9, 22, 2, 54, 0)
    contrib = ZoneContributorResponse(
        report_id=5,
        reporter_name="Juan",
        raw_text="Knee deep flood",
        severity="medium",
        created_at=dt,
    )
    dumped = contrib.model_dump(mode="json")
    assert dumped["created_at"] == "2026-09-22T02:54:00Z"


def test_flood_event_response_utc_serialization():
    dt = datetime(2026, 9, 22, 2, 54, 0)
    event = FloodEventResponse(
        id=100,
        status=FloodEventStatus.ACTIVE,
        first_reported_at=dt,
        verified_at=dt,
        ended_at=None,
        peak_severity=ReportSeverity.EXTREME,
        created_at=dt,
        updated_at=dt,
    )
    dumped = event.model_dump(mode="json")
    assert dumped["first_reported_at"] == "2026-09-22T02:54:00Z"
    assert dumped["verified_at"] == "2026-09-22T02:54:00Z"
    assert dumped["ended_at"] is None
    assert dumped["created_at"] == "2026-09-22T02:54:00Z"
    assert dumped["updated_at"] == "2026-09-22T02:54:00Z"


def test_audit_log_response_utc_serialization():
    dt = datetime(2026, 9, 22, 2, 54, 0)
    audit = AuditLogResponse(
        id=7,
        admin_id=1,
        action_type="CREATE_OFFICIAL_ZONE",
        target_table="flood_avoidance_zones",
        created_at=dt,
    )
    dumped = audit.model_dump(mode="json")
    assert dumped["created_at"] == "2026-09-22T02:54:00Z"
