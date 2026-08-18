from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models, schemas


def get_flood_report(db: Session, report_id: int) -> Optional[models.FloodReport]:
    return db.query(models.FloodReport).filter(models.FloodReport.id == report_id, models.FloodReport.deleted_at.is_(None)).first()


def get_flood_reports(db: Session, skip: int = 0, limit: int = 100) -> List[models.FloodReport]:
    return db.query(models.FloodReport).offset(skip).limit(limit).all()


def get_flood_reports_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.FloodReport]:
    return db.query(models.FloodReport).filter(
        models.FloodReport.user_id == user_id,
        models.FloodReport.deleted_at.is_(None)
    ).order_by(models.FloodReport.created_at.desc()).offset(skip).limit(limit).all()


def get_pending_flood_reports(db: Session, skip: int = 0, limit: int = 100) -> List[models.FloodReport]:
    return db.query(models.FloodReport).filter(
        models.FloodReport.status == "pending",
        models.FloodReport.deleted_at.is_(None)
    ).offset(skip).limit(limit).all()


def credit_user_verified_report(db: Session, user_id: int) -> None:
    """
    Increments reports_approved and recalculates accuracy_rate and trust_score for a user.
    Rule: +5 Trust Score (capped at 100).
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and user.profile:
        user.profile.reports_approved += 1
        # Calculate new trust score (+5 per approved report, capped at 100)
        user.profile.trust_score = min(100, user.profile.trust_score + 5)
        # Recalculate accuracy rate
        total_graded = user.profile.reports_approved + user.profile.reports_rejected
        if total_graded > 0:
            user.profile.accuracy_rate = round((user.profile.reports_approved / total_graded) * 100.0, 1)
        db.commit()


def penalize_user_rejected_report(db: Session, user_id: int) -> None:
    """
    Increments reports_rejected and recalculates accuracy_rate and trust_score for a user.
    Rule: -10 Trust Score (minimum 0).
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and user.profile:
        user.profile.reports_rejected += 1
        user.profile.trust_score = max(0, user.profile.trust_score - 10)
        total_graded = user.profile.reports_approved + user.profile.reports_rejected
        if total_graded > 0:
            user.profile.accuracy_rate = round((user.profile.reports_approved / total_graded) * 100.0, 1)
        db.commit()


def update_flood_report_status(db: Session, report_id: int, status: str) -> Optional[models.FloodReport]:
    report = get_flood_report(db, report_id)
    if report:
        report.status = status
        if status == "rejected" and report.user_id:
            penalize_user_rejected_report(db, report.user_id)
        db.commit()
        db.refresh(report)
    return report


def archive_flood_report(db: Session, report_id: int) -> Optional[models.FloodReport]:
    from datetime import datetime
    # Use direct query to include already deleted items if necessary, or just rely on get which filters by deleted_at is None
    report = db.query(models.FloodReport).filter(models.FloodReport.id == report_id).first()
    if report and report.deleted_at is None:
        report.deleted_at = datetime.utcnow()
        db.commit()
        db.refresh(report)
    return report


def restore_flood_report(db: Session, report_id: int) -> Optional[models.FloodReport]:
    report = db.query(models.FloodReport).filter(models.FloodReport.id == report_id).first()
    if report and report.deleted_at is not None:
        report.deleted_at = None
        db.commit()
        db.refresh(report)
    return report


