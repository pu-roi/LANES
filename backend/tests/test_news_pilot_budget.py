"""Dispatch safety under interruption, stale generations and invalid requests."""
from copy import deepcopy
import json

import httpx
import pytest

from app.services.news_pilot_budget import PilotBudget, new_ledger, MODEL
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_ner_durable.gemini_resolution import provider_error_diagnostic


class Store:
    def __init__(self):
        self.state, self.generation = new_ledger('selection'), 1

    def read(self):
        return deepcopy(self.state), str(self.generation)

    def compare_and_swap(self, generation, value):
        if generation != str(self.generation):
            raise ResolutionError('pilot_budget_concurrent_or_storage_failure')
        self.state, self.generation = deepcopy(value), self.generation+1


def payload(size=10):
    return {'systemInstruction': {}, 'contents': ['x'*size], 'generationConfig': {
        'temperature': 0, 'maxOutputTokens': 8192, 'responseMimeType': 'application/json',
        'responseJsonSchema': {}}}


def test_interruption_and_failures_never_reset_reservations():
    store = Store(); budget = PilotBudget(store, 'selection')
    key = budget.reserve(MODEL, payload(), {'article': 1})
    held = store.state['attempts'][0]['reserved_nanodollars']
    with pytest.raises(ResolutionError, match='in_flight'):
        PilotBudget(store, 'selection').reserve(MODEL, payload(), {'article': 2})
    budget.finish(key, succeeded=False, diagnostic={'http_status': 402})
    with pytest.raises(ResolutionError, match='stopped'):
        budget.reserve(MODEL, payload(), {'article': 2})
    assert store.state['attempts'][0]['reserved_nanodollars'] == held


def test_budget_exhaustion_and_identical_request_replay():
    store = Store(); budget = PilotBudget(store, 'selection')
    key = budget.reserve(MODEL, payload(700000), {'article': 1})
    budget.finish(key, succeeded=True)
    with pytest.raises(ResolutionError, match='already_reserved'):
        budget.reserve(MODEL, payload(700000), {'article': 1})
    key = budget.reserve(MODEL, payload(700000), {'article': 2})
    budget.finish(key, succeeded=True)
    with pytest.raises(ResolutionError, match='exhausted'):
        budget.reserve(MODEL, payload(700000), {'article': 3})


def test_concurrent_stale_generation_and_wrong_identity_fail_closed():
    store = Store(); old, generation = store.read()
    PilotBudget(store, 'selection').reserve(MODEL, payload(), {'article': 1})
    with pytest.raises(ResolutionError, match='concurrent'):
        store.compare_and_swap(generation, old)
    with pytest.raises(ResolutionError, match='identity'):
        PilotBudget(store, 'other-selection').reserve(MODEL, payload(), {})
    assert len(store.state['attempts']) == 1


def test_tools_and_different_models_are_not_budgeted():
    budget = PilotBudget(Store(), 'selection')
    with pytest.raises(ResolutionError, match='request_invalid'):
        budget.reserve('some-other-model', payload(), {})
    with pytest.raises(ResolutionError, match='request_invalid'):
        budget.reserve(MODEL, {**payload(), 'tools': []}, {})


@pytest.mark.asyncio
async def test_diagnostic_never_retains_provider_text_or_key():
    secret = 'fictional-secret-never-echo'
    response = httpx.Response(400, json={'error': {'status': 'INVALID_ARGUMENT',
        'message': 'Invalid schema '+secret+' https://example.org/private'}})
    result = await provider_error_diagnostic(response)
    assert result['http_status'] == 400 and result['provider_status'] == 'INVALID_ARGUMENT'
    assert result['category'] == 'schema_request_rejected'
    assert 'Invalid schema' in result['message']
    assert secret not in json.dumps(result)
