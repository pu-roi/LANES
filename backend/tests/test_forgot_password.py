import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core import security

client = TestClient(app)


def test_forgot_password_request_nonexistent_email(monkeypatch):
    """Verify nonexistent emails receive clear 404 response."""
    from app import crud
    monkeypatch.setattr(crud, "get_user_by_email", lambda db, email: None)

    response = client.post(
        "/api/v1/auth/forgot-password/request-otp",
        json={"email": "nonexistent_email@example.com"}
    )
    assert response.status_code == 404
    assert "No registered account found with this email" in response.json()["detail"]


def test_forgot_password_request_existing_user(monkeypatch):
    """Verify requesting password reset for an existing active user sends OTP."""
    from app import crud
    from app.api.v1.endpoints import auth as auth_endpoint

    mock_user = MagicMock()
    mock_user.id = 10
    mock_user.email = "existing_user@example.com"
    mock_user.is_active = True

    monkeypatch.setattr(crud, "get_user_by_email", lambda db, email: mock_user)

    async def mock_send(db, email):
        return True, "", 60

    monkeypatch.setattr(auth_endpoint, "generate_and_send_password_reset_otp", mock_send)

    response = client.post(
        "/api/v1/auth/forgot-password/request-otp",
        json={"email": "existing_user@example.com"}
    )
    assert response.status_code == 200
    assert "Password reset code sent successfully" in response.json()["msg"]
    assert response.json()["cooldown_seconds"] == 60


def test_forgot_password_verify_invalid_otp(monkeypatch):
    """Verify that invalid OTP returns 400 Bad Request."""
    from app import crud
    from app.api.v1.endpoints import auth as auth_endpoint

    mock_user = MagicMock()
    mock_user.id = 10
    mock_user.email = "test@example.com"
    mock_user.is_active = True

    monkeypatch.setattr(crud, "get_user_by_email", lambda db, email: mock_user)
    monkeypatch.setattr(
        auth_endpoint,
        "validate_otp",
        lambda db, email, plain_otp: {"status": "INVALID", "message": "Incorrect code."}
    )

    response = client.post(
        "/api/v1/auth/forgot-password/verify-otp",
        json={"email": "test@example.com", "otp_code": "000000"}
    )
    assert response.status_code == 400
    assert "Incorrect code." in response.json()["detail"]


def test_forgot_password_verify_valid_otp_mints_token(monkeypatch):
    """Verify that valid OTP returns a signed reset token."""
    from app import crud
    from app.api.v1.endpoints import auth as auth_endpoint

    mock_user = MagicMock()
    mock_user.id = 42
    mock_user.email = "test@example.com"
    mock_user.is_active = True

    monkeypatch.setattr(crud, "get_user_by_email", lambda db, email: mock_user)
    monkeypatch.setattr(
        auth_endpoint,
        "validate_otp",
        lambda db, email, plain_otp: {"status": "SUCCESS", "message": "Verified successfully"}
    )

    response = client.post(
        "/api/v1/auth/forgot-password/verify-otp",
        json={"email": "test@example.com", "otp_code": "123456"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reset_token" in data
    assert data["msg"] == "Verified successfully"

    # Validate that the minted token resolves to user_id=42
    user_id = security.verify_password_reset_token(data["reset_token"])
    assert user_id == 42


def test_forgot_password_reset_invalid_token():
    """Verify that a forged or expired token is rejected with 400."""
    response = client.post(
        "/api/v1/auth/forgot-password/reset",
        json={"reset_token": "forged.fake.token", "new_password": "NewPassword123!"}
    )
    assert response.status_code == 400
    assert "Invalid or expired reset token" in response.json()["detail"]


def test_forgot_password_reset_weak_password(monkeypatch):
    """Verify that weak passwords fail validation."""
    from app import crud

    mock_user = MagicMock()
    mock_user.id = 42
    mock_user.is_active = True
    monkeypatch.setattr(crud, "get_user", lambda db, user_id: mock_user)

    valid_token = security.create_password_reset_token(42)

    # 1. Too short
    res1 = client.post(
        "/api/v1/auth/forgot-password/reset",
        json={"reset_token": valid_token, "new_password": "abc"}
    )
    assert res1.status_code == 400
    assert "at least 6 characters" in res1.json()["detail"]

    # 2. Missing special char
    res2 = client.post(
        "/api/v1/auth/forgot-password/reset",
        json={"reset_token": valid_token, "new_password": "Password123"}
    )
    assert res2.status_code == 400
    assert "special character" in res2.json()["detail"]


def test_forgot_password_reset_success(monkeypatch):
    """Verify that resetting password with valid token and strong password succeeds."""
    from app import crud
    from app.crud import otp as crud_otp

    mock_user = MagicMock()
    mock_user.id = 42
    mock_user.username = "testcommuter"
    mock_user.email = "commuter@example.com"
    mock_user.is_active = True

    updated_password_holder = {}

    monkeypatch.setattr(crud, "get_user", lambda db, user_id: mock_user)
    monkeypatch.setattr(
        crud,
        "update_user_password",
        lambda db, user_id, new_password: updated_password_holder.update({"password": new_password})
    )
    monkeypatch.setattr(crud_otp, "delete_otp", lambda db, email: None)
    monkeypatch.setattr(crud, "create_audit_log", lambda db, audit_in: None)

    valid_token = security.create_password_reset_token(42)

    response = client.post(
        "/api/v1/auth/forgot-password/reset",
        json={"reset_token": valid_token, "new_password": "NewSecretPass123!"}
    )
    assert response.status_code == 200
    assert "Password has been successfully reset" in response.json()["msg"]
    assert updated_password_holder["password"] == "NewSecretPass123!"
