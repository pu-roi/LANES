import os
import csv
import json
import uuid
import shutil
import tempfile
import subprocess
from datetime import datetime, timezone
from typing import List, Optional, Iterator, Tuple
from urllib.parse import quote

import httpx
from sqlalchemy.orm import Session
from sqlalchemy.engine import make_url

from app import models, schemas
from app.core.config import settings
from app.schemas.common import (
    serialize_utc_datetime,
    parse_ewkb_point,
    parse_ewkb_polygon,
    parse_ewkb_linestring,
)

BACKUP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backups"))
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR, exist_ok=True)

EXPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../exports"))
if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR, exist_ok=True)


# ==============================================================================
# Helper: Extract GeoJSON geometry from WKBElement
# ==============================================================================
def _extract_geometry_json(geom_val) -> Optional[dict]:
    if geom_val is None:
        return None
    try:
        from geoalchemy2.elements import WKBElement
        if isinstance(geom_val, WKBElement):
            data = bytes(geom_val.data)
            # Try Point
            try:
                coords = parse_ewkb_point(data)
                return {"type": "Point", "coordinates": coords}
            except Exception:
                pass
            # Try Polygon
            try:
                coords = parse_ewkb_polygon(data)
                return {"type": "Polygon", "coordinates": coords}
            except Exception:
                pass
            # Try LineString
            try:
                coords = parse_ewkb_linestring(data)
                return {"type": "LineString", "coordinates": coords}
            except Exception:
                pass
    except Exception:
        pass
    return None


# ==============================================================================
# Data Export Functions
# ==============================================================================
def export_reports(db: Session, format: str = "csv") -> str:
    reports = db.query(models.FloodReport).order_by(models.FloodReport.id.asc()).all()
    filename = f"reports_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    if format.lower() == "json":
        filepath = os.path.join(EXPORT_DIR, f"{filename}.json")
        data = []
        for r in reports:
            geom = _extract_geometry_json(r.geometry)
            data.append({
                "id": r.id,
                "raw_text": r.raw_text,
                "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                "severity": r.severity.value if hasattr(r.severity, "value") else str(r.severity),
                "depth": r.depth,
                "source": r.source.value if hasattr(r.source, "value") else str(r.source),
                "human_readable_location": r.human_readable_location,
                "barangay": r.barangay,
                "city": r.city,
                "geometry": geom,
                "created_at": serialize_utc_datetime(r.created_at),
                "updated_at": serialize_utc_datetime(r.updated_at),
            })
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return filepath

    else:  # default CSV
        filepath = os.path.join(EXPORT_DIR, f"{filename}.csv")
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "id", "status", "severity", "depth", "source",
                "human_readable_location", "barangay", "city",
                "longitude", "latitude", "created_at", "updated_at", "raw_text"
            ])
            for r in reports:
                geom = _extract_geometry_json(r.geometry)
                lng, lat = "", ""
                if geom and geom.get("type") == "Point" and len(geom.get("coordinates", [])) >= 2:
                    lng = geom["coordinates"][0]
                    lat = geom["coordinates"][1]

                writer.writerow([
                    r.id,
                    r.status.value if hasattr(r.status, "value") else str(r.status),
                    r.severity.value if hasattr(r.severity, "value") else str(r.severity),
                    r.depth or "",
                    r.source.value if hasattr(r.source, "value") else str(r.source),
                    r.human_readable_location or "",
                    r.barangay or "",
                    r.city or "",
                    lng,
                    lat,
                    serialize_utc_datetime(r.created_at) or "",
                    serialize_utc_datetime(r.updated_at) or "",
                    r.raw_text
                ])
        return filepath


