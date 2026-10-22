"""Qualification gates must reject forged success and nonconstructed input."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner import gpu_preflight as g
from training.flood_ner.preflight import load_cases, MODEL_REVISION

CASES = Path(__file__).resolve().parents[1] / 'training/flood_ner/configs/preflight_constructed_cases.jsonl'


def payload():
    cases = load_cases(CASES)
    predictions = [{'case_id': c.case_id, 'text_sha256': c.text_sha256, 'entities': []} for c in cases]
    return {'mode': 'gpu', 'python_version': '3.11.17', 'spacy_version': '3.7.5', 'model_revision': MODEL_REVISION,
            'baseline_predictions': predictions, 'trial_predictions': deepcopy(predictions),
            'cupy_kernel_passed': True, 'torch_cuda_passed': True, 'spacy_gpu_selected': True, 'parameters_on_gpu': True,
            'trial_labels': ['ROAD', 'LANDMARK', 'LOCAL_AREA', 'BARANGAY', 'CITY', 'PROVINCE'],
            'training_steps': [{'batch_size': n, 'loss': 1.0, 'elapsed_ms': 2.0} for n in (1, 4, 8)]}


@pytest.mark.parametrize('mutation', ['mode', 'python', 'spacy', 'model', 'cuda', 'cpu_parameters', 'labels',
                                    'case_hash', 'case_count', 'entity', 'nan', 'negative_loss', 'missing_step',
                                    'trial_identity', 'trial_entity'])
def test_rejects_forged_qualification(mutation):
    result = payload()
    if mutation == 'mode': result['mode'] = 'cpu'
    elif mutation == 'python': result['python_version'] = '3.14.6'
    elif mutation == 'spacy': result['spacy_version'] = '3.8.0'
    elif mutation == 'model': result['model_revision'] = 'main'
    elif mutation == 'cuda': result['torch_cuda_passed'] = False
    elif mutation == 'cpu_parameters': result['parameters_on_gpu'] = False
    elif mutation == 'labels': result['trial_labels'] = ['LOC']
    elif mutation == 'case_hash': result['baseline_predictions'][0]['text_sha256'] = '0' * 64
    elif mutation == 'case_count': result['baseline_predictions'].pop()
    elif mutation == 'entity': result['baseline_predictions'][0]['entities'] = [{'start': 0, 'end': 500, 'text': 'bad', 'label': 'LOC'}]
    elif mutation == 'nan': result['training_steps'][0]['loss'] = float('nan')
    elif mutation == 'negative_loss': result['training_steps'][0]['loss'] = -1
    elif mutation == 'missing_step': result['training_steps'].pop()
    elif mutation == 'trial_identity': result['trial_predictions'][0]['case_id'] = 'news-case'
    else: result['trial_predictions'][0]['entities'] = [{'start': 0, 'end': 1, 'text': 'F', 'label': 'LOC'}]
    with pytest.raises(ValueError):
        g.validate_worker(result, load_cases(CASES), 'gpu')


def test_fixed_probe_hash_and_valid_gpu_result():
    assert g.digest(CASES) == g.CASES_SHA256
    g.validate_worker(payload(), load_cases(CASES), 'gpu')


def test_existing_or_external_destinations_are_refused(tmp_path):
    for output in (tmp_path / 'elsewhere', tmp_path / 'backend/training/flood_ner/artifacts'):
        with pytest.raises(ValueError, match='new directory'):
            g.run(tmp_path / 'python.exe', tmp_path / 'manifest.json', output, tmp_path)


def test_main_python_is_refused(tmp_path):
    with pytest.raises(ValueError, match='isolated research Python'):
        g.run(Path(sys.executable), tmp_path / 'manifest.json', tmp_path / 'backend/training/flood_ner/artifacts/new', tmp_path)


def test_changed_or_replaced_constructed_probes_are_refused(tmp_path):
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'
    artifacts.mkdir(parents=True)
    exe = artifacts / 'python.exe'
    exe.write_bytes(b'never execute')
    cases = tmp_path / 'backend/training/flood_ner/configs/preflight_constructed_cases.jsonl'
    cases.parent.mkdir(parents=True)
    cases.write_text(json.dumps({'origin': 'constructed_fixture', 'text': 'unreviewed substitute'}))
    with pytest.raises(ValueError, match='fixed constructed'):
        g.run(exe, tmp_path / 'manifest.json', artifacts / 'new', tmp_path)
    assert not (artifacts / 'new').exists()


@pytest.mark.parametrize('value', [None, [], 'passed'])
def test_nonobject_output_is_rejected(value):
    with pytest.raises(ValueError, match='must be an object'):
        g.validate_worker(value, load_cases(CASES), 'gpu')


def test_worker_failure_preserves_evidence_and_never_qualifies(tmp_path, monkeypatch):
    import subprocess
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'
    artifacts.mkdir(parents=True)
    exe = artifacts / 'python.exe'
    exe.write_bytes(b'never execute')
    model_manifest = artifacts / 'model_manifest.json'
    model_manifest.write_text('{}')
    cases = tmp_path / 'backend/training/flood_ner/configs/preflight_constructed_cases.jsonl'
    cases.parent.mkdir(parents=True)
    cases.write_bytes(CASES.read_bytes())
    monkeypatch.setattr(g, 'verify_model', lambda *args: ({'revision': MODEL_REVISION}, artifacts / 'model'))
    monkeypatch.setattr(g.subprocess, 'run', lambda *args, **kwargs: subprocess.CompletedProcess([], 1, b'', b'CUDA allocation failed'))
    output = artifacts / 'new'
    result = g.run(exe, model_manifest, output, tmp_path)
    assert result['state'] == 'failed' and not result['gpu_environment_qualified']
    assert result['news_samples_processed'] == 0 and not result['source_admission_changed']
    assert 'CUDA allocation failed' in result['error']
    assert (output / 'gpu-stderr.log').read_bytes() == b'CUDA allocation failed'
    assert json.loads((output / 'report.json').read_text()) == result

@pytest.mark.parametrize('mode', ['gpu', 'cpu'])
@pytest.mark.parametrize('captured', [True, False])
def test_timeout_retains_partial_diagnostics_and_hashes(tmp_path, monkeypatch, mode, captured):
    import hashlib
    import subprocess
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'
    artifacts.mkdir(parents=True)
    exe = artifacts / 'python.exe'
    exe.write_bytes(b'never execute')
    model_manifest = artifacts / 'model_manifest.json'
    model_manifest.write_text('{}')
    cases = tmp_path / 'backend/training/flood_ner/configs/preflight_constructed_cases.jsonl'
    cases.parent.mkdir(parents=True)
    cases.write_bytes(CASES.read_bytes())
    monkeypatch.setattr(g, 'verify_model', lambda *args: ({'revision': MODEL_REVISION}, artifacts / 'model'))
    stdout = b'partial worker output' if captured else None
    stderr = 'CUDA diagnostic: pagsusuri'.encode('utf-8') if captured else None
    def execute(command, **kwargs):
        if command[-1] == mode:
            raise subprocess.TimeoutExpired(command, kwargs['timeout'], output=stdout, stderr=stderr)
        return subprocess.CompletedProcess(command, 0, json.dumps(payload()).encode('utf-8'), b'')
    monkeypatch.setattr(g.subprocess, 'run', execute)
    output = artifacts / 'timeout'
    result = g.run(exe, model_manifest, output, tmp_path)
    assert result['state'] == 'failed' and not result['gpu_environment_qualified']
    assert result['news_samples_processed'] == 0 and not result['source_admission_changed']
    assert 'timed out' in result['error']
    for stream, expected in [('stdout', stdout or b''), ('stderr', stderr or b'')]:
        name = f'{mode}-{stream}.log'
        assert (output / name).read_bytes() == expected
        assert result['files'][name] == hashlib.sha256(expected).hexdigest()
    assert json.loads((output / 'report.json').read_text()) == result
