"""Fictional text and mocked resources only; no neural or private-corpus execution."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from training.flood_ner import context_safeguards as r
from training.flood_ner import context_safeguard_study as s
from training.flood_ner.context_safeguard_cases import core_cases, build_case


@pytest.mark.parametrize('case', core_cases(), ids=lambda c: c['case_id'])
def test_core_contract(case):
    before = deepcopy(case['prediction'])
    result = r.propose('opaque', case['text'], before)
    assert [{'action': d['action'], 'label': d['proposed_label'], 'abstained': d['abstained']}
            for d in result['decisions']] == case['expected_decisions']
    assert before == case['prediction']
    assert {(a, b) for a, b, _ in result['shadow']} <= {(a, b) for a, b, _ in before}
    assert r.propose('opaque', case['text'], result['shadow'])['shadow'] == result['shadow']
    for decision in result['decisions']:
        for proof in decision['evidence']:
            assert case['text'][proof['start']:proof['end']] == proof['text']


def test_complete_fixture_matrix_and_unscored_ambiguity():
    assert len(s.fixture_checks(core_cases())) == 48
    assert sum(c['expected_entities'] is None for c in core_cases()) == 12
    modified = deepcopy(core_cases()); modified[0]['text'] += '!'
    with pytest.raises(ValueError): s.fixture_checks(modified)


def marked(text):
    case = build_case('extra', 'english', 'supported', text)
    return r.propose('opaque', case['text'], case['prediction'])


def test_conflict_keeps_original_and_explains_both_cues():
    result = marked('Flooding at [[CITY>ABSTAIN:Barangay Aster Hall]].')
    d = result['decisions'][0]
    assert d['abstained'] and d['action'] == 'keep'
    assert set(d['rule_ids']) == {'explicit_barangay', 'named_asset'}
    assert {p['target'] for p in d['rule_evidence']} == {'BARANGAY', 'LANDMARK'}


@pytest.mark.parametrize('tail', [' and 2 families.', '\n and 2 families.', ' and 2 Children.'])
def test_ordinary_counts_are_not_added_or_retagged(tail):
    text = 'Purok 4' + tail
    n = text.index('2')
    result = r.propose('opaque', text, [[n, n + 1, 'CITY']])
    assert result['shadow'] == [[n, n + 1, 'CITY']]
    assert r.propose('opaque', text, [])['shadow'] == []


def test_list_scope_does_not_cross_line_or_resize_multiword_mentions():
    result = marked('Purok 4,\n[[CITY>KEEP:7]] was listed; Barangays Aster and [[CITY>KEEP:Upper Bay]].')
    assert [d['action'] for d in result['decisions']] == ['keep', 'keep']
    result = marked('Purok\n4 and [[CITY>KEEP:7]] were ordinary table counts.')
    assert result['decisions'][0]['action'] == 'keep'


def test_overlong_shared_list_abstains_instead_of_truncating():
    text = 'Purok 1, ' + ', '.join(str(i) for i in range(2, 16))
    p = text.index('2')
    result = r.propose('opaque', text, [[p, p + 1, 'CITY']])
    assert result['decisions'][0]['abstained']


def test_directional_boundaries_are_never_repaired():
    text = 'Peña Road northbound flooded.'
    original = [[0, 20, 'CITY']]
    assert r.propose('opaque', text, original)['shadow'] == original


@pytest.mark.parametrize('bad', [None, [[0, 99, 'CITY']], [[True, 3, 'CITY']],
    [[0, 3, 'ORG']], [[0, 3, 'CITY'], [0, 3, 'CITY']], [[0, 4, 'CITY'], [3, 5, 'ROAD']]])
def test_invalid_spans_rejected(bad):
    with pytest.raises(ValueError): r.propose('opaque', 'Aster Road', bad)


@pytest.mark.parametrize('field', ['reference', 'entities', 'source_id', 'language', 'expected_label'])
def test_decision_function_cannot_receive_references_or_source_metadata(field):
    row = {'record_id': 'opaque', 'text': 'Aster Road', 'prediction': []}
    with pytest.raises(ValueError): r.raw_record({**row, field: []})


def test_unknown_rule_and_empty_identity_rejected():
    with pytest.raises(ValueError): r.propose('opaque', 'Text.', [], enabled={'secret'})
    with pytest.raises(ValueError): r.propose('', 'Text.', [])


@pytest.mark.parametrize('fp,fn,changed,status', [(0, 0, 1, 'feasible'), (0, 0, 0, 'partially_supported'),
    (1, 0, 1, 'unsupported'), (0, 1, 1, 'unsupported')])
def test_qualification_requires_observed_actions_without_introduced_errors(fp, fn, changed, status):
    result = s.qualify({'introduced_FP': fp, 'introduced_FN': fn, 'changed_spans': changed})
    assert result['disposition'] == status
    assert result['qualifies_for_later_proposal'] == (status == 'feasible')


def synthetic_records():
    records, metadata, guesses = [], [], []
    for i in range(345):
        rid = 'fictional-' + str(i); text = 'Aster Road flooded.'
        sha = hashlib.sha256(text.encode()).hexdigest(); lang = 'english' if i < 170 else 'taglish'
        row = {'record_id': rid, 'annotation_profile': 'location-only-v1', 'passage_language': lang,
            'text': text, 'text_sha256': sha, 'passage_start': 0, 'passage_end': len(text),
            'entities': [{'id': 'e1', 'start': 0, 'end': 10, 'text': 'Aster Road', 'label': 'ROAD'}],
            'complete': True, 'split': 'train', 'review_status': 'accepted', 'quality': 'silver',
            'annotation_revision': 'fixture', 'source': {'source_id': rid, 'url': 'https://example.org/fictional',
            'publisher': 'fictional', 'origin': 'captured_original', 'text': text, 'text_sha256': sha,
            'capture_version': 'fixture', 'article_group': rid, 'reuse_terms': 'constructed only', 'extraction_method': 'fixture'}}
        records.append(row)
        metadata.append({'record_id': rid, 'partition': 'train', 'language': lang, 'passage_sha256': sha})
        guesses.append({'record_id': rid, 'seed': 0, 'partition': 'train', 'language': lang,
            'text_sha256': sha, 'reference': [[0, 10, 'ROAD']], 'prediction': [[0, 10, 'CITY']]})
    return records, metadata, guesses


def test_deterministic_training_projection_ignores_nontraining_payloads():
    rows, metadata, guesses = synthetic_records()
    inputs = deepcopy((rows, metadata, guesses))
    raw, refs, selected = s.stage_training(rows + [{'split': 'dev', 'poison': object()}], metadata,
        guesses + [{'partition': 'dev', 'poison': object()}, {'partition': 'train', 'seed': 1}])
    assert len(raw) == len(refs) == len(selected) == 345
    assert all(set(x) == {'record_id', 'text', 'prediction'} for x in raw)
    assert all(x['record_id'].startswith('train-') for x in raw)
    assert s.stage_training(rows, metadata, guesses)[:2] == (raw, refs)
    assert (rows, metadata, guesses) == inputs
    s.validate_view(raw, refs)


@pytest.mark.parametrize('damage', ['missing', 'duplicate', 'metadata', 'incomplete', 'absent_entities',
    'wrong_text', 'wrong_reference', 'wrong_language', 'missing_prediction'])
def test_projection_rejects_incomplete_or_mismatched_training(damage):
    rows, metadata, guesses = synthetic_records()
    if damage == 'missing': rows.pop()
    if damage == 'duplicate': rows.append(deepcopy(rows[0]))
    if damage == 'metadata': metadata.append(deepcopy(metadata[0]))
    if damage == 'incomplete': rows[0]['complete'] = False
    if damage == 'absent_entities': del rows[0]['entities']
    if damage == 'wrong_text': rows[0]['text'] += '!'
    if damage == 'wrong_reference': guesses[0]['reference'] = []
    if damage == 'wrong_language': guesses[0]['language'] = 'taglish'
    if damage == 'missing_prediction': guesses.pop()
    with pytest.raises(ValueError): s.stage_training(rows, metadata, guesses)


@pytest.mark.parametrize('damage', ['holdout', 'null_reference', 'duplicate', 'wrong_hash', 'raw_reference'])
def test_worker_input_rejects_leakage_and_missing_references(damage):
    raw, refs, _ = s.stage_training(*synthetic_records())
    if damage == 'holdout': refs[0]['partition'] = 'test'
    if damage == 'null_reference': refs[0]['reference'] = None
    if damage == 'duplicate': raw[1]['record_id'] = raw[0]['record_id']
    if damage == 'wrong_hash': refs[0]['text_sha256'] = '0' * 64
    if damage == 'raw_reference': raw[0]['reference'] = []
    with pytest.raises(ValueError): s.validate_view(raw, refs)


def test_strict_gains_losses_negatives_and_unsupported_slices():
    raw = [{'record_id': 'a', 'text': 'Aster Road flooded.', 'prediction': [[0, 10, 'CITY']]},
           {'record_id': 'b', 'text': 'Office of Aster Safety reported rain.', 'prediction': [[0, 22, 'CITY']]}]
    refs = {'a': {'reference': [[0, 10, 'ROAD']], 'language': 'english'},
            'b': {'reference': [], 'language': 'taglish'}}
    result, outputs, delta = s.run_shadow(raw, refs, {'named_asset', 'agency_actor'})
    assert result['counts']['gained_TP'] == 1 and result['counts']['resolved_FP'] == 2
    assert result['counts']['introduced_FN'] == result['counts']['introduced_FP'] == 0
    assert result['metrics']['overall']['f1'] == 1
    assert result['metrics']['labels']['PROVINCE']['f1'] is None
    assert len(outputs) == len(delta) == 2


def test_missing_reference_is_not_a_negative():
    with pytest.raises(ValueError):
        s.run_shadow([{'record_id': 'a', 'text': 'Text.', 'prediction': []}],
            {'a': {'reference': None, 'language': 'english'}}, set())


def test_stale_grant_manifest_and_occupied_destination(tmp_path):
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'; artifacts.mkdir(parents=True)
    grant = tmp_path / 'grant.json'; grant.write_text('{}')
    with pytest.raises(ValueError, match='stale preparation'):
        s.prepare(tmp_path, grant, '0' * 64, artifacts / 'new')
    view = tmp_path / 'view'; view.mkdir(); (view / 'manifest.json').write_text('{}')
    with pytest.raises(ValueError, match='stale view'):
        s.study(tmp_path, view, '0' * 64, artifacts / 'new')
    occupied = artifacts / 'occupied'; occupied.mkdir()
    with pytest.raises(ValueError): s.output_path(tmp_path, occupied)
    assert not (artifacts / 'new').exists()


def test_source_binding_mismatch_rejected(tmp_path):
    values = [{'path': p, 'sha256': '0' * 64} for p in s.SOURCES]
    with pytest.raises((ValueError, FileNotFoundError)):
        s.verify_sources(tmp_path, {'implementation': values, 'tests': {'path': s.TEST, 'sha256': '0' * 64}})


def test_constructed_preparation_and_separate_worker_end_to_end(tmp_path):
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'; artifacts.mkdir(parents=True)
    def dump(path, value):
        path.write_text(json.dumps(value), encoding='utf-8')
    def binding(path):
        return {'path': path.relative_to(tmp_path).as_posix(), 'sha256': s.digest(path)}
    for name in [*s.SOURCES, s.TEST]:
        p = tmp_path / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('fictional binding')
    development = tmp_path / 'development'; development.mkdir()
    records, metadata, predictions = synthetic_records()
    (development / 'admitted-records.jsonl').write_text('\n'.join(json.dumps(x) for x in records))
    dump(development / 'partitions.json', {'members': metadata})
    dump(development / 'status.json', {'capability': 'development', 'counts': {'train': 345, 'dev': 60},
        'files': {n: s.digest(development / n) for n in ('admitted-records.jsonl', 'partitions.json')}})
    (tmp_path / 'predictions.jsonl').write_text('\n'.join(json.dumps(x) for x in predictions))
    raw, refs, _ = s.stage_training(records, metadata, predictions)
    result, _, _ = s.run_shadow(raw, {x['record_id']: x for x in refs}, set())
    dump(tmp_path / 'metrics.json', {'0': {'train': result['metrics']}})
    first = records[0]
    dump(tmp_path / 'grounding.json', {k: [{'record_id': first['record_id'], 'text_sha256': first['text_sha256'],
        'source_sha256': first['source']['text_sha256'], 'start': 0, 'end': 10, 'text': 'Aster Road'}] for k in r.RULES})
    (tmp_path / 'guide.md').write_text('Fictional test convention')
    grant = {'schema': 'lanes-context-safeguard-preparation-v1', 'scope': s.SCOPE,
        'development_directory': 'development', 'inputs': {k: binding(tmp_path / v) for k, v in {
            'development_status': 'development/status.json', 'control_predictions': 'predictions.jsonl',
            'control_metrics': 'metrics.json', 'grounding': 'grounding.json', 'annotation_guide': 'guide.md',
            'scope_guide': 'guide.md'}.items()},
        'implementation': [binding(tmp_path / name) for name in s.SOURCES], 'tests': binding(tmp_path / s.TEST)}
    dump(tmp_path / 'grant.json', grant)
    view = artifacts / 'view'; output = artifacts / 'study'
    s.prepare(tmp_path, tmp_path / 'grant.json', s.digest(tmp_path / 'grant.json'), view)
    # Parent files are deliberately unavailable to the study worker. It consumes only the projected training view.
    (tmp_path / 'predictions.jsonl').unlink()
    (development / 'admitted-records.jsonl').unlink()
    summary = s.study(tmp_path, view, s.digest(view / 'manifest.json'), output)
    assert summary['qualifying_rule_ids'] == ['named_asset']
    assert summary['combined_counts']['gained_TP'] == 345
    assert summary['validation_evaluated'] is summary['holdout_accessed'] is False
    assert all(item['disposition'] == 'partially_supported' for key, item in summary['per_rule'].items() if key != 'named_asset')
    (view / 'references.jsonl').write_text('changed')
    with pytest.raises(ValueError, match='view member changed'):
        s.study(tmp_path, view, s.digest(view / 'manifest.json'), artifacts / 'other')


def test_competing_writer_rejected_without_modifying_existing_lock(tmp_path):
    lock = tmp_path / 'lock'
    with s.exclusive(lock):
        before = lock.read_bytes()
        with pytest.raises(FileExistsError):
            with s.exclusive(lock): pass
        assert lock.read_bytes() == before
    assert not lock.exists()


def test_guards_block_neural_network_and_training_processes():
    program = """
import sys, socket, subprocess
sys.path.insert(0, 'backend')
from training.flood_ner.context_safeguard_study import install_guards
install_guards()
for op in (lambda: __import__('spacy'), lambda: socket.getaddrinfo('example.org', 443),
           lambda: subprocess.run([sys.executable, '-c', 'print(1)'])):
    try: op()
    except RuntimeError: pass
    else: raise AssertionError('forbidden execution passed')
print('blocked')
"""
    result = subprocess.run([sys.executable, '-B', '-c', program], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'blocked'
