"""Transactional lifecycle services for verified Flood Events.

Route handlers delegate here so event history, operational zones, report outcomes,
and reporter trust are updated as one server-side unit of work.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app import models, schemas
from app.schemas.common import ensure_utc, serialize_utc_datetime
from app.crud.report import create_flood_avoidance_zone, credit_user_verified_report, penalize_user_rejected_report
from app.models.notification import Notification, NotificationType


_SEVERITY_ORDER = {
    models.ReportSeverity.LOW: 1,
    models.ReportSeverity.MEDIUM: 2,
    models.ReportSeverity.HIGH: 3,
    models.ReportSeverity.EXTREME: 4,
}

_REJECTION_NOTIFICATION_REASONS = {
    models.ReportRejectionReason.INSUFFICIENT_EVIDENCE: "insufficient supporting evidence",
    models.ReportRejectionReason.INCORRECT_LOCATION_OR_DETAILS: "incorrect location or details",
    models.ReportRejectionReason.FALSE_SPAM_OR_MALICIOUS: "a report classified as false, spam, or malicious",
    models.ReportRejectionReason.OUTSIDE_COVERAGE_AREA: "outside the current coverage area",
    models.ReportRejectionReason.WITHDRAWN: "a withdrawn report",
    models.ReportRejectionReason.OTHER: "the review details provided by the moderation team",
}


def _severity_value(value: models.ReportSeverity | str) -> models.ReportSeverity:
    return value if isinstance(value, models.ReportSeverity) else models.ReportSeverity(value)


def _is_more_severe(candidate: models.ReportSeverity, current: models.ReportSeverity) -> bool:
    return _SEVERITY_ORDER[candidate] > _SEVERITY_ORDER[current]


def _as_manila_time(value: datetime) -> datetime:
    """Treat legacy-naive persistence timestamps as UTC before staff display aggregation."""
    return (value if value.tzinfo else value.replace(tzinfo=UTC)).astimezone(ZoneInfo("Asia/Manila"))


def _append_timeline(
    db: Session,
    event_id: int,
    entry_type: str,
    summary: str,
    snapshot_json: Optional[dict[str, Any]] = None,
    occurred_at: Optional[datetime] = None,
) -> None:
    db.add(models.FloodEventTimelineEntry(
        event_id=event_id,
        entry_type=entry_type,
        summary=summary,
        snapshot_json=snapshot_json,
        occurred_at=ensure_utc(occurred_at) or datetime.now(timezone.utc),
    ))


def _record_report_location_rows(db: Session, event: models.FloodEvent, report: models.FloodReport) -> None:
    locations = (
        (models.FloodEventLocationType.ROAD, report.human_readable_location),
        (models.FloodEventLocationType.BARANGAY, report.barangay),
        (models.FloodEventLocationType.CITY, report.city),
    )
    for location_type, name in locations:
        if not name or not name.strip():
            continue
        cleaned = name.strip()
        normalized = cleaned.lower()
        exists = db.query(models.FloodEventLocation.id).filter(
            models.FloodEventLocation.event_id == event.id,
            models.FloodEventLocation.location_type == location_type,
            models.FloodEventLocation.normalized_name == normalized,
        ).first()
        if not exists:
            db.add(models.FloodEventLocation(
                event_id=event.id,
                location_type=location_type,
                display_name=cleaned,
                normalized_name=normalized,
            ))


def get_event_metrics(
    db: Session,
    event: models.FloodEvent,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Calculate durable event metrics on the server for admin history views."""
    as_of = ensure_utc(now) or datetime.now(timezone.utc)
    active_zone_count = db.query(models.FloodAvoidanceZone.id).filter(
        models.FloodAvoidanceZone.event_id == event.id,
        models.FloodAvoidanceZone.is_active.is_(True),
        (models.FloodAvoidanceZone.expires_at.is_(None)) | (models.FloodAvoidanceZone.expires_at > as_of),
    ).count()
    end_time = ensure_utc(event.ended_at) or as_of
    start_time = ensure_utc(event.verified_at) or as_of
    duration_seconds = max(0, int((end_time - start_time).total_seconds()))
    approved_reports_filter = (
        models.FloodReport.event_id == event.id,
        models.FloodReport.status == models.ReportStatus.APPROVED,
        models.FloodReport.deleted_at.is_(None),
    )
    return {
        "event_id": event.id,
        "status": event.status.value,
        "verified_at": serialize_utc_datetime(event.verified_at),
        "ended_at": serialize_utc_datetime(event.ended_at),
        "duration_seconds": duration_seconds,
        "duration_minutes": (
            duration_seconds // 60
            if event.status == models.FloodEventStatus.ENDED and event.ended_at else None
        ),
        "evidence_count": db.query(models.FloodReport.id).filter(
            *approved_reports_filter,
        ).count(),
        "supporting_report_count": db.query(models.FloodReport.id).filter(
            *approved_reports_filter,
            models.FloodReport.zone_id.is_not(None),
        ).count(),
        "reporter_count": int(db.query(func.count(func.distinct(models.FloodReport.user_id))).filter(
            *approved_reports_filter,
            models.FloodReport.user_id.is_not(None),
        ).scalar() or 0),
        "zone_count": db.query(models.FloodAvoidanceZone.id).filter(
            models.FloodAvoidanceZone.event_id == event.id,
        ).count(),
        "active_zone_count": active_zone_count,
        "location_count": db.query(models.FloodEventLocation.id).filter(
            models.FloodEventLocation.event_id == event.id,
        ).count(),
        "peak_severity": event.peak_severity.value,
        "peak_depth": event.peak_depth,
    }


