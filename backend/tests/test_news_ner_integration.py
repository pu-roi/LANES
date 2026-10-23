"""C3b fictional source/reader/lifecycle checks on explicitly disposable storage."""
from copy import deepcopy
from datetime import timedelta
import json
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine,select,text,func
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.crud.news_processing import enqueue_article,claim_due_run,finish_owned_run
from app.models.news import NewsArticle,NewsArticleVersion,NewsExtractionRun
from app.models.news_publication import NewsClaimCase,NewsClaimSource,NewsClaimEvaluation,NewsClaimDecision
from app.services.news_ner.location_pipeline import from_neural_mentions
from app.services.news_ner_durable.adapter import build_native_result,verify_saved_result
from app.services.news_ner_durable.assets import with_placement_assets
from app.services.news_ner_durable.collection import NativeCollectionContext
from app.services.news_ner_durable.contracts import RunEvidence
from app.services.news_ner_durable.enrichment import enrich_native_result
from app.services.news_ner_durable.evaluation import native_evaluation_policy,seed_native_evaluations,evaluate_native_claims
from app.services.news_ner_durable.reconciliation import reconcile_native_article
from app.services.news_results_service import browse_news_results,read_news_result
from app.services.news_ner_durable.readers import read_native_group
from app.services.news_sources import NewsSource
from test_news_ner_durable import trusted as base_trusted,make_case,BODY,LEAD,NOW

SOURCES=(NewsSource('fictional','Fictional',('example.org',),('https://example.org/feed',),NOW.date(),True),)


@pytest.fixture(scope='module')
def operational_trusted(base_trusted):
    return with_placement_assets(base_trusted)


@pytest.fixture
def c3b_db():
    value=os.environ.get('LANES_NEWS_C3B_TEST_DATABASE_URL')
    if not value:pytest.skip('Owned C3b disposable database required')
    url=make_url(value)
    assert url.host in ('127.0.0.1','localhost') and url.database=='lanes_p3_verify_c3b_publication'
    # Clone the owned empty migrated template per case. Immutable publication
    # history also forbids TRUNCATE; never disable those protections for tests.
    name='lanes_p3_verify_c3b_case_'+uuid4().hex
    admin=create_engine(url.set(database='postgres'),isolation_level='AUTOCOMMIT')
    with admin.connect() as db:
        db.execute(text(f'CREATE DATABASE "{name}" TEMPLATE "{url.database}"'))
    engine=create_engine(url.set(database=name))
    try:
        with engine.connect() as db:
            assert db.scalar(text('SELECT current_database()'))==name
            assert db.scalar(text('SELECT version_num FROM alembic_version'))=='f1a9c7e2b604'
        yield sessionmaker(bind=engine)
    finally:
        engine.dispose()
        assert name.startswith('lanes_p3_verify_c3b_case_')
        with admin.connect() as db:db.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()


def save_native(factory,trusted,body=BODY,labels=None,*,article_id=None,readers=True):
    with factory() as db,db.begin():
        if article_id is None:
            article=NewsArticle(canonical_url=f'https://example.org/c3b/{uuid4()}',publisher_source_id='fictional',
                title='Fictional flood report',excerpt='',published_at=NOW,article_text=body,content_fingerprint='0'*64,review_state='pending')
            db.add(article);db.flush()
        else:
            article=db.get(NewsArticle,article_id);article.article_text=body
        run_id=enqueue_article(db,article,mode='ner_rules_v1',pipeline_version=trusted.pipeline_version)
        owned=claim_due_run(db,NOW,article_id=article.id,mode='ner_rules_v1',pipeline_version=trusted.pipeline_version)
        assert owned.run_id==run_id
        run=db.get(NewsExtractionRun,run_id);version=db.get(NewsArticleVersion,run.article_version_id)
        context=RunEvidence.from_records(run,version);request=context.source().runtime_request(context.input_fingerprint)
        *_,inference,_result=make_case(trusted,body,labels=labels)
        pure=from_neural_mentions({**request,'mentions':inference['proposal']['neural_mentions']})
        result=build_native_result(context,{**pure,'provenance':trusted.provenance,'measurements':inference['measurements']},trusted,extracted_at=NOW)
        if readers:result=enrich_native_result(context,result,trusted)
        assert finish_owned_run(db,owned,NOW,result=result.model_dump(mode='json',by_alias=True))
        return run_id,article.id


