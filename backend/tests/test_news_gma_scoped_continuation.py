"""Continuation grants preserve accounting history and prevent duplicate dispatch."""
from copy import deepcopy
from unittest.mock import patch
import base64
import json

import pytest

from app.services.news_gma_scoped_budget import (SESSION, ScopedGmaBudget, effective_commitment,
    extend_ledger, extension_policy)
from app.services.news_gma_scoped_continuation import ScopedGmaBatchPlan, batch_manifest, REQUESTS
from app.services.news_pilot_accounting import AccountedPilotBudget, accounting_policy, commitment, reservation
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_pilot_budget import MODEL
from test_news_pilot_budget import Store, payload
from test_news_pilot_accounting import Objects


def setup():
    store = Store()
    state = store.state
    state['attempts'] = [{'id':sha(i),'reserved_nanodollars':30_000_000,'status':'failed'} for i in range(24)]
    state['attempts'][-1]['reserved_nanodollars'] = 180_978_600
    state.update(schema_version='news-pilot-budget-v2',accounting_policy_sha256=sha(accounting_policy()),
        legacy_attempts_sha256=sha(state['attempts'][:20]),status='stopped',settlements=[])
    for index,cost in ((0,1_000_000),(23,11_667_400)):
        state['settlements'].append({'attempt_id':state['attempts'][index]['id'],
            'usage_estimate_nanodollars':cost,'policy_sha256':sha(accounting_policy()),
            'response_bundle_sha256':sha(index)})
    packets = [payload(i+1) for i in range(12)]
    policy = extension_policy([sha(p) for p in packets])
    assert commitment(state) == 672_667_400
    objects = Objects()
    old = deepcopy(state)
    extend_ledger(store,'selection',policy,baseline_sha256=sha(old),journal=objects)
    counts = {'schema_version':'news-pilot-count-catalog-v2','accounting_policy_sha256':sha(accounting_policy()),
        'requests':[{'request_sha256':sha(p),'total_tokens':6000,'model':MODEL,
            'accounting_policy_sha256':sha(accounting_policy()),'reserved_nanodollars':reservation(p,6000)} for p in packets]}
    budget = ScopedGmaBudget(store,'selection',policy=policy,counts=counts,counts_sha256=sha(counts),journal=objects)
    return store,old,policy,objects,packets,budget


def resume(store):
    store.state.update(status='ready',manual_resumptions=[{'id':SESSION}])


def test_extension_keeps_all_old_attempts_settlements_and_commitment():
    store,old,policy,objects,packets,budget = setup()
    assert store.state['attempts'] == old['attempts']
    assert store.state['settlements'] == old['settlements']
    assert effective_commitment(store.state,policy) == commitment(old)
    assert len(objects.objects) == 2
    with pytest.raises(ResolutionError):
        AccountedPilotBudget(store,'selection',counts=budget.counts,counts_sha256=budget.counts_pin,journal=objects)._read()
    with pytest.raises(ResolutionError):
        extend_ledger(store,'selection',policy,baseline_sha256=sha(old),journal=objects)


@pytest.mark.parametrize('field',['attempt','settlement','policy','target'])
def test_historical_tampering_rejects_before_dispatch(field):
    store,old,policy,objects,packets,budget = setup()
    if field == 'attempt':store.state['attempts'][0]['status'] = 'completed'
    if field == 'settlement':store.state['settlements'][0]['usage_estimate_nanodollars'] += 1
    if field == 'policy':store.state['accounting_extension']['maximum_attempt_count'] = 37
    if field == 'target':store.state['identity'] = 'other'
    resume(store)
    with pytest.raises(ResolutionError):budget.reserve(MODEL,packets[0],{})
    assert len(store.state['attempts']) == 24


def test_storage_failure_prevents_ledger_transition():
    store,old,policy,objects,packets,budget = setup()
    store.state = old
    with patch.object(objects,'put',side_effect=ResolutionError('storage_failed')):
        with pytest.raises(ResolutionError):extend_ledger(store,'selection',policy,baseline_sha256=sha(old),journal=objects)
    assert store.state == old


def test_interrupted_request_blocks_next_and_repeat_send():
    store,old,policy,objects,packets,budget = setup()
    resume(store)
    key = budget.reserve(MODEL,packets[0],{})
    with pytest.raises(ResolutionError,match='in_flight'):budget.reserve(MODEL,packets[1],{})
    budget.finish(key,succeeded=False)
    resume(store)
    with pytest.raises(ResolutionError,match='already_reserved'):budget.reserve(MODEL,packets[0],{})
    assert len(store.state['attempts']) == 25


