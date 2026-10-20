"""Constructed C3a checks; model inference is forbidden in this module."""
import asyncio
from contextlib import contextmanager
from datetime import timedelta
import os
from types import SimpleNamespace

import pytest
from sqlalchemy import func,select,text
from sqlalchemy.engine import URL

from app.crud.news_processing import capture_pending_inputs,enqueue_article
from app.models.news import NewsArticle,NewsArticleVersion,NewsExtractionRun
from app.services.news_ner.location_pipeline import from_neural_mentions
from app.services.news_ner_durable import processing
from app.services.news_ner_durable.contracts import NerEvidenceError,PublicationEvidence
from app.services.news_ner_runtime.supervisor import RuntimeFailure
from test_news_ner_durable import BODY,NOW,make_case,trusted
from test_news_processing_postgres import postgres_queue,seed


@pytest.mark.parametrize('environment,database,driver,accepted',[
    ('test','lanes_p3_verify_fixture','postgresql+psycopg',True),
    ('development','lanes_p3_verify_fixture','postgresql+psycopg',False),
    ('production','lanes_p3_verify_fixture','postgresql+psycopg',False),
    ('test','lanes','postgresql+psycopg',False),('test','lanes_p3_verify_fixture','sqlite',False)])
def test_target_guard(environment,database,driver,accepted):
    url=URL.create(driver,database=database).render_as_string(hide_password=False)
    if accepted:processing.require_local_target(environment,url)
    else:
        with pytest.raises(NerEvidenceError,match='ner_configuration_invalid'):processing.require_local_target(environment,url)


def test_timer_refuses_invalid_platform_or_nested_owner(monkeypatch):
    monkeypatch.setattr(processing.platform,'system',lambda:'Windows')
    with pytest.raises(NerEvidenceError,match='ner_configuration_invalid'):
        with processing.deadline(1):pass
    with pytest.raises(processing.OperationDeadline):
        with processing.deadline(0):pass


@pytest.fixture
def native_job(postgres_queue,trusted,monkeypatch):
    @contextmanager
    def constructed_timer(seconds):
        if seconds<=0:raise processing.OperationDeadline()
        yield
    monkeypatch.setattr(processing,'deadline',constructed_timer)
    class FictionalRuntime:
        starts=0;requests=0;closes=0;failure=None;after=None;state='new'
        async def start(self):self.starts+=1;self.state='ready'
        async def request(self,request,*,timeout):
            self.requests+=1
            with postgres_queue() as db:
                assert db.scalar(text("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND state='idle in transaction'"))==0
            if self.failure:raise self.failure
            _,_,_,inference,_=make_case(trusted,request['text'])
            pure=from_neural_mentions({**request,'mentions':inference['proposal']['neural_mentions']})
            if self.after:self.after()
            return {**pure,'provenance':trusted.provenance,'measurements':inference['measurements']}
        async def close(self):
            if self.state!='closed':self.closes+=1;self.state='closed'
    runtime=FictionalRuntime()
    sources=(SimpleNamespace(id='fixture',enabled=True,verified_at=NOW),)
    async def run(**kwargs):
        return await processing.process_native_saved_news(postgres_queue,load_assets=lambda:trusted,
            environment='test',database_url=os.environ['LANES_NEWS_TEST_DATABASE_URL'],
            runtime_factory=lambda _:runtime,sources=sources,clock=lambda:NOW,**kwargs)
    return runtime,run


@pytest.mark.asyncio
async def test_native_capture_processing_duplicates_and_changed_body(postgres_queue,trusted,native_job):
    seed(postgres_queue,2)
    with postgres_queue() as db,db.begin():
        for row in db.scalars(select(NewsArticle)):row.article_text=BODY
    runtime,run=native_job
    first=await run()
    assert first.completed==2 and first.captured==2 and not first.error_code
    assert runtime.starts==1 and runtime.requests==2 and runtime.closes==1
    second=await run()
    assert second.completed==0 and second.captured==0 and runtime.requests==2 and runtime.starts==1
    with postgres_queue() as db,db.begin():
        row=db.scalar(select(NewsArticle).order_by(NewsArticle.id));row.article_text='  🌧️\n'+BODY
    third=await run()
    assert third.completed==1 and runtime.requests==3
    with postgres_queue() as db:
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion))==5
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun).where(NewsExtractionRun.mode=='rules_only'))==2
        result=db.scalar(select(NewsExtractionRun).where(NewsExtractionRun.mode=='ner_rules_v1').order_by(NewsExtractionRun.id.desc())).result
        assert result['source']['publication_timezone_known'] is False and result['claims'][0]['confidence_score'] is None
        for table in ('news_claim_sources','news_claim_decisions','flood_avoidance_zones'):
            assert db.scalar(text('SELECT count(*) FROM '+table))==0


@pytest.mark.asyncio
@pytest.mark.parametrize('failure,code,retry',[(RuntimeFailure('deadline'),'ner_runtime_timeout',True),
    (RuntimeFailure('worker_exit'),'ner_runtime_failed',True),(ValueError('fictional mismatch'),'ner_result_contract_invalid',False)])
async def test_failure_persisted_once_and_session_not_restarted(postgres_queue,native_job,failure,code,retry):
    seed(postgres_queue,2);runtime,run=native_job;runtime.failure=failure
    result=await run()
    assert result.runs[0]['error_code']==code and runtime.requests==1 and runtime.starts==1 and runtime.closes==1
    assert result.retry_wait==int(retry) and result.failed==int(not retry)
    with postgres_queue() as db:
        rows=db.scalars(select(NewsExtractionRun).where(NewsExtractionRun.mode=='ner_rules_v1').order_by(NewsExtractionRun.id)).all()
        assert rows[0].attempt_count==1 and rows[0].result is None
        assert rows[1].status=='pending' and rows[1].attempt_count==0


