"""Explicit local reconstruction of a captured article in the connected database.

Uses collector, rules extraction, real auditor, publication and footprint worker.
No guessed decisions, copied zones, source retiming or label substitution.
Run only after authorizing this specific connected-database simulation.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import ExitStack
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
from unittest.mock import patch

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
from scripts.replay_september24_pipeline import CAPTURE_DIR, REPLAY_AT, client, sources
from scripts.replay_september24_news import URL


async def reconstruct(at: datetime, output: Path) -> dict:
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("Reconstruction time requires a timezone offset")
    requests = []
    selected = tuple(source for source in sources() if source.id == "daily-tribune")
    with connected_reconstruction(URL, REPLAY_AT), ExitStack() as stack:
        stack.enter_context(patch.object(capture_tools, "REPLAY_AT", REPLAY_AT))
        stack.enter_context(capture_tools.replay_clock())
        with SessionLocal() as db, client(CAPTURE_DIR, requests, at=REPLAY_AT) as publisher:
            discovered = discover_news(selected, publisher, db)
        with SessionLocal() as db, db.begin():
            article = db.scalar(select(NewsArticle).where(NewsArticle.canonical_url == URL))
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
        policy = evaluation_policy(auditor, config, publication_admission_at=REPLAY_AT)
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
        result = {"at": at.isoformat(), "publication_admission_at": REPLAY_AT.isoformat(), "source_url": URL,
            "article_id": article_id, "run_id": run_id, "requests": requests,
            "collector_candidates": len(discovered.candidates), "extraction": asdict(extracted),
            "seed": asdict(seeded), "evaluation": asdict(evaluated), "publication": published,
            "publication_skipped": skipped, "footprints": asdict(footprints),
            "zone_ids": sorted(set(row[0] for row in links)), "case_ids": sorted(set(row[1] for row in links))}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        if result["zone_ids"]:
            configuration = {"database_identity": database_identity(), "at": at.isoformat(),
                "source_url": URL, "case_ids": result["case_ids"], "zone_ids": result["zone_ids"]}
            SCENARIO_PATH.parent.mkdir(parents=True, exist_ok=True)
            SCENARIO_PATH.write_text(json.dumps(configuration, indent=2), encoding="utf-8")
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorize-connected-reconstruction", action="store_true", required=True)
    parser.add_argument("--at", type=datetime.fromisoformat, default=datetime.fromisoformat("2026-09-24T16:39:00+08:00"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = asyncio.run(reconstruct(args.at, args.output))
    print(json.dumps(result, default=str))
    if not result["zone_ids"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
