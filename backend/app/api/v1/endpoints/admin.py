import csv
import io
import json
import logging
from typing import List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app import crud, models, schemas
from app.api import deps
from app.core.database import get_db
from app.models.post import CommunityPost, CommunityPostReport
from app.models.notification import Notification, NotificationType
from app.services.flood_event_service import (
    build_flood_event_history_query,
    create_verified_event_with_zone,
    deactivate_zone_and_end_event_if_final,
    get_flood_event_planning_analytics,
    get_event_metrics,
    initialize_verified_event_for_zone,
    link_supporting_report,
    record_zone_update,
    reject_report as reject_report_with_outcome,
    serialize_flood_event_planning_records,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/moderation/flood-reports")
def get_flood_report_moderation_cases(
    status_filter: str = "all",
    source: Optional[str] = None,
    location: Optional[str] = None,
    reporter: Optional[str] = None,
    rejection_reason: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> list[dict]:
    """List internal flood-report moderation cases without duplicating map actions."""
    allowed_statuses = {"all", *(status.value for status in models.ReportStatus)}
    if status_filter not in allowed_statuses:
        raise HTTPException(status_code=422, detail="Invalid flood report moderation status")
    allowed_reasons = {reason.value for reason in models.ReportRejectionReason}
    if rejection_reason and rejection_reason not in allowed_reasons:
        raise HTTPException(status_code=422, detail="Invalid rejection reason")
    if limit < 1 or limit > 250:
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 250")

    query = db.query(models.FloodReport).filter(models.FloodReport.deleted_at.is_(None))
    if status_filter != "all":
        query = query.filter(models.FloodReport.status == status_filter)
    if source:
        try:
            query = query.filter(models.FloodReport.source == models.ReportSource(source))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid report source") from exc
    if date_from:
        query = query.filter(models.FloodReport.created_at >= date_from)
    if date_to:
        query = query.filter(models.FloodReport.created_at <= date_to)
    if location:
        pattern = f"%{location.strip()}%"
        query = query.filter(or_(
            models.FloodReport.human_readable_location.ilike(pattern),
            models.FloodReport.barangay.ilike(pattern),
            models.FloodReport.city.ilike(pattern),
        ))
    if reporter:
        query = query.join(models.User, models.FloodReport.user_id == models.User.id).filter(
            models.User.username.ilike(f"%{reporter.strip()}%")
        )
    if rejection_reason:
        query = query.filter(models.FloodReport.moderation_outcomes.any(
            models.FloodReportModerationOutcome.rejection_reason == rejection_reason
        ))

    reports = query.order_by(models.FloodReport.created_at.desc()).limit(limit).all()
    cases: list[dict] = []
    for report in reports:
        outcome = (
            db.query(models.FloodReportModerationOutcome)
            .filter(models.FloodReportModerationOutcome.report_id == report.id)
            .order_by(models.FloodReportModerationOutcome.acted_at.desc(), models.FloodReportModerationOutcome.id.desc())
            .first()
        )
        acting_admin = db.get(models.User, outcome.acted_by_user_id) if outcome and outcome.acted_by_user_id else None
        reporter_user = db.get(models.User, report.user_id) if report.user_id else None
        longitude = latitude = None
        if report.geometry is not None:
            longitude, latitude = db.query(
                func.ST_X(func.ST_Centroid(report.geometry)),
                func.ST_Y(func.ST_Centroid(report.geometry)),
            ).one()
        cases.append({
            "report_id": report.id,
            "status": report.status.value,
            "source": report.source.value,
            "raw_text": report.raw_text,
            "severity": report.severity.value,
            "depth": report.depth,
            "submitted_at": report.created_at,
            "location": ", ".join(part for part in [report.human_readable_location, report.barangay, report.city] if part) or None,
            "reporter": reporter_user.username if reporter_user else "System",
            "event_id": report.event_id,
            "zone_id": report.zone_id,
            "resolution": outcome.outcome.value if outcome else None,
            "rejection_reason": outcome.rejection_reason.value if outcome and outcome.rejection_reason else None,
            "internal_note": outcome.internal_note if outcome else None,
            "resolved_at": outcome.acted_at if outcome else None,
            "acting_admin": acting_admin.username if acting_admin else None,
            "latitude": latitude,
            "longitude": longitude,
        })
    return cases

@router.get("/moderation/reports")
def get_community_post_reports(
    status_filter: str = "open",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> list[dict]:
    if status_filter not in {"open", "resolved"}:
        raise HTTPException(status_code=422, detail="Invalid report status")

    reports = (
        db.query(CommunityPostReport)
        .filter(CommunityPostReport.status == status_filter)
        .order_by(CommunityPostReport.created_at.asc())
        .all()
    )
    result: list[dict] = []
    seen_post_ids: set[int] = set()
    for report in reports:
        if report.post_id in seen_post_ids:
            continue
        seen_post_ids.add(report.post_id)
        post = db.query(CommunityPost).filter(CommunityPost.id == report.post_id).first()
        if post:
            open_report_count = (
                db.query(CommunityPostReport)
                .filter(
                    CommunityPostReport.post_id == post.id,
                    CommunityPostReport.status == "open",
                )
                .count()
            )
            result.append(
                {
                    "id": report.id,
                    "post_id": post.id,
                    "post_content": post.content,
                    "post_author_id": post.user_id,
                    "reason": report.reason,
                    "details": report.details,
                    "created_at": report.created_at,
                    "open_report_count": open_report_count,
                }
            )
    return result

@router.post("/moderation/posts/{post_id}/resolve")
async def resolve_community_post_reports(
    post_id: int,
    payload: schemas.CommunityPostModerationResolution,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> dict:
    if payload.action not in {"dismiss", "warn", "hide"}:
        raise HTTPException(status_code=422, detail="Invalid moderation action")
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    reports = db.query(CommunityPostReport).filter(CommunityPostReport.post_id == post_id, CommunityPostReport.status == "open").all()
    if not reports:
        raise HTTPException(status_code=404, detail="No open reports for this post")
    now = datetime.utcnow()
    if payload.action == "hide":
        post.hidden_at, post.hidden_by_user_id = now, current_user.id
    for report in reports:
        report.status = "resolved"
        report.resolution_action = payload.action
        report.resolved_by_user_id, report.resolved_at = current_user.id, now
        db.add(
            Notification(
                user_id=report.reporter_user_id,
                type=NotificationType.SYSTEM,
                message="Your post report was reviewed.",
                payload={"post_id": post_id, "action": payload.action},
            )
        )
    if payload.action in {"warn", "hide"}:
        reason_label_map = {
            "spam_scam": "Spam or scam",
            "misinformation": "Misinformation / False Hazard",
            "harassment_hate": "Harassment or hate speech",
            "explicit_violent": "Explicit or violent content",
            "other": "Community guidelines violation",
        }
        reasons_list = [reason_label_map.get(r.reason, r.reason) for r in reports if r.reason]
        unique_reasons = list(dict.fromkeys(reasons_list))
        reasons_str = f" Reason: {', '.join(unique_reasons)}." if unique_reasons else ""

        message = (
            f"A moderator warned you about a Community Feed post.{reasons_str}"
            if payload.action == "warn"
            else f"A moderator hid one of your Community Feed posts from public view.{reasons_str}"
        )
        db.add(
            Notification(
                user_id=post.user_id,
                type=NotificationType.SYSTEM,
                message=message,
                payload={"post_id": post_id, "action": payload.action, "reasons": unique_reasons},
            )
        )
    db.commit()

    if payload.action == "hide":
        from app.core.sse import manager
        await manager.broadcast({
            "event": "feed_post_deleted",
            "data": {"post_id": post_id}
        })

    return {"message": "Reports resolved", "action": payload.action, "resolved_count": len(reports)}


def _attach_report_media(zone: models.FloodAvoidanceZone) -> schemas.FloodAvoidanceZoneResponse:
    """Expose source-report evidence and zone media without copying."""
    response = schemas.FloodAvoidanceZoneResponse.model_validate(zone)
    report_media: list[str] = []
    if zone.reports:
        for r in zone.reports:
            if r.media_urls:
                for url in r.media_urls:
                    if url and url not in report_media:
                        report_media.append(url)

    return response.model_copy(
        update={
            "report_media_urls": report_media,
            "media_urls": list(zone.media_urls or []),
        }
    )


@router.get("/reports/pending", response_model=List[schemas.FloodReportResponse])
def get_pending_reports(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all pending flood reports for moderation.
    Requires admin privileges.
    """
    return crud.get_pending_flood_reports(db=db, skip=skip, limit=limit)


@router.get("/reports/detail/{report_id}", response_model=schemas.FloodReportResponse)
def get_report_for_spatial_review(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> models.FloodReport:
    """Return one non-deleted report for an admin's focused spatial review."""
    report = crud.get_flood_report(db=db, report_id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/flood-events/{event_id}/summary")
def get_flood_event_summary(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> dict[str, Any]:
    """Return admin-only server-calculated lifecycle metrics for one Flood Event."""
    event = db.get(models.FloodEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Flood Event not found")
    return get_event_metrics(db=db, event=event)


@router.get("/flood-events", response_model=List[schemas.FloodEventResponse])
def list_flood_events(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> list[models.FloodEvent]:
    return db.query(models.FloodEvent).order_by(models.FloodEvent.verified_at.desc()).all()


@router.get("/flood-events/history")
def list_flood_event_history(
    status_filter: str = "all",
    severity: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    barangay: Optional[str] = None,
    road: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> list[dict[str, Any]]:
    """Return filtered, admin-only historical records with isolated event map data."""
    if limit < 1 or limit > 250:
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 250")
    try:
        query = build_flood_event_history_query(
            db,
            status_filter=status_filter,
            severity=severity,
            date_from=date_from,
            date_to=date_to,
            barangay=barangay,
            road=road,
            search=search,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    events = query.order_by(models.FloodEvent.verified_at.desc()).limit(limit).all()
    records: list[dict[str, Any]] = []
    for event in events:
        locations = db.query(models.FloodEventLocation).filter(
            models.FloodEventLocation.event_id == event.id
        ).order_by(models.FloodEventLocation.location_type, models.FloodEventLocation.display_name).all()
        zones = db.query(models.FloodAvoidanceZone).filter(
            models.FloodAvoidanceZone.event_id == event.id
        ).order_by(models.FloodAvoidanceZone.created_at.asc()).all()
        records.append({
            **schemas.FloodEventResponse.model_validate(event).model_dump(mode="json"),
            **get_event_metrics(db=db, event=event),
            "locations": [
                schemas.FloodEventLocationResponse.model_validate(location).model_dump(mode="json")
                for location in locations
            ],
            # These are event-owned historic copies, never the live routing source.
            "zones": [
                schemas.FloodAvoidanceZoneResponse.model_validate(zone).model_dump(mode="json")
                for zone in zones
            ],
        })
    return records


@router.get("/flood-events/analytics")
def get_flood_event_analytics(
    status_filter: str = "all",
    severity: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    barangay: Optional[str] = None,
    road: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> dict[str, Any]:
    """Return filtered city-planning analytics where one Flood Event counts once."""
    try:
        events = build_flood_event_history_query(
            db,
            status_filter=status_filter,
            severity=severity,
            date_from=date_from,
            date_to=date_to,
            barangay=barangay,
            road=road,
            search=search,
        ).order_by(models.FloodEvent.verified_at.asc()).all()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return get_flood_event_planning_analytics(db, events)


@router.get("/flood-events/export")
def export_flood_event_planning_data(
    export_type: str = "records",
    export_format: str = "csv",
    status_filter: str = "all",
    severity: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    barangay: Optional[str] = None,
    road: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Response:
    """Export safe planning data only; raw reports and reporter identity stay internal."""
    if export_type not in {"records", "analytics"}:
        raise HTTPException(status_code=422, detail="Export type must be records or analytics")
    if export_format not in {"csv", "json"}:
        raise HTTPException(status_code=422, detail="Export format must be csv or json")
    try:
        events = build_flood_event_history_query(
            db,
            status_filter=status_filter,
            severity=severity,
            date_from=date_from,
            date_to=date_to,
            barangay=barangay,
            road=road,
            search=search,
        ).order_by(models.FloodEvent.verified_at.desc()).all()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    payload: Any = (
        serialize_flood_event_planning_records(db, events)
        if export_type == "records"
        else get_flood_event_planning_analytics(db, events)
    )
    filename = f"lanes_flood_event_{export_type}.{export_format}"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    if export_format == "json":
        return Response(
            content=json.dumps(payload, default=str, indent=2),
            media_type="application/json",
            headers=headers,
        )

    output = io.StringIO()

    def safe_csv_cell(value: Any) -> Any:
        """Prevent spreadsheet applications from interpreting exported text as a formula."""
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return f"'{value}"
        return value

    if export_type == "records":
        rows: list[dict[str, Any]] = payload
        fieldnames = list(rows[0].keys()) if rows else [
            "event_id", "status", "first_reported_at", "verified_at", "ended_at",
            "peak_verified_severity", "peak_depth_label", "official_duration_minutes",
            "approved_supporting_report_count", "barangays", "roads", "cities",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([
            {fieldname: safe_csv_cell(row.get(fieldname)) for fieldname in fieldnames}
            for row in rows
        ])
    else:
        # CSV analytics is intentionally a compact metric/value table, while
        # JSON retains the full time-series and distribution structure.
        writer = csv.writer(output)
        writer.writerow(["metric", "value"])
        for metric in ("total_events", "ended_events", "active_events"):
            writer.writerow([safe_csv_cell(metric), safe_csv_cell(payload[metric])])
        writer.writerow(["approved_supporting_report_count", safe_csv_cell(payload["supporting_report_volume"]["approved_report_count"])])
        writer.writerow(["average_reports_per_event", safe_csv_cell(payload["supporting_report_volume"]["average_per_event"])])
        writer.writerow(["average_official_duration_minutes", safe_csv_cell(payload["duration"]["average_minutes"])])
        for entry in payload["peak_severity_distribution"]:
            writer.writerow([f"peak_severity_{safe_csv_cell(entry['severity'])}", safe_csv_cell(entry["event_count"])])
        for entry in payload["duration"]["distribution"]:
            writer.writerow([f"duration_{safe_csv_cell(entry['bucket'])}", safe_csv_cell(entry["event_count"])])
        for entry in payload["events_over_time"]:
            writer.writerow([f"events_verified_{safe_csv_cell(entry['date'])}", safe_csv_cell(entry["event_count"])])
        for entry in payload["recurring_barangays"]:
            writer.writerow([f"recurring_barangay_{safe_csv_cell(entry['name'])}", safe_csv_cell(entry["event_count"])])
        for entry in payload["frequently_affected_roads"]:
            writer.writerow([f"frequently_affected_road_{safe_csv_cell(entry['name'])}", safe_csv_cell(entry["event_count"])])
    return Response(content=output.getvalue(), media_type="text/csv", headers=headers)


@router.get("/flood-events/{event_id}/history-detail")
def get_flood_event_history_detail(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> dict[str, Any]:
    """Return the staff-only event detail, evidence, and readable lifecycle timeline."""
    event = db.get(models.FloodEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Flood Event not found")

    locations = db.query(models.FloodEventLocation).filter(
        models.FloodEventLocation.event_id == event.id
    ).order_by(models.FloodEventLocation.location_type, models.FloodEventLocation.display_name).all()
    zones = db.query(models.FloodAvoidanceZone).filter(
        models.FloodAvoidanceZone.event_id == event.id
    ).order_by(models.FloodAvoidanceZone.created_at.asc()).all()
    reports = db.query(models.FloodReport).filter(
        models.FloodReport.event_id == event.id,
        models.FloodReport.deleted_at.is_(None),
    ).order_by(models.FloodReport.created_at.asc()).all()
    timeline = db.query(models.FloodEventTimelineEntry).filter(
        models.FloodEventTimelineEntry.event_id == event.id
    ).order_by(models.FloodEventTimelineEntry.occurred_at.asc()).all()

    return {
        **schemas.FloodEventResponse.model_validate(event).model_dump(mode="json"),
        **get_event_metrics(db=db, event=event),
        "locations": [schemas.FloodEventLocationResponse.model_validate(location).model_dump(mode="json") for location in locations],
        "zones": [schemas.FloodAvoidanceZoneResponse.model_validate(zone).model_dump(mode="json") for zone in zones],
        "reports": [schemas.FloodReportResponse.model_validate(report).model_dump(mode="json") for report in reports],
        "timeline": [schemas.FloodEventTimelineEntryResponse.model_validate(entry).model_dump(mode="json") for entry in timeline],
    }


@router.post("/reports/{report_id}/approve", response_model=schemas.FloodReportResponse)
async def approve_report(
    report_id: int,
    request: Request,
    body: Optional[schemas.ApproveReportRequest] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Approve a flood report.
    Supports either creating a new FloodAvoidanceZone (with auto-generated or custom geometry)
    or merging into an existing active zone.
    Awards Trust Score credit to the reporter.
    Requires admin privileges.
    """
    report = crud.get_flood_report(db, report_id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    # A completed report carries its immutable event/zone association. Returning
    # it makes client retries safe without creating a second Flood Event.
    if report.status == models.ReportStatus.APPROVED and report.event_id and report.zone_id:
        return report
    if report.status != models.ReportStatus.PENDING:
        raise HTTPException(status_code=409, detail="Only pending reports can be approved.")

    # 2. Reverse Geocoding via Photon if barangay is missing
    if not report.barangay and report.geometry is not None:
        try:
            pt_json = db.query(func.ST_AsGeoJSON(func.ST_StartPoint(report.geometry) if func.ST_GeometryType(report.geometry) == 'ST_LineString' else report.geometry)).scalar()
            if pt_json:
                import json
                pt_data = json.loads(pt_json)
                lon, lat = pt_data["coordinates"][0], pt_data["coordinates"][1]
                import httpx
                async with httpx.AsyncClient(timeout=3.0) as client:
                    res = await client.get(f"https://photon.komoot.io/reverse?lat={lat}&lon={lon}")
                    if res.status_code == 200:
                        features = res.json().get("features", [])
                        if features:
                            props = features[0].get("properties", {})
                            barangay = props.get("district") or props.get("locality") or props.get("city")
                            if barangay:
                                report.barangay = barangay
                                db.flush()
        except Exception as e:
            print(f"Photon reverse geocode failed: {e}")

    # 3. Spatial Moderation Action (CREATE_NEW vs MERGE)
    action = body.action if body else "CREATE_NEW"
    target_zone = None

    if action not in {"CREATE_NEW", "MERGE"}:
        raise HTTPException(status_code=422, detail="Unsupported report approval action.")

    if action == "MERGE" and body and body.target_zone_id:
        # Merge report into existing active zone
        target_zone = db.query(models.FloodAvoidanceZone).filter(
            models.FloodAvoidanceZone.id == body.target_zone_id
        ).first()
        if not target_zone:
            raise HTTPException(status_code=404, detail="Target avoidance zone not found")
        if not target_zone.is_active or target_zone.event_id is None:
            raise HTTPException(
                status_code=409,
                detail="Select an active event-enabled zone, or create a new verified event.",
            )
        if body.custom_geometry:
            geojson_str = body.custom_geometry.model_dump_json()
            target_zone.geometry = func.ST_SetSRID(func.ST_GeomFromGeoJSON(geojson_str), 4326)
            target_zone.curated_by_admin_id = current_user.id
        if body.severity:
            target_zone.severity_override = body.severity
        if body.depth:
            target_zone.depth_override = body.depth
        if body.admin_notes:
            target_zone.admin_notes = body.admin_notes
        try:
            zone_changes = {
                key: value
                for key, value in body.model_dump(exclude_none=True, mode="json").items()
                if key in {"custom_geometry", "severity", "depth", "admin_notes"}
            }
            if zone_changes:
                record_zone_update(db=db, zone=target_zone, changes=zone_changes, commit=False)
            link_supporting_report(
                db=db,
                report=report,
                event=target_zone.flood_event,
                zone=target_zone,
                acted_by_user_id=current_user.id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
    else:
        # Action is CREATE_NEW
        if body and body.custom_geometry:
            # Use admin hand-drawn or adjusted polygon
            zone_in = schemas.FloodAvoidanceZoneCreate(
                report_id=report.id,
                geometry=body.custom_geometry,
                curated_by_admin_id=current_user.id,
                is_active=True
            )
            _, target_zone = create_verified_event_with_zone(
                db=db,
                zone_input=zone_in,
                peak_severity=body.severity if body and body.severity else report.severity,
                peak_depth=body.depth if body and body.depth else report.depth,
                acted_by_user_id=current_user.id,
                source_report=report,
                zone_attributes={
                    "severity_override": body.severity if body else None,
                    "depth_override": body.depth if body else None,
                    "admin_notes": body.admin_notes if body else None,
                },
            )
        elif report.geometry is not None:
            # Auto-calculate buffer polygon via PostGIS
            geom_type = db.query(func.ST_GeometryType(report.geometry)).scalar()
            is_linestring = geom_type == "ST_LineString"
            is_collection = geom_type in ["ST_GeometryCollection", "ST_MultiLineString"]

            # For bidirectional reports stored as a GeometryCollection (original + opposite line),
            # we collect both lines and buffer together so the resulting polygon accurately wraps
            # both carriageways instead of just inflating one line.
            if is_collection:
                # Use a tighter per-line buffer since both roads are already included in the collection
                buffer_radius = body.buffer_radius if (body and body.buffer_radius) else 0.00015
                buffered_geojson_str = db.query(
                    func.ST_AsGeoJSON(
                        func.ST_ConvexHull(
                            func.ST_Collect(
                                func.ST_Buffer(
                                    func.ST_GeometryN(report.geometry, 1),  # Original line
                                    buffer_radius
                                ),
                                func.ST_Buffer(
                                    func.ST_GeometryN(report.geometry, 2),  # Opposite line
                                    buffer_radius
                                )
                            )
                        )
                    )
                ).scalar()
            else:
                # Fallback: single LineString or Point — use original logic
                default_buffer = 0.00015 if is_linestring else 0.0005
                buffer_radius = body.buffer_radius if (body and body.buffer_radius) else default_buffer
                buffered_geojson_str = db.query(
                    func.ST_AsGeoJSON(func.ST_Buffer(report.geometry, buffer_radius))
                ).scalar()

            if buffered_geojson_str:
                import json
                polygon_data = json.loads(buffered_geojson_str)
                polygon = schemas.PolygonGeometry(
                    type="Polygon",
                    coordinates=polygon_data["coordinates"]
                )
                zone_in = schemas.FloodAvoidanceZoneCreate(
                    report_id=report.id,
                    geometry=polygon,
                    is_active=True
                )
                _, target_zone = create_verified_event_with_zone(
                    db=db,
                    zone_input=zone_in,
                    peak_severity=body.severity if body and body.severity else report.severity,
                    peak_depth=body.depth if body and body.depth else report.depth,
                    acted_by_user_id=current_user.id,
                    source_report=report,
                    zone_attributes={
                        "severity_override": body.severity if body else None,
                        "depth_override": body.depth if body else None,
                        "admin_notes": body.admin_notes if body else None,
                    },
                )

    if not target_zone:
        raise HTTPException(status_code=422, detail="A valid geometry is required to create an official flood zone.")

    # 5. Audit Trail Logging
    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="APPROVE_REPORT",
            target_table="flood_reports",
            target_id=report.id,
            metadata_json={
                "report_id": report.id,
                "action": action,
                "zone_id": report.zone_id,
                "severity": str(report.severity)
            },
            ip_address=client_ip
        )
    )

    # 6. Broadcast real-time signal via SSE
    from app.core.sse import manager
    await manager.broadcast({
        "event": "report_approved",
        "data": {
            "report_id": report.id,
            "zone_id": report.zone_id,
            "action": action
        }
    })

    return report


@router.get("/reports/merge-candidates", response_model=schemas.MergeCandidatesListResponse)
def get_merge_candidates(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Intelligent Merge Candidate Engine (Decision #16 & OSM Graph Grouping).
    Computes explainable match scores (0-100), detects conflicts in severity/depth/passability,
    and returns a synthesized linear-referenced geometry proposal.
    Requires admin privileges.
    """
    from app.services.merge_service import find_merge_candidates
    try:
        return find_merge_candidates(report_id=report_id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to identify merge candidates: {e}")


@router.post("/reports/merge", response_model=schemas.MergeReportsResponse)
async def merge_reports(
    payload: schemas.MergeReportsRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Atomic Multi-Report Merge & Official Zone Declaration.
    - Merges primary_report and merged_report_ids into a new or existing FloodAvoidanceZone.
    - Saves overridden passable vehicles, hazards, severity, depth, notes, and merge rationale.
    - Buffers geometry into active avoidance polygon (using dual-carriageway hull if bidirectional).
    - Credits +5 Trust Score to each unique reporter.
    - Preserves all original crowdsourced reports and leaves CommunityFeed posts 100% immutable.
    - Broadcasts real-time SSE notification and records audit trail.
    Requires admin privileges.
    """
    all_report_ids = list(dict.fromkeys([payload.primary_report_id] + payload.merged_report_ids))
    matched_reports = db.query(models.FloodReport).filter(
        models.FloodReport.id.in_(all_report_ids),
        models.FloodReport.deleted_at.is_(None),
    ).all()

    if len(matched_reports) != len(all_report_ids):
        raise HTTPException(status_code=409, detail="All selected reports must still be available for merge.")

    completed_zone_ids = {report.zone_id for report in matched_reports if report.status == models.ReportStatus.APPROVED and report.event_id and report.zone_id}
    if len(completed_zone_ids) == 1 and len(completed_zone_ids) == len({report.zone_id for report in matched_reports}):
        completed_zone_id = completed_zone_ids.pop()
        if payload.target_zone_id is None or payload.target_zone_id == completed_zone_id:
            completed_zone = db.get(models.FloodAvoidanceZone, completed_zone_id)
            if completed_zone:
                return schemas.MergeReportsResponse(
                    message="Selected reports are already linked to this verified Flood Event.",
                    zone_id=completed_zone.id,
                    zone_name=completed_zone.name,
                    merged_count=len(matched_reports),
                    awarded_user_ids=[],
                )

    if any(report.status != models.ReportStatus.PENDING for report in matched_reports):
        raise HTTPException(status_code=409, detail="All selected reports must still be pending and available for merge.")
    reports = matched_reports

    final = payload.final_data
    target_zone = None
    created_new_zone = False

    # 1. Resolve Target Avoidance Zone (Existing vs New)
    if payload.target_zone_id:
        target_zone = db.query(models.FloodAvoidanceZone).filter(
            models.FloodAvoidanceZone.id == payload.target_zone_id
        ).first()
        if not target_zone:
            raise HTTPException(status_code=404, detail=f"Target avoidance zone #{payload.target_zone_id} not found")
        if not target_zone.is_active or target_zone.event_id is None:
            raise HTTPException(status_code=409, detail="Select an active event-enabled zone, or create a new verified event.")
    else:
        # Create a new FloodAvoidanceZone
        created_new_zone = True

    # 2. Process and Buffer the Final Zone Geometry
    # Final geometry can be Hand-Drawn Polygon (TerraDraw) or Routed Line/MultiLine
    geom_dict = final.geometry.model_dump()
    geom_type = geom_dict.get("type")
    
    if geom_type in ["Polygon", "MultiPolygon"]:
        # Hand-drawn boundary polygon
        geojson_str = json.dumps(geom_dict)
        final_poly_geom = func.ST_SetSRID(func.ST_GeomFromGeoJSON(geojson_str), 4326)
    else:
        # LineString or MultiLineString: buffer into avoidance polygon
        geojson_str = json.dumps(geom_dict)
        input_geom = func.ST_SetSRID(func.ST_GeomFromGeoJSON(geojson_str), 4326)
        buffer_radius = (final.buffer_radius or 25.0) / 111000.0  # meters to approx degrees

        if geom_type == "MultiLineString":
            # Dual carriageway (Decision #16): buffer both lines and take convex hull
            final_poly_geom = func.ST_ConvexHull(
                func.ST_Collect(
                    func.ST_Buffer(func.ST_GeometryN(input_geom, 1), buffer_radius),
                    func.ST_Buffer(func.ST_GeometryN(input_geom, 2), buffer_radius)
                )
            )
        else:
            final_poly_geom = func.ST_Buffer(input_geom, buffer_radius)

    # 3. Apply Overrides to Avoidance Zone
    if created_new_zone:
        target_zone = models.FloodAvoidanceZone(
            curated_by_admin_id=current_user.id,
            geometry=final_poly_geom,
            name=final.name,
            severity_override=models.ReportSeverity(final.severity) if final.severity in [s.value for s in models.ReportSeverity] else models.ReportSeverity.MEDIUM,
            depth_override=final.depth,
            passable_vehicles_override=final.passable_vehicles,
            hidden_hazards_override=final.hidden_hazards,
            merge_rationale=final.merge_rationale or f"Merged {len(reports)} reports ({', '.join([f'#{r.id}' for r in reports])})",
            admin_notes=final.admin_notes,
            is_active=True
        )
        db.add(target_zone)
        db.flush()
        try:
            initialize_verified_event_for_zone(
                db=db,
                zone=target_zone,
                peak_severity=final.severity,
                peak_depth=final.depth,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
    else:
        target_zone.curated_by_admin_id = current_user.id
        target_zone.geometry = final_poly_geom
        target_zone.name = final.name
        if final.severity:
            target_zone.severity_override = models.ReportSeverity(final.severity) if final.severity in [s.value for s in models.ReportSeverity] else target_zone.severity_override
        if final.depth:
            target_zone.depth_override = final.depth
        if final.passable_vehicles:
            target_zone.passable_vehicles_override = final.passable_vehicles
        if final.hidden_hazards:
            target_zone.hidden_hazards_override = final.hidden_hazards
        target_zone.merge_rationale = final.merge_rationale or f"Merged {len(reports)} additional reports ({', '.join([f'#{r.id}' for r in reports])})"
        if final.admin_notes:
            target_zone.admin_notes = final.admin_notes
        target_zone.is_active = True
        db.flush()
        record_zone_update(
            db=db,
            zone=target_zone,
            changes={"merge_report_ids": all_report_ids, "official_overrides": final.model_dump(mode="json")},
            commit=False,
        )

    # 4. Link all reports as corroborating evidence without creating duplicate events.
    awarded_user_ids = list(dict.fromkeys(report.user_id for report in reports if report.user_id))
    try:
        for report in reports:
            link_supporting_report(
                db=db,
                report=report,
                event=target_zone.flood_event,
                zone=target_zone,
                acted_by_user_id=current_user.id,
                commit=False,
            )
        db.commit()
        db.refresh(target_zone)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    # 5. Audit Trail Logging
    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="MERGE_REPORTS",
            target_table="flood_avoidance_zones",
            target_id=target_zone.id,
            metadata_json={
                "zone_id": target_zone.id,
                "created_new_zone": created_new_zone,
                "merged_report_ids": all_report_ids,
                "awarded_user_ids": awarded_user_ids,
                "final_severity": final.severity,
            },
            ip_address=client_ip
        )
    )

    # 6. Real-Time Broadcast via SSE
    from app.core.sse import manager
    await manager.broadcast({
        "event": "reports_merged",
        "data": {
            "zone_id": target_zone.id,
            "zone_name": target_zone.name,
            "merged_count": len(reports),
            "report_ids": all_report_ids
        }
    })

    zone_resp = schemas.FloodAvoidanceZoneResponse.model_validate(target_zone)
    return schemas.MergeReportsResponse(
        message=f"Successfully merged {len(reports)} reports into zone '{target_zone.name}'",
        zone_id=target_zone.id,
        zone_name=target_zone.name,
        merged_count=len(reports),
        awarded_user_ids=awarded_user_ids,
        zone=zone_resp
    )


@router.get("/zones/nearby", response_model=List[schemas.NearbyZoneResponse])
def get_nearby_zones(
    report_id: int,
    max_distance_meters: float = 400.0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Find active avoidance zones within proximity of a specific pending flood report.
    Returns calculated geodesic distance in meters for frontend merge recommendations.
    Requires admin privileges.
    """
    nearby_data = crud.get_nearby_active_avoidance_zones(
        db=db,
        report_id=report_id,
        max_distance_meters=max_distance_meters
    )
    
    response = []
    for item in nearby_data:
        zone = item["zone"]
        dist = item["distance_meters"]
        zone_response = schemas.FloodAvoidanceZoneResponse.model_validate(zone)
        response.append(schemas.NearbyZoneResponse(
            id=zone.id,
            severity=zone.severity,
            depth=zone.depth,
            distance_meters=dist,
            created_at=zone.created_at,
            geometry=zone_response.geometry,
            report_count=len(zone.reports)
        ))
    return response


@router.post("/reports/{report_id}/reject", response_model=schemas.FloodReportResponse)
async def reject_report(
    report_id: int,
    request: Request,
    payload: schemas.RejectFloodReportRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Reject a flood report. 
    Requires admin privileges.
    """
    report = crud.get_flood_report(db, report_id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        updated_report = reject_report_with_outcome(
            db=db,
            report=report,
            rejection_reason=payload.reason,
            internal_note=payload.internal_note,
            acted_by_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="REJECT_REPORT",
            target_table="flood_reports",
            target_id=report_id,
            metadata_json={
                "report_id": report_id,
                "reason": payload.reason.value,
                "internal_note": payload.internal_note,
            },
            ip_address=client_ip
        )
    )

    # Broadcast real-time signal
    from app.core.sse import manager
    await manager.broadcast({
        "event": "report_rejected",
        "data": {"report_id": report_id}
    })

    return updated_report


@router.patch("/reports/{report_id}/archive", response_model=schemas.FloodReportResponse)
async def archive_report(
    report_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Archive (soft-delete) a flood report. 
    Requires admin privileges.
    """
    report = crud.archive_flood_report(db, report_id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="ARCHIVE_REPORT",
            target_table="flood_reports",
            target_id=report_id,
            metadata_json={"report_id": report_id},
            ip_address=client_ip
        )
    )

    # Broadcast real-time signal
    from app.core.sse import manager
    await manager.broadcast({
        "event": "report_archived",
        "data": {"report_id": report_id}
    })

    return report


@router.patch("/reports/{report_id}/restore", response_model=schemas.FloodReportResponse)
@router.post("/reports/{report_id}/restore", response_model=schemas.FloodReportResponse)
async def restore_report(
    report_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Restore an archived flood report. 
    Requires admin privileges.
    """
    report = crud.restore_flood_report(db, report_id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or not archived")
    
    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="RESTORE_REPORT",
            target_table="flood_reports",
            target_id=report_id,
            metadata_json={"report_id": report_id},
            ip_address=client_ip
        )
    )

    # Broadcast real-time signal
    from app.core.sse import manager
    await manager.broadcast({
        "event": "report_restored",
        "data": {"report_id": report_id}
    })

    return report


@router.delete("/reports/{report_id}/permanent")
async def permanent_delete_report(
    report_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Permanently delete (hard-delete) a flood report from the archive.
    Requires admin privileges.
    """
    try:
        success = crud.hard_delete_flood_report(db, report_id=report_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    
    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="HARD_DELETE_REPORT",
            target_table="flood_reports",
            target_id=report_id,
            metadata_json={"report_id": report_id},
            ip_address=client_ip
        )
    )
    return {"message": "Report permanently deleted", "id": report_id}


@router.get("/reports/all", response_model=schemas.FloodReportsPaginatedResponse)
def get_all_reports(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "newest",
    archived: bool = False,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    barangays: Optional[str] = None,
) -> Any:
    """
    Retrieve all flood reports with pagination, filtering, and search.
    Requires admin privileges.
    """
    reports, total = crud.get_all_flood_reports_filtered(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        severity=severity,
        search=search,
        sort_by=sort_by,
        archived=archived,
        date_from=date_from,
        date_to=date_to,
        barangays=barangays.split(",") if barangays else None
    )
    return {"reports": reports, "total": total}


@router.get("/dashboard/stats", response_model=schemas.AdminDashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Retrieve aggregated metrics for the admin dashboard.
    Requires admin privileges.
    """
    return crud.get_admin_dashboard_stats(db=db)


@router.get("/dashboard/charts")
def get_dashboard_charts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Retrieve statistics for dashboard charts (severity, timeline, barangays).
    Requires admin privileges.
    """
    return crud.get_admin_dashboard_charts(db=db)


@router.get("/zones/all", response_model=schemas.FloodAvoidanceZonesPaginatedResponse)
def get_all_zones(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
    skip: int = 0,
    limit: int = 10,
    active_only: bool = False,
    archived: bool = False,
    search: Optional[str] = None,
) -> Any:
    """
    Retrieve all flood avoidance zones (detours) with pagination.
    Requires admin privileges.
    """
    zones, total = crud.get_all_avoidance_zones_filtered(
        db=db,
        skip=skip,
        limit=limit,
        active_only=active_only,
        archived=archived,
        search=search,
    )
    
    return {"zones": [_attach_report_media(zone) for zone in zones], "total": total}


@router.patch("/zones/{zone_id}/deactivate", response_model=schemas.FloodAvoidanceZoneResponse)
async def deactivate_zone(
    zone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Deactivate a single flood avoidance zone (detour).
    Requires admin privileges.
    """
    zone = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Avoidance zone not found")
    zone = deactivate_zone_and_end_event_if_final(db=db, zone=zone)

    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="DEACTIVATE_ZONE",
            target_table="flood_avoidance_zones",
            target_id=zone_id,
            metadata_json={"zone_id": zone_id},
            ip_address=client_ip
        )
    )

    # Broadcast real-time signal
    from app.core.sse import manager
    await manager.broadcast({
        "event": "zone_deactivated",
        "data": {"zone_id": zone_id}
    })

    return zone


@router.patch("/zones/{zone_id}/restore", response_model=schemas.FloodAvoidanceZoneResponse)
@router.post("/zones/{zone_id}/restore", response_model=schemas.FloodAvoidanceZoneResponse)
async def restore_zone(
    zone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Restore a deactivated avoidance zone back to active.
    Requires admin privileges.
    """
    existing_zone = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone_id).first()
    if existing_zone and existing_zone.flood_event and existing_zone.flood_event.status == models.FloodEventStatus.ENDED:
        raise HTTPException(status_code=409, detail="Ended Flood Events cannot be reopened. Verify a new flooding event instead.")
    zone = crud.restore_flood_avoidance_zone(db=db, zone_id=zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Avoidance zone not found")

    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="RESTORE_ZONE",
            target_table="flood_avoidance_zones",
            target_id=zone_id,
            metadata_json={"zone_id": zone_id},
            ip_address=client_ip
        )
    )

    from app.core.sse import manager
    await manager.broadcast({
        "event": "zone_updated",
        "data": {"zone_id": zone_id}
    })

    return _attach_report_media(zone)


@router.delete("/zones/{zone_id}/permanent")
async def permanent_delete_zone(
    zone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Permanently delete (hard-delete) an avoidance zone from the archive.
    Requires admin privileges.
    """
    try:
        success = crud.hard_delete_flood_avoidance_zone(db, zone_id=zone_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not success:
        raise HTTPException(status_code=404, detail="Avoidance zone not found")

    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="HARD_DELETE_ZONE",
            target_table="flood_avoidance_zones",
            target_id=zone_id,
            metadata_json={"zone_id": zone_id},
            ip_address=client_ip
        )
    )

    from app.core.sse import manager
    await manager.broadcast({
        "event": "zone_deactivated",
        "data": {"zone_id": zone_id}
    })

    return {"message": "Avoidance zone permanently deleted", "id": zone_id}


@router.patch("/zones/{zone_id}", response_model=schemas.FloodAvoidanceZoneResponse)
async def update_zone(
    zone_id: int,
    payload: schemas.AvoidanceZoneUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Update detour zone settings (is_active, expires_at).
    Requires admin privileges.
    """
    existing_zone = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone_id).first()
    if not existing_zone:
        raise HTTPException(status_code=404, detail="Avoidance zone not found")
    if payload.is_active is True and existing_zone.flood_event and existing_zone.flood_event.status == models.FloodEventStatus.ENDED:
        raise HTTPException(status_code=409, detail="Ended Flood Events cannot be reopened. Verify a new flooding event instead.")
    if payload.is_active is False:
        if payload.expires_at is not None:
            existing_zone.expires_at = payload.expires_at
        zone = deactivate_zone_and_end_event_if_final(db=db, zone=existing_zone)
    else:
        zone = crud.update_flood_avoidance_zone(db=db, zone_id=zone_id, update_data=payload)
        if zone.event_id:
            record_zone_update(
                db=db,
                zone=zone,
                changes=payload.model_dump(exclude_none=True, mode="json"),
            )

    client_ip = request.client.host if request.client else None
    
    # Check if this is technically a restore or archive action based on payload
    if payload.is_active is True and not getattr(zone, '_was_active_before', False):
        action_type = "RESTORE_ZONE"
    elif payload.is_active is False and getattr(zone, '_was_active_before', True):
        action_type = "ARCHIVE_ZONE"
    else:
        action_type = "UPDATE_ZONE"

    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type=action_type,
            target_table="flood_avoidance_zones",
            target_id=zone_id,
            metadata_json={"zone_id": zone_id, "expires_at": payload.expires_at.isoformat() if payload.expires_at else None, "is_active": payload.is_active},
            ip_address=client_ip
        )
    )

    # Broadcast real-time signal
    from app.core.sse import manager
    await manager.broadcast({
        "event": "zone_updated",
        "data": {
            "zone_id": zone_id,
            "is_active": zone.is_active,
            "expires_at": zone.expires_at.isoformat() if zone.expires_at else None
        }
    })

    return zone


@router.patch("/zones/{zone_id}/archive", response_model=schemas.FloodAvoidanceZoneResponse)
async def archive_zone(
    zone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Archive (soft-delete / deactivate) a flood avoidance zone.
    Requires admin privileges.
    """
    zone = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Avoidance zone not found")
    zone = deactivate_zone_and_end_event_if_final(db=db, zone=zone)

    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="ARCHIVE_ZONE",
            target_table="flood_avoidance_zones",
            target_id=zone_id,
            metadata_json={"zone_id": zone_id},
            ip_address=client_ip
        )
    )

    # Broadcast real-time signal
    from app.core.sse import manager
    await manager.broadcast({
        "event": "zone_archived",
        "data": {"zone_id": zone_id}
    })

    return zone


@router.patch("/zones/{zone_id}/restore", response_model=schemas.FloodAvoidanceZoneResponse)
async def restore_zone(
    zone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Restore an archived (deactivated) flood avoidance zone.
    Requires admin privileges.
    """
    existing_zone = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone_id).first()
    if existing_zone and existing_zone.flood_event and existing_zone.flood_event.status == models.FloodEventStatus.ENDED:
        raise HTTPException(status_code=409, detail="Ended Flood Events cannot be reopened. Verify a new flooding event instead.")
    zone = crud.update_flood_avoidance_zone(db=db, zone_id=zone_id, update_data=schemas.AvoidanceZoneUpdateRequest(is_active=True))
    if not zone:
        raise HTTPException(status_code=404, detail="Avoidance zone not found")

    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="RESTORE_ZONE",
            target_table="flood_avoidance_zones",
            target_id=zone_id,
            metadata_json={"zone_id": zone_id},
            ip_address=client_ip
        )
    )

    # Broadcast real-time signal
    from app.core.sse import manager
    await manager.broadcast({
        "event": "zone_restored",
        "data": {"zone_id": zone_id}
    })

    return zone


@router.post("/zones/deactivate-bulk")
async def deactivate_zones_bulk(
    payload: schemas.AvoidanceZoneDeactivateBulkRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Deactivate multiple flood avoidance zones (detours) in bulk.
    Requires admin privileges.
    """
    zones = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id.in_(payload.zone_ids)).all()
    count = 0
    for zone in zones:
        if zone.is_active:
            deactivate_zone_and_end_event_if_final(db=db, zone=zone)
            count += 1
    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="DEACTIVATE_ZONES_BULK",
            target_table="flood_avoidance_zones",
            target_id=None,
            metadata_json={"zone_ids": payload.zone_ids, "count": count},
            ip_address=client_ip
        )
    )

    # Broadcast real-time signal
    from app.core.sse import manager
    await manager.broadcast({
        "event": "zone_deactivated",
        "data": {"zone_ids": payload.zone_ids}
    })

    return {"message": f"Successfully deactivated {count} avoidance zones", "count": count}


@router.get("/users", response_model=schemas.UsersPaginatedResponse)
def get_admin_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    role: Optional[str] = None,
    archived: bool = False,
) -> Any:
    """
    Retrieve all users with filtering, search, and pagination.
    Requires admin privileges.
    """
    users, total = crud.get_users_filtered(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        role=role,
        archived=archived
    )
    return {"users": users, "total": total}


@router.patch("/users/{user_id}/status", response_model=schemas.UserResponse)
def update_admin_user_status(
    user_id: int,
    payload: schemas.UserStatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Toggle a user's active status (activate/deactivate).
    Requires admin privileges.
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own active status")
    
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    previous_status = "active" if user.is_active else "disabled"
    new_status = "active" if payload.is_active else "disabled"

    updated_user = crud.update_user_status(db=db, user_id=user_id, is_active=payload.is_active)
    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="UPDATE_USER_STATUS",
            target_table="users",
            target_id=user_id,
            metadata_json={
                "target_user_id": user_id,
                "target_username": user.username,
                "previous_status": previous_status,
                "new_status": new_status,
                "reason": "Admin status toggle"
            },
            ip_address=client_ip
        )
    )
    return updated_user


@router.post("/users", response_model=schemas.UserResponse, status_code=201)
def create_admin_user(
    payload: schemas.UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Create a new user (usually a sub-admin/moderator) with a specific role.
    Requires admin privileges.
    """
    clean_email = payload.email.strip().lower()
    clean_username = payload.username.strip().lower()

    # 1. Check if an active account already uses this email or username
    active_email_user = db.query(models.User).filter(
        func.lower(models.User.email) == clean_email,
        models.User.deleted_at.is_(None)
    ).first()
    if active_email_user:
        raise HTTPException(status_code=400, detail="Email is already registered by an active account.")

    active_username_user = db.query(models.User).filter(
        func.lower(models.User.username) == clean_username,
        models.User.deleted_at.is_(None)
    ).first()
    if active_username_user:
        raise HTTPException(status_code=400, detail="Username is already taken by an active account.")

    # 2. If an archived/soft-deleted user exists with this email or username, purge it so the new account can be created cleanly
    archived_users = db.query(models.User).filter(
        (func.lower(models.User.email) == clean_email) | (func.lower(models.User.username) == clean_username),
        models.User.deleted_at.is_not(None)
    ).all()
    for arch_user in archived_users:
        crud.hard_delete_user(db, arch_user.id)

    # Set is_active to True to skip OTP
    payload.is_active = True
    payload.email = clean_email
    payload.username = clean_username

    try:
        new_user = crud.create_user(db=db, user=payload)
        # Auto-provision a linked Profile record so the user can immediately edit their profile
        if not new_user.profile:
            default_profile = models.Profile(
                user_id=new_user.id,
                first_name=new_user.username,
                last_name="",
                display_full_name=True,
                is_public=True
            )
            db.add(default_profile)
            db.commit()
            db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email or username already exists.")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create user account. Please try again.")

    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="CREATE_USER",
            target_table="users",
            target_id=new_user.id,
            metadata_json={
                "target_username": new_user.username,
                "role_id": new_user.role_id
            },
            ip_address=client_ip
        )
    )
    return new_user


@router.patch("/users/{user_id}/role", response_model=schemas.UserResponse)
def update_admin_user_role(
    user_id: int,
    payload: schemas.UserRoleUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Update a user's role.
    Requires admin privileges.
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    old_role_id = user.role_id
    updated_user = crud.update_user_role(db=db, user_id=user_id, role_id=payload.role_id)
    
    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="UPDATE_USER_ROLE",
            target_table="users",
            target_id=user_id,
            metadata_json={
                "target_user_id": user_id,
                "target_username": user.username,
                "old_role_id": old_role_id,
                "new_role_id": payload.role_id
            },
            ip_address=client_ip
        )
    )
    return updated_user


@router.delete("/users/{user_id}")
def delete_admin_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Delete a user account.
    Requires admin privileges. Cannot delete yourself.
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
    
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    success = crud.delete_user(db=db, user_id=user_id)
    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="DELETE_USER",
            target_table="users",
            target_id=user_id,
            metadata_json={
                "target_user_id": user_id,
                "target_username": user.username
            },
            ip_address=client_ip
        )
    )
    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/restore", response_model=schemas.UserResponse)
@router.patch("/users/{user_id}/restore", response_model=schemas.UserResponse)
def restore_archived_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Restore an archived / soft-deleted user back to active users.
    Requires admin privileges.
    """
    user = db.query(models.User).filter(models.User.id == user_id, models.User.deleted_at.is_not(None)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Archived user not found")

    # Check if another active account now uses this email or username
    conflict = db.query(models.User).filter(
        ((func.lower(models.User.email) == user.email.lower()) | (func.lower(models.User.username) == user.username.lower())),
        models.User.deleted_at.is_(None),
        models.User.id != user.id
    ).first()
    if conflict:
        raise HTTPException(
            status_code=409,
            detail="Cannot restore: another active account already uses this email or username."
        )

    user.deleted_at = None
    db.commit()
    db.refresh(user)

    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="RESTORE_USER",
            target_table="users",
            target_id=user_id,
            metadata_json={"target_username": user.username},
            ip_address=client_ip
        )
    )
    return user


@router.delete("/users/{user_id}/permanent")
def hard_delete_user_account(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Permanently delete (hard-delete) a user account from the database.
    Requires admin privileges.
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    target_username = user.username
    success = crud.hard_delete_user(db=db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to permanently delete user")

    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="HARD_DELETE_USER",
            target_table="users",
            target_id=user_id,
            metadata_json={"target_username": target_username},
            ip_address=client_ip
        )
    )
    return {"message": "User permanently deleted", "id": user_id}


@router.post("/archive/purge-expired")
def trigger_purge_expired_archive(
    request: Request,
    retention_days: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Manually trigger permanent deletion of soft-deleted/archived records older than retention_days.
    Requires admin privileges.
    """
    from app.services.retention_service import purge_expired_archived_records
    results = purge_expired_archived_records(db=db, retention_days=retention_days)

    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="PURGE_EXPIRED_ARCHIVE",
            target_table="archive",
            target_id=None,
            metadata_json={"retention_days": retention_days, "purged": results},
            ip_address=client_ip
        )
    )
    return {"message": "Expired archive purge completed successfully.", "results": results}



@router.get("/audit-logs", response_model=schemas.AuditLogsPaginatedResponse)
def get_audit_trail(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
    skip: int = 0,
    limit: int = 50,
    action_type: Optional[str] = None,
    admin_id: Optional[int] = None,
) -> Any:
    """
    Retrieve system action audit logs.
    Requires admin privileges.
    """
    logs, total = crud.get_audit_logs(
        db=db,
        skip=skip,
        limit=limit,
        action_type=action_type,
        admin_id=admin_id,
    )
    return {"logs": logs, "total": total}


@router.post("/zones/{zone_id}/merge-pending", response_model=schemas.MergePendingReportsResponse)
async def merge_pending_into_zone(
    zone_id: int,
    payload: schemas.MergePendingReportsRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Batch-approve a list of pending flood reports and merge them all into an
    existing active avoidance zone. The zone must belong to an active Flood
    Event so every approved report receives an event link and an immutable
    moderation outcome. Requires admin privileges.
    """
    target_zone = db.query(models.FloodAvoidanceZone).filter(
        models.FloodAvoidanceZone.id == zone_id
    ).first()
    if not target_zone:
        raise HTTPException(status_code=404, detail="Target avoidance zone not found")
    if not target_zone.is_active or not target_zone.event_id:
        raise HTTPException(
            status_code=409,
            detail="Select an active event-enabled zone, or create a new Flood Event first.",
        )

    target_event = db.get(models.FloodEvent, target_zone.event_id)
    if not target_event or target_event.status != models.FloodEventStatus.ACTIVE:
        raise HTTPException(status_code=409, detail="The target Flood Event is no longer active.")

    reports = [crud.get_flood_report(db, report_id=report_id) for report_id in payload.report_ids]
    if all(
        report
        and report.status == models.ReportStatus.APPROVED
        and report.event_id == target_event.id
        and report.zone_id == target_zone.id
        for report in reports
    ):
        return schemas.MergePendingReportsResponse(
            message=f"Selected reports are already linked to Zone #{zone_id}",
            merged_count=len(reports),
            zone_id=zone_id,
        )
    invalid_ids = [
        report_id
        for report_id, report in zip(payload.report_ids, reports)
        if not report or report.status != models.ReportStatus.PENDING or report.deleted_at is not None
    ]
    if invalid_ids:
        raise HTTPException(
            status_code=409,
            detail=f"Only pending, non-archived reports can be merged. Invalid report IDs: {invalid_ids}",
        )

    try:
        for report in reports:
            link_supporting_report(
                db=db,
                report=report,
                event=target_event,
                zone=target_zone,
                acted_by_user_id=current_user.id,
                commit=False,
            )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception:
        db.rollback()
        logger.exception("Unable to batch-merge reports into zone %s", zone_id)
        raise HTTPException(status_code=500, detail="Unable to merge reports. No changes were saved.")

    merged_count = len(reports)

    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="BATCH_MERGE_REPORTS",
            target_table="flood_avoidance_zones",
            target_id=zone_id,
            metadata_json={
                "zone_id": zone_id,
                "report_ids": payload.report_ids,
                "merged_count": merged_count,
            },
            ip_address=client_ip,
        ),
    )

    # Broadcast real-time signal
    from app.core.sse import manager
    await manager.broadcast({
        "event": "reports_batch_merged",
        "data": {
            "zone_id": zone_id,
            "merged_count": merged_count,
        }
    })

    return schemas.MergePendingReportsResponse(
        message=f"Successfully merged {merged_count} report(s) into Zone #{zone_id}",
        merged_count=merged_count,
        zone_id=zone_id,
    )


@router.post("/zones", response_model=schemas.FloodAvoidanceZoneResponse)
async def create_official_zone(
    request: Request,
    body: str = Form(..., description="JSON-encoded FloodAvoidanceZoneCreateOfficial payload"),
    media: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Create a new official DRRMO flood avoidance zone without a user report.
    Accepts multipart/form-data with an optional list of media files (photos/videos).
    """
    from app.services.cloudinary_service import upload_image

    # Parse the JSON body field
    try:
        payload_data = json.loads(body)
        payload = schemas.FloodAvoidanceZoneCreateOfficial(**payload_data)
    except Exception:
        logger.warning("Invalid official-zone request payload", exc_info=True)
        raise HTTPException(
            status_code=422,
            detail="The zone data is invalid. Please review the shape and try again.",
        )

    zone_geometry: Any = payload.geometry
    source_geometry: Any = None
    if payload.geometry.type in {"LineString", "MultiLineString"}:
        # Official zones are stored as polygons, while the line-mode UI sends a
        # routed road centreline. Buffer it by roughly 25 metres to create the
        # actual avoidance corridor without changing the client contract.
        source_geometry = payload.geometry
        buffer_degrees = 25.0 / 111000.0
        buffered_geojson = db.query(
            func.ST_AsGeoJSON(
                func.ST_Buffer(
                    func.ST_SetSRID(
                        func.ST_GeomFromGeoJSON(payload.geometry.model_dump_json()),
                        4326,
                    ),
                    buffer_degrees,
                )
            )
        ).scalar()
        if not buffered_geojson:
            raise HTTPException(status_code=422, detail="The road segment could not be converted into an avoidance zone.")

        buffered_geometry = json.loads(buffered_geojson)
        if buffered_geometry.get("type") == "Polygon":
            zone_geometry = schemas.PolygonGeometry(**buffered_geometry)
        elif buffered_geometry.get("type") == "MultiPolygon":
            zone_geometry = schemas.MultiPolygonGeometry(**buffered_geometry)
        else:
            logger.error("Unexpected buffered official-zone geometry type: %s", buffered_geometry.get("type"))
            raise HTTPException(status_code=422, detail="The road segment could not be converted into an avoidance zone.")

    media_urls: List[str] = []
    for file in media:
        url = upload_image(file)
        if url:
            media_urls.append(url)

    zone_in = schemas.FloodAvoidanceZoneCreate(
        geometry=zone_geometry,
        source_geometry=source_geometry,
        curated_by_admin_id=current_user.id,
        is_active=payload.is_active
    )
    _, zone = create_verified_event_with_zone(
        db=db,
        zone_input=zone_in,
        peak_severity=payload.severity_override,
        peak_depth=payload.depth_override,
        acted_by_user_id=current_user.id,
        zone_attributes={
            "name": payload.name,
            "severity_override": payload.severity_override,
            "depth_override": payload.depth_override,
            "passable_vehicles_override": payload.passable_vehicles_override,
            "hidden_hazards_override": payload.hidden_hazards_override,
            "admin_notes": payload.admin_notes,
            "media_urls": media_urls or None,
        },
        zone_snapshot={
            "name": payload.name,
            "severity_override": payload.severity_override.value,
            "depth_override": payload.depth_override,
            "source_geometry_type": source_geometry.type if source_geometry else None,
        },
    )

    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="CREATE_OFFICIAL_ZONE",
            target_table="flood_avoidance_zones",
            target_id=zone.id,
            metadata_json={"zone_id": zone.id, "media_count": len(media_urls)},
            ip_address=client_ip
        )
    )

    from app.core.sse import manager
    await manager.broadcast({
        "event": "zone_created",
        "data": {"zone_id": zone.id}
    })

    return _attach_report_media(zone)


@router.get("/zones/{zone_id}", response_model=schemas.FloodAvoidanceZoneResponse)
def get_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """Return the current shared version before resuming a local zone edit."""
    zone = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    if body.is_active is True and zone.flood_event and zone.flood_event.status == models.FloodEventStatus.ENDED:
        raise HTTPException(status_code=409, detail="Ended Flood Events cannot be reopened. Verify a new flooding event instead.")
    return _attach_report_media(zone)


@router.put("/zones/{zone_id}", response_model=schemas.FloodAvoidanceZoneResponse)
async def update_zone(
    zone_id: int,
    request: Request,
    body: schemas.FloodAvoidanceZoneUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Update an existing flood avoidance zone's overrides (DRRMO Edit Map Info).
    """
    zone = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
        
    if body.name is not None:
        zone.name = body.name
    if body.severity_override is not None:
        zone.severity_override = body.severity_override
    if body.depth_override is not None:
        zone.depth_override = body.depth_override
    if body.admin_notes is not None:
        zone.admin_notes = body.admin_notes
    if body.passable_vehicles_override is not None:
        zone.passable_vehicles_override = body.passable_vehicles_override
    if body.hidden_hazards_override is not None:
        zone.hidden_hazards_override = body.hidden_hazards_override
    if body.geometry is not None:
        if body.geometry.type in {"LineString", "MultiLineString"}:
            # Preserve the exact routed centreline for later editing while the
            # polygon remains the authoritative routing barrier.
            source_expression = func.ST_SetSRID(
                func.ST_GeomFromGeoJSON(body.geometry.model_dump_json()),
                4326,
            )
            buffered_geojson = db.query(
                func.ST_AsGeoJSON(func.ST_Buffer(source_expression, 25.0 / 111000.0))
            ).scalar()
            if not buffered_geojson:
                raise HTTPException(status_code=422, detail="The road segment could not be converted into an avoidance zone.")
            buffered_geometry = json.loads(buffered_geojson)
            # The existing column is intentionally a Polygon. A disconnected
            # line set cannot be stored as one operational zone safely.
            if buffered_geometry.get("type") != "Polygon":
                raise HTTPException(status_code=422, detail="The selected road geometry must form one continuous avoidance zone.")
            zone.source_geometry = source_expression
            zone.geometry = func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps(buffered_geometry)), 4326)
        else:
            zone.geometry = func.ST_SetSRID(func.ST_GeomFromGeoJSON(body.geometry.model_dump_json()), 4326)
            zone.source_geometry = None

    changes = body.model_dump(exclude_none=True, mode="json")
    if body.is_active is False:
        zone = deactivate_zone_and_end_event_if_final(db=db, zone=zone)
    else:
        if body.is_active is True:
            zone.is_active = True
        if zone.event_id:
            record_zone_update(db=db, zone=zone, changes=changes)
        else:
            db.commit()
            db.refresh(zone)
    
    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="UPDATE_ZONE",
            target_table="flood_avoidance_zones",
            target_id=zone.id,
            metadata_json={"zone_id": zone.id},
            ip_address=client_ip
        )
    )
    
    from app.core.sse import manager
    await manager.broadcast({
        "event": "zone_updated",
        "data": {"zone_id": zone.id}
    })
    
    return zone


@router.post("/zones/{zone_id}/media", response_model=schemas.FloodAvoidanceZoneResponse)
async def add_zone_media(
    zone_id: int,
    media: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """Append evidence files while an authenticated administrator edits a zone."""
    from app.services.cloudinary_service import upload_image

    zone = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    uploaded_urls = [url for file in media if (url := upload_image(file))]
    if not uploaded_urls:
        raise HTTPException(status_code=422, detail="No media files could be uploaded")

    zone.media_urls = [*(zone.media_urls or []), *uploaded_urls]
    db.commit()
    db.refresh(zone)
    return zone


def _get_user_display_name(user: Optional[models.User], fallback: Optional[str] = "Unknown") -> Optional[str]:
    if not user:
        return fallback
    if user.profile and (user.profile.first_name or user.profile.last_name):
        name = f"{user.profile.first_name or ''} {user.profile.last_name or ''}".strip()
        if name:
            return name
    return user.username or fallback


@router.get("/posts/archived", response_model=schemas.ArchivedCommunityPostsPaginatedResponse)
def get_archived_community_posts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
    skip: int = 0,
    limit: int = 10,
    filter_type: str = "deleted",
    search: Optional[str] = None,
) -> Any:
    """
    Retrieve soft-deleted or hidden community feed posts for the Archive Center.
    Requires admin privileges.
    """
    posts, total = crud.get_archived_posts(
        db=db,
        skip=skip,
        limit=limit,
        post_filter=filter_type,
        search=search,
    )
    
    formatted_posts = []
    for post in posts:
        author_name = _get_user_display_name(post.user, fallback="Unknown") or "Unknown"
        author_avatar = post.user.profile.avatar_url if (post.user and post.user.profile) else None
        deleted_by_name = _get_user_display_name(post.deleted_by, fallback=None) if post.deleted_by else None
        hidden_by_name = _get_user_display_name(post.hidden_by, fallback=None) if post.hidden_by else None

        formatted_posts.append(
            schemas.ArchivedCommunityPostResponse(
                id=post.id,
                user_id=post.user_id,
                author_name=author_name,
                author_avatar=author_avatar,
                content=post.content,
                media_urls=post.media_urls,
                location_tag=post.location_tag,
                location_lat=post.location_lat,
                location_lng=post.location_lng,
                created_at=post.created_at,
                updated_at=post.updated_at,
                deleted_at=post.deleted_at,
                deleted_by_user_id=post.deleted_by_user_id,
                deleted_by_name=deleted_by_name,
                hidden_at=post.hidden_at,
                hidden_by_user_id=post.hidden_by_user_id,
                hidden_by_name=hidden_by_name,
                flood_report_id=post.flood_report_id,
            )
        )

    return schemas.ArchivedCommunityPostsPaginatedResponse(posts=formatted_posts, total=total)


@router.post("/posts/{post_id}/restore", response_model=schemas.ArchivedCommunityPostResponse)
@router.patch("/posts/{post_id}/restore", response_model=schemas.ArchivedCommunityPostResponse)
async def restore_archived_post(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Restore a soft-deleted or hidden post back to the active community feed.
    Requires admin privileges.
    """
    post = crud.restore_post(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="RESTORE_POST",
            target_table="community_posts",
            target_id=post_id,
            metadata_json={"post_id": post_id},
            ip_address=client_ip,
        )
    )

    from app.core.sse import manager
    await manager.broadcast({
        "event": "feed_post_restored",
        "data": {"post_id": post_id}
    })

    author_name = _get_user_display_name(post.user, fallback="Unknown") or "Unknown"
    author_avatar = post.user.profile.avatar_url if (post.user and post.user.profile) else None

    return schemas.ArchivedCommunityPostResponse(
        id=post.id,
        user_id=post.user_id,
        author_name=author_name,
        author_avatar=author_avatar,
        content=post.content,
        media_urls=post.media_urls,
        location_tag=post.location_tag,
        location_lat=post.location_lat,
        location_lng=post.location_lng,
        created_at=post.created_at,
        updated_at=post.updated_at,
        deleted_at=post.deleted_at,
        deleted_by_user_id=post.deleted_by_user_id,
        deleted_by_name=None,
        hidden_at=post.hidden_at,
        hidden_by_user_id=post.hidden_by_user_id,
        hidden_by_name=None,
        flood_report_id=post.flood_report_id,
    )


@router.delete("/posts/{post_id}/permanent")
async def permanent_delete_post(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Permanently delete (hard-delete) a post from the database.
    Requires admin privileges.
    """
    success = crud.hard_delete_post(db=db, post_id=post_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")

    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="HARD_DELETE_POST",
            target_table="community_posts",
            target_id=post_id,
            metadata_json={"post_id": post_id},
            ip_address=client_ip,
        )
    )

    from app.core.sse import manager
    await manager.broadcast({
        "event": "feed_post_permanently_deleted",
        "data": {"post_id": post_id}
    })

    return {"message": "Post permanently deleted", "id": post_id}
