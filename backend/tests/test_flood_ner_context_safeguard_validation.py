"""Constructed validation envelopes, text and outcomes; never private corpus fixtures."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from training.flood_ner import context_safeguard_validation as v


def sha(text): return hashlib.sha256(text.encode()).hexdigest()


def synthetic():
    records, metadata, predictions = [], [], []
    for i in range(60):
        rid = 'fictional-' + str(i); text = 'Peña Road flooded.'; language = 'english' if i < 38 else 'taglish'
        spans = [{'id': 'one', 'start': 0, 'end': 9, 'text': 'Peña Road', 'label': 'ROAD'}]
        records.append({'record_id': rid, 'annotation_profile': 'location-only-v1', 'passage_language': language,
            'text': text, 'text_sha256': sha(text), 'passage_start': 0, 'passage_end': len(text), 'entities': spans,
            'complete': True, 'split': 'dev', 'review_status': 'accepted', 'quality': 'silver', 'annotation_revision': 'fixture',
            'source': {'source_id': rid, 'url': 'https://example.org/fictional', 'publisher': 'fictional',
                'origin': 'captured_original', 'text': text, 'text_sha256': sha(text), 'capture_version': 'fixture',
                'article_group': 'fictional-' + str(i // 3), 'reuse_terms': 'constructed test only', 'extraction_method': 'fixture'}})
        metadata.append({'record_id': rid, 'partition': 'dev', 'language': language, 'passage_sha256': sha(text),
            'source_sha256': sha(text), 'passage_start': 0, 'passage_end': len(text), 'is_negative': False,
            'fitted_component': False, 'group_keys': ['fictional-' + str(i // 3)]})
        predictions.append({'record_id': rid, 'seed': 0, 'partition': 'dev', 'language': language,
            'text_sha256': sha(text), 'reference': [[0, 9, 'ROAD']], 'prediction': [[0, 9, 'LANDMARK']]})
    return records, metadata, predictions


def test_projection_is_deterministic_and_skips_training_and_other_seeds():
    records, metadata, guesses = synthetic(); original = deepcopy((records, metadata, guesses))
    raw, refs, groups = v.stage_validation(records + [{'split': 'train', 'poison': object()}], metadata,
        guesses + [{'partition': 'train', 'poison': object()}, {'partition': 'dev', 'seed': 2}])
    assert v.stage_validation(records, metadata, guesses) == (raw, refs, groups)
    assert (records, metadata, guesses) == original
    assert all(set(r) == {'record_id', 'text', 'prediction'} for r in raw)
    assert all(len(r['group_keys'][0]) == 64 for r in groups)
    assert len(v.validate_view(raw, refs, groups)) == 60


@pytest.mark.parametrize('damage', ['missing', 'duplicate', 'meta_duplicate', 'fitted', 'split_group',
    'incomplete', 'missing_reference', 'null_reference', 'text', 'language', 'source', 'polarity', 'prediction', 'duplicate_prediction', 'seed_bool'])
def test_projection_rejects_inconsistent_inputs(damage):
    records, metadata, guesses = synthetic()
    if damage == 'missing': records.pop()
    if damage == 'duplicate': records.append(deepcopy(records[0]))
    if damage == 'meta_duplicate': metadata.append(deepcopy(metadata[0]))
    if damage == 'fitted': metadata[0]['fitted_component'] = True
    if damage == 'split_group': metadata.append({'partition': 'train', 'group_keys': metadata[0]['group_keys']})
    if damage == 'incomplete': records[0]['complete'] = False
    if damage == 'missing_reference': del records[0]['entities']
    if damage == 'null_reference': records[0]['entities'] = None
    if damage == 'text': records[0]['text'] += '!'
    if damage == 'language': guesses[0]['language'] = 'taglish'
    if damage == 'source': metadata[0]['source_sha256'] = '0' * 64
    if damage == 'polarity': metadata[0]['is_negative'] = True
    if damage == 'prediction': guesses.pop()
    if damage == 'duplicate_prediction': guesses.append(deepcopy(guesses[0]))
    if damage == 'seed_bool': guesses[0]['seed'] = False
    with pytest.raises(ValueError): v.stage_validation(records, metadata, guesses)


@pytest.mark.parametrize('damage', ['training', 'holdout', 'duplicate', 'missing', 'null', 'raw_reference', 'hash', 'groups', 'language'])
def test_worker_validation_roster_and_reference_separation(damage):
    raw, refs, groups = v.stage_validation(*synthetic())
    if damage in ('training', 'holdout'): refs[0]['partition'] = 'train' if damage == 'training' else 'test'
    if damage == 'duplicate': raw[1]['record_id'] = raw[0]['record_id']
    if damage == 'missing': raw.pop()
    if damage == 'null': refs[0]['reference'] = None
    if damage == 'raw_reference': raw[0]['reference'] = []
    if damage == 'hash': refs[0]['text_sha256'] = '0' * 64
    if damage == 'groups': groups[0]['group_keys'] = []
    if damage == 'language': refs[0]['language'] = 'taglish'
    with pytest.raises(ValueError): v.validate_view(raw, refs, groups)


def test_joint_rules_unicode_repetition_and_strict_transitions():
    text = 'Peña Road; Peña Road; Purok 6 and 7.'
    number = len('Peña Road; Peña Road; Purok 6 and ')
    predictions = [[0, 9, 'LANDMARK'], [11, 20, 'ROAD'], [number, number + 1, 'ROAD']]
    raw = [{'record_id': 'opaque', 'text': text, 'prediction': predictions}]
    refs = {'opaque': {'reference': [[0, 9, 'ROAD'], [11, 20, 'ROAD'], [number, number + 1, 'LOCAL_AREA']],
                       'language': 'english', 'text_sha256': sha(text)}}
    before = deepcopy(raw)
    metrics, counts, rows, actions, groups = v.compare(raw, refs, [{'record_id': 'opaque', 'group_keys': ['fictional']}])
    assert raw == before and counts['gained_TP'] == counts['resolved_FP'] == 2
    assert counts['introduced_FN'] == counts['introduced_FP'] == 0
    assert counts['retags'] == 2 and counts['drops'] == 0
    assert metrics['shadow']['overall']['f1'] == 1
    assert groups['connected_groups'] == groups['changed_groups'] == 1
    assert rows[0]['disposition'] == 'changed_no_new_strict_error'
    assert set(actions) == set(v.ENABLED)


def test_drop_only_family_is_not_enabled_and_ambiguous_facility_abstains():
    text = 'Office of Aster Safety reported rain; Aster Center board met.'
    raw = [{'record_id': 'a', 'text': text, 'prediction': [[0, 22, 'CITY'], [38, 50, 'ROAD']]}]
    result = v.raw_record(raw[0], enabled=set(v.ENABLED))
    assert result['shadow'] == raw[0]['prediction']
    assert result['decisions'][1]['abstained']


def scoring_sample(prediction):
    text = 'Peña Road'
    refs = {'a': [[0, 9, 'ROAD']], 'b': []}; langs = {'a': 'english', 'b': 'taglish'}
    baseline = v.score_partition(refs, {'a': [[0, 9, 'LANDMARK']], 'b': []}, langs)
    shadow = v.score_partition(refs, prediction, langs)
    return {'baseline': baseline, 'shadow': shadow}


def test_qualifying_outcome_and_unsupported_slices():
    metrics = scoring_sample({'a': [[0, 9, 'ROAD']], 'b': []})
    assert metrics['shadow']['language_labels']['taglish']['ROAD']['f1'] is None
    assert v.outcome(metrics, {'introduced_FP': 0, 'introduced_FN': 0})['disposition'] == 'qualifies'


@pytest.mark.parametrize('damage', ['tie', 'tiny_gain', 'new_fp', 'new_fn', 'label_decline', 'negative_error'])
def test_conservative_gate_rejects_ties_and_compensating_harms(damage):
    metrics = scoring_sample({'a': [[0, 9, 'ROAD']], 'b': []}); counts = {'introduced_FP': 0, 'introduced_FN': 0}
    if damage == 'tie': metrics['shadow']['overall']['f1'] = metrics['baseline']['overall']['f1']
    if damage == 'tiny_gain': metrics['shadow']['overall']['f1'] = metrics['baseline']['overall']['f1'] + 5e-13
    if damage == 'new_fp': counts['introduced_FP'] = 1
    if damage == 'new_fn': counts['introduced_FN'] = 1
    if damage == 'label_decline': metrics['shadow']['labels']['ROAD']['f1'] = -0.1
    if damage == 'negative_error': metrics['shadow']['negative_passages']['taglish']['false_positive_passages'] = 1
    assert v.outcome(metrics, counts)['disposition'] == 'does_not_qualify'


def setup_package(tmp_path):
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'; artifacts.mkdir(parents=True)
    def dump(path, data): path.write_text(json.dumps(data), encoding='utf-8')
    def bind(path): return {'path': path.relative_to(tmp_path).as_posix(), 'sha256': v.digest(path)}
    for name in [*v.SOURCES, v.TEST, 'old-test.py']:
        p = tmp_path / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('fictional source binding')
    implementation = [bind(tmp_path / n) for n in v.SOURCES]; tests = bind(tmp_path / v.TEST)
    dev = tmp_path / 'development'; dev.mkdir(); records, metadata, guesses = synthetic()
    (dev / 'admitted-records.jsonl').write_text('\n'.join(json.dumps(x) for x in records))
    dump(dev / 'partitions.json', {'members': metadata})
    dump(tmp_path / 'status.json', {'capability': 'development', 'counts': {'train': 345, 'dev': 60},
        'files': {n: v.digest(dev / n) for n in ('admitted-records.jsonl', 'partitions.json')}})
    (tmp_path / 'predictions.jsonl').write_text('\n'.join(json.dumps(x) for x in guesses))
    raw, refs, groups = v.stage_validation(records, metadata, guesses)
    baseline = v.score_partition({r['record_id']: r['reference'] for r in refs},
        {r['record_id']: r['prediction'] for r in raw}, {r['record_id']: r['language'] for r in refs})
    dump(tmp_path / 'metrics.json', {'0': {'dev': baseline}})
    dump(tmp_path / 'summary.json', {'qualifying_rule_ids': v.ENABLED, 'eligible_subset_safe': True, 'validation_evaluated': False})
    dump(tmp_path / 'old-manifest.json', {'files': {'summary.json': v.digest(tmp_path / 'summary.json')},
        'implementation': implementation[:-1], 'tests': bind(tmp_path / 'old-test.py')})
    dump(tmp_path / 'test-evidence.json', {'scope': 'constructed_checks_only', 'passed': 1, 'failed': 0,
        'implementation': implementation, 'tests': tests})
    (tmp_path / 'guide.md').write_text('fictional conventions')
    inputs = {k: bind(tmp_path / n) for k, n in {'study_manifest': 'old-manifest.json', 'study_summary': 'summary.json',
        'development_status': 'status.json', 'control_predictions': 'predictions.jsonl', 'control_metrics': 'metrics.json',
        'annotation_guide': 'guide.md', 'scope_guide': 'guide.md', 'test_evidence': 'test-evidence.json'}.items()}
    grant = {'schema': 'lanes-context-validation-grant-v1', 'scope': v.SCOPE, 'protocol': deepcopy(v.POLICY),
        'permissions': v.PERMISSIONS, 'inputs': inputs, 'implementation': implementation, 'tests': tests,
        'development_directory': 'development'}
    grant_path = tmp_path / 'grant.json'; dump(grant_path, grant)
    return artifacts, grant_path, grant


def test_end_to_end_one_attempt_and_parent_separation(tmp_path):
    artifacts, grant, _ = setup_package(tmp_path); view = artifacts / 'view'
    v.prepare(tmp_path, grant, v.digest(grant), view)
    (tmp_path / 'predictions.jsonl').unlink(); (tmp_path / 'development/admitted-records.jsonl').unlink()
    summary = v.evaluate(tmp_path, view, v.digest(view / 'manifest.json'), artifacts / 'result')
    assert summary['decision']['disposition'] == 'qualifies'
    assert summary['transitions']['gained_TP'] == 60 and summary['groups']['connected_groups'] == 20
    assert summary['model_selection_changed'] is summary['holdout_accessed'] is summary['training'] is False
    with pytest.raises(FileExistsError): v.evaluate(tmp_path, view, v.digest(view / 'manifest.json'), artifacts / 'second')
    assert not (artifacts / 'second').exists()


@pytest.mark.parametrize('damage', ['hash', 'source', 'policy', 'permissions', 'evidence'])
def test_preparation_rejects_stale_or_unqualified_grants(tmp_path, damage):
    artifacts, grant_path, grant = setup_package(tmp_path)
    if damage == 'hash': expected = '0' * 64
    else:
        if damage == 'source': (tmp_path / v.SOURCES[0]).write_text('changed source')
        if damage == 'policy': grant['protocol']['subset'] = ['agency_actor']
        if damage == 'permissions': grant['permissions'] = {**v.PERMISSIONS, 'training': True}
        if damage == 'evidence':
            p = tmp_path / 'test-evidence.json'; data = json.loads(p.read_text()); data['failed'] = 1
            p.write_text(json.dumps(data)); grant['inputs']['test_evidence']['sha256'] = v.digest(p)
        grant_path.write_text(json.dumps(grant)); expected = v.digest(grant_path)
    with pytest.raises(ValueError): v.prepare(tmp_path, grant_path, expected, artifacts / 'view')
    assert not (artifacts / 'view').exists()


@pytest.mark.parametrize('damage', ['stale_manifest', 'changed_member', 'occupied', 'concurrent', 'holdout', 'attempt'])
def test_evaluation_preflight_rejects_invalid_inputs(tmp_path, damage):
    artifacts, grant, _ = setup_package(tmp_path); view = artifacts / 'view'
    v.prepare(tmp_path, grant, v.digest(grant), view)
    output = artifacts / 'out'; expected = v.digest(view / 'manifest.json')
    if damage == 'stale_manifest': expected = '0' * 64
    if damage == 'changed_member': (view / 'raw-predictions.jsonl').write_text('changed')
    if damage == 'occupied': output.mkdir()
    if damage == 'concurrent': (artifacts / 'context-validation-active.lock').write_text('owner')
    if damage in ('holdout', 'attempt'):
        p = view / 'manifest.json'; data = json.loads(p.read_text())
        if damage == 'holdout': data['capability'] = 'holdout'
        else: data['attempt_key'] = '0' * 64
        p.write_text(json.dumps(data)); expected = v.digest(p)
    with pytest.raises((ValueError, FileExistsError)): v.evaluate(tmp_path, view, expected, output)


def test_failure_preserves_evidence_and_consumes_attempt(tmp_path, monkeypatch):
    artifacts, grant, _ = setup_package(tmp_path); view = artifacts / 'view'
    v.prepare(tmp_path, grant, v.digest(grant), view)
    monkeypatch.setattr(v, 'compare', lambda *args: (_ for _ in ()).throw(RuntimeError('constructed failure')))
    with pytest.raises(RuntimeError): v.evaluate(tmp_path, view, v.digest(view / 'manifest.json'), artifacts / 'failed')
    assert json.loads((artifacts / 'failed/failure.json').read_text())['attempt_consumed']
    assert len(list((artifacts / 'context-validation-attempts').iterdir())) == 1
    assert not (artifacts / 'context-validation-active.lock').exists()
    with pytest.raises(FileExistsError): v.evaluate(tmp_path, view, v.digest(view / 'manifest.json'), artifacts / 'retry')


def test_cli_guards_block_models_network_and_training_processes():
    program = """
