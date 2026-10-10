"""Operator-owned local scenario clocks; never rewrite source facts or expiry.

Only development reads accept the ignored, database-bound scenario file.
Connected reconstruction admission is an explicit CLI context, unavailable to
ordinary HTTP publication and restored when the operator command exits.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterator

from sqlalchemy import case, literal
from sqlalchemy.sql.elements import ColumnElement

SCENARIO_PATH = Path(__file__).resolve().parents[3] / "data/news-replay/connected-scenario.local.json"
_admission: ContextVar[tuple[str, str, datetime] | None] = ContextVar("connected_news_admission", default=None)


def database_identity() -> str:
    from app.core.database import engine
    # No passwords or connection strings are persisted in the scenario file.
    url = engine.url
    return sha256(json.dumps([url.drivername, url.host, url.port, url.database, url.username], separators=(",", ":")).encode()).hexdigest()


def _development() -> bool:
    from app.core.config import settings
    return settings.ENVIRONMENT.lower() == "development"


def read_scenario() -> dict[str, Any] | None:
    if not _development() or not SCENARIO_PATH.exists():
        return None
    data = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    if data.get("database_identity") != database_identity():
        return None
    clock = datetime.fromisoformat(data["at"])
    if clock.tzinfo is None or not all(isinstance(value, int) and value > 0
            for key in ("case_ids", "zone_ids") for value in data[key]):
        raise ValueError("Invalid local news scenario configuration")
    return {**data, "clock": clock}


def scoped_clock(identity: int, kind: str, default: datetime) -> datetime:
    scenario = read_scenario()
    return scenario["clock"] if scenario and identity in scenario[f"{kind}_ids"] else default


def sql_clock(identity_column: ColumnElement[Any], kind: str,
              default: ColumnElement[Any] | datetime) -> ColumnElement[Any] | datetime:
    scenario = read_scenario()
    if scenario and scenario[f"{kind}_ids"]:
        return case((identity_column.in_(scenario[f"{kind}_ids"]), literal(scenario["clock"])), else_=default)
    return default


@contextmanager
def connected_reconstruction(source_url: str, publication_at: datetime) -> Iterator[None]:
    from sqlalchemy.engine import make_url
    from app.core.config import settings
    from app.core.database import engine
    if (not _development() or make_url(settings.DATABASE_URL) != engine.url
            or publication_at.tzinfo is None or not source_url.startswith("https://")):
        raise ValueError("Connected reconstruction requires an explicit development database and source")
    token = _admission.set((database_identity(), source_url, publication_at))
    try:
        yield
    finally:
        _admission.reset(token)


def admits_connected_reconstruction(publication_at: datetime) -> bool:
    scope = _admission.get()
    return bool(_development() and scope and scope[0] == database_identity() and scope[2] == publication_at)


def admitted_source_matches(source_url: str) -> bool:
    scope = _admission.get()
    return scope is None or (scope[0] == database_identity() and scope[1] == source_url)
