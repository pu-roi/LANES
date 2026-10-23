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
from sqlalchemy.orm import Session, selectinload

from app import models, schemas
from app.schemas.common import ensure_utc, serialize_utc_datetime
from app.services.configuration_service import unexpired_deadline
from app.crud.report import create_flood_avoidance_zone, credit_user_verified_report, penalize_user_rejected_report
from app.services.report_notification_service import stage_report_status_notification


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
    record_event_locations(db, event, locations)


def record_event_locations(
    db: Session,
    event: models.FloodEvent,
    locations: tuple[tuple[models.FloodEventLocationType, Optional[str]], ...],
) -> None:
    """Keep verified report/news locations searchable in permanent event history."""
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
        unexpired_deadline(db, models.FloodAvoidanceZone.expires_at, as_of),
    ).count()
    approved_reports_filter = (
        models.FloodReport.event_id == event.id,
        models.FloodReport.status == models.ReportStatus.APPROVED,
        models.FloodReport.deleted_at.is_(None),
    )
    counts = {
        "evidence_count": db.query(models.FloodReport.id).filter(*approved_reports_filter).count(),
        "supporting_report_count": db.query(models.FloodReport.id).filter(
            *approved_reports_filter, models.FloodReport.zone_id.is_not(None)).count(),
        "reporter_count": int(db.query(func.count(func.distinct(models.FloodReport.user_id))).filter(
            *approved_reports_filter, models.FloodReport.user_id.is_not(None)).scalar() or 0),
        "zone_count": db.query(models.FloodAvoidanceZone.id).filter(models.FloodAvoidanceZone.event_id == event.id).count(),
        "active_zone_count": active_zone_count,
        "location_count": db.query(models.FloodEventLocation.id).filter(models.FloodEventLocation.event_id == event.id).count(),
    }
    from app.services.news_history_evidence import event_projections, project_values
    return project_values(_event_metrics(event, as_of, counts), event_projections(db, [event.id]).get(event.id))


def _event_metrics(event: models.FloodEvent, as_of: datetime, counts: dict[str, int]) -> dict[str, Any]:
    end_time = ensure_utc(event.ended_at) or as_of
    start_time = ensure_utc(event.verified_at) or as_of
    duration_seconds = max(0, int((end_time - start_time).total_seconds()))
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
        **counts,
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
    multiple_places: bool = False,
    dataset_id: Optional[str] = None,
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
    from app.services.news_source_repair import superseded_event
    query = query.filter(~superseded_event())
    from app.services.news_gma_active_outputs import active_only_event
    query = query.filter(~active_only_event())
    from app.services.news_tribune_pilot import pending_history_event
    query = query.filter(~pending_history_event())
    from app.services.historical_news_metadata import DATASET, Timeline, ENTRY, occurrence_day, metadata_field
    if dataset_id:
        import re
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,99}', dataset_id):
            raise ValueError('Unknown historical dataset')
        if dataset_id != DATASET and not db.query(Timeline.id).filter(Timeline.entry_type == ENTRY,
                Timeline.snapshot_json['schema_version'].as_string() == 'historical-import-v1',
                Timeline.snapshot_json['dataset_id'].as_string() == dataset_id).first():
            raise ValueError('Unknown historical dataset')
        query = query.filter(db.query(Timeline.id).filter(Timeline.event_id == models.FloodEvent.id,
            Timeline.entry_type == ENTRY, Timeline.snapshot_json['dataset_id'].as_string() == dataset_id).exists())
    if multiple_places:
        place_count = db.query(func.count(models.FloodEventLocation.id)).filter(
            models.FloodEventLocation.event_id == models.FloodEvent.id,
            models.FloodEventLocation.location_type != models.FloodEventLocationType.CITY,
        ).correlate(models.FloodEvent).scalar_subquery()
        query = query.filter(place_count > 1)
    if status_value:
        query = query.filter(models.FloodEvent.status == status_value)
    if severity_value:
        query = query.filter(models.FloodEvent.peak_severity == severity_value)
    if date_from:
        query = query.filter(occurrence_day() >= date_from.date())
    if date_to:
        query = query.filter(occurrence_day() <= date_to.date())

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


