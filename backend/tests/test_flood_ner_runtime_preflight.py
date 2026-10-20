"""Constructed metadata/assets and mocked children; no private corpus or inference."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner import runtime_preflight as r
from training.flood_ner import runtime_probe_worker as w


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')
    return r.digest(path)


@pytest.fixture
def assets(tmp_path):
    model = tmp_path / 'models/control-seed-0/model'
    for name in r.MODEL_FILES:
        put(model / name, {'fictional': name})
    put(model / 'meta.json', {'pipeline': ['ner'], 'labels': {'ner': sorted(r.LABELS)},
                             'vectors': {'mode': 'floret'}})
    files = {name: r.digest(model / name) for name in r.MODEL_FILES}
    manifest = tmp_path / 'MANIFEST.json'
    sha = put(manifest, {'schema': 'lanes-v19-scoped-models-v1', 'retained': 'control',
        'primary': 'control-seed-0', 'runs': [{'name': 'control-seed-0',
        'model': 'models/control-seed-0/model', 'files': files}]})
    base = tmp_path / 'base'
    entries = []
    for i in range(23):
        p = base / str(i); h = put(p, {'fictional': i})
        entries.append({'path': str(i), 'bytes': p.stat().st_size, 'sha256': h})
    resource = tmp_path / 'resource.json'
    rh = put(resource, {'model': 'tl_calamancy_md', 'version': '0.1.0',
        'revision': '51a40433059d8a2c25b98a48eca854f8789a491a',
        'download_complete': True, 'files': entries})
    return [manifest, sha, resource, rh, base]


def test_authenticate_exact_primary_only(assets):
    result = r.authenticate(*assets)
    assert len(result['model_files']) == 11 and len(result['resource_files']) == 23
    assert result['labels'] == sorted(r.LABELS)


@pytest.mark.parametrize('position', [1, 3])
def test_stale_manifest_binding(assets, position):
    assets[position] = '0' * 64
    with pytest.raises(ValueError, match='stale'): r.authenticate(*assets)


@pytest.mark.parametrize('change', ['missing', 'changed', 'extra', 'wrong_labels', 'wrong_vectors', 'duplicate_primary'])
def test_checkpoint_rejection(assets, change):
    p = assets[0].parent / 'models/control-seed-0/model'
    if change == 'missing': (p / 'ner/model').unlink()
    if change == 'changed': (p / 'ner/model').write_bytes(b'changed')
    if change == 'extra': (p / 'extra').write_bytes(b'extra')
    if change in ('wrong_labels', 'wrong_vectors'):
        meta = json.loads((p / 'meta.json').read_text())
        if change == 'wrong_labels': meta['labels']['ner'] = ['LOC']
        else: meta['vectors']['mode'] = 'default'
        put(p / 'meta.json', meta)
        m = json.loads(assets[0].read_text())
        m['runs'][0]['files']['meta.json'] = r.digest(p / 'meta.json')
        assets[1] = put(assets[0], m)
    if change == 'duplicate_primary':
        m = json.loads(assets[0].read_text()); m['runs'].append(deepcopy(m['runs'][0]))
        assets[1] = put(assets[0], m)
    with pytest.raises(ValueError): r.authenticate(*assets)


@pytest.mark.parametrize('change', ['duplicate', 'size', 'revision', 'incomplete'])
def test_resource_binding(assets, change):
    m = json.loads(assets[2].read_text())
    if change == 'duplicate': m['files'][-1] = m['files'][0]
    if change == 'size': m['files'][0]['bytes'] += 1
    if change == 'revision': m['revision'] = 'changed'
    if change == 'incomplete': m['download_complete'] = False
    assets[3] = put(assets[2], m)
    with pytest.raises(ValueError): r.authenticate(*assets)


@pytest.mark.parametrize('name', ['../escape', '/absolute', 'C:/escape', 'a\\b', '', './a', 'a//b'])
def test_path_escape(tmp_path, name):
    with pytest.raises(ValueError): r.checked_path(tmp_path, name)


def env(system='Windows', python=None, spacy='3.7.5', floret=None):
    return {'ok': True, 'value': {'system': system, 'python': python or [3, 12, 14],
            'packages': {'spacy': spacy, 'floret': floret}}}


def test_prerequisite_success_never_claims_qualification():
    result = r.assess(env('Linux', floret='0.10.5'), {'ok': True, 'value': {'os': 'linux'}},
                      {'ok': True, 'value': {'loaded': True, 'lookup_verified': True}})
    assert result['status'] == 'preflight_passed_qualification_pending'
    for key in ('linux_inference_qualified', 'latency_measured', 'memory_measured',
                'neural_inference_performed', 'training_started', 'application_connected',
                'validation_accessed', 'holdout_accessed'):
        assert result[key] is False


@pytest.mark.parametrize('environment,docker,vocabulary,blocker', [
    ({'ok': False}, {'ok': True, 'value': {'os': 'linux'}}, None, 'backend_interpreter_probe_failed'),
    (env(python=[3, 11]), {'ok': True, 'value': {'os': 'linux'}}, None, 'backend_python_3_12_not_verified'),
    (env(spacy='3.8'), {'ok': True, 'value': {'os': 'linux'}}, None, 'spacy_3_7_5_not_verified'),
    (env(), {'ok': False}, None, 'linux_docker_engine_unavailable'),
    (env(), {'ok': True, 'value': {'os': 'windows'}}, None, 'linux_docker_engine_unavailable'),
    (env(), {'ok': False}, {'ok': True, 'value': {'loaded': False}}, 'backend_vocabulary_load_failed'),
    (env(), {'ok': False}, {'ok': False}, 'backend_vocabulary_load_failed'),
])
def test_actual_blockers(environment, docker, vocabulary, blocker):
    result = r.assess(environment, docker, vocabulary)
    assert result['status'] == 'preflight_blocked' and blocker in result['blockers']


@pytest.mark.parametrize('failure', [OSError('missing'), subprocess.TimeoutExpired(['probe'], 1)])
def test_bounded_child_failure(monkeypatch, failure):
    def run(*a, **k): raise failure
    monkeypatch.setattr(r.subprocess, 'run', run)
    assert r.run_json(['probe']) == {'ok': False, 'error_type': type(failure).__name__}


@pytest.mark.parametrize('rc,out', [(1, '{}'), (0, 'not json'), (0, '[]')])
def test_failed_or_malformed_child(monkeypatch, rc, out):
    monkeypatch.setattr(r.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=rc, stdout=out, stderr='evidence'))
    assert r.run_json(['probe'])['ok'] is False


def test_probe_commands_have_no_application_corpus_or_training(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(r, 'run_json', lambda args, *a: calls.append(args) or {'ok': False})
    r.environment_probe(Path('python')); r.vocabulary_probe(Path('python'), tmp_path); r.docker_probe(Path('docker'))
    assert calls[0][1:4] == ['-I', '-B', '-c']
    assert 'Vocab().from_disk' in calls[1][4] and calls[1][-1] == str(tmp_path / 'vocab')
    for command in calls:
        text = ' '.join(command)
        assert all(s not in text for s in ('spacy.load(', '.initialize(', '.update(', 'app.services', 'train.spacy', 'dev.spacy', 'holdout'))
    assert calls[2][1:3] == ['info', '--format']


def test_output_never_overwrites(tmp_path):
    dest = tmp_path / 'new'
    r.save_new(dest, {'status': 'blocked'}, {'private': True})
    before = {p.name: p.read_bytes() for p in dest.iterdir()}
    with pytest.raises(ValueError, match='new output'): r.save_new(dest, {}, {})
    assert before == {p.name: p.read_bytes() for p in dest.iterdir()}


def test_standalone_floret_is_not_a_required_inference_dependency():
    result = r.assess(env(floret=None), {'ok': True, 'value': {'os': 'linux'}},
                      {'ok': True, 'value': {'loaded': True, 'lookup_verified': True}})
    assert result['blockers'] == []


@pytest.fixture
def probe_request(tmp_path):
    value = {k: 'fictional' for k in w.REQUEST_KEYS}
    value.update(scope='fictional_cpu_runtime_smoke', worker_sha256=r.digest(Path(w.__file__)))
    path = tmp_path / 'request.json'
    return path, value


def test_worker_request_binding(probe_request):
    path, value = probe_request
    sha = put(path, value)
    assert w.checked_request(path, sha) == value


@pytest.mark.parametrize('change', ['scope', 'worker_sha256', 'extra_references', 'extra_holdout', 'extra_predictions'])
def test_worker_rejects_corpus_and_stale_scope(probe_request, change):
    path, value = probe_request
    if change.startswith('extra'): value[change] = []
    else: value[change] = 'changed'
    sha = put(path, value)
    with pytest.raises(ValueError): w.checked_request(path, sha)


def test_worker_stale_request(probe_request):
    path, value = probe_request; put(path, value)
    with pytest.raises(ValueError): w.checked_request(path, '0' * 64)


def test_unicode_repeated_mentions_preserve_offsets():
    text = '  Piña Road / Piña Road\n'
    rows = [SimpleNamespace(label_='ROAD', start_char=2, end_char=11, text='Piña Road'),
            SimpleNamespace(label_='ROAD', start_char=14, end_char=23, text='Piña Road')]
    # Build exact offsets to avoid coupling this test to a hand-counted index.
    for entity, start in zip(rows, (text.index('Piña'), text.rindex('Piña'))):
        entity.start_char = start; entity.end_char = start + len(entity.text)
    assert w.spans(SimpleNamespace(text=text, ents=rows), text) == [[e.start_char, e.end_char, 'ROAD'] for e in rows]


@pytest.mark.parametrize('change', ['label', 'boundary', 'overlap', 'text', 'type'])
def test_worker_rejects_invalid_output(change):
    text = 'Aster Road'
    entity = SimpleNamespace(label_='ROAD', start_char=0, end_char=len(text), text=text)
    rows = [entity]; doc = SimpleNamespace(text=text, ents=rows)
    if change == 'label': entity.label_ = 'ORG'
    if change == 'boundary': entity.end_char += 1
    if change == 'overlap': rows.append(entity)
    if change == 'text': doc.text = text + ' '
    if change == 'type': entity.start_char = False
    with pytest.raises(ValueError): w.spans(doc, text)


def test_worker_training_network_guard_and_fixed_probes():
    with pytest.raises(RuntimeError): w.blocked()
    assert len(w.PROBES) == 4
    assert any('Piña' in text for text in w.PROBES)
    assert any(text.startswith('  ') and text.endswith('\n') for text in w.PROBES)


@pytest.mark.parametrize('relative', ['public', 'artifacts', 'artifacts/../public'])
def test_private_output_boundary(tmp_path, relative):
    with pytest.raises(ValueError): r.private_destination(tmp_path / relative, tmp_path / 'artifacts')


def test_new_private_output_allowed(tmp_path):
    r.private_destination(tmp_path / 'artifacts/new', tmp_path / 'artifacts')
