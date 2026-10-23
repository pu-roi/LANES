"""Database-owned, bounded card/map projections for staff workspaces."""
import json
import math
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Text, case, func, or_, select
from sqlalchemy.orm import Session, load_only

from app import models, schemas
from app.crud.report import avoidance_zones_query
from app.schemas.spatial_browse import HistoryRecordsPage, MapPage, MapFeature
from app.services.configuration_service import unexpired_deadline
from app.services.flood_event_service import build_flood_event_history_query, _event_metrics

SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "extreme": 4}


def history_query(db: Session, filters: dict[str, Any]) -> Any:
    values = dict(filters)
    event_id = values.pop("event_id", None)
    query = build_flood_event_history_query(db, **values)
    return query.filter(models.FloodEvent.id == event_id) if event_id else query


def history_cards(db: Session, filters: dict[str, Any], *, page: int, focus_event_id: int | None) -> HistoryRecordsPage:
    event = models.FloodEvent
    query = history_query(db, filters)
    total = query.count()
    pages = max(1, math.ceil(total / 20))
    if focus_event_id is not None:
        focused = query.filter(event.id == focus_event_id).first()
        if focused is None:
            from fastapi import HTTPException
            raise HTTPException(404, "This event is outside the current filters or is no longer available.")
        preceding = query.filter(or_(event.verified_at > focused.verified_at,
            (event.verified_at == focused.verified_at) & (event.id > focused.id))).count()
        page = preceding // 20 + 1
    actual = min(page, pages)
    events = query.order_by(event.verified_at.desc(), event.id.desc()).offset((actual-1)*20).limit(20).all()
    return HistoryRecordsPage(items=card_values(db, events), total=total, page=actual, pages=pages, page_size=20)


def card_values(db: Session, events: list[models.FloodEvent]) -> list[dict[str, Any]]:
    if not events:
        return []
    ids = [event.id for event in events]
    report, zone, location = models.FloodReport, models.FloodAvoidanceZone, models.FloodEventLocation
    reports = {row[0]: row[1:] for row in db.query(report.event_id, func.count(report.id),
        func.count(report.id).filter(report.zone_id.is_not(None)), func.count(func.distinct(report.user_id)))
        .filter(report.event_id.in_(ids), report.status == models.ReportStatus.APPROVED, report.deleted_at.is_(None))
        .group_by(report.event_id)}
    now = datetime.now(timezone.utc)
    zones = {row[0]: row[1:] for row in db.query(zone.event_id, func.count(zone.id),
        func.count(zone.id).filter(zone.is_active.is_(True), unexpired_deadline(db, zone.expires_at, now)))
        .filter(zone.event_id.in_(ids)).group_by(zone.event_id)}
    counts: dict[int, int] = {}
    ranked = db.query(location.id.label("id"), func.count().over(partition_by=location.event_id).label('total'), func.row_number().over(partition_by=location.event_id,
        order_by=(location.location_type, location.display_name, location.id)).label("rank"))
    ranked = ranked.filter(location.event_id.in_(ids)).subquery()
    locations: dict[int, list[Any]] = {}
    for row, total in db.query(location, ranked.c.total).options(load_only(location.id, location.event_id, location.location_type,
            location.display_name, location.normalized_name, location.created_at)).join(ranked, ranked.c.id == location.id).filter(ranked.c.rank <= 3).order_by(
            location.location_type, location.display_name, location.id):
        counts[row.event_id] = total
        locations.setdefault(row.event_id, []).append(schemas.FloodEventLocationResponse.model_validate(row).model_dump(mode="json"))
    result = []
    from app.services.news_history_evidence import event_projections, project_values
    projections = event_projections(db, ids)
    for event in events:
        evidence, supporting, reporters = reports.get(event.id, (0, 0, 0))
        zone_count, active_count = zones.get(event.id, (0, 0))
        result.append(project_values({**schemas.FloodEventResponse.model_validate(event).model_dump(mode="json"),
            **_event_metrics(event, now, {"evidence_count": evidence, "supporting_report_count": supporting,
                "reporter_count": reporters, "zone_count": zone_count, "active_zone_count": active_count,
                "location_count": counts.get(event.id, 0)}), "locations": locations.get(event.id, [])}, projections.get(event.id)))
    return result


