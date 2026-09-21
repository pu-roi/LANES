from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app import models, schemas
from app.services.flood_event_service import (
    create_verified_event_with_zone,
    deactivate_zone_and_end_event_if_final,
    get_flood_event_planning_analytics,
    get_event_metrics,
    link_supporting_report,
    record_zone_update,
    reject_report,
    serialize_flood_event_planning_records,
)


def test_verified_event_ends_when_its_final_zone_deactivates(db_session: Session) -> None:
    admin = db_session.query(models.User).filter(models.User.username == "admin").first()
    assert admin is not None

    polygon = schemas.PolygonGeometry(
        type="Polygon",
        coordinates=[[
            [121.0800, 14.5700], [121.0805, 14.5700], [121.0805, 14.5705],
            [121.0800, 14.5705], [121.0800, 14.5700],
        ]],
    )
    event = None
    zone = None
    new_event = None
    new_zone = None
    try:
        event, zone = create_verified_event_with_zone(
            db=db_session,
            zone_input=schemas.FloodAvoidanceZoneCreate(
                geometry=polygon,
                curated_by_admin_id=admin.id,
                is_active=True,
            ),
            peak_severity=models.ReportSeverity.HIGH,
            peak_depth="Knee",
            acted_by_user_id=admin.id,
        )

        assert zone.event_id == event.id
        assert event.status == models.FloodEventStatus.ACTIVE
        assert db_session.query(models.FloodEventTimelineEntry).filter(
            models.FloodEventTimelineEntry.event_id == event.id,
            models.FloodEventTimelineEntry.entry_type == "event_verified",
        ).count() == 1

        deactivate_zone_and_end_event_if_final(db_session, zone)
        db_session.refresh(event)
        assert event.status == models.FloodEventStatus.ENDED
        assert event.ended_at is not None

        # A later, newly verified official zone must begin a new incident; an
        # ended event is historical evidence and must never be reactivated.
        new_event, new_zone = create_verified_event_with_zone(
            db=db_session,
            zone_input=schemas.FloodAvoidanceZoneCreate(geometry=polygon, is_active=True),
            peak_severity=models.ReportSeverity.MEDIUM,
            peak_depth="Ankle",
            acted_by_user_id=admin.id,
        )
        assert new_event.id != event.id
        assert new_zone.event_id == new_event.id
        assert new_event.status == models.FloodEventStatus.ACTIVE
    finally:
        if new_zone is not None:
            db_session.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == new_zone.id).delete()
        if new_event is not None:
            db_session.query(models.FloodEvent).filter(models.FloodEvent.id == new_event.id).delete()
        if zone is not None:
            db_session.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone.id).delete()
        if event is not None:
            db_session.query(models.FloodEvent).filter(models.FloodEvent.id == event.id).delete()
        db_session.commit()


def test_event_metrics_zone_timeline_and_create_retry_are_server_owned(db_session: Session) -> None:
    polygon = schemas.PolygonGeometry(
        type="Polygon",
        coordinates=[[
            [121.0810, 14.5710], [121.0815, 14.5710], [121.0815, 14.5715],
            [121.0810, 14.5715], [121.0810, 14.5710],
        ]],
    )
    report = models.FloodReport(
        raw_text="Service metrics test report",
        source=models.ReportSource.USER_REPORT,
        severity=models.ReportSeverity.MEDIUM,
        depth="Ankle",
        status=models.ReportStatus.PENDING,
        human_readable_location="First Road",
        barangay="San Antonio",
    )
    supporting_report = models.FloodReport(
        raw_text="Corroborating severity test report",
        source=models.ReportSource.USER_REPORT,
        severity=models.ReportSeverity.EXTREME,
        depth="Chest",
        status=models.ReportStatus.PENDING,
        human_readable_location="Second Road",
        barangay="Sampaguita",
    )
    event = None
    zone = None
    try:
        db_session.add_all([report, supporting_report])
        db_session.commit()
        db_session.refresh(report)
        event, zone = create_verified_event_with_zone(
            db=db_session,
            zone_input=schemas.FloodAvoidanceZoneCreate(geometry=polygon, is_active=True),
            peak_severity=models.ReportSeverity.MEDIUM,
            peak_depth="Ankle",
            acted_by_user_id=1,
            source_report=report,
        )

        retry_event, retry_zone = create_verified_event_with_zone(
            db=db_session,
            zone_input=schemas.FloodAvoidanceZoneCreate(geometry=polygon, is_active=True),
            peak_severity=models.ReportSeverity.MEDIUM,
            peak_depth="Ankle",
            acted_by_user_id=1,
            source_report=report,
        )
        assert (retry_event.id, retry_zone.id) == (event.id, zone.id)
        assert db_session.query(models.FloodEvent).filter(models.FloodEvent.id == event.id).count() == 1

        linked_report = link_supporting_report(
            db_session, supporting_report, event, zone, acted_by_user_id=1
        )
        db_session.refresh(event)
        assert linked_report.event_id == event.id
        assert linked_report.zone_id == zone.id
        assert linked_report.status == models.ReportStatus.APPROVED
        assert event.peak_severity == models.ReportSeverity.EXTREME
        assert event.peak_depth == "Chest"
        locations = {
            (location.location_type.value, location.display_name)
            for location in db_session.query(models.FloodEventLocation).filter(
                models.FloodEventLocation.event_id == event.id
            )
        }
        assert {("road", "First Road"), ("road", "Second Road"), ("barangay", "San Antonio"), ("barangay", "Sampaguita")} <= locations

        zone.severity_override = models.ReportSeverity.EXTREME
        zone.depth_override = "Chest"
        record_zone_update(db_session, zone, {"severity_override": "extreme", "depth_override": "Chest"})
        db_session.refresh(event)
        metrics = get_event_metrics(db_session, event)
        assert metrics["evidence_count"] == 2
        assert metrics["supporting_report_count"] == 2
        assert metrics["reporter_count"] == 0
        assert metrics["duration_minutes"] is None
        assert metrics["active_zone_count"] == 1
        assert metrics["location_count"] == 4
        assert metrics["peak_severity"] == "extreme"
        assert db_session.query(models.FloodEventTimelineEntry).filter(
            models.FloodEventTimelineEntry.event_id == event.id,
            models.FloodEventTimelineEntry.entry_type == "zone_updated",
        ).count() == 1
    finally:
        report_ids = [item.id for item in [report, supporting_report] if item.id]
        if report_ids:
            db_session.query(models.FloodReport).filter(models.FloodReport.id.in_(report_ids)).delete(synchronize_session=False)
        if zone is not None:
            db_session.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone.id).delete()
        if event is not None:
            db_session.query(models.FloodEvent).filter(models.FloodEvent.id == event.id).delete()
        db_session.commit()