def flood_history_window(query: Any, *, limit: int, page: int | None,
                        page_size: int, focus_event_id: int | None) -> tuple[list[models.FloodEvent], dict[str, int] | None]:
    """Page the same bounded, ordered history set used by the overview map."""
    ordered = query.order_by(models.FloodEvent.verified_at.desc(), models.FloodEvent.id.desc())
    if page is None:
        return ordered.limit(limit).all(), None
    ids = [row.id for row in ordered.with_entities(models.FloodEvent.id, models.FloodEvent.verified_at).limit(limit).all()]
    total = len(ids)
    pages = max(1, (total + page_size - 1) // page_size)
    actual = ids.index(focus_event_id) // page_size + 1 if focus_event_id in ids else min(page, pages)
    selected = ids[(actual - 1) * page_size:actual * page_size]
    events = ordered.filter(models.FloodEvent.id.in_(selected)).all() if selected else []
    return events, {"total": total, "page": actual, "pages": pages, "page_size": page_size}


def flood_history_records(db: Session, events: list[models.FloodEvent], *, summary: bool = False) -> list[dict[str, Any]]:
    """Batch the browsing projection; evidence details remain available on inspection."""
    from app.schemas.flood_event import HistoricalFloodZoneResponse
    from app.services.flood_heatmap_service import historical_heatmap_features

    if not events:
        return []
    ids = [event.id for event in events]
    locations: dict[int, list[Any]] = defaultdict(list)
    from app.services.news_history_evidence import event_projections, project_values
    projections = event_projections(db, ids, locations=locations)
    zones: dict[int, list[Any]] = defaultdict(list)
    zone_query = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.event_id.in_(ids)).order_by(
        models.FloodAvoidanceZone.created_at.asc(), models.FloodAvoidanceZone.id.asc())
    reports = selectinload(models.FloodAvoidanceZone.reports)
    if summary:
        zone_query = zone_query.options(reports.load_only(models.FloodReport.severity, models.FloodReport.depth))
    else:
        zone_query = zone_query.options(
            reports.selectinload(models.FloodReport.user).selectinload(models.User.profile),
            reports.selectinload(models.FloodReport.user).selectinload(models.User.role),
            reports.selectinload(models.FloodReport.survey))
    for zone in zone_query:
        zones[zone.event_id].append(zone)
    report_counts = {row[0]: row[1:] for row in db.query(models.FloodReport.event_id,
        func.count(models.FloodReport.id),
        func.count(models.FloodReport.id).filter(models.FloodReport.zone_id.is_not(None)),
        func.count(func.distinct(models.FloodReport.user_id))).filter(
            models.FloodReport.event_id.in_(ids), models.FloodReport.status == models.ReportStatus.APPROVED,
            models.FloodReport.deleted_at.is_(None)).group_by(models.FloodReport.event_id)}
    as_of = datetime.now(timezone.utc)
    active_counts = dict(db.query(models.FloodAvoidanceZone.event_id, func.count(models.FloodAvoidanceZone.id)).filter(
        models.FloodAvoidanceZone.event_id.in_(ids), models.FloodAvoidanceZone.is_active.is_(True),
        unexpired_deadline(db, models.FloodAvoidanceZone.expires_at, as_of)).group_by(models.FloodAvoidanceZone.event_id).all())
    records = []
    for event in events:
        evidence, supporting, reporters = report_counts.get(event.id, (0, 0, 0))
        event_zones = zones[event.id]
        serialized_zones = []
        for zone in event_zones:
            # ORM evidence/contributor properties can query news/users once per zone.
            # Browsing needs saved footprints and severity only, never those properties.
            value = {key: getattr(zone, key) for key in (
                "id", "event_id", "geometry", "is_active", "created_at", "updated_at", "severity", "depth"
            )} if summary else zone
            serialized_zones.append(HistoricalFloodZoneResponse.model_validate(value).model_dump(
                mode="json", exclude_unset=summary))
        records.append({
            **schemas.FloodEventResponse.model_validate(event).model_dump(mode="json"),
            **_event_metrics(event, as_of, {"evidence_count": evidence, "supporting_report_count": supporting,
                "reporter_count": reporters, "zone_count": len(event_zones), "active_zone_count": active_counts.get(event.id, 0),
                "location_count": len(locations[event.id])}),
            "locations": [schemas.FloodEventLocationResponse.model_validate(row).model_dump(mode="json")
                for row in locations[event.id]],
            "heatmap_features": [feature.model_dump(mode="json") for feature in historical_heatmap_features(
                event.id, event.peak_severity, event_zones)],
            "zones": serialized_zones,
        })
    return [project_values(row, projections.get(row["id"])) for row in records]


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


