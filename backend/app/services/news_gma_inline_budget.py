"""One new request; preserve all 41 previously accounted attempts."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime,timezone
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_pilot_budget import PilotBudget,MODEL,LIMIT,new_ledger
from app.services.news_pilot_accounting import accounting_policy,commitment,reservation,authenticated_response
from app.services.news_gma_heading_budget import heading_commitment,VERSION as PREVIOUS_VERSION
from app.services.news_gma_inline_continuation import SESSION
VERSION='news-gma-inline-budget-v1'


def inline_commitment(state: dict,policy: dict) -> int:
    t=state.get('inline_transition',{});n=t.get('settlement_count')
    if (state.get('schema_version')!=VERSION or state.get('inline_policy')!=policy
            or state.get('accounting_policy_sha256')!=sha(policy) or type(n) is not int
            or not 41<=len(state.get('attempts',[]))<=42
            or sha(state['attempts'][:41])!=t.get('attempts_sha256')
            or sha(state.get('settlements',[])[:n])!=t.get('settlements_sha256')):
        raise ResolutionError('inline_budget_history_changed')
    previous=deepcopy(state)
    previous.update(schema_version=PREVIOUS_VERSION,accounting_policy_sha256=sha(state['heading_policy']),
        attempts=previous['attempts'][:41],settlements=previous['settlements'][:n])
    if heading_commitment(previous,previous['heading_policy'])!=748841000:
        raise ResolutionError('inline_budget_baseline_changed')
    extra=state['attempts'][41:];ids={a['id'] for a in extra}
    if any(a.get('request_sha256') not in policy['request_sha256s'] or a.get('session_id')!=SESSION for a in extra):
        raise ResolutionError('inline_budget_request_changed')
    if any(s['attempt_id'] not in ids or s['policy_sha256']!=sha(policy) for s in state['settlements'][n:]):
        raise ResolutionError('inline_budget_settlement_changed')
    normalized=deepcopy(state)
    for s in normalized['settlements']:s['policy_sha256']=sha(accounting_policy())
    return commitment(normalized)


def extend(store: object,policy: dict,baseline_sha256: str,journal: object) -> dict:
    state,generation=store.read();old=deepcopy(state)
    if (sha(state)!=baseline_sha256 or state['status']!='stopped' or len(state['attempts'])!=41
            or any(a['status']=='in_flight' for a in state['attempts'])
            or heading_commitment(state,state['heading_policy'])!=748841000
            or policy.get('session_id')!=SESSION or policy.get('limit_nanodollars')!=LIMIT
            or len(policy.get('request_sha256s',[]))!=1):
        raise ResolutionError('inline_budget_baseline_changed')
    transition={'schema_version':VERSION,'previous_ledger_sha256':sha(old),
        'attempts_sha256':sha(state['attempts']),'settlements_sha256':sha(state['settlements']),
        'settlement_count':len(state['settlements']),'policy_sha256':sha(policy)}
    state.update(schema_version=VERSION,accounting_policy_sha256=sha(policy),inline_policy=deepcopy(policy),inline_transition=transition)
    if inline_commitment(state,policy)!=748841000:raise ResolutionError('inline_budget_accounting_changed')
    journal.put(sha(old)+'/previous-ledger.json',old);journal.put(sha(transition)+'/inline-transition.json',transition)
    store.compare_and_swap(generation,state)
    return state


class InlineBudget(PilotBudget):
    def __init__(self, store: object, identity: str, *, policy: dict, counts: dict, journal: object) -> None:
        super().__init__(store, identity)
        self.policy, self.counts, self.journal = deepcopy(policy), deepcopy(counts), journal
        if ([r['request_sha256'] for r in counts['requests']] != policy['request_sha256s']
                or counts['accounting_policy_sha256'] != sha(accounting_policy())
                or counts['schema_version'] != 'news-pilot-count-catalog-v2'):
            raise ResolutionError('source_repair_counts_changed')

    def _read(self) -> tuple[dict, str]:
        state, generation = self.store.read(); expected = new_ledger(self.identity)
        if any(state.get(k) != expected[k] for k in ('identity','model','limit_nanodollars','price')):
            raise ResolutionError('source_repair_budget_target_changed')
        inline_commitment(state, self.policy)
        return state, generation

    def reserve(self, model: str, payload: dict, context: dict) -> str:
        pin = sha(payload)
        rows = [r for r in self.counts['requests'] if r['request_sha256'] == pin]
        if model != MODEL or len(rows) != 1:
            raise ResolutionError('source_repair_uncounted_request')
        row = rows[0]; cost = reservation(payload, row['total_tokens'])
        if row['reserved_nanodollars'] != cost or row['model'] != MODEL or row['accounting_policy_sha256'] != sha(accounting_policy()):
            raise ResolutionError('source_repair_counts_changed')
        state, generation = self._read()
        if (state['status'] != 'ready' or state.get('manual_resumptions', [{}])[-1].get('id') != SESSION
                or any(a['status'] == 'in_flight' for a in state['attempts'])):
            raise ResolutionError('source_repair_budget_stopped')
        used = {a.get('request_sha256') for a in state['attempts'][41:]}
        if pin in used:
            raise ResolutionError('source_repair_already_dispatched')
        outstanding = sum(r['reserved_nanodollars'] for r in self.counts['requests'] if r['request_sha256'] not in used)
        if inline_commitment(state, self.policy)+outstanding > LIMIT:
            raise ResolutionError('pilot_budget_schedule_exhausted')
        key = sha({'request_sha256':pin,'context':context})
        state['attempts'].append({'id':key,'request_sha256':pin,'context':context,'reserved_nanodollars':cost,
            'status':'in_flight','session_id':SESSION,'at':datetime.now(timezone.utc).isoformat(),
            'count_catalog_sha256':sha(self.counts)})
        self.store.compare_and_swap(generation,state)
        return key

    def observe_response(self, key: str, intent: dict, response: dict) -> dict:
        pin = sha({'intent':intent,'response':response})
        bound, value = authenticated_response({'intent':intent,'response':response}, pin)
        state, generation = self._read()
        attempt = next((a for a in state['attempts'][41:] if a['id']==key),None)
        if (bound['budget_reservation_id'] != key or attempt is None or attempt['status'] != 'in_flight'
                or any(s['attempt_id']==key for s in state['settlements'])):
            raise ResolutionError('source_repair_accounting_invalid')
        receipt = {**value,'schema_version':VERSION,'attempt_id':key,'policy_sha256':sha(self.policy),'response_bundle_sha256':pin}
        self.journal.put(sha(receipt)+'/accounting.json',receipt)
        state['settlements'].append(receipt)
        if value['usage_estimate_nanodollars'] > attempt['reserved_nanodollars']:
            state['status']='stopped';self.store.compare_and_swap(generation,state)
            raise ResolutionError('pilot_accounting_reservation_exceeded')
        self.store.compare_and_swap(generation,state)
        return value
