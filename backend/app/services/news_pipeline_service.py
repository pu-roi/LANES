"""Explicit runtime orchestration; immutable extraction is committed first."""
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.crud.news_processing import utc_now
from app.services.news_claim_auditor import NewsClaimAuditor
from app.services.news_evaluation_service import evaluate_news_claims, evaluation_policy, seed_claim_evaluations
from app.services.news_processing_service import process_saved_news
from app.services.news_footprint_worker_service import process_news_footprints
from app.services.news_sources import NewsSource


async def run_news_pipeline(session_factory: Callable[[], Session], *, limit: int = 50,
                            seed_cursor: int = 0, auditor: NewsClaimAuditor | None = None,
                            footprint_cursor: int = 0, unbound_only: bool = False,
                            sources: tuple[NewsSource, ...] | None = None,
                            clock: Callable[[], datetime] = utc_now) -> dict:
    """Only call after operator configuration; auditing may incur provider fees.

    No discovery is performed here. A collector can keep capturing articles
    independently. Each extraction/evaluation/publication stage commits its own
    durable work; one provider failure never rolls back captured extraction.
    """
    from app.services.news_publication_service import process_news_publications
    if not 1 <= limit <= 200 or seed_cursor < 0 or footprint_cursor < 0:
        raise ValueError("Invalid pipeline batch")
    auditor = auditor or NewsClaimAuditor()
    policy = evaluation_policy(auditor)
    processed = await process_saved_news(session_factory, limit=limit, clock=clock)
    seeded = seed_claim_evaluations(session_factory, policy, now=clock(), limit=limit, after_run_id=seed_cursor,
                                    sources=sources, unbound_only=unbound_only)
    evaluated = await evaluate_news_claims(session_factory, limit=limit, auditor=auditor, policy=policy, clock=clock, sources=sources)
    published = process_news_publications(session_factory, policy=policy, limit=limit, clock=clock, sources=sources)
    footprints = process_news_footprints(session_factory, policy=policy, limit=limit, clock=clock,
                                        after_case_id=footprint_cursor, sources=sources)
    return {"extraction": asdict(processed), "seed": asdict(seeded), "evaluation": asdict(evaluated),
            "publication": asdict(published), "footprints": asdict(footprints),
            "next_seed_cursor": seeded.next_after_run_id, "next_footprint_cursor": footprints.next_after_case_id}


def pipeline_has_failures(result: dict) -> bool:
    """Operational fallback without a configured catalog is normal, errors are not."""
    return any(result.get(stage, {}).get(key, 0)
        for stage in ("extraction", "seed", "evaluation", "publication", "footprints")
        for key in ("failed", "retry_wait", "lease_lost", "skipped"))
