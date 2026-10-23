"""GMA-only accounting extension; original policies and settlements stay intact."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_pilot_accounting import (AccountedPilotBudget, accounting_policy,
    authenticated_response, commitment, reservation)
from app.services.news_pilot_budget import LIMIT, MODEL, new_ledger

VERSION = 'news-pilot-budget-v3'
SESSION = 'gma-scoped-populate-20261023-v1'


def extension_policy(requests: list[str]) -> dict:
    if len(requests) != 12 or len(set(requests)) != 12:
        raise ResolutionError('gma_scoped_schedule_invalid')
    return {'schema_version':'gma-scoped-accounting-extension-v1', 'session_id':SESSION,
        'previous_policy_sha256':sha(accounting_policy()), 'limit_nanodollars':LIMIT,
        'initial_attempt_count':24, 'maximum_attempt_count':36,
        'allowed_request_sha256s':list(requests)}


def effective_commitment(state: dict, policy: dict) -> int:
    """Validate old and new policy ownership without rewriting any receipt."""
    if (state.get('schema_version') != VERSION or state.get('accounting_policy_sha256') != sha(policy)
            or state.get('accounting_extension') != policy):
        raise ResolutionError('gma_scoped_accounting_identity_changed')
    transition = state.get('accounting_transition', {})
    attempts = state.get('attempts', [])
    settlements = state.get('settlements', [])
    old_count = transition.get('previous_settlement_count')
    if (len(attempts) < 24 or len(attempts) > 36 or type(old_count) is not int
            or old_count < 0 or len(settlements) < old_count
            or sha(attempts[:24]) != transition.get('previous_attempts_sha256')
            or sha(settlements[:old_count]) != transition.get('previous_settlements_sha256')):
        raise ResolutionError('gma_scoped_accounting_history_changed')
    old_ids = {a['id'] for a in attempts[:24]}
    for index, value in enumerate(settlements):
        old = index < old_count
        if (value.get('policy_sha256') != (sha(accounting_policy()) if old else sha(policy))
                or (value['attempt_id'] in old_ids) is not old):
            raise ResolutionError('gma_scoped_settlement_owner_changed')
    new = attempts[24:]
    if (len({a.get('request_sha256') for a in new}) != len(new)
            or any(a.get('request_sha256') not in policy['allowed_request_sha256s']
                or a.get('session_id') != SESSION for a in new)):
        raise ResolutionError('gma_scoped_request_not_authorized')
    normalized = deepcopy(state)
    for value in normalized['settlements']:
        value['policy_sha256'] = sha(accounting_policy())
    return commitment(normalized)


def extend_ledger(store: object, identity: str, policy: dict, *, baseline_sha256: str,
                  journal: object) -> dict:
    state, generation = store.read()
    if (sha(state) != baseline_sha256 or state.get('schema_version') != 'news-pilot-budget-v2'
            or state.get('accounting_policy_sha256') != sha(accounting_policy())
            or state.get('identity') != identity or state.get('status') != 'stopped'
            or len(state['attempts']) != 24 or commitment(state) != 672_667_400
            or sum(a['reserved_nanodollars'] for a in state['attempts']) != 870_978_600
            or any(a['status'] == 'in_flight' for a in state['attempts'])
            or policy != extension_policy(policy['allowed_request_sha256s'])):
        raise ResolutionError('gma_scoped_extension_baseline_changed')
    old = deepcopy(state)
    transition = {'schema_version':'gma-scoped-ledger-transition-v1',
        'previous_ledger_sha256':baseline_sha256, 'previous_policy_sha256':sha(accounting_policy()),
        'previous_attempts_sha256':sha(old['attempts']),
        'previous_settlements_sha256':sha(old['settlements']),
        'previous_settlement_count':len(old['settlements']), 'new_policy_sha256':sha(policy)}
    state.update(schema_version=VERSION, accounting_policy_sha256=sha(policy),
        accounting_extension=deepcopy(policy), accounting_transition=transition)
    if effective_commitment(state, policy) != 672_667_400:
        raise ResolutionError('gma_scoped_extension_commitment_changed')
    journal.put(baseline_sha256+'/previous-ledger.json', old)
    journal.put(sha(transition)+'/accounting-transition.json', transition)
    store.compare_and_swap(generation, state)
    return state


class ScopedGmaBudget(AccountedPilotBudget):
    """Only the frozen GMA requests may consume the twelve extra slots."""
    def __init__(self, store: object, identity: str, *, policy: dict, counts: dict,
                 counts_sha256: str, journal: object) -> None:
        super().__init__(store, identity, counts=counts, counts_sha256=counts_sha256, journal=journal)
        if policy != extension_policy(policy['allowed_request_sha256s']):
            raise ResolutionError('gma_scoped_policy_changed')
        self.policy = deepcopy(policy)

    def _read(self) -> tuple[dict, str]:
        state, generation = self.store.read()
        expected = new_ledger(self.identity)
        if any(state.get(k) != expected[k] for k in ('identity','limit_nanodollars','model','price')):
            raise ResolutionError('gma_scoped_budget_target_changed')
        effective_commitment(state, self.policy)
        return state, generation

    def reserve(self, model: str, payload: dict, context: dict) -> str:
        pin = sha(payload)
        if (model != MODEL or pin not in self.policy['allowed_request_sha256s']
                or sha(self.counts) != self.counts_pin):
            raise ResolutionError('gma_scoped_request_not_authorized')
        matches = [c for c in self.counts['requests'] if c['request_sha256'] == pin]
        if len(matches) != 1:
            raise ResolutionError('pilot_uncounted_request')
        item = matches[0]
        cost = reservation(payload, item['total_tokens'])
        if (item['model'] != MODEL or item['accounting_policy_sha256'] != sha(accounting_policy())
                or item['reserved_nanodollars'] != cost):
            raise ResolutionError('pilot_token_count_changed')
        state, generation = self._read()
        if state['status'] != 'ready' or any(a['status'] == 'in_flight' for a in state['attempts']):
            raise ResolutionError('pilot_budget_stopped_or_in_flight')
        if state.get('manual_resumptions', [{}])[-1].get('id') != SESSION:
            raise ResolutionError('gma_scoped_resume_required')
        key = sha({'request_sha256':pin,'context':context})
        if any(a['id'] == key or a.get('request_sha256') == pin for a in state['attempts']):
            raise ResolutionError('pilot_budget_attempt_already_reserved')
        if len(state['attempts']) >= 36 or effective_commitment(state,self.policy)+cost > LIMIT:
            raise ResolutionError('pilot_budget_exhausted')
        # Reserve every outstanding maximum logically, not just this request.
        used = {a.get('request_sha256') for a in state['attempts'][24:]}
        remaining = sum(c['reserved_nanodollars'] for c in self.counts['requests']
            if c['request_sha256'] in self.policy['allowed_request_sha256s'] and c['request_sha256'] not in used)
        if effective_commitment(state,self.policy)+remaining > LIMIT:
            raise ResolutionError('pilot_budget_schedule_exhausted')
        state['attempts'].append({'id':key,'request_sha256':pin,'context':context,
            'reserved_nanodollars':cost,'status':'in_flight','session_id':SESSION,
            'at':datetime.now(timezone.utc).isoformat(),'count_catalog_sha256':self.counts_pin})
        self.store.compare_and_swap(generation,state)
        return key

    def observe_response(self, key: str, intent: dict, response: dict) -> dict:
        bundle = {'intent':intent,'response':response}
        pin = sha(bundle)
        bound, value = authenticated_response(bundle,pin)
        state,generation = self._read()
        attempt = next((a for a in state['attempts'][24:] if a['id'] == key),None)
        if (bound['budget_reservation_id'] != key or attempt is None or attempt['status'] != 'in_flight'
                or any(s['attempt_id'] == key for s in state['settlements'])):
            raise ResolutionError('pilot_accounting_attempt_invalid')
        receipt = {**value,'schema_version':'news-pilot-settlement-v3','attempt_id':key,
            'policy_sha256':sha(self.policy),'response_bundle_sha256':pin}
        self.journal.put(sha(receipt)+'/accounting.json',receipt)
        state['settlements'].append(receipt)
        over = value['usage_estimate_nanodollars'] > attempt['reserved_nanodollars']
        if over:
            state['status'] = 'stopped'
        self.store.compare_and_swap(generation,state)
        if over:
            raise ResolutionError('pilot_accounting_reservation_exceeded')
        return value
