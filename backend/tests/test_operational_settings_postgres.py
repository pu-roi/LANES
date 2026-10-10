"""Writes are confined to a fresh, disposable local database named lanes_settings_test_* ."""
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString
import pytest
from sqlalchemy import create_engine, inspect, select, func, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app import models
from app.models.audit import AuditLog
from app.models.report import HazardPresence
from app.models.setting import SystemSetting
from app.schemas.configuration import OperationalSettings, ConfigurationUpdate
from app.services import configuration_service as settings
from app.services.citizen_approval_service import approve_citizen_report, record_observation, human_history, APPROVAL_ACTION

NOW = datetime.now(timezone.utc)
LINE = LineString([(121.08, 14.57), (121.0805, 14.5705)])




@pytest.fixture
def isolated_db(settings_factory):
    engine = settings_factory.kw["bind"]
    with engine.connect() as connection:
        transaction = connection.begin()
        db = settings_factory(bind=connection, join_transaction_mode="create_savepoint")
        role = models.Role(name="admin", permissions={"settings": "full", "reports": "full", "zones": "full"})
        db.add(role); db.flush()
        admin = models.User(username="settings-admin", email="settings@example.invalid", hashed_password="fixture", role_id=role.id)
        db.add(admin); db.commit()
        try:
            yield db, admin
        finally:
            db.close()
            transaction.rollback()


def citizen(db, role_id):
    token = uuid4().hex
    user = models.User(username=token, email=token+"@example.invalid", hashed_password="fixture", role_id=role_id)
    db.add(user); db.flush()
    db.add(models.Profile(user_id=user.id, first_name="Fixture", last_name="Citizen", trust_score=75, reports_approved=5, accuracy_rate=100))
    db.commit()
    return user


def report(db, user, description="Observed knee-deep flooding", geometry=LINE):
    item = models.FloodReport(user_id=user.id, raw_text=description, source=models.ReportSource.USER_REPORT,
        severity=models.ReportSeverity.MEDIUM, depth="knee", status=models.ReportStatus.PENDING,
        city="Pasig", barangay="Maybunga", human_readable_location="Fixture road", geometry=from_shape(geometry, srid=4326))
    db.add(item); db.flush()
    db.add(models.FloodReportSurvey(report_id=item.id, passable_vehicles="Truck", hidden_hazards=HazardPresence.NO))
    db.commit(); db.refresh(item)
    return item


def reviewed_history(db, user, admin):
    for index in range(5):
        old = report(db, user, str(index))
        old.status = models.ReportStatus.APPROVED
        db.add(models.FloodReportModerationOutcome(report_id=old.id, outcome=models.ReportModerationOutcomeType.APPROVED, acted_by_user_id=admin.id))
    db.commit()


def enable(db, admin):
    config = OperationalSettings(citizen_auto_approval_enabled=True)
    return settings.save_configuration(db, ConfigurationUpdate(revision=0, settings=config), actor_id=admin.id)


def test_save_audits_and_conflicts_without_partial_writes(isolated_db):
    db, admin = isolated_db
    result = enable(db, admin)
    assert result.revision == 1
    assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action_type == "UPDATE_SETTINGS")) == 1
    with pytest.raises(settings.ConfigurationConflict):
        settings.save_configuration(db, ConfigurationUpdate(revision=0, settings=OperationalSettings()), actor_id=admin.id)
    assert settings.read_configuration(db).citizen_auto_approval_enabled


def test_failed_audit_rolls_back_settings(isolated_db, monkeypatch):
    db, admin = isolated_db
    def fail(*args, **kwargs):
        raise RuntimeError("synthetic audit failure")
    monkeypatch.setattr(settings, "create_audit_log", fail)
    with pytest.raises(RuntimeError):
        enable(db, admin)
    assert db.get(SystemSetting, settings.CONFIG_KEY) is None


def test_two_independent_reporters_create_one_finite_zone_without_credit(isolated_db):
    db, admin = isolated_db
    enable(db, admin)
    first, second = citizen(db, admin.role_id), citizen(db, admin.role_id)
    reviewed_history(db, first, admin); reviewed_history(db, second, admin)
    a = report(db, first, "I observed knee deep water blocking this road")
    b = report(db, second, "Water is at my knees on the affected section")
    for item in (a,b):
        record_observation(db, item, observed_at=NOW, road_validated=True, media_hashes=[])
    assert approve_citizen_report(db, a.id, now=NOW) == "independent_citizen_observations_agree"
    db.refresh(a); db.refresh(b)
    assert a.zone_id == b.zone_id and a.status == b.status == models.ReportStatus.APPROVED
    zone = db.get(models.FloodAvoidanceZone, a.zone_id)
    assert zone.expires_at == NOW + timedelta(hours=2)
    db.refresh(first.profile)
    assert first.profile.trust_score == 75 and first.profile.reports_approved == 5
    assert human_history(db, first.id) == (5, 100)
    assert approve_citizen_report(db, b.id, now=NOW) == "report_already_reviewed"
    assert db.scalar(select(func.count()).select_from(models.FloodAvoidanceZone)) == 1
    assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action_type == APPROVAL_ACTION)) == 2


