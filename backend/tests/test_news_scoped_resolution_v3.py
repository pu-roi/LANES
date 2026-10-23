"""Actual retained GMA layout and failed provider row; no paid calls/inference."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import hashlib
import json
import re

import httpx
import pytest

from app.services.news_ner_durable.scoped_resolution_v3 import source_layout,evaluate_rows,CONTRACT
from app.services.news_ner_durable.scoped_resolution import source_layout as layout_v2,evaluate_rows as evaluate_v2
from app.services.news_ner_durable.resolution import targets,ResolvedMention,apply_resolution,ResolutionError
from app.services.news_ner_durable.contracts import sha,RunEvidence
from app.services.news_ner_durable.adapter import build_native_result,verify_saved_result
from app.services.news_ner_durable.assets import with_resolution_assets
from app.services.news_ner.contract import object_sha
from app.services.news_ner.location_pipeline import from_neural_mentions
from app.services.news_source_repair_resolver import SourceRepairResolver
from app.services.news_gma_heading_repair import HeadingBatchPlan,VERSION,require_three_observations
from app.services.news_gemini_receipts import BatchJournal,replay_bundle
from test_news_ner_durable import trusted,make_case,NOW
from test_news_native_resolution import answer,resolver
from test_news_gemini_receipts import Receipts,envelope

FIXTURE=json.loads((Path(__file__).parent/'fixtures/gma_plain_list_20260909.json').read_text(encoding='utf-8'))
TEXT=FIXTURE['article_text']
LABELS=[('E. Rodriguez','ROAD'),('Araneta Avenue','ROAD'),('Quezon City','CITY'),
    ('E-Rodriguez-Araneta Avenue','ROAD'),('Malabon City','CITY'),('Rizal Ave Extn','ROAD'),
    ('Brgy San Agustin','BARANGAY'),('F. Sevilla Blvd.','ROAD'),('Marikina City','CITY'),('Marcos Highway','LANDMARK')]


def case(trusted):
    run,version,context,_,_=make_case(trusted,TEXT,labels=[])
    request=context.source().runtime_request(context.input_fingerprint)
    mentions=deepcopy(FIXTURE['mentions'])
    provenance=object_sha({'bundle':trusted.provenance['bundle_sha256'],
        'tokenizer':trusted.provenance['tokenizer_sha256'],'text':request['text_sha256']})
    for mention in mentions:mention['provenance_sha256']=provenance
    inference={**from_neural_mentions({**request,'mentions':mentions}),'provenance':trusted.provenance,
        'measurements':{'extraction_seconds':.001,'peak_worker_rss_bytes':0}}
    original=build_native_result(context,inference,trusted,extracted_at=NOW)
    manifest={'schema_version':VERSION,'targets':['n'+str(i) for i in range(11)],
        'required_targets':['n6','n8','n10'],'batch_sizes':[4,4,3]}
    service=SourceRepairResolver(replace(resolver().config,batch_size=4),evidence_contract=CONTRACT,
        batch_plan=HeadingBatchPlan(manifest))
    derived=with_resolution_assets(trusted,service.identity)
    context=context.model_copy(update={'pipeline_version':derived.pipeline_version})
    baseline=build_native_result(context,inference,derived,extracted_at=NOW);service.catalog=derived.catalog
    return service,derived,context,baseline,run,original


def row(target):
    if target['id'] not in ('n6','n8','n10'):
        return answer({**target,'label':'CITY'})
    value=deepcopy(FIXTURE['failed_row']);value['target_id']=target['id']
    index={'n6':9,'n8':10,'n10':12}[target['id']]
    value.update(city='Marikina City' if target['id']=='n10' else 'Malabon City',
        barangay={'n6':'San Agustin','n8':'Tañong','n10':None}[target['id']],
        place_evidence=[11 if target['id']=='n10' else 8,index],status_evidence=[7,index],
        time_evidence=[2,index],depth_evidence=[index],access_evidence=[index],section_evidence=[index],
        road_section={'n6':'Rizal Ave Extn','n8':'Tañong F. Sevilla Blvd. (Bayan)','n10':'Marcos Highway Underloop'}[target['id']],
        depth_text='Gutter Deep' if target['id']=='n10' else 'Gutter deep')
    return value


def parsed(values):return [ResolvedMention.model_validate_json(json.dumps(v),strict=True) for v in values]


def test_actual_plain_list_binds_both_malabon_roads_and_separate_marikina(trusted):
    _,_,context,baseline,_,_=case(trusted)
    assert hashlib.sha256(TEXT.encode()).hexdigest()==FIXTURE['body_sha256']
    layout=source_layout(TEXT,targets(baseline));by={r['target_id']:r for r in layout['targets']}
    assert by['n6']['city_context']==by['n8']['city_context']=={'option_index':8,'exact_text':'Malabon City'}
    assert by['n10']['city_context']=={'option_index':11,'exact_text':'Marikina City'}
    assert by['n5']['context_only_heading'] and by['n9']['context_only_heading']
    assert layout_v2(TEXT,targets(baseline))['heading_passages']==[]
    failed=evaluate_v2(context.source(),baseline,parsed([FIXTURE['failed_row']]),trusted.catalog)
    assert failed[3][0]['issues']==[{'field':'place_evidence','code':'native_resolution_city_evidence_missing'}]


@pytest.mark.asyncio
async def test_complete_gma_v3_roundtrip_retention_and_repeat_offline_replay(trusted):
    service,derived,context,baseline,parent,original=case(trusted);storage=Receipts();service.receipts=BatchJournal(storage)
    calls=[]
    def handler(request):
        doc=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        assert doc['evidence_text']==TEXT and doc['quote_options'][8]['quote']=='Malabon City'
        calls.append([m['id'] for m in doc['targets']]);return httpx.Response(200,json=envelope([row(m) for m in doc['targets']]))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        saved=await service.resolve(context.source(),baseline,parent_run_id=parent.id,parent_result_sha256=sha(original.model_dump(mode='json')),client=client)
    result=apply_resolution(context.source(),baseline,saved,derived.catalog,service.identity)
    require_three_observations(result)
    assert len(verify_saved_result(context,result,derived).claims)==3
    assert list(map(len,calls))==[4,4,3] and len(service.last_usage)==3
    for name,intent in storage.items.items():
        if not name.endswith('/intent.json'):continue
        bundle={'intent':intent,'response':storage.items[intent['request_identity']+'/response.json']}
        assert replay_bundle(bundle,sha(bundle),config=service.config)['provider_requests']==0


@pytest.mark.parametrize('field,value,issue',[
    ('city',None,'city_evidence_missing'),('city','Marikina City','city_scope_mismatch'),
    ('place_evidence',[10],'city_heading_missing'),('place_evidence',[11,10],'scope_mismatch'),
    ('depth_evidence',[9],'fact_target_mismatch'),('clock_text','4 PM','clock_evidence_missing')])
def test_missing_or_borrowed_facts_remain_unresolved(trusted,field,value,issue):
    _,_,context,baseline,_,_=case(trusted);value_row=row(next(m for m in targets(baseline) if m['id']=='n8'))
    value_row[field]=value
    claims,_,_,outcomes,_=evaluate_rows(context.source(),baseline,parsed([value_row]),trusted.catalog)
    assert not claims and any(issue in i['code'] for i in outcomes[0]['issues'])


@pytest.mark.parametrize('interrupt',['The flooding subsided at 11 AM.','Updated: unrelated information.','There is no flooding on Road A.'])
def test_narrative_update_and_clearance_stop_plain_list_context(interrupt):
    text='Malabon City\nRoad A - Gutter deep\n'+interrupt+'\nRoad B - Gutter deep\nMarikina City\nRoad C - Gutter deep'
    candidates=[]
    for name,label in [('Malabon City','CITY'),('Road A','ROAD'),('Road B','ROAD'),('Marikina City','CITY'),('Road C','ROAD')]:
        start=text.index(name);candidates.append(dict(id=name,text=name,label=label,start=start,end=start+len(name)))
    scopes={r['target_id']:r for r in source_layout(text,candidates)['targets']}
    assert scopes['Road A']['city_context']['exact_text']=='Malabon City'
    assert scopes['Road B']['city_context'] is None
    assert scopes['Road C']['city_context']['exact_text']=='Marikina City'


@pytest.mark.asyncio
async def test_required_road_failure_stops_before_last_batch(trusted):
    service,_,context,baseline,parent,original=case(trusted);calls=[]
    def handler(request):
        doc=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text']);calls.append(1)
        values=[row(m) for m in doc['targets']]
        for v in values:
            if v['target_id']=='n6':v['city']=None
        return httpx.Response(200,json=envelope(values))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ResolutionError,match='required_observation_unresolved'):
            await service.resolve(context.source(),baseline,parent_run_id=parent.id,parent_result_sha256=sha(original.model_dump(mode='json')),client=client)
    assert len(calls)==2 and len(service.last_usage)==2


@pytest.mark.asyncio
async def test_retained_extra_barangay_response_stops_before_third_request(trusted):
    fixture=json.loads((Path(__file__).parent/'fixtures/gma_plain_list_extra_locality_response.json').read_text(encoding='utf-8'))
    assert fixture['body_sha256']==FIXTURE['body_sha256']
    service,_,context,baseline,parent,original=case(trusted);calls=[]
    def handler(request):
        doc=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text']);calls.append(1)
        values=fixture['results'] if len(calls)==2 else [row(m) for m in doc['targets']]
        return httpx.Response(200,json=envelope(values))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ResolutionError,match='unexpected_observation'):
            await service.resolve(context.source(),baseline,parent_run_id=parent.id,parent_result_sha256=sha(original.model_dump(mode='json')),client=client)
    assert len(calls)==2 and len(service.last_usage)==2
