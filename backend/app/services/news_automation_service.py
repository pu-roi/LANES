"""Server-owned status derivation. A configured due time is not a scheduler promise."""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.crud.news_automation import latest_collection_diagnostics
from app.schemas.configuration import NewsCycleSummary
from app.schemas.news_automation import NewsAutomationStatus, NewsAuditDiagnostics
from app.services.configuration_service import configuration_response, selected_news_sources, RUNTIME_KEY
from app.models.setting import SystemSetting
from app.services.news_monitoring_service import read_news_monitoring
from app.crud.news_weather import read_controller
from app.schemas.news_weather import NewsWeatherStatus
from app.services.news_weather_service import choose_interval, effective_providers, POINTS, CATALOG_VERSION
from app.services.news_collection_cadence_service import next_collection_due

STAGE_LABELS = {"maintenance": "Updating flood statuses", "collection": "Gathering news",
                "pipeline": "Preparing news workflow",
                "extraction": "Processing articles", "seed": "Preparing flood claims",
                "evaluation": "Evaluating flood claims", "publication": "Updating flood publications",
                "footprints": "Plotting qualified flood areas"}


def read_news_automation(db: Session, *, now: datetime | None = None) -> NewsAutomationStatus:
    now = now or datetime.now(timezone.utc)
    response = configuration_response(db, can_edit=False)
    config, runtime = response.settings, response.runtime
    controller = read_controller(db)
    decision = choose_interval(controller.providers, now=now, last_positive_at=controller.last_positive_at,
        active_flood=bool(controller.active_flood_until and controller.active_flood_until > now))
    weather = NewsWeatherStatus(catalog_version=CATALOG_VERSION, points=list(POINTS), providers=effective_providers(controller.providers, now),
        effective_interval_minutes=decision.interval_minutes, reason=decision.reason,
        last_positive_at=controller.last_positive_at, controller_heartbeat_at=controller.last_tick_at,
        controller_stale=not controller.last_tick_at or now-controller.last_tick_at >= timedelta(minutes=30),
        dispatch_state=controller.dispatch_state, dispatch_error=controller.dispatch_error,
        last_dispatch_at=controller.last_dispatch_at, last_tick_duration_ms=controller.last_tick_duration_ms,
        checks=controller.checks, provider_failures=controller.provider_failures, worker_starts=controller.worker_starts)
    latest, feeds = latest_collection_diagnostics(db)
    latest_at = latest.started_at if latest else None
    if latest_at and latest_at.tzinfo is None:
        latest_at = latest_at.replace(tzinfo=timezone.utc)
    row = db.get(SystemSetting, RUNTIME_KEY)
    collection_health = runtime.stages.get("collection")
    persisted_collection = bool(row and row.value.get("stages", {}).get("collection"))
    if (persisted_collection and latest and latest.finished_at and collection_health
            and collection_health.last_attempt_at and latest_at
            and abs(latest_at - collection_health.last_attempt_at) < timedelta(minutes=1)):
        candidates = collection_health.counts.get("eligible_candidates")
        if candidates is not None:
            feeds["eligible_candidates"] = candidates
    monitor = read_news_monitoring(db)
    active = len(selected_news_sources(db))
    progress = runtime.last_progress_at or runtime.last_started_at
    interrupted = runtime.error_code == "worker_interrupted" or bool(
        runtime.running and progress and now - progress > timedelta(minutes=12))
    running = runtime.running and not interrupted
    due = next_collection_due(latest_at, decision.interval_minutes) if latest_at and config.news_collection_enabled and active else None
    overdue = bool(due and not running and now > due + timedelta(minutes=runtime.scheduler_tick_minutes))
    last_cycle = runtime.last_cycle
    stage_label = STAGE_LABELS.get(runtime.current_stage)
    if runtime.current_stage == "publication" and not config.news_publication_enabled:
        stage_label = "Updating flood statuses"
    # Older workers only persisted completion totals. Never label their old
    # totals as belonging to a new, currently running cycle.
    if last_cycle is None and not running and runtime.last_started_at and runtime.last_finished_at:
        if runtime.last_finished_at >= runtime.last_started_at:
            last_cycle = NewsCycleSummary(started_at=runtime.last_started_at, finished_at=runtime.last_finished_at,
                outcome="requires_attention" if runtime.error_code else "completed",
                counts=runtime.stage_counts, error_code=runtime.error_code)
    if last_cycle is not None:
        last_cycle = last_cycle.model_copy(deep=True)
        footprints = last_cycle.counts.get("footprints", {})
        if "activated" in footprints or "estimated_activated" in footprints:
            footprints["total_activated"] = footprints.get("activated", 0) + footprints.get("estimated_activated", 0)
    if interrupted:
        state, label = "interrupted", "Worker status is stale"
    elif running:
        state, label = "running", stage_label or "Worker running"
    elif runtime.error_code:
        state, label = "requires_attention", "Last cycle needs attention"
    elif not any((config.news_collection_enabled, config.news_processing_enabled, config.news_publication_enabled)):
        state, label = "paused", "News automation paused"
    elif overdue:
        state, label = "overdue", "Collection overdue"
    elif due and now >= due:
        state, label = "due", "Collection due; waiting for worker"
    elif any(feeds.get(key, 0) for key in ("feed_errors", "body_errors", "scope_unresolved")):
        state, label = "partial", "Latest collection needs attention"
    elif runtime.last_finished_at:
        state, label = "idle", "Idle; last cycle finished"
    else:
        state, label = "not_recorded", "No worker cycle recorded"
    audit = read_audit_diagnostics(db)
    return NewsAutomationStatus(checked_at=now, state=state, status_label=label, running=running, audit=audit,
        current_stage=runtime.current_stage if running else None,
        stage_label=stage_label if running else None,
        stage_started_at=runtime.stage_started_at if running else None, last_progress_at=runtime.last_progress_at,
        collection_enabled=config.news_collection_enabled, processing_enabled=config.news_processing_enabled,
        publication_enabled=config.news_publication_enabled, enabled_sources=active,
        collection_interval_minutes=decision.interval_minutes, weather=weather,
        scheduler_tick_target_minutes=runtime.scheduler_tick_minutes, next_collection_due_at=due,
        collection_overdue=overdue, last_started_at=runtime.last_started_at, last_finished_at=runtime.last_finished_at,
        last_successful_at=runtime.last_successful_at, last_cycle=last_cycle, recent_cycles=runtime.recent_cycles, stages=runtime.stages,
        latest_collection_at=latest_at, feed_counts=feeds,
        queue_counts=monitor.latest_processing_counts,
        error_code="worker_interrupted" if interrupted else runtime.error_code)