def test_rejection_reason_other_requires_staff_note(db_session: Session) -> None:
    report = models.FloodReport(
        raw_text="Reason validation test report",
        source=models.ReportSource.USER_REPORT,
        severity=models.ReportSeverity.LOW,
        status=models.ReportStatus.PENDING,
    )
    try:
        db_session.add(report)
        db_session.commit()

        with pytest.raises(ValueError, match="internal note is required"):
            reject_report(
                db_session,
                report,
                models.ReportRejectionReason.OTHER,
                "   ",
                acted_by_user_id=1,
            )
        db_session.refresh(report)
        assert report.status == models.ReportStatus.PENDING
    finally:
        if report.id:
            db_session.query(models.FloodReport).filter(models.FloodReport.id == report.id).delete()
        db_session.commit()


def test_planning_analytics_count_distinct_events_and_keep_reports_separate(db_session: Session) -> None:
    verified_at = datetime.utcnow() - timedelta(days=2)
    ended_event = models.FloodEvent(
        status=models.FloodEventStatus.ENDED,
        verified_at=verified_at,
        ended_at=verified_at + timedelta(hours=2),
        peak_severity=models.ReportSeverity.HIGH,
    )
    active_event = models.FloodEvent(
        status=models.FloodEventStatus.ACTIVE,
        verified_at=verified_at + timedelta(days=1),
        peak_severity=models.ReportSeverity.MEDIUM,
    )
    try:
        db_session.add_all([ended_event, active_event])
        db_session.flush()
        db_session.add_all([
            models.FloodEventLocation(event_id=ended_event.id, location_type=models.FloodEventLocationType.BARANGAY, display_name="San Antonio", normalized_name="san antonio"),
            models.FloodEventLocation(event_id=active_event.id, location_type=models.FloodEventLocationType.BARANGAY, display_name="San Antonio", normalized_name="san antonio"),
            models.FloodEventLocation(event_id=ended_event.id, location_type=models.FloodEventLocationType.ROAD, display_name="Example Road", normalized_name="example road"),
            models.FloodReport(event_id=ended_event.id, raw_text="First corroborating report", source=models.ReportSource.USER_REPORT, severity=models.ReportSeverity.HIGH, status=models.ReportStatus.APPROVED),
            models.FloodReport(event_id=ended_event.id, raw_text="Second corroborating report", source=models.ReportSource.USER_REPORT, severity=models.ReportSeverity.HIGH, status=models.ReportStatus.APPROVED),
        ])
        db_session.commit()

        analytics = get_flood_event_planning_analytics(db_session, [ended_event, active_event])
        assert analytics["total_events"] == 2
        assert analytics["ended_events"] == 1
        assert analytics["supporting_report_volume"]["approved_report_count"] == 2
        assert analytics["supporting_report_volume"]["average_per_event"] == 1
        assert analytics["duration"]["average_minutes"] == 120
        assert sum(entry["report_count"] for entry in analytics["approved_reports_over_time"]) == 2
        assert sum(entry["event_count"] for entry in analytics["verification_pattern"]) == 2
        assert analytics["recurring_barangays"] == [{"name": "San Antonio", "event_count": 2}]
        assert analytics["frequently_affected_roads"] == [{"name": "Example Road", "event_count": 1}]

        export_rows = serialize_flood_event_planning_records(db_session, [ended_event, active_event])
        ended_row = next(row for row in export_rows if row["event_id"] == ended_event.id)
        assert ended_row["approved_supporting_report_count"] == 2
        assert "raw_text" not in ended_row
        assert "user_id" not in ended_row
    finally:
        db_session.rollback()
        event_ids = [event_id for event_id in [ended_event.id, active_event.id] if event_id is not None]
        if event_ids:
            db_session.query(models.FloodReport).filter(models.FloodReport.event_id.in_(event_ids)).delete(synchronize_session=False)
            db_session.query(models.FloodEventLocation).filter(models.FloodEventLocation.event_id.in_(event_ids)).delete(synchronize_session=False)
            db_session.query(models.FloodEvent).filter(models.FloodEvent.id.in_(event_ids)).delete(synchronize_session=False)
            db_session.commit()