def parse_bbox(value: str | None) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    try:
        west, south, east, north = tuple(float(part) for part in value.split(","))
        if not all(math.isfinite(part) for part in (west, south, east, north)) or not (
                -180 <= west < east <= 180 and -85.051129 <= south < north <= 85.051129):
            raise ValueError
        return west, south, east, north
    except (ValueError, TypeError):
        from fastapi import HTTPException
        raise HTTPException(422, "Invalid map bounds") from None


def valid_polygon() -> Any:
    geometry = models.FloodAvoidanceZone.geometry
    return geometry.is_not(None) & func.ST_IsValid(geometry) & ~func.ST_IsEmpty(geometry) & func.GeometryType(geometry).in_(["POLYGON", "MULTIPOLYGON"])


def map_read(db: Session, *, filters: dict[str, Any] | None, bbox: str | None, zoom: float,
             cursor: int, summary_only: bool = False) -> MapPage:
    zone, event, report = models.FloodAvoidanceZone, models.FloodEvent, models.FloodReport
    bounds = parse_bbox(bbox)
    historical = filters is not None
    if historical:
        eligible_events = history_query(db, filters)
        query = eligible_events.join(zone, zone.event_id == event.id).with_entities(zone)
        total = eligible_events.count() if summary_only or not bounds else 0
    else:
        query = avoidance_zones_query(db, active_only=True)
        total = query.count() if summary_only or not bounds else 0
    mapped = query.filter(valid_polygon())
    result = MapPage()
    if summary_only or not bounds:
        extent = func.ST_Extent(zone.geometry)
        west, south, east, north, mapped_count = mapped.with_entities(func.ST_XMin(extent), func.ST_YMin(extent),
            func.ST_XMax(extent), func.ST_YMax(extent), func.count(zone.id)).one()
        global_bounds = (west, south, east, north) if west is not None else None
        mapped_events = mapped.with_entities(func.count(func.distinct(zone.event_id))).scalar() if historical else mapped_count
        result = MapPage(bounds=global_bounds, total=total, mapped_count=mapped_count,
            unmapped_count=max(0, total-int(mapped_events or 0)))
    if summary_only or not bounds:
        return result
    envelope = func.ST_MakeEnvelope(*bounds, 4326)
    visible = mapped.filter(func.ST_Intersects(zone.geometry, envelope))
    result.viewport_count = visible.count()
    if historical and zoom < 15 and cursor == 0:
        result.heatmap_features = heatmap_cells(db, mapped, envelope, bounds, zoom)
    if historical and zoom < 14:
        return result
    fields = [zone.id, func.ST_AsGeoJSON(zone.geometry).label("geojson")]
    if not historical:
        fields.append(zone.event_id)
    if historical:
        fields.extend([zone.event_id, event.peak_severity.label("severity")])
    else:
        from app.models.news_publication import NewsClaimZoneLink, NewsClaimDecision
        primary = lambda column: select(column).where(report.zone_id == zone.id).order_by(report.id).limit(1).correlate(zone).scalar_subquery()
        news_field = lambda name: select(NewsClaimDecision.snapshot["public"][name].as_string()).select_from(NewsClaimZoneLink).join(
            NewsClaimDecision, NewsClaimDecision.id == NewsClaimZoneLink.decision_id).where(NewsClaimZoneLink.zone_id == zone.id).order_by(
            NewsClaimDecision.revision.desc(), NewsClaimDecision.id.desc()).limit(1).correlate(zone).scalar_subquery()
        has_news = select(NewsClaimZoneLink.zone_id).where(NewsClaimZoneLink.zone_id == zone.id).correlate(zone).exists()
        max_rank = select(func.max(case(*[(report.severity == level, rank) for level, rank in SEVERITY_RANK.items()], else_=2)))
        max_rank = max_rank.where(report.zone_id == zone.id).correlate(zone).scalar_subquery()
        level = case(*[(max_rank == rank, name) for name, rank in SEVERITY_RANK.items()], else_="medium")
        fields.extend([zone.created_at, zone.updated_at, zone.expires_at, zone.name, zone.admin_notes, zone.is_active,
            zone.passable_vehicles_override, zone.hidden_hazards_override,
            func.coalesce(zone.severity_override, level).label("severity"),
            func.coalesce(func.nullif(zone.depth_override, ""), primary(report.depth)).label("depth"),
            func.ST_AsGeoJSON(func.coalesce(zone.source_geometry, primary(report.geometry))).label("report_geometry"),
            primary(report.id).label("report_id"), func.coalesce(primary(report.source.cast(Text)),
                case((has_news, "news"), (zone.curated_by_admin_id.is_not(None), "official"), else_="other")).label("report_source"),
            news_field("source_publisher").label("reporter_name"),
            func.coalesce(func.nullif(zone.admin_notes, ""), primary(report.raw_text), news_field("evidence_excerpt")).label("report_text")])
    rows = visible.filter(zone.id > cursor).with_entities(*fields).order_by(zone.id).limit(251).all()
    result.next_cursor = rows[249].id if len(rows) > 250 else None
    labels = {}
    if not historical:
        user, profile, role, survey = models.User, models.Profile, models.Role, models.FloodReportSurvey
        report_ids = [row.report_id for row in rows[:250] if row.report_id is not None]
        if report_ids:
            labels = {row.id: row for row in db.query(report.id, user.username, profile.first_name, profile.last_name,
                role.name.label("role"), survey.passable_vehicles, survey.hidden_hazards)
                .outerjoin(user, user.id == report.user_id).outerjoin(profile, profile.user_id == user.id)
                .outerjoin(role, role.id == user.role_id).outerjoin(survey, survey.report_id == report.id)
                .filter(report.id.in_(report_ids))}
    from app.services.historical_news_metadata import event_metadata, public_metadata
    historical_metadata = event_metadata(db, [row.event_id for row in rows[:250] if row.event_id])
    for row in rows[:250]:
        properties = dict(row._mapping)
        geometry = json.loads(properties.pop("geojson"))
        metadata = historical_metadata.get(row.event_id)
        properties["historical"] = public_metadata(metadata)
        properties["affects_routing"] = not metadata.is_demo if metadata else True
        if historical:
            properties["zone_id"] = row.id
        else:
            properties["report_geometry"] = json.loads(row.report_geometry) if row.report_geometry else None
            evidence = labels.get(row.report_id)
            properties["passable_vehicles"] = properties.pop("passable_vehicles_override") or (evidence.passable_vehicles if evidence else None)
            hazard = properties.pop("hidden_hazards_override") or (evidence.hidden_hazards if evidence else None)
            properties["hidden_hazards"] = getattr(hazard, "value", hazard)
            properties["reporter_role"] = evidence.role if evidence else "News report" if row.report_source == "news" else None
            properties["reporter_name"] = (" ".join(part for part in (evidence.first_name, evidence.last_name) if part).strip()
                or evidence.username or "Anonymous") if evidence else row.reporter_name or "System"
            from app.services.flood_depth import format_flood_depth
            properties["depth_formatted"] = format_flood_depth(row.depth) if row.depth else None
        result.features.append(MapFeature(geometry=geometry, properties=properties))
    return result


