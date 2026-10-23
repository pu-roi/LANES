"""A new source body gets bounded slots, never a reset balance or silent retries."""
from copy import deepcopy
from unittest.mock import patch

import pytest

from app.services.news_source_repair_budget import SourceRepairBudget, extend, repair_commitment
from app.services.news_source_repair import SESSION
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_pilot_budget import MODEL
from app.services.news_pilot_accounting import accounting_policy, reservation
from app.services.news_gma_scoped_budget import effective_commitment
from test_news_gma_scoped_continuation import setup as previous_setup, resume
from test_news_pilot_budget import payload
from test_news_pilot_accounting import Objects


def previous():
    store, _old, policy, objects, packets, budget = previous_setup()
    resume(store)
    for i, packet in enumerate(packets):
        key = budget.reserve(MODEL,packet,{})
        store.state['settlements'].append({'attempt_id':key,'usage_estimate_nanodollars':4_000_000 if i<11 else 14_802_200,
            'policy_sha256':sha(policy),'response_bundle_sha256':sha(i)})
        budget.finish(key,succeeded=True)
    store.state['status']='stopped'
    assert effective_commitment(store.state,policy)==731_469_600
    return store


def candidate(store):
    p=payload(99);objects=Objects()
    policy={'schema_version':'source-repair-accounting-v1','session_id':SESSION,'limit_nanodollars':1_000_000_000,'request_sha256s':[sha(p)]}
    counts={'schema_version':'news-pilot-count-catalog-v2','accounting_policy_sha256':sha(accounting_policy()),
        'requests':[{'request_sha256':sha(p),'total_tokens':6000,'reserved_nanodollars':reservation(p,6000),
            'model':MODEL,'accounting_policy_sha256':sha(accounting_policy())}]}
    return p,policy,counts,objects


def test_preserves_all_consumed_attempts_and_settlements_and_old_worker_rejects():
    store=previous();old=deepcopy(store.state);p,policy,counts,objects=candidate(store)
    extend(store,policy,sha(old),objects)
    assert store.state['attempts']==old['attempts'] and store.state['settlements']==old['settlements']
    assert repair_commitment(store.state,policy)==731_469_600
    with pytest.raises(ResolutionError):effective_commitment(store.state,old['accounting_extension'])
    with pytest.raises(ResolutionError):extend(store,policy,sha(old),objects)


def test_reserve_before_dispatch_and_interrupt_blocks_resend():
    store=previous();p,policy,counts,objects=candidate(store)
    extend(store,policy,sha(store.state),objects)
    budget=SourceRepairBudget(store,'selection',policy=policy,counts=counts,journal=objects)
    with pytest.raises(ResolutionError,match='stopped'):budget.reserve(MODEL,p,{})
    store.state['status']='ready';store.state['manual_resumptions'].append({'id':SESSION})
    key=budget.reserve(MODEL,p,{})
    assert len(store.state['attempts'])==37 and store.state['attempts'][-1]['status']=='in_flight'
    with pytest.raises(ResolutionError):budget.reserve(MODEL,p,{})
    budget.finish(key,succeeded=False)
    store.state['status']='ready'
    with pytest.raises(ResolutionError,match='already_dispatched'):budget.reserve(MODEL,p,{})


@pytest.mark.parametrize('tamper',['attempt','settlement','counts','over_cap'])
def test_tampering_and_cap_exhaustion_stop_before_any_new_reservation(tamper):
    store=previous();p,policy,counts,objects=candidate(store)
    extend(store,policy,sha(store.state),objects)
    budget=SourceRepairBudget(store,'selection',policy=policy,counts=counts,journal=objects)
    store.state['status']='ready';store.state['manual_resumptions'].append({'id':SESSION})
    if tamper=='attempt':store.state['attempts'][0]['reserved_nanodollars']+=1
    if tamper=='settlement':store.state['settlements'][0]['usage_estimate_nanodollars']+=1
    if tamper=='counts':budget.counts['requests'][0]['total_tokens']+=1
    if tamper=='over_cap':
        budget.counts['requests'][0].update(total_tokens=999999,reserved_nanodollars=reservation(p,999999))
    with pytest.raises(ResolutionError):budget.reserve(MODEL,p,{})
    assert len(store.state['attempts'])==36


def test_receipt_storage_failure_prevents_accounting_transition():
    store=previous();old=deepcopy(store.state);_p,policy,_counts,objects=candidate(store)
    with patch.object(objects,'put',side_effect=ResolutionError('storage_failed')):
        with pytest.raises(ResolutionError):extend(store,policy,sha(old),objects)
    assert store.state==old


def test_unused_schedule_replacement_preserves_history_and_rejects_consumed_schedule():
    from app.services.news_source_repair_budget import replace_unused_schedule
    store=previous();p,policy,counts,objects=candidate(store)
    extend(store,policy,sha(store.state),objects)
    old=deepcopy(store.state)
    changed={**policy,'request_sha256s':[sha(payload(100))]}
    replace_unused_schedule(store,changed,sha(old),objects)
    assert store.state['attempts']==old['attempts'] and store.state['settlements']==old['settlements']
    assert repair_commitment(store.state,changed)==731_469_600
    store.state['attempts'].append({'id':'unexpected'})
    with pytest.raises(ResolutionError):replace_unused_schedule(store,policy,sha(store.state),objects)
