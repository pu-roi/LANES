"""Replay preserved news through the real credit-free pipeline on a private local DB.

This is an explicitly historical defense demonstration, not a live flood feed.
The normal production collector remains available independently.
"""
import argparse
import asyncio
from dataclasses import replace
from datetime import datetime, timedelta
from email.utils import format_datetime
from html import escape
import json
import os
from pathlib import Path
from unittest.mock import patch

from alembic import command
from alembic.config import Config
import httpx
from sqlalchemy import inspect, select
from sqlalchemy.engine import make_url


async def replay() -> dict:
    from app.core.config import settings
    from app.core.database import engine, SessionLocal
    from app.models.news_publication import NewsClaimCase
    from app.models.report import FloodAvoidanceZone
    from app.schemas.news_extraction import NewsArticleExtractorInput
    from app.services import news_discovery_service as discovery
    from app.services.local_news_scenario_service import SCENARIO_PATH, database_identity
    from app.services.news_scheduler_service import run_scheduled_news_tick
    from app.services.news_sources import load_news_sources

    url = make_url(settings.DATABASE_URL)
    if (settings.ENVIRONMENT != "development" or url != engine.url or url.query
            or url.host not in {"localhost", "127.0.0.1", "::1"}
            or not (url.database or "").startswith("lanes_nlp_demo_")):
        raise ValueError("Historical demonstration requires a private loopback lanes_nlp_demo_ database")
    if not os.environ.get("LANES_NEWS_SCENARIO_FILE"):
        raise ValueError("Set a dedicated LANES_NEWS_SCENARIO_FILE; do not overwrite an existing reconstruction")
    root = Path(__file__).resolve().parents[1]
    if not inspect(engine).get_table_names():
        config = Config(str(root / "alembic.ini"))
        config.set_main_option("script_location", str(root / "alembic"))
        command.upgrade(config, "head")
    capture = json.loads((root / "tests/fixtures/mcp_saved_news.json").read_text(encoding="utf-8"))[0]["article"]
    article = NewsArticleExtractorInput.model_validate(capture)
    now = article.published_at + timedelta(minutes=1)
    source = next(s for s in load_news_sources() if s.id == article.publisher)
    source = replace(source, feed_urls=(source.feed_urls[0],))
    rss = ("<rss><channel><item><title>" + escape(article.title) + "</title><link>" + escape(article.canonical_url)
           + "</link><pubDate>" + format_datetime(article.published_at) + "</pubDate></item></channel></rss>")
    html = "<html><body><article>" + "".join("<p>" + escape(line) + "</p>" for line in article.article_text.splitlines()) + "</article></body></html>"
    def captured_http(request):
        if str(request.url) == source.feed_urls[0]:
            return httpx.Response(200, text=rss, headers={"content-type": "application/rss+xml"})
        if str(request.url) == article.canonical_url:
            return httpx.Response(200, text=html, headers={"content-type": "text/html"})
        raise ValueError("Unexpected publisher URL in historical demonstration")
    class CaptureClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz) if tz else now.replace(tzinfo=None)
    if (os.environ.get("LANES_NEWS_AUDITOR_PROVIDER") != "source_rules"
            or os.environ.get("LANES_NEWS_AUDITOR_MODEL") != "source-rules-v1"):
        raise ValueError("Select source_rules/source-rules-v1 before running the demonstration")
    original_client = httpx.Client
    class CapturedClient(original_client):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs, transport=httpx.MockTransport(captured_http))
    with patch.object(discovery, "datetime", CaptureClock), patch.object(httpx, "Client", CapturedClient):
        first = await run_scheduled_news_tick(SessionLocal, sources=(source,), clock=lambda: now)
        duplicate = await run_scheduled_news_tick(SessionLocal, sources=(source,), clock=lambda: now)
    with SessionLocal() as db:
        cases = list(db.scalars(select(NewsClaimCase.id)))
        zones = list(db.scalars(select(FloodAvoidanceZone.id).where(FloodAvoidanceZone.is_active)))
    scenario = {"database_identity": database_identity(), "at": now.isoformat(), "case_ids": cases,
                "zone_ids": zones, "mode": "historical_nlp_demo", "source_url": article.canonical_url}
    SCENARIO_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCENARIO_PATH.write_text(json.dumps(scenario, indent=2), encoding="utf-8")
    report = {"historical_replay": True, "source_url": article.canonical_url, "clock": now.isoformat(),
              "worker_entrypoint": "run_scheduled_news_tick", "pipeline": first,
              "duplicate_pipeline": duplicate, "active_zone_ids": zones, "llm_requests": first["evaluation"]["request_count"]}
    result_path = SCENARIO_PATH.parent / "result.json"
    if result_path.exists():
        (SCENARIO_PATH.parent / "last-repeat.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    else:
        result_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return {"historical_replay": True, "clock": now.isoformat(), "active_zones": len(zones),
            "source_alerts": first["publication"]["published"], "llm_requests": first["evaluation"]["request_count"],
            "repeat_created_zones": duplicate["footprints"]["activated"], "report": str(SCENARIO_PATH.parent / "result.json")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-replay", action="store_true", required=True,
                        help="Explicitly present captured September 9 evidence using its historical clock")
    parser.parse_args()
    print(json.dumps(asyncio.run(replay()), indent=2))


if __name__ == "__main__":
    main()
