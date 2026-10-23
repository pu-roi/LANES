"""Real migrated disposable PostGIS plus mocked Gemini; parent runs stay immutable."""
import asyncio
from datetime import timedelta
import json

import httpx
import pytest
from sqlalchemy import select,func,text

from app.models.news import NewsExtractionRun,NewsArticleVersion
from app.models.news_publication import NewsClaimEvaluation,NewsClaimDecision
from app.services.news_ner_durable.assets import with_resolution_assets
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_ner_durable.resolution_worker import resolve_native_runs,resolution_preflight
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.evaluation import seed_native_evaluations,evaluate_native_claims
from app.services.news_ner_durable.readers import read_native_group
from app.services.news_publication_service import process_news_publications
from test_news_ner_integration import c3b_db,operational_trusted,base_trusted,save_native,view,policy,SOURCES
from test_news_native_resolution import resolver,answer,TEXT,NOW


def client_with(calls, *, status=200, after=None):
    def handler(request):
        document=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        calls.append(document)
        if after:after()
        return httpx.Response(status,json={'candidates':[{'finishReason':'STOP','content':{'parts':[
            {'text':json.dumps({'results':[answer(m) for m in document['targets']]})}]}}]})
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_handoff_readers_evaluation_publication_and_repeat(c3b_db,operational_trusted,monkeypatch):
    from app.services.news_ner_runtime.supervisor import Session
    async def forbidden(*_args,**_kwargs):pytest.fail('Resolution reran neural inference')
    monkeypatch.setattr(Session,'start',forbidden)
    raw_id,_=save_native(c3b_db,operational_trusted,body=TEXT)
    with c3b_db() as db:
        original=sha(db.get(NewsExtractionRun,raw_id).result)
    service=resolver();derived=with_resolution_assets(operational_trusted,service.identity);calls=[]
    async with client_with(calls) as client:
        result=await resolve_native_runs(c3b_db,(raw_id,),trusted=operational_trusted,resolver=service,sources=SOURCES,clock=lambda:NOW,client=client)
        assert result['completed']==1 and len(calls)==1
        repeated=await resolve_native_runs(c3b_db,(raw_id,),trusted=operational_trusted,resolver=service,sources=SOURCES,clock=lambda:NOW,client=client)
        assert repeated['reused']==1 and len(calls)==1
    page=view(c3b_db,derived)
    assert page.total==1 and page.items[0].summary.flood_time.isoformat()=='2026-10-20T10:00:00+08:00'
    with c3b_db() as db:
        item=page.items[0]
        detail=read_native_group(db,item.run_id,item.group_id,{'fictional':'Fictional'})
        assert detail.claim.event_time_resolved==page.items[0].summary.flood_time
        assert sha(db.get(NewsExtractionRun,raw_id).result)==original
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun))==2
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion))==1
        assert db.scalar(text('SELECT count(*) FROM flood_reports'))==0
    current_policy=policy(c3b_db,derived)
    assert current_policy.auditor_identity['provider']=='gemini'
    seeded=seed_native_evaluations(c3b_db,current_policy,now=NOW,sources=SOURCES)
    assert seeded.evaluations_created==1
    evaluated=evaluate_native_claims(c3b_db,current_policy,clock=lambda:NOW,sources=SOURCES)
    assert evaluated.completed==1 and not evaluated.failed
    published=process_news_publications(c3b_db,policy=current_policy,clock=lambda:NOW,sources=SOURCES)
    with c3b_db() as db:
        value=db.scalar(select(NewsClaimEvaluation)).result
        assert value['audit']['provider']=='gemini' and value['audit']['outcome']=='verified'
        decisions=list(db.scalars(select(NewsClaimDecision)))
        assert decisions and all(d.reason_code not in {'source_ner_evidence_mismatch','audit_identity_mismatch'} for d in decisions)
        assert all(d.public_state=='active_alert' for d in decisions)
        assert db.scalar(text('SELECT count(*) FROM flood_avoidance_zones'))==0
    assert seed_native_evaluations(c3b_db,current_policy,now=NOW,sources=SOURCES).evaluations_created==0


@pytest.mark.asyncio
async def test_provider_retry_reuses_parent_without_extra_neural_run(c3b_db,operational_trusted):
    raw_id,_=save_native(c3b_db,operational_trusted,body=TEXT);service=resolver();calls=[]
    async with client_with(calls,status=429) as client:
        first=await resolve_native_runs(c3b_db,(raw_id,),trusted=operational_trusted,resolver=service,sources=SOURCES,clock=lambda:NOW,client=client)
    assert first['retry_wait']==1 and len(calls)==1
    async with client_with(calls) as client:
        resumed=await resolve_native_runs(c3b_db,(raw_id,),trusted=operational_trusted,resolver=service,sources=SOURCES,clock=lambda:NOW+timedelta(minutes=2),client=client)
    assert resumed['completed']==1 and len(calls)==2
    with c3b_db() as db:
        rows=list(db.scalars(select(NewsExtractionRun).order_by(NewsExtractionRun.id)))
        assert len(rows)==2 and rows[0].attempt_count==1 and rows[1].attempt_count==2


