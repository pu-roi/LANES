"""Versioned, receipt-backed commitments; historical reservations stay immutable."""
from __future__ import annotations

import base64
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re

import httpx

from app.services.news_claim_auditor import _unique_json_object
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_pilot_budget import PilotBudget, new_ledger, MODEL, LIMIT

VERSION = 'news-pilot-budget-v2'
INITIAL = (
    ('c2042c6f02df5febba6b6709248324059a6d037135d115e7e4e435daa05b317a', 4_109_100),
    ('e8b539af345e16930d541dbea1791ddd7ff6a71f4ca63821bc2eeb54ba06cf4b', 4_417_200),
    ('5e30239931d72fe8ed62cb47d0fa1b9b04ef0847208fb1a1661277c4dfe33ce1', 0),
)


def accounting_policy() -> dict:
    return {'schema_version':'news-pilot-accounting-policy-v2', 'model':MODEL,
        'limit_nanodollars':LIMIT, 'input_nanodollars_per_token':300,
        'output_nanodollars_per_token':2500, 'schema_bytes_as_tokens':True,
        'framing_tokens':1024, 'max_output_tokens':8192,
        'nonbillable_http_statuses':[400,500], 'max_new_generations':12,
        'initial_attempt_count':20, 'initial_reserved_nanodollars':773_199_400,
        'initial_effective_nanodollars':656_674_900,
        'initial_reconciliations':[{'attempt_number':18+i,'bundle_sha256':pin,
            'usage_estimate_nanodollars':cost} for i,(pin,cost) in enumerate(INITIAL)]}


def authenticated_response(bundle: dict, pin: str) -> tuple[dict, dict]:
    """Authenticate envelope bytes without depending on article-fact validity."""
    try:
        intent,response=bundle['intent'],bundle['response']
        key=sha({'request_sha256':sha(intent['payload']),'context':intent['context']})
        raw=base64.b64decode(response['body_base64'],validate=True)
        if (sha(bundle)!=pin or intent['schema_version']!='news-gemini-batch-intent-v1'
                or response['schema_version']!='news-gemini-batch-response-v1'
                or intent['model']!=MODEL or intent['request_identity']!=key
                or response['request_identity']!=key or intent['budget_reservation_id']!=key
                or intent['request_sha256']!=sha(intent['payload']) or response['replayable'] is not True
                or hashlib.sha256(raw).hexdigest()!=response['body_sha256'] or len(raw)>65536):
            raise ResolutionError('pilot_accounting_receipt_invalid')
        envelope=json.loads(raw,object_pairs_hook=_unique_json_object)
        return intent, usage_estimate(response['http_status'],envelope)
    except (KeyError,ValueError,TypeError) as exc:
        if isinstance(exc,ResolutionError):raise
        raise ResolutionError('pilot_accounting_receipt_invalid') from exc


def usage_estimate(status: int, envelope: dict) -> dict:
    if type(envelope) is not dict:raise ResolutionError('pilot_accounting_usage_unknown')
    if status in (400,500):
        error=envelope.get('error',{})
        if type(error.get('code')) is not int or error['code']!=status:
            raise ResolutionError('pilot_accounting_error_unproven')
        return {'basis':'provider_http_error_not_billable','http_status':status,'usage_estimate_nanodollars':0}
    if status!=200 or envelope.get('modelVersion')!=MODEL:
        raise ResolutionError('pilot_accounting_usage_unknown')
    usage=envelope.get('usageMetadata',{})
    if type(usage) is not dict:raise ResolutionError('pilot_accounting_usage_unknown')
    names=('promptTokenCount','candidatesTokenCount','totalTokenCount')
    if any(type(usage.get(n)) is not int or not 0<=usage[n]<=10_000_000 for n in names):
        raise ResolutionError('pilot_accounting_usage_unknown')
    thoughts=usage.get('thoughtsTokenCount',0);tools=usage.get('toolUsePromptTokenCount',0)
    if (type(thoughts) is not int or thoughts<0 or type(tools) is not int or tools!=0
            or usage['totalTokenCount']!=usage['promptTokenCount']+usage['candidatesTokenCount']+thoughts
            or usage.get('serviceTier','standard')!='standard'):
        raise ResolutionError('pilot_accounting_usage_inconsistent')
    return {'basis':'provider_usage_at_pinned_rates','http_status':200,
        'input_tokens':usage['promptTokenCount'],'output_tokens':usage['candidatesTokenCount'],
        'thinking_tokens':thoughts,'total_tokens':usage['totalTokenCount'],
        'usage_estimate_nanodollars':usage['promptTokenCount']*300+(usage['candidatesTokenCount']+thoughts)*2500}


