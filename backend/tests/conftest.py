import pytest
from typing import Generator
from fastapi.testclient import TestClient

# We use the main app for the TestClient
from app.main import app

@pytest.fixture(scope="module")
def client() -> Generator:
    """
    A test client for the FastAPI application.
    """
    with TestClient(app) as c:
        yield c