@pytest.mark.asyncio
async def test_concurrent_workers_only_send_one_request(c3b_db,operational_trusted):
    raw_id,_=save_native(c3b_db,operational_trusted,body=TEXT);service=resolver();calls=[]
    async def handler(request):
        document=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text']);calls.append(document)
        await asyncio.sleep(.05)
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps({'results':[answer(m) for m in document['targets']]})}]}}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        results=await asyncio.gather(*(resolve_native_runs(c3b_db,(raw_id,),trusted=operational_trusted,resolver=service,
            sources=SOURCES,clock=lambda:NOW,client=client) for _ in range(2)))
    assert len(calls)==1 and sum(r['completed'] for r in results)==1 and sum(r['busy'] for r in results)==1


@pytest.mark.asyncio
async def test_changed_authority_fails_before_enqueue_or_paid_request(c3b_db,operational_trusted):
    raw_id,_=save_native(c3b_db,operational_trusted,body=TEXT);service=resolver();calls=[]
    authority=resolution_preflight(c3b_db,(raw_id,),operational_trusted,service.identity,SOURCES)
    authority['assets_sha256']='0'*64
    async with client_with(calls) as client:
        with pytest.raises(ResolutionError,match='authority_mismatch'):
            await resolve_native_runs(c3b_db,(raw_id,),trusted=operational_trusted,resolver=service,sources=SOURCES,
                clock=lambda:NOW,client=client,authority=authority,authority_sha256=sha(authority))
    assert not calls
    with c3b_db() as db:assert db.scalar(select(func.count()).select_from(NewsExtractionRun))==1


@pytest.mark.asyncio
async def test_source_suppressed_during_api_call_cannot_commit_corrections(c3b_db,operational_trusted,monkeypatch):
    from app.services.news_ner_durable import resolution_worker
    raw_id,_=save_native(c3b_db,operational_trusted,body=TEXT);service=resolver();calls=[]
    enabled=[True]
    monkeypatch.setattr(resolution_worker,'selected_news_sources',lambda _db,_sources:SOURCES if enabled[0] else ())
    async with client_with(calls,after=lambda:enabled.__setitem__(0,False)) as client:
        result=await resolve_native_runs(c3b_db,(raw_id,),trusted=operational_trusted,resolver=service,sources=SOURCES,clock=lambda:NOW,client=client)
    assert result['failed']==1 and result['runs'][0]['error_code']=='native_resolution_source_suppressed'
    with c3b_db() as db:
        assert db.get(NewsExtractionRun,raw_id).status=='completed'
        derived=db.scalar(select(NewsExtractionRun).where(NewsExtractionRun.id!=raw_id))
        assert derived.status=='failed' and derived.result is None


@pytest.mark.asyncio
@pytest.mark.parametrize('http_status',[200,401])
async def test_rollout_keeps_unprocessed_native_articles_and_never_falls_back_from_failed_verification(c3b_db,operational_trusted,http_status):
    from app.services.news_native_read_context import SavedNativeReadContext
    from app.services.news_historical_processing import database_identity
    from app.services.news_results_service import browse_news_results
    from app.services.news_browsing_service import browse_news_articles
    from app.services.news_collection_service import browse_news_collection
    first,first_article=save_native(c3b_db,operational_trusted,body=TEXT)
    second,second_article=save_native(c3b_db,operational_trusted,body=TEXT)
    service=resolver();derived=with_resolution_assets(operational_trusted,service.identity);calls=[]
    async with client_with(calls,status=http_status) as client:
        result=await resolve_native_runs(c3b_db,(first,),trusted=operational_trusted,resolver=service,sources=SOURCES,clock=lambda:NOW,client=client)
    with c3b_db() as db:
        ctx=SavedNativeReadContext(derived.pipeline_version,database_identity(db.get_bind()),(operational_trusted.pipeline_version,))
        page=browse_news_results(db,page=1,page_size=12,search='',publisher=None,condition=None,placement=None,order='extraction_newest',processing_context=ctx)
        articles=browse_news_articles(db,page=1,page_size=12,search='',publisher=None,body=None,processing=None,order='publication_newest',processing_context=ctx)
        collection=browse_news_collection(db,page=1,page_size=12,search='',publisher=None,status='all',processing_context=ctx)
        assert articles.total==collection.total==2
        selected={a.id:a for a in articles.items}
        assert selected[second_article].latest_run_id==second
        assert selected[first_article].latest_run_id==result['runs'][0]['run_id']
        if http_status==200:
            assert page.total==2 and {i.run_id for i in page.items}=={second,result['runs'][0]['run_id']}
        else:
            assert page.total==1 and page.items[0].run_id==second
            assert selected[first_article].processing_status=='failed'
            assert collection.counts['processing_failed']==1