@pytest.mark.parametrize("problem,expected", [("missing_time","explicit_observation_time_required"),
    ("stale","observation_not_current"),("future","observation_not_current"),
    ("unvalidated","road_geometry_not_validated"),("low_trust","trust_below_threshold"),
    ("no_human_history","human_review_history_below_threshold")])
def test_ineligible_evidence_stays_pending(isolated_db, problem, expected):
    db, admin = isolated_db; enable(db, admin)
    user = citizen(db, admin.role_id)
    if problem != "no_human_history": reviewed_history(db, user, admin)
    item = report(db, user)
    if problem == "low_trust": user.profile.trust_score = 74; db.commit()
    observed = None if problem == "missing_time" else NOW-timedelta(minutes=31) if problem == "stale" else NOW+timedelta(minutes=1) if problem == "future" else NOW
    record_observation(db, item, observed_at=observed, road_validated=problem != "unvalidated", media_hashes=[])
    assert approve_citizen_report(db, item.id, now=NOW) == expected
    db.refresh(item); assert item.status == models.ReportStatus.PENDING


def test_copied_media_does_not_supply_independent_support(isolated_db):
    db, admin = isolated_db; enable(db, admin)
    first, second = citizen(db, admin.role_id), citizen(db, admin.role_id)
    for user in (first, second): reviewed_history(db, user, admin)
    a,b = report(db, first, "Observation one"), report(db, second, "Observation two")
    for item in (a,b): record_observation(db, item, observed_at=NOW, road_validated=True, media_hashes=["same-capture"])
    assert approve_citizen_report(db, a.id, now=NOW) == "waiting_for_independent_corroboration"
    assert db.scalar(select(func.count()).select_from(models.FloodAvoidanceZone)) == 0


def qualifying_pair(db, admin):
    enable(db, admin)
    first, second = citizen(db, admin.role_id), citizen(db, admin.role_id)
    for user in (first, second):
        reviewed_history(db, user, admin)
    a, b = report(db, first, "Current observation one"), report(db, second, "Current observation two")
    for item in (a, b):
        record_observation(db, item, observed_at=NOW, road_validated=True, media_hashes=[])
    return a, b


def test_new_zone_uses_only_continuous_common_section(isolated_db):
    from geoalchemy2.shape import to_shape
    db, admin = isolated_db
    a, b = qualifying_pair(db, admin)
    a.geometry = from_shape(LineString([(121.08, 14.57), (121.08025, 14.5703), (121.0805, 14.5705)]), srid=4326)
    b.geometry = from_shape(LineString([(121.08025, 14.5703), (121.0805, 14.5705)]), srid=4326)
    db.commit()
    record_observation(db, a, observed_at=NOW, road_validated=True, media_hashes=[])
    record_observation(db, b, observed_at=NOW, road_validated=True, media_hashes=[])
    assert approve_citizen_report(db, a.id, now=NOW) == "independent_citizen_observations_agree"
    zone = db.get(models.FloodAvoidanceZone, a.zone_id)
    assert to_shape(zone.source_geometry).equals(to_shape(b.geometry))
    assert to_shape(zone.source_geometry).length < to_shape(a.geometry).length


@pytest.mark.parametrize("problem", ["unknown_depth", "wrong_severity", "light_vehicle_conflict", "contradiction", "copied_text", "same_reporter"])
def test_ambiguous_or_inconsistent_pair_does_not_create_zone(isolated_db, problem):
    db, admin = isolated_db
    a, b = qualifying_pair(db, admin)
    if problem == "unknown_depth": b.depth = None
    if problem == "wrong_severity": b.severity = models.ReportSeverity.HIGH
    if problem == "light_vehicle_conflict": b.survey.passable_vehicles = "Sedans / Hatchbacks"
    if problem == "contradiction": b.survey.hidden_hazards = HazardPresence.YES
    if problem == "copied_text": b.raw_text = a.raw_text
    if problem == "same_reporter": b.user_id = a.user_id
    db.commit()
    approve_citizen_report(db, a.id, now=NOW)
    assert db.scalar(select(func.count()).select_from(models.FloodAvoidanceZone)) == 0
    assert a.status == b.status == models.ReportStatus.PENDING