def view(factory,trusted,**changes):
    options=dict(page=1,page_size=12,search='',publisher=None,condition=None,placement=None,order='extraction_newest')
    options.update(changes)
    with factory() as db:
        context=NativeCollectionContext(trusted,'test',db.get_bind().url.render_as_string(hide_password=False))
        return browse_news_results(db,**options,processing_context=context)


def policy(factory,trusted):
    from app.services.configuration_service import read_configuration
    with factory() as db:return native_evaluation_policy(trusted,read_configuration(db))


def test_native_reader_returns_one_group_per_projection_and_exact_details(c3b_db,operational_trusted):
    run_id,article_id=save_native(c3b_db,operational_trusted)
    page=view(c3b_db,operational_trusted)
    assert page.total==1 and page.items[0].result_kind=='ner_group'
    assert page.items[0].claim_index==0
    with c3b_db() as db:
        detail=read_news_result(db,run_id,0)
        assert detail.claim.confidence_score is None
        group=read_native_group(db,run_id,page.items[0].group_id,{})
        assert group.result.read_projection is not None and group.captured_input.capture_schema=='lanes-news-ner-input-v1'
        assert group.captured_input.article_text==BODY
        assert group.lifecycle.state=='not_evaluated'
        assert read_native_group(db,run_id,'g99999',{}) is None


@pytest.mark.parametrize('body,labels',[
    (LEAD+'Fictional Crescent and Sample Road in Pasig City were flooded knee-deep.',[('Fictional Crescent','ROAD'),('Sample Road','ROAD'),('Pasig City','CITY')]),
    (LEAD+'Fictional Pocket in Pasig City was flooded knee-deep.',[('Fictional Pocket','LOCAL_AREA'),('Pasig City','CITY')]),
])
def test_native_only_groups_are_cards_without_synthetic_claims(c3b_db,operational_trusted,body,labels):
    run_id,_=save_native(c3b_db,operational_trusted,body,labels)
    page=view(c3b_db,operational_trusted)
    assert page.total==1 and page.items[0].claim_index is None
    with c3b_db() as db:
        run=db.get(NewsExtractionRun,run_id)
        assert run.result['claims']==[] and run.result['projection']['disposition']=='native_only'
        detail=read_native_group(db,run_id,page.items[0].group_id,{})
        assert all(name in detail.item.summary.location for name,label in labels if label!='CITY')
        assert 'Shared observation' not in detail.item.summary.location_qualifier


@pytest.mark.parametrize('fragment',['will be flooded','is not flooded','had flooding last year','has a flood-control prevention project','was cleared of floodwater'])
def test_non_observation_native_graph_has_no_cards(c3b_db,operational_trusted,fragment):
    save_native(c3b_db,operational_trusted,LEAD+'Fictional Crescent in Pasig City '+fragment+'.')
    assert view(c3b_db,operational_trusted).total==0


def test_native_sql_pagination_search_and_condition(c3b_db,operational_trusted):
    for index in range(3):save_native(c3b_db,operational_trusted,BODY.replace('knee-deep','waist-deep' if index else 'knee-deep'))
    first=view(c3b_db,operational_trusted,page_size=2)
    last=view(c3b_db,operational_trusted,page=99,page_size=2)
    assert first.total==3 and len(first.items)==2 and last.page==2 and len(last.items)==1
    assert {x.key for x in first.items}.isdisjoint({x.key for x in last.items})
    assert view(c3b_db,operational_trusted,search='100%').total==0
    assert view(c3b_db,operational_trusted,condition='receding').total==0
    assert view(c3b_db,operational_trusted,publisher='fictional',placement='not_recorded').total==0


