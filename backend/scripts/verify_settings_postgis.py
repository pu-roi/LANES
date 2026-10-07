"""Verify settings and news lifecycle in fresh local PostGIS databases.

Uses the existing local development container without changing its application
database or volume. Generated databases are removed after the test subprocess.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


def main() -> int:
    info = json.loads(subprocess.check_output(["docker", "inspect", "lanes_postgis_db"]))[0]
    environment = dict(item.split("=", 1) for item in info["Config"]["Env"] if "=" in item)
    ports = info["NetworkSettings"]["Ports"]["5432/tcp"]
    url = URL.create("postgresql+psycopg", username=environment["POSTGRES_USER"],
        password=environment["POSTGRES_PASSWORD"], host="127.0.0.1", port=int(ports[0]["HostPort"]),
        database=environment.get("POSTGRES_DB", environment["POSTGRES_USER"]))
    engine = create_engine(url, isolation_level="AUTOCOMMIT")
    names = []
    child = os.environ.copy()
    try:
        for key, prefix in (("LANES_SETTINGS_TEST_DATABASE_URL", "lanes_settings_test_"),
                ("LANES_NEWS_PUBLICATION_LIFECYCLE_TEST_DATABASE_URL", "lanes_publication_lifecycle_test_")):
            name = prefix + uuid4().hex[:12]
            with engine.connect() as connection:
                connection.execute(text("CREATE DATABASE " + name))
            names.append(name)
            child[key] = url.set(database=name).render_as_string(hide_password=False)
        tests = sys.argv[1:] or ["tests/test_operational_settings_postgres.py",
            "tests/test_news_publication_lifecycle_postgres.py", "tests/test_flood_zone_growth.py"]
        return subprocess.run([sys.executable, "-m", "pytest", *tests, "-q", "--tb=short"],
            cwd=Path(__file__).resolve().parents[1], env=child).returncode
    finally:
        for name in names:
            assert url.host == "127.0.0.1" and name.startswith(("lanes_settings_test_", "lanes_publication_lifecycle_test_"))
            with engine.connect() as connection:
                connection.execute(text("DROP DATABASE " + name + " WITH (FORCE)"))
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
