"""Replay captured real September 24 coverage through the configured collector.

Article HTML is original publisher data. RSS is reconstructed from published
metadata because an authentic September 24 RSS snapshot is unavailable. Original
facts, dates, source approvals and publication gates are never rewritten.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import ExitStack
from dataclasses import asdict, replace
from datetime import datetime
from email.utils import format_datetime
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

import httpx

from app.schemas.news_audit import IndependentAuditResult
from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from scripts import replay_september9_news as capture_tools
from scripts.replay_september24_news import URL, TITLE, PUBLISHED
from scripts.seed_local_news_replay import require_local_test_database

REPLAY_AT = datetime.fromisoformat("2026-09-25T04:42:00+08:00")
TIMELINE = (
    datetime.fromisoformat("2026-09-24T15:42:00+08:00"),
    datetime.fromisoformat("2026-09-24T16:59:00+08:00"),
    REPLAY_AT,
)
CAPTURE_DIR = Path(__file__).resolve().parents[2] / "data/news-replay/september24-system"
ARTICLES = (
    capture_tools.ArticleSpec(2, "feedspot-01", "https://www.gmanetwork.com/news/weather/content/1003547/thunderstorm-advisory-heavy-to-intense-rains-over-parts-of-metro-manila-6-areas-thursday-2-24-p-m/story/",
        "THUNDERSTORM ADVISORY: Heavy to intense rains over parts of Metro Manila, 6 areas (Thursday, 2:24 p.m.)",
        datetime.fromisoformat("2026-09-24T15:41:00+08:00")),
    capture_tools.ArticleSpec(3, "feedspot-01", "https://www.gmanetwork.com/news/weather/content/1003561/thunderstorm-advisory-metro-manila-laguna-tarlac-9-areas-thursday-4-12-p-m/story/",
        "THUNDERSTORM ADVISORY: Metro Manila, Laguna, Tarlac, 9 areas (Thursday, 4:12 p.m.)",
        datetime.fromisoformat("2026-09-24T16:58:00+08:00")),
    capture_tools.ArticleSpec(4, "daily-tribune", URL, TITLE, PUBLISHED),
)


def sources() -> tuple:
    from app.services.news_sources import load_news_sources
    registry = {s.id: s for s in load_news_sources()}
    gma = registry["feedspot-01"]
    return (replace(gma, feed_urls=(gma.feed_urls[0] + "?lanes_historical_test=2026-09-24",)),
        registry["daily-tribune"])


def feed(specs: tuple) -> bytes:
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "Reconstructed September 24 publisher metadata"
    for spec in specs:
        item = ET.SubElement(channel, "item")
        for tag, value in (("title", spec.title), ("link", spec.url), ("guid", spec.url),
                ("pubDate", format_datetime(spec.published_at))):
            ET.SubElement(item, tag).text = value
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def available_articles(at: datetime) -> tuple:
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("Simulation clock requires a timezone offset")
    return tuple(spec for spec in ARTICLES if spec.published_at <= at)


def client(capture_dir: Path, requests: list[str], *, at: datetime = REPLAY_AT) -> httpx.Client:
    available = available_articles(at)
    feeds = {s.feed_urls[0]: feed(tuple(a for a in available if a.source_id == s.id))
        for s in sources() if s.feed_urls}
    articles = {a.url: capture_dir / f"article-{a.number}.html" for a in available}

    def response(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        requests.append(url)
        if url in feeds:
            return httpx.Response(200, content=feeds[url], headers={"content-type": "application/rss+xml"})
        if url in articles:
            return httpx.Response(200, content=articles[url].read_bytes(), headers={"content-type": "text/html; charset=utf-8"})
        raise RuntimeError("Replay attempted an uncaptured resource")

    return httpx.Client(transport=httpx.MockTransport(response))


async def replay(capture_dir: Path, *, at: datetime = REPLAY_AT, reconstruct: bool = False) -> dict:
    from app.core.config import settings
    require_local_test_database(settings.DATABASE_URL)
    from app.core.database import SessionLocal, engine
    require_local_test_database(engine.url.render_as_string(hide_password=False))
    publication_at = REPLAY_AT if reconstruct else at
    available = available_articles(publication_at)
    from sqlalchemy import func, select
    from app.models.report import FloodAvoidanceZone
    from app.schemas.news_extraction import NewsArticleExtractorInput
    from app.services.news_claim_auditor import NewsClaimAuditor
    from app.services.news_discovery_service import discover_news, extract_captured_news_article
    from app.services.news_estimated_road_service import build_estimated_road_zone
    from app.services.news_evaluation_service import evaluation_policy, preliminary_reason, source_is_approved
    from app.crud.news_publication import NewsPublicationError
    from app.services.news_pipeline_service import run_news_pipeline
    from app.services.news_publication_read_service import browse_public_news_alerts
    from app.crud import report as zone_reader
    from app.services.flood_subsidence_prediction_service import load_research_model, model_status
    from app.services.zone_prediction_service import predict_zone
    from app.models.user import User

    requests, auditor_calls = [], []

    class RecordedAuditor(NewsClaimAuditor):
        async def audit(self, claim: ExtractedClaim, article: NewsArticleExtractorInput,
                        **kwargs) -> IndependentAuditResult:
            auditor_calls.append(article.canonical_url)
            return await super().audit(claim, article, **kwargs)

    auditor = RecordedAuditor()  # Actual configured implementation, no stubbed answers.
    policy = evaluation_policy(auditor, publication_admission_at=publication_at if reconstruct else None)
    with SessionLocal() as db:
        before_ids = set(db.scalars(select(FloodAvoidanceZone.id)))
        before = len(before_ids)
    with ExitStack() as stack:
        # Capture availability and flood observation are separate clocks in a
        # historical reconstruction. Keep the publisher's dates unchanged.
        stack.enter_context(patch.object(capture_tools, "REPLAY_AT", publication_at))
        stack.enter_context(capture_tools.replay_clock())
        with SessionLocal() as db, client(capture_dir, requests, at=publication_at) as publisher:
            discovered = discover_news(sources(), publisher, db)
        pipeline = await run_news_pipeline(SessionLocal, sources=sources(), clock=lambda: at,
            limit=200, unbound_only=True, auditor=auditor,
            publication_admission_at=publication_at if reconstruct else None)
        # Read-only diagnostics include unregistered and rejected articles to
        # explain absence. They do not inject those articles into publication.
        details = []
        for spec in ARTICLES:
            if spec not in available:
                details.append({"url": spec.url, "published_at": spec.published_at,
                    "status": "not_yet_published_at_simulation_clock"})
                continue
            body = (capture_dir / f"article-{spec.number}-body.txt").read_text(encoding="utf-8")
            article = NewsArticleExtractorInput(article_id=-spec.number, canonical_url=spec.url,
                publisher=spec.source_id, title=spec.title, article_text=body, published_at=spec.published_at)
            extraction = await extract_captured_news_article(article)
            claims = []
            for claim in extraction.extraction.claims if extraction.extraction else []:
                if claim.place_type != "street":
                    continue
                try:
                    zone = build_estimated_road_zone(claim)
                    geometry = {"eligible": True, "type": zone.geometry["type"]}
                except NewsPublicationError as error:
                    geometry = {"eligible": False, "reason": error.code}
                claims.append({"road": claim.canonical_road, "condition": claim.condition,
                    "depth": claim.depth_raw, "access": claim.road_passability,
                    "city": claim.canonical_city, "observed_at": claim.event_time_resolved,
                    "admission_reason": preliminary_reason(claim, at, policy),
                    "placement": geometry, "preview_candidates": len(claim.placement_preview.candidates),
                    "modeled_preview_count": sum(bool(c.preview_geometry) for c in claim.placement_preview.candidates)})
            details.append({"url": spec.url, "title": spec.title, "published_at": spec.published_at,
                "registered_approved_source": source_is_approved(article, sources()),
                "body_sha256": hashlib.sha256(body.encode()).hexdigest(), "extraction_error": extraction.error,
                "raw_claim_count": len(extraction.extraction.claims) if extraction.extraction else 0, "roads": claims})
    with SessionLocal() as db:
        after_ids = set(db.scalars(select(FloodAvoidanceZone.id)))
        after = len(after_ids)
        new_ids = sorted(after_ids - before_ids)
        active_ids = [zone.id for zone in zone_reader.get_active_avoidance_zones(db, now=at)]
        alerts = browse_public_news_alerts(db, page=1, page_size=100, now=at, sources=sources())
        predictions = []
        if new_ids:
            staff = db.scalar(select(User).where(User.username == "admin", User.is_active.is_(True)))
            if staff is None:
                raise RuntimeError("Private simulation requires its existing staff account for prediction reads")
            predictions = [predict_zone(db, zone_id, staff, now=at).model_dump(mode="json") for zone_id in new_ids]
    model = model_status(*load_research_model()).model_dump(mode="json")
    return {"simulated_at": at, "database": "lanes_news_test", "production_writes": False,
        "articles": "captured original publisher HTML/body; no invented flood facts",
        "feeds": "reconstructed titles/URLs/publication metadata; authentic archived RSS unavailable; no descriptions assumed",
        "source_registry": "current verified publisher registry; historical feed membership unverified",
        "replay_mode": "historical_reconstruction" if reconstruct else "publication_timeline",
        "publication_admission_at": publication_at,
        "requests": requests, "probes": [asdict(p) for p in discovered.probes],
        "notices": [asdict(n) for n in discovered.notices], "collected_candidates": len(discovered.candidates),
        "pipeline": pipeline, "provider_calls": auditor_calls, "zone_count_before": before,
        "zone_count_after": after, "new_zone_count": after - before, "article_diagnostics": details,
        "map": {"new_zone_ids": new_ids, "active_zone_ids_at_simulation_clock": active_ids,
            "public_news_alerts": alerts.total},
        "subsidence": {"model": model, "new_zone_predictions": predictions,
            "stage": "executed_for_new_zones" if new_ids else "not_reached_no_new_zone",
            "current_news_geometry_policy": "verified_incident_footprint_or_staff_reviewed_footprint",
            "estimated_news_corridors_accepted_by_zone_adapter": False}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="Fetch original publisher HTML with existing bounded service")
    parser.add_argument("--capture-dir", type=Path, default=CAPTURE_DIR)
    parser.add_argument("--at", type=datetime.fromisoformat, default=REPLAY_AT,
        help="Timezone-aware simulated present; future articles are unavailable")
    parser.add_argument("--timeline", action="store_true",
        help="Run September 24 afternoon checkpoints and first Tribune publication availability")
    parser.add_argument("--reconstruct", action="store_true",
        help="Private historical reconstruction at --at using later captured evidence; preserve publication dates")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from app.core.config import settings
    require_local_test_database(settings.DATABASE_URL)
    if args.capture:
        with patch.object(capture_tools, "ARTICLES", ARTICLES), patch.object(capture_tools, "replay_sources", sources):
            capture_tools.capture_articles(args.capture_dir)
    try:
        available_articles(args.at)
    except ValueError as exc:
        parser.error(str(exc))
    async def run() -> dict:
        if args.timeline:
            return {"simulation_timeline": [await replay(args.capture_dir, at=at) for at in TIMELINE]}
        return await replay(args.capture_dir, at=args.at, reconstruct=args.reconstruct)
    result = asyncio.run(run())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
