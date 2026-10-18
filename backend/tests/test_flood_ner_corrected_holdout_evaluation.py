"""Constructed-only protocol/security tests. Never locate or read held records."""
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from training.flood_ner import corrected_holdout_evaluation as e
from training.flood_ner import corrected_rules_worker as w


def h(value):
    return hashlib.sha256(value.encode()).hexdigest()


class Tokenizer:
    def make_doc(self, text):
        class Doc:
            def char_span(self, start, end, alignment_mode):
                return object()
        return Doc()


def corpus():
    from training.flood_ner.annotation.schema import AnnotationRecord
    from training.flood_ner.research_review import group_keys
    from training.flood_ner.successor_preparation import safe_group_keys
    records, metadata, join = [], [], []
    for i in range(60):
        text = f'Pasig City constructed example {i}.'
        source = {'source_id': f's{i}', 'url': f'https://constructed.invalid/story/{i}', 'publisher': 'constructed',
                  'origin': 'captured_original', 'text': text, 'text_sha256': h(text), 'capture_version': 'fixture',
                  'article_group': f'article{i // 2}', 'event_group': f'event{i // 2}', 'reuse_status': 'allowed',
                  'reuse_terms': 'constructed test', 'admission_status': 'training_admitted', 'extraction_method': 'fixture'}
        entities = [] if i % 30 >= 27 else [{'id': 'e1', 'start': 0, 'end': 10, 'text': 'Pasig City', 'label': 'CITY'}]
        row = {'schema_version': 'lanes-flood-ner-v1', 'annotation_profile': 'location-only-v1',
               'passage_language': 'english' if i < 30 else 'taglish', 'record_id': f'constructed-{i}',
               'source': source, 'passage_start': 0, 'passage_end': len(text), 'text': text, 'text_sha256': h(text),
               'entities': entities, 'facts': [], 'relations': [], 'annotation_revision': 'fixture', 'quality': 'silver',
               'teacher': 'fixture', 'reviewer': 'fixture', 'review_status': 'accepted', 'complete': True, 'split': 'test'}
        model = AnnotationRecord.model_validate_json(json.dumps(row))
        meta = {'record_id': row['record_id'], 'partition': 'research_holdout', 'group_keys': sorted(group_keys(model)),
                'article_group': source['article_group'], 'source_sha256': h(text), 'passage_sha256': h(text),
                'passage_start': 0, 'passage_end': len(text), 'alternatives': [], 'fitted_component': False,
                'language': row['passage_language'], 'is_negative': not entities}
        records.append(row); metadata.append(meta)
        join.append({**{k: v for k, v in meta.items() if k != 'article_group'}, 'group_keys': safe_group_keys(meta['group_keys'])})
    exclusions = [{'record_id': f'dev-fixture-{i}', 'partition': 'train' if i < 345 else 'dev',
                   'group_keys': [f'article:devfixture{i}'], 'source_sha256': h(f'source{i}'),
                   'passage_sha256': h(f'passage{i}'), 'passage_start': 0, 'passage_end': 10,
                   'alternatives': [], 'fitted_component': i < 280} for i in range(405)]
    return records, metadata, join, exclusions


def test_full_constructed_validation_and_unicode():
    rows, metadata, join, exclusions = corpus()
    e.validate_rows(rows, metadata, join, exclusions, Tokenizer())
    rows[0]['text'] = 'é' + rows[0]['text'][1:]
    with pytest.raises(ValueError):
        e.validate_rows(rows, metadata, join, exclusions, Tokenizer())


@pytest.mark.parametrize('mutate', [
    lambda r, m, j, d: r[27].pop('entities'),
    lambda r, m, j, d: r[0].update(complete=False),
    lambda r, m, j, d: r[0]['entities'][0].update(text='wrong'),
    lambda r, m, j, d: m[0].update(group_keys=[]),
    lambda r, m, j, d: m[0].update(fitted_component=True),
    lambda r, m, j, d: m[0].update(alternatives=[r[1]['record_id']]),
    lambda r, m, j, d: d[0].update(group_keys=j[0]['group_keys']),
    lambda r, m, j, d: d[0].update(passage_sha256=j[0]['passage_sha256']),
    lambda r, m, j, d: d[0].update(record_id=r[0]['record_id']),
    lambda r, m, j, d: j[0].update(passage_end=1),
])
def test_reject_incomplete_group_or_cross_partition_leakage(mutate):
    args = corpus()
    mutate(*args)
    with pytest.raises((ValueError, KeyError)):
        e.validate_rows(*args, Tokenizer())


