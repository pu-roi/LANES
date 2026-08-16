from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Approve a flood report. Automatically generates a FloodAvoidanceZone if the report has coordinates.
    Requires admin privileges.
    """
    report = crud.get_flood_report(db, report_id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status == "approved":
        raise HTTPException(status_code=400, detail="Report is already approved")
    
    report = crud.update_flood_report_status(db, report_id=report_id, status="approved")

    # Reverse geocode using Photon API to get the barangay
    response_report = schemas.FloodReportResponse.model_validate(report)
    if response_report.geometry and not report.barangay:
        import httpx
        
        coords = response_report.geometry.coordinates
        lon, lat = None, None
        if response_report.geometry.type == "Point":
            lon, lat = coords[0], coords[1]
        elif response_report.geometry.type == "LineString":
            lon, lat = coords[0][0], coords[0][1]
            
        if lon is not None and lat is not None:
            url = f"https://photon.komoot.io/reverse?lon={lon}&lat={lat}"
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, timeout=5.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        features = data.get("features", [])
                        if features:
                            props = features[0].get("properties", {})
                            barangay = props.get("district") or props.get("locality") or props.get("city")
                            if barangay:
                                report.barangay = barangay
                                db.commit()
                                db.refresh(report)
                                response_report = schemas.FloodReportResponse.model_validate(report)
            except Exception as e:
                print(f"Photon reverse geocode failed: {e}")

    # If the report has geometry, create an avoidance zone (simple 200m bounding box buffer)
    # The geometry field on the response schema will have the PointGeometry parsed from EWKB
    response_report = schemas.FloodReportResponse.model_validate(report)
    if response_report.geometry:
        from sqlalchemy import func
        import json

        is_linestring = response_report.geometry.type == "LineString"
        buffer_radius = 0.00015 if is_linestring else 0.0005

        # Query PostGIS to calculate the buffer polygon
        buffered_geojson_str = db.query(
            func.ST_AsGeoJSON(func.ST_Buffer(report.geometry, buffer_radius))
        ).scalar()

        if buffered_geojson_str:
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
            crud.create_flood_avoidance_zone(db, zone=zone_in)
            
    # [Phase 3] Auto-create CommunityPost if the report is public
    if report.is_public and report.user_id:
        post_in = schemas.CommunityPostCreate(
            flood_report_id=report.id,
            content=report.raw_text,
            media_urls=[report.image_url] if report.image_url else None
        )
        crud.create_community_post(db=db, post_in=post_in, user_id=report.user_id)

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
                "severity": report.severity,
                "detour_generated": {
                    "has_geometry": bool(response_report.geometry)
                }
            },
            ip_address=client_ip
        )
    )

    # Broadcast real-time signal
    from app.core.sse import manager
    await manager.broadcast({
        "event": "report_approved",
        "data": {"report_id": report.id}
    })

    return report


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
        archived=archived
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
    
    # Populate future-proofed reporter details and trust metrics
    for zone in zones:
        if zone.report:
            zone.report_text = zone.report.raw_text
            zone.report_source = zone.report.source.value if hasattr(zone.report.source, 'value') else str(zone.report.source)
            zone.depth = zone.report.depth
            if zone.report.user:
                zone.reporter_name = zone.report.user.username
                user_id = zone.report.user_id
                reports_submitted = db.query(models.FloodReport).filter(
                    models.FloodReport.user_id == user_id,
                    models.FloodReport.deleted_at.is_(None)
                ).count()
                reports_verified = db.query(models.FloodReport).filter(
                    models.FloodReport.user_id == user_id,
                    models.FloodReport.status == "approved",
                    models.FloodReport.deleted_at.is_(None)
                ).count()
                zone.reporter_reports_submitted = reports_submitted
                zone.reporter_reports_verified = reports_verified
                zone.reporter_trust_score = round((reports_verified / reports_submitted) * 100.0, 1) if reports_submitted > 0 else 100.0
            else:
                # Default for automated/social scraper reports
                zone.reporter_name = "System Parser"
                zone.reporter_trust_score = 100.0
                zone.reporter_reports_submitted = 0
                zone.reporter_reports_verified = 0
                
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
