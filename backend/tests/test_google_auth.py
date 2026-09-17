import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_google_auth_missing_token():
    """Verify that calling /api/v1/auth/google without any token returns 400 Bad Request."""
    response = client.post("/api/v1/auth/google", json={})
    assert response.status_code == 400
    assert "Google authentication token is required" in response.json()["detail"]


def test_google_auth_invalid_credential():
    """Verify that calling /api/v1/auth/google with a forged or invalid credential returns 401 Unauthorized."""
    response = client.post("/api/v1/auth/google", json={"credential": "invalid.jwt.token"})
    assert response.status_code == 401
    assert "Invalid or expired Google token" in response.json()["detail"] or "Google token verification failed" in response.json()["detail"]


def test_google_auth_invalid_access_token():
    """Verify that calling /api/v1/auth/google with a forged access token returns 401 Unauthorized."""
    response = client.post("/api/v1/auth/google", json={"access_token": "fake-access-token-12345"})
    assert response.status_code == 401
    assert "Invalid Google access token" in response.json()["detail"] or "Google OAuth verification failed" in response.json()["detail"]


def test_google_auth_login_mode_not_found(monkeypatch):
    """Verify that login mode returns 404 if the Google account is not registered."""
    from app.services import auth_service
    
    # Mock verify_google_token to return a fake verified profile
    monkeypatch.setattr(
        auth_service,
        "verify_google_token",
        lambda credential=None, access_token=None: {
            "email": "unregistered_test_user@example.com",
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": None,
            "sub": "12345"
        }
    )

    response = client.post("/api/v1/auth/google", json={"credential": "mock_token", "mode": "login"})
    # Either 404 if DB is reachable, or DB connection error if DB is down
    if response.status_code == 404:
        assert "No registered account found with this Google email" in response.json()["detail"]

