"""Bounded, source-bound IPC shared by the supervisor and isolated child."""
from __future__ import annotations

import json
from pathlib import Path

from app.services.news_ner.bundle import digest
from app.services.news_ner.contract import MAX_OUTPUT_BYTES, object_sha, require, validate_raw_input

VERSION = 'lanes-ner-subprocess-v1'
INPUT_BYTES = 1024 * 1024
COLD_SECONDS = 60
REQUEST_SECONDS = 60
CLEANUP_SECONDS = 5
SESSION_SECONDS = 450
HEADROOM_BYTES = 896 * 1024**2


def encode(value: dict, limit: int = MAX_OUTPUT_BYTES) -> bytes:
    data = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8') + b'\n'
    require(len(data) <= limit, 'message_limit')
    return data


def decode(data: bytes, limit: int = MAX_OUTPUT_BYTES) -> dict:
    require(len(data) <= limit and data.endswith(b'\n'), 'message_limit')
    def pairs(items: list) -> dict:
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate_key')
            result[key] = value
        return result
    value = json.loads(data, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))
    require(isinstance(value, dict), 'object_required')
    return value


def validate_request(value: dict) -> None:
    require(set(value) == {'record_id', 'text', 'text_sha256', 'publication'}, 'request_keys')
    validate_raw_input({**value, 'mentions': []})
    encode(value, INPUT_BYTES)


def code_bindings(root: Path) -> dict:
    files = [*sorted((root / 'news_ner').glob('*.py')), root / 'news_ner/promotion.json',
             *sorted((root / 'news_ner_runtime').glob('*.py'))]
    return {p.relative_to(root).as_posix(): digest(p) for p in files}


def verify_code(root: Path, expected: dict) -> None:
    require(bool(expected) and code_bindings(root) == expected, 'code_mismatch')


def verify_result(request: dict, result: dict, bundle_sha: str, code: dict) -> None:
    """Authenticate raw predictions and reproduce every proposal/group binding."""
    from app.services.news_ner.location_pipeline import from_neural_mentions
    require(set(result) == {'proposal', 'graph', 'measurements', 'provenance'}, 'result_keys')
    provenance = result['provenance']
    require(provenance['bundle_sha256'] == bundle_sha and provenance['code_sha256'] == object_sha(code)
            and provenance['runtime'] == VERSION, 'result_provenance')
    raw = {**request, 'mentions': result['proposal']['neural_mentions']}
    validate_raw_input(raw)
    binding = object_sha({'bundle': bundle_sha, 'tokenizer': provenance['tokenizer_sha256'], 'text': request['text_sha256']})
    require(all(m['provenance_sha256'] == binding for m in raw['mentions']), 'prediction_binding')
    expected = from_neural_mentions(raw)
    require(result['proposal'] == expected['proposal'] and result['graph'] == expected['graph'], 'graph_binding')
