"""Discover and automatically plot a labeled synthetic article in the local test DB.

RSS/article HTTP and the paid auditor response are fixtures. Extraction, OSM,
NOAH, evidence validation, publication and PostGIS writes use normal services.
The historical September 24 article is never modified. No live network calls.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import json
from pathlib import Path
from uuid import uuid4
from xml.sax.saxutils import escape

import httpx
from sqlalchemy import select

from app.schemas.news_audit import IndependentAuditResult
from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from scripts.seed_local_news_replay import require_local_test_database

SOURCE_ID = "local-september24-simulation"
TITLE = "SIMULATION: September 24 flood scenario in Manila"
PUBLISHER = "SIMULATION ONLY - local flood plotting test"


class FixtureAuditor:
    """Validate a recorded provider answer without contacting a paid provider."""

    def __init__(self) -> None:
        from app.services.news_claim_auditor import AuditorConfig, NewsClaimAuditor
        self.auditor = NewsClaimAuditor(AuditorConfig(provider="openrouter",
            model="fixture/september24-simulation", openrouter_api_key="synthetic-local-only"))

    def policy_identity(self) -> dict:
        return self.auditor.policy_identity()

    async def audit(self, claim: ExtractedClaim, article: NewsArticleExtractorInput,
                    **kwargs) -> IndependentAuditResult:
        from app.services.news_claim_auditor import canonical_claim_sha256
        if (claim.canonical_road != "Quirino Avenue" or claim.canonical_city != "City of Manila"
                or claim.depth_canonical != "knee" or claim.condition != "active"
                or claim.event_time_resolved is None or claim.road_passability != "unknown"):
            raise ValueError("Synthetic audit fixture does not match the extracted claim")
        begin, end = claim.evidence_sentence_offset
        span = {"start": begin, "end": end, "quote": claim.evidence_sentence}
        evidence = {
            "claim_sha256": canonical_claim_sha256(claim),
            "place": {"confirmed": True, "evidence": [span], "raw_place_name": claim.raw_place_name,
                "canonical_city": claim.canonical_city, "canonical_barangay": claim.canonical_barangay},
            "status": {"confirmed": True, "evidence": [span], "classification": "active",
                "contradictory": False, "historical": False},
            "time": {"confirmed": True, "evidence": [span], "kind": "observation",
                "observed_at": claim.event_time_resolved.isoformat()},
            "depth": {"confirmed": True, "evidence": [span], "canonical": "knee",
                "raw": claim.depth_raw, "qualifiers": []},
            "access": {"confirmed": False, "evidence": [], "classification": "unknown"},
        }

        def answer(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"id": "synthetic-local-audit", "choices": [{
                "finish_reason": "stop", "message": {"content": json.dumps(evidence)}}]})

        async with httpx.AsyncClient(transport=httpx.MockTransport(answer)) as client:
            result = await self.auditor.audit(claim, article, client=client)
        if result.outcome != "verified":
            raise ValueError(f"Synthetic answer failed normal evidence validation: {result.reason_code}")
        return result


async def simulate() -> dict:
    from app.core.config import settings
    require_local_test_database(settings.DATABASE_URL)
    from app.core.database import SessionLocal, engine
    require_local_test_database(engine.url.render_as_string(hide_password=False))
    from app.crud.news_publication import latest_decision
    from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
    from app.models.news_publication import NewsClaimSource
    from app.models.report import FloodAvoidanceZone
    from app.models.setting import SystemSetting
    from app.schemas.configuration import OperationalSettings
    from app.services.configuration_service import CONFIG_KEY
    from app.services.news_discovery_service import discover_news
    from app.services.news_pipeline_service import run_news_pipeline
    from app.services.news_sources import NewsSource

    now = datetime.now(timezone.utc)
    observed = (now - timedelta(minutes=3)).astimezone(timezone(timedelta(hours=8)))
    time_label = observed.strftime("%I:%M %p").lstrip("0").lower().replace("am", "a.m.").replace("pm", "p.m.")
    url = f"https://example.org/flood/september24-simulation-{uuid4()}"
    source = NewsSource(SOURCE_ID, PUBLISHER, ("example.org",),
        ("https://example.org/september24-simulation-feed",), now.date(), True)
    body = (f"As of {time_label} today, knee-deep flooding was reported on Quirino Avenue "
        "from Asuncion Street to Camia Street in Manila. "
        "The field team recorded the water level during its inspection.\n"
        "This text is fabricated for a local software simulation.")
    feed = (f"<rss><channel><title>{escape(PUBLISHER)}</title><item><title>{escape(TITLE)}</title>"
        f"<link>{escape(url)}</link><pubDate>{format_datetime(now)}</pubDate></item></channel></rss>").encode()
    calls = []

    def publisher(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if str(request.url) == source.feed_urls[0]:
            return httpx.Response(200, content=feed, headers={"content-type": "application/rss+xml"})
        if str(request.url) != url:
            raise ValueError("Unrecorded synthetic publisher request")
        return httpx.Response(200, text=f"<html><body><article><p>{escape(body)}</p></article></body></html>",
            headers={"content-type": "text/html"})

    # Register only in an existing private configuration, preserving its switches.
    # The approved fixture source is injected into this one-shot pipeline, never
    # added to the production publisher registry or scheduled collector.
    with SessionLocal() as db, db.begin():
        row = db.get(SystemSetting, CONFIG_KEY)
        if row is not None:
            value = dict(row.value)
            config = OperationalSettings.model_validate(value["settings"], context={"persisted_history": True})
            if not config.news_processing_enabled or not config.news_publication_enabled:
                raise ValueError("Enable the normal news pipeline in the private test configuration first")
            if SOURCE_ID not in config.news_source_ids:
                value["settings"] = config.model_copy(update={"news_source_ids": [*config.news_source_ids, SOURCE_ID]}).model_dump(mode="json")
                value["revision"] = value.get("revision", 0) + 1
                row.value = value

    with SessionLocal() as db, httpx.Client(transport=httpx.MockTransport(publisher)) as client:
        discovery = discover_news((source,), client, db)
        if len(discovery.candidates) != 1:
            raise ValueError(f"Synthetic feed admission failed: {discovery.notices}")
        article = db.scalar(select(NewsArticle).where(NewsArticle.canonical_url == url))
        article_id = article.id
        db.commit()
    result = await run_news_pipeline(SessionLocal, limit=200, auditor=FixtureAuditor(),
        sources=(source,), unbound_only=True)
    with SessionLocal() as db, db.begin():
        sources = list(db.scalars(select(NewsClaimSource).join(NewsExtractionRun,
            NewsExtractionRun.id == NewsClaimSource.extraction_run_id).join(NewsArticleVersion,
            NewsArticleVersion.id == NewsExtractionRun.article_version_id)
            .where(NewsArticleVersion.article_id == article_id)))
        decisions = [latest_decision(db, s.case_id) for s in sources]
        active = [d for d in decisions if d is not None and d.public_state == "active_zone" and d.actor_kind == "automatic"]
        for decision in active:
            for zone_id in decision.snapshot["linked_zone_ids"]:
                zone = db.get(FloodAvoidanceZone, zone_id)
                zone.name = "SIMULATION: September 24 - Quirino Avenue"
                zone.admin_notes = "Synthetic local demonstration. Fresh time, bounded span and knee depth are test inputs; auditor response is a fixture."
        output = {"simulation_only": True, "database": "lanes_news_test", "article_id": article_id,
            "source_url": url, "source_title": TITLE, "observation_test_input": observed.isoformat(),
            "changed_from_historical_article": ["synthetic publisher and article", "fresh observation/publication",
                "explicit Asuncion-Camia road span", "hypothetical knee depth; vehicle access unknown"],
            "network": "RSS, article and provider MockTransport; no external calls",
            "assets": "bundled checked OSM and UP NOAH, unchanged", "discovery_request_count": len(calls),
            "pipeline": result,
            "active_decisions": [{"case_id": d.case_id, "actor_kind": d.actor_kind,
                "zone_ids": d.snapshot["linked_zone_ids"], "expires_at": d.expires_at.isoformat()} for d in active]}
        if not active:
            raise ValueError("Simulation did not activate automatically: " + json.dumps(output, default=str))
        return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Private JSON run evidence")
    args = parser.parse_args()
    result = asyncio.run(simulate())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
