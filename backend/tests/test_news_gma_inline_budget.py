"""One new slot cannot reset previous history or permit resend."""
from copy import deepcopy
from unittest.mock import patch
import pytest
from app.services.news_gma_inline_budget import InlineBudget,extend,inline_commitment
from app.services.news_gma_heading_budget import HeadingBudget,heading_commitment
from app.services.news_gma_inline_continuation import SESSION
from app.services.news_gma_heading_repair import SESSION as OLD_SESSION
from app.services.news_pilot_budget import MODEL
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from test_news_gma_heading_budget import setup as previous_setup,selection
from test_news_pilot_accounting import Objects


def setup():
    store,_,packets,old_policy,counts,objects=previous_setup()
    guard=HeadingBudget(store,'selection',policy=old_policy,counts=counts,journal=objects)
    store.state['status']='ready';store.state['manual_resumptions'].append({'id':OLD_SESSION})
    for p,cost in zip(packets[:2],[3_000_000,4_022_200]):
        key=guard.reserve(MODEL,p,{})
        store.state['settlements'].append({'attempt_id':key,'usage_estimate_nanodollars':cost,
            'policy_sha256':sha(old_policy),'response_bundle_sha256':sha(key)})
        guard.finish(key,succeeded=True)
    store.state['status']='stopped';assert heading_commitment(store.state,old_policy)==748841000
    packets,policy,counts=selection(SESSION,500)
    policy['request_sha256s']=policy['request_sha256s'][:1];counts['requests']=counts['requests'][:1]
    objects=Objects();old=deepcopy(store.state);extend(store,policy,sha(old),objects)
    return store,old,packets[0],policy,counts,objects


def test_one_request_ceiling_preserves_history_and_rejects_resend():
    store,old,p,policy,counts,objects=setup()
    assert inline_commitment(store.state,policy)==748841000
    assert store.state['attempts']==old['attempts'] and store.state['settlements']==old['settlements']
    with pytest.raises(ResolutionError):heading_commitment(store.state,old['heading_policy'])
    budget=InlineBudget(store,'selection',policy=policy,counts=counts,journal=objects)
    with pytest.raises(ResolutionError):budget.reserve(MODEL,p,{})
    store.state['status']='ready';store.state['manual_resumptions'].append({'id':SESSION})
    key=budget.reserve(MODEL,p,{})
    assert len(store.state['attempts'])==42
    with pytest.raises(ResolutionError):budget.reserve(MODEL,p,{})
    budget.finish(key,succeeded=False);store.state['status']='ready'
    with pytest.raises(ResolutionError):budget.reserve(MODEL,p,{})


@pytest.mark.parametrize('change',['attempt','settlement','count','cap'])
def test_changed_history_and_cost_stop_before_dispatch(change):
    store,old,p,policy,counts,objects=setup();budget=InlineBudget(store,'selection',policy=policy,counts=counts,journal=objects)
    store.state['status']='ready';store.state['manual_resumptions'].append({'id':SESSION})
    if change=='attempt':store.state['attempts'][0]['reserved_nanodollars']+=1
    if change=='settlement':store.state['settlements'][0]['usage_estimate_nanodollars']+=1
    if change=='count':budget.counts['requests'][0]['total_tokens']+=1
    if change=='cap':budget.counts['requests'][0]['reserved_nanodollars']=999999999
    with pytest.raises(ResolutionError):budget.reserve(MODEL,p,{})
    assert len(store.state['attempts'])==41


def test_transition_storage_failure_and_concurrent_generation_do_not_reset_history():
    store,old,p,policy,counts,objects=setup();store.state=deepcopy(old)
    with patch.object(objects,'put',side_effect=ResolutionError('storage_failed')):
        with pytest.raises(ResolutionError):extend(store,policy,sha(old),objects)
    assert store.state==old
    with patch.object(store,'compare_and_swap',side_effect=ResolutionError('concurrent_generation')):
        with pytest.raises(ResolutionError):extend(store,policy,sha(old),objects)
    assert store.state==old