def heatmap_cells(db: Session, query: Any, envelope: Any, bounds: tuple[float, float, float, float], zoom: float) -> list[MapFeature]:
    """Bound overview size without excluding any matching representative point."""
    zone, event = models.FloodAvoidanceZone, models.FloodEvent
    point = func.ST_PointOnSurface(zone.geometry)
    projected = func.ST_Transform(point, 3857)
    weight = case((event.peak_severity == "low", 1), (event.peak_severity == "medium", 2),
                  (event.peak_severity == "high", 3), (event.peak_severity == "extreme", 5), else_=2)
    west, south, east, north = bounds
    mercator_y = lambda lat: 6378137 * math.log(math.tan(math.pi/4 + math.radians(lat)/2))
    left, right = math.radians(west)*6378137, math.radians(east)*6378137
    bottom, top = mercator_y(south), mercator_y(north)
    cell = 40075016.68557849/(512 * 2**zoom)*8
    while (math.floor(right/cell)-math.floor(left/cell)+1)*(math.floor(top/cell)-math.floor(bottom/cell)+1) > 4096:
        cell *= 2
    points = query.filter(func.ST_Intersects(point, envelope)).with_entities(zone.id.label("id"),
        func.ST_AsGeoJSON(point).label("point"), weight.label("weight"),
        func.floor(func.ST_X(projected)/cell).label("x"), func.floor(func.ST_Y(projected)/cell).label("y")).cte("viewport_points")
    cells = select(func.min(points.c.id).label("representative"), func.sum(points.c.weight).label("weight"),
        func.count().label("zone_count")).group_by(points.c.x, points.c.y).subquery()
    rows = db.execute(select(points.c.point, cells.c.weight, cells.c.zone_count).join(cells, cells.c.representative == points.c.id))
    return [MapFeature(geometry=json.loads(row.point), properties={"weight": row.weight, "zone_count": row.zone_count}) for row in rows]


