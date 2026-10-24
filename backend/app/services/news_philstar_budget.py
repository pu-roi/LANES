"""Append-only Philstar continuation of the stopped 46-attempt pilot ledger."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from app.services.news_tribune_budget import effective_commitment as previous_commitment
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_pilot_accounting import accounting_policy, commitment, reservation, authenticated_response
from app.services.news_pilot_budget import PilotBudget, MODEL, LIMIT, new_ledger
from app.services.news_philstar_pilot import SESSION, require

VERSION = 'news-philstar-budget-v2'
APPROVED_LIMIT = 1_500_000_000
CAP_APPROVAL = {'basis': 'explicit_developer_budget_selection', 'approved_by': 'roicambe',
                'approved_on': '2026-10-24', 'session_id': SESSION,
                'previous_limit_nanodollars': LIMIT, 'cumulative_limit_nanodollars': APPROVED_LIMIT}


def schedule_floor(packets: list[dict], previous_nanodollars: int, *, cumulative_limit: int = LIMIT) -> dict:
    """Reject an impossible complete schedule without even counting tokens.

    One input token is a lower bound, never a tokenizer estimate or an
    authorization to generate. Counted full reservations are still required.
    """
    import hashlib
    import json
    from app.services.news_philstar_pilot import BODY
    require(type(cumulative_limit) is int and cumulative_limit in (LIMIT, APPROVED_LIMIT)
        and type(previous_nanodollars) is int and 0 <= previous_nanodollars <= cumulative_limit
        and 1 <= len(packets) <= 64, 'philstar_schedule_invalid')
    for packet in packets:
        document = json.loads(packet['payload']['contents'][0]['parts'][0]['text'])
        require(hashlib.sha256(document['evidence_text'].encode()).hexdigest() == BODY
            and 1 <= len(document['targets']) <= 4, 'philstar_schedule_source_or_batch_changed')
    floor = sum(reservation(packet['payload'], 1) for packet in packets)
    return dict(previous_nanodollars=previous_nanodollars,
        reservation_lower_bound_nanodollars=floor, limit_nanodollars=cumulative_limit,
        minimum_cumulative_nanodollars=previous_nanodollars + floor,
        requires_token_count=previous_nanodollars + floor <= cumulative_limit,
        generation_authorized=False)


def effective_commitment(state: dict, policy: dict) -> int:
    transition = state.get('philstar_transition', {})
    n = transition.get('settlement_count')
    require(policy.get('limit_nanodollars') == APPROVED_LIMIT and policy.get('cap_approval') == CAP_APPROVAL
        and state.get('schema_version') == VERSION and state.get('philstar_policy') == policy
        and state.get('accounting_policy_sha256') == sha(policy) and type(n) is int
        and 46 <= len(state['attempts']) <= 46 + len(policy['request_sha256s'])
        and sha(state['attempts'][:46]) == transition.get('attempts_sha256')
        and sha(state['settlements'][:n]) == transition.get('settlements_sha256'), 'philstar_budget_history_changed')
    previous = deepcopy(state)
    previous.update(schema_version='news-tribune-budget-v1', accounting_policy_sha256=sha(state['tribune_policy']),
        attempts=previous['attempts'][:46], settlements=previous['settlements'][:n])
    require(previous_commitment(previous, previous['tribune_policy']) == 768326100, 'philstar_budget_baseline_changed')
    extra = state['attempts'][46:]
    require(len({a['request_sha256'] for a in extra}) == len(extra)
        and all(a['request_sha256'] in policy['request_sha256s'] and a['session_id'] == SESSION for a in extra),
        'philstar_budget_request_changed')
    ids = {a['id'] for a in extra}
    require(all(s['attempt_id'] in ids and s['policy_sha256'] == sha(policy) for s in state['settlements'][n:]),
        'philstar_budget_settlement_changed')
    normalized = deepcopy(state)
    for s in normalized['settlements']:
        s['policy_sha256'] = sha(accounting_policy())
    return commitment(normalized)


def extend(store: object, policy: dict, baseline_sha256: str, journal: object) -> dict:
    state, generation = store.read()
    require(sha(state) == baseline_sha256 and state['status'] == 'stopped'
        and len(state['attempts']) == 46 and not any(a['status'] == 'in_flight' for a in state['attempts'])
        and previous_commitment(state, state['tribune_policy']) == 768326100
        and policy.get('session_id') == SESSION and policy.get('limit_nanodollars') == APPROVED_LIMIT
        and policy.get('cap_approval') == CAP_APPROVAL
        and 1 <= len(policy.get('request_sha256s', [])) <= 64
        and len(set(policy['request_sha256s'])) == len(policy['request_sha256s']), 'philstar_budget_baseline_changed')
    old = deepcopy(state)
    transition = dict(previous_ledger_sha256=sha(old), attempts_sha256=sha(state['attempts']),
        settlements_sha256=sha(state['settlements']), settlement_count=len(state['settlements']), policy_sha256=sha(policy))
    state.update(schema_version=VERSION, philstar_policy=deepcopy(policy), philstar_transition=transition,
        accounting_policy_sha256=sha(policy))
    require(effective_commitment(state, policy) == 768326100, 'philstar_budget_accounting_changed')
    journal.put(sha(old)+'/previous-ledger.json', old)
    journal.put(sha(transition)+'/philstar-transition.json', transition)
    store.compare_and_swap(generation, state)
    return state


class PhilstarBudget(PilotBudget):
    def __init__(self, store: object, identity: str, *, policy: dict, counts: dict, journal: object) -> None:
        super().__init__(store, identity)
        self.policy, self.counts, self.journal = deepcopy(policy), deepcopy(counts), journal
        require(counts.get('schema_version') == 'news-pilot-count-catalog-v2'
            and counts.get('accounting_policy_sha256') == sha(accounting_policy())
            and [r['request_sha256'] for r in counts['requests']] == policy['request_sha256s']
            and sha(counts) == policy['counts_sha256']
            and all(type(r['reserved_nanodollars']) is int and r['reserved_nanodollars'] > 0
                for r in counts['requests']), 'philstar_budget_counts_changed')

    def _read(self) -> tuple[dict, str]:
        state, generation = self.store.read()
        expected = new_ledger(self.identity)
        require(all(state.get(k) == expected[k] for k in ('identity','model','limit_nanodollars','price')),
            'philstar_budget_target_changed')
        effective_commitment(state, self.policy)
        return state, generation

    def reserve(self, model: str, payload: dict, context: dict) -> str:
        pin = sha(payload)
        rows = [r for r in self.counts['requests'] if r['request_sha256'] == pin]
        require(model == MODEL and len(rows) == 1, 'philstar_request_uncounted')
        row = rows[0]
        cost = reservation(payload, row['total_tokens'])
        require(row['model'] == MODEL and row['reserved_nanodollars'] == cost
            and row['accounting_policy_sha256'] == sha(accounting_policy()), 'philstar_counts_changed')
        state, generation = self._read()
        require(state['status'] == 'ready' and state.get('manual_resumptions', [{}])[-1].get('id') == SESSION
            and not any(a['status'] == 'in_flight' for a in state['attempts']), 'philstar_budget_stopped')
        used = {a['request_sha256'] for a in state['attempts'][46:]}
        require(pin not in used, 'philstar_request_already_dispatched')
        outstanding = sum(r['reserved_nanodollars'] for r in self.counts['requests'] if r['request_sha256'] not in used)
        require(effective_commitment(state, self.policy) + outstanding <= self.policy['limit_nanodollars'],
                'philstar_budget_schedule_exhausted')
        key = sha(dict(request_sha256=pin, context=context))
        state['attempts'].append(dict(id=key, request_sha256=pin, context=context, reserved_nanodollars=cost,
            status='in_flight', session_id=SESSION, count_catalog_sha256=sha(self.counts), at=datetime.now(timezone.utc).isoformat()))
        self.store.compare_and_swap(generation, state)
        return key

    def observe_response(self, key: str, intent: dict, response: dict) -> dict:
        bundle = dict(intent=intent, response=response)
        pin = sha(bundle)
        bound, value = authenticated_response(bundle, pin)
        state, generation = self._read()
        attempt = next((a for a in state['attempts'][46:] if a['id'] == key), None)
        require(bound['budget_reservation_id'] == key and attempt is not None and attempt['status'] == 'in_flight'
            and not any(s['attempt_id'] == key for s in state['settlements']), 'philstar_accounting_invalid')
        receipt = dict(**value, schema_version=VERSION, attempt_id=key, policy_sha256=sha(self.policy), response_bundle_sha256=pin)
        self.journal.put(sha(receipt)+'/accounting.json', receipt)
        state['settlements'].append(receipt)
        over = value['usage_estimate_nanodollars'] > attempt['reserved_nanodollars']
        if over:
            state['status'] = 'stopped'
        self.store.compare_and_swap(generation, state)
        require(not over, 'philstar_accounting_reservation_exceeded')
        return value