def test_article_cap_and_overlap():
    from training.flood_ner.successor_preparation import validate_partition_rows
    _, rows, _, _ = corpus()
    for row in rows[:4]: row['article_group'] = 'same-article'
    with pytest.raises(ValueError, match='article passage cap'):
        validate_partition_rows(rows, capability='research_holdout')
    _, rows, _, _ = corpus()
    rows[1]['source_sha256'] = rows[0]['source_sha256']
    with pytest.raises(ValueError, match='overlapping'):
        validate_partition_rows(rows, capability='research_holdout')


def test_group_keys_independently_derived():
    from training.flood_ner.successor_preparation import safe_group_keys
    rows, metadata, join, exclusions = corpus()
    metadata[0]['group_keys'] = ['constructed:invented']
    join[0]['group_keys'] = safe_group_keys(metadata[0]['group_keys'])
    with pytest.raises(ValueError, match='source group omitted'):
        e.validate_rows(rows, metadata, join, exclusions, Tokenizer())


def test_token_alignment():
    class Misaligned:
        def make_doc(self, text):
            class Doc:
                def char_span(self, *args, **kwargs): return None
            return Doc()
    with pytest.raises(ValueError, match='schema/source/tokenizer'):
        e.validate_rows(*corpus(), Misaligned())


def test_shared_persistent_claim_concurrent_and_second_freeze(tmp_path):
    (tmp_path / 'backend/training/flood_ner/artifacts').mkdir(parents=True)
    def attempt(i):
        try:
            e.claim_attempt(tmp_path, h(f'freeze{i}'), tmp_path / f'output{i}')
            return True
        except FileExistsError:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(8))) == 1
    with pytest.raises(FileExistsError):
        e.claim_attempt(tmp_path, h('completely-new-freeze'), tmp_path / 'second-output')
    assert len(list((tmp_path / 'backend/training/flood_ner/artifacts/v19-single-holdout-attempts').iterdir())) == 1


def test_strict_scoring_and_zero_support():
    truth = {'x': [(0, 10, 'CITY')], 'y': []}
    pred = {'x': [(0, 9, 'CITY')], 'y': [(0, 3, 'ROAD')]}
    result = e.scored(truth, pred, {'x': 'english', 'y': 'taglish'})
    assert result['overall']['TP'] == 0 and result['overall']['FP'] == 2 and result['overall']['FN'] == 1
    assert result['labels']['ROAD']['f1'] is None
    assert result['labels']['ROAD']['support_status'] == 'unmeasured'
    assert result['negative_passages']['taglish']['rate'] == 1
    with pytest.raises(ValueError):
        e.scored(truth, {'x': truth['x'] * 2, 'y': []}, {'x': 'english', 'y': 'taglish'})


def test_connected_group_bootstrap_reproducible_and_paired():
    truth = {'x': [(0, 1, 'CITY')], 'y': [], 'z': [(0, 1, 'CITY')]}
    predictions = {name: truth for name in e.ROSTER}
    one = e.paired_intervals(truth, predictions, [['x', 'y'], ['z']])
    assert one == e.paired_intervals(truth, predictions, [['x', 'y'], ['z']])
    assert all(v == {'lower_95': 0.0, 'upper_95': 0.0, 'defined_replicates': 10000} for v in one['comparisons'].values())
    with pytest.raises(ValueError):
        e.paired_intervals(truth, predictions, [['x', 'y'], ['y', 'z']])


def aggregate():
    records, members, _, _ = corpus()
    truth = {r['record_id']: [(v['start'], v['end'], v['label']) for v in r['entities']] for r in records}
    langs = {r['record_id']: r['passage_language'] for r in records}
    metrics = {n: e.scored(truth, truth, langs) for n in e.ROSTER}
    return {'schema': 'lanes-v19-holdout-aggregate-v2', 'state': 'passed', 'freeze_sha256': h('freeze'),
            'qualification_sha256': h('qual'), 'original_handoff_sha256': e.ORIGINAL_HANDOFF,
            'holdout_qualification_sha256': e.HOLDOUT_QUALIFICATION, 'protocol_sha256': e.PROTOCOL_SHA256,
            'primary': 'control-seed-0', 'roster': list(e.ROSTER), 'device': 'cpu', 'records': 60,
            'metrics': metrics, 'family_statistics': {f: {'primary_seed': 0, 'primary_f1': 1.0, 'mean_f1': 1.0, 'sample_stddev': 0.0}
                                                    for f in ('control', 'v16')},
            'uncertainty': e.paired_intervals(truth, {n: truth for n in e.ROSTER}, e.groups(members)),
            'training_performed': False, 'selection_changed': False, 'holdout_predictions_performed': True,
            'global_history_verified': False, 'accounting_verified': False, 'certified_fresh': False,
            'python_version': '3.11.17', 'spacy_version': '3.7.5', 'rules_python_version': '3.12.14',
            'private_artifact_sha256': {n: h(n) for n in ('predictions.json', 'metrics.json', 'uncertainty.json')}}


