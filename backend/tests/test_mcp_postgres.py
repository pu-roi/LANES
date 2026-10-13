"""Opt-in real PostGIS: migrated fresh local DB, immutable reads and no writes."""
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.services.mcp_review_service import get_bundle, list_news
from app.services.news_claim_auditor import canonical_input_sha256
from tests.test_news_batch_audit import sample


@pytest.fixture(scope="module")
def local_factory():
    value=os.environ.get("LANES_MCP_TEST_DATABASE_URL")
    if not value: pytest.skip("Fresh guarded local MCP PostGIS database required")
    url=make_url(value)
    assert url.host in {"localhost","127.0.0.1","::1"}
    assert (url.database or "").startswith("lanes_mcp_test_")
    engine=create_engine(value)
    assert not inspect(engine).get_table_names(), "Refusing a nonempty test database"
    from app.core.config import settings
    patch=pytest.MonkeyPatch();patch.setattr(settings,"DATABASE_URL",value)
    config=Config(str(Path(__file__).resolve().parents[1]/"alembic.ini"))
    config.set_main_option("script_location",str(Path(__file__).resolve().parents[1]/"alembic"))
    command.upgrade(config,"head")
    with engine.connect() as db: assert db.scalar(text("SELECT postgis_version()"))
    yield sessionmaker(bind=engine,autoflush=False),engine
    patch.undo();engine.dispose()


def test_saved_runs_include_negative_claims_and_preview_reads_are_database_read_only(local_factory):
    factory,engine=local_factory
    candidates,source=sample(2)
    claims=[c.claim.model_dump(mode="json") for c in candidates]
    claims[1]["is_forecast"]=True
    now=datetime.now(timezone.utc)
    with factory() as db,db.begin():
        article=NewsArticle(canonical_url=source.canonical_url,publisher_source_id=source.publisher,
            title=source.title,excerpt="",article_text=source.article_text,content_fingerprint="0"*64)
        db.add(article);db.flush()
        version=NewsArticleVersion(article_id=article.id,input_fingerprint=canonical_input_sha256(source),
                                   input_snapshot=source.model_dump(mode="json"))
        db.add(version);db.flush()
        run=NewsExtractionRun(article_version_id=version.id,pipeline_version="mcp-frozen-v1",mode="rules_only",
            status="completed",attempt_count=1,completed_at=now,result={"claims":claims})
        db.add(run);db.flush();run_id=run.id
    queries=[]
    def observed(connection,cursor,statement,params,context,executemany): queries.append(statement)
    event.listen(engine,"before_cursor_execute",observed)
    try:
        with factory() as db:
            db.execute(text("SET TRANSACTION READ ONLY"))
            page=list_news(db,1,20)
            assert page["items"][0]["claim_count"]==2
            bundle=get_bundle(db,run_id,(0,1))
            assert bundle["original_claims"][1]["is_forecast"] is True
            assert bundle["preview_only"] and not bundle["publication_permitted"]
            db.rollback()
        assert all(s.lstrip().upper().startswith(("SELECT","SET")) for s in queries)
    finally: event.remove(engine,"before_cursor_execute",observed)
    with factory() as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        from sqlalchemy.exc import DBAPIError
        with pytest.raises(DBAPIError):
            db.execute(text("INSERT INTO system_settings (key,value) VALUES ('mcp-forbidden','{}')"))
        db.rollback()
