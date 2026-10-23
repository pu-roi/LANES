"""The v3 continuation preserves prior spending and grants only three requests."""
from copy import deepcopy
from unittest.mock import patch

import pytest

from app.services.news_gma_heading_budget import HeadingBudget,extend,heading_commitment
from app.services.news_gma_heading_repair import SESSION
from app.services.news_source_repair_budget import SourceRepairBudget,extend as old_extend,repair_commitment
from app.services.news_source_repair import SESSION as OLD_SESSION
from app.services.news_pilot_budget import MODEL
from app.services.news_pilot_accounting import accounting_policy,reservation
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from test_news_source_repair_budget import previous
from test_news_pilot_budget import payload
from test_news_pilot_accounting import Objects


def selection(session,offset):
    packets=[payload(offset+i) for i in range(3)]
    policy={'schema_version':'heading-accounting-v1','session_id':session,
        'limit_nanodollars':1_000_000_000,'request_sha256s':[sha(p) for p in packets]}
    counts={'schema_version':'news-pilot-count-catalog-v2','accounting_policy_sha256':sha(accounting_policy()),
        'requests':[{'request_sha256':sha(p),'total_tokens':6000,'reserved_nanodollars':reservation(p,6000),
            'model':MODEL,'accounting_policy_sha256':sha(accounting_policy())} for p in packets]}
    return packets,policy,counts


def baseline():
    store=previous();packets,policy,counts=selection(OLD_SESSION,200);objects=Objects()
    old_extend(store,policy,sha(store.state),objects)
    budget=SourceRepairBudget(store,'selection',policy=policy,counts=counts,journal=objects)
    store.state['status']='ready';store.state['manual_resumptions'].append({'id':OLD_SESSION})
    for p,cost in zip(packets,[3_000_000,3_000_000,4_349_200]):
        key=budget.reserve(MODEL,p,{})
        store.state['settlements'].append({'attempt_id':key,'usage_estimate_nanodollars':cost,
            'policy_sha256':sha(policy),'response_bundle_sha256':sha(key)})
        budget.finish(key,succeeded=True)
    store.state['status']='stopped'
    assert len(store.state['attempts'])==39 and repair_commitment(store.state,policy)==741818800
    return store


def setup():
    store=baseline();old=deepcopy(store.state);packets,policy,counts=selection(SESSION,300);objects=Objects()
    extend(store,policy,sha(old),objects)
    return store,old,packets,policy,counts,objects


def test_immutable_transition_preserves_39_attempts_and_old_worker_rejects():
    store,old,_,policy,_,objects=setup()
    assert store.state['attempts']==old['attempts'] and store.state['settlements']==old['settlements']
    assert heading_commitment(store.state,policy)==741818800 and len(objects.objects)==2
    with pytest.raises(ResolutionError):repair_commitment(store.state,old['source_repair_policy'])
    with pytest.raises(ResolutionError):extend(store,policy,sha(old),objects)


def test_exact_three_requests_and_uncertain_dispatch_cannot_resend():
    store,_,packets,policy,counts,objects=setup()
    budget=HeadingBudget(store,'selection',policy=policy,counts=counts,journal=objects)
    with pytest.raises(ResolutionError,match='stopped'):budget.reserve(MODEL,packets[0],{})
    store.state['status']='ready';store.state['manual_resumptions'].append({'id':SESSION})
    key=budget.reserve(MODEL,packets[0],{})
    assert len(store.state['attempts'])==40 and store.state['attempts'][-1]['status']=='in_flight'
    with pytest.raises(ResolutionError):budget.reserve(MODEL,packets[1],{})
    budget.finish(key,succeeded=False);store.state['status']='ready'
    with pytest.raises(ResolutionError,match='already_dispatched'):budget.reserve(MODEL,packets[0],{})
    for p in packets[1:]:
        key=budget.reserve(MODEL,p,{});budget.finish(key,succeeded=True)
    assert len(store.state['attempts'])==42
    with pytest.raises(ResolutionError):budget.reserve(MODEL,payload(999),{})


@pytest.mark.parametrize('tamper',['attempt','settlement','count','cap'])
def test_history_count_and_full_schedule_guards(tamper):
    store,_,packets,policy,counts,objects=setup()
    budget=HeadingBudget(store,'selection',policy=policy,counts=counts,journal=objects)
    store.state['status']='ready';store.state['manual_resumptions'].append({'id':SESSION})
    if tamper=='attempt':store.state['attempts'][0]['reserved_nanodollars']+=1
    if tamper=='settlement':store.state['settlements'][0]['usage_estimate_nanodollars']+=1
    if tamper=='count':budget.counts['requests'][0]['total_tokens']+=1
    if tamper=='cap':
        for r,p in zip(budget.counts['requests'],packets):
            r.update(total_tokens=500000,reserved_nanodollars=reservation(p,500000))
    with pytest.raises(ResolutionError):budget.reserve(MODEL,packets[0],{})
    assert len(store.state['attempts'])==39


def test_storage_failure_preserves_old_ledger():
    store=baseline();old=deepcopy(store.state);_,policy,_=selection(SESSION,300);objects=Objects()
    with patch.object(objects,'put',side_effect=ResolutionError('storage_failed')):
        with pytest.raises(ResolutionError):extend(store,policy,sha(old),objects)
    assert store.state==old