def require_event(db: Session, event_id: int, dataset_id: str | None = None) -> models.FloodEvent:
    from fastapi import HTTPException
    event = (history_query(db, {'dataset_id': dataset_id, 'event_id': event_id}).first()
             if dataset_id else db.get(models.FloodEvent, event_id))
    if event is None:
        raise HTTPException(404, "Flood Event not found")
    from app.services.news_gma_active_outputs import active_only_event
    from app.services.news_source_repair import superseded_event
    blocked = db.query(models.FloodEvent.id, active_only_event().label('active_only')).filter(
        models.FloodEvent.id == event_id, or_(active_only_event(), superseded_event())).first()
    if blocked and blocked.active_only:
        raise HTTPException(404, "Flood Event not found")
    if blocked:
        raise HTTPException(409, "This news archive was superseded after a source correction. Review the current Flood History records.")
    return event


def history_overview(db: Session, event_id: int, dataset_id: str | None = None) -> dict[str, Any]:
    event = require_event(db, event_id, dataset_id)
    value = card_values(db, [event])[0]
    report, zone = models.FloodReport, models.FloodAvoidanceZone
    report_media = db.query(func.coalesce(func.sum(func.jsonb_array_length(report.media_urls)), 0)).filter(
        report.event_id == event_id, report.deleted_at.is_(None)).scalar()
    zone_media = db.query(func.coalesce(func.sum(func.jsonb_array_length(zone.media_urls)), 0)).filter(zone.event_id == event_id).scalar()
    value.update(reports=[], zones=[], timeline=[], media_count=int(report_media or 0)+int(zone_media or 0))
    # The paged collections own evidence; the initial dialog never loads it all.
    return value


