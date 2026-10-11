"""Controller persistence/dispatch tests use the guarded disposable DB fixture."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4
import httpx
import pytest
from sqlalchemy import delete, text
from app.models.setting import SystemSetting
from app.models.news_telemetry import NewsDiscoveryRun
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.models.report import FloodEvent, FloodAvoidanceZone
from app.schemas.configuration import ConfigurationUpdate, OperationalSettings
from app.schemas.news_weather import NewsWeatherController, WeatherProvider
from app.services import news_weather_controller_service as controller
from app.services import configuration_service as settings
from app.crud.news_weather import CONTROLLER_KEY, read_controller, save_controller, current_flood_until
from app.services.news_weather_service import OPEN_METEO_URL, PAGASA_URL

NOW = datetime(2026,10,11,13,30,tzinfo=timezone.utc)


@pytest.fixture
def factory(settings_factory, monkeypatch):
    with settings_factory() as db:
        before={key:db.get(SystemSetting,key).value if db.get(SystemSetting,key) else None for key in (settings.CONFIG_KEY, CONTROLLER_KEY)}
        config=OperationalSettings(news_source_ids=["daily-tribune"])
        row=db.get(SystemSetting,settings.CONFIG_KEY) or SystemSetting(key=settings.CONFIG_KEY)
        row.value={"revision":0,"settings":config.model_dump(mode="json")};db.add(row)
        db.execute(delete(SystemSetting).where(SystemSetting.key==CONTROLLER_KEY));db.commit()
    monkeypatch.setattr(controller,"selected_news_sources",lambda db: [SimpleNamespace(id="daily-tribune")])
    monkeypatch.setattr(controller,"latest_collection_at",lambda db:NOW-timedelta(minutes=40))
    monkeypatch.setattr(controller,"current_flood_until",lambda db,now:None)
    monkeypatch.setattr(controller,"pending_pipeline_work",lambda *a,**kw:False)
    yield settings_factory
    with settings_factory() as db:
        for key,value in before.items():
            row=db.get(SystemSetting,key)
            if value is None:
                if row:db.delete(row)
            else:
                row=row or SystemSetting(key=key);row.value=value;db.add(row)
        db.commit()


class Gateway:
    def __init__(self,fail=False,result="finished"):
        self.starts=[];self.fail=fail;self.result=result;self.reconciled=[]
    def start(self,token):
        self.starts.append(token)
        if self.fail:raise httpx.ReadTimeout("uncertain accepted start")
        return "fixture-operation"
    def reconcile(self,token,operation,reserved_at):
        self.reconciled.append(token)
        return self.result


def signals(status="quiet"):
    return [WeatherProvider(name=name,source_url=url,checked_at=NOW,status=status) for name,url in (("Open-Meteo",OPEN_METEO_URL),("PAGASA",PAGASA_URL))]


def tick(factory,monkeypatch,gateway,now=NOW,status="quiet"):
    monkeypatch.setattr(controller,"fetch_weather",lambda client,now: [p.model_copy(update={"checked_at":now}) for p in signals(status)])
    with httpx.Client() as client:return controller.run_weather_tick(factory,now=now,client=client,gateway=gateway)


@pytest.mark.parametrize("signal,outcome",[("quiet","not_due"),("risk","dispatched"),("unavailable","dispatched")])
def test_adaptive_due_and_committed_reader_snapshot(factory,monkeypatch,signal,outcome):
    gateway=Gateway()
    assert tick(factory,monkeypatch,gateway,status=signal)["outcome"]==outcome
    with factory() as reader:
        state=read_controller(reader)
        assert state.last_tick_at==NOW and state.checks==1
        assert state.worker_starts==len(gateway.starts)


def test_duplicate_tick_and_running_execution_do_not_dispatch_twice(factory,monkeypatch):
    gateway=Gateway(result="running")
    assert tick(factory,monkeypatch,gateway,status="risk")["outcome"]=="dispatched"
    assert tick(factory,monkeypatch,gateway,status="risk")["outcome"]=="duplicate_tick"
    assert tick(factory,monkeypatch,gateway,NOW+timedelta(minutes=15),status="risk")["outcome"]=="dispatch_pending"
    assert len(gateway.starts)==1 and len(gateway.reconciled)==1


def test_uncertain_dispatch_reserved_before_post_and_reconciled_without_resend(factory,monkeypatch):
    gateway=Gateway(fail=True,result="running")
    original=gateway.start
    def start(token):
        with factory() as reader:
            assert read_controller(reader).dispatch_state=="reserved"
            assert read_controller(reader).dispatch_token==token
        return original(token)
    gateway.start=start
    assert tick(factory,monkeypatch,gateway,status="risk")["outcome"]=="requires_attention"
    with factory() as reader:assert read_controller(reader).dispatch_state=="unknown"
    assert tick(factory,monkeypatch,gateway,NOW+timedelta(minutes=15),status="risk")["outcome"]=="dispatch_pending"
    assert len(gateway.starts)==1
    with factory() as reader:
        assert read_controller(reader).dispatch_error is None
        assert read_controller(reader).worker_starts==1


def test_proven_absent_dispatch_can_retry_next_tick(factory,monkeypatch):
    gateway=Gateway(fail=True,result="absent")
    tick(factory,monkeypatch,gateway,status="risk")
    gateway.fail=False
    assert tick(factory,monkeypatch,gateway,NOW+timedelta(minutes=15),status="risk")["outcome"]=="dispatched"
    assert len(set(gateway.starts))==2


def test_failed_reconciliation_keeps_uncertain_reservation_and_prevents_resend(factory,monkeypatch):
    gateway=Gateway(fail=True)
    assert tick(factory,monkeypatch,gateway,status="risk")["outcome"]=="requires_attention"
    def unavailable(*args):
        raise httpx.ReadTimeout("cannot establish execution state")
    gateway.reconcile=unavailable
    for minutes in (15,30):
        assert tick(factory,monkeypatch,gateway,NOW+timedelta(minutes=minutes),status="risk")["outcome"]=="requires_attention"
        with factory() as db:assert read_controller(db).dispatch_state=="unknown"
    assert len(gateway.starts)==1


def test_controller_overlap_lock(factory,monkeypatch):
    with factory() as holder:
        conn=holder.connection();conn.execute(text("SELECT pg_advisory_lock(:key)"),{"key":controller.CONTROLLER_LOCK})
        try:assert tick(factory,monkeypatch,Gateway(),status="risk")["outcome"]=="already_checking"
        finally:conn.execute(text("SELECT pg_advisory_unlock(:key)"),{"key":controller.CONTROLLER_LOCK})


def test_paused_collection_preserves_pending_pipeline_work(factory,monkeypatch):
    with factory() as db:
        config=OperationalSettings(news_collection_enabled=False)
        db.get(SystemSetting,settings.CONFIG_KEY).value={"revision":0,"settings":config.model_dump(mode="json")};db.commit()
    gateway=Gateway()
    assert tick(factory,monkeypatch,gateway,status="risk")["outcome"]=="not_due"
    monkeypatch.setattr(controller,"pending_pipeline_work",lambda *args,**kw:True)
    assert tick(factory,monkeypatch,gateway,NOW+timedelta(minutes=15),status="risk")["outcome"]=="dispatched"


def test_legacy_interval_save_is_ignored_without_revision_or_audit(factory):
    with factory() as db:
        settings.save_configuration(db,ConfigurationUpdate(revision=0,settings=OperationalSettings(
            news_source_ids=["daily-tribune"],news_collection_interval_minutes=15)),actor_id=999999)
        assert settings.read_configuration(db).news_collection_interval_minutes==30
        assert db.get(SystemSetting,settings.CONFIG_KEY).value["revision"]==0


def test_historical_zone_retained_by_paused_expiry_is_not_weather_evidence(settings_factory):
    from geoalchemy2.shape import from_shape
    from shapely.geometry import Polygon
    with settings_factory() as db:
        incident=FloodEvent(status="active",first_reported_at=NOW-timedelta(days=20),verified_at=NOW,peak_severity="medium")
        db.add(incident);db.flush()
        zone=FloodAvoidanceZone(event_id=incident.id,is_active=True,expires_at=NOW-timedelta(days=19),
            geometry=from_shape(Polygon([(121,14.5),(121.001,14.5),(121.001,14.501),(121,14.5)]),srid=4326))
        db.add(zone);db.flush()
        assert current_flood_until(db,NOW) is None
        incident.first_reported_at=NOW-timedelta(minutes=20);zone.expires_at=NOW+timedelta(minutes=40);db.flush()
        assert current_flood_until(db,NOW)==NOW+timedelta(minutes=40)
        db.rollback()


def test_actual_pending_article_remains_actionable_with_collector_paused(settings_factory):
    from app.crud.news_weather import pending_pipeline_work
    with settings_factory() as db:
        article=NewsArticle(canonical_url="https://example.invalid/"+uuid4().hex,publisher_source_id="daily-tribune",
            title="Flood",article_text="Flooding observed",content_fingerprint="a"*64,review_state="pending")
        db.add(article);db.flush()
        assert pending_pipeline_work(db,NOW,OperationalSettings(news_collection_enabled=False),("daily-tribune",),policy_fingerprint="a"*64,admission_age=timedelta(hours=12))
        assert not pending_pipeline_work(db,NOW,OperationalSettings(news_collection_enabled=False,news_processing_enabled=False),(),policy_fingerprint="a"*64,admission_age=timedelta(hours=12))
        db.rollback()


@pytest.mark.parametrize("status,claims,delay,published_age,expected", [
    ("completed",[],0,1,False), ("completed",[{}],0,1,True),
    ("completed",[{}],0,13,False), ("retry_wait",None,5,1,False),
    ("retry_wait",None,-5,1,True), ("processing",None,-5,1,True),
])
def test_actual_pipeline_predicates_do_not_launch_for_empty_or_future_work(settings_factory,status,claims,delay,published_age,expected):
    from app.crud.news_weather import pending_pipeline_work
    from app.crud.news_processing import current_pipeline_version
    with settings_factory() as db:
        article=NewsArticle(canonical_url="https://example.invalid/"+uuid4().hex,publisher_source_id="daily-tribune",
            title="Flood",article_text="Flooding observed",published_at=NOW-timedelta(hours=published_age),
            content_fingerprint="a"*64,review_state="pending")
        db.add(article);db.flush()
        version=NewsArticleVersion(article_id=article.id,input_fingerprint="b"*64,input_snapshot={})
        db.add(version);db.flush()
        run=NewsExtractionRun(article_version_id=version.id,pipeline_version=current_pipeline_version(),status=status,
            next_attempt_at=NOW+timedelta(minutes=delay) if status=="retry_wait" else None,
            lease_expires_at=NOW+timedelta(minutes=delay) if status=="processing" else None,
            lease_token=uuid4() if status=="processing" else None,
            result={"claims":claims} if status=="completed" else None,
            completed_at=NOW if status=="completed" else None)
        db.add(run);db.flush()
        assert pending_pipeline_work(db,NOW,OperationalSettings(news_collection_enabled=False),
            ("daily-tribune",),policy_fingerprint="a"*64,admission_age=timedelta(hours=12))==expected
        db.rollback()
