"""Explicit local reconstruction of a captured article in the connected database.

Uses collector, rules extraction, real auditor, publication and footprint worker.
No guessed decisions, copied zones, source retiming or label substitution.
Run only after authorizing this specific connected-database simulation.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import ExitStack
from dataclasses import asdict, replace
from datetime import datetime
import hashlib
from html import escape
import json
from pathlib import Path
from unittest.mock import patch

import httpx
from sqlalchemy import select

from app.core.database import SessionLocal
from app.crud.news_processing import enqueue_article
from app.crud.news_publication import NewsPublicationError
from app.models.news import NewsArticle
from app.models.news_publication import NewsClaimEvaluation, NewsClaimSource, NewsClaimZoneLink
from app.services.local_news_scenario_service import connected_reconstruction, database_identity, SCENARIO_PATH
from app.services.news_claim_auditor import NewsClaimAuditor
from app.services.news_discovery_service import discover_news
from app.services.news_evaluation_service import evaluate_news_claims, evaluation_policy, seed_claim_evaluations
from app.services.news_footprint_worker_service import process_news_footprints
from app.services.news_processing_service import process_saved_news
from app.services.news_publication_service import publish_completed_evaluation
from app.services.configuration_service import read_configuration, selected_news_sources
from scripts import replay_september9_news as capture_tools
from scripts.replay_september24_pipeline import CAPTURE_DIR, REPLAY_AT
from scripts.replay_september24_news import URL


def scenario_inputs(scenario: str) -> tuple:
    if scenario == "september24":
        return URL, REPLAY_AT, datetime.fromisoformat("2026-09-24T16:39:00+08:00"), CAPTURE_DIR / "article-4.html", None, "daily-tribune"
    if scenario == "september9":
        spec = capture_tools.ARTICLES[1]
        return spec.url, datetime.fromisoformat("2026-09-09T09:56:00+08:00"), datetime.fromisoformat("2026-09-09T09:56:00+08:00"), capture_tools.CAPTURE_DIR / "gma-0955-indexed-body-20261012.txt", spec, spec.source_id
    raise ValueError("Unknown captured scenario")


def reconstruction_client(scenario: str, selected: tuple, requests: list[str]) -> httpx.Client:
    url, _, _, path, spec, _ = scenario_inputs(scenario)
    if spec is None:
        from scripts.replay_september24_pipeline import ARTICLES
        spec = next(item for item in ARTICLES if item.url == url)
    captured = path.read_bytes()
    # The preserved publisher index text has no archived HTML. This is the same
    # escaped wrapper used by the existing timeline replay; facts stay intact.
    content = captured if scenario == "september24" else ("<article>" + "".join(
        "<p>" + escape(line) + "</p>" for line in captured.decode("utf-8").splitlines()) + "</article>").encode()
    from scripts.replay_september24_pipeline import feed
    render_feed = feed if scenario == "september24" else capture_tools.reconstructed_feed
    feeds = {feed_url: render_feed((spec,)) for source in selected for feed_url in source.feed_urls}
    def response(request: httpx.Request) -> httpx.Response:
        address = str(request.url)
        requests.append(address)
        if address in feeds:
            return httpx.Response(200, content=feeds[address], headers={"content-type": "application/rss+xml"})
        if address == url:
            return httpx.Response(200, content=content, headers={"content-type": "text/html; charset=utf-8"})
        raise RuntimeError("Reconstruction attempted an uncaptured resource")
    return httpx.Client(transport=httpx.MockTransport(response))


def require_connected_target(expected_database: str) -> None:
    from app.core.config import settings
    from app.core.database import engine
    from sqlalchemy.engine import make_url
    configured = make_url(settings.DATABASE_URL)
    if not expected_database or configured != engine.url or configured.database != expected_database:
        raise ValueError("Explicit database confirmation must match the configured and bound database")
    if settings.ENVIRONMENT.lower() != "development":
        raise ValueError("Connected reconstruction requires the existing development environment")
    identity = NewsClaimAuditor().policy_identity()
    if identity.get("provider") != "source_rules" or not identity.get("configured"):
        raise ValueError("Connected reconstruction requires configured credit-free source_rules")
    if SCENARIO_PATH.exists():
        previous = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
        if previous.get("database_identity") != database_identity():
            raise ValueError("Existing scenario file belongs to another database")
    with SessionLocal() as db:
        config = read_configuration(db)
        if config.automatic_expiry_enabled:
            raise ValueError("Disable automatic expiry in System Settings before the presentation reconstruction")
        if not config.news_collection_enabled or not config.news_processing_enabled or not config.news_publication_enabled:
            raise ValueError("Configured news collection/processing/publication is paused")


def retain_scenarios(result: dict) -> None:
    previous = json.loads(SCENARIO_PATH.read_text(encoding="utf-8")) if SCENARIO_PATH.exists() else {}
    if previous and previous.get("database_identity") != database_identity():
        raise ValueError("Existing scenario file belongs to another database")
    retained = {"database_identity": database_identity(),
        "at": max(datetime.fromisoformat(result["at"]), datetime.fromisoformat(previous.get("at", result["at"]))).isoformat(),
        "case_ids": sorted(set(previous.get("case_ids", []) + result["case_ids"])),
        "zone_ids": sorted(set(previous.get("zone_ids", []) + result["zone_ids"])),
        "scenarios": {**previous.get("scenarios", {}), result["scenario"]: {
            key: result[key] for key in ("at", "source_url", "article_id", "run_id", "case_ids", "zone_ids")}}}
    SCENARIO_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = SCENARIO_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(retained, indent=2), encoding="utf-8")
    temporary.replace(SCENARIO_PATH)


async def reconstruct(at: datetime, output: Path, *, scenario: str, expected_database: str) -> dict:
    require_connected_target(expected_database)
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("Reconstruction time requires a timezone offset")
    url, admission_at, _, capture_path, _, source_id = scenario_inputs(scenario)
    if at.date() != scenario_inputs(scenario)[2].date():
        raise ValueError("Reconstruction clock must remain on the historical event date")
    capture_checksum = hashlib.sha256(capture_path.read_bytes()).hexdigest()
    requests = []
    from app.services.news_sources import load_news_sources
    with SessionLocal() as db:
        selected = selected_news_sources(db, tuple(source for source in load_news_sources() if source.id == source_id))
    if not selected:
        raise RuntimeError("Configured captured publisher is paused or unverified")
    # Keep reconstructed feed checkpoints separate from normal live collection.
    selected = tuple(replace(source, feed_urls=(source.feed_urls[0] + "?lanes_connected_reconstruction=" + scenario,)) for source in selected)
    with connected_reconstruction(url, admission_at), ExitStack() as stack:
        stack.enter_context(patch.object(capture_tools, "REPLAY_AT", admission_at))
        stack.enter_context(capture_tools.replay_clock())
        with SessionLocal() as db, reconstruction_client(scenario, selected, requests) as publisher:
            discovered = discover_news(selected, publisher, db)
        with SessionLocal() as db, db.begin():
            article = db.scalar(select(NewsArticle).where(NewsArticle.canonical_url == url))
            if article is None:
                raise RuntimeError("Original article was not captured")
            article_id = article.id
            run_id = enqueue_article(db, article)
            config = read_configuration(db)
            selected = selected_news_sources(db, selected)
            if not config.news_processing_enabled or not config.news_publication_enabled or not selected:
                raise RuntimeError("Configured news processing/publication/source is paused")
        if run_id is None:
            raise RuntimeError("Article cannot enter the existing extraction workflow")
        extracted = await process_saved_news(SessionLocal, article_id=article_id, clock=lambda: at,
            obey_configuration=True, sources=selected)
        # Historical operator runs allow the configured provider to finish;
        # scheduled collection keeps its normal bounded timeout.
        auditor = NewsClaimAuditor(timeout_seconds=60)
        policy = evaluation_policy(auditor, config, publication_admission_at=admission_at)
        seeded = seed_claim_evaluations(SessionLocal, policy, run_id=run_id, now=at,
            sources=selected, obey_configuration=True)
        evaluated = await evaluate_news_claims(SessionLocal, run_id=run_id, policy=policy, auditor=auditor,
            clock=lambda: at, sources=selected, obey_configuration=True)
        with SessionLocal() as db:
            ids = list(db.scalars(select(NewsClaimEvaluation.id).join(NewsClaimSource,
                NewsClaimSource.id == NewsClaimEvaluation.claim_source_id).where(
                NewsClaimSource.extraction_run_id == run_id, NewsClaimEvaluation.policy_fingerprint == policy.fingerprint,
                NewsClaimEvaluation.status.in_(("completed", "failed"))).order_by(NewsClaimEvaluation.id)))
        published, skipped = [], []
        for identity in ids:
            try:
                with SessionLocal() as db, db.begin():
                    decision = publish_completed_evaluation(db, identity, policy=policy, now=at, sources=selected)
                    published.append({"case_id": decision.case_id, "decision_id": decision.id, "state": decision.public_state})
            except NewsPublicationError as error:
                skipped.append({"evaluation_id": identity, "reason_code": error.code})
        footprints = process_news_footprints(SessionLocal, policy=policy, clock=lambda: at, sources=selected)
        with SessionLocal() as db:
            from app.models.news_publication import NewsClaimDecision
            links = list(db.execute(select(NewsClaimZoneLink.zone_id, NewsClaimDecision.case_id)
                .join(NewsClaimDecision, NewsClaimDecision.id == NewsClaimZoneLink.decision_id)
                .join(NewsClaimEvaluation, NewsClaimEvaluation.id == NewsClaimDecision.evaluation_id)
                .join(NewsClaimSource, NewsClaimSource.id == NewsClaimEvaluation.claim_source_id)
                .where(NewsClaimSource.extraction_run_id == run_id,
                    NewsClaimDecision.snapshot["policy_fingerprint"].astext == policy.fingerprint)))
        result = {"scenario": scenario, "database_identity": database_identity(),
            "capture_sha256": capture_checksum, "feed_origin": "Reconstructed RSS from original publisher metadata; archived RSS unavailable",
            "body_origin": "Original captured publisher HTML" if scenario == "september24" else "Preserved publisher index text in escaped HTML wrapper",
            "at": at.isoformat(), "publication_admission_at": admission_at.isoformat(), "source_url": url,
            "article_id": article_id, "run_id": run_id, "requests": requests,
            "collector_candidates": len(discovered.candidates), "extraction": asdict(extracted),
            "seed": asdict(seeded), "evaluation": asdict(evaluated), "publication": published,
            "publication_skipped": skipped, "footprints": asdict(footprints),
            "zone_ids": sorted(set(row[0] for row in links)), "case_ids": sorted(set(row[1] for row in links))}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        if result["zone_ids"]:
            retain_scenarios(result)
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorize-connected-reconstruction", action="store_true", required=True)
    parser.add_argument("--confirm-database", required=True, help="Exact existing database name; checked before writes")
    parser.add_argument("--scenario", choices=("september24", "september9"), required=True)
    parser.add_argument("--at", type=datetime.fromisoformat)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = asyncio.run(reconstruct(args.at or scenario_inputs(args.scenario)[2], args.output,
        scenario=args.scenario, expected_database=args.confirm_database))
    print(json.dumps(result, default=str))
    if not result["zone_ids"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
