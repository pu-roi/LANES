"""Lightweight weather controller; all pipeline work remains in the existing job."""
from datetime import datetime, timedelta, timezone
import time
from uuid import uuid4
import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import settings
from app.crud.news_weather import current_flood_until, latest_collection_at, pending_pipeline_work, read_controller, save_controller
from app.services.configuration_service import read_configuration, selected_news_sources
from app.services.news_job_dispatch_service import NewsJobGateway
from app.services.news_weather_service import choose_interval, fetch_weather
from app.schemas.news_weather import AdaptiveDecision

CONTROLLER_LOCK = 614296503


def adaptive_decision(db: Session, now: datetime) -> AdaptiveDecision:
    state = read_controller(db)
    return choose_interval(state.providers, now=now, last_positive_at=state.last_positive_at,
                           active_flood=bool(state.active_flood_until and state.active_flood_until > now))


def run_weather_tick(session_factory: sessionmaker, *, now: datetime | None = None,
                     client: httpx.Client | None = None, gateway: object | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    timer = time.monotonic()
    with session_factory() as lease:
        connection = lease.connection()
        if not connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": CONTROLLER_LOCK}):
            return {"outcome": "already_checking"}
        own_client = client is None
        client = client or httpx.Client(timeout=httpx.Timeout(10, connect=5), follow_redirects=False)
        try:
            with session_factory() as db:
                state = read_controller(db)
                # Retries of a completed quarter-hour tick never repeat provider calls or dispatch.
                slot = now.replace(minute=(now.minute//15)*15, second=0, microsecond=0)
                if state.last_tick_at and state.last_tick_at >= slot:
                    return {"outcome": "duplicate_tick", "dispatch_state": state.dispatch_state}
                state.providers = fetch_weather(client, now=now)
                state.active_flood_until = current_flood_until(db, now)
                decision = choose_interval(state.providers, now=now, last_positive_at=state.last_positive_at,
                    active_flood=bool(state.active_flood_until and state.active_flood_until > now))
                state.last_positive_at = decision.last_positive_at
                state.last_tick_at = now
                state.checks += 1
                state.provider_failures += sum(p.error_code is not None for p in state.providers)
                save_controller(db, state)
                try:
                    if state.dispatch_state in ("reserved", "submitted", "unknown"):
                        gateway = gateway or NewsJobGateway(settings.NEWS_CLOUD_RUN_JOB, client)
                        if state.dispatch_reserved_at and now-state.dispatch_reserved_at < timedelta(minutes=15):
                            return {"outcome": "dispatch_pending"}
                        result = gateway.reconcile(state.dispatch_token, state.dispatch_operation, state.dispatch_reserved_at)
                        if state.dispatch_state in ("reserved", "unknown") and result in ("running", "finished", "failed"):
                            state.worker_starts += 1
                            state.last_dispatch_at = state.dispatch_reserved_at
                        if result in ("running", "unknown"):
                            state.dispatch_state = "submitted" if result == "running" else "unknown"
                            state.dispatch_error = None if result == "running" else "news_dispatch_reconciliation_unresolved"
                            return {"outcome": "dispatch_pending"}
                        state.dispatch_state = "failed" if result == "failed" else "idle"
                        state.dispatch_error = "news_worker_execution_failed" if result == "failed" else None
                    config = read_configuration(db)
                    sources = selected_news_sources(db)
                    previous = latest_collection_at(db)
                    collection_due = config.news_collection_enabled and sources and (previous is None or now >= previous+timedelta(minutes=decision.interval_minutes))
                    from app.services.news_evaluation_service import evaluation_policy, ADMISSION_AGE
                    from app.services.news_claim_auditor import NewsClaimAuditor
                    policy = evaluation_policy(NewsClaimAuditor(), config)
                    work_due = pending_pipeline_work(db, now, config, tuple(s.id for s in sources),
                        policy_fingerprint=policy.fingerprint, admission_age=ADMISSION_AGE)
                    if not collection_due and not work_due:
                        return {"outcome": "not_due", "interval_minutes": decision.interval_minutes}
                    gateway = gateway or NewsJobGateway(settings.NEWS_CLOUD_RUN_JOB, client)
                    state.dispatch_token = str(uuid4())
                    state.dispatch_reserved_at = now
                    state.dispatch_operation = None
                    state.dispatch_state = "reserved"
                    state.dispatch_error = None
                    save_controller(db, state)  # Durable reservation BEFORE external side effect.
                    state.dispatch_operation = gateway.start(state.dispatch_token)
                    state.dispatch_state = "submitted"
                    state.last_dispatch_at = now
                    state.worker_starts += 1
                    return {"outcome": "dispatched", "interval_minutes": decision.interval_minutes}
                except Exception:
                    # Timeouts can follow an accepted external start. Keep its token
                    # for reconciliation instead of immediately posting a duplicate.
                    state.dispatch_state = "unknown" if state.dispatch_state in ("reserved", "submitted", "unknown") else "failed"
                    state.dispatch_error = "news_dispatch_unavailable"
                    return {"outcome": "requires_attention", "error_code": state.dispatch_error}
                finally:
                    state.last_tick_duration_ms = round((time.monotonic()-timer)*1000)
                    save_controller(db, state)
        finally:
            if own_client:
                client.close()
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": CONTROLLER_LOCK})
