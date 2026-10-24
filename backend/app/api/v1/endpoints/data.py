from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
import os

from app import schemas, models
from app.api import deps
from app.services import data_service
from app.crud.audit import create_audit_log

router = APIRouter()

@router.get("/export/reports", response_class=FileResponse)
def export_reports(
    request: Request,
    db: Session = Depends(deps.get_db),
    format: str = "csv",
    current_user: models.User = Depends(deps.get_current_active_admin)
) -> Any:
    """
    Export all flood reports as CSV or JSON.
    """
    if current_user.role_id is None:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        filepath = data_service.export_reports(db, format=format)

        # Log action
        create_audit_log(
            db=db,
            audit_in=schemas.AuditLogCreate(
                admin_id=current_user.id,
                action_type="EXPORT_DATA",
                target_table="flood_reports",
                metadata_json={"format": format},
                ip_address=request.client.host if request.client else None
            )
        )

        filename = os.path.basename(filepath)
        return FileResponse(filepath, filename=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/zones", response_class=FileResponse)
def export_zones(
    request: Request,
    db: Session = Depends(deps.get_db),
    format: str = "csv",
    current_user: models.User = Depends(deps.get_current_active_admin)
) -> Any:
    """
    Export all avoidance zones as CSV or JSON.
    """
    if current_user.role_id is None:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        filepath = data_service.export_zones(db, format=format)

        # Log action
        create_audit_log(
            db=db,
            audit_in=schemas.AuditLogCreate(
                admin_id=current_user.id,
                action_type="EXPORT_DATA",
                target_table="flood_avoidance_zones",
                metadata_json={"format": format},
                ip_address=request.client.host if request.client else None
            )
        )

        filename = os.path.basename(filepath)
        return FileResponse(filepath, filename=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup", response_model=schemas.BackupFile)
def create_backup(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_admin)
) -> Any:
    """
    Trigger a pg_dump database backup.
    """
    if current_user.role_id is None:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        backup = data_service.create_backup(user_id=current_user.id)

        create_audit_log(
            db=db,
            audit_in=schemas.AuditLogCreate(
                admin_id=current_user.id,
                action_type="CREATE_BACKUP",
                target_table="database",
                metadata_json={"backup_id": backup.id, "filename": backup.name, "size_bytes": backup.size_bytes},
                ip_address=request.client.host if request.client else None
            )
        )

        return backup
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups", response_model=List[schemas.BackupFile])
def list_backups(
    current_user: models.User = Depends(deps.get_current_active_admin)
) -> Any:
    """
    List all available database backups.
    """
    if current_user.role_id is None:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return data_service.list_backups()


@router.get("/backups/{backup_id}/download")
def download_backup(
    backup_id: str,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_admin)
) -> Any:
    """
    Download a specific database backup.
    """
    if current_user.role_id is None:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        backup, local_path, stream = data_service.get_backup_download(backup_id)

        # Log action
        create_audit_log(
            db=db,
            audit_in=schemas.AuditLogCreate(
                admin_id=current_user.id,
                action_type="DOWNLOAD_BACKUP",
                target_table="database",
                metadata_json={"backup_id": backup.id, "filename": backup.name, "size_bytes": backup.size_bytes},
                ip_address=request.client.host if request.client else None
            )
        )

        if local_path:
            return FileResponse(local_path, filename=backup.name, media_type="application/octet-stream")
        elif stream:
            return StreamingResponse(
                stream,
                media_type="application/octet-stream",
                headers={"Content-Disposition": f'attachment; filename="{backup.name}"'}
            )
        else:
            raise HTTPException(status_code=404, detail="Backup file content unavailable")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore/{backup_id}")
def restore_backup(
    backup_id: str,
    req: schemas.RestoreRequest,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_admin)
) -> Any:
    """
    Restore database from a backup file.
    """
    if current_user.role_id is None:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not req.confirm:
        raise HTTPException(status_code=400, detail="Must confirm restoration")

    try:
        data_service.restore_backup(backup_id=backup_id)

        create_audit_log(
            db=db,
            audit_in=schemas.AuditLogCreate(
                admin_id=current_user.id,
                action_type="RESTORE_BACKUP",
                target_table="database",
                metadata_json={"backup_id": backup_id},
                ip_address=request.client.host if request.client else None
            )
        )

        return {"detail": "Database restored successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/backups/{backup_id}")
def delete_backup(
    backup_id: str,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_admin)
) -> Any:
    """
    Delete a specific database backup.
    """
    if current_user.role_id is None:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        data_service.delete_backup(backup_id=backup_id)

        create_audit_log(
            db=db,
            audit_in=schemas.AuditLogCreate(
                admin_id=current_user.id,
                action_type="DELETE_BACKUP",
                target_table="database",
                metadata_json={"backup_id": backup_id},
                ip_address=request.client.host if request.client else None
            )
        )

        return {"detail": "Backup deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
def cleanup_data(
    req: schemas.CleanupRequest,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_admin)
) -> Any:
    """
    Cleanup old data based on date range.
    """
    if current_user.role_id is None:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not req.confirm:
        raise HTTPException(status_code=400, detail="Must confirm cleanup")

    if req.date_from > req.date_to:
        raise HTTPException(status_code=400, detail="Invalid date range: 'From Date' must be before 'To Date'")

    try:
        deleted_count = data_service.cleanup_data(db, req.date_from, req.date_to)

        create_audit_log(
            db=db,
            audit_in=schemas.AuditLogCreate(
                admin_id=current_user.id,
                action_type="CLEANUP_DATA",
                target_table="multiple",
                metadata_json={
                    "date_from": req.date_from.isoformat(),
                    "date_to": req.date_to.isoformat(),
                    "deleted_count": deleted_count
                },
                ip_address=request.client.host if request.client else None
            )
        )

        return {"detail": f"Successfully deleted {deleted_count} records"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
