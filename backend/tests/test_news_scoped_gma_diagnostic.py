"""Exact diagnostic authority, one-call retention and conservative stop behavior."""
from copy import deepcopy
import json
from types import SimpleNamespace

import httpx
import pytest

import app.services.news_scoped_gma_diagnostic as diagnostic
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_gemini_receipts import BatchJournal
from app.services.news_pilot_accounting import accounting_policy,commitment
from test_news_gemini_receipts import CONFIG,Receipts,packet,envelope
from test_news_native_resolution import answer
from test_news_pilot_accounting import ledger,budget,catalog


def grant(monkeypatch,operation='count'):
    p={'payload':packet(),'context':{'parent_run_id':375,'parent_result_sha256':diagnostic.PARENT,'input_sha256':'a'*64}}
    doc=json.loads(p['payload']['contents'][0]['parts'][0]['text'])
    doc['targets']=[{'id':i} for i in diagnostic.TARGETS];doc['source_layout']={}
    p['payload']['contents'][0]['parts'][0]['text']=json.dumps(doc)
    monkeypatch.setattr(diagnostic,'REQUEST',sha(p['payload']))
    release={'application_files':{},'base_assets_sha256':'b'*64,'database_identity_sha256':'c'*64,
             'resolver':{'evidence_contract':diagnostic.CONTRACT}}
    authority={'schema_version':diagnostic.VERSION,'session_id':diagnostic.SESSION,'release_sha256':sha(release),
        'application_sha256':sha({}),'assets_sha256':'b'*64,'database_identity_sha256':'c'*64,
        'resolver':release['resolver'],'article_id':47,'version_id':574,'parent_run_id':375,'parent_result_sha256':diagnostic.PARENT,
        'input_sha256':'a'*64,'source_body_sha256':__import__('hashlib').sha256(doc['evidence_text'].encode()).hexdigest(),
        'source_layout_sha256':sha({}),'request_sha256':diagnostic.REQUEST,'batch_index':3,'targets':diagnostic.TARGETS,
        'operation':operation,'generation_requests':int(operation=='gate'),'count_requests':int(operation=='count'),
        'database_writes':False,'budget_object':diagnostic.ROOT+'budget.json','budget_identity':'selection',
        'baseline_sha256':'d'*64,'attempts_sha256':'e'*64,'settlements_sha256':'f'*64,
        'receipts_prefix':diagnostic.PREFIX,'accounting_policy_sha256':sha(accounting_policy()),
        'count_catalog':None,'expected_reservation_nanodollars':None}
    return release,p,authority


@pytest.mark.parametrize('mutation',[None,'authority_pin','release','target','version','request','write','prefix','budget','operation','extra'])
def test_exact_grant_rejects_expanded_or_changed_authority(monkeypatch,mutation):
    release,p,a=grant(monkeypatch);pin=sha(a)
    if mutation=='authority_pin':pin='0'*64
    if mutation=='release':release['application_files']={'changed':'0'*64}
    if mutation=='target':a['targets']=['n0']
    if mutation=='version':a['version_id']=137
    if mutation=='request':p['payload']['systemInstruction']={'text':'changed'}
    if mutation=='write':a['database_writes']=True
    if mutation=='prefix':a['receipts_prefix']='other'
    if mutation=='budget':a['budget_object']='different'
    if mutation=='operation':a['operation']='resolve'
    if mutation=='extra':a['allowed_operations']=['archive']
    if mutation not in ('authority_pin','release','request'):pin=sha(a)
    def validate():diagnostic.validate_authority(a,pin,release,p,operation='count',receipts_prefix=diagnostic.PREFIX,budget_identity='selection')
    if mutation:
        with pytest.raises(ResolutionError):validate()
    else:validate()


@pytest.mark.asyncio
@pytest.mark.parametrize('outcome',['valid','invalid','http','storage','interrupted'])
async def test_count_once_retains_before_validation_and_cannot_repeat(outcome):
    storage=Receipts('response.json' if outcome=='storage' else None);journal=BatchJournal(storage,secrets=(CONFIG.gemini_api_key,))
    p={'payload':packet()};calls=[]
    async def respond(request):
        calls.append(request.url.path)
        if outcome=='interrupted':raise httpx.ReadTimeout('synthetic')
        return httpx.Response(400 if outcome=='http' else 200,json={'totalTokens':123 if outcome!='invalid' else -1})
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        if outcome=='valid':
            counts=await diagnostic.count_once(CONFIG,p,journal,http=client)
            assert counts['requests'][0]['total_tokens']==123
        else:
            with pytest.raises((ResolutionError,httpx.HTTPError)):
                await diagnostic.count_once(CONFIG,p,journal,http=client)
        with pytest.raises(ResolutionError):await diagnostic.count_once(CONFIG,p,journal,http=client)
    assert len(calls)==1 and calls[0].endswith(':countTokens')
    if outcome not in ('storage','interrupted'):assert any(k.endswith('/response.json') for k in storage.items)
    assert CONFIG.gemini_api_key not in json.dumps(storage.items)


@pytest.mark.asyncio
async def test_count_intent_failure_prevents_http_dispatch():
    store=Receipts('count-intent.json');calls=[]
    def respond(_):calls.append(1);return httpx.Response(200,json={'totalTokens':1})
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
        with pytest.raises(ResolutionError):
            await diagnostic.count_once(CONFIG,{'payload':packet()},BatchJournal(store),http=http)
    assert not calls