def create_flood_report(db: Session, report: schemas.FloodReportCreate) -> models.FloodReport:
    geometry_clause = None
    if report.geometry:
        # Convert Pydantic PointGeometry to GeoJSON string for direct PostGIS parsing
        geojson_str = report.geometry.model_dump_json()
        geometry_clause = func.ST_SetSRID(func.ST_GeomFromGeoJSON(geojson_str), 4326)

    db_report = models.FloodReport(
        raw_text=report.raw_text,
        source=report.source,
        severity=report.severity,
        depth=report.depth,
        geometry=geometry_clause,
        human_readable_location=report.human_readable_location,
        is_public=report.is_public,
        user_id=report.user_id,
        media_urls=report.media_urls
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    if report.survey_data:
        db_survey = models.FloodReportSurvey(
            report_id=db_report.id,
            passable_vehicles=report.survey_data.passable_vehicles,
            hidden_hazards=report.survey_data.hidden_hazards
        )
        db.add(db_survey)
        db.commit()
        db.refresh(db_report) # refresh to get the relationship

    return db_report


def get_active_avoidance_zones(db: Session) -> List[models.FloodAvoidanceZone]:
    """
    Selects all avoidance zones that are marked active and whose expiry dates
    are either null (infinite) or in the future.
    """
    return db.query(models.FloodAvoidanceZone).filter(
        models.FloodAvoidanceZone.is_active == True,
        (models.FloodAvoidanceZone.expires_at == None) | (models.FloodAvoidanceZone.expires_at > func.now())
    ).all()


def get_nearby_active_avoidance_zones(
    db: Session,
    report_id: int,
    max_distance_meters: float = 300.0
) -> List[dict]:
    """
    Finds active avoidance zones that are within max_distance_meters of a given flood report's geometry.
    Uses PostGIS ST_Distance with spheroid projection.
    """
    target_report = get_flood_report(db, report_id)
    if not target_report or target_report.geometry is None:
        return []

    # Query active zones and compute geodesic distance
    distance_expr = func.ST_Distance(
        func.ST_Transform(models.FloodAvoidanceZone.geometry, 3857),
        func.ST_Transform(target_report.geometry, 3857)
    )

    results = db.query(
        models.FloodAvoidanceZone,
        distance_expr.label("distance_meters")
    ).filter(
        models.FloodAvoidanceZone.is_active == True,
        (models.FloodAvoidanceZone.expires_at == None) | (models.FloodAvoidanceZone.expires_at > func.now()),
        func.ST_DWithin(
            func.ST_Transform(models.FloodAvoidanceZone.geometry, 3857),
            func.ST_Transform(target_report.geometry, 3857),
            max_distance_meters
        )
    ).order_by("distance_meters").all()

    nearby = []
    for zone, dist in results:
        nearby.append({
            "zone": zone,
            "distance_meters": round(float(dist), 1)
        })
    return nearby


def create_flood_avoidance_zone(db: Session, zone: schemas.FloodAvoidanceZoneCreate) -> models.FloodAvoidanceZone:
    # Convert Pydantic PolygonGeometry to GeoJSON string for direct PostGIS parsing
    geojson_str = zone.geometry.model_dump_json()
    geometry_clause = func.ST_SetSRID(func.ST_GeomFromGeoJSON(geojson_str), 4326)

    db_zone = models.FloodAvoidanceZone(
        geometry=geometry_clause,
        is_active=zone.is_active,
        expires_at=zone.expires_at,
        curated_by_admin_id=zone.curated_by_admin_id
    )
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)

    if zone.report_id:
        db_report = db.query(models.FloodReport).filter(models.FloodReport.id == zone.report_id).first()
        if db_report:
            db_report.zone_id = db_zone.id
            db_report.status = models.ReportStatus.APPROVED
            db_report.approved_at = datetime.utcnow()
            db.commit()
            db.refresh(db_zone)

    return db_zone


def get_all_flood_reports_filtered(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "newest",
    archived: bool = False,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    barangays: Optional[List[str]] = None
) -> tuple[List[models.FloodReport], int]:
    """
    Retrieve all flood reports matching filter criteria, with pagination and search.
    Returns a tuple of (reports, total_count).
    """
    if archived:
        query = db.query(models.FloodReport).filter(models.FloodReport.deleted_at.is_not(None))
    else:
        query = db.query(models.FloodReport).filter(models.FloodReport.deleted_at.is_(None))

    if status and status != "all":
        query = query.filter(models.FloodReport.status == status)
    if severity and severity != "all":
        query = query.filter(models.FloodReport.severity == severity)
    if search:
        query = query.filter(models.FloodReport.raw_text.ilike(f"%{search}%"))

    if date_from:
        query = query.filter(models.FloodReport.created_at >= date_from)
    if date_to:
        query = query.filter(models.FloodReport.created_at <= date_to)

    if barangays and len(barangays) > 0:
        query = query.filter(models.FloodReport.barangay.in_(barangays))

    if sort_by == "oldest":
        query = query.order_by(models.FloodReport.created_at.asc())
    else:
        query = query.order_by(models.FloodReport.created_at.desc())

    total = query.count()
    reports = query.offset(skip).limit(limit).all()
    return reports, total


def get_admin_dashboard_stats(db: Session) -> dict:
    """
    Get aggregated dashboard stats for administrators.
    """
    from datetime import datetime, time
    now = datetime.utcnow()
    start_of_today = datetime.combine(now.date(), time.min)

    total_pending = db.query(models.FloodReport).filter(
        models.FloodReport.status == "pending",
        models.FloodReport.deleted_at.is_(None)
    ).count()
    
    total_active_zones = db.query(models.FloodAvoidanceZone).filter(
        models.FloodAvoidanceZone.is_active == True,
        (models.FloodAvoidanceZone.expires_at == None) | (models.FloodAvoidanceZone.expires_at > func.now())
    ).count()

    total_approved_today = db.query(models.FloodReport).filter(
        models.FloodReport.status == "approved",
        models.FloodReport.updated_at >= start_of_today,
        models.FloodReport.deleted_at.is_(None)
    ).count()

    total_rejected_today = db.query(models.FloodReport).filter(
        models.FloodReport.status == "rejected",
        models.FloodReport.updated_at >= start_of_today,
        models.FloodReport.deleted_at.is_(None)
    ).count()

    total_users = db.query(models.User).count()

    return {
        "total_pending_reports": total_pending,
        "total_active_zones": total_active_zones,
        "total_approved_today": total_approved_today,
        "total_rejected_today": total_rejected_today,
        "total_users": total_users,
        "database_status": "connected"
    }