def _event_locations(db: Session, event_ids: list[int]) -> dict[int, list[Any]]:
    if not event_ids:
        return {}
    locations_by_event: dict[int, list[Any]] = defaultdict(list)
    locations = (
        db.query(models.FloodEventLocation.event_id, models.FloodEventLocation.location_type,
            models.FloodEventLocation.display_name, models.FloodEventLocation.normalized_name)
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
    from app.services.historical_news_metadata import event_metadata
    historical = event_metadata(db, [e.id for e in events])
    demo_count = sum(m.is_demo for m in historical.values())
    events = [e for e in events if e.id not in historical or not historical[e.id].is_demo]
    event_ids = [event.id for event in events]
    report_counts = _event_report_counts(db, event_ids)
    locations_by_event = _event_locations(db, event_ids)
    severity_counts = Counter(event.peak_severity.value for event in events)
    from app.services.news_history_evidence import event_projections
    projections = event_projections(db, event_ids)
    daily_counts = Counter(projections[event.id]["occurrence_date"] or "Unknown" if projections[event.id]["news_timing"] else event.verified_at.date().isoformat() for event in events)
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
        if not projections[event.id]["news_timing"] and event.status == models.FloodEventStatus.ENDED and event.ended_at:
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
        day = func.date(func.coalesce(models.FloodReport.approved_at, models.FloodReport.created_at))
        approved_reports = (
            db.query(day, func.count(models.FloodReport.id))
            .filter(
                models.FloodReport.event_id.in_(event_ids),
                models.FloodReport.status == models.ReportStatus.APPROVED,
                models.FloodReport.deleted_at.is_(None),
            )
            .group_by(day).all()
        )
        for report_day, count in approved_reports:
            report_day_counts[str(report_day)] += count
    ended_count = sum(event.status == models.FloodEventStatus.ENDED for event in events)
    return {
        "demonstration_instances": demo_count,
        "historical_intervals": {
            "assumed_two_hour_events": sum(m.closure_basis == 'assumed_two_hours' for m in historical.values() if not m.is_demo),
            "unknown_endpoints": sum(e.ended_at is None for e in events if e.id in historical),
        },
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
            "official_duration": "Time from operational verification until the final active zone ended. News administrative intervals, imported assumptions and active events are excluded.",
            "historical_occurrence": "News-origin events use supported source occurrence dates; unknown source dates remain unknown. Demonstration instances do not add real flood occurrences.",
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
    from app.services.historical_news_metadata import event_metadata
    historical = event_metadata(db, event_ids)
    from app.services.news_history_evidence import event_projections
    projections = event_projections(db, event_ids)
    rows: list[dict[str, Any]] = []
    for event in events:
        locations = locations_by_event.get(event.id, [])
        rows.append({
            "event_id": event.id,
            "historical": historical[event.id].model_dump(mode="json") if event.id in historical else None,
            "origin": projections[event.id]["origin"],
            "news_article_count": projections[event.id]["news_article_count"],
            "occurrence_date": projections[event.id]["occurrence_date"] if projections[event.id]["news_timing"] else event.verified_at.date().isoformat(),
            "observation_precision": projections[event.id]["observation_precision"],
            "closure_basis": projections[event.id]["closure_basis"],
            "status": event.status.value,
            "first_reported_at": event.first_reported_at,
            "verified_at": event.verified_at,
            "ended_at": event.ended_at,
            "peak_verified_severity": event.peak_severity.value,
            "peak_depth_label": event.peak_depth,
            "official_duration_minutes": (
                max(0, int((event.ended_at - event.verified_at).total_seconds() // 60))
                if not projections[event.id]["news_timing"] and event.status == models.FloodEventStatus.ENDED and event.ended_at else None
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
    acted_by_user_id: Optional[int] = None,
    source_report: Optional[models.FloodReport] = None,
    zone_snapshot: Optional[dict[str, Any]] = None,
    zone_attributes: Optional[dict[str, Any]] = None,
    commit: bool = True,
    first_reported_at: Optional[datetime] = None,
    credit_reputation: bool = True,
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
    onset_at = ensure_utc(first_reported_at) or (ensure_utc(source_report.created_at) if source_report else None)
    try:
        event = models.FloodEvent(
            status=models.FloodEventStatus.ACTIVE,
            first_reported_at=onset_at,
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
            if acted_by_user_id is not None:
                db.add(models.FloodReportModerationOutcome(
                    report_id=source_report.id,
                    outcome=models.ReportModerationOutcomeType.APPROVED,
                    event_id=event.id,
                    zone_id=zone.id,
                    acted_by_user_id=acted_by_user_id,
                    acted_at=verified_at,
                ))
            if source_report.user_id and credit_reputation:
                credit_user_verified_report(db, source_report.user_id, commit=False)
            stage_report_status_notification(db, source_report)

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
        if commit:
            db.commit()
            db.refresh(event)
            db.refresh(zone)
        else:
            db.flush()
        return event, zone
    except Exception:
        if commit:
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
    acted_by_user_id: Optional[int],
    commit: bool = True,
    credit_reputation: bool = True,
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
        if report.user_id and credit_reputation:
            credit_user_verified_report(db, report.user_id, commit=False)
        stage_report_status_notification(db, report)
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
            stage_report_status_notification(
                db, report,
                message=(
                    "Your flood report was reviewed and was not added to the live map "
                    f"because it had {_REJECTION_NOTIFICATION_REASONS[rejection_reason]}."
                ),
                extra_payload={
                    "rejection_reason": rejection_reason.value,
                },
            )
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
    commit: bool = True,
) -> models.FloodAvoidanceZone:
    """Deactivate one zone and end the event only when no live zones remain."""
    occurred_at = ensure_utc(occurred_at) or datetime.now(timezone.utc)
    if not zone.is_active:
        return zone
    try:
        zone.is_active = False
        if zone.event_id:
            from app.services.historical_news_metadata import record_demo_deactivation
            record_demo_deactivation(db, zone.event_id, zone.id, occurred_at)
        event = zone.flood_event
        if event:
            remaining = db.query(models.FloodAvoidanceZone.id).filter(
                models.FloodAvoidanceZone.event_id == event.id,
                models.FloodAvoidanceZone.id != zone.id,
                models.FloodAvoidanceZone.is_active.is_(True),
                unexpired_deadline(db, models.FloodAvoidanceZone.expires_at, occurred_at),
            ).first()
            if not remaining:
                event.status = models.FloodEventStatus.ENDED
                event.ended_at = occurred_at
                _append_timeline(
                    db, event.id, "event_ended", "All live flood zones for this event have ended.",
                    {"final_zone_id": zone.id}, occurred_at,
                )
        if commit:
            db.commit()
            db.refresh(zone)
        else:
            db.flush()
        return zone
    except Exception:
        if commit:
            db.rollback()
        raise


def expire_due_zones(db: Session, now: Optional[datetime] = None) -> int:
    """End all due zones through the same lifecycle path as manual deactivation."""
    cutoff = ensure_utc(now) or datetime.now(timezone.utc)
    from app.services.configuration_service import configuration_lock, read_configuration
    configuration_lock(db)
    if not read_configuration(db).automatic_expiry_enabled:
        return 0
    from app.services.pasig_ml_expiry_service import synchronize_active_zones
    synchronize_active_zones(db, now=cutoff)
    db.commit()
    configuration_lock(db)
    from app.services.local_news_scenario_service import sql_clock
    eligibility_clock = sql_clock(models.FloodAvoidanceZone.id, "zone", cutoff)
    due_zones = db.query(models.FloodAvoidanceZone).filter(
        models.FloodAvoidanceZone.is_active.is_(True),
        models.FloodAvoidanceZone.expires_at.is_not(None),
        models.FloodAvoidanceZone.expires_at <= eligibility_clock,
    ).all()
    expired_count = 0
    for zone in due_zones:
        # Each lifecycle commit releases the policy lock. Reacquire it before
        # the next zone so a saved pause cannot be bypassed by a queued batch.
        configuration_lock(db)
        if not read_configuration(db).automatic_expiry_enabled:
            break
        if zone.event_id:
            _append_timeline(db, zone.event_id, "evidence_expired",
                "Evidence deadline passed; current condition is Unconfirmed, not observed cleared.",
                {"zone_id": zone.id, "expires_at": zone.expires_at.isoformat(), "condition": "Unconfirmed"}, cutoff)
        deactivate_zone_and_end_event_if_final(db=db, zone=zone, occurred_at=cutoff)
        expired_count += 1
    return expired_count
