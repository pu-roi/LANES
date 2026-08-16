import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.api import deps
from app import models

def override_get_current_active_admin(db: Session = deps.Depends(deps.get_db)):
    user = db.query(models.User).filter(models.User.username == "admin").first()
    return user

def override_get_current_user(db: Session = deps.Depends(deps.get_db)):
    user = db.query(models.User).filter(models.User.username == "admin").first()
    return user

app.dependency_overrides[deps.get_current_active_admin] = override_get_current_active_admin
app.dependency_overrides[deps.get_current_user] = override_get_current_user

client = TestClient(app)

def test_audit_trail_create_role(db_session: Session):
    # Ensure starting clean for this test
    db_session.query(models.AuditLog).delete()
    db_session.query(models.Role).filter(models.Role.name == "Test Audit Role").delete()
    db_session.commit()

    # Create a new role
    payload = {
        "name": "Test Audit Role",
        "permissions": {"reports": "view"}
    }
    response = client.post("/api/v1/admin/roles", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Audit Role"

    # Verify audit log was created
    audit_log = db_session.query(models.AuditLog).filter(models.AuditLog.action_type == "CREATE_ROLE").first()
    assert audit_log is not None
    assert audit_log.admin.username == "admin"
    assert audit_log.target_table == "roles"
    assert audit_log.target_id == data["id"]
    assert audit_log.metadata_json["role_name"] == "Test Audit Role"
    
    # Optional clean up
    db_session.query(models.AuditLog).delete()
    db_session.query(models.Role).filter(models.Role.name == "Test Audit Role").delete()
    db_session.commit()