def test_fresh_existing_support_refreshes_only_its_saved_policy(isolated_db):
    from app.services.flood_event_service import expire_due_zones
    from app.services.citizen_approval_service import has_active_citizen_support
    db, admin = isolated_db
    a, b = qualifying_pair(db, admin)
    approve_citizen_report(db, a.id, now=NOW)
    zone = db.get(models.FloodAvoidanceZone, a.zone_id)
    original = zone.expires_at
    config = settings.read_configuration(db)
    config.evidence_expiry_minutes["knee"] = 30
    settings.save_configuration(db, ConfigurationUpdate(revision=1, settings=config), actor_id=admin.id)
    db.refresh(zone)
    assert zone.expires_at == original  # A settings edit never extends/revives old evidence.
    person = citizen(db, admin.role_id); reviewed_history(db, person, admin)
    c = report(db, person, "Fresh independent current observation")
    record_observation(db, c, observed_at=NOW + timedelta(minutes=110), road_validated=True, media_hashes=[])
    assert approve_citizen_report(db, c.id, now=NOW + timedelta(minutes=110)) == "existing_zone_corroborated"
    db.refresh(zone)
    assert zone.expires_at == NOW + timedelta(minutes=140)
    assert has_active_citizen_support(db, zone.id, NOW + timedelta(minutes=125))
    assert not has_active_citizen_support(db, zone.id, NOW + timedelta(minutes=141))
    assert expire_due_zones(db, NOW + timedelta(minutes=141)) == 1
    assert not zone.is_active
    assert db.scalar(select(models.FloodEventTimelineEntry).where(
        models.FloodEventTimelineEntry.entry_type == "evidence_expired")).snapshot_json["condition"] == "Unconfirmed"


def test_human_review_accuracy_is_enforced_instead_of_profile_cache(isolated_db):
    db, admin = isolated_db; enable(db, admin)
    user = citizen(db, admin.role_id); reviewed_history(db, user, admin)
    old = report(db, user, "Human-reviewed rejected evidence")
    old.status = models.ReportStatus.REJECTED
    db.add(models.FloodReportModerationOutcome(report_id=old.id, outcome=models.ReportModerationOutcomeType.REJECTED,
        acted_by_user_id=admin.id, rejection_reason=models.ReportRejectionReason.INSUFFICIENT_EVIDENCE))
    db.commit()
    current = report(db, user)
    record_observation(db, current, observed_at=NOW, road_validated=True, media_hashes=[])
    assert user.profile.accuracy_rate == 100
    assert approve_citizen_report(db, current.id, now=NOW) == "human_review_history_below_threshold"


@pytest.mark.asyncio
async def test_failed_road_reconstruction_preserves_manual_report_without_auto_qualification(isolated_db, monkeypatch):
    from app.services import report_service
    from app.services.citizen_approval_service import observation
    db, admin = isolated_db; enable(db, admin)
    user = citizen(db, admin.role_id); reviewed_history(db, user, admin)
    def unavailable(*args): raise RuntimeError("synthetic road provider unavailable")
    monkeypatch.setattr(report_service, "validate_report_road_geometry", unavailable)
    result = await report_service.process_new_report(db=db, user_id=user.id, raw_text="Current knee-deep flood",
        source="direct_user", severity="medium", depth="knee", is_public=False,
        human_readable_location="Fixture road", city="Pasig", barangay="Maybunga",
        geometry={"type":"LineString","coordinates":list(LINE.coords)}, observed_at=NOW,
        survey_data={"passable_vehicles":"Large Trucks / Buses","hidden_hazards":"no"})
    assert result.status == models.ReportStatus.PENDING
    assert result.automatic_review_reason == "road_geometry_not_validated"
    assert not observation(db, result.id)["road_validated"]
    assert result.geometry is not None


