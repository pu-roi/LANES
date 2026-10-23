"""Inline locality is retained context only after its exact road passes."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import json
import httpx
import pytest

from app.services.news_ner_durable.scoped_resolution_v4 import CONTRACT,evaluate_rows,source_layout
from app.services.news_ner_durable.assets import with_resolution_assets
from app.services.news_ner_durable.adapter import verify_saved_result
from app.services.news_ner_durable.resolution import targets,apply_resolution,ResolutionError
from app.services.news_ner_durable.contracts import sha
from app.services.news_source_repair_resolver import SourceRepairResolver
from app.services.news_gma_inline_continuation import InlineBatchPlan,batch_manifest,require_three_observations
from test_news_scoped_resolution_v3 import case as original_case,row,parsed,TEXT
from test_news_ner_durable import trusted,make_case
from test_news_gemini_receipts import envelope
from test_news_native_resolution import answer

RETAINED=json.loads((Path(__file__).parent/'fixtures/gma_plain_list_extra_locality_response.json').read_text(encoding='utf-8'))['results']


def case(trusted):
    old,_,context,baseline,parent,original=original_case(trusted)
    service=SourceRepairResolver(old.config,evidence_contract=CONTRACT,batch_plan=InlineBatchPlan(batch_manifest()))
    derived=with_resolution_assets(trusted,service.identity);service.catalog=derived.catalog
    context=context.model_copy(update={'pipeline_version':derived.pipeline_version})
    # Only source provenance changes; the pre-resolution graph is unchanged.
    from app.services.news_ner_durable.adapter import build_native_result
    from app.services.news_ner.location_pipeline import from_neural_mentions
    proposal=from_neural_mentions({**context.source().runtime_request(context.input_fingerprint),
        'mentions':[m.model_dump(mode='json') for m in baseline.native.neural_mentions]})['proposal']
    raw={'proposal':proposal,
        'graph':baseline.native.graph.model_dump(mode='json',by_alias=True),'measurements':baseline.measurements,
        'provenance':baseline.provenance['runtime']}
    baseline=build_native_result(context,raw,derived,extracted_at=baseline.extracted_at)
    return service,derived,context,baseline,parent,original


def test_real_retained_barangay_becomes_owned_context_without_row_rewrite(trusted):
    _,_,context,baseline,_,_=case(trusted);before=deepcopy(RETAINED)
    claims,groups,_,outcomes,_=evaluate_rows(context.source(),baseline,parsed(RETAINED),trusted.catalog)
    assert len(claims)==1 and RETAINED==before
    assert next(o for o in outcomes if o['target_id']=='n7')['outcome']=='context_only'
    context_group=next(g for g in groups if g['target_entity_ids']==['n7'])
    assert context_group['claim_index'] is None and context_group['normalizations']['inline_locality_owner']['target_id']=='n6'
    assert claims[0].canonical_barangay=='San Agustin'


@pytest.mark.parametrize('change',[{'city':None},{'clock_text':'3 PM'},{'depth_text':'waist deep'},
    {'access':'impassable_all'},{'depth_evidence':[10]}])
def test_unsupported_owner_or_conflict_does_not_silently_suppress_locality(trusted,change):
    _,_,context,baseline,_,_=case(trusted);rows=deepcopy(RETAINED)
    next(r for r in rows if r['target_id']=='n6').update(change)
    _,_,_,outcomes,_=evaluate_rows(context.source(),baseline,parsed(rows),trusted.catalog)
    assert next(o for o in outcomes if o['target_id']=='n7')['outcome']!='context_only'


@pytest.mark.parametrize('text',[
    'Malabon City\nRizal Ave Extn and Road B Brgy San Agustin - Gutter deep',
    'Malabon City\nRizal Ave Extn was flooded. Brgy San Agustin was flooded too.',
    'Malabon City\nRizal Ave Extn Brgy San Agustin - The entire barangay was flooded gutter deep.',
    'Malabon City\nBrgy San Agustin - Gutter deep\nRizal Ave Extn - Gutter deep'])
def test_independent_clauses_multiple_roads_and_locality_only_are_not_inline(text):
    names=[('Malabon City','CITY'),('Rizal Ave Extn','ROAD'),('Road B','ROAD'),('Brgy San Agustin','BARANGAY')]
    candidates=[dict(id=name,text=name,label=label,start=text.index(name),end=text.index(name)+len(name)) for name,label in names if name in text]
    assert all('inline_locality_owner' not in s for s in source_layout(text,candidates)['targets'])


def test_genuine_barangay_only_observation_remains_accepted(trusted):
    text='On September 9, 2026\nMalabon City\nBrgy San Agustin was flooded gutter deep as of 2:47 p.m.'
    _,_,context,_,baseline=make_case(trusted,text,labels=[('Malabon City','CITY'),('Brgy San Agustin','BARANGAY')])
    target=next(t for t in targets(baseline) if t['label']=='BARANGAY')
    value=answer(target,verdict='observed',city='Malabon City',barangay='Brgy San Agustin',place_evidence=[1,2],
        status='active',status_evidence=[2],time_role='observation',date_text='September 9, 2026',clock_text='2:47 p.m.',
        time_evidence=[0,2],depth_text='gutter deep',depth_scope='individual',depth_evidence=[2])
    claims,_,_,outcomes,_=evaluate_rows(context.source(),baseline,parsed([value]),trusted.catalog)
    assert len(claims)==1 and outcomes[0]['outcome']=='accepted'


@pytest.mark.asyncio
async def test_full_three_observation_result_preserves_context_and_raw_label(trusted):
    service,derived,context,baseline,parent,original=case(trusted)
    # This test mocks all three batches; adoption has separate authenticated tests.
    service.batch_plan.adopt=lambda *args:None
    def handler(request):
        document=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        rows=RETAINED if document['targets'][0]['id']=='n4' else [row(t) for t in document['targets']]
        return httpx.Response(200,json=envelope(rows))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        payload=await service.resolve(context.source(),baseline,parent_run_id=parent.id,parent_result_sha256=sha(original.model_dump(mode='json')),client=client)
    result=apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)
    require_three_observations(result)
    assert len(verify_saved_result(context,result,derived).claims)==3
    assert len(result.projection['groups'])==4
    assert next(m for m in result.native.graph.mentions if m.id=='n10').label=='LANDMARK'
    # The source names Tañong in the quoted section, without explicitly assigning
    # an administrative role. Keeping barangay unknown must not lose that road.
    original_row=next(r for r in payload['results'] if r['target_id']=='n8')
    original_row['barangay']=None
    payload['row_outcomes']=evaluate_rows(context.source(),baseline,parsed(payload['results']),derived.catalog)[3]
    unknown=apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)
    require_three_observations(unknown)
    assert unknown.claims[1].canonical_barangay is None


def test_zero_dispatch_finalizer_budget_never_permits_a_provider_call():
    from scripts.run_news_gma_inline_finalize import NoDispatchBudget
    with pytest.raises(ResolutionError,match='dispatch_forbidden'):NoDispatchBudget().reserve('model',{}, {})


@pytest.mark.asyncio
@pytest.mark.parametrize('tamper',[None,'source','response','model','targets'])
async def test_adopts_two_authenticated_responses_and_sends_only_remaining_batch(trusted,monkeypatch,tamper):
    from app.services.news_gemini_receipts import BatchJournal
    from test_news_gemini_receipts import Receipts
    from app.services import news_gma_inline_continuation as module
    old,_,context,baseline,parent,original=original_case(trusted);storage=Receipts();old.receipts=BatchJournal(storage)
    def old_handler(request):
        doc=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        return httpx.Response(200,json=envelope(RETAINED if doc['targets'][0]['id']=='n4' else [row(t) for t in doc['targets']]))
    async with httpx.AsyncClient(transport=httpx.MockTransport(old_handler)) as client:
        with pytest.raises(ResolutionError,match='unexpected_observation'):
            await old.resolve(context.source(),baseline,parent_run_id=parent.id,parent_result_sha256=sha(original.model_dump(mode='json')),client=client)
    bundles=[]
    for name,intent in storage.items.items():
        if name.endswith('/intent.json'):bundles.append({'intent':intent,'response':storage.items[intent['request_identity']+'/response.json']})
    assert len(bundles)==2
    monkeypatch.setattr(module,'CACHE_PINS',tuple(sha(b) for b in bundles))
    service,derived,context,baseline,parent,original=case(trusted)
    service.batch_plan.cache_loader=lambda index:deepcopy(bundles[index]);service.receipts=BatchJournal(Receipts())
    if tamper=='response':bundles[0]['response']['body_base64']='tampered'
    if tamper=='source':bundles[0]['intent']['payload']['contents'][0]['parts'][0]['text']+='tampered'
    if tamper=='model':bundles[0]['intent']['model']='other-model'
    if tamper=='targets':bundles[0]['intent']['context']['targets_sha256']='0'*64
    calls=[]
    def handler(request):
        doc=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text']);calls.append(doc['targets'][0]['id'])
        return httpx.Response(200,json=envelope([row(t) for t in doc['targets']]))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        if tamper:
            with pytest.raises(ResolutionError):await service.resolve(context.source(),baseline,parent_run_id=parent.id,parent_result_sha256=sha(original.model_dump(mode='json')),client=client)
            assert not calls
        else:
            payload=await service.resolve(context.source(),baseline,parent_run_id=parent.id,parent_result_sha256=sha(original.model_dump(mode='json')),client=client)
            require_three_observations(apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity))
            assert calls==['n8'] and service.last_request_count==1 and len(service.last_usage)==1
