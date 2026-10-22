"""Standalone equivalent of the frozen raw-context validator."""
from datetime import datetime
import hashlib
import json
import re

LABELS = frozenset({'ROAD', 'LANDMARK', 'LOCAL_AREA', 'CITY', 'BARANGAY', 'PROVINCE'})
IMAGE = 'sha256:a51ce2a6b0f19f382ce96bf63c265e060b37112098176c97c66c23e887794680'
MAX_CHARS = 100000
MAX_OUTPUT_BYTES = 8 * 1024 * 1024


def object_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_raw_input(value: dict) -> None:
    require(set(value) == {'record_id', 'text', 'text_sha256', 'publication', 'mentions'}, 'exact raw input required')
    require(isinstance(value['record_id'], str) and re.fullmatch(r'[A-Za-z0-9_-]{1,90}', value['record_id']) is not None, 'invalid identity')
    text = value['text']
    require(isinstance(text, str) and len(text) <= MAX_CHARS and hashlib.sha256(text.encode('utf-8')).hexdigest() == value['text_sha256'], 'source hash mismatch')
    publication = value['publication']
    if publication is not None:
        require(set(publication) == {'value', 'basis'} and bool(publication['basis']), 'invalid publication metadata')
        require(datetime.fromisoformat(publication['value']).utcoffset() is not None, 'aware publication required')
    require(isinstance(value['mentions'], list), 'mentions required')
    previous = -1
    ids: set[str] = set()
    for m in value['mentions']:
        require(set(m) == {'id', 'start', 'end', 'text', 'label', 'provenance_sha256'} and m['label'] in LABELS, 'invalid mention')
        require(type(m['start']) is int and type(m['end']) is int and previous <= m['start'] < m['end'] <= len(text) and text[m['start']:m['end']] == m['text'], 'source slice or overlap mismatch')
        require(isinstance(m['id'], str) and bool(m['id']) and m['id'] not in ids and isinstance(m['provenance_sha256'], str) and re.fullmatch('[a-f0-9]{64}', m['provenance_sha256']) is not None, 'invalid mention binding')
        ids.add(m['id'])
        previous = m['end']