def test_count_schedule_and_cap_are_checked(monkeypatch):
    _,p,a=grant(monkeypatch,'gate');counts=catalog(p['payload']);store=ledger()
    a.update(count_catalog={'object':diagnostic.PREFIX+'frozen/count-catalog.json','sha256':sha(counts)},
             expected_reservation_nanodollars=counts['requests'][0]['reserved_nanodollars'])
    assert diagnostic.qualify_count(counts,a,p,store.state)>0
    changed=deepcopy(counts);changed['requests'][0]['total_tokens']+=1
    with pytest.raises(ResolutionError):diagnostic.qualify_count(changed,a,p,store.state)
    store.state['attempts'][0]['reserved_nanodollars']=999_000_000
    with pytest.raises(ResolutionError,match='budget_exhausted'):diagnostic.qualify_count(counts,a,p,store.state)


@pytest.mark.asyncio
@pytest.mark.parametrize('bad', [False,True])
async def test_gate_stops_after_one_request_and_never_retries(monkeypatch,bad):
    p={'payload':packet(),'context':{'parent_run_id':375}};monkeypatch.setattr(diagnostic,'REQUEST',sha(p['payload']))
    storage=Receipts();account=ledger();objects=storage
    guard=budget(account,p['payload'],objects)
    service=SimpleNamespace(config=CONFIG,timeout_seconds=30,receipts=BatchJournal(storage),catalog=None)
    monkeypatch.setattr(diagnostic,'semantic_quality',lambda *_:{'status':'one_batch_accepted','row_outcomes':[],
        'quality_issues':[],'article_acceptance':'not_evaluated','database_writes':0})
    calls=[]
    def respond(request):
        calls.append(1);r=answer({'id':'m0','label':'CITY'},place_evidence=[999] if bad else [])
        value=envelope([r]);value['usageMetadata']['totalTokenCount']=30
        return httpx.Response(200,json=value)
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result=await diagnostic.gate_once(service,p,None,None,guard,http=client)
        assert result['provider_requests']==1 and result['database_writes']==0
        assert result['status']==('requires_attention' if bad else 'completed')
        assert account.state['status']=='stopped' and len(account.state['attempts'])==21
        repeated=await diagnostic.gate_once(service,p,None,None,guard,http=client)
        assert repeated['provider_requests']==0 and len(calls)==1


def test_preflight_failure_stop_preserves_attempts():
    store=ledger();store.state['manual_resumptions']=[{'id':diagnostic.SESSION}]
    before=deepcopy(store.state['attempts'])
    diagnostic.stop_session(store)
    assert store.state['status']=='stopped' and store.state['attempts']==before


@pytest.mark.parametrize('mutation',[None,'attempt','settlement','resume','status'])
def test_baseline_preserves_all_twenty_three_attempts(monkeypatch,mutation):
    _,_,authority=grant(monkeypatch)
    store=ledger();state=store.state
    state['attempts'][0]['reserved_nanodollars']=200_000_000
    for i,cost in enumerate((25_226_266,25_226_266,25_226_268)):
        state['attempts'].append({'id':sha(20+i),'reserved_nanodollars':cost,'status':'completed'})
    state['settlements']=[{'attempt_id':state['attempts'][0]['id'],'usage_estimate_nanodollars':21_695_600,
                          'policy_sha256':sha(accounting_policy()),'response_bundle_sha256':'a'*64}]
    state['status']='stopped'
    authority.update(baseline_sha256=sha(state),attempts_sha256=sha(state['attempts']),settlements_sha256=sha(state['settlements']))
    diagnostic.validate_baseline(state,authority)
    state['status']='ready';state['manual_resumptions']=[{'id':diagnostic.SESSION,'previous_sha256':authority['baseline_sha256']}]
    if mutation=='attempt':state['attempts'][0]['status']='changed'
    if mutation=='settlement':state['settlements'][0]['usage_estimate_nanodollars']+=1
    if mutation=='resume':state['manual_resumptions'][-1]['id']='other'
    if mutation=='status':state['status']='stopped'
    if mutation:
        with pytest.raises(ResolutionError):diagnostic.validate_baseline(state,authority,ready=True)
    else:diagnostic.validate_baseline(state,authority,ready=True)


@pytest.mark.parametrize('change',[None,'time','depth','heading','missing'])
def test_quality_requires_both_roads_and_context_only_headings(monkeypatch,change):
    rows=[SimpleNamespace(target_id=i,verdict='unsupported',status='unclear',depth_scope='unknown',depth_text=None)
          for i in diagnostic.TARGETS]
    claims=[];groups=[]
    from datetime import datetime
    for target_id in ('n13','n14'):
        row=next(r for r in rows if r.target_id==target_id)
        row.verdict='observed';row.status='active';row.depth_scope='shared';row.depth_text='Waist-deep (37 inches)'
        groups.append({'target_entity_ids':[target_id],'claim_index':len(claims)})
        claims.append(SimpleNamespace(canonical_city='Quezon City',event_time_resolved=datetime.fromisoformat('2026-09-09T08:55:00+08:00'),depth_canonical=None))
    if change=='time':claims[0].event_time_resolved=None
    if change=='depth':rows[1].depth_scope='individual'
    if change=='heading':rows[0].verdict='observed'
    if change=='missing':groups.pop();claims.pop()
    monkeypatch.setattr(diagnostic,'evaluate_rows',lambda *_:(claims,groups,[],[],'a'*64))
    catalog=SimpleNamespace(city=lambda _:[SimpleNamespace(name='Quezon City')])
    result=diagnostic.semantic_quality(None,None,rows,catalog)
    assert result['status']==('one_batch_accepted' if change is None else 'one_batch_incomplete')
