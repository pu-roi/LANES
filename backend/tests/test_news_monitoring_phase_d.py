"""Phase D regressions: monitoring truth, service failures and retry evidence."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from dataclasses import replace

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import event, select
from sqlalchemy.exc import OperationalError

from app.api import deps
from app.core.database import get_db
from app.main import app
from app.models.setting import SystemSetting
from app.models.news import NewsArticle, NewsFeedCheckpoint, NewsExtractionRun
from app.schemas.configuration import ConfigurationRuntime, NewsStageHealth, OperationalSettings
from app.schemas.news_monitoring import NewsMonitoringSummary
from app.schemas.news_telemetry import FeedAttempt
from app.services.configuration_service import CONFIG_KEY,RUNTIME_KEY
from app.services.news_cycle_service import finish_cycle,attempt_identity
from app.services.news_claim_auditor import AuditorConfig,AuditorConfigurationError,NewsClaimAuditor
from app.services.news_automation_service import read_news_automation
from app.services.news_source_health_service import read_source_health
from app.services.news_collection_service import browse_news_collection
from app.services.hybrid_extraction_service import HybridExtractionService
from app.services.news_processing_service import process_saved_news
from app.services.news_evaluation_service import evaluate_news_claims
from app.crud.news_processing import enqueue_article
from test_news_processing import queue_db, article
from test_news_automation import status_db
from test_news_ner_integration import c3b_db,operational_trusted,base_trusted,save_native,NOW


@pytest.mark.parametrize('key,value', [('LANES_NEWS_AUDITOR_BATCH_SIZE','private-invalid'),
    ('LANES_NEWS_AUDITOR_REASONING_ENABLED','private-invalid')])
def test_invalid_auditor_settings_are_bounded_and_do_not_break_status(status_db,monkeypatch,key,value):
    monkeypatch.setenv(key,value)
    with pytest.raises(AuditorConfigurationError) as caught:AuditorConfig.from_environment()
    assert str(caught.value)=='auditor_configuration_invalid' and value not in str(caught.value)
    status=read_news_automation(status_db)
    assert status.audit.state=='requires_attention' and status.audit.error_code=='auditor_configuration_invalid'
    assert status.weather and status.queue_counts and status.read_only


def test_semantic_auditor_configuration_error_is_preserved(status_db,monkeypatch):
    monkeypatch.setenv('LANES_NEWS_AUDITOR_CONFIG_REVISION','INVALID!')
    status=read_news_automation(status_db)
    assert status.audit.error_code=='auditor_config_revision_invalid'


@pytest.mark.asyncio
async def test_rules_only_processing_does_not_load_invalid_auditor(queue_db,monkeypatch):
    monkeypatch.setenv('LANES_NEWS_AUDITOR_BATCH_SIZE','not-valid')
    with queue_db() as db,db.begin():db.add(article());db.flush();enqueue_article(db,db.get(NewsArticle,1))
    assert (await process_saved_news(queue_db)).completed==1


@pytest.mark.asyncio
async def test_evaluation_rejects_configuration_before_storage_or_claim(monkeypatch):
    def forbidden():pytest.fail('configuration failure reached storage')
    monkeypatch.setenv('LANES_NEWS_AUDITOR_BATCH_SIZE','not-valid')
    assert (await evaluate_news_claims(forbidden)).error_code=='auditor_configuration_invalid'
    auditor=NewsClaimAuditor(AuditorConfig(provider='missing'))
    assert (await evaluate_news_claims(forbidden,auditor=auditor)).error_code=='auditor_provider_not_configured'


@pytest.mark.asyncio
async def test_extraction_result_validation_is_not_article_input_failure(queue_db,monkeypatch):
    from app.schemas.news_extraction import NewsArticleExtractorInput
    import app.services.news_processing_service as service
    async def invalid(_article):NewsArticleExtractorInput.model_validate({})
    monkeypatch.setattr(service,'extract_captured_news_article',invalid)
    with queue_db() as db,db.begin():db.add(article());db.flush();enqueue_article(db,db.get(NewsArticle,1))
    result=await process_saved_news(queue_db)
    assert result.retry_wait==1 and result.runs[0]['error_code']=='extraction_result_errors'


def test_cycle_history_bounds_identity_and_repeat_finalization(monkeypatch):
    monkeypatch.setenv('CLOUD_RUN_EXECUTION','lanes-news-test')
    monkeypatch.setenv('CLOUD_RUN_TASK_INDEX','0')
    runtime=ConfigurationRuntime()
    for index in range(12):
        monkeypatch.setenv('CLOUD_RUN_TASK_ATTEMPT',str(index))
        runtime.last_started_at=NOW+timedelta(minutes=index)
        runtime.error_code='pipeline_requires_attention' if index==10 else None
        runtime.stage_outcomes={'collection':'failed' if index==10 else 'not_due','untrusted':'bad'}
        runtime.stages={'collection':NewsStageHealth(last_attempt_at=runtime.last_started_at,errors=['feed_error','private / path'])}
        cycle=finish_cycle(runtime,runtime.last_started_at+timedelta(seconds=2),attempt_identity())
        assert finish_cycle(runtime,runtime.last_started_at+timedelta(seconds=3),attempt_identity())==cycle
    assert len(runtime.recent_cycles)==10 and runtime.recent_cycles[0].task_attempt==11
    assert runtime.recent_cycles[1].outcome=='requires_attention'
    assert runtime.recent_cycles[1].stage_errors['collection']==['feed_error','stage_failed']
    assert 'untrusted' not in cycle.stage_outcomes
    assert ConfigurationRuntime.model_validate_json(runtime.model_dump_json()).recent_cycles==runtime.recent_cycles
    assert ConfigurationRuntime.model_validate({}).recent_cycles==[]


def test_invalid_cloud_metadata_remains_unknown(monkeypatch):
    monkeypatch.setenv('CLOUD_RUN_EXECUTION','/private/path')
    monkeypatch.setenv('CLOUD_RUN_TASK_INDEX','-1')
    monkeypatch.setenv('CLOUD_RUN_TASK_ATTEMPT','invalid')
    assert attempt_identity()==dict(execution_name=None,task_index=None,task_attempt=None)


def test_cycle_uses_actual_stage_result_without_relabeling_legacy_configuration_flags():
    runtime=ConfigurationRuntime(last_started_at=NOW,stage_outcomes={'publication':'enabled'},
        stages={'publication':NewsStageHealth(last_attempt_at=NOW,outcome='completed')})
    cycle=finish_cycle(runtime,NOW+timedelta(seconds=1),{})
    assert cycle.stage_outcomes['publication']=='completed'
    assert runtime.stage_outcomes['publication']=='enabled'


def test_feed_counter_retains_legacy_name_without_changing_meaning():
    feed=FeedAttempt(source_id='fictional',feed_url='https://example.org/rss',status='parsed',checked_at=NOW,
        error_code=None,entries_seen=7,candidates_saved=4,body_errors=1,scope_unresolved=0)
    assert feed.model_dump()['articles_saved_or_seen']==feed.candidates_saved==4


def test_source_registry_selection_pause_and_saved_health(c3b_db):
    from app.services.news_sources import load_news_sources
    sources=load_news_sources();source=next(s for s in sources if s.enabled)
    disabled=replace(source,id='disabled',enabled=False)
    with c3b_db() as db,db.begin():
        config=OperationalSettings(news_source_ids=[],news_collection_enabled=True)
        db.add(SystemSetting(key=CONFIG_KEY,value={'settings':config.model_dump(mode='json'),'revision':1}))
        db.add(NewsFeedCheckpoint(source_id=source.id,feed_url=source.feed_urls[0],last_checked_at=NOW,
            last_success_at=NOW-timedelta(hours=1),last_error='private raw network diagnostic'))
        db.add(article(publisher_source_id=source.id,article_error='blocked'))
    with c3b_db() as db:
        first,second=read_source_health(db,(source,disabled))
        assert first.enabled and first.registry_eligible and not first.selected_for_collection and not first.collection_active
        assert first.feed_health[0].status=='error' and first.feed_health[0].error_code=='feed_retrieval_failed'
        assert first.body_counts['error']==1 and 'private' not in first.model_dump_json()
        assert not second.registry_eligible and second.feed_health[0].status=='not_recorded'
        row=db.get(SystemSetting,CONFIG_KEY);saved=dict(row.value);saved['settings']={**saved['settings'],'news_source_ids':[source.id],'news_collection_enabled':False};row.value=saved;db.commit()
        first=read_source_health(db,(source,))[0]
        assert first.selected_for_collection and not first.collection_active


def test_default_selection_and_feed_success_do_not_prove_body_health(c3b_db):
    from app.services.news_sources import load_news_sources
    source=next(s for s in load_news_sources() if s.enabled)
    with c3b_db() as db,db.begin():
        db.add(NewsFeedCheckpoint(source_id=source.id,feed_url=source.feed_urls[0],last_checked_at=NOW,last_success_at=NOW))
        db.add(article(publisher_source_id=source.id,article_text=None,article_error='failed'))
    with c3b_db() as db:
        row=read_source_health(db,(source,))[0]
        assert row.selected_for_collection and row.collection_active and row.feed_health[0].status=='ok'
        assert row.body_counts==dict(available=0,missing=0,error=1)


def test_mixed_feed_checks_and_timestamp_without_outcome_remain_independent(c3b_db):
    from app.services.news_sources import NewsSource
    urls=tuple('https://example.org/'+str(index) for index in range(4))
    source=NewsSource('fictional','Fictional',('example.org',),urls,NOW.date(),True)
    with c3b_db() as db,db.begin():
        db.add_all([NewsFeedCheckpoint(source_id=source.id,feed_url=urls[0],last_checked_at=NOW,last_success_at=NOW),
            NewsFeedCheckpoint(source_id=source.id,feed_url=urls[1],last_checked_at=NOW,last_error='failure'),
            NewsFeedCheckpoint(source_id=source.id,feed_url=urls[2],last_checked_at=NOW)])
    with c3b_db() as db:
        row=read_source_health(db,(source,))[0]
        assert [f.status for f in row.feed_health]==['ok','error','not_recorded','not_recorded']


@pytest.mark.parametrize('native',[False,True])
def test_retrieval_filter_preserves_eligibility_counts_and_native_context(c3b_db,operational_trusted,native):
    from app.services.news_ner_durable.collection import NativeCollectionContext
    if native:
        _,article_id=save_native(c3b_db,operational_trusted)
    else:
        with c3b_db() as db,db.begin():db.add(article());article_id=1
    with c3b_db() as db,db.begin():db.get(NewsArticle,article_id).article_error='retrieval problem'
    with c3b_db() as db:
        context=NativeCollectionContext(operational_trusted,'test',db.get_bind().url.render_as_string(hide_password=False)) if native else None
        page=browse_news_collection(db,page=5,page_size=1,search='',publisher=None,status='all',retrieval='error',processing_context=context)
        assert page.total==1 and page.page==1 and page.retrieval_counts['error']==1
        assert page.items[0].collection_status==('retrieval_failed' if native else 'excluded')
        # Failed refresh does not erase a previously saved native observation.
        assert page.items[0].location_count==(1 if native else 0)
        assert browse_news_collection(db,page=1,page_size=1,search='',publisher=None,status='all',retrieval='available',processing_context=context).total==0


@pytest.mark.asyncio
async def test_health_gets_are_authorized_readonly_no_network(c3b_db,monkeypatch):
    def forbidden(*_a,**_k):pytest.fail('read attempted network or mutation')
    monkeypatch.setattr(httpx.Client,'request',forbidden)
    with c3b_db() as db:
        def guard(_connection,_cursor,statement,*_):
            assert statement.lstrip().split()[0].upper() in ('SELECT','SHOW'),statement[:30]
        event.listen(db.get_bind(),'before_cursor_execute',guard)
        app.dependency_overrides[get_db]=lambda:db
        app.dependency_overrides[deps.get_current_active_admin]=lambda:SimpleNamespace(id=1)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
                assert (await client.get('/api/v1/admin/news/sources')).status_code==200
                response=await client.get('/api/v1/admin/news/collection?status=all&retrieval=error')
                assert response.status_code==200 and response.json()['retrieval_counts']==dict(available=0,missing=0,error=0)
                assert (await client.get('/api/v1/admin/news/collection?retrieval=wrong')).status_code==422
                monkeypatch.setenv('LANES_NEWS_AUDITOR_BATCH_SIZE','not-valid')
                response=await client.get('/api/v1/admin/news/automation')
                assert response.status_code==200 and response.json()['audit']['error_code']=='auditor_configuration_invalid'
                app.dependency_overrides.pop(deps.get_current_active_admin)
                assert (await client.get('/api/v1/admin/news/sources')).status_code in (401,403)
                app.dependency_overrides[deps.get_current_user]=lambda:SimpleNamespace(role=SimpleNamespace(name='Commuter'))
                assert (await client.get('/api/v1/admin/news/sources')).status_code==403
        finally:
            app.dependency_overrides.clear();event.remove(db.get_bind(),'before_cursor_execute',guard)


def test_automation_database_errors_are_not_configuration_errors(status_db,monkeypatch):
    from app.services import news_audit_quota_service as quota
    def failed(*_a,**_k):raise OperationalError('fictional',{},Exception('storage'))
    monkeypatch.setattr(quota,'read_quota',failed)
    with pytest.raises(OperationalError):read_news_automation(status_db)


@pytest.mark.asyncio
async def test_real_scheduler_retry_retains_failed_collection_without_fabricated_recovery(c3b_db,monkeypatch):
    from app.services import news_scheduler_service as scheduler, news_weather_controller_service as weather, flood_event_service
    from app.models.news_telemetry import NewsDiscoveryRun
    from test_news_ner_integration import SOURCES
    when=[NOW]
    config=OperationalSettings(news_processing_enabled=False,news_publication_enabled=False).model_dump(mode='json')
    config['news_source_ids']=['fictional']
    with c3b_db() as db,db.begin():db.add(SystemSetting(key=CONFIG_KEY,value={'revision':1,'settings':config}))
    calls=[]
    def collect(_sources,_client,db):
        calls.append(1)
        db.add(NewsDiscoveryRun(trigger='collector',started_at=when[0],finished_at=when[0],status='completed'))
        db.commit()
        return SimpleNamespace(probes=[SimpleNamespace(status='http_error',entry_count=3)],candidates=[])
    async def pipeline(*_a,**_k):
        return {**{s:{} for s in ('extraction','seed','evaluation','publication','footprints')},
            'stage_outcomes':{'processing':'paused','publication':'paused'}}
    monkeypatch.setattr(scheduler,'discover_news',collect)
    monkeypatch.setattr(scheduler,'run_news_pipeline',pipeline)
    monkeypatch.setattr(weather,'adaptive_decision',lambda *_a:SimpleNamespace(interval_minutes=60))
    monkeypatch.setattr(flood_event_service,'expire_due_zones',lambda *_a,**_k:None)
    monkeypatch.setenv('CLOUD_RUN_EXECUTION','lanes-news-fictional')
    monkeypatch.setenv('CLOUD_RUN_TASK_INDEX','0');monkeypatch.setenv('CLOUD_RUN_TASK_ATTEMPT','0')
    first=await scheduler.run_scheduled_news_tick(c3b_db,sources=SOURCES,clock=lambda:when[0])
    assert first['outcome']=='requires_attention' and first['stage_errors']['collection']==['feed_http_error']
    when[0]+=timedelta(seconds=28);monkeypatch.setenv('CLOUD_RUN_TASK_ATTEMPT','1')
    second=await scheduler.run_scheduled_news_tick(c3b_db,sources=SOURCES,clock=lambda:when[0])
    assert second['outcome']=='completed' and second['stage_outcomes']['collection']=='not_due' and len(calls)==1
    with c3b_db() as db:
        runtime=ConfigurationRuntime.model_validate(db.get(SystemSetting,RUNTIME_KEY).value)
        assert [c.task_attempt for c in runtime.recent_cycles]==[1,0]
        assert runtime.recent_cycles[1].outcome=='requires_attention'
        assert runtime.stages['collection'].outcome=='failed' and runtime.stages['collection'].last_success_at is None


@pytest.mark.asyncio
async def test_scheduler_configuration_failure_is_bounded_and_claims_no_articles(c3b_db,monkeypatch):
    from app.services.news_scheduler_service import run_scheduled_news_tick
    from test_news_ner_integration import SOURCES
    monkeypatch.setenv('LANES_NEWS_AUDITOR_BATCH_SIZE','private-invalid')
    config=OperationalSettings(news_collection_enabled=False).model_dump(mode='json');config['news_source_ids']=['fictional']
    with c3b_db() as db,db.begin():db.add(SystemSetting(key=CONFIG_KEY,value={'revision':1,'settings':config}))
    result=await run_scheduled_news_tick(c3b_db,sources=SOURCES,clock=lambda:NOW)
    assert result['outcome']=='requires_attention' and result['error_code']=='auditor_configuration_invalid'
    assert result['stage_errors']['pipeline']==['auditor_configuration_invalid']
    assert 'private-invalid' not in str(result)
    with c3b_db() as db:assert list(db.scalars(select(NewsExtractionRun)))==[]


@pytest.mark.asyncio
@pytest.mark.parametrize('cancel',[False,True])
async def test_scheduler_aggregate_failures_and_cancellation_never_mark_success(c3b_db,monkeypatch,cancel):
    import asyncio
    from app.services import news_scheduler_service as scheduler
    from test_news_ner_integration import SOURCES
    config=OperationalSettings(news_collection_enabled=False).model_dump(mode='json');config['news_source_ids']=['fictional']
    with c3b_db() as db,db.begin():db.add(SystemSetting(key=CONFIG_KEY,value={'revision':1,'settings':config}))
    async def pipeline(*_a,**_k):
        if cancel:raise asyncio.CancelledError()
        return {'extraction':{'failed':1},'stage_outcomes':{'processing':'enabled','publication':'enabled'}}
    monkeypatch.setattr(scheduler,'run_news_pipeline',pipeline)
    if cancel:
        with pytest.raises(asyncio.CancelledError):await scheduler.run_scheduled_news_tick(c3b_db,sources=SOURCES,clock=lambda:NOW)
    else:
        result=await scheduler.run_scheduled_news_tick(c3b_db,sources=SOURCES,clock=lambda:NOW)
        assert result['outcome']=='requires_attention' and result['stage_errors']['extraction']==['stage_failed']
    with c3b_db() as db:
        runtime=ConfigurationRuntime.model_validate(db.get(SystemSetting,RUNTIME_KEY).value)
        assert runtime.last_cycle.outcome=='requires_attention' and runtime.last_successful_at is None
