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


def runtime_configuration(session_factory, sources):
    from app.services.configuration_service import read_configuration, selected_news_sources
    with session_factory() as db:
        return read_configuration(db), selected_news_sources(db, sources)


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
    maintenance_sources = sources
    config, sources = runtime_configuration(session_factory, sources)
    policy = evaluation_policy(auditor, config)
    from app.services.news_processing_service import ProcessingSummary
    from app.services.news_evaluation_service import EvaluationSummary
    from app.services.news_footprint_worker_service import FootprintWorkerSummary
    processed = (await process_saved_news(session_factory, limit=limit, clock=clock, obey_configuration=True, sources=sources)
                 if config.news_processing_enabled else ProcessingSummary())
    seeded = seed_claim_evaluations(session_factory, policy, now=clock(), limit=limit, after_run_id=seed_cursor,
                                    sources=sources, unbound_only=unbound_only, obey_configuration=True) if config.news_processing_enabled else EvaluationSummary()
    evaluated = await evaluate_news_claims(session_factory, limit=limit, auditor=auditor, policy=policy, clock=clock, sources=sources, obey_configuration=True) if config.news_processing_enabled else EvaluationSummary()
    published = process_news_publications(session_factory, policy=policy, limit=limit, clock=clock, sources=maintenance_sources, maintenance_only=not config.news_publication_enabled)
    footprints = process_news_footprints(session_factory, policy=policy, limit=limit, clock=clock,
                                        after_case_id=footprint_cursor, sources=sources) if config.news_publication_enabled else FootprintWorkerSummary()
    return {"extraction": asdict(processed), "seed": asdict(seeded), "evaluation": asdict(evaluated),
            "publication": asdict(published), "footprints": asdict(footprints),
            "stage_outcomes": {"processing": "enabled" if config.news_processing_enabled else "paused", "publication": "enabled" if config.news_publication_enabled else "paused"},
            "next_seed_cursor": seeded.next_after_run_id, "next_footprint_cursor": footprints.next_after_case_id}


def pipeline_has_failures(result: dict) -> bool:
    """Operational fallback without a configured catalog is normal, errors are not."""
    for stage in ("extraction", "seed", "evaluation", "publication", "footprints"):
        value = result.get(stage, {})
        if any(value.get(key, 0) for key in ("failed", "retry_wait", "lease_lost")):
            return True
        if any(item.get("reason_code") not in ("automatic_publication_paused", "automatic_source_paused") for item in value.get("skipped", [])):
            return True
    return False