def build_flood_event_history_query(
    db: Session,
    *,
    status_filter: str = "all",
    severity: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    barangay: Optional[str] = None,
    road: Optional[str] = None,
    search: Optional[str] = None,
) -> Any:
    """Build one authorized-event query for history, planning, and exports.

    A Flood Event is deliberately the aggregation unit here.  Reports are only
    consulted later as a separate confidence signal, so repeated reports can
    never inflate recurrence or duration analytics.
    """
    try:
        status_value = None if status_filter == "all" else models.FloodEventStatus(status_filter)
    except ValueError as exc:
        raise ValueError("Invalid Flood Event status") from exc
    try:
        severity_value = models.ReportSeverity(severity) if severity else None
    except ValueError as exc:
        raise ValueError("Invalid Flood Event severity") from exc

    query = db.query(models.FloodEvent)
    if status_value:
        query = query.filter(models.FloodEvent.status == status_value)
    if severity_value:
        query = query.filter(models.FloodEvent.peak_severity == severity_value)
    if date_from:
        query = query.filter(models.FloodEvent.verified_at >= ensure_utc(date_from))
    if date_to:
        query = query.filter(models.FloodEvent.verified_at <= ensure_utc(date_to))

    barangay_term = barangay.strip() if barangay else ""
    road_term = road.strip() if road else ""
    search_term = search.strip() if search else ""
    if barangay_term or road_term or search_term:
        location_filters = []
        if barangay_term:
            location_filters.append(
                (models.FloodEventLocation.location_type == models.FloodEventLocationType.BARANGAY)
                & models.FloodEventLocation.display_name.ilike(f"%{barangay_term}%")
            )
        if road_term:
            location_filters.append(
                (models.FloodEventLocation.location_type == models.FloodEventLocationType.ROAD)
                & models.FloodEventLocation.display_name.ilike(f"%{road_term}%")
            )
        if search_term:
            pattern = f"%{search_term}%"
            location_filters.extend([
                models.FloodEventLocation.display_name.ilike(pattern),
                models.FloodEventLocation.normalized_name.ilike(pattern),
            ])
        query = query.join(models.FloodEventLocation).filter(or_(*location_filters)).distinct()
    return query


def _event_report_counts(db: Session, event_ids: list[int]) -> dict[int, int]:
    """Return approved, non-deleted report volume by event without user details."""
    if not event_ids:
        return {}
    rows = (
        db.query(models.FloodReport.event_id, func.count(models.FloodReport.id))
        .filter(
            models.FloodReport.event_id.in_(event_ids),
            models.FloodReport.status == models.ReportStatus.APPROVED,
            models.FloodReport.deleted_at.is_(None),
        )
        .group_by(models.FloodReport.event_id)
        .all()
    )
    return {event_id: int(count) for event_id, count in rows if event_id is not None}


def _event_locations(db: Session, event_ids: list[int]) -> dict[int, list[models.FloodEventLocation]]:
    if not event_ids:
        return {}
    locations_by_event: dict[int, list[models.FloodEventLocation]] = defaultdict(list)
    locations = (
        db.query(models.FloodEventLocation)
        .filter(models.FloodEventLocation.event_id.in_(event_ids))
        .order_by(models.FloodEventLocation.location_type, models.FloodEventLocation.display_name)
        .all()
    )
    for location in locations:
        locations_by_event[location.event_id].append(location)
    return locations_by_event


