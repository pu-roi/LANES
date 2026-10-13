"""Guarded historical acceptance through the production worker and public APIs.

Only publisher HTTP and time are replay inputs. Original captures, observations,
source approvals, NLP, validation, publication and OSM/NOAH geometry stay intact.
Run separately for each scenario on a fresh private loopback database.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import ExitStack
from datetime import datetime, timedelta
from email.utils import format_datetime
import hashlib
from html import escape
import json
import os
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

import httpx
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select, func
from sqlalchemy.engine import make_url


async def replay(scenario: str, output: Path) -> dict:
    from app.core.config import settings
    from app.core.database import engine, SessionLocal
    from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
    from app.models.news_publication import NewsClaimCase, NewsClaimDecision, NewsClaimEvaluation
    from app.models.report import FloodAvoidanceZone
    from app.services.news_sources import load_news_sources
    from app.services.news_scheduler_service import run_scheduled_news_tick
    from app.services import news_scheduler_service as scheduler
    from app.services.news_claim_auditor import NewsClaimAuditor
    from app.services import local_news_scenario_service as local
    from scripts import replay_september9_news as history
    from scripts import replay_september24_pipeline as september24

    url = make_url(settings.DATABASE_URL)
    if (settings.ENVIRONMENT != "development" or url != engine.url or url.query
            or url.host not in {"localhost", "127.0.0.1", "::1"}
            or not (url.database or "").startswith("lanes_nlp_acceptance_")):
        raise ValueError("Requires an explicit private loopback lanes_nlp_acceptance_ database")
    if output.exists() or inspect(engine).get_table_names():
        raise ValueError("Requires a fresh database and unused output path; preserves previous results")
    if (os.getenv("LANES_NEWS_AUDITOR_PROVIDER") != "source_rules"
            or os.getenv("LANES_NEWS_AUDITOR_MODEL") != "source-rules-v1"):
        raise ValueError("Explicit source_rules/source-rules-v1 configuration required")
    root = Path(__file__).resolve().parents[1]
    migrations = Config(str(root / "alembic.ini"))
    migrations.set_main_option("script_location", str(root / "alembic"))
    command.upgrade(migrations, "head")
    specs = september24.ARTICLES if scenario == "september24" else history.ARTICLES
    captures = september24.CAPTURE_DIR if scenario == "september24" else history.CAPTURE_DIR
    sources = tuple(s for s in load_news_sources() if s.id in {a.source_id for a in specs})
    assert sources and all(s.enabled and s.verified_at for s in sources)
    early_path = history.CAPTURE_DIR / "gma-0955-indexed-body-20261012.txt"
    early_at = datetime.fromisoformat("2026-09-09T09:55:00+08:00")
    times = ([datetime.fromisoformat(s) for s in ["2026-09-24T15:42:00+08:00",
        "2026-09-24T16:59:00+08:00", "2026-09-24T17:29:00+08:00",
        "2026-09-25T04:42:00+08:00", "2026-09-25T05:12:00+08:00"]]
        if scenario == "september24" else [early_at + timedelta(minutes=1+30*i) for i in range(26)])
    output.parent.mkdir(parents=True, exist_ok=True)
    local.SCENARIO_PATH = output.parent / (output.stem + ".scenario.local.json")
    requests: list[dict] = []
    current = times[0]

    def availability(spec) -> datetime:
        return early_at if scenario == "september9" and spec.number == 2 else spec.updated_at or spec.published_at

    def publisher(request: httpx.Request) -> httpx.Response:
        available = tuple(a for a in specs if availability(a) <= current)
        requests.append({"at": current.isoformat(), "method": request.method, "url": str(request.url)})
        feed_source = next((s for s in sources if str(request.url) in s.feed_urls), None)
        if feed_source:
            rss = ET.Element("rss", version="2.0")
            channel = ET.SubElement(rss, "channel")
            for spec in available:
                if spec.source_id != feed_source.id:
                    continue
                item = ET.SubElement(channel, "item")
                for tag, value in (("title", spec.title), ("link", spec.url), ("guid", spec.url),
                                   ("pubDate", format_datetime(spec.published_at))):
                    ET.SubElement(item, tag).text = value
            return httpx.Response(200, content=ET.tostring(rss), headers={"content-type": "application/rss+xml"})
        spec = next((a for a in available if a.url == str(request.url)), None)
        if spec:
            if scenario == "september9" and spec.number == 2 and current < spec.updated_at:
                body = early_path.read_text(encoding="utf-8")
                content = ("<article>" + "".join("<p>" + escape(line) + "</p>" for line in body.splitlines()) + "</article>").encode()
            else:
                content = (captures / f"article-{spec.number}.html").read_bytes()
            return httpx.Response(200, content=content, headers={"content-type": "text/html; charset=utf-8"})
        raise ValueError("Uncaptured publisher request; never substituting flood facts")

    class PublisherHTTP:
        Timeout = httpx.Timeout
        Client = staticmethod(lambda *args, **kwargs: httpx.Client(*args, **kwargs, transport=httpx.MockTransport(publisher)))

    def no_inference(*args, **kwargs):
        raise AssertionError("Historical source-mode acceptance attempted LLM inference")

    from app.main import app
    api = TestClient(app)  # Read requests only; avoids unrelated startup/retention side effects.

    def snapshot() -> dict:
        with SessionLocal() as db:
            case_ids = list(db.scalars(select(NewsClaimCase.id)))
            zone_ids = list(db.scalars(select(FloodAvoidanceZone.id)))
            counts = {model.__tablename__: db.scalar(select(func.count()).select_from(model))
                for model in [NewsArticle, NewsArticleVersion, NewsExtractionRun, NewsClaimEvaluation,
                              NewsClaimDecision, FloodAvoidanceZone]}
            attempts = {r.id: r.attempt_count for r in db.scalars(select(NewsClaimEvaluation).where(NewsClaimEvaluation.status == "completed"))}
            decisions = [{"id":r.id,"case_id":r.case_id,"state":r.public_state,"reason":r.reason_code,
                          "public":r.snapshot.get("public")} for r in db.scalars(select(NewsClaimDecision).order_by(NewsClaimDecision.id))]
        local.SCENARIO_PATH.write_text(json.dumps({"database_identity":local.database_identity(),
            "at":current.isoformat(),"case_ids":case_ids,"zone_ids":zone_ids}),encoding="utf-8")
        zones = api.get("/api/v1/reports/active-zones")
        alerts = api.get("/api/v1/news/alerts?page_size=100")
        assert zones.status_code == alerts.status_code == 200, (zones.status_code, alerts.status_code)
        return {"counts":counts,"completed_attempts":attempts,"decisions":decisions,
                "api_zones":zones.json(),"api_alerts":alerts.json()}

    receipt = {"scenario":scenario,"worker":"run_scheduled_news_tick","database":url.database,
        "limitations":["Reconstructed RSS membership; archived feeds unavailable",
                        "Early September 9 text preserved from publisher index; HTML wrapper reconstructed",
                        "Current source registry and historical read clock; no production writes"],
        "html_sha256":{s.url:hashlib.sha256((captures/f"article-{s.number}.html").read_bytes()).hexdigest() for s in specs},
        "ticks":[],"requests":requests}
    if scenario == "september9":
        receipt["early_body_sha256"] = hashlib.sha256(early_path.read_bytes()).hexdigest()
    with patch.object(NewsClaimAuditor,"_request",no_inference):
        for current in times:
            history.REPLAY_AT = current
            with history.replay_clock(), patch.object(scheduler,"httpx",PublisherHTTP):
                worker = await run_scheduled_news_tick(SessionLocal,limit=200,sources=sources,clock=lambda:current)
            assert worker["outcome"] == "completed", worker
            assert worker["evaluation"]["request_count"] == 0
            state = snapshot()
            receipt["ticks"].append({"at":current.isoformat(),"worker":worker,"snapshot":state})
            output.write_text(json.dumps(receipt,indent=2,default=str),encoding="utf-8")
            print(json.dumps({"at":current.isoformat(),"zones":len(state["api_zones"]),
                              "published":worker["publication"]["published"],"requests":0}),flush=True)
        before = snapshot()
        with history.replay_clock(), patch.object(scheduler,"httpx",PublisherHTTP):
            repeated = await run_scheduled_news_tick(SessionLocal,limit=200,sources=sources,clock=lambda:current)
        after = snapshot()
        assert before["counts"] == after["counts"] and before["completed_attempts"] == after["completed_attempts"]
        receipt["repeat"] = {"counts_unchanged":True,"attempts_unchanged":True,"worker":repeated}
    if scenario == "september24":
        assert all(not t["snapshot"]["api_zones"] for t in receipt["ticks"])
        assert any(d["reason"] == "observation_outside_admission_window" for d in after["decisions"])
    else:
        initial = receipt["ticks"][0]["snapshot"]["api_zones"]
        assert any(n["depth_label"] == "19 inches" and (n["location_qualifier"] or "").startswith("Santo Domingo,")
                   for z in initial for n in z.get("news",[])), "Initial target did not plot"
        assert any(d["public"] and d["public"].get("depth_label") == "10 inches"
                   and (d["public"].get("location_qualifier") or "").startswith("Santo Domingo,")
                   and "16:30:00" in d["public"].get("observed_at", "")
                   for d in after["decisions"]), "Later measured target never published"
        assert not after["api_zones"], "Historical zones did not expire"
    receipt["accepted"] = True
    output.write_text(json.dumps(receipt,indent=2,default=str),encoding="utf-8")
    api.close()
    return {"scenario":scenario,"accepted":True,"ticks":len(times),"zero_llm_requests":True,"output":str(output)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario",required=True,choices=("september24","september9"))
    parser.add_argument("--output",required=True,type=Path)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(replay(args.scenario,args.output)),indent=2))


if __name__ == "__main__":
    main()
