from sqlalchemy.orm import Session

from app import models, schemas
from app.services.flood_event_service import (
    create_verified_event_with_zone,
    deactivate_zone_and_end_event_if_final,
    get_event_metrics,
    record_zone_update,
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
    finally:
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
        barangay="San Antonio",
    )
    event = None
    zone = None
    try:
        db_session.add(report)
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

        zone.severity_override = models.ReportSeverity.EXTREME
        zone.depth_override = "Chest"
        record_zone_update(db_session, zone, {"severity_override": "extreme", "depth_override": "Chest"})
        db_session.refresh(event)
        metrics = get_event_metrics(db_session, event)
        assert metrics["evidence_count"] == 1
        assert metrics["supporting_report_count"] == 1
        assert metrics["active_zone_count"] == 1
        assert metrics["location_count"] == 1
        assert metrics["peak_severity"] == "extreme"
        assert db_session.query(models.FloodEventTimelineEntry).filter(
            models.FloodEventTimelineEntry.event_id == event.id,
            models.FloodEventTimelineEntry.entry_type == "zone_updated",
        ).count() == 1
    finally:
        if report.id:
            db_session.query(models.FloodReport).filter(models.FloodReport.id == report.id).delete()
        if zone is not None:
            db_session.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone.id).delete()
        if event is not None:
            db_session.query(models.FloodEvent).filter(models.FloodEvent.id == event.id).delete()
        db_session.commit()
