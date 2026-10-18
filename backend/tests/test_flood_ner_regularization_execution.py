"""Constructed bounded execution, raw scoring and portable CPU model fixtures."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from training.flood_ner import regularization_experiment_execution as e
from training.flood_ner import regularization_development_worker as w
from training.flood_ner.corrected_experiment_execution import check_selection

spec = importlib.util.spec_from_file_location('v21_constructed', Path(__file__).with_name('test_flood_ner_regularization_experiment.py'))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


def sequence(tmp_path, modes):
    called = []
    def dispatch(seed, output):
        assert (tmp_path / f'seed-{seed}-dispatch.json').is_file()
        called.append(seed)
        if modes[seed] == 'failure':
            output.mkdir(); (output / 'partial.log').write_text('preserve')
            raise ValueError('constructed failure')
        return {'seed': seed, 'validation': fixtures.fixture_score(mode=modes[seed])}
    return called, dispatch


@pytest.mark.parametrize('mode', ['control', 'drop_ROAD', 'drop_LOCAL_AREA'])
def test_screen_failure_dispatches_only_seed_zero(tmp_path, mode):
    calls, dispatch = sequence(tmp_path, [mode])
    result = e.run_sequence(tmp_path, fixtures.baseline(), dispatch, lambda: None)
    assert calls == [0] and result['schedule']['retained'] == 'control'
    assert result['schedule']['state'] == 'screening_failed'
    assert not (tmp_path / 'seed-1-dispatch.json').exists()


@pytest.mark.parametrize('modes,retained', [(['perfect'] * 3, 'stronger_weight_decay'),
    (['perfect', 'drop_ROAD', 'drop_ROAD'], 'control'),
    (['perfect', 'drop_LOCAL_AREA', 'drop_LOCAL_AREA'], 'control')])
def test_three_run_retention_uses_means(tmp_path, modes, retained):
    calls, dispatch = sequence(tmp_path, modes)
    result = e.run_sequence(tmp_path, fixtures.baseline(), dispatch, lambda: None)
    assert calls == [0, 1, 2] and result['schedule']['retained'] == retained
    assert result['candidate']['sample_stddev'] is not None
    assert not (tmp_path / 'seed-3-dispatch.json').exists()


@pytest.mark.parametrize('failed_seed', [0, 1, 2])
def test_failure_preserves_partial_evidence_and_never_continues(tmp_path, failed_seed):
    calls, dispatch = sequence(tmp_path, ['perfect'] * failed_seed + ['failure'])
    with pytest.raises(ValueError, match='constructed failure'):
        e.run_sequence(tmp_path, fixtures.baseline(), dispatch, lambda: None)
    assert calls == list(range(failed_seed + 1))
    assert e.read(tmp_path / 'stopped-on-failure.json')['retained'] == 'control'
    assert (tmp_path / f'runs/stronger-weight-decay-seed-{failed_seed}/partial.log').read_text() == 'preserve'
    with pytest.raises(FileExistsError):
        e.run_sequence(tmp_path, fixtures.baseline(), dispatch, lambda: None)
    assert calls == list(range(failed_seed + 1))


def test_occupied_destination_and_input_failure_prevent_dispatch(tmp_path):
    (tmp_path / 'runs').mkdir()
    with pytest.raises(FileExistsError):
        e.run_sequence(tmp_path, fixtures.baseline(), lambda *a: pytest.fail('dispatch'), lambda: None)
    empty = tmp_path / 'new'; empty.mkdir()
    def fail(): raise ValueError('binding changed')
    with pytest.raises(ValueError, match='binding changed'):
        e.run_sequence(empty, fixtures.baseline(), lambda *a: pytest.fail('dispatch'), fail)
    assert not (empty / 'seed-0-dispatch.json').exists()


@pytest.mark.parametrize('bad', [float('nan'), float('inf'), .12345])
def test_invalid_scores_stop_before_next_seed(tmp_path, bad):
    def dispatch(seed, output):
        row = fixtures.fixture_score(mode='perfect'); row['overall']['f1'] = bad
        return {'seed': seed, 'validation': row}
    with pytest.raises(ValueError):
        e.run_sequence(tmp_path, fixtures.baseline(), dispatch, lambda: None)
    assert not (tmp_path / 'seed-1-dispatch.json').exists()


def test_permanent_claim_and_active_lock_reject_before_training(tmp_path, monkeypatch):
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'; artifacts.mkdir(parents=True)
    bundle = artifacts / e.BUNDLE_NAME; bundle.mkdir()
    e.write_new(bundle / 'baseline-metrics.json', fixtures.baseline())
    monkeypatch.setattr(e, 'verify_authorization', lambda *a: {})
    monkeypatch.setattr(e, 'verify_preserved', lambda *a: 0)
    monkeypatch.setattr(e.protocol, 'verify_portable', lambda *a: None)
    monkeypatch.setattr(e, 'dispatch_one', lambda *a: pytest.fail('training forbidden'))
    output = artifacts / e.OUTPUT_NAME
    lock = artifacts / 'regularization-execution-active.lock'; lock.write_text('other operator')
    with pytest.raises(FileExistsError): e.execute(tmp_path, output, tmp_path, 'unused')
    assert lock.read_text() == 'other operator' and not output.exists()
    lock.unlink()  # Constructed fixture owned by this test only.
    claim = artifacts / ('regularization-execution-claim-' + e.EXPERIMENT_SHA + '.json')
    claim.write_text('original claim')
    with pytest.raises(FileExistsError): e.execute(tmp_path, output, tmp_path, 'unused')
    assert claim.read_text() == 'original claim' and not output.exists()


@pytest.fixture
def authorization(tmp_path, monkeypatch):
    bindings = {}
    for name in e.NEW_BINDINGS:
        p = tmp_path / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'# constructed')
        bindings[name] = e.digest(p)
    ledger = tmp_path / 'preservation.json'; e.write_new(ledger, {})
    preflight = tmp_path / 'preflight.json'
    e.write_new(preflight, {'state': 'verified_read_only', 'gpu_verified': True,
                'configuration_schema_verified': True, 'training_started': False})
    grant = {'schema': 'lanes-v21-execution-authorization-v1', 'explicit_training_authorization': True,
        'maximum_runs': 3, 'experiment_sha256': e.EXPERIMENT_SHA, 'source_bindings': bindings,
        'preservation': {'path': 'preservation.json', 'sha256': e.digest(ledger)},
        'preflight': {'path': 'preflight.json', 'sha256': e.digest(preflight)}, 'checkout_commit': 'constructed-head'}
    path = tmp_path / 'authorization.json'; e.write_new(path, grant)
    monkeypatch.setattr(e.subprocess, 'check_output', lambda args, **kw:
        b'roi-branch' if args[1] == 'branch' else b'constructed-head')
    return path, grant


@pytest.mark.parametrize('mutation', ['none', 'manifest', 'source', 'preflight', 'authorization', 'maximum'])
def test_authorization_and_evidence_tampering(tmp_path, authorization, mutation):
    path, grant = authorization; expected = e.digest(path)
    if mutation == 'manifest': grant['experiment_sha256'] = '0' * 64
    if mutation == 'maximum': grant['maximum_runs'] = 4
    if mutation in ('manifest', 'maximum'):
        path.write_text(json.dumps(grant)); expected = e.digest(path)
    if mutation == 'authorization': path.write_text('{}')
    if mutation == 'source': (tmp_path / next(iter(e.NEW_BINDINGS))).write_bytes(b'changed')
    if mutation == 'preflight': (tmp_path / 'preflight.json').write_text('{}')
    if mutation == 'none': assert e.verify_authorization(tmp_path, path, expected) == grant
    else:
        with pytest.raises(ValueError): e.verify_authorization(tmp_path, path, expected)


def documents():
    data = [('english', 'Peña Road', [(0, 4, 'CITY')]), ('taglish', 'Bayan', [])]
    docs, metadata = [], []
    for index, (lang, text, spans) in enumerate(data):
        rid = str(index)
        docs.append(SimpleNamespace(text=text, user_data={'record_id': rid}, ents=[SimpleNamespace(
            start_char=a, end_char=b, label_=label) for a, b, label in spans]))
        metadata.append({'record_id': rid, 'partition': 'dev', 'language': lang,
                         'passage_sha256': hashlib.sha256(text.encode()).hexdigest(), 'is_negative': not spans})
    return docs, metadata


@pytest.mark.parametrize('mutation', ['id', 'duplicate', 'hash', 'negative', 'label', 'offset'])
def test_development_join_rejects_wrong_membership_and_unicode_spans(monkeypatch, mutation):
    monkeypatch.setitem(w.protocol.COUNTS, 'dev', 2)
    docs, metadata = documents()
    if mutation == 'id': docs[0].user_data['record_id'] = 'unknown'
    if mutation == 'duplicate': docs[1].user_data['record_id'] = '0'
    if mutation == 'hash': metadata[0]['passage_sha256'] = 'bad'
    if mutation == 'negative': metadata[0]['is_negative'] = True
    if mutation == 'label': docs[0].ents[0].label_ = 'UNSUPPORTED'
    if mutation == 'offset': docs[0].ents[0].end_char = 999
    with pytest.raises(ValueError): w.join_documents(docs, metadata, 'dev')


def test_only_raw_strings_reach_inference_and_support_is_explicit(monkeypatch):
    monkeypatch.setitem(w.protocol.COUNTS, 'dev', 2)
    docs, metadata = documents()
    class Model:
        def pipe(self, texts, batch_size):
            assert texts == ['Peña Road', 'Bayan'] and batch_size == 8
            assert all(isinstance(t, str) for t in texts)
            return docs
    score, predictions = w.score_documents(Model(), docs, metadata, 'dev')
    assert score['overall']['f1'] == 1
    assert score['labels']['ROAD']['f1'] is None
    assert score['negative_passages']['overall']['false_positive_passages'] == 0
    assert predictions['0'] == [(0, 4, 'CITY')]


def test_real_constructed_cpu_loading_and_frozen_tokenizer(tmp_path):
    import spacy
    resources = tmp_path / 'resources'; (resources / 'vocab').mkdir(parents=True)
    nlp = spacy.blank('xx'); nlp.vocab.to_disk(resources / 'vocab')
    while len(list(resources.rglob('*'))) < 24:
        (resources / f'constructed-{len(list(resources.rglob("*")))}.bin').write_bytes(b'constructed')
    files = [p for p in resources.rglob('*') if p.is_file()]
    assert len(files) == 23
    package = tmp_path / 'package'; package.mkdir()
    token = nlp.tokenizer.to_bytes(exclude=['vocab']); (package / 'tokenizer.bin').write_bytes(token)
    contract = {'model': 'tl_calamancy_md', 'version': '0.1.0', 'download_complete': True,
        'revision': '51a40433059d8a2c25b98a48eca854f8789a491a', 'model_dir': str(resources),
        'files': [{'path': p.relative_to(resources).as_posix(), 'bytes': p.stat().st_size, 'sha256': e.digest(p)} for p in files]}
    e.write_new(package / 'model-contract.json', contract)
    for label in e.protocol.LABELS: nlp.add_pipe('ner') if not nlp.has_pipe('ner') else None; nlp.get_pipe('ner').add_label(label)
    nlp.initialize()  # Random constructed model only; no corpus/training examples.
    nlp.config['nlp']['tokenizer'] = {'@tokenizers': 'lanes.qualified_tokenizer.v1',
        'model_manifest': str(package / 'model-contract.json'), 'manifest_sha256': e.digest(package / 'model-contract.json'),
        'tokenizer_file': str(package / 'tokenizer.bin'), 'tokenizer_sha256': e.digest(package / 'tokenizer.bin')}
    model = tmp_path / 'model'; nlp.to_disk(model)
    output = tmp_path / 'load-check'; output.mkdir()
    loaded, handles = w.load_model(ROOT, model, package, resources, output)
    assert loaded.pipe_names == ['ner'] and set(loaded.get_pipe('ner').labels) == e.protocol.LABELS
    assert loaded.tokenizer.to_bytes(exclude=['vocab']) == token
