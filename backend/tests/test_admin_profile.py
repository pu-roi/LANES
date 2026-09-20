import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core import security
from app import models, schemas, crud
from sqlalchemy.orm import Session

def test_admin_created_user_has_profile_and_healing(db_session: Session, client: TestClient):
    db = db_session
    # 1. Create a dummy test user with NO profile directly in DB to test self-healing
    dummy_email = "test_healing_user@lanes.local"
    dummy_user = db.query(models.User).filter(models.User.email == dummy_email).first()
    if dummy_user:
        dummy_user.hashed_password = security.get_password_hash("Password123!")
        if dummy_user.profile:
            db.delete(dummy_user.profile)
        db.commit()
        db.refresh(dummy_user)
    else:
        role = db.query(models.Role).filter(models.Role.name == "Super Admin").first()
        if not role:
            role = models.Role(name="Super Admin", description="Super Admin")
            db.add(role)
            db.commit()
        dummy_user = models.User(
            email=dummy_email,
            username="healinguser",
            hashed_password=security.get_password_hash("Password123!"),
            role_id=role.id,
            is_active=True
        )
        db.add(dummy_user)
        db.commit()
        db.refresh(dummy_user)

    # Verify dummy user has no profile
    db.refresh(dummy_user)
    assert dummy_user.profile is None

    # Authenticate as this dummy user
    token = security.create_access_token({"sub": str(dummy_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Test test-token endpoint heals profile
    res = client.post("/api/v1/auth/test-token", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["profile"] is not None

    # Test PATCH /api/v1/users/me/profile updates and heals seamlessly
    patch_res = client.patch(
        "/api/v1/users/me/profile",
        json={"first_name": "Healing", "last_name": "Tester"},
        headers=headers
    )
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["profile"]["first_name"] == "Healing"
    assert patch_data["profile"]["last_name"] == "Tester"

    # Clean existing OTPs for this email so cooldown doesn't block the test
    db.query(models.OTPVerification).filter(models.OTPVerification.email == dummy_email).delete()
    db.commit()

    # Test request-otp with wrong current password fails
    req_otp_fail = client.post(
        "/api/v1/users/me/password/request-otp",
        json={"current_password": "WrongPassword123!"},
        headers=headers
    )

    assert req_otp_fail.status_code == 400
    assert "Incorrect current password" in req_otp_fail.json()["detail"]

    # Test request-otp with correct current password succeeds
    from unittest.mock import patch, AsyncMock
    with patch("app.services.auth_service.send_password_change_otp_email_async", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = (True, "")
        req_otp_ok = client.post(
            "/api/v1/users/me/password/request-otp",
            json={"current_password": "Password123!"},
            headers=headers
        )
        assert req_otp_ok.status_code == 200, req_otp_ok.json()

        assert "Verification code sent" in req_otp_ok.json()["message"]


    # Manually inject a known OTP for deterministic testing
    from datetime import datetime, timedelta
    from app.services.auth_service import get_otp_hash

    # Clean existing OTPs for this email and add known one
    db.query(models.OTPVerification).filter(models.OTPVerification.email == dummy_email).delete()
    db.commit()

    known_otp = "852963"
    db_otp = models.OTPVerification(
        email=dummy_email,
        otp_code=get_otp_hash(known_otp),
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        attempts=0,
        is_verified=False
    )
    db.add(db_otp)
    db.commit()

    # Test change password with wrong OTP fails
    pwd_res_bad_otp = client.put(
        "/api/v1/users/me/password",
        json={
            "current_password": "Password123!",
            "new_password": "NewSecretPassword123!",
            "otp_code": "000000"
        },
        headers=headers
    )
    assert pwd_res_bad_otp.status_code == 400
    assert "Invalid verification code" in pwd_res_bad_otp.json()["detail"]

    # Re-inject fresh OTP since attempts were counted
    db.query(models.OTPVerification).filter(models.OTPVerification.email == dummy_email).delete()
    db.commit()
    db_otp = models.OTPVerification(
        email=dummy_email,
        otp_code=get_otp_hash(known_otp),
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        attempts=0,
        is_verified=False
    )
    db.add(db_otp)
    db.commit()

    # Test change password with weak new password fails
    pwd_res_weak = client.put(
        "/api/v1/users/me/password",
        json={
            "current_password": "Password123!",
            "new_password": "short",
            "otp_code": known_otp
        },
        headers=headers
    )
    assert pwd_res_weak.status_code == 400

    # Re-inject fresh OTP for success step
    db.query(models.OTPVerification).filter(models.OTPVerification.email == dummy_email).delete()
    db.commit()
    db_otp = models.OTPVerification(
        email=dummy_email,
        otp_code=get_otp_hash(known_otp),
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        attempts=0,
        is_verified=False
    )
    db.add(db_otp)
    db.commit()

    # Test change password success
    pwd_res_ok = client.put(
        "/api/v1/users/me/password",
        json={
            "current_password": "Password123!",
            "new_password": "NewSecretPassword123!",
            "otp_code": known_otp
        },
        headers=headers
    )
    assert pwd_res_ok.status_code == 200
    assert pwd_res_ok.json()["message"] == "Password updated successfully"

    # Verify new password can authenticate
    db.refresh(dummy_user)
    assert security.verify_password("NewSecretPassword123!", dummy_user.hashed_password)