def commitment(state: dict) -> int:
    if any(type(a.get('reserved_nanodollars')) is not int or a['reserved_nanodollars']<=0
            for a in state['attempts']):raise ResolutionError('pilot_budget_state_invalid')
    attempts={a['id']:a for a in state['attempts']};settled={}
    if len(attempts)!=len(state['attempts']):raise ResolutionError('pilot_accounting_duplicate_attempt')
    for value in state.get('settlements',[]):
        key=value['attempt_id'];cost=value['usage_estimate_nanodollars']
        if (key not in attempts or key in settled or type(cost) is not int or cost<0
                or value.get('policy_sha256')!=sha(accounting_policy())
                or not isinstance(value.get('response_bundle_sha256'),str)
                or not re.fullmatch('[a-f0-9]{64}',value['response_bundle_sha256'])):
            raise ResolutionError('pilot_accounting_settlement_invalid')
        settled[key]=cost
    return sum(settled.get(key,a['reserved_nanodollars']) for key,a in attempts.items())


def upgrade_reviewed_ledger(store: object, identity: str, bundles: list[dict], *,
                            baseline_sha256: str, journal: object) -> dict:
    """One explicitly reviewed migration, preserving all 20 attempt objects."""
    old,generation=PilotBudget(store,identity)._read()
    if (sha(old)!=baseline_sha256 or old['status']!='stopped' or len(old['attempts'])!=20
            or sum(a['reserved_nanodollars'] for a in old['attempts'])!=773_199_400
            or any(a['status']=='in_flight' for a in old['attempts']) or len(bundles)!=3):
        raise ResolutionError('pilot_accounting_baseline_changed')
    state=deepcopy(old);state.update(schema_version=VERSION,accounting_policy_sha256=sha(accounting_policy()),
        legacy_baseline_sha256=baseline_sha256,legacy_attempts_sha256=sha(old['attempts']),settlements=[])
    journal.put(baseline_sha256+'/legacy-ledger.json',old)
    for index,(bundle,(pin,cost)) in enumerate(zip(bundles,INITIAL,strict=True),start=17):
        intent,value=authenticated_response(bundle,pin);attempt=old['attempts'][index]
        if intent['budget_reservation_id']!=attempt['id'] or value['usage_estimate_nanodollars']!=cost:
            raise ResolutionError('pilot_accounting_reconciliation_changed')
        receipt={**value,'schema_version':'news-pilot-settlement-v2','attempt_id':attempt['id'],
            'policy_sha256':sha(accounting_policy()),'response_bundle_sha256':pin}
        journal.put(sha(receipt)+'/accounting.json',receipt)
        state['settlements'].append(receipt)
    if commitment(state)!=656_674_900:raise ResolutionError('pilot_accounting_initial_commitment_changed')
    journal.put(sha(state)+'/ledger-upgrade.json',{'schema_version':'news-pilot-budget-upgrade-v2',
        'old_sha256':sha(old),'new_sha256':sha(state),'attempts_sha256':sha(old['attempts'])})
    store.compare_and_swap(generation,state)
    return state


def reservation(payload: dict, counted_tokens: int) -> int:
    if type(counted_tokens) is not int or not 1<=counted_tokens<=1_000_000:
        raise ResolutionError('pilot_token_count_invalid')
    config=payload['generationConfig']
    if (set(payload)!={'systemInstruction','contents','generationConfig'}
            or config.get('maxOutputTokens')!=8192 or config.get('temperature')!=0
            or config.get('responseMimeType')!='application/json'
            or set(config)!={'temperature','maxOutputTokens','responseMimeType','responseJsonSchema'}):
        raise ResolutionError('pilot_budget_request_invalid')
    overhead=len(json.dumps(config['responseJsonSchema'],ensure_ascii=False,allow_nan=False).encode())+1024
    return (counted_tokens+overhead)*300+8192*2500


