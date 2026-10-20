"""Scoring-only tests. Never calls a recognizer, context extractor or database."""
from copy import deepcopy
import json
import sys
from pathlib import Path
import pytest

from training.flood_ner.location_scoring_v45 import (METHODS, canonical_spans, location_result,
    author_repaired_expectations, repaired_result, original_integrity, text_sha)
from training.flood_ner.location_repair_cases_v44 import location_cases
from training.flood_ner.context_cases_v42 import core_cases
from training.flood_ner.location_reanalysis_v45 import checked, forbid_extraction, NoNeuralDatabase


def fake_repair(case, method):
    raw = case['raw']
    expected = case['expected_mentions'] if method in (case['family'], 'combined') else [
        (m['start'], m['end'], m['label']) for m in raw['mentions']]
    effective = [{'id': f'e{i}', 'start': a, 'end': b, 'label': label, 'text': raw['text'][a:b],
                  'provenance_sha256': 'c'*64} for i, (a, b, label) in enumerate(expected)]
    row = {'record_id': raw['record_id'], 'raw': deepcopy(raw), 'control_mentions': deepcopy(raw['mentions'])}
    repair = {'record_id': raw['record_id'], 'text_sha256': raw['text_sha256'], 'method': method,
              'neural_mentions': deepcopy(raw['mentions']), 'control_mentions': deepcopy(raw['mentions']), 'effective_mentions': effective}
    return row, repair


@pytest.mark.parametrize('case', location_cases(), ids=lambda c: c['case_id'])
@pytest.mark.parametrize('method', METHODS)
def test_all_36_cases_four_methods_before_and_after_json(case, method):
    row, repair = fake_repair(case, method)
    before = location_result(case, row, repair, conditional=True)
    case, row, repair = json.loads(json.dumps([case, row, repair], ensure_ascii=False))
    after = location_result(case, row, repair, conditional=True)
    assert before == after and after['passed']


@pytest.mark.parametrize('spans', [None, True, '0,1,ROAD', [(0, 1)], [(0, 1, 'ROAD', 'extra')],
    [(True, 1, 'ROAD')], [(0, 1.0, 'ROAD')], [(-1, 1, 'ROAD')], [(0, 0, 'ROAD')],
    [(0, 4, 'ROAD')], [(0, 1, 'road')], [(0, 1, ['ROAD'])], [(0, 1, 'ROAD'), (0, 1, 'ROAD')],
    [(0, 2, 'ROAD'), (1, 3, 'CITY')]])
def test_malformed_or_duplicate_spans_are_not_forgiven(spans):
    with pytest.raises(ValueError): canonical_spans(spans, text='ABC')


def test_wrong_valid_label_is_a_semantic_failure():
    case = location_cases()[0]; row, repair = fake_repair(case, 'combined')
    repair['effective_mentions'][0]['label'] = 'LANDMARK'
    assert not location_result(case, row, repair, conditional=True)['passed']


def test_changed_neural_mentions_never_become_repaired_preservation():
    case = location_cases()[0]; row, repair = fake_repair(case, 'combined')
    assert original_integrity(row, repair)
    repair['neural_mentions'] = deepcopy(repair['effective_mentions'])
    assert not original_integrity(row, repair)


def test_stale_body_identity_and_slice_rejected():
    case = location_cases()[0]; row, repair = fake_repair(case, 'combined')
    repair['text_sha256'] = 'a'*64
    with pytest.raises(ValueError): original_integrity(row, repair)
    row, repair = fake_repair(case, 'combined'); repair['record_id'] = 'wrong'
    with pytest.raises(ValueError): original_integrity(row, repair)
    row, repair = fake_repair(case, 'combined'); repair['effective_mentions'][0]['text'] = 'wrong'
    with pytest.raises(ValueError): original_integrity(row, repair)


