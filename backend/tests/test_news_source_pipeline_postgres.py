"""Normal collector-to-zone pipeline on fresh local PostGIS and bundled real assets.

Historical capture replay uses its source clock. It never reaches shared data or
claims historical RSS membership is proven. Only publisher HTTP is substituted.
"""
import json
import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.models.news import NewsArticle, NewsExtractionRun
from app.models.news_publication import NewsClaimDecision, NewsClaimEvaluation
from app.models.report import FloodAvoidanceZone
from app.services import news_discovery_service as discovery
from app.services.news_claim_auditor import NewsClaimAuditor
from app.services.news_scheduler_service import run_scheduled_news_tick
from app.services.news_sources import load_news_sources


@pytest.fixture(scope="module")
def local_factory():
    value = os.getenv("LANES_NLP_TEST_DATABASE_URL")
    if not value:
        pytest.skip("Fresh local NLP PostGIS database required")
    url = make_url(value)
    assert url.host in {"localhost", "127.0.0.1", "::1"}
    assert (url.database or "").startswith("lanes_publication_lifecycle_test_nlp_")
    assert not url.query
    engine = create_engine(value)
    assert not inspect(engine).get_table_names(), "Refusing a nonempty database"
    from app.core.config import settings
    patch = pytest.MonkeyPatch()
    patch.setattr(settings, "DATABASE_URL", value)
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    command.upgrade(config, "head")
    with engine.connect() as db:
        assert db.scalar(text("SELECT postgis_version()"))
    try:
        yield sessionmaker(bind=engine)
    finally:
        engine.dispose()
        patch.undo()


@pytest.mark.asyncio
async def test_collector_extraction_source_checks_zone_activation_duplicate_and_expiry(local_factory, monkeypatch):
    captured = json.loads((Path(__file__).parent / "fixtures/mcp_saved_news.json").read_text(encoding="utf-8"))[0]["article"]
    now = datetime.fromisoformat(captured["published_at"].replace("Z", "+00:00")) + timedelta(minutes=1)
    source = next(s for s in load_news_sources() if s.id == captured["publisher"])
    source = replace(source, feed_urls=(source.feed_urls[0],))
    url = captured["canonical_url"]
    rss = ("<rss><channel><item><title>" + escape(captured["title"]) + "</title><link>" + escape(url)
           + "</link><pubDate>" + format_datetime(now - timedelta(minutes=1)) + "</pubDate></item></channel></rss>")
    html = "<html><body><article>" + "".join("<p>" + escape(line) + "</p>" for line in captured["article_text"].splitlines()) + "</article></body></html>"
    calls = []
    def publisher(request):
        calls.append(str(request.url))
        if str(request.url) == source.feed_urls[0]:
            return httpx.Response(200, text=rss, headers={"content-type": "application/rss+xml"})
        if str(request.url) == url:
            return httpx.Response(200, text=html, headers={"content-type": "text/html"})
        pytest.fail("Unexpected publisher request: " + str(request.url))
    class CaptureClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz) if tz else now.replace(tzinfo=None)
    monkeypatch.setattr(discovery, "datetime", CaptureClock)
    def forbidden(*args, **kwargs):
        pytest.fail("Credit-free pipeline attempted provider/quota inference")
    monkeypatch.setattr(NewsClaimAuditor, "_request", forbidden)
    from app.services import news_evaluation_service as evaluations
    monkeypatch.setattr(evaluations, "check_quota", forbidden)
    monkeypatch.setattr(evaluations, "record_availability", forbidden)
    monkeypatch.setenv("LANES_NEWS_AUDITOR_PROVIDER", "source_rules")
    monkeypatch.setenv("LANES_NEWS_AUDITOR_MODEL", "source-rules-v1")
    original_client = httpx.Client
    class CapturedClient(original_client):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs, transport=httpx.MockTransport(publisher))
    monkeypatch.setattr(httpx, "Client", CapturedClient)
    first = await run_scheduled_news_tick(local_factory, sources=(source,), clock=lambda: now)
    assert len(calls) == 2
    with local_factory() as db:
        zones = db.scalar(select(func.count()).select_from(FloodAvoidanceZone).where(FloodAvoidanceZone.is_active))
        articles = db.scalar(select(func.count()).select_from(NewsArticle))
        decisions = db.scalar(select(func.count()).select_from(NewsClaimDecision))
        audits = list(db.scalars(select(NewsClaimEvaluation.result)))
        mapped = list(db.scalars(select(NewsClaimDecision.snapshot).where(NewsClaimDecision.public_state == "active_zone")))
    print(json.dumps({"historical_clock": now.isoformat(), "articles": articles, "active_zones": zones,
                      "pipeline": first}, default=str))
    assert first["extraction"]["completed"] == 1
    assert first["evaluation"]["request_count"] == 0
    assert first["publication"]["published"] > 0
    assert zones > 0 and first["footprints"]["estimated_activated"] > 0
    assert all(not row.get("audit") or row["audit"]["provider"] == "source_rules" for row in audits)
    assert any((s["public"]["location_qualifier"] or "").startswith("Santo Domingo,")
               and s["public"]["depth_label"] == "19 inches" for s in mapped)
    assert all("\u25b6" not in s["public"]["evidence_excerpt"] and " … " not in s["public"]["evidence_excerpt"]
               for s in mapped)
    again = await run_scheduled_news_tick(local_factory, sources=(source,), clock=lambda: now)
    with local_factory() as db:
        assert db.scalar(select(func.count()).select_from(FloodAvoidanceZone)) == zones
        assert db.scalar(select(func.count()).select_from(NewsClaimDecision)) == decisions
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun)) == 1
    assert again["evaluation"]["request_count"] == 0
    ended = await run_scheduled_news_tick(local_factory, sources=(source,),
                                         clock=lambda: now + timedelta(hours=13))
    with local_factory() as db:
        assert db.scalar(select(func.count()).select_from(FloodAvoidanceZone).where(FloodAvoidanceZone.is_active)) == 0
    assert ended["publication"]["expired"] > 0
