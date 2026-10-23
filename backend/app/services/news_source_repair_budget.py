"""Append-only continuation of the consumed pilot ledger under its unchanged $1 cap."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_pilot_accounting import accounting_policy, commitment, reservation, authenticated_response
from app.services.news_pilot_budget import PilotBudget, MODEL, LIMIT, new_ledger
from app.services.news_gma_scoped_budget import effective_commitment
from app.services.news_source_repair import SESSION

VERSION = 'news-source-repair-budget-v1'


def repair_commitment(state: dict, policy: dict) -> int:
    transition = state.get('source_repair_transition', {})
    n = transition.get('settlement_count')
    if (state.get('schema_version') != VERSION or state.get('accounting_policy_sha256') != sha(policy)
            or state.get('source_repair_policy') != policy or type(n) is not int
            or len(state.get('attempts', [])) < 36 or len(state['attempts']) > 36+len(policy['request_sha256s'])
            or sha(state['attempts'][:36]) != transition.get('attempts_sha256')
            or sha(state.get('settlements', [])[:n]) != transition.get('settlements_sha256')):
        raise ResolutionError('source_repair_budget_history_changed')
    previous = deepcopy(state)
    previous.update(schema_version='news-pilot-budget-v3', accounting_policy_sha256=sha(state['accounting_extension']),
        attempts=previous['attempts'][:36], settlements=previous['settlements'][:n])
    effective_commitment(previous, state['accounting_extension'])
    extra = state['attempts'][36:]
    if (len({a.get('request_sha256') for a in extra}) != len(extra)
            or any(a.get('request_sha256') not in policy['request_sha256s'] or a.get('session_id') != SESSION for a in extra)):
        raise ResolutionError('source_repair_request_not_authorized')
    extra_ids = {a['id'] for a in extra}
    for entry in state['settlements'][n:]:
        if entry['attempt_id'] not in extra_ids or entry['policy_sha256'] != sha(policy):
            raise ResolutionError('source_repair_settlement_changed')
    normalized = deepcopy(state)
    for entry in normalized['settlements']:
        entry['policy_sha256'] = sha(accounting_policy())
    return commitment(normalized)


def extend(store: object, policy: dict, baseline_sha256: str, journal: object) -> dict:
    state, generation = store.read()
    if (sha(state) != baseline_sha256 or state['status'] != 'stopped' or len(state['attempts']) != 36
            or effective_commitment(state, state['accounting_extension']) != 731_469_600
            or any(a['status'] == 'in_flight' for a in state['attempts'])
            or policy.get('session_id') != SESSION or policy.get('limit_nanodollars') != LIMIT
            or not 1 <= len(policy['request_sha256s']) <= 8 or len(set(policy['request_sha256s'])) != len(policy['request_sha256s'])):
        raise ResolutionError('source_repair_budget_baseline_changed')
    old = deepcopy(state)
    transition = {'schema_version': VERSION, 'previous_ledger_sha256': sha(old),
        'attempts_sha256': sha(old['attempts']), 'settlements_sha256': sha(old['settlements']),
        'settlement_count': len(old['settlements']), 'policy_sha256':sha(policy)}
    state.update(schema_version=VERSION, accounting_policy_sha256=sha(policy),
        source_repair_policy=deepcopy(policy), source_repair_transition=transition)
    if repair_commitment(state, policy) != 731_469_600:
        raise ResolutionError('source_repair_accounting_changed')
    journal.put(sha(old)+'/previous-ledger.json', old)
    journal.put(sha(transition)+'/source-repair-transition.json', transition)
    store.compare_and_swap(generation, state)
    return state


def replace_unused_schedule(store: object, policy: dict, baseline_sha256: str, journal: object) -> dict:
    """Explicit repair after a pre-dispatch rejection; never replace used slots."""
    state, generation = store.read()
    old = deepcopy(state)
    if (sha(state) != baseline_sha256 or state['status'] != 'stopped'
            or len(state['attempts']) != 36
            or repair_commitment(state, state['source_repair_policy']) != 731_469_600
            or policy.get('session_id') != SESSION or policy.get('limit_nanodollars') != LIMIT
            or not 1 <= len(policy.get('request_sha256s', [])) <= 8
            or len(set(policy['request_sha256s'])) != len(policy['request_sha256s'])):
        raise ResolutionError('source_repair_schedule_already_used_or_changed')
    transition = {'schema_version':'source-repair-unused-schedule-transition-v1',
        'previous_ledger_sha256':sha(old), 'previous_policy_sha256':sha(state['source_repair_policy']),
        'replacement_policy_sha256':sha(policy)}
    state.update(accounting_policy_sha256=sha(policy), source_repair_policy=deepcopy(policy))
    state.setdefault('source_repair_schedule_transitions', []).append(transition)
    assert repair_commitment(state, policy) == 731_469_600
    journal.put(sha(old)+'/previous-unused-schedule.json', old)
    journal.put(sha(transition)+'/unused-schedule-transition.json', transition)
    store.compare_and_swap(generation, state)
    return state


class SourceRepairBudget(PilotBudget):
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
        repair_commitment(state, self.policy)
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
        used = {a.get('request_sha256') for a in state['attempts'][36:]}
        if pin in used:
            raise ResolutionError('source_repair_already_dispatched')
        outstanding = sum(r['reserved_nanodollars'] for r in self.counts['requests'] if r['request_sha256'] not in used)
        if repair_commitment(state, self.policy)+outstanding > LIMIT:
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
        attempt = next((a for a in state['attempts'][36:] if a['id']==key),None)
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
