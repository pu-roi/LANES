import os
import csv
import json
import uuid
import subprocess
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.config import settings

BACKUP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backups"))
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# Ensure data export directory
EXPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../exports"))
if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR)


def export_reports(db: Session, format: str = "csv") -> str:
    reports = db.query(models.FloodReport).all()
    filename = f"reports_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    
    if format.lower() == "json":
        filepath = os.path.join(EXPORT_DIR, f"{filename}.json")
        data = []
        for r in reports:
            data.append({
                "id": r.id,
                "raw_text": r.raw_text,
                "status": r.status,
                "severity": r.severity,
                "source": r.source,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None
            })
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return filepath
        
    else:  # default csv
        filepath = os.path.join(EXPORT_DIR, f"{filename}.csv")
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "status", "severity", "source", "created_at", "updated_at", "raw_text"])
            for r in reports:
                writer.writerow([
                    r.id,
                    r.status,
                    r.severity,
                    r.source,
                    r.created_at.isoformat() if r.created_at else "",
                    r.updated_at.isoformat() if r.updated_at else "",
                    r.raw_text
                ])
        return filepath


def export_zones(db: Session, format: str = "csv") -> str:
    zones = db.query(models.FloodAvoidanceZone).all()
    filename = f"zones_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    
    if format.lower() == "json":
        filepath = os.path.join(EXPORT_DIR, f"{filename}.json")
        data = []
        for z in zones:
            data.append({
                "id": z.id,
                "report_id": z.report_id,
                "is_active": z.is_active,
                "created_at": z.created_at.isoformat() if z.created_at else None,
                "expires_at": z.expires_at.isoformat() if z.expires_at else None
            })
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return filepath
        
    else:
        filepath = os.path.join(EXPORT_DIR, f"{filename}.csv")
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "report_id", "is_active", "created_at", "expires_at"])
            for z in zones:
                writer.writerow([
                    z.id,
                    z.report_id,
                    z.is_active,
                    z.created_at.isoformat() if z.created_at else "",
                    z.expires_at.isoformat() if z.expires_at else ""
                ])
        return filepath


def create_backup(user_id: int) -> schemas.BackupFile:
    backup_id = str(uuid.uuid4())
    filename = f"backup_{backup_id}.dump"
    filepath = os.path.join(BACKUP_DIR, filename)
    
    # Run pg_dump inside container and write to a file inside the container
    container_filepath = f"/tmp/{filename}"
    cmd_dump = [
        "docker", "exec", "lanes_postgis_db",
        "pg_dump", "-U", "postgres", "-d", "lanes", "-F", "c", "-f", container_filepath
    ]
    
    try:
        # Create dump
        subprocess.run(cmd_dump, check=True, timeout=120)
        
        # Copy to host
        cmd_cp = [
            "docker", "cp", f"lanes_postgis_db:{container_filepath}", filepath
        ]
        subprocess.run(cmd_cp, check=True, timeout=60)
        
    except subprocess.CalledProcessError as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise RuntimeError(f"Backup failed: {e}")
    except subprocess.TimeoutExpired as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise RuntimeError("Backup timed out")
    finally:
        # Cleanup container file
        cmd_rm = ["docker", "exec", "lanes_postgis_db", "rm", "-f", container_filepath]
        subprocess.run(cmd_rm, check=False)
    stat = os.stat(filepath)
    
    # Optional: write a small metadata file
    meta_path = os.path.join(BACKUP_DIR, f"{backup_id}.json")
    meta = {
        "id": backup_id,
        "name": filename,
        "created_by": str(user_id),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f)
        
    return schemas.BackupFile(
        id=backup_id,
        name=filename,
        size_bytes=stat.st_size,
        created_at=datetime.now(timezone.utc),
        created_by=str(user_id)
    )


def list_backups() -> List[schemas.BackupFile]:
    backups = []
    for f in os.listdir(BACKUP_DIR):
        if f.endswith(".json"):
            meta_path = os.path.join(BACKUP_DIR, f)
            with open(meta_path, "r") as mf:
                try:
                    meta = json.load(mf)
                    dump_file = os.path.join(BACKUP_DIR, meta["name"])
                    if os.path.exists(dump_file):
                        stat = os.stat(dump_file)
                        backups.append(schemas.BackupFile(
                            id=meta["id"],
                            name=meta["name"],
                            size_bytes=stat.st_size,
                            created_at=datetime.fromisoformat(meta["created_at"]),
                            created_by=meta.get("created_by")
                        ))
                except Exception:
                    pass
    
    # Sort newest first
    backups.sort(key=lambda x: x.created_at, reverse=True)
    return backups


def restore_backup(backup_id: str) -> bool:
    meta_path = os.path.join(BACKUP_DIR, f"{backup_id}.json")
    if not os.path.exists(meta_path):
        raise ValueError("Backup not found")
        
    with open(meta_path, "r") as f:
        meta = json.load(f)
        
    filepath = os.path.join(BACKUP_DIR, meta["name"])
    if not os.path.exists(filepath):
        raise ValueError("Backup file not found")
        
    # We use docker cp to move the file into the container, then run pg_restore
    container_filepath = f"/tmp/{meta['name']}"
    cmd_cp = [
        "docker", "cp", filepath, f"lanes_postgis_db:{container_filepath}"
    ]
    
    cmd_restore = [
        "docker", "exec", "lanes_postgis_db",
        "pg_restore", "-U", "postgres", "-d", "lanes", "-c", "--if-exists", container_filepath
    ]
    
    try:
        subprocess.run(cmd_cp, check=True, timeout=60)
        subprocess.run(cmd_restore, check=True, timeout=120)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Restore failed: {e}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Restore timed out")
    finally:
        cmd_rm = ["docker", "exec", "lanes_postgis_db", "rm", "-f", container_filepath]
        subprocess.run(cmd_rm, check=False)
        
    return True


def delete_backup(backup_id: str) -> bool:
    meta_path = os.path.join(BACKUP_DIR, f"{backup_id}.json")
    if not os.path.exists(meta_path):
        raise ValueError("Backup not found")
        
    with open(meta_path, "r") as f:
        meta = json.load(f)
        
    filepath = os.path.join(BACKUP_DIR, meta["name"])
    
    if os.path.exists(filepath):
        os.remove(filepath)
    if os.path.exists(meta_path):
        os.remove(meta_path)
        
    return True


def cleanup_data(db: Session, date_from: datetime, date_to: datetime) -> int:
    # Delete older reports and zones
    # Be careful with Foreign Key constraints (zones depend on reports).
    # Since we want to cleanup properly, we'll let cascade handle it if configured,
    # or explicitly delete zones then reports.
    
    # Delete zones
    deleted_zones = db.query(models.FloodAvoidanceZone).filter(
        models.FloodAvoidanceZone.created_at >= date_from,
        models.FloodAvoidanceZone.created_at <= date_to
    ).delete(synchronize_session=False)
    
    # Delete reports
    deleted_reports = db.query(models.FloodReport).filter(
        models.FloodReport.created_at >= date_from,
        models.FloodReport.created_at <= date_to
    ).delete(synchronize_session=False)
    
    # Optionally delete audit logs...
    # But usually audit logs are kept or archived. 
    # Let's keep it simple and just return total rows deleted.
    
    db.commit()
    return deleted_zones + deleted_reports
