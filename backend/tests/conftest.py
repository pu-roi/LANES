import pytest
from typing import Generator
from fastapi.testclient import TestClient
from app.core.database import SessionLocal
from app.main import app

@pytest.fixture(scope="module")
def client() -> Generator:
    """
    A test client for the FastAPI application.
    """
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def db_session() -> Generator:
    """
    Yields an active database session for tests.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
