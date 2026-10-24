import os
import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.core.config import settings
from app.services import data_service
from app import schemas


def test_get_db_connection_params():
    params = data_service.get_db_connection_params()
    assert "user" in params
    assert "database" in params
    assert "port" in params


def test_local_backup_storage_lifecycle(tmp_path):
    storage = data_service.LocalBackupStorage(base_dir=str(tmp_path))
    backup_id = "test-backup-123"
    dump_filename = f"backup_{backup_id}.dump"

    # Create dummy dump file
    dummy_dump = tmp_path / "temp.dump"
    dummy_dump.write_bytes(b"PGDMP_DUMMY_CONTENT")

    meta = {
        "id": backup_id,
        "name": dump_filename,
        "size_bytes": 19,
        "created_by": "1",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # Save
    storage.save(backup_id=backup_id, dump_name=dump_filename, temp_dump_path=str(dummy_dump), meta=meta)

    # List
    backups = storage.list_backups()
    assert len(backups) == 1
    assert backups[0].id == backup_id
    assert backups[0].size_bytes == 19

    # Stream / Path
    path = storage.get_dump_path(dump_filename)
    assert path is not None
    assert os.path.exists(path)

    stream_chunks = list(storage.stream_dump(dump_filename))
    assert b"".join(stream_chunks) == b"PGDMP_DUMMY_CONTENT"

    # Delete
    storage.delete(backup_id=backup_id, dump_name=dump_filename)
    assert len(storage.list_backups()) == 0


def test_cloudsql_socket_parsing():
    original_url = settings.DATABASE_URL
    try:
        settings.DATABASE_URL = "postgresql+psycopg://postgres:secret@/lanes?host=/cloudsql/lanes-project-508809:asia-east1:lanes-db"
        params = data_service.get_db_connection_params()
        assert params["host"] == "/cloudsql/lanes-project-508809:asia-east1:lanes-db"
        assert params["database"] == "lanes"
        assert params["user"] == "postgres"
        assert params["password"] == "secret"
    finally:
        settings.DATABASE_URL = original_url


def test_geometry_extraction_helpers():
    # Null geometry returns None
    assert data_service._extract_geometry_json(None) is None

    # Invalid element returns None
    assert data_service._extract_geometry_json("not_a_geom") is None
