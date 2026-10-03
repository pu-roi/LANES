"""Opt-in checks against a migrated disposable PostgreSQL/PostGIS database.

Set LANES_NEWS_TEST_DATABASE_URL to a database named lanes_p3_verify_*.
The fixture refuses every other database and cleans only its news test rows.
"""
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest
from sqlalchemy import create_engine, func, inspect, select, text, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import sessionmaker

from app.crud.news_processing import claim_due_run, enqueue_article, finish_owned_run
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.services.news_processing_service import process_saved_news

NOW = datetime(2026, 10, 2, 3, tzinfo=timezone.utc)


@pytest.fixture
def postgres_queue():
    url = os.environ.get("LANES_NEWS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Disposable PostgreSQL connection not configured")
    engine = create_engine(url)
    with engine.connect() as connection:
        database = connection.scalar(text("SELECT current_database()"))
        assert database.startswith("lanes_p3_verify_"), "Refusing a non-disposable database"
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "c5a7e9d2104f"
        assert connection.scalar(text("SELECT postgis_version()"))
    tables = inspect(engine).get_table_names()
    assert "news_article_versions" in tables and "news_extraction_runs" in tables

    def clean():
        with engine.begin() as connection:
            connection.execute(text("TRUNCATE news_fallback_lookup_leads, news_fallback_lookups, "
                                    "news_discovery_feed_runs, news_discovery_runs, news_extraction_runs, news_article_versions, "
                                    "news_article_feed_entries, news_articles RESTART IDENTITY"))

    clean()
    try:
        yield sessionmaker(bind=engine)
    finally:
        clean()
        engine.dispose()


def seed(factory, count=1):
    with factory() as db, db.begin():
        for index in range(count):
            row = NewsArticle(canonical_url=f"https://example.org/flood/{index}", publisher_source_id="fixture",
                              title="Baha sa Pasig", excerpt="", published_at=NOW,
                              article_text="As of 10 AM, abot-tuhod ang baha sa Maybunga, Pasig City.",
                              content_fingerprint="0" * 64, review_state="pending")
            db.add(row)
            enqueue_article(db, row)


def test_database_enforces_immutable_versions_and_run_constraints(postgres_queue):
    seed(postgres_queue)
    with postgres_queue() as db:
        version_id = db.scalar(select(NewsArticleVersion.id))
        run_id = db.scalar(select(NewsExtractionRun.id))
    with pytest.raises(DBAPIError, match="immutable"):
        with postgres_queue() as db, db.begin():
            db.execute(update(NewsArticleVersion).where(NewsArticleVersion.id == version_id).values(
                input_snapshot={"replaced": True}))
    with pytest.raises(IntegrityError):
        with postgres_queue() as db, db.begin():
            db.execute(update(NewsExtractionRun).where(NewsExtractionRun.id == run_id).values(attempt_count=6))
    with pytest.raises(IntegrityError):
        with postgres_queue() as db, db.begin():
            db.execute(update(NewsExtractionRun).where(NewsExtractionRun.id == run_id).values(status="completed"))


def test_skip_locked_claims_and_reclaimed_lease_ownership(postgres_queue):
    seed(postgres_queue, count=2)
    with postgres_queue() as first, first.begin():
        claim1 = claim_due_run(first, NOW)
        with postgres_queue() as second, second.begin():
            claim2 = claim_due_run(second, NOW)
            assert claim1.run_id != claim2.run_id
            with postgres_queue() as third, third.begin():
                assert claim_due_run(third, NOW) is None
    expired = NOW + timedelta(minutes=6)
    with postgres_queue() as db, db.begin():
        reclaimed = claim_due_run(db, expired, article_id=claim1.article_id)
        assert reclaimed.run_id == claim1.run_id and reclaimed.attempt_count == 2
        assert reclaimed.lease_token != claim1.lease_token
        assert not finish_owned_run(db, claim1, expired, result={"stale": True})
        assert finish_owned_run(db, reclaimed, expired, result={"claims": []})


def test_concurrent_enqueue_reuses_one_version_and_run(postgres_queue):
    seed(postgres_queue)
    with postgres_queue() as db, db.begin():
        row = db.scalar(select(NewsArticle))
        row.article_text += " Updated flood coverage."
        article_id = row.id
    barrier = Barrier(2)

    def enqueue():
        with postgres_queue() as db, db.begin():
            row = db.get(NewsArticle, article_id)
            barrier.wait(timeout=10)
            return enqueue_article(db, row)

    with ThreadPoolExecutor(max_workers=2) as workers:
        first = workers.submit(enqueue)
        second = workers.submit(enqueue)
        assert first.result(timeout=30) == second.result(timeout=30)
    with postgres_queue() as db:
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion)) == 2
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun)) == 2


def test_real_rules_output_survives_new_session_and_repeat_delivery(postgres_queue):
    seed(postgres_queue)
    first = asyncio.run(process_saved_news(postgres_queue, clock=lambda: NOW))
    assert first.completed == 1 and first.failed == 0
    restarted = sessionmaker(bind=postgres_queue.kw["bind"])
    repeated = asyncio.run(process_saved_news(restarted, clock=lambda: NOW))
    assert repeated.runs == []
    with restarted() as db:
        run = db.scalar(select(NewsExtractionRun))
        assert any(claim["depth_canonical"] == "knee" for claim in run.result["claims"])
        assert db.scalar(select(NewsArticle)).review_state == "pending"
