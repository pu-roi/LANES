"""The news job rechecks adaptive collection due time and pipeline policy."""
from datetime import datetime, timezone
import asyncio
import httpx
from sqlalchemy import select, text
from app.models.setting import SystemSetting
from app.models.news_telemetry import NewsDiscoveryRun
from app.schemas.configuration import ConfigurationRuntime, NewsStageHealth, NewsCycleSummary
from app.services.configuration_service import RUNTIME_KEY, read_configuration, selected_news_sources, write_runtime
from app.services.news_discovery_service import discover_news
from app.services.news_pipeline_service import run_news_pipeline, pipeline_has_failures
from app.services.news_collection_cadence_service import collection_is_due, next_collection_due
from app.services.news_cycle_service import attempt_identity, finish_cycle, safe_code
from app.services.news_claim_auditor import AuditorConfigurationError

WORKER_LOCK = 614296502


async def run_scheduled_news_tick(session_factory, *, limit: int = 50, sources=None, clock=None) -> dict:
    clock = clock or (lambda: datetime.now(timezone.utc))
    identity = attempt_identity()
    output: dict = {}
    with session_factory() as lease:
        connection = lease.connection()
        locked = connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": WORKER_LOCK})
        if not locked:
            return {"outcome": "already_running"}
        try:
            with session_factory() as db:
                config = read_configuration(db)
                active = selected_news_sources(db, sources)
                row = db.get(SystemSetting, RUNTIME_KEY)
                runtime = ConfigurationRuntime.model_validate(row.value) if row else ConfigurationRuntime()
                previous = db.scalar(select(NewsDiscoveryRun.started_at).where(NewsDiscoveryRun.trigger == "collector").order_by(NewsDiscoveryRun.started_at.desc()).limit(1))
                runtime.last_started_at = clock()
                runtime.running = True
                runtime.error_code = None
                runtime.stage_outcomes = {}
                # Retain a distinct completed-cycle snapshot while this cycle
                # records its own progress and counts.
                if runtime.last_cycle is None and runtime.last_finished_at and row:
                    old = ConfigurationRuntime.model_validate(row.value)
                    if old.last_started_at and old.last_finished_at >= old.last_started_at:
                        runtime.last_cycle = NewsCycleSummary(started_at=old.last_started_at,
                            finished_at=old.last_finished_at, counts=old.stage_counts,
                            outcome="requires_attention" if old.error_code else "completed", error_code=old.error_code)
                runtime.stage_counts = {}
                runtime.current_stage = "maintenance"
                runtime.stage_started_at = runtime.last_started_at
                runtime.last_progress_at = runtime.last_started_at
                write_runtime(db, runtime)

            def report_stage(stage: str, summary: dict | None = None) -> None:
                runtime.last_progress_at = clock()
                if summary is None:
                    runtime.current_stage = stage
                    runtime.stage_started_at = runtime.last_progress_at
                else:
                    runtime.stage_counts[stage] = {k: v for k, v in summary.items()
                                                   if isinstance(v, int) and not isinstance(v, bool)}
                with session_factory() as progress_db:
                    write_runtime(progress_db, runtime)

            try:
                from app.services.news_weather_controller_service import adaptive_decision
                with session_factory() as db:
                    from app.services.flood_event_service import expire_due_zones
                    expire_due_zones(db, now=clock())
                    interval = adaptive_decision(db, clock()).interval_minutes
                due = collection_is_due(previous, clock(), interval)
                if config.news_collection_enabled and active and due:
                    with session_factory() as db, httpx.Client(timeout=httpx.Timeout(12, connect=5)) as client:
                        # Recheck immediately before network work; publisher URLs remain registry-owned.
                        current = read_configuration(db)
                        selected = selected_news_sources(db, active)
                        interval = adaptive_decision(db, clock()).interval_minutes
                        due = collection_is_due(previous, clock(), interval)
                        if current.news_collection_enabled and selected and due:
                            try:
                                report_stage("collection")
                                run = discover_news(selected, client, db)
                                runtime.stage_counts["collection"] = {
                                    "entries_read": sum(p.entry_count for p in run.probes),
                                    "eligible_candidates": len(run.candidates),
                                }
                                bad_feeds = [p for p in run.probes if p.status not in ("parsed", "unchanged", "empty")]
                                runtime.stage_outcomes["collection"] = "failed" if bad_feeds else "completed"
                                prior = runtime.stages.get("collection", NewsStageHealth())
                                runtime.stages["collection"] = NewsStageHealth(last_attempt_at=runtime.last_started_at,
                                    last_success_at=clock() if not bad_feeds else prior.last_success_at,
                                    outcome=runtime.stage_outcomes["collection"], counts=runtime.stage_counts["collection"],
                                    errors=sorted({safe_code("feed_" + probe.status) for probe in bad_feeds})[:20])
                                previous = runtime.last_started_at
                                report_stage("collection", runtime.stage_counts["collection"])
                            except Exception:
                                runtime.stage_outcomes["collection"] = "failed"
                                runtime.stages["collection"] = NewsStageHealth(last_attempt_at=runtime.last_started_at,
                                    last_success_at=runtime.stages.get("collection", NewsStageHealth()).last_success_at,
                                    outcome="failed", errors=["collection_failed"])
                                previous = runtime.last_started_at
                        else:
                            runtime.stage_outcomes["collection"] = "paused"
                else:
                    runtime.stage_outcomes["collection"] = "paused" if not config.news_collection_enabled else "no_enabled_sources" if not active else "not_due"
                report_stage("pipeline")
                result = await run_news_pipeline(session_factory, limit=limit, unbound_only=True, sources=sources, clock=clock,
                                                 on_stage=report_stage)
                for stage, value in result.items():
                    if isinstance(value, dict) and stage != "stage_outcomes":
                        runtime.stage_counts[stage] = {k: v for k, v in value.items() if isinstance(v, int) and not isinstance(v, bool)}
                        errors = [item.get("error_code") or item.get("reason_code") for name in ("runs", "evaluations", "skipped")
                            for item in value.get(name, []) if (item.get("error_code") or item.get("reason_code")) and item.get("reason_code") not in ("automatic_publication_paused", "automatic_source_paused")]
                        if value.get("error_code"):
                            errors.append(value["error_code"])
                        if not errors and any(value.get(key, 0) for key in ('failed','retry_wait','lease_lost')):
                            errors.append('stage_failed')
                        errors = sorted({safe_code(error) for error in errors})[:20]
                        prior = runtime.stages.get(stage, NewsStageHealth())
                        attempted = (config.news_processing_enabled if stage in ("extraction", "seed", "evaluation") else True)
                        if stage in ('extraction','seed','evaluation') and result.get('stage_outcomes',{}).get('processing')=='paused':
                            attempted = False
                        if stage == "footprints": attempted = config.news_publication_enabled
                        if attempted:
                            runtime.stages[stage] = NewsStageHealth(last_attempt_at=runtime.last_started_at,
                                last_success_at=clock() if not errors else prior.last_success_at,
                                outcome="requires_attention" if errors else "completed",
                                counts=runtime.stage_counts[stage], errors=sorted(set(errors)))
                            runtime.stage_outcomes[stage] = 'requires_attention' if errors else 'completed'
                        else:
                            runtime.stage_outcomes[stage] = 'paused'
                runtime.stage_outcomes.update(result["stage_outcomes"])
                failed = pipeline_has_failures(result) or runtime.stage_outcomes.get("collection") == "failed"
                runtime.error_code = "pipeline_requires_attention" if failed else None
                if not failed:
                    runtime.last_successful_at = clock()
                output.update({**result, "outcome": "requires_attention" if failed else "completed"})
                return output
            except AuditorConfigurationError as exc:
                runtime.error_code = exc.code
                stage = runtime.current_stage or 'pipeline'
                runtime.stage_outcomes[stage] = 'requires_attention'
                prior = runtime.stages.get(stage, NewsStageHealth())
                runtime.stages[stage] = NewsStageHealth(last_attempt_at=runtime.last_started_at,
                    last_success_at=prior.last_success_at, outcome='requires_attention', errors=[exc.code])
                output.update(outcome='requires_attention', error_code=exc.code)
                return output
            except BaseException as exc:
                # Cancellation must not become a successful completed history entry.
                runtime.error_code = 'worker_interrupted' if isinstance(exc,(KeyboardInterrupt,asyncio.CancelledError)) else 'worker_failed'
                stage = runtime.current_stage or 'pipeline'
                runtime.stage_outcomes[stage] = 'failed'
                prior = runtime.stages.get(stage, NewsStageHealth())
                runtime.stages[stage] = NewsStageHealth(last_attempt_at=runtime.last_started_at,
                    last_success_at=prior.last_success_at, outcome='failed', errors=[runtime.error_code])
                raise
            finally:
                runtime.running = False
                runtime.last_finished_at = clock()
                runtime.current_stage = None
                runtime.stage_started_at = None
                runtime.last_progress_at = runtime.last_finished_at
                cycle = finish_cycle(runtime, runtime.last_finished_at, identity)
                output.update(stage_outcomes=runtime.stage_outcomes, stage_results=cycle.stage_outcomes, stage_errors=cycle.stage_errors,
                    execution_name=cycle.execution_name, task_index=cycle.task_index, task_attempt=cycle.task_attempt)
                with session_factory() as db:
                    current = read_configuration(db)
                    interval = adaptive_decision(db, clock()).interval_minutes
                    runtime.next_collection_at = next_collection_due(previous, interval) if previous and current.news_collection_enabled and selected_news_sources(db, sources) else None
                    write_runtime(db, runtime)
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": WORKER_LOCK})
