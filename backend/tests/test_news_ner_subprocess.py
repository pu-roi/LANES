"""Constructed checks: no model loading, corpus, cloud or database fixtures."""
import asyncio
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.news_ner_runtime.protocol import decode, encode, validate_request, verify_result
from app.services.news_ner_runtime.supervisor import RuntimeFailure, Session
from app.services.news_ner.contract import object_sha
from app.services.news_ner.location_pipeline import from_neural_mentions
from app.services.news_ner.bundle import verify_bundle


def request(text='🚦 Baha sa Calle Niño sa Manila.'):
    return {'record_id': 'fictional', 'text': text, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'publication': None}


@pytest.mark.parametrize('text', ['', '🚦 Niño\r\nBaha', 'x' * 100000], ids=['empty', 'unicode', 'maximum'])
def test_exact_unicode_roundtrip(text):
    value = request(text)
    validate_request(value)
    assert decode(encode(value)) == value


@pytest.mark.parametrize('mutation', ['hash', 'size', 'keys', 'publication'])
def test_invalid_input(mutation):
    value = request()
    if mutation == 'hash': value['text_sha256'] = '0' * 64
    if mutation == 'size': value = request('x' * 100001)
    if mutation == 'keys': value['secret'] = 'not_allowed'
    if mutation == 'publication': value['publication'] = {'value': '2026-10-20T00:00:00', 'basis': 'feed'}
    with pytest.raises(ValueError): validate_request(value)


@pytest.mark.parametrize('payload', [b'[]\n', b'{"x":1,"x":2}\n', b'{"x":NaN}\n', b'{}', b'bad\n', b'x' * 50])
def test_bad_messages(payload):
    with pytest.raises((ValueError, UnicodeError)): decode(payload, 40)


def test_output_bound():
    with pytest.raises(ValueError): encode({'x': 'x' * 50}, 40)


def test_missing_corrupt_assets(tmp_path):
    with pytest.raises((OSError, ValueError)): verify_bundle(tmp_path, '0' * 64)
    (tmp_path / 'manifest.json').write_text('{}')
    with pytest.raises(ValueError): verify_bundle(tmp_path, '0' * 64)


def test_supervisor_recomputes_unicode_graph():
    req = request()
    tokenizer = 'a' * 64
    binding = object_sha({'bundle': 'b', 'tokenizer': tokenizer, 'text': req['text_sha256']})
    start = req['text'].index('Calle')
    mention = {'id': 'n0', 'start': start, 'end': start + len('Calle Niño'), 'text': 'Calle Niño', 'label': 'ROAD', 'provenance_sha256': binding}
    result = {**from_neural_mentions({**req, 'mentions': [mention]}), 'measurements': {}, 'provenance': {
        'runtime': 'lanes-ner-subprocess-v1', 'bundle_sha256': 'b', 'code_sha256': object_sha({}), 'tokenizer_sha256': tokenizer}}
    verify_result(req, result, 'b', {})
    result['graph']['unassigned'].append({'invented': True})
    with pytest.raises(ValueError): verify_result(req, result, 'b', {})


def test_misbound_occurrence():
    req = request('Niño Niño')
    with pytest.raises(ValueError):
        from_neural_mentions({**req, 'mentions': [{'id': 'n0', 'start': 1, 'end': 5, 'text': 'Niño', 'label': 'ROAD', 'provenance_sha256': 'a'*64}]})


def test_state_concurrency_and_budget():
    async def check():
        session = Session('b', {})
        with pytest.raises(RuntimeFailure, match='not_ready'): await session.request(request())
        session.busy = True
        with pytest.raises(RuntimeFailure, match='concurrent_request'): await session.request(request())
        session.busy = False; session.state = 'ready'; session.started -= 450
        with pytest.raises(RuntimeFailure, match='session_budget'): await session.request(request())
    asyncio.run(check())


def test_deadline_classification():
    async def check():
        class Input:
            def write(self, data): pass
            async def drain(self): await asyncio.sleep(1)
        class Process:
            stdin = Input()
            stdout = object()
        session = Session('b', {}); session.proc = Process()
        with pytest.raises(RuntimeFailure, match='deadline'): await session._exchange({}, .001)
    asyncio.run(check())