def fixture_graphs(oracle):
    case = next(c for c in core_cases() if c['case_id'] == oracle['case_id']); raw = case['raw']
    mentions = [{'id': f't{i}', **s, 'provenance_sha256': 'c'*64} for i, s in enumerate(oracle['target_spans'])]
    expr = [{'id': f'x{i}', **s} for i, s in enumerate(oracle['depth_spans'])]
    facts = [{'id': f'f{i}', 'kind': 'depth', 'value': s['text'], 'temporal_role': None, 'depth_scope': 'point',
              'entity_ids': [f'x{i}'], 'qualifiers': [], 'evidence': [{'start': 0, 'end': len(raw['text']), 'text': raw['text']}]} for i, s in enumerate(oracle['depth_spans'])]
    control = {'mentions': deepcopy(raw['mentions']), 'expressions': deepcopy(expr), 'facts': deepcopy(facts),
               'relations': [], 'absolute_instants': [], 'numeric_depths': []}
    graph = {**deepcopy(control), 'mentions': mentions, 'relations': [
        {'fact_id': f['id'], 'target_entity_ids': [m['id'] for m in mentions], 'scope': 'collective'} for f in facts]}
    row = {'record_id': raw['record_id'], 'raw': raw, 'control_mentions': raw['mentions']}
    repair = {'record_id': raw['record_id'], 'text_sha256': raw['text_sha256'], 'method': 'combined',
              'neural_mentions': raw['mentions'], 'control_mentions': raw['mentions'], 'effective_mentions': mentions}
    return row, repair, control, graph


@pytest.mark.parametrize('oracle', author_repaired_expectations(core_cases()), ids=lambda o: o['case_id'])
def test_three_source_authored_repaired_expectations(oracle):
    before = deepcopy(oracle); values = fixture_graphs(oracle)
    assert repaired_result(oracle, *values)['passed']
    assert repaired_result(json.loads(json.dumps(oracle)), *json.loads(json.dumps(values)))['passed']
    assert oracle == before


@pytest.mark.parametrize('mutation', ('scope', 'target', 'measurement', 'qualifier', 'onset', 'neural'))
def test_repaired_view_still_rejects_semantic_losses(mutation):
    oracle = author_repaired_expectations(core_cases())[0]; row, repair, control, graph = fixture_graphs(oracle)
    if mutation == 'scope': graph['relations'][0]['scope'] = 'shared'
    elif mutation == 'target': graph['relations'][0]['target_entity_ids'].pop()
    elif mutation == 'measurement': graph['facts'][0]['value'] = '9 inches'
    elif mutation == 'qualifier': control['facts'][0]['qualifiers'] = ['about']
    elif mutation == 'onset': graph['facts'][0]['temporal_role'] = 'onset'
    else: repair['neural_mentions'] = graph['mentions']
    assert not repaired_result(oracle, row, repair, control, graph)['passed']


def test_expectation_author_does_not_accept_candidate_outputs():
    cases = core_cases(); before = deepcopy(cases)
    authored = author_repaired_expectations(cases)
    assert cases == before and len(authored) == 3
    assert all(o['basis'] == 'source_and_approved_complete_junction_contract' for o in authored)


@pytest.mark.parametrize('oracle', author_repaired_expectations(core_cases()), ids=lambda o: o['case_id'])
def test_original_expectations_still_require_original_view(oracle):
    from training.flood_ner.location_reassessment_v45 import original_case
    case = next(c for c in core_cases() if c['case_id'] == oracle['case_id'])
    row, repair, control, graph = fixture_graphs(oracle)
    assert original_case(case, row, 'v42', control)['passed']
    assert not original_case(case, row, 'v42', graph)['passed']
    assert repaired_result(oracle, row, repair, control, graph)['passed']
    assert oracle['original_expectation_unchanged']


def test_stale_hash_and_unsafe_path_binding(tmp_path):
    f = tmp_path/'safe'; f.write_text('safe')
    with pytest.raises(ValueError): checked({'path': 'safe', 'sha256': 'a'*64}, tmp_path)
    with pytest.raises(ValueError): checked({'path': 'missing', 'sha256': 'a'*64}, tmp_path)
    for name in ('../safe', '/safe', 'C:/safe', '..\\safe'):
        with pytest.raises(ValueError): checked({'path': name, 'sha256': text_sha('safe')}, tmp_path)


def test_no_extraction_guard_prevents_even_a_stub_call():
    def extract(): raise AssertionError('must never reach function body')
    prior = sys.getprofile(); sys.setprofile(forbid_extraction)
    try:
        with pytest.raises(RuntimeError, match='extraction'): extract()
    finally: sys.setprofile(prior)
    for name in ('spacy', 'torch', 'sqlalchemy', 'psycopg'):
        with pytest.raises(RuntimeError): NoNeuralDatabase().find_spec(name)