def test_native_pending_or_failed_newest_run_hides_prior_result(c3b_db,operational_trusted):
    _,article_id=save_native(c3b_db,operational_trusted)
    with c3b_db() as db,db.begin():
        article=db.get(NewsArticle,article_id);article.article_text=BODY+' New update.'
        newest=enqueue_article(db,article,mode='ner_rules_v1',pipeline_version=operational_trusted.pipeline_version)
    assert view(c3b_db,operational_trusted).total==0
    with c3b_db() as db,db.begin():
        run=db.get(NewsExtractionRun,newest);run.status='failed';run.error_code='ner_runtime_failed';run.completed_at=NOW
    assert view(c3b_db,operational_trusted).total==0


def test_read_projection_tampering_is_operationally_rejected(c3b_db,operational_trusted):
    run_id,_=save_native(c3b_db,operational_trusted)
    with c3b_db() as db:
        run=db.get(NewsExtractionRun,run_id);version=db.get(NewsArticleVersion,run.article_version_id)
        raw=deepcopy(run.result);raw['read_projection']['groups'][0]['group_id']='g999'
        with pytest.raises(ValueError,match='ner_result_contract_invalid'):
            verify_saved_result(RunEvidence.from_records(run,version),raw,operational_trusted)


def test_native_collection_counts_match_group_cards(c3b_db,operational_trusted):
    from app.services.news_collection_service import browse_news_collection
    save_native(c3b_db,operational_trusted)
    with c3b_db() as db:
        ctx=NativeCollectionContext(operational_trusted,'test',db.get_bind().url.render_as_string(hide_password=False))
        page=browse_news_collection(db,page=1,page_size=12,search='',publisher=None,status='all',processing_context=ctx)
        assert page.items[0].location_count==view(c3b_db,operational_trusted).total==1


def test_native_source_evaluation_and_text_publication(c3b_db,operational_trusted,monkeypatch):
    from app.services.news_publication_service import process_news_publications
    import app.services.news_source_validation_service as old_checker
    monkeypatch.setattr(old_checker,'validate_source_batch',lambda *_a,**_kw:pytest.fail('native used legacy checker'))
    run_id,_=save_native(c3b_db,operational_trusted,'  🌧️\n'+BODY+'  ')
    current=policy(c3b_db,operational_trusted)
    seeded=seed_native_evaluations(c3b_db,current,now=NOW,sources=SOURCES)
    assert seeded.evaluations_created==1 and seeded.sources_created==1
    assert seed_native_evaluations(c3b_db,current,now=NOW,sources=SOURCES).evaluations_created==0
    evaluated=evaluate_native_claims(c3b_db,current,clock=lambda:NOW,sources=SOURCES)
    assert evaluated.completed==1 and evaluated.failed==0
    published=process_news_publications(c3b_db,policy=current,clock=lambda:NOW,sources=SOURCES)
    assert published.published==1 and not published.skipped
    with c3b_db() as db:
        decision=db.scalar(select(NewsClaimDecision))
        assert decision.public_state=='active_alert' and not decision.snapshot['public']['affects_routing']
        assert db.scalar(text('SELECT count(*) FROM flood_avoidance_zones'))==0
        detail=read_native_group(db,run_id,'g0',{})
        assert detail.lifecycle.state=='active_alert' and detail.lifecycle.decision_id==decision.id