async def count_request(config: object, payload: dict, *, http: httpx.AsyncClient, journal: object) -> dict:
    """Non-generating tokenizer call, no retries or fallback input estimates."""
    key=sha(payload);policy=sha(accounting_policy())
    intent={'schema_version':'news-pilot-count-intent-v2','request_sha256':key,'model':MODEL,
        'accounting_policy_sha256':policy}
    journal.put(key+'/count-intent.json',intent)
    try:
        async with http.stream('POST','https://generativelanguage.googleapis.com/v1beta/models/'+MODEL+':countTokens',
                headers={'x-goog-api-key':config.gemini_api_key},
                json={'generateContentRequest':{'model':'models/'+MODEL,**payload}},
                follow_redirects=False,timeout=10) as response:
            raw=bytearray()
            async for part in response.aiter_bytes():
                raw.extend(part[:max(0,16385-len(raw))])
                if len(raw)>16384:raise ResolutionError('pilot_token_count_oversized')
            if response.status_code!=200:raise ResolutionError('pilot_token_count_http_error')
        value=json.loads(raw,object_pairs_hook=_unique_json_object)
        cost=reservation(payload,value.get('totalTokens'))
        receipt={**intent,'schema_version':'news-pilot-count-v2','total_tokens':value['totalTokens'],
            'reserved_nanodollars':cost,'response_sha256':hashlib.sha256(raw).hexdigest()}
        journal.put(key+'/token-count.json',receipt)
        return receipt
    except (httpx.HTTPError,ValueError,TypeError) as exc:
        if isinstance(exc,ResolutionError):raise
        raise ResolutionError('pilot_token_count_failed') from exc


class AccountedPilotBudget(PilotBudget):
    def __init__(self, store: object, identity: str, *, counts: dict, counts_sha256: str, journal: object) -> None:
        super().__init__(store,identity)
        if (sha(counts)!=counts_sha256 or counts.get('schema_version')!='news-pilot-count-catalog-v2'
                or counts.get('accounting_policy_sha256')!=sha(accounting_policy())):
            raise ResolutionError('pilot_token_catalog_changed')
        self.counts=deepcopy(counts);self.counts_pin=counts_sha256;self.journal=journal

    def _read(self) -> tuple[dict,str]:
        state,generation=self.store.read();expected=new_ledger(self.identity)
        if (state.get('schema_version')!=VERSION or state.get('accounting_policy_sha256')!=sha(accounting_policy())
                or any(state.get(k)!=expected[k] for k in ('identity','limit_nanodollars','model','price'))
                or len(state.get('attempts',[]))<20
                or sha(state['attempts'][:20])!=state.get('legacy_attempts_sha256')):
            raise ResolutionError('pilot_budget_identity_mismatch')
        commitment(state)
        return state,generation

    def reserve(self, model: str, payload: dict, context: dict) -> str:
        if sha(self.counts)!=self.counts_pin or model!=MODEL:
            raise ResolutionError('pilot_token_catalog_changed')
        pin=sha(payload);matches=[c for c in self.counts['requests'] if c['request_sha256']==pin]
        if len(matches)!=1:raise ResolutionError('pilot_uncounted_request')
        item=matches[0];cost=reservation(payload,item['total_tokens'])
        if (item['model']!=MODEL or item['accounting_policy_sha256']!=sha(accounting_policy())
                or item['reserved_nanodollars']!=cost):raise ResolutionError('pilot_token_count_changed')
        state,generation=self._read()
        if state['status']!='ready' or any(a['status']=='in_flight' for a in state['attempts']):
            raise ResolutionError('pilot_budget_stopped_or_in_flight')
        key=sha({'request_sha256':pin,'context':context})
        if any(a['id']==key or a.get('request_sha256')==pin for a in state['attempts']):
            raise ResolutionError('pilot_budget_attempt_already_reserved')
        if len(state['attempts'])>=32 or commitment(state)+cost>LIMIT:
            raise ResolutionError('pilot_budget_exhausted')
        state['attempts'].append({'id':key,'request_sha256':pin,'context':context,
            'reserved_nanodollars':cost,'status':'in_flight','at':datetime.now(timezone.utc).isoformat(),
            'count_catalog_sha256':self.counts_pin})
        self.store.compare_and_swap(generation,state)
        return key

    def observe_response(self, key: str, intent: dict, response: dict) -> dict:
        bundle={'intent':intent,'response':response};pin=sha(bundle)
        bound,value=authenticated_response(bundle,pin)
        if bound['budget_reservation_id']!=key:raise ResolutionError('pilot_accounting_response_changed')
        state,generation=self._read()
        attempt=next((a for a in state['attempts'] if a['id']==key),None)
        if attempt is None or attempt['status']!='in_flight' or any(s['attempt_id']==key for s in state['settlements']):
            raise ResolutionError('pilot_accounting_attempt_invalid')
        receipt={**value,'schema_version':'news-pilot-settlement-v2','attempt_id':key,
            'policy_sha256':sha(accounting_policy()),'response_bundle_sha256':pin}
        self.journal.put(sha(receipt)+'/accounting.json',receipt)
        state['settlements'].append(receipt)
        over=value['usage_estimate_nanodollars']>attempt['reserved_nanodollars']
        if over:state['status']='stopped'
        self.store.compare_and_swap(generation,state)
        if over:raise ResolutionError('pilot_accounting_reservation_exceeded')
        return value
