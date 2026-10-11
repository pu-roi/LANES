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


@pytest.fixture(scope="session")
def settings_factory():
    import os
    from pathlib import Path
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.engine import make_url
    from sqlalchemy.orm import sessionmaker
    value = os.getenv("LANES_SETTINGS_TEST_DATABASE_URL")
    if not value:
        pytest.skip("Disposable settings database required")
    url = make_url(value)
    assert url.host in ("localhost", "127.0.0.1", "::1") and url.database.startswith("lanes_settings_test_")
    engine = create_engine(url)
    assert not inspect(engine).get_table_names(), "Refusing a nonempty settings database"
    from app.core.config import settings as environment
    patch = pytest.MonkeyPatch()
    patch.setattr(environment, "DATABASE_URL", value)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    command.upgrade(config, "head")
    try:
        yield sessionmaker(bind=engine, expire_on_commit=False)
    finally:
        patch.undo()
        engine.dispose()
