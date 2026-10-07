"""Shared database policy, atomic configuration changes and bounded run status."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.crud.audit import create_audit_log
from app.models.setting import SystemSetting
from app.schemas.audit import AuditLogCreate
from app.schemas.configuration import ConfigurationResponse, ConfigurationRuntime, ConfigurationUpdate, OperationalSettings, NewsStageHealth
from app.services.flood_depth import FLOOD_DEPTH_MEASUREMENTS, normalize_flood_depth
from app.services.news_sources import NewsSource, load_news_sources

CONFIG_KEY = "operational_configuration_v1"
RUNTIME_KEY = "news_automation_runtime_v1"
CONFIG_LOCK = 614296501


class ConfigurationConflict(ValueError):
    pass


def configuration_lock(db: Session) -> None:
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": CONFIG_LOCK})


def read_configuration(db: Session) -> OperationalSettings:
    row = db.get(SystemSetting, CONFIG_KEY, populate_existing=True)
    return OperationalSettings.model_validate(row.value["settings"], context={"persisted_history": True}) if row else OperationalSettings()


def selected_news_sources(db: Session, sources: tuple[NewsSource, ...] | None = None) -> tuple[NewsSource, ...]:
    sources = load_news_sources() if sources is None else sources
    config = read_configuration(db)
    configured = db.get(SystemSetting, CONFIG_KEY) is not None
    return tuple(s for s in sources if s.enabled and s.verified_at
                 and (not configured or s.id in config.news_source_ids))


def evidence_deadline(config: OperationalSettings, observed_at: datetime, depth: str | None) -> datetime:
    key = normalize_flood_depth(depth) or "unknown"
    return observed_at + timedelta(minutes=config.evidence_expiry_minutes[key])


def configuration_response(db: Session, *, can_edit: bool) -> ConfigurationResponse:
    config = read_configuration(db)
    row = db.get(SystemSetting, CONFIG_KEY)
    runtime_row = db.get(SystemSetting, RUNTIME_KEY)
    runtime = ConfigurationRuntime.model_validate(runtime_row.value) if runtime_row else ConfigurationRuntime()
    if runtime.last_started_at and datetime.now(timezone.utc) - runtime.last_started_at > timedelta(minutes=12):
        if runtime.running:
            runtime.running = False
            runtime.error_code = "worker_interrupted"
    from app.models.news_telemetry import NewsDiscoveryRun, NewsDiscoveryFeedRun
    from sqlalchemy import select
    latest = db.scalar(select(NewsDiscoveryRun).where(NewsDiscoveryRun.trigger == "collector")
        .order_by(NewsDiscoveryRun.started_at.desc()).limit(1))
    if latest and "collection" not in runtime.stages:
        feeds = list(db.scalars(select(NewsDiscoveryFeedRun).where(NewsDiscoveryFeedRun.discovery_run_id == latest.id)))
        successful = db.scalar(select(NewsDiscoveryRun.finished_at).where(NewsDiscoveryRun.trigger == "collector",
            NewsDiscoveryRun.status == "completed").order_by(NewsDiscoveryRun.finished_at.desc()).limit(1))
        runtime.stages["collection"] = NewsStageHealth(last_attempt_at=latest.started_at,
            last_success_at=successful, outcome=latest.status,
            counts={"entries_read": sum(feed.entries_seen for feed in feeds),
                    "eligible_candidates": sum(feed.candidates_saved for feed in feeds)},
            errors=[feed.error_code for feed in feeds if feed.error_code])
    if latest and config.news_collection_enabled and selected_news_sources(db):
        runtime.next_collection_at = latest.started_at + timedelta(minutes=config.news_collection_interval_minutes)
    elif not config.news_collection_enabled or not selected_news_sources(db):
        runtime.next_collection_at = None
    return ConfigurationResponse(settings=config, revision=row.value["revision"] if row else 0,
        updated_at=row.updated_at if row else None, updated_by=row.last_updated_by if row else None,
        can_edit=can_edit, runtime=runtime,
        depth_options=[{"key": k, "label": v.display_label} for k, v in FLOOD_DEPTH_MEASUREMENTS.items()]
                      + [{"key": "unknown", "label": "Unknown depth"}],
        source_options=[{"id": s.id, "publisher": s.publisher} for s in load_news_sources() if s.enabled and s.verified_at])


def save_configuration(db: Session, update: ConfigurationUpdate, *, actor_id: int) -> ConfigurationResponse:
    try:
        configuration_lock(db)
        row = db.get(SystemSetting, CONFIG_KEY, populate_existing=True)
        revision = row.value["revision"] if row else 0
        if update.revision != revision:
            raise ConfigurationConflict("Settings changed elsewhere. Reload before saving your draft.")
        before = read_configuration(db).model_dump(mode="json")
        after = update.settings.model_dump(mode="json")
        if before != after:
            if row is None:
                row = SystemSetting(key=CONFIG_KEY)
                db.add(row)
            row.value = {"revision": revision + 1, "settings": after}
            row.last_updated_by = actor_id
            create_audit_log(db, AuditLogCreate(admin_id=actor_id, action_type="UPDATE_SETTINGS",
                target_table="system_settings", metadata_json={"revision": revision + 1, "before": before, "after": after}), commit=False)
        db.flush()
        result = configuration_response(db, can_edit=True)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


def write_runtime(db: Session, runtime: ConfigurationRuntime) -> None:
    row = db.get(SystemSetting, RUNTIME_KEY)
    if row is None:
        row = SystemSetting(key=RUNTIME_KEY)
        db.add(row)
    row.value = runtime.model_dump(mode="json")
    db.commit()