def export_zones(db: Session, format: str = "csv") -> str:
    zones = db.query(models.FloodAvoidanceZone).order_by(models.FloodAvoidanceZone.id.asc()).all()
    filename = f"zones_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    if format.lower() == "json":
        filepath = os.path.join(EXPORT_DIR, f"{filename}.json")
        data = []
        for z in zones:
            geom = _extract_geometry_json(z.geometry)
            data.append({
                "id": z.id,
                "report_id": z.report_id,
                "name": z.name,
                "is_active": z.is_active,
                "severity": z.severity,
                "depth": z.depth,
                "admin_notes": z.admin_notes,
                "geometry": geom,
                "created_at": serialize_utc_datetime(z.created_at),
                "updated_at": serialize_utc_datetime(z.updated_at),
                "expires_at": serialize_utc_datetime(z.expires_at),
            })
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return filepath

    else:  # default CSV
        filepath = os.path.join(EXPORT_DIR, f"{filename}.csv")
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "id", "report_id", "name", "is_active", "severity",
                "depth", "created_at", "expires_at", "geometry_coordinates"
            ])
            for z in zones:
                geom = _extract_geometry_json(z.geometry)
                coords_str = json.dumps(geom.get("coordinates", [])) if geom else ""
                writer.writerow([
                    z.id,
                    z.report_id or "",
                    z.name or "",
                    z.is_active,
                    z.severity,
                    z.depth or "",
                    serialize_utc_datetime(z.created_at) or "",
                    serialize_utc_datetime(z.expires_at) or "",
                    coords_str
                ])
        return filepath


# ==============================================================================
# Database Connection Parsing & CLI Execution
# ==============================================================================
def get_db_connection_params() -> dict:
    url = make_url(settings.DATABASE_URL)
    host = url.host
    query_host = url.query.get("host") if hasattr(url, "query") else None
    if query_host and query_host.startswith("/cloudsql/"):
        host = query_host
    elif not host and query_host:
        host = query_host

    return {
        "host": host,
        "port": url.port or 5432,
        "user": url.username or "postgres",
        "password": url.password,
        "database": url.database or "lanes"
    }


def _docker_pg_dump_fallback(output_path: str, params: dict) -> None:
    container_filepath = f"/tmp/{os.path.basename(output_path)}"
    cmd_dump = [
        "docker", "exec", "lanes_postgis_db",
        "pg_dump", "-U", str(params["user"] or "postgres"),
        "-d", str(params["database"] or "lanes"),
        "-F", "c", "-f", container_filepath
    ]
    cmd_cp = [
        "docker", "cp", f"lanes_postgis_db:{container_filepath}", output_path
    ]
    cmd_rm = [
        "docker", "exec", "lanes_postgis_db", "rm", "-f", container_filepath
    ]
    try:
        subprocess.run(cmd_dump, check=True, timeout=120, capture_output=True, text=True)
        subprocess.run(cmd_cp, check=True, timeout=60, capture_output=True, text=True)
    except Exception as e:
        raise RuntimeError(f"pg_dump execution failed (neither local CLI nor Docker available): {e}")
    finally:
        subprocess.run(cmd_rm, check=False)


def _docker_pg_restore_fallback(dump_path: str, params: dict) -> None:
    container_filepath = f"/tmp/{os.path.basename(dump_path)}"
    cmd_cp = [
        "docker", "cp", dump_path, f"lanes_postgis_db:{container_filepath}"
    ]
    cmd_restore = [
        "docker", "exec", "lanes_postgis_db",
        "pg_restore", "-U", str(params["user"] or "postgres"),
        "-d", str(params["database"] or "lanes"),
        "-c", "--if-exists", container_filepath
    ]
    cmd_rm = [
        "docker", "exec", "lanes_postgis_db", "rm", "-f", container_filepath
    ]
    try:
        subprocess.run(cmd_cp, check=True, timeout=60, capture_output=True, text=True)
        subprocess.run(cmd_restore, check=True, timeout=120, capture_output=True, text=True)
    except Exception as e:
        raise RuntimeError(f"pg_restore execution failed (neither local CLI nor Docker available): {e}")
    finally:
        subprocess.run(cmd_rm, check=False)


def execute_pg_dump(output_path: str) -> None:
    params = get_db_connection_params()
    env = os.environ.copy()
    if params["password"]:
        env["PGPASSWORD"] = str(params["password"])

    cmd = ["pg_dump"]
    if params["host"]:
        cmd.extend(["-h", str(params["host"])])
    if params["port"]:
        cmd.extend(["-p", str(params["port"])])
    if params["user"]:
        cmd.extend(["-U", str(params["user"])])
    if params["database"]:
        cmd.extend(["-d", str(params["database"])])
    cmd.extend(["-F", "c", "-f", output_path])

    try:
        subprocess.run(cmd, env=env, check=True, timeout=180, capture_output=True, text=True)
    except FileNotFoundError:
        _docker_pg_dump_fallback(output_path, params)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Database backup dump failed: {e.stderr or e}")


