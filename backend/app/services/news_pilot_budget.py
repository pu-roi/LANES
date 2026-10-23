"""Durable reserve-before-dispatch ledger for the manually selected news pilot.

Amounts are integer nanodollars. Reservations are never refunded automatically.
Object generation preconditions protect against competing Cloud Run invocations;
an interrupted in-flight reservation blocks further dispatch pending investigation.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from urllib.parse import quote

import httpx

from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError

MODEL = 'gemini-3.5-flash-lite'
LIMIT = 1_000_000_000
PRICE = {'input_nanodollars_per_token': 300, 'output_nanodollars_per_token': 2500,
         'source': 'https://ai.google.dev/gemini-api/docs/pricing', 'checked_on': '2026-10-22'}


def new_ledger(identity: str) -> dict:
    return {'schema_version': 'news-pilot-budget-v1', 'identity': identity,
            'limit_nanodollars': LIMIT, 'model': MODEL, 'price': PRICE,
            'status': 'ready', 'attempts': []}


class GCSLedgerStore:
    """Private existing object only; never creates or resets a missing ledger."""
    def __init__(self, bucket: str, name: str, *, token: object = None) -> None:
        if bucket != 'lanes-storage' or not name.startswith('private/news-pilot/'):
            raise ResolutionError('pilot_budget_location_invalid')
        self.bucket, self.name, self.token = bucket, name, token

    def _headers(self) -> dict:
        if self.token is not None:
            token = self.token()
        else:
            import google.auth
            from google.auth.transport.requests import Request
            credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/devstorage.read_write'])
            credentials.refresh(Request())
            token = credentials.token
        return {'Authorization': 'Bearer '+token}

    def read(self) -> tuple[dict, str]:
        url = 'https://storage.googleapis.com/storage/v1/b/'+self.bucket+'/o/'+quote(self.name, safe='')
        with httpx.Client(timeout=10, follow_redirects=False, headers=self._headers()) as client:
            metadata = client.get(url)
            if metadata.status_code != 200:
                raise ResolutionError('pilot_budget_storage_unavailable')
            generation = metadata.json()['generation']
            response = client.get(url, params={'alt': 'media', 'generation': generation})
            if response.status_code != 200 or len(response.content) > 262144:
                raise ResolutionError('pilot_budget_storage_unavailable')
            return response.json(), generation

    def compare_and_swap(self, generation: str, value: dict) -> None:
        url = 'https://storage.googleapis.com/upload/storage/v1/b/'+self.bucket+'/o'
        response = httpx.post(url, params={'uploadType': 'media', 'name': self.name,
            'ifGenerationMatch': generation}, headers={**self._headers(), 'Content-Type': 'application/json'},
            content=json.dumps(value, allow_nan=False), timeout=10, follow_redirects=False)
        if response.status_code not in (200, 201):
            raise ResolutionError('pilot_budget_concurrent_or_storage_failure')


class PilotBudget:
    def __init__(self, store: object, identity: str) -> None:
        self.store, self.identity = store, identity

    def _read(self) -> tuple[dict, str]:
        state, generation = self.store.read()
        expected = new_ledger(self.identity)
        if any(state.get(key) != expected[key] for key in
               ('schema_version', 'identity', 'limit_nanodollars', 'model', 'price')):
            raise ResolutionError('pilot_budget_identity_mismatch')
        attempts = state.get('attempts')
        if not isinstance(attempts, list) or any(type(a.get('reserved_nanodollars')) != int
                or a['reserved_nanodollars'] <= 0 for a in attempts):
            raise ResolutionError('pilot_budget_state_invalid')
        if sum(a['reserved_nanodollars'] for a in attempts) > LIMIT:
            raise ResolutionError('pilot_budget_state_invalid')
        return state, generation

    def reserve(self, model: str, payload: dict, context: dict) -> str:
        if model != MODEL or set(payload) != {'systemInstruction', 'contents', 'generationConfig'}:
            raise ResolutionError('pilot_budget_request_invalid')
        config = payload['generationConfig']
        if config.get('maxOutputTokens') != 8192 or set(config) != {
                'temperature', 'maxOutputTokens', 'responseMimeType', 'responseJsonSchema'}:
            raise ResolutionError('pilot_budget_request_invalid')
        size = len(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8'))
        if size > 1_000_000:
            raise ResolutionError('pilot_budget_request_invalid')
        # A conservative text-token envelope, including JSON schema/system framing.
        reservation = (2*size+16384)*300 + 8192*2500
        key = sha({'request_sha256': sha(payload), 'context': context})
        state, generation = self._read()
        if state['status'] != 'ready' or any(a['status'] == 'in_flight' for a in state['attempts']):
            raise ResolutionError('pilot_budget_stopped_or_in_flight')
        if any(a['id'] == key for a in state['attempts']):
            raise ResolutionError('pilot_budget_attempt_already_reserved')
        if sum(a['reserved_nanodollars'] for a in state['attempts'])+reservation > LIMIT:
            raise ResolutionError('pilot_budget_exhausted')
        state = deepcopy(state)
        state['attempts'].append({'id': key, 'context': context, 'reserved_nanodollars': reservation,
            'status': 'in_flight', 'at': datetime.now(timezone.utc).isoformat()})
        self.store.compare_and_swap(generation, state)
        return key

    def finish(self, key: str, *, succeeded: bool, diagnostic: dict | None = None) -> None:
        state, generation = self._read()
        entries = [a for a in state['attempts'] if a['id'] == key]
        if len(entries) != 1 or entries[0]['status'] != 'in_flight':
            raise ResolutionError('pilot_budget_attempt_invalid')
        entries[0].update(status='completed' if succeeded else 'failed', diagnostic=diagnostic or {})
        if not succeeded:
            state['status'] = 'stopped'
        self.store.compare_and_swap(generation, state)

    def stop(self, error_code: str) -> None:
        state, generation = self._read()
        state.update(status='stopped', stop_reason=error_code)
        self.store.compare_and_swap(generation, state)
