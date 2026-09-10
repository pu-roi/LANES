from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Create engine with calibrated connection pool settings for GIS workload
db_url = settings.DATABASE_URL
if db_url.startswith("encrypted:"):
    db_url = "postgresql+psycopg://postgres:postgres@localhost:5432/lanes"

engine = create_engine(
    db_url,
    pool_size=20,
    max_overflow=10,
    pool_recycle=1800,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 3},  # Prevent hanging when DB is offline
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy ORM models.
    """
    metadata = MetaData(naming_convention=naming_convention)


def get_db():
    """
    Dependency generator for request-scoped database sessions.
    Closes the session after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