def execute_pg_restore(dump_path: str) -> None:
    params = get_db_connection_params()
    env = os.environ.copy()
    if params["password"]:
        env["PGPASSWORD"] = str(params["password"])

    cmd = ["pg_restore"]
    if params["host"]:
        cmd.extend(["-h", str(params["host"])])
    if params["port"]:
        cmd.extend(["-p", str(params["port"])])
    if params["user"]:
        cmd.extend(["-U", str(params["user"])])
    if params["database"]:
        cmd.extend(["-d", str(params["database"])])
    cmd.extend(["-c", "--if-exists", dump_path])

    try:
        result = subprocess.run(cmd, env=env, check=False, timeout=180, capture_output=True, text=True)
        # pg_restore returns exit code 1 on non-fatal warnings (e.g. dropping non-existent tables)
        if result.returncode != 0 and "FATAL" in (result.stderr or ""):
            raise RuntimeError(f"Database restore failed: {result.stderr}")
    except FileNotFoundError:
        _docker_pg_restore_fallback(dump_path, params)


# ==============================================================================
# Storage Abstraction: Local Disk & Google Cloud Storage (GCS)
# ==============================================================================
class LocalBackupStorage:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)

    def save(self, backup_id: str, dump_name: str, temp_dump_path: str, meta: dict) -> None:
        dest_path = os.path.join(self.base_dir, dump_name)
        if temp_dump_path != dest_path:
            shutil.copyfile(temp_dump_path, dest_path)
        meta_path = os.path.join(self.base_dir, f"{backup_id}.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def list_backups(self) -> List[schemas.BackupFile]:
        backups = []
        if not os.path.exists(self.base_dir):
            return backups
        for f in os.listdir(self.base_dir):
            if f.endswith(".json"):
                meta_path = os.path.join(self.base_dir, f)
                try:
                    with open(meta_path, "r", encoding="utf-8") as mf:
                        meta = json.load(mf)
                    dump_file = os.path.join(self.base_dir, meta["name"])
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
        backups.sort(key=lambda x: x.created_at, reverse=True)
        return backups

    def get_dump_path(self, dump_name: str) -> Optional[str]:
        path = os.path.join(self.base_dir, dump_name)
        return path if os.path.exists(path) else None

    def stream_dump(self, dump_name: str) -> Iterator[bytes]:
        path = os.path.join(self.base_dir, dump_name)
        if not os.path.exists(path):
            raise FileNotFoundError("Backup file missing")
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                yield chunk

    def prepare_dump_for_restore(self, dump_name: str) -> str:
        path = os.path.join(self.base_dir, dump_name)
        if not os.path.exists(path):
            raise FileNotFoundError("Backup file missing")
        return path

    def delete(self, backup_id: str, dump_name: str) -> None:
        dump_path = os.path.join(self.base_dir, dump_name)
        meta_path = os.path.join(self.base_dir, f"{backup_id}.json")
        if os.path.exists(dump_path):
            os.remove(dump_path)
        if os.path.exists(meta_path):
            os.remove(meta_path)


class GCSBackupStorage:
    def __init__(self, bucket: str, prefix: str = "backups"):
        self.bucket = bucket
        self.prefix = prefix.strip("/")

    def _headers(self) -> dict:
        import google.auth
        from google.auth.transport.requests import Request
        credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/devstorage.read_write'])
        credentials.refresh(Request())
        return {'Authorization': f'Bearer {credentials.token}'}

    def save(self, backup_id: str, dump_name: str, temp_dump_path: str, meta: dict) -> None:
        upload_url = f"https://storage.googleapis.com/upload/storage/v1/b/{self.bucket}/o"
        # 1. Upload dump file
        with open(temp_dump_path, "rb") as f:
            content = f.read()
        headers = {**self._headers(), "Content-Type": "application/octet-stream"}
        with httpx.Client(timeout=300, headers=headers) as client:
            resp = client.post(upload_url, params={"uploadType": "media", "name": f"{self.prefix}/{dump_name}"}, content=content)
            if resp.status_code not in (200, 201):
                raise RuntimeError(f"GCS backup dump upload failed ({resp.status_code}): {resp.text}")

        # 2. Upload metadata JSON
        meta_content = json.dumps(meta, indent=2).encode("utf-8")
        headers = {**self._headers(), "Content-Type": "application/json"}
        with httpx.Client(timeout=60, headers=headers) as client:
            resp = client.post(upload_url, params={"uploadType": "media", "name": f"{self.prefix}/{backup_id}.json"}, content=meta_content)
            if resp.status_code not in (200, 201):
                raise RuntimeError(f"GCS backup metadata upload failed ({resp.status_code}): {resp.text}")

    def list_backups(self) -> List[schemas.BackupFile]:
        list_url = f"https://storage.googleapis.com/storage/v1/b/{self.bucket}/o"
        try:
            with httpx.Client(timeout=30, headers=self._headers()) as client:
                resp = client.get(list_url, params={"prefix": f"{self.prefix}/"})
                if resp.status_code != 200:
                    return []
                items = resp.json().get("items", [])
        except Exception:
            return []

        backups = []
        for item in items:
            name = item.get("name", "")
            if name.endswith(".json"):
                try:
                    get_url = f"https://storage.googleapis.com/storage/v1/b/{self.bucket}/o/{quote(name, safe='')}"
                    with httpx.Client(timeout=15, headers=self._headers()) as client:
                        meta_resp = client.get(get_url, params={"alt": "media"})
                        if meta_resp.status_code == 200:
                            meta = meta_resp.json()
                            backups.append(schemas.BackupFile(
                                id=meta["id"],
                                name=meta["name"],
                                size_bytes=int(meta["size_bytes"]),
                                created_at=datetime.fromisoformat(meta["created_at"]),
                                created_by=meta.get("created_by")
                            ))
                except Exception:
                    pass
        backups.sort(key=lambda x: x.created_at, reverse=True)
        return backups

    def get_dump_path(self, dump_name: str) -> Optional[str]:
        # For GCS, direct local path doesn't exist; use stream_dump instead
        return None

    def stream_dump(self, dump_name: str) -> Iterator[bytes]:
        url = f"https://storage.googleapis.com/storage/v1/b/{self.bucket}/o/{quote(f'{self.prefix}/{dump_name}', safe='')}"
        with httpx.Client(timeout=180, headers=self._headers()) as client:
            with client.stream("GET", url, params={"alt": "media"}) as resp:
                if resp.status_code != 200:
                    raise FileNotFoundError(f"GCS backup file missing ({resp.status_code})")
                yield from resp.iter_bytes(chunk_size=65536)

    def prepare_dump_for_restore(self, dump_name: str) -> str:
        temp_file = tempfile.NamedTemporaryFile(suffix=".dump", delete=False)
        temp_file.close()
        url = f"https://storage.googleapis.com/storage/v1/b/{self.bucket}/o/{quote(f'{self.prefix}/{dump_name}', safe='')}"
        with httpx.Client(timeout=180, headers=self._headers()) as client:
            with client.stream("GET", url, params={"alt": "media"}) as resp:
                if resp.status_code != 200:
                    os.unlink(temp_file.name)
                    raise FileNotFoundError(f"GCS backup file missing ({resp.status_code})")
                with open(temp_file.name, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=65536):
                        f.write(chunk)
        return temp_file.name

    def delete(self, backup_id: str, dump_name: str) -> None:
        for name in [f"{self.prefix}/{dump_name}", f"{self.prefix}/{backup_id}.json"]:
            url = f"https://storage.googleapis.com/storage/v1/b/{self.bucket}/o/{quote(name, safe='')}"
            try:
                with httpx.Client(timeout=15, headers=self._headers()) as client:
                    client.delete(url)
            except Exception:
                pass


def get_storage_provider():
    # If in production or connecting to Cloud SQL via unix socket, use GCS
    if settings.ENVIRONMENT.lower() in {"production", "prod"} or "/cloudsql/" in settings.DATABASE_URL:
        try:
            return GCSBackupStorage(bucket=settings.BACKUP_STORAGE_BUCKET, prefix=settings.BACKUP_STORAGE_PREFIX)
        except Exception:
            pass
    return LocalBackupStorage(base_dir=BACKUP_DIR)


# ==============================================================================
# Public Backup & Restore API
# ==============================================================================
def create_backup(user_id: int) -> schemas.BackupFile:
    backup_id = str(uuid.uuid4())
    filename = f"backup_{backup_id}.dump"
    storage = get_storage_provider()

    with tempfile.NamedTemporaryFile(suffix=".dump", delete=False) as temp_dump:
        temp_dump_path = temp_dump.name

    try:
        execute_pg_dump(temp_dump_path)
        stat = os.stat(temp_dump_path)
        meta = {
            "id": backup_id,
            "name": filename,
            "size_bytes": stat.st_size,
            "created_by": str(user_id),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        storage.save(backup_id=backup_id, dump_name=filename, temp_dump_path=temp_dump_path, meta=meta)

        return schemas.BackupFile(
            id=backup_id,
            name=filename,
            size_bytes=stat.st_size,
            created_at=datetime.now(timezone.utc),
            created_by=str(user_id)
        )
    finally:
        if os.path.exists(temp_dump_path):
            os.remove(temp_dump_path)


def list_backups() -> List[schemas.BackupFile]:
    storage = get_storage_provider()
    return storage.list_backups()


def get_backup_download(backup_id: str) -> Tuple[schemas.BackupFile, Optional[str], Optional[Iterator[bytes]]]:
    storage = get_storage_provider()
    backups = storage.list_backups()
    backup = next((b for b in backups if b.id == backup_id), None)
    if not backup:
        raise ValueError("Backup not found")

    local_path = storage.get_dump_path(backup.name)
    if local_path:
        return backup, local_path, None

    # Stream from storage (e.g. GCS)
    stream = storage.stream_dump(backup.name)
    return backup, None, stream


def restore_backup(backup_id: str) -> bool:
    storage = get_storage_provider()
    backups = storage.list_backups()
    backup = next((b for b in backups if b.id == backup_id), None)
    if not backup:
        raise ValueError("Backup not found")

    dump_path = storage.prepare_dump_for_restore(backup.name)
    try:
        execute_pg_restore(dump_path)
        return True
    finally:
        # If the dump was retrieved to a temporary file, clean it up
        if dump_path and not dump_path.startswith(BACKUP_DIR) and os.path.exists(dump_path):
            os.remove(dump_path)


def delete_backup(backup_id: str) -> bool:
    storage = get_storage_provider()
    backups = storage.list_backups()
    backup = next((b for b in backups if b.id == backup_id), None)
    if not backup:
        raise ValueError("Backup not found")

    storage.delete(backup_id=backup_id, dump_name=backup.name)
    return True


# ==============================================================================
# Hardened Data Cleanup (Foreign Key Safe & Community Posts Protected)
# ==============================================================================
def cleanup_data(db: Session, date_from: datetime, date_to: datetime) -> int:
    try:
        # 1. Identify zones in date range
        zone_ids = [z[0] for z in db.query(models.FloodAvoidanceZone.id).filter(
            models.FloodAvoidanceZone.created_at >= date_from,
            models.FloodAvoidanceZone.created_at <= date_to
        ).all()]

        # 2. Identify reports in date range
        report_ids = [r[0] for r in db.query(models.FloodReport.id).filter(
            models.FloodReport.created_at >= date_from,
            models.FloodReport.created_at <= date_to
        ).all()]

        # 3. Disassociate news claim links to avoid ON DELETE RESTRICT failure
        if zone_ids:
            if hasattr(models, "NewsClaimZoneLink"):
                db.query(models.NewsClaimZoneLink).filter(
                    models.NewsClaimZoneLink.zone_id.in_(zone_ids)
                ).delete(synchronize_session=False)

            deleted_zones = db.query(models.FloodAvoidanceZone).filter(
                models.FloodAvoidanceZone.id.in_(zone_ids)
            ).delete(synchronize_session=False)
        else:
            deleted_zones = 0

        # 4. Protect community posts: disassociate them before deleting flood reports
        if report_ids:
            db.query(models.CommunityPost).filter(
                models.CommunityPost.flood_report_id.in_(report_ids)
            ).update({"flood_report_id": None}, synchronize_session=False)

            # Delete associated survey records if any
            if hasattr(models, "FloodReportSurvey"):
                db.query(models.FloodReportSurvey).filter(
                    models.FloodReportSurvey.report_id.in_(report_ids)
                ).delete(synchronize_session=False)

            deleted_reports = db.query(models.FloodReport).filter(
                models.FloodReport.id.in_(report_ids)
            ).delete(synchronize_session=False)
        else:
            deleted_reports = 0

        db.commit()
        return deleted_zones + deleted_reports
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Data cleanup failed: {e}")