def history_collection(db: Session, event_id: int, collection: str, page: int, dataset_id: str | None = None) -> Any:
    from app.schemas.spatial_browse import InspectionPage
    from app.schemas.flood_event import HistoricalFloodZoneResponse
    from app.crud.zone_queue import queue_zone_details
    from app.services.news_zone_projection_service import brief_zone_response_bases
    from sqlalchemy.orm import selectinload
    require_event(db, event_id, dataset_id)
    if collection == 'news_sources':
        from app.services.news_history_evidence import news_sources
        return news_sources(db, event_id, page)
    model, schema, time = {
        "reports": (models.FloodReport, schemas.FloodReportResponse, models.FloodReport.created_at),
        "zones": (models.FloodAvoidanceZone, HistoricalFloodZoneResponse, models.FloodAvoidanceZone.created_at),
        "timeline": (models.FloodEventTimelineEntry, schemas.FloodEventTimelineEntryResponse, models.FloodEventTimelineEntry.occurred_at),
        "locations": (models.FloodEventLocation, schemas.FloodEventLocationResponse, models.FloodEventLocation.created_at),
    }[collection]
    query = db.query(model).filter(model.event_id == event_id)
    if collection == "timeline":
        query = query.filter(model.entry_type != 'historical_demo_deactivated')
    if collection == "reports":
        query = query.filter(model.deleted_at.is_(None))
    total = query.count()
    actual = min(page, max(1, math.ceil(total/20)))
    selected = query.order_by(time, model.id).offset((actual-1)*20).limit(20)
    if collection == "reports":
        selected = selected.options(selectinload(model.user).selectinload(models.User.profile),
            selectinload(model.user).selectinload(models.User.role), selectinload(model.survey))
    if collection == "zones":
        ids = [row.id for row in selected.with_entities(model.id)]
        by_id = {row.id: row for row in queue_zone_details(db, ids, brief=True)}
        zones = [by_id[id] for id in ids]
        # History owns retained source evidence in news_sources; current alerts
        # cannot describe an inactive historical footprint.
        values = brief_zone_response_bases(db, zones, schema=HistoricalFloodZoneResponse)
    else:
        values = [schema.model_validate(row) for row in selected]
    return InspectionPage(items=[value.model_dump(mode="json") for value in values], total=total,
        page=actual, pages=max(1, math.ceil(total/20)), page_size=20)


def zone_contributors(db: Session, zone_id: int, page: int, focus_report_id: int | None) -> Any:
    from fastapi import HTTPException
    from sqlalchemy.orm import selectinload
    from app.schemas.report import ZoneContributorResponse
    from app.schemas.spatial_browse import InspectionPage
    if db.get(models.FloodAvoidanceZone, zone_id) is None:
        raise HTTPException(404, "Zone not found")
    report = models.FloodReport
    query = db.query(report).filter(report.zone_id == zone_id)
    total = query.count()
    if focus_report_id is not None and query.filter(report.id == focus_report_id).first() is not None:
        page = query.filter(report.id < focus_report_id).count() // 20 + 1
    actual = min(page, max(1, math.ceil(total/20)))
    primary_id = query.with_entities(func.min(report.id)).scalar()
    rows = query.options(selectinload(report.user).selectinload(models.User.profile),
        selectinload(report.user).selectinload(models.User.role)).order_by(report.id).offset((actual-1)*20).limit(20)
    items = []
    for row in rows:
        user = row.user
        profile = user.profile if user else None
        name = " ".join(part for part in (profile.first_name, profile.last_name) if part) if profile else ""
        value = dict(report_id=row.id, reporter_name=name or (user.username if user else "Anonymous"),
            reporter_username=user.username if user else None, reporter_role=user.role.name if user and user.role else None,
            reporter_trust_score=float(profile.trust_score) if profile else 100.0, raw_text=row.raw_text,
            severity=str(getattr(row.severity, "value", row.severity)), depth=row.depth, created_at=row.created_at,
            is_primary=row.id == primary_id, geometry=row.geometry)
        items.append(ZoneContributorResponse.model_validate(value).model_dump(mode="json"))
    return InspectionPage(items=items, total=total, page=actual, pages=max(1, math.ceil(total/20)), page_size=20)


