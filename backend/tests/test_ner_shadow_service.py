"""Fictional location-only fixtures, with references absent from the adapter."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services import ner_shadow_service as s

PROVENANCE = dict(model='a' * 64, tokenizer='b' * 64, rules='c' * 64)


def value(text):
    return {'article_id': 'fictional-01', 'text': text, 'text_sha256': s.text_hash(text)}


def span(text, name, label, occurrence=0):
    start = [i for i in range(len(text)) if text.startswith(name, i)][occurrence]
    return {'start': start, 'end': start + len(name), 'text': name, 'label': label}


def split(text):
    return [(text, 0, len(text))] if text else []


def raw(item, kind='street', **context):
    return {'char_start': item['start'], 'char_end': item['end'],
            'raw_place_name': item['text'], 'place_type': kind, **context}


@pytest.mark.parametrize('label,kind', [(v, k) for k, v in s.TYPE_MAP.items()])
def test_mapping_and_original_unicode_offsets(label, kind):
    text = '  🌧 Piña Road. Piña Road.\n'
    mentions = [span(text, 'Piña Road', label, i) for i in range(2)]
    result = s.compare_article(value(text), lambda _: mentions, provenance=PROVENANCE,
        splitter=split, finder=lambda sentence, offset: [raw(m, kind) for m in mentions])
    assert result['comparison']['exact_pairs'] == [[0, 0], [1, 1]]
    assert result['neural']['mentions'] == mentions
    assert result['status'] == 'completed'


def test_rules_unknown_context_and_overlaps_are_preserved():
    text = 'Piña Road in Sample District'
    n = span(text, 'Sample District', 'LOCAL_AREA')
    candidates = [raw(span(text, 'Piña Road', 'ROAD'), local_area_raw='Sample District'),
                  raw(span(text, 'Piña', 'LANDMARK'), 'landmark'), raw(n, 'unknown')]
    before = deepcopy(candidates)
    result = s.compare_article(value(text), lambda _: [n], provenance=PROVENANCE,
                               splitter=split, finder=lambda *_: candidates)
    rules = result['rules']['mentions']
    assert rules[0]['overlaps_other_rules_candidate'] and rules[1]['overlaps_other_rules_candidate']
    assert rules[2]['label'] is None and rules[2]['rules_type'] == 'unknown'
    assert any(r['context'].get('local_area_raw') == 'Sample District' for r in rules)
    assert result['neural']['mentions'][0]['label'] == 'LOCAL_AREA'
    assert candidates == before


@pytest.mark.parametrize('text', ['', '  \n', 'No named locations.', 'x' * 100000],
                         ids=['empty', 'whitespace', 'negative', 'max-length'])
def test_empty_results_and_maximum_input(text):
    result = s.compare_article(value(text), lambda _: [], provenance=PROVENANCE, splitter=split, finder=lambda *_: [])
    assert result['status'] == 'completed' and result['comparison']['exact_pairs'] == []


@pytest.mark.parametrize('damage', ['oversize', 'type', 'hash', 'references', 'predictions', 'url', 'id'])
def test_rejects_invalid_input_before_predicting(damage):
    v = value('Sample City')
    if damage == 'oversize': v = value('x' * 100001)
    elif damage == 'type': v['text'] = 2
    elif damage == 'hash': v['text_sha256'] = '0' * 64
    elif damage == 'id': v['article_id'] = 'https://example.invalid/article'
    else: v[damage] = []
    with pytest.raises(ValueError):
        s.compare_article(v, lambda _: pytest.fail('predictor called'), provenance=PROVENANCE)


@pytest.mark.parametrize('damage', ['slice', 'offset', 'bool', 'label', 'overlap', 'fields', 'missing'])
def test_invalid_neural_results_fail_without_rules_fallback(damage):
    text = 'Sample Road'; entity = span(text, text, 'ROAD'); predictions = [entity]
    if damage == 'slice': entity['text'] = 'changed'
    elif damage == 'offset': entity['start'] = -1
    elif damage == 'bool': entity['start'] = False
    elif damage == 'label': entity['label'] = 'PERSON'
    elif damage == 'overlap': predictions.append(dict(entity))
    elif damage == 'fields': entity['confidence'] = .9
    elif damage == 'missing': predictions = None
    result = s.compare_article(value(text), lambda _: predictions, provenance=PROVENANCE,
                               splitter=split, finder=lambda *_: [])
    assert result['status'] == 'failed' and result['neural']['status'] == 'failed'
    assert result['rules']['status'] == 'completed' and result['comparison'] is None


@pytest.mark.parametrize('failure', ['sentence', 'slice', 'outside', 'exception'])
def test_rules_failure_is_explicit_and_preserves_neural_result(failure):
    text = 'Sample Road'; entity = span(text, text, 'ROAD')
    candidate = raw(entity); splitter = split
    if failure == 'sentence': splitter = lambda _: [(text, 1, len(text))]
    if failure == 'slice': candidate['raw_place_name'] = 'invented'
    if failure == 'outside': candidate['char_end'] = len(text) + 1
    def finder(*_):
        if failure == 'exception': raise RuntimeError('fixture')
        return [candidate]
    result = s.compare_article(value(text), lambda _: [entity], provenance=PROVENANCE, splitter=splitter, finder=finder)
    assert result['neural']['status'] == 'completed' and result['rules']['status'] == 'failed'
    assert result['comparison'] is None


def test_comparison_pair_accounting_does_not_score_truth():
    text = 'Alpha Road Beta City Gamma'
    neural = [span(text, 'Alpha Road', 'ROAD'), span(text, 'Beta City', 'CITY'), span(text, 'Gamma', 'LOCAL_AREA')]
    rules = [dict(span(text, 'Alpha Road', 'ROAD')), dict(span(text, 'Beta City', 'BARANGAY')),
             dict(span(text, 'Gamm', 'LANDMARK'))]
    result = s.compare_mentions(neural, rules)
    assert result == {'exact_pairs': [[0, 0]], 'same_span_type_pairs': [[1, 1]],
                      'boundary_links': [[2, 2]], 'unmatched_neural': [2], 'unmatched_rules': [2]}
    assert result == s.compare_mentions(deepcopy(neural), deepcopy(rules))


def test_duplicate_rules_candidates_cannot_double_count_exact_pairs():
    mention = span('Sample City', 'Sample City', 'CITY')
    result = s.compare_mentions([mention], [mention, mention])
    assert result['exact_pairs'] == [[0, 0]] and result['unmatched_rules'] == [1]


def test_import_is_inert():
    backend = Path(__file__).resolve().parents[1]
    code = "import sys;sys.path.insert(0," + repr(str(backend)) + ");from app.services import ner_shadow_service;assert not any(n in sys.modules for n in ['spacy','sqlalchemy','app.core.database','app.services.taglish_extraction_service'])"
    result = subprocess.run([sys.executable, '-I', '-B', '-c', code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_real_rules_offsets_on_fictional_repeated_and_whitespace_text():
    text = '  Baha sa Sample Road.\n Sample Road remains open. 🌧\n'
    result = s.compare_article(value(text), lambda _: [], provenance=PROVENANCE)
    assert result['rules']['status'] == 'completed'
    for mention in result['rules']['mentions']:
        assert text[mention['start']:mention['end']] == mention['text']


def test_no_production_registration():
    backend = Path(__file__).resolve().parents[1]
    occurrences = []
    for source in (backend / 'app').rglob('*.py'):
        if source.name != 'ner_shadow_service.py' and 'ner_shadow_service' in source.read_text(encoding='utf-8'):
            occurrences.append(source)
    assert occurrences == []