@pytest.mark.asyncio
async def test_configuration_http_permissions_validation_and_legacy_contract(isolated_db, monkeypatch):
    from app.main import app
    from app.api import deps
    from app.core.database import get_db
    import httpx
    db, admin = isolated_db
    previous = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[deps.get_current_user] = lambda: admin
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://fixture") as client:
            path = "/api/v1/admin/settings/configuration"
            response = await client.get(path)
            assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
            assert response.json()["settings"]["automatic_expiry_enabled"] is True
            assert response.json()["supported_options"]["collection_intervals_minutes"] == [15,30,60]
            db.add(SystemSetting(key="legacy_fixture", value=0.5)); db.commit()
            payload = {"revision": 0, "settings": OperationalSettings(staff_road_buffer_metres=30, automatic_expiry_enabled=False).model_dump()}
            assert (await client.put(path, json={**payload, "unknown": True})).status_code == 422
            assert (await client.put(path, json=payload)).status_code == 200
            assert (await client.get(path)).json()["settings"]["automatic_expiry_enabled"] is False
            saved = db.get(SystemSetting, settings.CONFIG_KEY)
            assert saved.value["automatic_expiry_enabled"] is False
            assert "automatic_expiry_enabled" not in saved.value["settings"]
            audit = db.scalar(select(AuditLog).where(AuditLog.action_type == "UPDATE_SETTINGS").order_by(AuditLog.id.desc()))
            assert audit.metadata_json["before"]["automatic_expiry_enabled"] is True
            assert audit.metadata_json["after"]["automatic_expiry_enabled"] is False
            assert (await client.put(path, json=payload)).status_code == 409
            legacy = await client.get("/api/v1/admin/settings")
            assert legacy.json()["legacy_fixture"] == 0.5
            assert settings.CONFIG_KEY not in legacy.json()
            assert (await client.put("/api/v1/admin/settings", json={})).status_code == 410
            admin.role.permissions = {"settings": "view"}
            assert not (await client.get(path)).json()["can_edit"]
            assert (await client.put(path, json=payload)).status_code == 403
            admin.role.permissions = {}
            assert (await client.get(path)).status_code == 403
            assert (await client.put(path, json=payload)).status_code == 403
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


@pytest.mark.asyncio
async def test_explicit_staff_deadline_is_not_extended_by_citizen_support(isolated_db):
    import httpx
    from app.main import app
    from app.api import deps
    from app.core.database import get_db
    db, admin = isolated_db
    a, b = qualifying_pair(db, admin)
    approve_citizen_report(db, a.id, now=NOW)
    zone = db.get(models.FloodAvoidanceZone, a.zone_id)
    deadline = NOW + timedelta(minutes=60)
    previous = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[deps.get_current_active_admin] = lambda: admin
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://fixture") as client:
            response = await client.patch(f"/api/v1/admin/zones/{zone.id}", json={"expires_at":deadline.isoformat()})
            assert response.status_code == 200, response.text
        db.refresh(zone)
        assert zone.curated_by_admin_id == admin.id and zone.expires_at == deadline
        user = citizen(db, admin.role_id); reviewed_history(db, user, admin)
        current = report(db, user, "Fresh independent evidence with a staff-managed deadline")
        record_observation(db, current, observed_at=NOW+timedelta(minutes=50), road_validated=True, media_hashes=[])
        assert approve_citizen_report(db, current.id, now=NOW+timedelta(minutes=50)) == "existing_zone_corroborated"
        db.refresh(zone)
        assert zone.expires_at == deadline
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