def planning_metrics(db: Session, query: Any) -> dict[str, Any]:
    """Aggregate the entire matching history without materializing event/evidence rows."""
    event, report, location = models.FloodEvent, models.FloodReport, models.FloodEventLocation
    from app.services.historical_news_metadata import demo_event, occurrence_day, observed_duration_eligible, metadata_field
    demo_count, simulated_count, unknown_count = query.with_entities(
        func.count().filter(demo_event()),
        func.count().filter(~demo_event(), metadata_field('closure_basis') == 'assumed_two_hours'),
        func.count().filter(~demo_event(), metadata_field('dataset_id').is_not(None), event.ended_at.is_(None))).one()
    selected = query.filter(~demo_event()).with_entities(event.id, event.status, event.verified_at, event.ended_at, event.peak_severity, occurrence_day().label("occurrence_day"), observed_duration_eligible().label("duration_eligible")).subquery()
    ended = selected.c.status == "ended"
    duration_ended = ended & selected.c.duration_eligible
    minutes = func.greatest(0, func.floor(func.extract("epoch", selected.c.ended_at-selected.c.verified_at)/60))
    total, ended_count, average = db.query(func.count(selected.c.id), func.count().filter(ended),
        func.avg(minutes).filter(duration_ended, selected.c.ended_at.is_not(None))).one()
    durations = db.query(*(func.count().filter(duration_ended, selected.c.ended_at.is_not(None), predicate) for predicate in (
        minutes < 60, (minutes >= 60) & (minutes < 180), (minutes >= 180) & (minutes < 360), minutes >= 360))).one()
    levels = dict(db.query(selected.c.peak_severity,func.count()).group_by(selected.c.peak_severity).all())
    day = selected.c.occurrence_day
    days = db.query(day,func.count()).group_by(day).order_by(day).all()
    local_time = func.timezone("Asia/Manila",selected.c.verified_at)
    weekday, hour = func.extract("isodow",local_time)-1, func.extract("hour",local_time)
    pattern = db.query(weekday,hour,func.count()).group_by(weekday,hour).order_by(weekday,hour).all()
    places = db.query(location.event_id,location.location_type,location.normalized_name,
        func.min(location.display_name.collate("C")).label("name")).join(selected,selected.c.id == location.event_id).group_by(
        location.event_id,location.location_type,location.normalized_name).subquery()
    place_counts = db.query(places.c.location_type,places.c.name,func.count()).group_by(places.c.location_type,places.c.name).all()
    def top(kind: str) -> list[dict[str, Any]]:
        return [{"name":name,"event_count":count} for level,name,count in sorted(place_counts,key=lambda row:(-row[2],row[1])) if level == kind][:10]
    report_day = func.date(func.coalesce(report.approved_at, report.created_at))
    report_days = db.query(report_day,func.count(report.id)).join(selected,selected.c.id == report.event_id).filter(
        report.status == models.ReportStatus.APPROVED,report.deleted_at.is_(None)).group_by(report_day).order_by(report_day).all()
    report_count = sum(count for _,count in report_days)
    return {"demonstration_instances":demo_count,
        "historical_intervals":{"assumed_two_hour_events":simulated_count,"unknown_endpoints":unknown_count},
        "total_events":total,"ended_events":ended_count,"active_events":total-ended_count,
        "peak_severity_distribution":[{"severity":name,"event_count":levels.get(name,0)} for name in SEVERITY_RANK],
        "duration":{"ended_event_count":sum(durations),"average_minutes":round(float(average),1) if average is not None else None,
            "distribution":[{"bucket":label,"event_count":count} for label,count in zip(("Under 1 hour","1–3 hours","3–6 hours","Over 6 hours"),durations)]},
        "events_over_time":[{"date":str(date) if date is not None else "Unknown","event_count":count} for date,count in days],
        "approved_reports_over_time":[{"date":str(date),"report_count":count} for date,count in report_days],
        "verification_pattern":[{"weekday":int(weekday),"hour":int(hour),"event_count":count} for weekday,hour,count in pattern],
        "recurring_barangays":top("barangay"),"frequently_affected_roads":top("road"),
        "supporting_report_volume":{"approved_report_count":report_count,"average_per_event":round(report_count/total,1) if total else 0},
        "definitions":{
            "flood_events":"Distinct verified incidents. Repeated reports for one incident count once.",
            "supporting_reports":"Approved, non-deleted reports linked to the selected Flood Events; a confidence signal, not an event count.",
            "peak_verified_severity":"The highest verified severity recorded for each Flood Event.",
            "official_duration":"Time from operational verification until the final active zone ended. News administrative intervals, imported assumptions and active events are excluded.",
            "historical_occurrence":"News-origin events use supported source occurrence dates; unknown source dates remain unknown. Demonstration instances do not add real flood occurrences.",
            "verification_pattern":"Verified Flood Events by Asia/Manila day and hour. This shows verification timing, not when floodwater first began."}}
