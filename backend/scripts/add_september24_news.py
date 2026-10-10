"""Add the requested original article through normal capture/extraction services.

This is an explicit operator import, not an RSS membership assertion. It does
not change source approvals, zone rows, source facts or publication policy.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from sqlalchemy import select

from scripts.replay_september24_news import PUBLISHED, TITLE, URL
from scripts.replay_september24_pipeline import CAPTURE_DIR, REPLAY_AT


async def add_article(*, expected_database: str, write: bool) -> dict:
    from app.core.config import settings
    from app.core.database import SessionLocal, engine
    from sqlalchemy.engine import make_url
    configured = make_url(settings.DATABASE_URL)
    if engine.url != configured or configured.database != expected_database:
        raise ValueError("Configured and bound database must match the explicitly selected database")
    if not write:
        raise ValueError("Explicit --write is required for the requested article addition")
    from app.crud.news import get_article, save_candidate
    from app.models.report import FloodAvoidanceZone
    from app.services.news_discovery_service import NewsCandidate, body_has_metro_manila_flood_claim
    from app.services.news_feed_service import NewsEntry
    from app.services.news_processing_service import process_saved_news
    from app.services.news_results_service import browse_news_results, read_news_result
    from app.services.news_evaluation_service import source_is_approved
    from app.services.news_sources import load_news_sources
    from app.services.news_estimated_road_service import build_estimated_road_zone
    from app.crud.news_publication import NewsPublicationError
    from app.services.news_placement_preview_service import get_news_placement_preview_service
    from app.schemas.news_results import NewsResultPlacementPreview
    from app.schemas.news_extraction import NewsArticleExtractorInput

    body = (CAPTURE_DIR / "article-4-body.txt").read_text(encoding="utf-8")
    if hashlib.sha256(body.encode()).hexdigest() != "dc4773d602277a22fb0660705e21eb45f64125f4bd8167cd55ad21ec3350bc0f":
        raise ValueError("Captured original article body changed")
    source_id = "daily-tribune"
    entry = NewsEntry(source_id, "Daily Tribune", URL, URL, TITLE, "", URL, PUBLISHED)
    if not body_has_metro_manila_flood_claim(entry, body):
        raise ValueError("Captured article does not pass the normal observed-flood policy")
    with SessionLocal() as db:
        before = [(z.id, z.is_active, z.expires_at, bytes(z.geometry.data))
                  for z in db.scalars(select(FloodAvoidanceZone).order_by(FloodAvoidanceZone.id))]
        existing = get_article(db, URL)
        unchanged = bool(existing and existing.article_text == body and existing.title == TITLE
                         and existing.published_at == PUBLISHED
                         and existing.publisher_source_id == source_id)
        if unchanged:
            article_id = existing.id
        else:
            with db.begin_nested():
                article = save_candidate(db, entry, NewsCandidate(source_id, "Daily Tribune", URL,
                    URL, TITLE, "", PUBLISHED, datetime.now(timezone.utc), body, None))
                article_id = article.id
            db.commit()
    processed = await process_saved_news(SessionLocal, article_id=article_id, clock=lambda: REPLAY_AT)
    if processed.failed or processed.retry_wait or processed.lease_lost:
        raise RuntimeError("The normal article-processing service did not complete")
    from app.services.news_evaluation_service import evaluation_policy, seed_claim_evaluations
    from app.services.news_claim_auditor import NewsClaimAuditor
    with SessionLocal() as db:
        current = browse_news_results(db, page=1, page_size=100, search=TITLE, publisher=None,
            condition=None, placement=None, order="extraction_newest")
        run_ids = sorted({item.run_id for item in current.items if item.article_id == article_id})
    seeded = [asdict(seed_claim_evaluations(SessionLocal, evaluation_policy(NewsClaimAuditor()),
        now=REPLAY_AT, run_id=run_id, sources=load_news_sources(), obey_configuration=True)) for run_id in run_ids]
    with SessionLocal() as db:
        page = browse_news_results(db, page=1, page_size=100, search=TITLE, publisher=None,
            condition=None, placement=None, order="extraction_newest")
        items = [item for item in page.items if item.article_id == article_id]
        after = [(z.id, z.is_active, z.expires_at, bytes(z.geometry.data))
                 for z in db.scalars(select(FloodAvoidanceZone).order_by(FloodAvoidanceZone.id))]
        if before != after:
            raise RuntimeError("Zone state changed during article addition; inspect concurrent activity")
        article_input = NewsArticleExtractorInput(article_id=article_id, canonical_url=URL,
            publisher=source_id, title=TITLE, article_text=body, published_at=PUBLISHED)
        placements = []
        previews = []
        service = get_news_placement_preview_service()
        for item in items:
            detail = read_news_result(db, item.run_id, item.claim_index)
            previews.append(NewsResultPlacementPreview(run_id=item.run_id, claim_index=item.claim_index,
                input_fingerprint=detail.input_fingerprint, evidence_pipeline_version=detail.pipeline_version,
                placement_revision=service.revision, claim=detail.claim, preview=service.preview(detail.claim)))
            try:
                estimate = build_estimated_road_zone(detail.claim)
                placements.append({"road": item.claim.canonical_road, "eligible": True,
                    "geometry_type": estimate.geometry["type"]})
            except NewsPublicationError as error:
                placements.append({"road": item.claim.canonical_road, "eligible": False, "reason": error.code})
        selected = next((p for p in previews if any(c.preview_geometry for c in p.preview.candidates)), None)
        snapshot = {"mode": "september24", "simulated_at": REPLAY_AT.isoformat(), "article_title": TITLE,
            "source_url": URL, "reported_locations": len(previews), "status": "Needs Review",
            "placement": selected.model_dump(mode="json") if selected else None,
            "modeled_candidates": sum(bool(c.preview_geometry) for c in selected.preview.candidates) if selected else 0,
            "routing_affected": False,
            "reason": "The original report is captured in the connected database; source/time/section checks do not permit active-zone creation.",
            "subsidence_reason": "These reported locations are outside the current Pasig prediction scope."}
        return {"database": expected_database, "article_id": article_id, "already_present": unchanged,
            "processing": asdict(processed), "reported_locations": len(items),
            "evaluation_seed": seeded,
            "results": [item.model_dump(mode="json") for item in items],
            "source_approved": source_is_approved(article_input, load_news_sources()),
            "automatic_geometry_results": placements,
            "simulation_snapshot": snapshot,
            "existing_zones_unchanged": True, "active_zone_ids": [z[0] for z in after if z[1]],
            "source_url": URL, "published_at": PUBLISHED.isoformat(),
            "simulated_at": REPLAY_AT.isoformat(), "automatic_publication_executed": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-database", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = asyncio.run(add_article(expected_database=args.expected_database, write=args.write))
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key not in {"results", "simulation_snapshot"}}, indent=2))


if __name__ == "__main__":
    main()
