"""Paid work must be retained and fail closed; all transport here is synthetic."""
import asyncio
import base64
from copy import deepcopy
from dataclasses import replace
import json
import socket
from unittest.mock import patch

import httpx
import pytest

from app.services.news_claim_auditor import AuditorConfig
from app.services.news_gemini_receipts import BatchJournal, GCSReceiptStore, failure, request_batch, replay_bundle
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.gemini_resolution import GeminiResolver
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_pilot_budget import PilotBudget, MODEL
from test_news_pilot_budget import Store
from test_news_native_resolution import answer, setup, TEXT
from test_news_ner_durable import trusted


CONFIG=AuditorConfig(provider='gemini',model=MODEL,gemini_api_key='synthetic-private-key')


class Receipts:
    def __init__(self, fail_at=None):self.items={};self.fail_at=fail_at
    def put(self,name,value):
        if name.endswith(str(self.fail_at)) or name in self.items:raise failure('native_resolution_receipt_storage_failed')
        self.items[name]=deepcopy(value)
    def get(self,name):return deepcopy(self.items[name])


def packet():
    document={'evidence_text':'Flooding on Fictional Road.','quote_options':[{'option_index':0,'quote':'Flooding on Fictional Road.'}],
        'targets':[{'id':'m0','label':'ROAD'}]}
    return {'systemInstruction':{},'contents':[{'parts':[{'text':json.dumps(document)}]}],
        'generationConfig':{'temperature':0,'maxOutputTokens':8192,'responseMimeType':'application/json','responseJsonSchema':{}}}


def envelope(rows):
    return {'modelVersion':MODEL,'responseId':'safe-id', 'usageMetadata':{'promptTokenCount':10,'candidatesTokenCount':20},
        'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps({'results':rows})}]}}]}


def bundle(store):
    intent=next(v for k,v in store.items.items() if k.endswith('/intent.json'))
    key=intent['request_identity']
    return {'intent':intent,'response':store.items[key+'/response.json']}


@pytest.mark.asyncio
@pytest.mark.parametrize('indexes,duplicates,invalid', [([0,0],[0],[]),([-1],[],[-1]),([1],[],[1])])
async def test_invalid_evidence_survives_failure_and_replays_without_network(indexes,duplicates,invalid):
    storage=Receipts();journal=BatchJournal(storage,secrets=(CONFIG.gemini_api_key,));budget=PilotBudget(Store(),'selection')
    row=answer({'id':'m0','label':'CITY'},place_evidence=indexes)
    calls=[]
    def respond(request):calls.append(1);return httpx.Response(200,json=envelope([row]))
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(ResolutionError,match='native_resolution_evidence_invalid') as caught:
            await request_batch(CONFIG,packet(),{'parent_run_id':375},http=client,budget=budget,journal=journal)
    diagnostic=caught.value.provider_diagnostic
    assert diagnostic['errors'][0]=={'target_id':'m0','field':'place_evidence',
        'duplicate_indices':duplicates,'out_of_range_indices':invalid,'valid_range':[0,0]}
    assert len(calls)==1 and budget.store.state['status']=='stopped'
    saved=bundle(storage)
    assert saved['response']['replayable'] and CONFIG.gemini_api_key not in json.dumps(storage.items)
    with patch.object(socket.socket,'connect',side_effect=AssertionError('No network')):
        for _ in range(2):
            with pytest.raises(ResolutionError) as replayed:replay_bundle(saved,sha(saved),config=CONFIG)
            assert replayed.value.provider_diagnostic==diagnostic


@pytest.mark.asyncio
@pytest.mark.parametrize('fail_at,calls', [('intent.json',0),('response.json',1),('validation.json',1)])
async def test_storage_failure_stops_and_never_resends(fail_at,calls):
    storage=Receipts(fail_at);budget=PilotBudget(Store(),'selection');sent=[]
    def respond(request):sent.append(1);return httpx.Response(200,json=envelope([answer({'id':'m0','label':'CITY'})]))
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(ResolutionError,match='receipt_storage_failed'):
            await request_batch(CONFIG,packet(),{},http=client,budget=budget,journal=BatchJournal(storage))
        with pytest.raises(ResolutionError):
            await request_batch(CONFIG,packet(),{},http=client,budget=budget,journal=BatchJournal(storage))
    assert len(sent)==calls and budget.store.state['status']=='stopped'
    if fail_at=='validation.json':assert bundle(storage)['response']['replayable']


@pytest.mark.asyncio
async def test_valid_batch_is_retained_and_tampering_cannot_replay():
    storage=Receipts()
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json=envelope([answer({'id':'m0','label':'CITY'})])))) as client:
        await request_batch(CONFIG,packet(),{},http=client,journal=BatchJournal(storage))
    saved=bundle(storage);pin=sha(saved)
    with patch.object(socket.socket,'connect',side_effect=AssertionError('No network')):
        assert replay_bundle(saved,pin,config=CONFIG)['provider_requests']==0
    edited=deepcopy(saved);edited['response']['body_base64']='e30='
    with pytest.raises(ResolutionError,match='tampered'):replay_bundle(edited,pin,config=CONFIG)
    edited=deepcopy(saved);edited['response']['request_identity']='0'*64
    with pytest.raises(ResolutionError,match='binding_invalid'):replay_bundle(edited,sha(edited),config=CONFIG)


