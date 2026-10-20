"""Strict saved-output scoring helpers. No extraction or recognition is executed."""
from __future__ import annotations

from collections import Counter
import hashlib
import json

METHODS = ('missing_junction', 'boundary_replacement', 'junction_type', 'combined')
LABELS = frozenset({'ROAD', 'LANDMARK', 'LOCAL_AREA', 'BARANGAY', 'CITY', 'PROVINCE'})
REPAIRED = {'fictional-v42-10': 'missing_junction', 'fictional-v42-22': 'junction_type',
            'fictional-v42-34': 'boundary_replacement'}


def text_sha(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def canonical_spans(spans: list | tuple, *, text: str | None = None, labels: frozenset = LABELS) -> tuple:
    """Normalize representation only; duplicates, types and semantics stay strict."""
    if not isinstance(spans, (list, tuple)):
        raise ValueError('span collection must be a list or tuple')
    result = []
    for span in spans:
        if not isinstance(span, (list, tuple)) or len(span) != 3:
            raise ValueError('exact start/end/label triples required')
        a, b, label = span
        if type(a) is not int or type(b) is not int or not 0 <= a < b or (text is not None and b > len(text)):
            raise ValueError('invalid integer source offsets')
        if type(label) is not str or label not in labels:
            raise ValueError('invalid label')
        result.append((a, b, label))
    if len(result) != len(set(result)):
        raise ValueError('duplicate span')
    result.sort()
    if any(a[1] > b[0] for a, b in zip(result, result[1:])):
        raise ValueError('overlapping spans')
    return tuple(result)


def mention_spans(mentions: list, text: str) -> tuple:
    ids = []
    for m in mentions:
        if not isinstance(m, dict) or not isinstance(m.get('id'), str) or not m['id']:
            raise ValueError('mention identity required')
        a, b = m.get('start'), m.get('end')
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(text) or text[a:b] != m.get('text'):
            raise ValueError('stale source slice')
        ids.append(m['id'])
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate mention identity')
    return canonical_spans([(m['start'], m['end'], m['label']) for m in mentions], text=text)


def original_integrity(row: dict, repair: dict) -> bool:
    raw = row['raw']; text = raw['text']
    if text_sha(text) != raw['text_sha256'] or repair['text_sha256'] != raw['text_sha256']:
        raise ValueError('stale body binding')
    if row['record_id'] != raw['record_id'] or repair['record_id'] != row['record_id']:
        raise ValueError('stale record identity')
    mention_spans(raw['mentions'], text); mention_spans(row['control_mentions'], text)
    mention_spans(repair['effective_mentions'], text)
    return repair['neural_mentions'] == raw['mentions'] and repair['control_mentions'] == row['control_mentions']


def location_result(case: dict, row: dict, repair: dict, *, conditional: bool) -> dict:
    expected = case['expected_mentions']
    if conditional and repair['method'] not in (case['family'], 'combined'):
        expected = [(m['start'], m['end'], m['label']) for m in row['control_mentions']]
    wanted = canonical_spans(expected, text=row['raw']['text'])
    actual = mention_spans(repair['effective_mentions'], row['raw']['text'])
    return {'case_id': case['case_id'], 'passed': wanted == actual and original_integrity(row, repair),
            'expected': wanted, 'actual': actual}


def author_repaired_expectations(cases: list[dict]) -> list[dict]:
    """Source-author three new oracles; no candidate-output argument or lookup."""
    by_id = {c['case_id']: c for c in cases}
    authored = []
    for identity, family in REPAIRED.items():
        c = by_id[identity]; raw = c['raw']; text = raw['text']
        phrases = ('Daan Piña', 'Daan Áster') if c['language'] == 'tagalog' else ('Piña Street', 'Áster Road')
        measurements = ('8 pulgada', 'abot-sakong') if c['language'] == 'tagalog' else ('8 inches', 'gutter deep')
        targets = []
        for phrase in phrases:
            assert text.count(phrase) == 1
            a = text.index(phrase); targets.append({'start': a, 'end': a+len(phrase), 'text': phrase, 'label': 'ROAD'})
        depths = []
        for phrase in measurements:
            assert text.count(phrase) == 1
            a = text.index(phrase); depths.append({'start': a, 'end': a+len(phrase), 'text': phrase, 'label': 'DEPTH'})
        assert c['family'] == 'incomplete_targets' and raw['text_sha256'] == text_sha(text)
        authored.append({'case_id': identity, 'family_enabled': family, 'language': c['language'],
                         'text_sha256': raw['text_sha256'], 'target_spans': targets, 'depth_spans': depths,
                         'scope': 'collective', 'basis': 'source_and_approved_complete_junction_contract',
                         'original_expectation_unchanged': True})
    return authored


def protected_facts(graph: dict) -> Counter:
    expressions = {e['id']: e for e in graph['expressions']}
    return Counter((f['kind'], f['value'], f['temporal_role'], f['depth_scope'], tuple(f['qualifiers']),
                    tuple((expressions[i]['start'], expressions[i]['end'], expressions[i]['label']) for i in f['entity_ids']))
                   for f in graph['facts'])


def repaired_result(oracle: dict, row: dict, repair: dict, control: dict, graph: dict) -> dict:
    text = row['raw']['text']
    if oracle['text_sha256'] != text_sha(text):
        raise ValueError('stale repaired-view oracle')
    for s in oracle['target_spans']+oracle['depth_spans']:
        if text[s['start']:s['end']] != s['text']:
            raise ValueError('stale authored source slice')
    expected = canonical_spans([(s['start'], s['end'], s['label']) for s in oracle['target_spans']], text=text)
    actual = mention_spans(graph['mentions'], text)
    failures = []
    if actual != expected: failures.append('incomplete_or_incorrect_targets')
    if not original_integrity(row, repair): failures.append('original_mentions_changed')
    if graph['mentions'] != repair['effective_mentions']: failures.append('effective_view_mismatch')
    if graph['absolute_instants'] or graph['numeric_depths']: failures.append('invented_instant_or_conversion')
    if protected_facts(graph) != protected_facts(control): failures.append('fact_qualifier_or_time_role_change')
    if graph['expressions'] != control['expressions']: failures.append('expression_change')
    expr = {e['id']: e for e in graph['expressions']}; rel = {r['fact_id']: r for r in graph['relations']}
    target_by_id = {m['id']: m for m in graph['mentions']}
    depths = [f for f in graph['facts'] if f['kind'] == 'depth']
    if len(depths) != len(oracle['depth_spans']): failures.append('depth_count')
    observed_depths = []
    for f in depths:
        r = rel.get(f['id']); entities = [expr[i] for i in f['entity_ids']]
        observed_depths.extend((e['start'], e['end'], e['label']) for e in entities)
        if len(entities) != 1 or f['value'] != entities[0]['text']: failures.append('measurement_value')
        targets = [] if r is None else [(target_by_id[i]['start'], target_by_id[i]['end'], target_by_id[i]['label']) for i in r['target_entity_ids']]
        if canonical_spans(targets, text=text) != expected or r is None or r['scope'] != oracle['scope']:
            failures.append('depth_attachment_or_scope')
        if any(text[e['start']:e['end']] != e['text'] for e in f['evidence']): failures.append('evidence_slice')
    desired_depths = [(s['start'], s['end'], s['label']) for s in oracle['depth_spans']]
    if sorted(observed_depths) != sorted(desired_depths): failures.append('measurement_spans')
    return {'case_id': oracle['case_id'], 'passed': not failures, 'failures': failures,
            'view': 'repaired_effective', 'family_enabled': oracle['family_enabled']}
