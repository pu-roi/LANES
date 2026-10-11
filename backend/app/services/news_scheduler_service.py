"""A fixed scheduler tick runs due collection and independent lifecycle work."""
from datetime import datetime, timedelta, timezone
import httpx
from sqlalchemy import select, text
from app.models.setting import SystemSetting
from app.models.news_telemetry import NewsDiscoveryRun
from app.schemas.configuration import ConfigurationRuntime, NewsStageHealth
from app.services.configuration_service import RUNTIME_KEY, read_configuration, selected_news_sources, write_runtime
from app.services.news_discovery_service import discover_news
from app.services.news_pipeline_service import run_news_pipeline, pipeline_has_failures

WORKER_LOCK = 614296502


async def run_scheduled_news_tick(session_factory, *, limit: int = 50, sources=None, clock=None) -> dict:
    clock = clock or (lambda: datetime.now(timezone.utc))
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
                write_runtime(db, runtime)
            try:
                with session_factory() as db:
                    from app.services.flood_event_service import expire_due_zones
                    expire_due_zones(db, now=clock())
                due = previous is None or clock() >= previous + timedelta(minutes=config.news_collection_interval_minutes)
                if config.news_collection_enabled and active and due:
                    with session_factory() as db, httpx.Client(timeout=httpx.Timeout(12, connect=5)) as client:
                        # Recheck immediately before network work; publisher URLs remain registry-owned.
                        current = read_configuration(db)
                        selected = selected_news_sources(db, active)
                        if current.news_collection_enabled and selected:
                            try:
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
                                    errors=["feed_" + probe.status for probe in bad_feeds])
                                previous = runtime.last_started_at
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
                result = await run_news_pipeline(session_factory, limit=limit, unbound_only=True, sources=sources, clock=clock)
                for stage, value in result.items():
                    if isinstance(value, dict) and stage != "stage_outcomes":
                        runtime.stage_counts[stage] = {k: v for k, v in value.items() if isinstance(v, int) and not isinstance(v, bool)}
                        errors = [item.get("error_code") or item.get("reason_code") for name in ("runs", "evaluations", "skipped")
                            for item in value.get(name, []) if (item.get("error_code") or item.get("reason_code")) and item.get("reason_code") not in ("automatic_publication_paused", "automatic_source_paused")]
                        prior = runtime.stages.get(stage, NewsStageHealth())
                        attempted = (config.news_processing_enabled if stage in ("extraction", "seed", "evaluation") else True)
                        if stage == "footprints": attempted = config.news_publication_enabled
                        if attempted:
                            runtime.stages[stage] = NewsStageHealth(last_attempt_at=runtime.last_started_at,
                                last_success_at=clock() if not errors else prior.last_success_at,
                                outcome="requires_attention" if errors else "completed",
                                counts=runtime.stage_counts[stage], errors=sorted(set(errors)))
                runtime.stage_outcomes.update(result["stage_outcomes"])
                failed = pipeline_has_failures(result) or runtime.stage_outcomes.get("collection") == "failed"
                runtime.error_code = "pipeline_requires_attention" if failed else None
                if not failed:
                    runtime.last_successful_at = clock()
                return {"outcome": "requires_attention" if failed else "completed", **result}
            except Exception:
                runtime.error_code = "worker_failed"
                raise
            finally:
                runtime.running = False
                runtime.last_finished_at = clock()
                runtime.next_collection_at = (previous + timedelta(minutes=config.news_collection_interval_minutes)) if previous and config.news_collection_enabled and active else None
                with session_factory() as db:
                    current = read_configuration(db)
                    runtime.next_collection_at = previous + timedelta(minutes=current.news_collection_interval_minutes) if previous and current.news_collection_enabled and selected_news_sources(db, sources) else None
                    write_runtime(db, runtime)
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": WORKER_LOCK})