import sys,socket,subprocess
sys.path.insert(0,'backend')
from training.flood_ner.context_safeguard_validation import install_guards
install_guards()
for op in (lambda: __import__('spacy'), lambda:socket.getaddrinfo('example.org',443),
           lambda:subprocess.run([sys.executable,'-c','print(1)'])):
    try:op()
    except RuntimeError:pass
    else:raise AssertionError('forbidden execution')
print('blocked')
"""
    result = subprocess.run([sys.executable, '-B', '-c', program], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'blocked'


@pytest.mark.parametrize('bad', [[[0, 8, 'ROAD']], [[0, 9, 'ROAD'], [10, 17, 'CITY']], [[0, 9, 'DEPTH']]])
def test_rejects_added_resized_or_out_of_profile_shadow_spans(monkeypatch, bad):
    raw, references, groups = v.stage_validation(*synthetic())
    refs = v.validate_view(raw, references, groups)
    original = v.raw_record
    def corrupted(row, **kwargs):
        result = original(row, **kwargs); result['shadow'] = bad
        return result
    monkeypatch.setattr(v, 'raw_record', corrupted)
    with pytest.raises(ValueError): v.compare(raw, refs, groups)


def test_abstention_and_no_change_do_not_count_as_improvement():
    metrics = scoring_sample({'a': [[0, 9, 'LANDMARK']], 'b': []})
    result = v.outcome(metrics, {'introduced_FP': 0, 'introduced_FN': 0})
    assert result['disposition'] == 'does_not_qualify'
    assert result['checks']['no_introduced_FP'] and not result['checks']['overall_f1_improved']