def test_missing_observation_time_never_publishes(c3b_db,operational_trusted):
    from app.services.news_publication_service import process_news_publications
    save_native(c3b_db,operational_trusted,'At 10 AM, Fictional Crescent in Pasig City was flooded knee-deep.')
    current=policy(c3b_db,operational_trusted)
    assert seed_native_evaluations(c3b_db,current,now=NOW,sources=SOURCES).sources_created==1
    assert evaluate_native_claims(c3b_db,current,clock=lambda:NOW,sources=SOURCES).completed==1
    assert process_news_publications(c3b_db,policy=current,clock=lambda:NOW,sources=SOURCES).published==0
    with c3b_db() as db:
        record=db.scalar(select(NewsClaimEvaluation))
        assert record.result['reason_code']=='missing_supported_observation_time'


def test_zero_claim_correction_creates_idempotent_review_without_clearance(c3b_db,operational_trusted):
    from app.services.news_publication_service import process_news_publications
    _,article_id=save_native(c3b_db,operational_trusted)
    current=policy(c3b_db,operational_trusted)
    seed_native_evaluations(c3b_db,current,now=NOW,sources=SOURCES)
    evaluate_native_claims(c3b_db,current,clock=lambda:NOW,sources=SOURCES)
    assert process_news_publications(c3b_db,policy=current,clock=lambda:NOW,sources=SOURCES).published==1
    run_id,_=save_native(c3b_db,operational_trusted,LEAD+'Fictional Crescent in Pasig City is not flooded.',article_id=article_id)
    with c3b_db() as db,db.begin():
        from app.services.news_ner_durable.reconciliation import pending_reconciliation_runs
        assert pending_reconciliation_runs(db,current.pipeline_version,50)==[run_id]
        original=db.scalar(select(NewsClaimDecision))
        assert reconcile_native_article(db,run_id,now=NOW+timedelta(minutes=1),policy=current)==1
        assert reconcile_native_article(db,run_id,now=NOW+timedelta(minutes=2),policy=current)==0
        latest=db.scalar(select(NewsClaimDecision).order_by(NewsClaimDecision.id.desc()))
        assert latest.operation=='defer' and latest.review_state=='needs_review'
        assert latest.observed_at==original.observed_at and latest.expires_at==original.expires_at
        assert latest.public_state==original.public_state and latest.snapshot['native_reconciliation']['run_id']==run_id
        assert db.scalar(select(func.count()).select_from(NewsClaimSource))==1
        assert pending_reconciliation_runs(db,current.pipeline_version,50)==[]


@pytest.mark.asyncio
async def test_native_admin_reads_are_authorized_readonly_and_method_selected(c3b_db,operational_trusted,monkeypatch):
    import httpx
    from sqlalchemy import event
    from app.main import app
    from app.api import deps
    from app.core.database import get_db
    from app.services.news_ner_durable.readers import get_news_read_context
    from app.services.news_ner_runtime.supervisor import Session
    run_id,_=save_native(c3b_db,operational_trusted)
    def forbidden(*_args,**_kwargs):pytest.fail('admin GET attempted inference')
    monkeypatch.setattr(Session,'start',forbidden)
    def database():
        with c3b_db() as db:
            def no_writes(_c,_cursor,statement,_params,_ctx,_many):
                assert statement.lstrip().split()[0].upper() in ('SELECT','SHOW'),statement.split()[0]
            event.listen(db.get_bind(),'before_cursor_execute',no_writes)
            try:yield db
            finally:event.remove(db.get_bind(),'before_cursor_execute',no_writes)
    with c3b_db() as db:ctx=NativeCollectionContext(operational_trusted,'test',db.get_bind().url.render_as_string(hide_password=False))
    original=dict(app.dependency_overrides)
    app.dependency_overrides[get_db]=database
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            response=await client.get(f'/api/v1/admin/news/results/{run_id}/groups/g0')
            assert response.status_code==401
            app.dependency_overrides[deps.get_current_active_admin]=lambda:SimpleNamespace(id=1,role='admin')
            assert (await client.get('/api/v1/admin/news/results')).json()['total']==0
            app.dependency_overrides[get_news_read_context]=lambda:ctx
            page=await client.get('/api/v1/admin/news/results')
            assert page.status_code==200 and page.json()['total']==1
            item=page.json()['items'][0]
            detail=await client.get(f'/api/v1/admin/news/results/{run_id}/groups/{item["group_id"]}')
            assert detail.status_code==200 and detail.json()['result']['claims'][0]['confidence_score'] is None
            assert (await client.get('/api/v1/admin/news/collection?status=all')).status_code==200
    finally:app.dependency_overrides.clear();app.dependency_overrides.update(original)


