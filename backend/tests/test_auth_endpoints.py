import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app import crud
from app.schemas.user import UserCreate
from app.schemas.profile import ProfileCreate
from app.schemas.address import AddressCreate
from app.schemas.auth import RegistrationRequest
from datetime import datetime, date

client = TestClient(app)

def test_request_signup_otp(db: Session):
    response = client.post(
        "/api/v1/auth/request-signup-otp",
        json={"email": "testotp@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "OTP sent successfully"

def test_register_without_verified_email(db: Session):
    # Try to register without verifying OTP first
    reg_req = {
        "user": {"username": "unverified_user", "email": "unverified@example.com", "password": "Password123!"},
        "profile": {"first_name": "Un", "last_name": "Verified", "birthdate": "1990-01-01"},
        "address": {"province": "Test", "city_municipality": "Test", "barangay": "Test", "country": "Philippines"}
    }
    response = client.post(
        "/api/v1/auth/register",
        json=reg_req
    )
    assert response.status_code == 403
    assert "Email not verified" in response.json()["detail"]