@pytest.mark.asyncio
async def test_resolution_does_not_modify_existing_citizen_event_report_or_active_zone(c3b_db,operational_trusted):
    from app.models.report import FloodEvent,FloodEventStatus,FloodReport,ReportSource,ReportSeverity,ReportStatus,FloodAvoidanceZone
    from geoalchemy2 import WKTElement
    raw_id,_=save_native(c3b_db,operational_trusted,body=TEXT)
    with c3b_db() as db,db.begin():
        event=FloodEvent(status=FloodEventStatus.ACTIVE,verified_at=NOW,first_reported_at=NOW,peak_severity=ReportSeverity.MEDIUM)
        db.add(event);db.flush()
        zone=FloodAvoidanceZone(event_id=event.id,is_active=True,
            geometry=WKTElement('POLYGON((121.01 14.60,121.02 14.60,121.02 14.61,121.01 14.61,121.01 14.60))',srid=4326))
        db.add(zone);db.flush()
        db.add(FloodReport(event_id=event.id,zone_id=zone.id,user_id=None,raw_text='Fictional existing citizen evidence',
            source=ReportSource.USER_REPORT,severity=ReportSeverity.MEDIUM,status=ReportStatus.APPROVED))
    def fingerprints():
        with c3b_db() as db:
            return {name:db.scalar(text(f"SELECT md5(string_agg(row_to_json(t)::text, '' ORDER BY id)) FROM {name} t"))
                for name in ('flood_events','flood_reports','flood_avoidance_zones')}
    before=fingerprints();service=resolver()
    async with client_with([]) as client:
        result=await resolve_native_runs(c3b_db,(raw_id,),trusted=operational_trusted,resolver=service,sources=SOURCES,clock=lambda:NOW,client=client)
    assert result['completed']==1 and fingerprints()==before


@pytest.mark.asyncio
async def test_native_pipeline_connects_resolution_before_evaluation_and_reuses_it(c3b_db,operational_trusted,monkeypatch):
    from contextlib import contextmanager
    from app.models.setting import SystemSetting
    from app.services.configuration_service import read_configuration,CONFIG_KEY
    from app.services.news_ner_durable import pipeline,processing
    raw_id,_=save_native(c3b_db,operational_trusted,body=TEXT)
    with c3b_db() as db,db.begin():
        configuration=read_configuration(db).model_copy(update={'news_collection_enabled':False,'news_source_ids':['fictional']})
        db.add(SystemSetting(key=CONFIG_KEY,value={'revision':1,'settings':configuration.model_dump(mode='json')}))
        url=db.get_bind().url.render_as_string(hide_password=False)
    @contextmanager
    def fictional_deadline(_seconds):yield
    monkeypatch.setattr(pipeline,'deadline',fictional_deadline)
    monkeypatch.setattr(processing,'deadline',fictional_deadline)
    calls=[];stages=[];service=resolver()
    def forbidden(_trusted):pytest.fail('Pipeline repeated NER inference')
    async with client_with(calls) as client:
        options=dict(load_assets=lambda:operational_trusted,environment='test',database_url=url,sources=SOURCES,
            clock=lambda:NOW,resolver=service,resolution_client=client,runtime_factory=forbidden)
        result=await pipeline.run_native_news_pipeline(c3b_db,**options,on_stage=lambda name,_result:stages.append(name))
        assert result['error_code'] is None and result['stop_reason']=='completed',result
        assert result['resolution']['completed']==1 and result['evaluation']['completed']==1
        assert result['publication']['published']==1
        assert stages.index('resolution')<stages.index('evaluation')<stages.index('publication')
        with c3b_db() as db:
            decisions_before=list(db.scalars(select(NewsClaimDecision.id).order_by(NewsClaimDecision.id)))
        assert decisions_before
        repeated=await pipeline.run_native_news_pipeline(c3b_db,**options)
    assert repeated['error_code'] is None and len(calls)==1
    with c3b_db() as db:
        assert db.scalar(select(func.count()).select_from(NewsExtractionRun))==2
        assert list(db.scalars(select(NewsClaimDecision.id).order_by(NewsClaimDecision.id)))==decisions_before