def deactivate_flood_avoidance_zone(db: Session, zone_id: int) -> Optional[models.FloodAvoidanceZone]:
    db_zone = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone_id).first()
    if db_zone:
        db_zone.is_active = False
        db.commit()
        db.refresh(db_zone)
    return db_zone


def deactivate_flood_avoidance_zones_bulk(db: Session, zone_ids: List[int]) -> int:
    result = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id.in_(zone_ids)).update(
        {"is_active": False}, synchronize_session=False
    )
    db.commit()
    return result


def get_all_avoidance_zones_filtered(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False
) -> tuple[List[models.FloodAvoidanceZone], int]:
    query = db.query(models.FloodAvoidanceZone)
    if active_only:
        query = query.filter(
            models.FloodAvoidanceZone.is_active == True,
            (models.FloodAvoidanceZone.expires_at == None) | (models.FloodAvoidanceZone.expires_at > func.now())
        )
    
    total = query.count()
    zones = query.order_by(models.FloodAvoidanceZone.created_at.desc()).offset(skip).limit(limit).all()
    return zones, total


def update_flood_avoidance_zone(
    db: Session,
    zone_id: int,
    update_data: schemas.AvoidanceZoneUpdateRequest
) -> Optional[models.FloodAvoidanceZone]:
    zone = db.query(models.FloodAvoidanceZone).filter(models.FloodAvoidanceZone.id == zone_id).first()
    if not zone:
        return None
    if update_data.expires_at is not None:
        zone.expires_at = update_data.expires_at
    if update_data.is_active is not None:
        zone.is_active = update_data.is_active
    db.commit()
    db.refresh(zone)
    return zone


def get_admin_dashboard_charts(db: Session) -> dict:
    """
    Retrieve statistics for dashboard charts (severity, timeline, barangays).
    """
    from datetime import datetime, timedelta
    from sqlalchemy import desc
    
    # 1. Severity Distribution
    severity_stats = db.query(
        models.FloodReport.severity,
        func.count(models.FloodReport.id).label("count")
    ).filter(
        models.FloodReport.deleted_at.is_(None)
    ).group_by(models.FloodReport.severity).all()
    
    severity_data = {}
    for row in severity_stats:
        k = row[0].value if hasattr(row[0], 'value') else str(row[0])
        severity_data[k] = row[1]
    
    # Fill in missing severities with 0
    for sev in ["low", "medium", "high", "extreme"]:
        if sev not in severity_data:
            severity_data[sev] = 0

    # 2. Reports Over Time (Last 30 Days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    # Group by date part using func.date (compatible with SQLite/Postgres)
    timeline_stats = db.query(
        func.date(models.FloodReport.created_at).label("day"),
        func.count(models.FloodReport.id).label("count")
    ).filter(
        models.FloodReport.created_at >= thirty_days_ago,
        models.FloodReport.deleted_at.is_(None)
    ).group_by("day").order_by("day").all()
    
    # Pre-populate all 30 days to ensure there are no gaps
    timeline_map = {}
    for row in timeline_stats:
        # handle SQLite vs Postgres date formats or datetime objects
        day_str = str(row.day) if row.day else ""
        if " " in day_str:
            day_str = day_str.split(" ")[0]
        timeline_map[day_str] = row.count

    timeline_data = []
    for i in range(30):
        day_date = (datetime.utcnow() - timedelta(days=29 - i)).date()
        day_str = day_date.isoformat()
        timeline_data.append({
            "date": day_str,
            "count": timeline_map.get(day_str, 0)
        })

    # 3. Top 5 Flooded Barangays
    top_barangays_query = db.query(
        models.FloodReport.barangay,
        func.count(models.FloodReport.id).label("count")
    ).filter(
        models.FloodReport.status == "approved",
        models.FloodReport.deleted_at.is_(None),
        models.FloodReport.barangay.is_not(None),
        models.FloodReport.barangay != ""
    ).group_by(models.FloodReport.barangay).order_by(desc("count")).limit(5).all()
    
    barangay_data = [{"barangay": row.barangay, "count": row.count} for row in top_barangays_query]

    return {
        "severity_distribution": severity_data,
        "reports_timeline": timeline_data,
        "top_barangays": barangay_data
    }
