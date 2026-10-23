"""Receipt-backed accounting stays independent from source-fact acceptance."""
from copy import deepcopy
import base64
import hashlib
import json

import httpx
import pytest

from app.services.news_pilot_accounting import (AccountedPilotBudget,accounting_policy,
    authenticated_response,commitment,count_request,reservation,usage_estimate,VERSION)
from app.services.news_pilot_budget import PilotBudget,MODEL,new_ledger
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_gma_budget_review import GmaBudgetBatchPlan,batch_manifest,qualify_schedule,REQUESTS
from app.services.news_gemini_receipts import BatchJournal,request_batch
from test_news_pilot_budget import Store,payload
from app.services.news_claim_auditor import AuditorConfig


class Objects:
    def __init__(self):self.objects={}
    def put(self,key,value):
        if key in self.objects:raise ResolutionError('immutable_object_exists')
        self.objects[key]=deepcopy(value)
    def get(self,key):return deepcopy(self.objects[key])


def ledger():
    store=Store();state=store.state
    state['attempts']=[{'id':sha(i),'reserved_nanodollars':30_000_000,'status':'failed'} for i in range(20)]
    state.update(schema_version=VERSION,accounting_policy_sha256=sha(accounting_policy()),
        legacy_attempts_sha256=sha(state['attempts']),settlements=[])
    return store


def catalog(p):
    item={'request_sha256':sha(p),'total_tokens':6000,'model':MODEL,
        'accounting_policy_sha256':sha(accounting_policy()),'reserved_nanodollars':reservation(p,6000)}
    return {'schema_version':'news-pilot-count-catalog-v2','accounting_policy_sha256':sha(accounting_policy()),'requests':[item]}


def budget(store,p,objects):
    counts=catalog(p)
    return AccountedPilotBudget(store,'selection',counts=counts,counts_sha256=sha(counts),journal=objects)


def envelope(**changes):
    return {'modelVersion':MODEL,'usageMetadata':{'promptTokenCount':6349,'candidatesTokenCount':1005,
        'totalTokenCount':7354,**changes},'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'invalid JSON'}]}}]}


def test_usage_totals_include_thinking_and_preserve_conservative_unknowns():
    assert usage_estimate(200,envelope())['usage_estimate_nanodollars']==4_417_200
    assert usage_estimate(200,envelope(thoughtsTokenCount=100,totalTokenCount=7454))['usage_estimate_nanodollars']==4_667_200
    for value in (envelope(totalTokenCount=7355),envelope(promptTokenCount=True),envelope(thoughtsTokenCount=-1),
            envelope(toolUsePromptTokenCount=1),envelope(serviceTier='flex'),{'usageMetadata':{}},[]):
        with pytest.raises(ResolutionError):usage_estimate(200,value)


@pytest.mark.parametrize('status',[400,500])
def test_only_evidenced_documented_provider_errors_settle_to_zero(status):
    assert usage_estimate(status,{'error':{'code':status}})['usage_estimate_nanodollars']==0
    with pytest.raises(ResolutionError):usage_estimate(status,{'error':{'code':str(status)}})
    with pytest.raises(ResolutionError):usage_estimate(429,{'error':{'code':429}})


def test_old_workers_reject_v2_and_first_twenty_attempts_are_immutable():
    store=ledger();p=payload();objects=Objects();b=budget(store,p,objects)
    old=deepcopy(store.state['attempts']);key=b.reserve(MODEL,p,{})
    with pytest.raises(ResolutionError,match='identity'):PilotBudget(store,'selection')._read()
    b.finish(key,succeeded=False)
    assert store.state['attempts'][:20]==old and commitment(store.state)>600_000_000
    store.state['attempts'][0]['reserved_nanodollars']=1
    with pytest.raises(ResolutionError,match='identity'):b._read()


@pytest.mark.asyncio
async def test_http200_invalid_facts_are_accounted_before_validation():
    p=payload();store=ledger();objects=Objects();b=budget(store,p,objects)
    config=AuditorConfig(provider='gemini',model=MODEL,gemini_api_key='fake-offline')
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,json=envelope()))) as client:
        with pytest.raises(ResolutionError):await request_batch(config,p,{},http=client,timeout=5,budget=b,journal=BatchJournal(objects))
    assert len(store.state['settlements'])==1
    assert store.state['settlements'][0]['usage_estimate_nanodollars']==4_417_200
    assert store.state['status']=='stopped' and store.state['attempts'][-1]['status']=='failed'
    assert commitment(store.state)==604_417_200
    assert any(k.endswith('/response.json') for k in objects.objects)


@pytest.mark.asyncio
async def test_missing_usage_keeps_full_reservation_and_blocks_resend():
    p=payload();store=ledger();objects=Objects();b=budget(store,p,objects)
    config=AuditorConfig(provider='gemini',model=MODEL,gemini_api_key='fake-offline')
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={}))) as client:
        with pytest.raises(ResolutionError):await request_batch(config,p,{},http=client,timeout=5,budget=b,journal=BatchJournal(objects))
    assert store.state['settlements']==[] and commitment(store.state)==600_000_000+reservation(p,6000)
    store.state['status']='ready'
    with pytest.raises(ResolutionError,match='already_reserved'):b.reserve(MODEL,p,{})