def get_flood_event_planning_analytics(
    db: Session,
    events: list[models.FloodEvent],
) -> dict[str, Any]:
    """Calculate city-planning metrics using distinct verified Flood Events.

    Returned report numbers are an explicitly separate corroboration/confidence
    signal.  Rejected and deleted reports have no place in this aggregation.
    """
    event_ids = [event.id for event in events]
    report_counts = _event_report_counts(db, event_ids)
    locations_by_event = _event_locations(db, event_ids)
    severity_counts = Counter(event.peak_severity.value for event in events)
    daily_counts = Counter(event.verified_at.date().isoformat() for event in events)
    verification_pattern = Counter(
        (
            _as_manila_time(event.verified_at).weekday(),
            _as_manila_time(event.verified_at).hour,
        )
        for event in events
    )
    barangay_counts: Counter[str] = Counter()
    road_counts: Counter[str] = Counter()
    duration_minutes: list[int] = []

    for event in events:
        if event.status == models.FloodEventStatus.ENDED and event.ended_at:
            duration_minutes.append(max(0, int((ensure_utc(event.ended_at) - ensure_utc(event.verified_at)).total_seconds() // 60)))
        # Each normalized place is only counted once per event even if the
        # event gathered multiple corroborating reports from that place.
        seen_places: set[tuple[models.FloodEventLocationType, str]] = set()
        for location in locations_by_event.get(event.id, []):
            place_key = (location.location_type, location.normalized_name)
            if place_key in seen_places:
                continue
            seen_places.add(place_key)
            if location.location_type == models.FloodEventLocationType.BARANGAY:
                barangay_counts[location.display_name] += 1
            elif location.location_type == models.FloodEventLocationType.ROAD:
                road_counts[location.display_name] += 1

    duration_buckets = {
        "under_1_hour": 0,
        "1_to_3_hours": 0,
        "3_to_6_hours": 0,
        "over_6_hours": 0,
    }
    for minutes in duration_minutes:
        if minutes < 60:
            duration_buckets["under_1_hour"] += 1
        elif minutes < 180:
            duration_buckets["1_to_3_hours"] += 1
        elif minutes < 360:
            duration_buckets["3_to_6_hours"] += 1
        else:
            duration_buckets["over_6_hours"] += 1

    def top_places(counts: Counter[str]) -> list[dict[str, Any]]:
        return [
            {"name": name, "event_count": count}
            for name, count in counts.most_common(10)
        ]

    total_reports = sum(report_counts.values())
    report_day_counts: Counter[str] = Counter()
    if event_ids:
        approved_reports = (
            db.query(models.FloodReport)
            .filter(
                models.FloodReport.event_id.in_(event_ids),
                models.FloodReport.status == models.ReportStatus.APPROVED,
                models.FloodReport.deleted_at.is_(None),
            )
            .all()
        )
        for report in approved_reports:
            report_day_counts[(report.approved_at or report.created_at).date().isoformat()] += 1
    ended_count = sum(event.status == models.FloodEventStatus.ENDED for event in events)
    return {
        "total_events": len(events),
        "ended_events": ended_count,
        "active_events": len(events) - ended_count,
        "peak_severity_distribution": [
            {"severity": severity, "event_count": severity_counts[severity]}
            for severity in ("low", "medium", "high", "extreme")
        ],
        "duration": {
            "ended_event_count": len(duration_minutes),
            "average_minutes": round(sum(duration_minutes) / len(duration_minutes), 1) if duration_minutes else None,
            "distribution": [
                {"bucket": "Under 1 hour", "event_count": duration_buckets["under_1_hour"]},
                {"bucket": "1–3 hours", "event_count": duration_buckets["1_to_3_hours"]},
                {"bucket": "3–6 hours", "event_count": duration_buckets["3_to_6_hours"]},
                {"bucket": "Over 6 hours", "event_count": duration_buckets["over_6_hours"]},
            ],
        },
        "events_over_time": [
            {"date": date, "event_count": count}
            for date, count in sorted(daily_counts.items())
        ],
        "approved_reports_over_time": [
            {"date": date, "report_count": count}
            for date, count in sorted(report_day_counts.items())
        ],
        "verification_pattern": [
            {"weekday": weekday, "hour": hour, "event_count": count}
            for (weekday, hour), count in sorted(verification_pattern.items())
        ],
        "recurring_barangays": top_places(barangay_counts),
        "frequently_affected_roads": top_places(road_counts),
        "supporting_report_volume": {
            "approved_report_count": total_reports,
            "average_per_event": round(total_reports / len(events), 1) if events else 0,
        },
        "definitions": {
            "flood_events": "Distinct verified incidents. Repeated reports for one incident count once.",
            "supporting_reports": "Approved, non-deleted reports linked to the selected Flood Events; a confidence signal, not an event count.",
            "peak_verified_severity": "The highest verified severity recorded for each Flood Event.",
            "official_duration": "Time from event verification until the final active zone ended. Active events are excluded from duration averages.",
            "verification_pattern": "Verified Flood Events by Asia/Manila day and hour. This shows verification timing, not when floodwater first began.",
        },
    }


def serialize_flood_event_planning_records(
    db: Session,
    events: list[models.FloodEvent],
) -> list[dict[str, Any]]:
    """Create privacy-safe event rows for planning exports, never raw evidence."""
    event_ids = [event.id for event in events]
    report_counts = _event_report_counts(db, event_ids)
    locations_by_event = _event_locations(db, event_ids)
    rows: list[dict[str, Any]] = []
    for event in events:
        locations = locations_by_event.get(event.id, [])
        rows.append({
            "event_id": event.id,
            "status": event.status.value,
            "first_reported_at": event.first_reported_at,
            "verified_at": event.verified_at,
            "ended_at": event.ended_at,
            "peak_verified_severity": event.peak_severity.value,
            "peak_depth_label": event.peak_depth,
            "official_duration_minutes": (
                max(0, int((event.ended_at - event.verified_at).total_seconds() // 60))
                if event.status == models.FloodEventStatus.ENDED and event.ended_at else None
            ),
            "approved_supporting_report_count": report_counts.get(event.id, 0),
            "barangays": "; ".join(location.display_name for location in locations if location.location_type == models.FloodEventLocationType.BARANGAY),
            "roads": "; ".join(location.display_name for location in locations if location.location_type == models.FloodEventLocationType.ROAD),
            "cities": "; ".join(location.display_name for location in locations if location.location_type == models.FloodEventLocationType.CITY),
        })
    return rows


def record_zone_update(
    db: Session,
    zone: models.FloodAvoidanceZone,
    changes: dict[str, Any],
    commit: bool = True,
) -> None:
    """Append a readable snapshot when staff change an event-owned zone."""
    if not zone.event_id:
        return
    event = zone.flood_event or db.get(models.FloodEvent, zone.event_id)
    if not event:
        raise ValueError("The zone references a Flood Event that no longer exists.")
    occurred_at = datetime.now(timezone.utc)
    severity = zone.severity_override
    if severity and _is_more_severe(_severity_value(severity), _severity_value(event.peak_severity)):
        event.peak_severity = _severity_value(severity)
        event.peak_depth = zone.depth_override
        _append_timeline(
            db, event.id, "severity_peak_changed",
            "Verified event peak severity increased from an official zone update.",
            {"peak_severity": event.peak_severity.value, "peak_depth": event.peak_depth}, occurred_at,
        )
    _append_timeline(
        db, event.id, "zone_updated", "Official flood zone details were updated.",
        {"zone_id": zone.id, "changes": changes}, occurred_at,
    )
    if commit:
        db.commit()
        db.refresh(zone)


def create_verified_event_with_zone(
    db: Session,
    zone_input: schemas.FloodAvoidanceZoneCreate,
    peak_severity: models.ReportSeverity | str,
    peak_depth: Optional[str],
    acted_by_user_id: int,
    source_report: Optional[models.FloodReport] = None,
    zone_snapshot: Optional[dict[str, Any]] = None,
    zone_attributes: Optional[dict[str, Any]] = None,
) -> tuple[models.FloodEvent, models.FloodAvoidanceZone]:
    """Create a verified event and its first operational zone atomically."""
    if source_report and source_report.event_id is not None:
        existing_event = db.get(models.FloodEvent, source_report.event_id)
        existing_zone = db.get(models.FloodAvoidanceZone, source_report.zone_id) if source_report.zone_id else None
        if existing_event and existing_zone:
            return existing_event, existing_zone
        raise ValueError("The report has an incomplete existing Flood Event link and cannot be re-approved.")
    severity = _severity_value(peak_severity)
    verified_at = datetime.now(timezone.utc)
    try:
        event = models.FloodEvent(
            status=models.FloodEventStatus.ACTIVE,
            first_reported_at=ensure_utc(source_report.created_at) if source_report else None,
            verified_at=verified_at,
            peak_severity=severity,
            peak_depth=peak_depth,
        )
        db.add(event)
        db.flush()

        zone = create_flood_avoidance_zone(db, zone_input, event_id=event.id, commit=False)
        for attribute, value in (zone_attributes or {}).items():
            setattr(zone, attribute, value)
        if source_report:
            source_report.event_id = event.id
            source_report.zone_id = zone.id
            source_report.status = models.ReportStatus.APPROVED
            source_report.approved_at = verified_at
            _record_report_location_rows(db, event, source_report)
            db.add(models.FloodReportModerationOutcome(
                report_id=source_report.id,
                outcome=models.ReportModerationOutcomeType.APPROVED,
                event_id=event.id,
                zone_id=zone.id,
                acted_by_user_id=acted_by_user_id,
                acted_at=verified_at,
            ))
            if source_report.user_id:
                credit_user_verified_report(db, source_report.user_id, commit=False)

        _append_timeline(
            db,
            event.id,
            "event_verified",
            "Flood event verified and opened for live operations.",
            {"peak_severity": severity.value, "peak_depth": peak_depth},
            verified_at,
        )
        _append_timeline(
            db,
            event.id,
            "zone_created",
            "Official flood zone created for this event.",
            {"zone_id": zone.id, **(zone_snapshot or {})},
            verified_at,
        )
        db.commit()
        db.refresh(event)
        db.refresh(zone)
        return event, zone
    except Exception:
        db.rollback()
        raise


def initialize_verified_event_for_zone(
    db: Session,
    zone: models.FloodAvoidanceZone,
    peak_severity: models.ReportSeverity | str,
    peak_depth: Optional[str],
) -> models.FloodEvent:
    """Attach a newly-created operational zone to its first Flood Event.

    This helper intentionally does not commit so callers that build a custom
    merged zone can persist the zone, event, and first supporting report in one
    transaction.
    """
    if zone.event_id is not None:
        raise ValueError("The zone is already linked to a Flood Event.")
    severity = _severity_value(peak_severity)
    verified_at = datetime.now(timezone.utc)
    event = models.FloodEvent(
        status=models.FloodEventStatus.ACTIVE,
        verified_at=verified_at,
        peak_severity=severity,
        peak_depth=peak_depth,
    )
    db.add(event)
    db.flush()
    zone.event_id = event.id
    _append_timeline(
        db, event.id, "event_verified", "Flood event verified and opened for live operations.",
        {"peak_severity": severity.value, "peak_depth": peak_depth}, verified_at,
    )
    _append_timeline(
        db, event.id, "zone_created", "Official flood zone created for this event.",
        {"zone_id": zone.id}, verified_at,
    )
    return event


def link_supporting_report(
    db: Session,
    report: models.FloodReport,
    event: models.FloodEvent,
    zone: models.FloodAvoidanceZone,
    acted_by_user_id: int,
    commit: bool = True,
) -> models.FloodReport:
    """Approve a corroborating report without creating another event."""
    if zone.event_id != event.id:
        raise ValueError("The target zone does not belong to the target flood event.")
    if report.event_id == event.id and report.status == models.ReportStatus.APPROVED:
        return report
    if report.status != models.ReportStatus.PENDING:
        raise ValueError("Only pending reports can be linked as supporting evidence.")

    try:
        acted_at = datetime.now(timezone.utc)
        report.event_id = event.id
        report.zone_id = zone.id
        report.status = models.ReportStatus.APPROVED
        report.approved_at = acted_at
        if event.first_reported_at is None or (ensure_utc(report.created_at) < ensure_utc(event.first_reported_at)):
            event.first_reported_at = ensure_utc(report.created_at)
        report_severity = _severity_value(report.severity)
        if _is_more_severe(report_severity, _severity_value(event.peak_severity)):
            event.peak_severity = report_severity
            event.peak_depth = report.depth
            _append_timeline(
                db, event.id, "severity_peak_changed",
                "Verified event peak severity increased from supporting evidence.",
                {"peak_severity": report_severity.value, "peak_depth": report.depth}, acted_at,
            )
        _record_report_location_rows(db, event, report)
        db.add(models.FloodReportModerationOutcome(
            report_id=report.id,
            outcome=models.ReportModerationOutcomeType.LINKED,
            event_id=event.id,
            zone_id=zone.id,
            acted_by_user_id=acted_by_user_id,
            acted_at=acted_at,
        ))
        _append_timeline(
            db, event.id, "report_linked", "Supporting flood report linked to this event.",
            {"report_id": report.id, "zone_id": zone.id}, acted_at,
        )
        if report.user_id:
            credit_user_verified_report(db, report.user_id, commit=False)
        if commit:
            db.commit()
            db.refresh(report)
        return report
    except Exception:
        db.rollback()
        raise


def reject_report(
    db: Session,
    report: models.FloodReport,
    rejection_reason: models.ReportRejectionReason,
    internal_note: Optional[str],
    acted_by_user_id: int,
) -> models.FloodReport:
    """Record a structured moderation rejection without archiving evidence."""
    if rejection_reason == models.ReportRejectionReason.OTHER and not (internal_note and internal_note.strip()):
        raise ValueError("An internal note is required when rejection reason is 'other'.")
    if report.status == models.ReportStatus.REJECTED:
        return report
    if report.status != models.ReportStatus.PENDING:
        raise ValueError("Only pending reports can be rejected.")
    try:
        acted_at = datetime.now(timezone.utc)
        report.status = models.ReportStatus.REJECTED
        db.add(models.FloodReportModerationOutcome(
            report_id=report.id,
            outcome=models.ReportModerationOutcomeType.REJECTED,
            rejection_reason=rejection_reason,
            internal_note=internal_note.strip() if internal_note else None,
            acted_by_user_id=acted_by_user_id,
            acted_at=acted_at,
        ))
        if report.user_id:
            penalize_user_rejected_report(db, report.user_id, commit=False)
            # The reporter receives the decision and its structured public
            # reason in the existing notification bell. Staff-only notes must
            # never be included in this payload or message.
            db.add(Notification(
                user_id=report.user_id,
                type=NotificationType.SYSTEM,
                message=(
                    "Your flood report was reviewed and was not added to the live map "
                    f"because it had {_REJECTION_NOTIFICATION_REASONS[rejection_reason]}."
                ),
                payload={
                    "report_id": report.id,
                    "action": "flood_report_rejected",
                    "rejection_reason": rejection_reason.value,
                },
            ))
        db.commit()
        db.refresh(report)
        return report
    except Exception:
        db.rollback()
        raise


def deactivate_zone_and_end_event_if_final(
    db: Session,
    zone: models.FloodAvoidanceZone,
    occurred_at: Optional[datetime] = None,
) -> models.FloodAvoidanceZone:
    """Deactivate one zone and end the event only when no live zones remain."""
    occurred_at = ensure_utc(occurred_at) or datetime.now(timezone.utc)
    if not zone.is_active:
        return zone
    try:
        zone.is_active = False
        event = zone.flood_event
        if event:
            remaining = db.query(models.FloodAvoidanceZone.id).filter(
                models.FloodAvoidanceZone.event_id == event.id,
                models.FloodAvoidanceZone.id != zone.id,
                models.FloodAvoidanceZone.is_active.is_(True),
                (models.FloodAvoidanceZone.expires_at.is_(None)) | (models.FloodAvoidanceZone.expires_at > occurred_at),
            ).first()
            if not remaining:
                event.status = models.FloodEventStatus.ENDED
                event.ended_at = occurred_at
                _append_timeline(
                    db, event.id, "event_ended", "All live flood zones for this event have ended.",
                    {"final_zone_id": zone.id}, occurred_at,
                )
        db.commit()
        db.refresh(zone)
        return zone
    except Exception:
        db.rollback()
        raise


def expire_due_zones(db: Session, now: Optional[datetime] = None) -> int:
    """End all due zones through the same lifecycle path as manual deactivation."""
    cutoff = ensure_utc(now) or datetime.now(timezone.utc)
    due_zones = db.query(models.FloodAvoidanceZone).filter(
        models.FloodAvoidanceZone.is_active.is_(True),
        models.FloodAvoidanceZone.expires_at.is_not(None),
        models.FloodAvoidanceZone.expires_at <= cutoff,
    ).all()
    for zone in due_zones:
        deactivate_zone_and_end_event_if_final(db=db, zone=zone, occurred_at=cutoff)
    return len(due_zones)