def test_deep_aggregate_allowlist():
    result = aggregate()
    assert e.safe_aggregate(result) == result
    mutations = [
        lambda v: v.update(record_id='candidate'),
        lambda v: v['metrics']['rules']['labels']['CITY'].update(text='private'),
        lambda v: v['metrics']['rules']['overall'].update(f1='private'),
        lambda v: v['metrics']['rules']['overall'].update(f1=float('nan')),
        lambda v: v['uncertainty']['comparisons'].update(candidate_id={}),
        lambda v: v['private_artifact_sha256'].update({'private-text.json': h('secret')}),
        lambda v: v['family_statistics']['control'].update(primary_f1=True),
    ]
    for mutate in mutations:
        bad = copy.deepcopy(result); mutate(bad)
        with pytest.raises(ValueError): e.safe_aggregate(bad)


def request(tmp_path, monkeypatch):
    worker = tmp_path / 'backend/training/flood_ner/corrected_rules_worker.py'
    worker.parent.mkdir(parents=True)
    worker.write_text('constructed worker')
    baseline = worker.with_name('rules_baseline.py'); baseline.write_text('constructed baseline')
    monkeypatch.setattr(w.sys, 'version', '3.12.14 constructed')
    return {'schema': 'lanes-corrected-rules-request-v1', 'root': str(tmp_path),
            'runtime': {'python': sys.executable, 'sha256': w.digest(sys.executable), 'version': '3.12.14'},
            'files': {p.relative_to(tmp_path).as_posix(): w.digest(p) for p in (worker, baseline)},
            'rows': [{'record_id': 'opaque', 'text': 'Exact é\r\ntext.'}]}


def test_rules_raw_only_runtime_and_stale_binding(tmp_path, monkeypatch):
    req = request(tmp_path, monkeypatch)
    assert w.checked_request(req)[1] == req['rows']
    for mutate in [lambda q: q['rows'][0].update(entities=[]), lambda q: q.update(references=[]),
                   lambda q: q['runtime'].update(sha256='0' * 64), lambda q: q['runtime'].update(version='3.11.17'),
                   lambda q: q['files'].update({'../escape': '0' * 64})]:
        bad = copy.deepcopy(req); mutate(bad)
        with pytest.raises(ValueError): w.checked_request(bad)
    (tmp_path / 'backend/training/flood_ner/rules_baseline.py').write_text('changed')
    with pytest.raises(ValueError): w.checked_request(req)


def test_rules_guards_before_app_imports_and_real_constructed_probe():
    code = '''
import sys, socket
sys.path.insert(0, 'backend')
from training.flood_ner.corrected_rules_worker import install_guards
install_guards()
assert 'app.services.taglish_extraction_service' not in sys.modules
from training.flood_ner.rules_baseline import predict_mentions
assert isinstance(predict_mentions('Baha sa Pasig City.')['spans'], list)
import sqlalchemy
for operation in (lambda: socket.socket(), lambda: sqlalchemy.create_engine('inert').connect(), lambda: __import__('sqlite3'), lambda: __import__('psycopg')):
    try: operation()
    except RuntimeError: pass
    else: raise AssertionError('guard failed')
print('constructed guards passed')
'''
    proc = subprocess.run([str(ROOT / 'backend/.venv/Scripts/python.exe'), '-B', '-c', code], cwd=ROOT, capture_output=True)
    assert proc.returncode == 0, proc.stderr.decode('utf-8', errors='replace')
    assert proc.stdout.strip() == b'constructed guards passed'