@pytest.mark.asyncio
async def test_count_exact_full_request_and_receipt_pinning():
    p=payload();objects=Objects();calls=[]
    def respond(request):
        calls.append(request)
        assert json.loads(request.content)=={'generateContentRequest':{'model':'models/'+MODEL,**p}}
        assert str(request.url).endswith(':countTokens')
        return httpx.Response(200,json={'totalTokens':6000})
    config=AuditorConfig(provider='gemini',model=MODEL,gemini_api_key='fake-offline')
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        receipt=await count_request(config,p,http=client,journal=objects)
        with pytest.raises(ResolutionError,match='exists'):await count_request(config,p,http=client,journal=objects)
    assert len(calls)==1 and receipt['reserved_nanodollars']==reservation(p,6000)
    assert 'fake-offline' not in json.dumps(objects.objects)


def test_manifest_four_targets_and_no_new_generation_for_first_cached_batch():
    plan=GmaBudgetBatchPlan(batch_manifest());targets=[{'id':'n'+str(i)} for i in range(51)]
    assert [len(b) for b in plan.batches(targets)]==[4]*12+[3]
    with pytest.raises(ResolutionError):plan.batches(targets[::-1])
    assert len(REQUESTS)==13 and len(set(REQUESTS))==13


def test_tampered_catalog_concurrency_cap_and_uncertain_dispatch():
    p=payload();objects=Objects();store=ledger();b=budget(store,p,objects)
    before,generation=store.read();b.reserve(MODEL,p,{})
    with pytest.raises(ResolutionError,match='concurrent'):store.compare_and_swap(generation,before)
    with pytest.raises(ResolutionError,match='in_flight'):b.reserve(MODEL,p,{'different':True})
    b.counts['requests'][0]['total_tokens']=1
    with pytest.raises(ResolutionError,match='catalog_changed'):b.reserve(MODEL,p,{})
    store=ledger();store.state['attempts'][0]['reserved_nanodollars']=500_000_000
    store.state['legacy_attempts_sha256']=sha(store.state['attempts'])
    with pytest.raises(ResolutionError,match='exhausted'):budget(store,p,objects).reserve(MODEL,p,{})


def test_retained_response_cannot_be_tampered_or_bound_to_another_request():
    p=payload();context={};key=sha({'request_sha256':sha(p),'context':context})
    raw=json.dumps(envelope()).encode()
    bundle={'intent':{'schema_version':'news-gemini-batch-intent-v1','request_identity':key,
        'request_sha256':sha(p),'context':context,'payload':p,'model':MODEL,'budget_reservation_id':key},
        'response':{'schema_version':'news-gemini-batch-response-v1','request_identity':key,
        'body_base64':base64.b64encode(raw).decode(),'body_sha256':hashlib.sha256(raw).hexdigest(),
        'replayable':True,'http_status':200}}
    pin=sha(bundle);assert authenticated_response(bundle,pin)[1]['input_tokens']==6349
    bundle['intent']['payload']['contents']=[]
    with pytest.raises(ResolutionError):authenticated_response(bundle,pin)


@pytest.mark.asyncio
@pytest.mark.parametrize('status',[400,500])
async def test_provider_error_is_retained_settled_and_stopped(status):
    p=payload();store=ledger();objects=Objects();b=budget(store,p,objects)
    config=AuditorConfig(provider='gemini',model=MODEL,gemini_api_key='fake-offline')
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(status,json={
            'error':{'code':status,'status':'INVALID_ARGUMENT','message':'Synthetic provider error'}}))) as client:
        with pytest.raises(ResolutionError,match='http_error'):
            await request_batch(config,p,{},http=client,timeout=5,budget=b,journal=BatchJournal(objects))
    assert commitment(store.state)==600_000_000 and store.state['status']=='stopped'
    assert store.state['settlements'][0]['usage_estimate_nanodollars']==0


@pytest.mark.asyncio
@pytest.mark.parametrize('indexes',[[0,0],[-1],[999]])
async def test_invalid_evidence_keeps_actual_usage_without_accepting_facts(indexes):
    from test_news_gemini_receipts import packet,envelope as response_envelope,CONFIG
    from test_news_native_resolution import answer
    p=packet();store=ledger();objects=Objects();b=budget(store,p,objects)
    value=response_envelope([answer({'id':'m0','label':'CITY'},place_evidence=indexes)])
    value['usageMetadata']['totalTokenCount']=30
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,json=value))) as client:
        with pytest.raises(ResolutionError,match='evidence_invalid'):
            await request_batch(CONFIG,p,{},http=client,timeout=5,budget=b,journal=BatchJournal(objects))
    assert commitment(store.state)==600_053_000 and store.state['status']=='stopped'


@pytest.mark.asyncio
@pytest.mark.parametrize('fail_at,expected_calls',[('intent.json',0),('response.json',1),('accounting.json',1)])
async def test_receipt_storage_failure_retains_maximum_and_blocks_next_request(fail_at,expected_calls):
    class Broken(Objects):
        def put(self,key,value):
            if key.endswith(fail_at):raise ResolutionError('synthetic_storage_failed')
            super().put(key,value)
    p=payload();store=ledger();objects=Broken();b=budget(store,p,objects);calls=[]
    config=AuditorConfig(provider='gemini',model=MODEL,gemini_api_key='fake-offline')
    def respond(request):calls.append(1);return httpx.Response(200,json=envelope())
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(ResolutionError):await request_batch(config,p,{},http=client,timeout=5,budget=b,journal=BatchJournal(objects))
        with pytest.raises(ResolutionError):await request_batch(config,p,{},http=client,timeout=5,budget=b,journal=BatchJournal(objects))
    assert len(calls)==expected_calls and store.state['settlements']==[]
    assert commitment(store.state)==600_000_000+reservation(p,6000)
