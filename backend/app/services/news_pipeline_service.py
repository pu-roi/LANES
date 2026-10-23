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
                            publication_admission_at: datetime | None = None,
                            clock: Callable[[], datetime] = utc_now,
                            on_stage: Callable[[str, dict | None], None] | None = None,
                            native_context=None, native_client=None, runtime_factory=None) -> dict:
    """Only call after operator configuration; auditing may incur provider fees.

    No discovery is performed here. A collector can keep capturing articles
    independently. Each extraction/evaluation/publication stage commits its own
    durable work; one provider failure never rolls back captured extraction.
    """
    if native_context is not None:
        from app.services.news_ner_durable.pipeline import run_native_news_pipeline
        from app.services.news_ner_durable.gemini_resolution import GeminiResolver
        # Native source-rule operation remains credential-free. Paid verification
        # must be explicitly requested by the caller (or the dedicated CLI).
        resolver_config = auditor.config if auditor is not None else None
        if resolver_config is not None and resolver_config.provider not in (None,'source_rules','gemini'):
            from app.services.news_claim_auditor import AuditorConfigurationError
            raise AuditorConfigurationError('native_auditor_provider_unsupported')
        resolver = GeminiResolver(resolver_config) if resolver_config is not None and resolver_config.provider == 'gemini' else None
        if sources is None:
            from app.services.news_sources import load_news_sources
            sources=load_news_sources()
        return await run_native_news_pipeline(session_factory,load_assets=lambda:native_context.trusted,
            environment=native_context.environment,database_url=native_context.database_url,sources=sources,
            client=native_client,limit=limit,clock=clock,on_stage=on_stage,runtime_factory=runtime_factory,resolver=resolver)
    from app.services.news_publication_service import process_news_publications, process_news_expiry, PublicationSummary
    if not 1 <= limit <= 200 or seed_cursor < 0 or footprint_cursor < 0:
        raise ValueError("Invalid pipeline batch")
    from app.services.news_claim_auditor import AuditorConfigurationError
    try:
        auditor = auditor or NewsClaimAuditor()
        if getattr(auditor, 'config', None) and auditor.config.error_code():
            raise AuditorConfigurationError(auditor.config.error_code())
    except AuditorConfigurationError as exc:
        # No policy can be authenticated here. Only maintain existing deadlines;
        # do not process even saved clearance evidence through an invented policy.
        from sqlalchemy.exc import SQLAlchemyError
        try:
            maintenance = process_news_expiry(session_factory, limit=limit, clock=clock)
        except Exception as failure:
            code = "maintenance_storage_unavailable" if isinstance(failure, SQLAlchemyError) else "maintenance_failed"
            maintenance = PublicationSummary(skipped=[{"reason_code": code}])
        exc.maintenance_summary = maintenance
        raise
    maintenance_sources = sources
    config, sources = runtime_configuration(session_factory, sources)
    policy = evaluation_policy(auditor, config, publication_admission_at=publication_admission_at)
    from app.services.news_processing_service import ProcessingSummary
    from app.services.news_evaluation_service import EvaluationSummary
    from app.services.news_footprint_worker_service import FootprintWorkerSummary
    def report(stage: str, summary: dict | None = None) -> None:
        if on_stage is not None:
            on_stage(stage, summary)

    processed, seeded, evaluated = ProcessingSummary(), EvaluationSummary(), EvaluationSummary()
    if config.news_processing_enabled:
        report("extraction")
        processed = await process_saved_news(session_factory, limit=limit, clock=clock, obey_configuration=True, sources=sources)
        report("extraction", asdict(processed))
        report("seed")
        seeded = seed_claim_evaluations(session_factory, policy, now=clock(), limit=limit, after_run_id=seed_cursor,
                                        sources=sources, unbound_only=unbound_only, obey_configuration=True)
        report("seed", asdict(seeded))
        report("evaluation")
        evaluated = await evaluate_news_claims(session_factory, limit=limit, auditor=auditor, policy=policy, clock=clock,
            sources=sources, obey_configuration=True, on_progress=lambda summary: report("evaluation", summary))
        report("evaluation", asdict(evaluated))
    report("publication")
    published = process_news_publications(session_factory, policy=policy, limit=limit, clock=clock, sources=maintenance_sources, maintenance_only=not config.news_publication_enabled)
    report("publication", asdict(published))
    footprints = FootprintWorkerSummary()
    if config.news_publication_enabled:
        report("footprints")
        footprints = process_news_footprints(session_factory, policy=policy, limit=limit, clock=clock,
                                            after_case_id=footprint_cursor, sources=sources)
        report("footprints", asdict(footprints))
    return {"extraction": asdict(processed), "seed": asdict(seeded), "evaluation": asdict(evaluated),
            "publication": asdict(published), "footprints": asdict(footprints),
            "stage_outcomes": {"processing": "enabled" if config.news_processing_enabled else "paused", "publication": "enabled" if config.news_publication_enabled else "paused"},
            "next_seed_cursor": seeded.next_after_run_id, "next_footprint_cursor": footprints.next_after_case_id}


def pipeline_has_failures(result: dict) -> bool:
    """Operational fallback without a configured catalog is normal, errors are not."""
    for stage in ("extraction", "resolution", "seed", "evaluation", "publication", "footprints"):
        value = result.get(stage, {})
        if value.get("error_code"):
            return True
        if any(value.get(key, 0) for key in ("failed", "retry_wait", "lease_lost")):
            return True
        if any(item.get("reason_code") not in ("automatic_publication_paused", "automatic_source_paused") for item in value.get("skipped", [])):
            return True
    return False