@pytest.mark.asyncio
@pytest.mark.parametrize('kind',['malformed','oversized','missing','unexpected','duplicate','secret'])
async def test_invalid_responses_retained_without_credential_leak(kind):
    storage=Receipts();row=answer({'id':'m0','label':'CITY'})
    rows=[] if kind=='missing' else [row,row] if kind=='duplicate' else [{**row,'target_id':'other'}] if kind=='unexpected' else [row]
    raw=b'not json' if kind=='malformed' else b'x'*70000 if kind=='oversized' else json.dumps(envelope(rows)).encode()
    if kind=='secret':raw=CONFIG.gemini_api_key.encode()
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,content=raw))) as client:
        with pytest.raises(ResolutionError):
            await request_batch(CONFIG,packet(),{},http=client,journal=BatchJournal(storage,secrets=(CONFIG.gemini_api_key,)))
    assert 'synthetic-private-key' not in json.dumps(storage.items)
    assert any(k.endswith('/response.json') for k in storage.items)
    if kind=='secret':
        saved=bundle(storage)['response']
        assert not saved['replayable'] and saved['redacted']
        assert CONFIG.gemini_api_key.encode() not in base64.b64decode(saved['body_base64'])


@pytest.mark.asyncio
async def test_interrupted_request_cannot_be_silently_reissued():
    storage=Receipts();budget=PilotBudget(Store(),'selection');calls=[]
    async def respond(request):calls.append(1);raise asyncio.CancelledError()
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(asyncio.CancelledError):
            await request_batch(CONFIG,packet(),{},http=client,budget=budget,journal=BatchJournal(storage))
        with pytest.raises(ResolutionError):
            await request_batch(CONFIG,packet(),{},http=client,budget=budget,journal=BatchJournal(storage))
    assert calls==[1] and any(k.endswith('/intent.json') for k in storage.items)


@pytest.mark.asyncio
async def test_first_invalid_native_batch_prevents_second_dispatch(trusted):
    text='On October 20, 2026, Fictional Crescent in Pasig City was flooded.\n'+TEXT+'\n'+TEXT
    service,_,context,baseline,_,_=setup(trusted,text)
    service=GeminiResolver(replace(service.config,batch_size=4),receipts=BatchJournal(Receipts()))
    assert len(baseline.native.graph.mentions)>4
    calls=[]
    def respond(request):
        calls.append(1);doc=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        rows=[answer(t,place_evidence=[999]) for t in doc['targets']]
        return httpx.Response(200,json=envelope(rows))
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(ResolutionError,match='evidence_invalid'):
            await service.resolve(context.source(),baseline,parent_run_id=375,parent_result_sha256='a'*64,client=client)
    assert calls==[1]


def test_storage_requires_private_prefix():
    with pytest.raises(ResolutionError):GCSReceiptStore('public/receipts/')


@pytest.mark.asyncio
async def test_fictional_cloud_contract_cannot_write_live_receipts(trusted):
    from scripts.news_verified_contract import check_contract
    service=GeminiResolver(CONFIG,receipts=BatchJournal(Receipts('intent.json')))
    journal=service.receipts
    result=await check_contract(trusted,service)
    assert result['status']=='passed' and service.receipts is journal
    assert not journal.store.items


@pytest.mark.asyncio
async def test_diagnostic_one_call_then_stopped_even_when_invoked_again(monkeypatch):
    from types import SimpleNamespace
    from scripts import diagnose_news_gemini_evidence as script
    ledger=Store();receipts=Receipts();sent=[]
    authority={'budget_object':'fixed-ledger','budget_identity':'selection',
        'receipts_prefix':'private-prefix','session_id':'fixed-session','request_sha256':sha(packet())}
    frozen={'payload':packet(),'context':{'parent_run_id':375}}
    monkeypatch.setattr(script,'verified_input',lambda _:({},authority,frozen,{}))
    monkeypatch.setattr(script,'GCSLedgerStore',lambda *_:ledger)
    monkeypatch.setattr(script,'GCSReceiptStore',lambda *_:receipts)
    monkeypatch.setattr(script.AuditorConfig,'from_environment',lambda:CONFIG)
    monkeypatch.setenv('LANES_NEWS_PILOT_BUDGET_OBJECT','fixed-ledger')
    monkeypatch.setenv('LANES_NEWS_PILOT_BUDGET_IDENTITY','selection')
    def respond(request):sent.append(1);return httpx.Response(200,json=envelope([answer({'id':'m0','label':'CITY'})]))
    monkeypatch.setattr(script.httpx,'AsyncHTTPTransport',lambda **_:httpx.MockTransport(respond))
    first=await script.execute(SimpleNamespace(allow_one_request=True))
    second=await script.execute(SimpleNamespace(allow_one_request=True))
    assert first['status']=='one_batch_evidence_references_passed'
    assert second['status']=='failed' and second['provider_requests']==0
    assert sent==[1] and ledger.state['status']=='stopped'