def read_audit_diagnostics(db: Session) -> NewsAuditDiagnostics:
    from app.services.news_audit_quota_service import read_quota, quota_identity, deadline, real_now
    from app.services.news_claim_auditor import NewsClaimAuditor, AuditorConfigurationError
    try:
        auditor = NewsClaimAuditor()
    except AuditorConfigurationError as exc:
        return NewsAuditDiagnostics(state="requires_attention",error_code=exc.code)
    if auditor.config.error_code():
        return NewsAuditDiagnostics(state="requires_attention",error_code=auditor.config.error_code(),
            validation_mode="source_rules" if auditor.config.provider=="source_rules" else "llm")
    quota = read_quota(db, identity=quota_identity(auditor))
    from app.services.news_audit_availability_service import read_availability
    availability = read_availability(db, auditor)
    model_until = deadline(availability.blocked_until)
    transport = availability.last_transport
    from app.services.barangay_boundary_service import get_barangay_boundary_provider
    from app.services.philippine_location_service import get_philippine_location_service
    boundaries = get_barangay_boundary_provider()
    locations = get_philippine_location_service()
    expected_boundaries = len({entry["psgc_code"] for entries in locations.barangays.values() for entry in entries
        if entry.get("region") == "National Capital Region (NCR)"})
    blocked = deadline(quota.blocked_until)
    gemini = auditor.config.provider == "gemini"
    checked_at = (availability.last_checked_at or quota.checked_at) if gemini else quota.checked_at
    availability_state = ("unknown" if availability.last_error else "available") if gemini else (
        "unknown" if quota.checked_at and quota.remaining is None else "available")
    audit = NewsAuditDiagnostics(state="cooldown" if blocked and blocked > real_now() else
        "model_cooldown" if model_until and model_until > real_now() else
        "awaiting_check" if blocked else
        "awaiting_model_check" if model_until else
        availability_state if checked_at else "not_recorded",
        checked_at=deadline(checked_at), next_check_at=blocked,
        used=None if gemini else quota.used, limit=None if gemini else quota.limit,
        remaining=None if gemini else quota.remaining, request_count=quota.request_count,
        claims_dispatched=quota.claims_dispatched,
        http_status=availability.last_http_status if gemini else quota.http_status,
        error_code=quota.error_code or availability.last_error, model_next_check_at=model_until,
        failure_phase=transport.phase if transport and transport.phase != "complete" else None,
        timeout_kind=transport.timeout_kind if transport else None,
        elapsed_ms=transport.elapsed_ms if transport else None,
        actual_model=transport.actual_model if transport else None,
        boundary_qualified=len(boundaries.records), boundary_expected=expected_boundaries,
        boundary_missing=max(0, expected_boundaries-len(boundaries.records)), boundary_error=boundaries.error)
    if auditor.config.provider == "source_rules":
        audit = NewsAuditDiagnostics(state="available" if not auditor.config.error_code() else "requires_attention",
            validation_mode="source_rules", error_code=auditor.config.error_code(),
            boundary_qualified=len(boundaries.records), boundary_expected=expected_boundaries,
            boundary_missing=max(0, expected_boundaries-len(boundaries.records)), boundary_error=boundaries.error)
    return audit