@pytest.mark.asyncio
async def test_scheduler_cadence_publishers_overlap_pause_and_failure(settings_factory, monkeypatch):
    from types import SimpleNamespace
    from app.services import news_scheduler_service as worker
    from app.models.news_telemetry import NewsDiscoveryRun
    from app.services.news_sources import load_news_sources
    now = [datetime.now(timezone.utc)]
    collected = []
    pipeline_calls = []
    source = load_news_sources()[0]

    def collect(sources, client, db):
        collected.append(tuple(item.id for item in sources))
        db.add(NewsDiscoveryRun(trigger="collector", status="completed", started_at=now[0], finished_at=now[0]))
        db.commit()
        return SimpleNamespace(probes=[SimpleNamespace(entry_count=94, status="parsed")], candidates=[])

    async def pipeline(factory, **kwargs):
        pipeline_calls.append(now[0])
        with factory() as db:
            config = settings.read_configuration(db)
        return {"extraction": {"completed": 0}, "evaluation": {"completed": 0}, "publication": {"expired": 0},
            "stage_outcomes": {"processing": "enabled" if config.news_processing_enabled else "paused",
                "publication": "enabled" if config.news_publication_enabled else "paused"}}

    monkeypatch.setattr(worker, "discover_news", collect)
    monkeypatch.setattr(worker, "run_news_pipeline", pipeline)
    with settings_factory() as db:
        token = uuid4().hex
        role = models.Role(name=token, permissions={"settings": "full"}); db.add(role); db.flush()
        admin = models.User(username=token, email=token+"@example.invalid", hashed_password="fixture", role_id=role.id)
        db.add(admin); db.commit()
        actor_id = admin.id
        config = OperationalSettings(news_source_ids=[source.id])
        settings.save_configuration(db, ConfigurationUpdate(revision=0, settings=config), actor_id=actor_id)
    tick = lambda: worker.run_scheduled_news_tick(settings_factory, sources=load_news_sources(), clock=lambda: now[0])
    assert (await tick())["outcome"] == "completed"
    await tick()  # Duplicate delivery does not repeat RSS retrieval.
    assert collected == [(source.id,)]
    now[0] += timedelta(minutes=15)
    await tick()
    assert len(collected) == 1
    now[0] += timedelta(minutes=15)
    await tick()
    assert len(collected) == 2
    with settings_factory() as db:
        response = settings.configuration_response(db, can_edit=True)
        assert response.runtime.stages["collection"].counts == {"entries_read": 94, "eligible_candidates": 0}
        config.news_collection_interval_minutes = 15
        settings.save_configuration(db, ConfigurationUpdate(revision=response.revision, settings=config), actor_id=actor_id)
    now[0] += timedelta(minutes=15)
    await tick()
    assert len(collected) == 3
    with settings_factory() as holder:
        connection = holder.connection()
        connection.execute(text("SELECT pg_advisory_lock(:key)"), {"key": worker.WORKER_LOCK})
        try:
            assert (await tick())["outcome"] == "already_running"
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": worker.WORKER_LOCK})
    with settings_factory() as db:
        config.news_collection_enabled = config.news_processing_enabled = config.news_publication_enabled = False
        response = settings.configuration_response(db, can_edit=True)
        settings.save_configuration(db, ConfigurationUpdate(revision=response.revision, settings=config), actor_id=actor_id)
    now[0] += timedelta(minutes=15)
    result = await tick()
    assert result["stage_outcomes"] == {"processing": "paused", "publication": "paused"}
    assert len(collected) == 3 and len(pipeline_calls) == 6  # Maintenance remains independent.
    with settings_factory() as db:
        assert settings.configuration_response(db, can_edit=True).runtime.stage_outcomes["collection"] == "paused"
        config.news_collection_enabled = True
        response = settings.configuration_response(db, can_edit=True)
        settings.save_configuration(db, ConfigurationUpdate(revision=response.revision, settings=config), actor_id=actor_id)
    def failing_collection(*args): raise RuntimeError("synthetic provider failure")
    monkeypatch.setattr(worker, "discover_news", failing_collection)
    assert (await tick())["outcome"] == "requires_attention"
    with settings_factory() as db:
        runtime = settings.configuration_response(db, can_edit=True).runtime
        assert not runtime.running and runtime.error_code == "pipeline_requires_attention"
        assert runtime.stages["collection"].errors == ["collection_failed"]


def test_concurrent_administrators_cannot_overwrite_each_other(settings_factory):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    with settings_factory() as db:
        stored = db.get(SystemSetting, settings.CONFIG_KEY)
        if stored is None:
            token = uuid4().hex
            role = models.Role(name=token, permissions={"settings":"full"}); db.add(role); db.flush()
            user = models.User(username=token, email=token+"@example.invalid", hashed_password="fixture", role_id=role.id)
            db.add(user); db.commit()
            settings.save_configuration(db, ConfigurationUpdate(revision=0, settings=OperationalSettings(staff_road_buffer_metres=26)), actor_id=user.id)
            stored = db.get(SystemSetting, settings.CONFIG_KEY)
        actor_id, revision = stored.last_updated_by, stored.value["revision"]
        original = settings.read_configuration(db)
    barrier = Barrier(2)
    def save(value):
        config = original.model_copy(update={"staff_road_buffer_metres": value})
        barrier.wait(timeout=10)
        with settings_factory() as db:
            try:
                return settings.save_configuration(db, ConfigurationUpdate(revision=revision, settings=config), actor_id=actor_id).revision
            except settings.ConfigurationConflict:
                return "conflict"
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(save, value) for value in (40,45)]
        outcomes = [future.result(timeout=15) for future in futures]
    assert outcomes.count("conflict") == 1 and outcomes.count(revision+1) == 1
    with settings_factory() as db:
        assert settings.read_configuration(db).staff_road_buffer_metres in (40,45)
        settings.save_configuration(db, ConfigurationUpdate(revision=revision+1, settings=original), actor_id=actor_id)
