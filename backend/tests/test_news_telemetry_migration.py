"""Opt-in upgrade/downgrade check on a dedicated disposable PostgreSQL DB."""

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select, func
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


@pytest.mark.skipif(not os.getenv("TEST_NEWS_TELEMETRY_DATABASE_URL"), reason="Dedicated disposable PostgreSQL URL required")
def test_full_upgrade_round_trip_preserves_prior_news_evidence(monkeypatch):
    from app.core.config import settings
    from app.models.news import NewsArticle
    from app.models.news_telemetry import NewsDiscoveryRun, NewsDiscoveryFeedRun, NewsFallbackLookup, NewsFallbackLookupLead
    url = os.environ["TEST_NEWS_TELEMETRY_DATABASE_URL"]
    assert make_url(url).database.startswith("lanes_telemetry_test_"), "Refusing a non-test database"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    engine = create_engine(url)
    try:
        assert "news_articles" not in inspect(engine).get_table_names(), "Expected a fresh disposable DB"
        command.upgrade(config, "head")
        models = [NewsDiscoveryRun, NewsDiscoveryFeedRun, NewsFallbackLookup, NewsFallbackLookupLead]
        for model in models:
            inspector = inspect(engine)
            columns = {column["name"]: column for column in inspector.get_columns(model.__tablename__)}
            assert set(columns) == set(model.__table__.columns.keys())
            for column in model.__table__.columns:
                assert columns[column.name]["nullable"] == column.nullable
            assert {index["name"] for index in inspector.get_indexes(model.__tablename__)} >= {index.name for index in model.__table__.indexes}
            assert len(inspector.get_check_constraints(model.__tablename__)) == len([c for c in model.__table__.constraints if c.__class__.__name__ == "CheckConstraint"])
        with Session(engine) as db:
            db.add(NewsArticle(canonical_url="https://example.org/preserved", publisher_source_id="test",
                title="Preserved evidence", excerpt="", article_text="Original evidence", content_fingerprint="a" * 64,
                review_state="pending"))
            db.commit()
        command.downgrade(config, "f29b6c8d104e")
        assert not any(model.__tablename__ in inspect(engine).get_table_names() for model in models)
        with Session(engine) as db:
            assert db.scalar(select(NewsArticle.article_text)) == "Original evidence"
        command.upgrade(config, "head")
        command.upgrade(config, "head")
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(NewsArticle)) == 1
            assert db.scalar(select(func.count()).select_from(NewsDiscoveryRun)) == 0
    finally:
        engine.dispose()