def test_twelve_new_requests_allowed_without_expanding_dollar_cap():
    store,old,policy,objects,packets,budget = setup()
    resume(store)
    for packet in packets:
        key = budget.reserve(MODEL,packet,{})
        budget.finish(key,succeeded=True)
    assert len(store.state['attempts']) == 36
    assert effective_commitment(store.state,policy) < 1_000_000_000
    assert store.state['attempts'][:24] == old['attempts']
    with pytest.raises(ResolutionError):budget.reserve(MODEL,payload(99),{})


def test_full_outstanding_schedule_must_fit_before_first_request():
    store,old,policy,objects,packets,budget = setup()
    for item,packet in zip(budget.counts['requests'],packets,strict=True):
        item.update(total_tokens=100000,reserved_nanodollars=reservation(packet,100000))
    budget.counts_pin = sha(budget.counts)
    resume(store)
    with pytest.raises(ResolutionError,match='schedule_exhausted'):budget.reserve(MODEL,packets[0],{})
    assert len(store.state['attempts']) == 24


def test_http200_usage_settles_even_when_article_facts_will_fail():
    store,old,policy,objects,packets,budget = setup()
    resume(store)
    packet = packets[0]
    key = budget.reserve(MODEL,packet,{})
    raw = json.dumps({'modelVersion':MODEL,'usageMetadata':{'promptTokenCount':6000,
        'candidatesTokenCount':12,'totalTokenCount':6012},'candidates':[{'content':{'parts':[{'text':'invalid JSON'}]}}]}).encode()
    import hashlib
    intent = {'schema_version':'news-gemini-batch-intent-v1','request_identity':key,'payload':packet,
        'context':{},'model':MODEL,'budget_reservation_id':key,'request_sha256':sha(packet)}
    response = {'schema_version':'news-gemini-batch-response-v1','request_identity':key,
        'body_base64':base64.b64encode(raw).decode(),'body_sha256':hashlib.sha256(raw).hexdigest(),
        'http_status':200,'replayable':True}
    value = budget.observe_response(key,intent,response)
    budget.finish(key,succeeded=False)
    assert value['usage_estimate_nanodollars'] == 1_830_000
    assert effective_commitment(store.state,policy) == 674_497_400
    assert store.state['settlements'][:len(old['settlements'])] == old['settlements']


def test_batch_manifest_is_frozen_to_fifty_one_targets_and_one_cached_batch():
    plan = ScopedGmaBatchPlan(batch_manifest())
    assert [len(b) for b in plan.batches([{'id':'n'+str(i)} for i in range(51)])] == [4]*12+[3]
    assert len(plan.manifest['accounting_extension']['allowed_request_sha256s']) == 12
    assert REQUESTS[3] not in plan.manifest['accounting_extension']['allowed_request_sha256s']
    changed = batch_manifest();changed['sizes'][0] = 8
    with pytest.raises(ResolutionError):ScopedGmaBatchPlan(changed)
    plan.manifest['request_sha256s'][0] = '0'*64
    with pytest.raises(ResolutionError):plan.batches([{'id':'n'+str(i)} for i in range(51)])


@pytest.mark.parametrize('operation',['ner','outputs','activate','pilot-apply'])
def test_continuation_authority_rejects_other_operations(operation):
    from app.services.news_three_article_pilot import PilotAuthority
    from app.services.news_gma_scoped_continuation import validate_authority, VERSION
    policy = {'schema_version':VERSION,'allowed_operations':[operation]}
    with pytest.raises(ResolutionError,match='authority_invalid'):
        validate_authority(PilotAuthority(policy,sha(policy),None),None)


def test_transition_concurrency_cannot_overwrite_newer_ledger():
    store,old,policy,objects,packets,budget = setup()
    store.state = deepcopy(old)
    original = store.compare_and_swap
    def conflicting(generation,state):
        store.generation += 1
        original(generation,state)
    with patch.object(store,'compare_and_swap',side_effect=conflicting):
        with pytest.raises(ResolutionError,match='concurrent'):
            extend_ledger(store,'selection',policy,baseline_sha256=sha(old),journal=Objects())
    assert store.state == old