@pytest.mark.asyncio
async def test_budget_stop_does_not_claim_or_start_model(postgres_queue,native_job):
    seed(postgres_queue);runtime,run=native_job
    ticks=iter([0,0,400]);result=await run(monotonic=lambda:next(ticks,400))
    assert result.stop_reason=='budget_exhausted' and runtime.starts==0
    with postgres_queue() as db:
        assert db.scalar(select(NewsExtractionRun).where(NewsExtractionRun.mode=='ner_rules_v1')).attempt_count==0


def test_capture_retains_independently_supplied_publication_evidence(postgres_queue,trusted):
    seed(postgres_queue)
    with postgres_queue() as db,db.begin():
        row=db.scalar(select(NewsArticle));row.published_at=NOW
        known=PublicationEvidence(raw=NOW.isoformat(),timezone_known=True,basis='publisher_feed')
        enqueue_article(db,row,mode='ner_rules_v1',pipeline_version=trusted.pipeline_version,publication_evidence=known)
        assert capture_pending_inputs(db,50,mode='ner_rules_v1',pipeline_version=trusted.pipeline_version)==0
        row.published_at=NOW+timedelta(hours=1)
        assert capture_pending_inputs(db,50,mode='ner_rules_v1',pipeline_version=trusted.pipeline_version)==1


@pytest.mark.asyncio
async def test_native_only_success_and_empty_queue_never_start_model(postgres_queue,native_job):
    runtime,run=native_job
    assert (await run()).stop_reason=='no_work' and runtime.starts==0
    seed(postgres_queue)
    with postgres_queue() as db,db.begin():db.scalar(select(NewsArticle)).article_text='A fictional prevention project was announced.'
    result=await run()
    assert result.completed==1
    with postgres_queue() as db:
        native=db.scalar(select(NewsExtractionRun).where(NewsExtractionRun.mode=='ner_rules_v1'))
        assert native.result['claims']==[] and native.result['projection']['disposition']=='no_eligible_observations'


@pytest.mark.asyncio
async def test_cancellation_persists_retry_without_restart(postgres_queue,native_job):
    seed(postgres_queue);runtime,run=native_job;runtime.failure=asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):await run()
    with postgres_queue() as db:
        row=db.scalar(select(NewsExtractionRun).where(NewsExtractionRun.mode=='ner_rules_v1'))
        assert row.status=='retry_wait' and row.error_code=='ner_runtime_cancelled' and row.attempt_count==1
    assert runtime.requests==1 and runtime.closes==1


@pytest.mark.asyncio
async def test_normalization_budget_is_part_of_article_budget(postgres_queue,native_job):
    seed(postgres_queue);runtime,run=native_job;elapsed=[0]
    runtime.after=lambda:elapsed.__setitem__(0,116)
    result=await run(monotonic=lambda:elapsed[0])
    assert result.retry_wait==1 and result.runs[0]['error_code']=='ner_runtime_timeout' and runtime.closes==1


@pytest.mark.asyncio
async def test_source_selection_change_stops_before_second_claim(postgres_queue,native_job,monkeypatch):
    seed(postgres_queue,2);runtime,run=native_job
    original=processing.selected_news_sources;changed=[False]
    monkeypatch.setattr(processing,'selected_news_sources',lambda db,sources:() if changed[0] else original(db,sources))
    runtime.after=lambda:changed.__setitem__(0,True)
    result=await run()
    assert result.completed==1 and result.stop_reason=='sources_changed' and runtime.requests==1


@pytest.mark.asyncio
async def test_shutdown_failure_does_not_erase_completed_result(postgres_queue,native_job):
    seed(postgres_queue);runtime,run=native_job
    async def broken_close():raise RuntimeFailure('shutdown_failed')
    runtime.close=broken_close
    result=await run()
    assert result.completed==1 and result.error_code=='ner_runtime_cleanup_failed'
    with postgres_queue() as db:
        assert db.scalar(select(NewsExtractionRun).where(NewsExtractionRun.mode=='ner_rules_v1')).status=='completed'


@pytest.mark.asyncio
async def test_startup_deadline_is_owned_retry(postgres_queue,native_job):
    seed(postgres_queue);runtime,run=native_job
    async def late_start():runtime.starts+=1;raise RuntimeFailure('deadline')
    runtime.start=late_start
    result=await run()
    assert result.retry_wait==1 and runtime.starts==1 and runtime.requests==0
    with postgres_queue() as db:
        row=db.scalar(select(NewsExtractionRun).where(NewsExtractionRun.mode=='ner_rules_v1'))
        assert row.attempt_count==1 and row.error_code=='ner_runtime_timeout'


@pytest.mark.asyncio
async def test_asset_failure_precedes_native_capture(postgres_queue,trusted,native_job,monkeypatch):
    seed(postgres_queue);runtime,run=native_job
    def broken(_):raise NerEvidenceError('ner_assets_unavailable')
    monkeypatch.setattr(type(trusted),'validate',broken)
    result=await run()
    assert result.error_code=='ner_assets_unavailable' and runtime.starts==0
    with postgres_queue() as db:
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun).where(NewsExtractionRun.mode=='ner_rules_v1'))==0
