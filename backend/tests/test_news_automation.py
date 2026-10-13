"""Read-only status, honest due times and durable progress on isolated fixtures."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import httpx
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.api import deps
from app.core.database import get_db
from app.main import app
from app.models.setting import SystemSetting
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.models.news_telemetry import NewsDiscoveryRun, NewsDiscoveryFeedRun
from app.schemas.configuration import ConfigurationRuntime, OperationalSettings
from app.services.configuration_service import CONFIG_KEY, RUNTIME_KEY
from app.services.news_automation_service import read_news_automation


@compiles(JSONB, "sqlite")
def jsonb_sqlite(_type, _compiler, **_kwargs):
    return "JSON"


@pytest.fixture
def status_db():
    engine = create_engine("sqlite+pysqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    tables = [SystemSetting.__table__, NewsArticle.__table__, NewsArticleVersion.__table__,
              NewsExtractionRun.__table__, NewsDiscoveryRun.__table__, NewsDiscoveryFeedRun.__table__]
    SystemSetting.metadata.create_all(engine, tables=tables)
    with Session(engine) as db:
        yield db
    engine.dispose()


def save_runtime(db, now, **changes):
    runtime = ConfigurationRuntime(last_started_at=now-timedelta(minutes=2), last_finished_at=now-timedelta(minutes=1),
        last_successful_at=now-timedelta(minutes=1), **changes)
    db.add(SystemSetting(key=RUNTIME_KEY, value=runtime.model_dump(mode="json")))
    db.commit()
    return runtime


def test_collection_due_is_not_claimed_as_actual_next_scheduler_run(status_db):
    now = datetime(2026, 10, 13, 15, 4, 27, tzinfo=timezone.utc)
    save_runtime(status_db, now)
    status_db.add(NewsDiscoveryRun(trigger="collector", status="completed", started_at=now-timedelta(hours=2),
                                    finished_at=now-timedelta(hours=2)+timedelta(seconds=15)))
    status_db.commit()
    result = read_news_automation(status_db, now=now)
    assert result.state == "overdue" and result.collection_overdue
    assert result.next_collection_due_at == datetime(2026, 10, 13, 13, 30, tzinfo=timezone.utc)
    assert result.scheduler_tick_target_minutes == 15
    assert not result.running and result.last_cycle.outcome == "completed"


@pytest.mark.parametrize("stage,label", [("collection", "Gathering news"), ("extraction", "Processing articles"),
                                        ("footprints", "Plotting qualified flood areas")])
def test_running_stage_requires_saved_progress(status_db, stage, label):
    now = datetime.now(timezone.utc)
    save_runtime(status_db, now, running=True, current_stage=stage, last_progress_at=now)
    result = read_news_automation(status_db, now=now)
    assert result.running and result.status_label == label
    assert result.last_cycle is None  # Previous totals cannot describe this running cycle.


def test_stale_progress_is_interrupted_not_permanent_loading(status_db):
    now = datetime.now(timezone.utc)
    save_runtime(status_db, now, running=True, current_stage="evaluation", last_progress_at=now-timedelta(minutes=13))
    result = read_news_automation(status_db, now=now)
    assert not result.running and result.current_stage is None
    assert result.state == "interrupted" and result.error_code == "worker_interrupted"


def test_paused_settings_keep_due_time_absent_and_maintenance_honest(status_db):
    now = datetime.now(timezone.utc)
    config = OperationalSettings(news_collection_enabled=False, news_processing_enabled=False, news_publication_enabled=False)
    status_db.add(SystemSetting(key=CONFIG_KEY, value={"revision": 1, "settings": config.model_dump(mode="json")}))
    runtime = save_runtime(status_db, now)
    assert read_news_automation(status_db, now=now).state == "paused"
    assert read_news_automation(status_db, now=now).next_collection_due_at is None
    row = status_db.get(SystemSetting, RUNTIME_KEY)
    runtime.running, runtime.current_stage, runtime.last_progress_at = True, "publication", now
    row.value = runtime.model_dump(mode="json")
    status_db.commit()
    assert read_news_automation(status_db, now=now).status_label == "Updating flood statuses"


def test_feed_success_does_not_hide_body_errors_or_invent_flood_candidates(status_db):
    now = datetime.now(timezone.utc)
    save_runtime(status_db, now)
    run = NewsDiscoveryRun(trigger="collector", status="completed", started_at=now-timedelta(minutes=2),
                           finished_at=now-timedelta(minutes=1))
    status_db.add(run); status_db.flush()
    status_db.add(NewsDiscoveryFeedRun(discovery_run_id=run.id, source_id="daily-tribune", feed_url="https://example.invalid/rss",
        status="parsed", checked_at=now, entries_seen=30, candidates_saved=3, body_errors=2, scope_unresolved=2))
    status_db.commit()
    writes = []
    def record(_conn, _cursor, statement, *_args):
        if statement.lstrip().split()[0].upper() in ("INSERT", "UPDATE", "DELETE"):
            writes.append(statement)
    event.listen(status_db.get_bind(), "before_cursor_execute", record)
    result = read_news_automation(status_db, now=now)
    assert result.feed_counts["feed_errors"] == 0
    assert result.feed_counts["body_errors"] == 2 and result.feed_counts["scope_unresolved"] == 2
    assert result.feed_counts["articles_saved_or_seen"] == 3
    assert "eligible_candidates" not in result.feed_counts  # Saved commuter articles are not flood candidates.
    assert writes == []


def test_activation_total_includes_estimated_roads_without_changing_saved_counts(status_db):
    now = datetime.now(timezone.utc)
    save_runtime(status_db, now, stage_counts={"footprints": {"activated": 1, "estimated_activated": 2}})
    result = read_news_automation(status_db, now=now)
    assert result.last_cycle.counts["footprints"]["total_activated"] == 3
    assert "total_activated" not in status_db.get(SystemSetting, RUNTIME_KEY).value["stage_counts"]["footprints"]


@pytest.mark.asyncio
async def test_status_endpoint_enforces_staff_and_get_never_collects(status_db, monkeypatch):
    from app.services import news_discovery_service
    def unexpected(*args, **kwargs):
        raise AssertionError("A status GET must not collect news")
    monkeypatch.setattr(news_discovery_service, "discover_news", unexpected)
    previous = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = lambda: status_db
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://fixture") as client:
            assert (await client.get("/api/v1/admin/news/automation")).status_code == 401
            app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(is_active=True, role=SimpleNamespace(name="Commuter"))
            assert (await client.get("/api/v1/admin/news/automation")).status_code == 403
            app.dependency_overrides[deps.get_current_active_admin] = lambda: object()
            response = await client.get("/api/v1/admin/news/automation")
            assert response.status_code == 200, response.text
            assert response.headers["cache-control"] == "no-store"
            assert response.json()["state"] == "not_recorded"
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
