"""Internal, opt-in location comparison. No model, database or provider imports."""
from __future__ import annotations

import hashlib
import re
from typing import Any, Callable

LABELS = frozenset({'ROAD', 'BARANGAY', 'CITY', 'PROVINCE', 'LANDMARK', 'LOCAL_AREA'})
TYPE_MAP = {'street': 'ROAD', 'barangay': 'BARANGAY', 'city': 'CITY',
            'province': 'PROVINCE', 'landmark': 'LANDMARK'}
MAX_CHARS = 100_000
Predictor = Callable[[str], list[dict[str, Any]]]


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def validate_input(value: dict[str, Any]) -> None:
    require(isinstance(value, dict) and set(value) == {'article_id', 'text', 'text_sha256'},
            'raw text, opaque ID and hash only')
    require(isinstance(value['article_id'], str) and
            re.fullmatch(r'[A-Za-z0-9_-]{1,80}', value['article_id']) is not None,
            'opaque article ID required')
    require(isinstance(value['text'], str) and len(value['text']) <= MAX_CHARS,
            'text must be a string of at most 100000 characters')
    require(value['text_sha256'] == text_hash(value['text']), 'source hash mismatch')


def validate_span(span: dict[str, Any], text: str) -> None:
    require(type(span['start']) is int and type(span['end']) is int and
            0 <= span['start'] < span['end'] <= len(text), 'invalid Unicode offsets')
    require(span['text'] == text[span['start']:span['end']], 'source slice mismatch')


def neural_mentions(text: str, predict: Predictor) -> list[dict[str, Any]]:
    proposed = predict(text)
    require(isinstance(proposed, list), 'prediction list required')
    result = []
    for span in proposed:
        require(isinstance(span, dict) and set(span) == {'start', 'end', 'text', 'label'},
                'exact neural mention fields required')
        validate_span(span, text)
        require(span['label'] in LABELS, 'unexpected neural label')
        result.append(dict(span))
    result.sort(key=lambda s: (s['start'], s['end'], s['label']))
    require(all(a['end'] <= b['start'] for a, b in zip(result, result[1:])),
            'overlapping neural mentions')
    return result


def rules_mentions(text: str, splitter: Callable | None = None,
                   finder: Callable | None = None) -> list[dict[str, Any]]:
    # The production rules module is loaded only during explicit comparison.
    if splitter is None or finder is None:
        from app.services.taglish_extraction_service import (
            split_sentences_with_offsets, find_place_mentions,
        )
        splitter = splitter or split_sentences_with_offsets
        finder = finder or find_place_mentions
    result = []
    previous_end = 0
    for sentence, start, end in splitter(text):
        require(type(start) is int and type(end) is int and
                previous_end <= start < end <= len(text) and text[start:end] == sentence,
                'sentence source offsets mismatch')
        previous_end = end
        candidates = finder(sentence, start)
        require(isinstance(candidates, list), 'rules candidates must be a list')
        for raw in candidates:
            require(isinstance(raw, dict) and
                    {'char_start', 'char_end', 'raw_place_name', 'place_type'} <= set(raw),
                    'incomplete rules candidate')
            item = {'start': raw['char_start'], 'end': raw['char_end'],
                    'text': raw['raw_place_name'], 'label': TYPE_MAP.get(raw['place_type']),
                    'rules_type': raw['place_type'],
                    'context': {k: v for k, v in raw.items() if k not in
                                {'char_start', 'char_end', 'raw_place_name', 'place_type'}},
                    'overlaps_other_rules_candidate': False}
            validate_span(item, text)
            require(start <= item['start'] < item['end'] <= end,
                    'rules mention escapes sentence')
            result.append(item)
    result.sort(key=lambda s: (s['start'], s['end'], s['rules_type']))
    for i, left in enumerate(result):
        for right in result[i + 1:]:
            if right['start'] >= left['end']:
                break
            left['overlaps_other_rules_candidate'] = True
            right['overlaps_other_rules_candidate'] = True
    return result


def compare_mentions(neural: list[dict], rules: list[dict]) -> dict[str, Any]:
    """One-to-one exact/type pairs; remaining overlap links are diagnostic only."""
    available_n, available_r = set(range(len(neural))), set(range(len(rules)))
    exact, types = [], []
    for same_type, target in ((True, exact), (False, types)):
        for i in sorted(available_n):
            n = neural[i]
            candidates = [j for j in sorted(available_r) if
                          (n['start'], n['end']) == (rules[j]['start'], rules[j]['end']) and
                          (n['label'] == rules[j]['label']) is same_type]
            if candidates:
                j = candidates[0]
                target.append([i, j]); available_n.remove(i); available_r.remove(j)
    boundaries = [[i, j] for i in sorted(available_n) for j in sorted(available_r)
                  if max(neural[i]['start'], rules[j]['start']) <
                  min(neural[i]['end'], rules[j]['end'])]
    return {'exact_pairs': exact, 'same_span_type_pairs': types,
            'boundary_links': boundaries,
            'unmatched_neural': sorted(available_n), 'unmatched_rules': sorted(available_r)}


def compare_article(value: dict[str, Any], predictor: Predictor, *,
                    provenance: dict[str, str], splitter: Callable | None = None,
                    finder: Callable | None = None) -> dict[str, Any]:
    validate_input(value)
    require(set(provenance) == {'model', 'tokenizer', 'rules'} and
            all(isinstance(v, str) and re.fullmatch('[a-f0-9]{64}', v) for v in provenance.values()),
            'hash-bound model/tokenizer/rules provenance required')
    outputs = {}
    for name, operation in (
        ('neural', lambda: neural_mentions(value['text'], predictor)),
        ('rules', lambda: rules_mentions(value['text'], splitter, finder)),
    ):
        try:
            outputs[name] = {'status': 'completed', 'mentions': operation()}
        except Exception as exc:
            # Explicit errors; neither result substitutes for the failed method.
            outputs[name] = {'status': 'failed', 'error_type': type(exc).__name__,
                             'reason': str(exc)[:200]}
    completed = all(v['status'] == 'completed' for v in outputs.values())
    return {'schema': 'lanes-ner-shadow-article-v1', 'article_id': value['article_id'],
            'text_sha256': value['text_sha256'], 'provenance': dict(provenance),
            **outputs, 'status': 'completed' if completed else 'failed',
            'comparison': compare_mentions(outputs['neural']['mentions'], outputs['rules']['mentions'])
            if completed else None, 'application_connected': False}