def test_full_raw_rules_subprocess_and_complete_package_closure(tmp_path):
    from training.flood_ner.rules_baseline import specification
    runtime = ROOT / 'backend/.venv/Scripts/python.exe'
    files = w.rules_code_files(ROOT)
    assert 'backend/app/schemas/__init__.py' in files
    assert 'backend/app/models/__init__.py' in files
    files['backend/training/flood_ner/corrected_rules_worker.py'] = w.digest(ROOT / 'backend/training/flood_ner/corrected_rules_worker.py')
    receipt = {'rules_runtime': {'python': str(runtime), 'sha256': w.digest(runtime), 'version': '3.12.14'},
               'rules_specification': specification(ROOT), 'implementation': files}
    rows = [{'record_id': 'opaque-constructed', 'text': 'Baha sa Pasig City.\r\nÉxact raw text.'}]
    result = e.run_rules(ROOT, receipt, rows, tmp_path / 'rules-probe')
    assert set(result) == {'opaque-constructed'}
    assert any(v == [8, 18, 'CITY'] for v in result['opaque-constructed'])


def scoped_fixture(tmp_path):
    folder = tmp_path / 'scoped'; folder.mkdir()
    package = folder / 'package'; package.mkdir()
    (package / 'tokenizer.bin').write_bytes(b'constructed')
    (package / 'model-contract.json').write_text('{}')
    runs = []
    for name in e.ROSTER[:-1]:
        model = folder / name; model.mkdir()
        (model / 'meta.json').write_text(json.dumps({'pipeline': ['ner'], 'labels': {'ner': sorted(e.LABELS)}}))
        runs.append({'name': name, 'model': name, 'files': e.tree(model)})
    manifest = {'schema': 'lanes-v19-scoped-models-v1', 'original_handoff_sha256': e.ORIGINAL_HANDOFF,
                'retained': 'control', 'primary': 'control-seed-0', 'runs': runs, 'files': e.tree(folder)}
    path = folder / 'manifest.json'; e.write_new(path, manifest)
    return folder, {'scoped_manifest': {'path': path.relative_to(tmp_path).as_posix(), 'sha256': e.digest(path)}}


@pytest.mark.parametrize('mutation', ['model', 'extra', 'manifest'])
def test_scoped_hash_and_extra_capability_rejected(tmp_path, mutation):
    folder, receipt = scoped_fixture(tmp_path)
    assert e.verify_scoped(tmp_path, receipt)[1] == folder
    if mutation == 'model':
        (folder / 'control-seed-0/meta.json').write_text('{}')
    elif mutation == 'extra':
        (folder / 'package/dev.spacy').write_bytes(b'constructed forbidden capability')
    else:
        receipt['scoped_manifest']['sha256'] = '0' * 64
    with pytest.raises(ValueError):
        e.verify_scoped(tmp_path, receipt)


def test_stale_qualification_and_freeze_rejected_before_claim(tmp_path, monkeypatch):
    from training.flood_ner.v19_evaluation_qualification import verify_receipt
    qualification = tmp_path / 'qualification.json'; qualification.write_text('{}')
    with pytest.raises(ValueError):
        verify_receipt(tmp_path, qualification, '0' * 64)
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'; artifacts.mkdir(parents=True)
    freeze = artifacts / 'freeze'; freeze.mkdir()
    manifest = {'schema': 'lanes-v19-holdout-freeze-v2', 'protocol_sha256': e.PROTOCOL_SHA256,
                'original_handoff_sha256': e.ORIGINAL_HANDOFF, 'roster': list(e.ROSTER), 'primary': 'control-seed-0',
                'qualification': str(tmp_path / 'missing-qualification.json'), 'qualification_sha256': '0' * 64}
    e.write_new(freeze / 'manifest.json', manifest)
    with pytest.raises(ValueError, match='freeze changed'):
        e.verify_freeze(tmp_path, freeze, '0' * 64)
    monkeypatch.setattr(e, 'block_network', lambda: None)
    with pytest.raises((ValueError, FileNotFoundError)):
        e.evaluate(tmp_path, freeze, e.digest(freeze / 'manifest.json'), artifacts / 'output')
    assert not (artifacts / 'v19-single-holdout-attempts').exists()
    assert not (artifacts / 'output').exists()


def test_wrong_neural_runtime_rejected_before_loading(tmp_path, monkeypatch):
    from training.flood_ner import v19_evaluation_qualification as qualification
    receipt = {'original_handoff_sha256': e.ORIGINAL_HANDOFF, 'protocol_sha256': e.PROTOCOL_SHA256, 'verified': True,
               'neural_runtime': {'python': str(tmp_path / 'different-python.exe'), 'sha256': '0' * 64,
                                  'version': '3.11.17', 'spacy': '3.7.5'}}
    monkeypatch.setattr(qualification, 'verify_receipt', lambda *args: receipt)
    with pytest.raises(ValueError, match='neural interpreter'):
        e.verify_qualification(tmp_path, tmp_path / 'unused', '0' * 64)