@pytest.mark.asyncio
async def test_full_pipeline_uses_single_fake_session_and_no_duplicate_work(c3b_db,operational_trusted,monkeypatch):
    from contextlib import contextmanager
    import httpx
    from app.services.news_ner_durable import pipeline,processing
    from app.services.news_discovery_service import discover_news
    from app.services.news_pipeline_service import run_news_pipeline
    @contextmanager
    def fictional_deadline(seconds):
        if seconds<=0:raise processing.OperationDeadline()
        yield
    monkeypatch.setattr(pipeline,'deadline',fictional_deadline)
    monkeypatch.setattr(processing,'deadline',fictional_deadline)
    class Runtime:
        starts=0;requests=0;closed=0
        async def start(self):self.starts+=1
        async def request(self,request,*,timeout):
            self.requests+=1
            *_,inference,_result=make_case(operational_trusted,request['text'])
            pure=from_neural_mentions({**request,'mentions':inference['proposal']['neural_mentions']})
            return {**pure,'provenance':operational_trusted.provenance,'measurements':inference['measurements']}
        async def close(self):self.closed+=1
    runtime=Runtime()
    from email.utils import format_datetime
    from datetime import datetime,timezone
    pub=format_datetime(NOW)
    def handler(request):
        if str(request.url)=='https://example.org/feed':
            return httpx.Response(200,text=f'<rss><channel><item><guid>one</guid><title>Flood in Pasig</title><link>https://example.org/article</link><pubDate>{pub}</pubDate></item></channel></rss>')
        return httpx.Response(200,text='<article><p>'+BODY+' Details are fictional and used only for a local software acceptance check.</p></article>',headers={'content-type':'text/html'})
    with c3b_db() as db:ctx=NativeCollectionContext(operational_trusted,'test',db.get_bind().url.render_as_string(hide_password=False))
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        first=await run_news_pipeline(c3b_db,native_context=ctx,native_client=client,sources=SOURCES,
            runtime_factory=lambda _:runtime,clock=lambda:NOW)
        assert first['error_code'] is None and first['extraction']['completed']==1,first
        assert first['publication']['published']==1 and first['stop_reason']=='completed',first
        second=await run_news_pipeline(c3b_db,native_context=ctx,native_client=client,sources=SOURCES,
            runtime_factory=lambda _:runtime,clock=lambda:NOW)
        assert second['extraction']['completed']==0,second
    assert runtime.starts==runtime.closed==runtime.requests==1
    assert view(c3b_db,operational_trusted).total==1


def test_native_publication_cannot_reuse_old_run_after_new_failure(c3b_db,operational_trusted):
    from app.services.news_publication_service import process_news_publications
    run_id,article_id=save_native(c3b_db,operational_trusted)
    current=policy(c3b_db,operational_trusted)
    seed_native_evaluations(c3b_db,current,now=NOW,sources=SOURCES)
    evaluate_native_claims(c3b_db,current,clock=lambda:NOW,sources=SOURCES)
    with c3b_db() as db,db.begin():
        article=db.get(NewsArticle,article_id);article.article_text=BODY+' Revised source.'
        enqueue_article(db,article,mode='ner_rules_v1',pipeline_version=operational_trusted.pipeline_version)
    assert process_news_publications(c3b_db,policy=current,clock=lambda:NOW,sources=SOURCES).published==0


