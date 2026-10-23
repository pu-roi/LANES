"""Disposable PostGIS, mocked provider: partial acceptance and honest usage."""
import json

import httpx
import pytest
from sqlalchemy import text

from app.models.news import NewsExtractionRun
from app.services.news_ner_durable.assets import with_resolution_assets
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution_worker import resolve_native_runs
from test_news_ner_integration import c3b_db, operational_trusted, base_trusted, save_native, view, SOURCES
from test_news_scoped_resolution import case, LIST, LABELS, list_answer
from test_news_ner_durable import NOW


@pytest.mark.asyncio
async def test_partial_results_persist_and_reuse_without_provider_or_duplicate_claims(c3b_db,operational_trusted):
    raw_id,_=save_native(c3b_db,operational_trusted,body=LIST,labels=LABELS)
    with c3b_db() as db:
        parent_sha=sha(db.get(NewsExtractionRun,raw_id).result)
    service,_,_,_,_,_=case(operational_trusted)
    derived=with_resolution_assets(operational_trusted,service.identity);calls=[]
    def handler(request):
        doc=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        rows=[list_answer(m) for m in doc['targets']]
        for r in rows:
            if any(m['id']==r['target_id'] and m['text']=='Fictional Crescent' for m in doc['targets']):
                r['time_evidence']=[2]  # Legal reference, missing supported date.
        calls.append(1)
        return httpx.Response(200,json={'usageMetadata':{'promptTokenCount':10,'candidatesTokenCount':20,'thoughtsTokenCount':3},
            'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps({'results':rows})}]}}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        first=await resolve_native_runs(c3b_db,(raw_id,),trusted=operational_trusted,resolver=service,
                                       sources=SOURCES,clock=lambda:NOW,client=client)
        assert first['completed']==1 and first['request_count']==2
        assert (first['input_tokens'],first['output_tokens'],first['thinking_tokens'])==(20,40,6)
        with c3b_db() as db:
            saved=db.get(NewsExtractionRun,first['runs'][0]['run_id'])
            assert len(saved.result['claims'])==2
            assert len([r for r in saved.result['projection']['resolution_outcomes'] if r['outcome']=='unresolved'])==1
        repeated=await resolve_native_runs(c3b_db,(raw_id,),trusted=operational_trusted,resolver=service,
                                         sources=SOURCES,clock=lambda:NOW,client=client)
    assert repeated['reused']==1 and repeated['request_count']==0 and len(calls)==2
    assert view(c3b_db,derived).total==2
    with c3b_db() as db:
        assert sha(db.get(NewsExtractionRun,raw_id).result)==parent_sha
        for table in ('flood_events','flood_avoidance_zones','flood_reports'):
            assert db.scalar(text('SELECT count(*) FROM '+table))==0


@pytest.mark.asyncio
async def test_failed_legacy_semantics_keeps_provider_usage_in_worker_summary(c3b_db,operational_trusted):
    from test_news_native_resolution import resolver, answer, TEXT
    raw_id,_=save_native(c3b_db,operational_trusted,body=TEXT);service=resolver()
    def handler(request):
        doc=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        rows=[answer(m) for m in doc['targets']]
        for r in rows:
            if r['verdict']=='observed':r['clock_text']='11 PM'
        return httpx.Response(200,json={'usageMetadata':{'promptTokenCount':12,'candidatesTokenCount':23,'thoughtsTokenCount':4},
            'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps({'results':rows})}]}}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result=await resolve_native_runs(c3b_db,(raw_id,),trusted=operational_trusted,resolver=service,
                                         sources=SOURCES,clock=lambda:NOW,client=client)
    assert result['failed']==1 and result['request_count']==1
    assert (result['input_tokens'],result['output_tokens'],result['thinking_tokens'])==(12,23,4)
