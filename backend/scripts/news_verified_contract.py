"""Fixed fictional transport/projection checks. No model loading or SQL writes.

MockTransport cannot contact Gemini. These are software contract cases, never
provider/model accuracy evidence or article extraction saved to the database.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime,timezone
import json
import re
from types import SimpleNamespace

import httpx

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_ner.location_pipeline import from_neural_mentions
from app.services.news_ner_durable.adapter import build_native_result,verify_saved_result
from app.services.news_ner_durable.assets import with_resolution_assets
from app.services.news_ner_durable.contracts import RunEvidence,capture_native_input,sha
from app.services.news_ner_durable.read_projection import build_read_projection
from app.services.news_ner_durable.resolution import ResolutionError,apply_resolution,targets,resolution_audit

NOW=datetime(2026,10,20,3,tzinfo=timezone.utc)


def fixture(trusted: object, text: str) -> tuple:
    article=NewsArticleExtractorInput(article_id=1,canonical_url='https://example.org/contract-only',
        publisher='fictional',title='Cloud software contract; not a real event',article_text=text,published_at=NOW)
    snapshot,fingerprint=capture_native_input(article)
    version=SimpleNamespace(id=1,article_id=1,input_snapshot=snapshot,input_fingerprint=fingerprint)
    run=SimpleNamespace(id=1,article_version_id=1,mode='ner_rules_v1',pipeline_version=trusted.pipeline_version)
    context=RunEvidence.from_records(run,version);request=context.source().runtime_request(fingerprint)
    mentions=[]
    for name,label in (('Fictional Crescent','ROAD'),('Pasig City','CITY')):
        for m in re.finditer(re.escape(name),text):
            mentions.append({'id':'pending','start':m.start(),'end':m.end(),'text':m.group(),'label':label,
                'provenance_sha256':sha({'bundle':trusted.provenance['bundle_sha256'],
                    'tokenizer':trusted.provenance['tokenizer_sha256'],'text':request['text_sha256']})})
    mentions.sort(key=lambda m:m['start'])
    for i,m in enumerate(mentions):m['id']='m'+str(i)
    raw={**from_neural_mentions({**request,'mentions':mentions}), 'provenance':trusted.provenance,
         'measurements':{'extraction_seconds':0.001,'peak_worker_rss_bytes':0}}
    return context,raw,build_native_result(context,raw,trusted,extracted_at=NOW)


def row(target: dict, *, fallback: bool=False) -> dict:
    value={'target_id':target['id'],'verdict':'unsupported','city':None,'barangay':None,'place_evidence':[],
        'status':'unclear','historical':False,'contradictory':False,'status_evidence':[],
        'time_role':'unknown','date_text':None,'clock_text':None,'contemporaneous':False,'time_evidence':[],
        'depth_text':None,'depth_scope':'unknown','depth_evidence':[],'access':'unknown',
        'access_evidence':[],'road_section':None,'section_evidence':[]}
    if target['label']=='ROAD':
        value.update(verdict='observed',city='Pasig City',place_evidence=[0],status='active',status_evidence=[0],
            time_role='observation',date_text='Today' if fallback else 'October 20, 2026',
            clock_text=None if fallback else '10 AM',contemporaneous=fallback,time_evidence=[0],
            depth_text='knee-deep',depth_scope='individual',depth_evidence=[0])
    return value


async def check_contract(trusted: object, resolver: object) -> dict:
    # Fixed fictional transport cases never write the live receipt bucket.
    # Receipt retention/replay has separate failure-path tests with private stores.
    receipts=getattr(resolver,'receipts',None)
    batch_plan=getattr(resolver,'batch_plan',None)
    resolver.receipts=None
    resolver.batch_plan=None
    try:
        return await _check_contract(trusted,resolver)
    finally:
        resolver.receipts=receipts
        resolver.batch_plan=batch_plan


async def _check_contract(trusted: object, resolver: object) -> dict:
    derived=with_resolution_assets(trusted,resolver.identity);checks=[];mock_requests=[]
    for fallback in (False,True):
        text=('Today, ' if fallback else 'On October 20, 2026 as of 10 AM, ')+\
            'Fictional Crescent in Pasig City was flooded knee-deep.'
        parent_context,raw,parent=fixture(trusted,text)
        parent_hash=sha(parent.model_dump(mode='json',by_alias=True))
        context=RunEvidence.model_validate({**parent_context.model_dump(),'run_id':2,'pipeline_version':derived.pipeline_version})
        baseline=build_native_result(context,raw,derived,extracted_at=NOW)
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.host=='generativelanguage.googleapis.com'
            doc=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
            assert doc['evidence_text']==text and doc['native_facts']==baseline.native.graph.model_dump(mode='json',by_alias=True)['facts']
            mock_requests.append({'source_sha256':sha(text),'target_count':len(doc['targets'])})
            return httpx.Response(200,json={'modelVersion':resolver.identity['model'],
                'usageMetadata':{'promptTokenCount':1,'candidatesTokenCount':1},
                'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps({'results':[row(m,fallback=fallback) for m in doc['targets']]})}]}}]})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            payload=await resolver.resolve(context.source(),baseline,parent_run_id=1,parent_result_sha256=parent_hash,client=client)
        result=apply_resolution(context.source(),baseline,payload,derived.catalog,resolver.identity)
        result.read_projection=build_read_projection(context.source(),result,derived.catalog)
        observed=result.claims[0].event_time_resolved
        assert observed==NOW if fallback else observed.isoformat()=='2026-10-20T10:00:00+08:00'
        assert sha(parent.model_dump(mode='json',by_alias=True))==parent_hash
        assert verify_saved_result(context,result,derived).claims[0].event_time_resolved==observed
        assert resolution_audit(context,result,0).outcome=='verified'
        checks.append('publication_fallback' if fallback else 'quoted_clock_and_saved_recomputation')
        if not fallback:
            edited=deepcopy(payload);next(r for r in edited['results'] if r['verdict']=='observed')['clock_text']='11 PM'
            try:apply_resolution(context.source(),baseline,edited,derived.catalog,resolver.identity)
            except ResolutionError:checks.append('unsupported_clock_rejected')
            else:raise ValueError('contract_unsupported_clock_accepted')
            for status in (401,429,503,302):
                calls=[]
                def failed(request: httpx.Request) -> httpx.Response:
                    calls.append(request.url.host)
                    return httpx.Response(status,headers={'location':'https://example.org/never-forward-key'})
                async with httpx.AsyncClient(transport=httpx.MockTransport(failed),follow_redirects=True) as client:
                    try:await resolver.resolve(context.source(),baseline,parent_run_id=1,parent_result_sha256=parent_hash,client=client)
                    except ResolutionError as exc:assert exc.retryable==(status in (429,503))
                    else:raise ValueError('contract_failed_response_accepted')
                assert len(calls)==1;checks.append('http_'+str(status)+'_no_retry_or_redirect')
    return {'status':'passed','checks':checks,'mock_requests':len(mock_requests),
            'external_provider_requests':0,'database_writes':0,'model_inferences':0,
            'fixture_kind':'source_authored_neural_mentions_not_model_predictions'}
