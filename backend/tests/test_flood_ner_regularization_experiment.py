"""Constructed data only: finite scheduling, unchanged exports and qualification guards."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from training.flood_ner import regularization_experiment as p
from training.flood_ner import regularization_worker as w
from training.flood_ner.development_error_audit import score_partition


def recipe(seed=0):
    return f'''[paths]
train = "@@TRAIN@@"
dev = "@@DEV@@"
vectors = null
init_tok2vec = null
[system]
seed = {seed}
[nlp.tokenizer]
model_manifest = "@@MODEL_MANIFEST@@"
manifest_sha256 = "@@MODEL_MANIFEST_SHA256@@"
tokenizer_file = "@@TOKENIZER@@"
[components.ner.model]
nO = null
[corpora.train]
path = ${{paths.train}}
[corpora.dev]
path = ${{paths.dev}}
[training]
max_steps = 1000
max_epochs = 30
eval_frequency = 35
patience = 175
dropout = 0.1
[training.batcher]
size = 8
[training.optimizer]
L2 = 0.01
L2_is_weight_decay = true
learn_rate = 0.001
[training.before_to_disk]
output = "@@CHECKPOINT@@"
'''


def fixture_score(split='dev', mode='control'):
    counts = p.LANGUAGES[split]
    truth, languages = {}, {}
    ordinal = 0
    for lang, count in counts.items():
        positive = (21 if lang == 'english' else 12) if split == 'dev' else 1
        for i in range(count):
            rid = f'constructed-{split}-{lang}-{i}'
            spans = []
            if i < positive:
                length = (3 if ordinal < 19 else 2) if split == 'dev' else 3
                spans = [(j * 5, j * 5 + 4, sorted(p.LABELS)[(ordinal + j) % 6]) for j in range(length)]
                ordinal += 1
            truth[rid] = spans; languages[rid] = lang
    n = 0; prediction = {}
    for rid, spans in truth.items():
        prediction[rid] = []
        for span in spans:
            keep = mode == 'perfect' or mode.startswith('drop_') and span[2] != mode[5:] or mode == 'control' and n % 4 != 0
            if keep: prediction[rid].append(span)
            n += 1
    return score_partition(truth, prediction, languages)


def baseline():
    return {str(seed): {'train': fixture_score('train'), 'dev': fixture_score()} for seed in range(3)}


def outcome(seed, mode='perfect'):
    return {'seed': seed, 'state': 'completed', 'validation': fixture_score(mode=mode)}


@pytest.mark.parametrize('seed', [0, 1, 2])
def test_exact_one_parameter_change(seed):
    result = p.candidate_template(recipe(seed), seed)
    p.verify_candidate(result, recipe(seed), seed)
    before, after = p.config_values(recipe(seed)), p.config_values(result)
    assert {k for k in before if before[k] != after[k]} == {('training.optimizer', 'L2')}
    assert after['training.optimizer', 'L2'] == '0.05'


@pytest.mark.parametrize('old,new', [('L2 = 0.05', 'L2 = 0.1'), ('L2 = 0.05', 'l2 = 0.05'),
    ('L2_is_weight_decay = true', 'L2_is_weight_decay = false'), ('dropout = 0.1', 'dropout = 0.2'),
    ('learn_rate = 0.001', 'learn_rate = 0.0005'), ('patience = 175', 'patience = 350'),
    ('nO = null', 'no = null'), ('size = 8', 'size = 16'), ('max_epochs = 30', 'max_epochs = 60'),
    ('max_steps = 1000', 'max_steps = 2000'), ('eval_frequency = 35', 'eval_frequency = 10')])
def test_other_recipe_changes_rejected(old, new):
    with pytest.raises(ValueError):
        p.verify_candidate(p.candidate_template(recipe(), 0).replace(old, new), recipe(), 0)


def test_holdout_and_wrong_control_rejected():
    with pytest.raises(ValueError): p.candidate_template(recipe().replace('@@DEV@@', 'test.spacy'), 0)
    with pytest.raises(ValueError): p.candidate_template(recipe().replace('L2 = 0.01', 'L2 = 0.1'), 0)


def test_screen_and_confirmation_maximum_three():
    base = baseline()
    assert p.schedule([], base)['next_seed'] == 0
    assert p.schedule([outcome(0)], base)['next_seed'] == 1
    assert p.schedule([outcome(0), outcome(1)], base)['next_seed'] == 2
    final = p.schedule([outcome(i) for i in range(3)], base)
    assert final['retained'] == 'stronger_weight_decay' and final['completed_runs'] == 3
    with pytest.raises(ValueError): p.schedule([outcome(i) for i in range(4)], base)


@pytest.mark.parametrize('mode', ['control', 'empty', 'drop_ROAD', 'drop_LOCAL_AREA'])
def test_failed_screen_never_runs_confirmation(mode):
    rows = [outcome(0, mode)]
    assert p.schedule(rows, baseline())['state'] == 'screening_failed'
    assert p.schedule(rows, baseline())['retained'] == 'control'
    with pytest.raises(ValueError): p.schedule(rows + [outcome(1)], baseline())


@pytest.mark.parametrize('mode', ['empty', 'drop_ROAD', 'drop_LOCAL_AREA'])
def test_mean_or_key_label_regression_retains_control(mode):
    rows = [outcome(0), outcome(1, mode), outcome(2, mode)]
    assert p.schedule(rows, baseline())['retained'] == 'control'


@pytest.mark.parametrize('position', [0, 1, 2])
def test_failure_stops_sequence(position):
    rows = [outcome(i) for i in range(position)] + [{'seed': position, 'state': 'failed', 'validation': None}]
    assert p.schedule(rows, baseline())['state'] == 'stopped_on_failure'
    with pytest.raises(ValueError): p.schedule(rows + [outcome(position + 1)], baseline())


@pytest.mark.parametrize('seeds', [[1], [0, 0], [0, 2], [False]])
def test_wrong_order_duplicate_or_boolean_seed(seeds):
    with pytest.raises(ValueError): p.schedule([outcome(i) for i in seeds], baseline())


def test_epsilon_tie_rules():
    assert not p.beats(.5 + 5e-13, .5)
    assert p.beats(.5 + 2e-12, .5)
    assert p.not_worse(.5 - 5e-13, .5)
    assert not p.not_worse(.5 - 2e-12, .5)


@pytest.mark.parametrize('mutate', [
    lambda s: s['overall'].update(f1=float('nan')),
    lambda s: s['overall'].update(f1=.12345),
    lambda s: s['labels']['ROAD'].update(TP=True),
    lambda s: s['languages']['english'].update(reference_spans=99),
    lambda s: s['language_labels']['taglish'].pop('ROAD'),
    lambda s: s.pop('negative_passages'),
])
def test_incomplete_or_forged_scores_rejected(mutate):
    row = outcome(0); mutate(row['validation'])
    with pytest.raises(ValueError): p.schedule([row], baseline())


def slices():
    rows = []
    for split, langs in p.LANGUAGES.items():
        for language, count in langs.items():
            for i in range(count):
                rid = f'constructed-{split}-{language}-{i}'
                rows.append({'record_id': rid, 'partition': split, 'language': language, 'is_negative': False,
                    'group_keys': ['article:' + rid], 'source_sha256': hashlib.sha256(rid.encode()).hexdigest(),
                    'passage_sha256': hashlib.sha256(('passage' + rid).encode()).hexdigest(), 'passage_start': 0,
                    'passage_end': 4, 'fitted_component': split == 'train', 'alternatives': []})
    return rows


@pytest.mark.parametrize('mutation', ['holdout', 'duplicate', 'language', 'fitted', 'group', 'text', 'reference'])
def test_development_sidecar_boundaries(mutation):
    rows = slices(); assert p.validate_slices(rows) == rows
    if mutation == 'holdout': rows[0]['partition'] = 'test'
    if mutation == 'duplicate': rows[1]['record_id'] = rows[0]['record_id']
    if mutation == 'language': rows[0]['language'] = 'taglish'
    if mutation == 'fitted': rows[-1]['fitted_component'] = True
    if mutation == 'group': rows[-1]['group_keys'] = rows[0]['group_keys']
    if mutation == 'text': rows[0]['text'] = 'forbidden'
    if mutation == 'reference': rows[0]['entities'] = []
    with pytest.raises(ValueError): p.validate_slices(rows)


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


@pytest.fixture
def grant_case(tmp_path, monkeypatch):
    root = tmp_path
    dev, control = root / 'development', root / 'control'
    dev.mkdir(); control.mkdir(); (root / 'model').mkdir()
    for name in ('admitted-records.jsonl', 'train.spacy', 'dev.spacy', 'tokenizer.bin', 'partitions.json', 'source-only-join-metadata.json'):
        (dev / name).write_bytes(b'constructed input')
    for name in ('train.spacy', 'dev.spacy', 'tokenizer.bin'):
        (control / name).write_bytes((dev / name).read_bytes())
    put(dev / 'aggregate-status.json', {'capability': 'development', 'counts': p.COUNTS, 'languages': p.LANGUAGES,
        'files': {n.name: p.digest(n) for n in dev.iterdir()}})
    put(control / 'handoff-manifest.json', {'variant': 'control',
        'partition_manifest_sha256': '4be5213e0b4106d358505027af936bedd7f80b8151345e62362127fcb2a5f20e'})
    put(root / 'preparation.json', {'schema': 'lanes-corrected-experiment-result-v1', 'counts': p.COUNTS,
        'training_performed': False, 'files': {'packages/control/handoff-manifest.json': p.digest(control / 'handoff-manifest.json'),
        'development/aggregate-status.json': p.digest(dev / 'aggregate-status.json')}})
    put(root / 'metrics.json', baseline())
    put(root / 'diagnosis.json', {'state': 'passed', 'counts': p.COUNTS, 'prediction_records': 1215,
        'desktop_metrics_reproduced': True, 'holdout_accessed': False, 'files': {'metrics.json': p.digest(root / 'metrics.json')}})
    put(root / 'desktop.json', {'schedule': {'state': 'complete', 'retained': 'control'},
        'outcomes': [{'variant': 'control', 'seed': s, **{k: baseline()[str(s)]['dev']['overall'][k]
                        for k in ('f1', 'precision', 'recall')}} for s in range(3)]})
    for name in (*p.IMPLEMENTATION, p.TEST_PATH):
        path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('constructed source')
    put(root / 'preservation.json', {'files': {}, 'holdout_metadata_only': {}})
    binding = lambda name: {'path': name, 'sha256': p.digest(root / name)}
    names = {'preparation_result': 'preparation.json', 'baseline_manifest': 'control/handoff-manifest.json',
        'development_status': 'development/aggregate-status.json', 'diagnosis_status': 'diagnosis.json',
        'baseline_metrics': 'metrics.json', 'desktop_selection': 'desktop.json', 'preservation': 'preservation.json'}
    grant = {'schema': 'lanes-regularization-grant-v1', 'scope': p.SCOPE,
        'permissions': dict.fromkeys(('network', 'holdout', 'inference', 'training', 'upload', 'git'), False),
        'bindings': {k: binding(v) for k, v in names.items()}, 'implementation': [binding(n) for n in p.IMPLEMENTATION],
        'tests': binding(p.TEST_PATH), 'development_directory': 'development', 'baseline_directory': 'control',
        'model_directory': 'model', 'runtime': {'python': sys.executable, 'sha256': p.digest(Path(sys.executable)),
                                              'version': '3.11.17', 'spacy': '3.7.5'}}
    monkeypatch.setattr(p, 'verify_package', lambda *args: p.read(control / 'handoff-manifest.json'))
    (root / 'backend/training/flood_ner/artifacts').mkdir(parents=True)
    return root, grant


@pytest.mark.parametrize('mutation', ['permission', 'runtime', 'source', 'metric_hash', 'missing', 'holdout', 'data', 'diagnosis'])
def test_grant_rejects_stale_or_unsafe_inputs(grant_case, mutation):
    root, grant = grant_case; p.verify_grant(root, grant)
    if mutation == 'permission': grant['permissions']['training'] = True
    if mutation == 'runtime': grant['runtime']['version'] = '3.12.14'
    if mutation == 'source': (root / p.IMPLEMENTATION[0]).write_text('changed')
    if mutation == 'metric_hash': grant['bindings']['baseline_metrics']['sha256'] = '0' * 64
    if mutation == 'missing': grant['bindings'].pop('diagnosis_status')
    if mutation == 'holdout': grant['development_directory'] = 'held-holdout'
    if mutation == 'data': (root / 'development/dev.spacy').write_text('changed')
    if mutation == 'diagnosis':
        path = root / 'diagnosis.json'; row = p.read(path); row['desktop_metrics_reproduced'] = False; put(path, row)
        grant['bindings']['diagnosis_status']['sha256'] = p.digest(path)
    with pytest.raises(ValueError): p.verify_grant(root, grant)


def test_existing_output_stale_grant_and_consumed_claim(grant_case, monkeypatch):
    root, grant = grant_case; path = root / 'grant.json'; put(path, grant)
    out = root / 'backend/training/flood_ner/artifacts/out'; out.mkdir()
    monkeypatch.setattr(p.subprocess, 'run', lambda *a, **k: pytest.fail('must not dispatch'))
    with pytest.raises(ValueError, match='stale'): p.prepare(root, path, '0' * 64, out)
    with pytest.raises(ValueError, match='new private'): p.prepare(root, path, p.digest(path), out)
    out = out.with_name('absent')
    claim = out.parent / ('regularization-preparation-claim-' + p.digest(path) + '.json'); put(claim, {})
    with pytest.raises(FileExistsError): p.prepare(root, path, p.digest(path), out)
    assert not out.exists() and claim.exists()


def test_exclusive_lock_rejects_competitors_and_releases_on_error(tmp_path):
    lock = tmp_path / 'active.lock'
    with pytest.raises(RuntimeError):
        with p.exclusive_lock(lock, 'first'):
            def competitor(_):
                with pytest.raises(FileExistsError):
                    with p.exclusive_lock(lock, 'second'): pass
            with ThreadPoolExecutor(max_workers=8) as pool: list(pool.map(competitor, range(8)))
            assert lock.read_text() == 'first'
            raise RuntimeError('constructed failure')
    assert not lock.exists()


def test_verification_never_starts_training_or_falls_back(tmp_path, monkeypatch):
    monkeypatch.setattr(p, 'verify_portable', lambda *args: None)
    calls = []
    def launcher(*args, **kwargs):
        calls.append(kwargs)
        return {'state': 'verified_read_only', 'configuration_schema_verified': True,
                'gpu_verified': kwargs['verify_device'], 'training_started': False}
    monkeypatch.setattr(p, 'launch', launcher)
    result = p.verify_desktop(tmp_path, tmp_path, 'hash', tmp_path, tmp_path, verify_gpu=True)
    assert result['training_started'] is False and calls == [{'start': False, 'verify_device': True}]
    with pytest.raises(ValueError, match='no training authorization'):
        p.verify_desktop(tmp_path, tmp_path, 'hash', tmp_path, tmp_path, start=True)
    def missing_gpu(*args, **kwargs):
        calls.append(kwargs); raise ValueError('GPU absent')
    monkeypatch.setattr(p, 'launch', missing_gpu)
    with pytest.raises(ValueError, match='GPU absent'):
        p.verify_desktop(tmp_path, tmp_path, 'hash', tmp_path, tmp_path, verify_gpu=True)
    assert len(calls) == 2


def test_stale_portable_manifest_rejected(tmp_path):
    put(tmp_path / 'experiment-manifest.json', {})
    with pytest.raises(ValueError, match='stale'): p.verify_portable(tmp_path, tmp_path, tmp_path, '0' * 64)


def record(text, spans, *, complete=True):
    sha = hashlib.sha256(text.encode()).hexdigest()
    return {'schema_version': 'lanes-flood-ner-v1', 'record_id': 'constructed-record',
        'annotation_profile': 'location-only-v1', 'passage_language': 'english',
        'source': {'source_id': 'constructed-source', 'url': 'https://constructed.invalid/example',
            'publisher': 'constructed', 'origin': 'captured_original', 'text': text, 'text_sha256': sha,
            'capture_version': 'fixture', 'article_group': 'constructed-group', 'reuse_status': 'allowed',
            'reuse_terms': 'test fixture', 'admission_status': 'training_admitted', 'extraction_method': 'fixture'},
        'passage_start': 0, 'passage_end': len(text), 'text': text, 'text_sha256': sha,
        'entities': [{'id': f'e{i}', 'start': a, 'end': z, 'text': text[a:z], 'label': label} for i, (a, z, label) in enumerate(spans)],
        'facts': [], 'relations': [], 'annotation_revision': 'fixture', 'quality': 'silver',
        'teacher': 'constructed', 'reviewer': 'constructed', 'review_status': 'accepted', 'complete': complete, 'split': 'train'}


@pytest.mark.parametrize('text,spans', [
    ('Elm Road southbound is flooded.', [(0, 8, 'ROAD')]),
    ('Elm Road corner Pine Street.', [(0, 8, 'ROAD'), (16, 27, 'ROAD')]),
    ('Barangay Peña-an is flooded.', [(0, 16, 'BARANGAY')]),
    ('Purok 1 and 2 are flooded.', [(0, 7, 'LOCAL_AREA'), (12, 13, 'LOCAL_AREA')]),
    ('Sitio Uno is flooded.', [(0, 9, 'LOCAL_AREA')]),
    ('Elm Road, Elm Road.', [(0, 8, 'ROAD'), (10, 18, 'ROAD')]),
    ('Southbound vehicles stopped.', []),
])
def test_constructed_boundaries_unicode_shared_numbers_and_reload(text, spans, tmp_path):
    import spacy
    from training.flood_ner.successor_experiment_worker import qualify_records
    from training.flood_ner.successor_export_worker import serialize
    tokenizer = spacy.blank('xx').tokenizer
    row = record(text, spans)
    parsed = qualify_records([row], tokenizer)
    # Serializer requires both partitions, so duplicate only as a constructed dev fixture.
    dev = deepcopy(row); dev.update(record_id='constructed-dev', split='dev')
    parsed += qualify_records([dev], tokenizer)
    serialize(parsed, tokenizer, tokenizer.to_bytes(exclude=['vocab']), tmp_path, 'development')
    assert w.verify_serialization(tmp_path / 'train.spacy', parsed[:1], tokenizer) == 1


@pytest.mark.parametrize('mutation', ['missing', 'null', 'incomplete', 'type', 'offset', 'overlap', 'use'])
def test_unknown_references_are_not_negatives_or_automatically_corrected(mutation):
    import spacy
    from training.flood_ner.successor_experiment_worker import qualify_records
    row = record('Elm Road is flooded.', [(0, 8, 'ROAD')])
    if mutation == 'missing': row.pop('entities')
    if mutation == 'null': row['entities'] = None
    if mutation == 'incomplete': row.update(entities=[], complete=False)
    if mutation == 'type': row['entities'][0]['label'] = 'UNKNOWN'
    if mutation == 'offset': row['entities'][0]['start'] = 1
    if mutation == 'overlap': row['entities'].append(dict(row['entities'][0], id='another'))
    if mutation == 'use': row['source']['reuse_status'] = 'unknown'
    with pytest.raises(ValueError): qualify_records([row], spacy.blank('xx').tokenizer)


def test_worker_denies_initialization_predictions_updates_and_transport():
    code = '''
import sys
sys.path.insert(0, 'backend')
import spacy
from training.flood_ner.regularization_worker import deny_execution
nlp=spacy.blank('xx')
deny_execution()
import subprocess,socket
for operation in (lambda:nlp.initialize(),lambda:nlp.update([]),lambda:nlp('constructed'),lambda:list(nlp.pipe(['constructed'])),lambda:subprocess.run(['unreachable']),lambda:socket.create_connection(('constructed.invalid',80))):
 try:operation()
 except RuntimeError:pass
 else:raise AssertionError('forbidden capability allowed')
print('constructed qualification guards passed')
'''
    process = subprocess.run([sys.executable, '-B', '-c', code], cwd=ROOT, capture_output=True)
    assert process.returncode == 0, process.stderr.decode(errors='replace')


def test_training_flag_not_exposed():
    process = subprocess.run([sys.executable, '-B', str(ROOT / 'backend/training/flood_ner/regularization_experiment.py'),
                              '--start-training'], capture_output=True)
    assert process.returncode == 2 and b'unrecognized arguments' in process.stderr