@pytest.mark.asyncio
async def test_native_pipeline_rejects_production_before_assets_or_storage():
    from app.services.news_ner_durable.pipeline import run_native_news_pipeline
    from app.services.news_ner_durable.contracts import NerEvidenceError
    from sqlalchemy.engine import URL
    def forbidden():pytest.fail('invalid invocation accessed assets or storage')
    with pytest.raises(NerEvidenceError,match='ner_configuration_invalid'):
        await run_native_news_pipeline(forbidden,load_assets=forbidden,environment='production',
            database_url=URL.create('postgresql+psycopg',database='lanes_p3_verify_forbidden').render_as_string(hide_password=False),sources=())


@pytest.mark.asyncio
async def test_native_pipeline_reserves_time_for_downstream_and_stops_claiming(c3b_db,operational_trusted,monkeypatch):
    from contextlib import contextmanager
    from app.models.setting import SystemSetting
    from app.services.configuration_service import read_configuration,CONFIG_KEY
    from app.services.news_ner_durable import pipeline
    from app.services.news_ner_durable.processing import NativeProcessingSummary,OperationDeadline
    with c3b_db() as db,db.begin():
        config=read_configuration(db).model_copy(update={'news_collection_enabled':False,'news_publication_enabled':False})
        db.add(SystemSetting(key=CONFIG_KEY,value={'revision':1,'settings':config.model_dump(mode='json')}))
        url=db.get_bind().url.render_as_string(hide_password=False)
    @contextmanager
    def fictional_deadline(seconds):
        if seconds<=0:raise OperationDeadline()
        yield
    monkeypatch.setattr(pipeline,'deadline',fictional_deadline)
    ticks=[0.0];captured=[]
    def stage(name,summary):
        if name=='collection' and summary is not None:ticks[0]=350.0
    async def stopped(*_args,**kwargs):
        captured.append(kwargs['invocation_deadline'])
        return NativeProcessingSummary(stop_reason='budget_exhausted')
    monkeypatch.setattr(pipeline,'process_native_saved_news',stopped)
    result=await pipeline.run_native_news_pipeline(c3b_db,load_assets=lambda:operational_trusted,
        environment='test',database_url=url,sources=SOURCES,monotonic=lambda:ticks[0],clock=lambda:NOW,on_stage=stage)
    assert captured==[470.0] and result['error_code'] is None,result
    assert result['extraction']['stop_reason']=='budget_exhausted'


@pytest.mark.asyncio
async def test_native_pipeline_exhausted_invocation_is_explicit(c3b_db,operational_trusted,monkeypatch):
    from contextlib import contextmanager
    from app.services.news_ner_durable import pipeline
    from app.services.news_ner_durable.processing import OperationDeadline
    @contextmanager
    def expired(_seconds):raise OperationDeadline();yield
    monkeypatch.setattr(pipeline,'deadline',expired)
    with c3b_db() as db:url=db.get_bind().url.render_as_string(hide_password=False)
    result=await pipeline.run_native_news_pipeline(c3b_db,load_assets=lambda:operational_trusted,
        environment='test',database_url=url,sources=SOURCES)
    assert result['error_code']=='ner_pipeline_budget_exhausted' and result['stop_reason']=='budget_exhausted'


@pytest.mark.asyncio
async def test_short_remaining_extraction_budget_does_not_authenticate_or_capture():
    from app.services.news_ner_durable.processing import process_native_saved_news
    from sqlalchemy.engine import URL
    def forbidden():pytest.fail('insufficient remaining time still accessed assets or storage')
    result=await process_native_saved_news(forbidden,load_assets=forbidden,environment='test',
        database_url=URL.create('postgresql+psycopg',database='lanes_p3_verify_budget').render_as_string(hide_password=False),
        monotonic=lambda:10.0,invocation_deadline=100.0)
    assert result.stop_reason=='budget_exhausted' and result.completed==result.captured==0
