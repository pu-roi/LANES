import json
from typing import List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import crud, models, schemas
from app.api import deps
from app.core.database import get_db

router = APIRouter()


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
    
    # 1. Update report status and timestamp
    report.status = models.ReportStatus.APPROVED
    report.approved_at = datetime.utcnow()

    db.commit()
    db.refresh(report)

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
                                db.commit()
                                db.refresh(report)
        except Exception as e:
            print(f"Photon reverse geocode failed: {e}")

    # 3. Spatial Moderation Action (CREATE_NEW vs MERGE)
    action = body.action if body else "CREATE_NEW"
    target_zone = None

    if action == "MERGE" and body and body.target_zone_id:
        # Merge report into existing active zone
        target_zone = db.query(models.FloodAvoidanceZone).filter(
            models.FloodAvoidanceZone.id == body.target_zone_id
        ).first()
        if target_zone:
            report.zone_id = target_zone.id
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
            db.commit()
            db.refresh(target_zone)
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
            target_zone = crud.create_flood_avoidance_zone(db, zone=zone_in)
            if body.severity:
                target_zone.severity_override = body.severity
            if body.depth:
                target_zone.depth_override = body.depth
            if body.admin_notes:
                target_zone.admin_notes = body.admin_notes
            db.commit()
            db.refresh(target_zone)
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
                target_zone = crud.create_flood_avoidance_zone(db, zone=zone_in)
                if body and body.severity:
                    target_zone.severity_override = body.severity
                if body and body.depth:
                    target_zone.depth_override = body.depth
                if body and body.admin_notes:
                    target_zone.admin_notes = body.admin_notes
                db.commit()
                db.refresh(target_zone)

    # 4. Award Trust Score & Verification credit to reporter
    if report.user_id:
        crud.credit_user_verified_report(db, user_id=report.user_id)

    # 5. [Phase 3] Auto-create CommunityPost if the report is public and not already posted
    if report.is_public and report.user_id and not report.community_post:
        post_in = schemas.CommunityPostCreate(
            flood_report_id=report.id,
            content=report.raw_text,
            media_urls=report.media_urls if report.media_urls else None,
            location_tag=report.barangay or report.human_readable_location or None
        )
        crud.create_community_post(db=db, post_in=post_in, user_id=report.user_id)

    # 6. Audit Trail Logging
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

    # 7. Broadcast real-time signal via SSE
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
    reports = db.query(models.FloodReport).filter(
        models.FloodReport.id.in_(all_report_ids),
        models.FloodReport.deleted_at.is_(None)
    ).all()

    if not reports:
        raise HTTPException(status_code=404, detail="No matching reports found to merge")

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
        db.commit()
        db.refresh(target_zone)
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
        db.commit()
        db.refresh(target_zone)

    # 4. Attach all reports to zone, approve them, and credit trust scores
    awarded_user_ids = []
    for report in reports:
        report.zone_id = target_zone.id
        report.status = models.ReportStatus.APPROVED
        report.approved_at = datetime.utcnow()
        if report.user_id and report.user_id not in awarded_user_ids:
            crud.credit_user_verified_report(db, user_id=report.user_id)
            awarded_user_ids.append(report.user_id)

    db.commit()

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
    
    updated_report = crud.update_flood_report_status(db, report_id=report_id, status="rejected")
    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="REJECT_REPORT",
            target_table="flood_reports",
            target_id=report_id,
            metadata_json={"report_id": report_id, "reason": "Admin manual rejection"},
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
) -> Any:
    """
    Retrieve all flood avoidance zones (detours) with pagination.
    Requires admin privileges.
    """
    zones, total = crud.get_all_avoidance_zones_filtered(
        db=db,
        skip=skip,
        limit=limit,
        active_only=active_only
    )
    
    return {"zones": zones, "total": total}


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
    zone = crud.deactivate_flood_avoidance_zone(db=db, zone_id=zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Avoidance zone not found")

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
    zone = crud.update_flood_avoidance_zone(db=db, zone_id=zone_id, update_data=payload)
    if not zone:
        raise HTTPException(status_code=404, detail="Avoidance zone not found")

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
    zone = crud.deactivate_flood_avoidance_zone(db=db, zone_id=zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Avoidance zone not found")

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
    count = crud.deactivate_flood_avoidance_zones_bulk(db=db, zone_ids=payload.zone_ids)
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
    user = crud.get_user_by_email(db, email=payload.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = crud.get_user_by_username(db, username=payload.username)
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Set is_active to True to skip OTP
    payload.is_active = True
    new_user = crud.create_user(db=db, user=payload)
    
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
    existing active avoidance zone. Credits +5 trust score to each reporter.
    Requires admin privileges.
    """
    target_zone = db.query(models.FloodAvoidanceZone).filter(
        models.FloodAvoidanceZone.id == zone_id
    ).first()
    if not target_zone:
        raise HTTPException(status_code=404, detail="Target avoidance zone not found")

    merged_count = 0
    for report_id in payload.report_ids:
        report = crud.get_flood_report(db, report_id=report_id)
        if not report or report.status != models.ReportStatus.PENDING:
            continue

        # Approve and link report to zone
        report.status = models.ReportStatus.APPROVED
        report.approved_at = datetime.utcnow()
        report.zone_id = target_zone.id
        db.commit()
        db.refresh(report)

        # Award trust score to the reporter
        if report.user_id:
            crud.credit_user_verified_report(db, user_id=report.user_id)

        merged_count += 1

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
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid body JSON: {e}")

    zone_in = schemas.FloodAvoidanceZoneCreate(
        geometry=payload.geometry,
        curated_by_admin_id=current_user.id,
        is_active=payload.is_active
    )
    zone = crud.create_flood_avoidance_zone(db, zone=zone_in)

    # Upload media files to Cloudinary
    media_urls: List[str] = []
    for file in media:
        url = upload_image(file)
        if url:
            media_urls.append(url)

    zone.name = payload.name
    zone.severity_override = payload.severity_override
    zone.depth_override = payload.depth_override
    zone.passable_vehicles_override = payload.passable_vehicles_override
    zone.hidden_hazards_override = payload.hidden_hazards_override
    zone.admin_notes = payload.admin_notes
    zone.media_urls = media_urls if media_urls else None
    db.commit()
    db.refresh(zone)

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

    return zone


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
    if body.is_active is not None:
        zone.is_active = body.is_active

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
