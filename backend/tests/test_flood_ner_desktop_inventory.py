"""A driver inventory cannot falsely claim training or source-use qualification."""
import hashlib
import json
import subprocess

import pytest

from training.flood_ner import desktop_inventory as d


@pytest.mark.parametrize('text', ['', 'NVIDIA RTX 3060 Ti, 555.12, N/A, 1',
                                  'NVIDIA RTX 3060 Ti, N/A, 8192, 1',
                                  'NVIDIA RTX 3060 Ti, 555.12, 8192, 9000',
                                  'NVIDIA RTX 3060 Ti, 555.12, 8192, -1',
                                  'NVIDIA RTX 3060 Ti, 555.12, 8192, 1, extra',
                                  'NVIDIA RTX 3060 Ti, 555.12, 8192 MiB, 1',
                                  'NVIDIA RTX 3060 Ti, 555.12, 0, 0'])
def test_reject_unknown_or_invalid_driver_memory(text):
    with pytest.raises(ValueError):
        d.parse_gpus(text)


def test_multiple_devices_do_not_select_laptop_or_insufficient_vram():
    rows = d.parse_gpus('NVIDIA GeForce MX330, 555.12, 2048, 1200\nNVIDIA GeForce RTX 3060 Ti, 555.12, 8192, 7000\nRTX 3060 Ti, 555.12, 4096, 3000\n')
    assert [r['matches_reported_target'] for r in rows] == [False, True, False]


def test_missing_tool_is_explicit_not_a_pass(monkeypatch):
    monkeypatch.setattr(d.shutil, 'which', lambda name: None)
    result = d.collect_inventory()
    assert result['state'] == 'inventory_failed' and result['errors']
    assert result['gpu_training_qualified'] is False


@pytest.mark.parametrize('failure', [subprocess.TimeoutExpired(['nvidia-smi'], 15),
                                     subprocess.CalledProcessError(9, ['nvidia-smi'], stderr='driver unavailable'),
                                     OSError('driver executable unavailable')])
def test_failed_process_is_retained(monkeypatch, failure):
    monkeypatch.setattr(d.shutil, 'which', lambda name: 'constructed-nvidia-smi')
    def fail(*args, **kwargs):
        raise failure
    monkeypatch.setattr(d.subprocess, 'run', fail)
    result = d.collect_inventory()
    assert result['state'] == 'inventory_failed' and result['errors']
    if isinstance(failure, subprocess.CalledProcessError):
        assert result['query']['returncode'] == 9
        assert result['query']['stderr'] == 'driver unavailable'


@pytest.mark.parametrize('device,state', [('NVIDIA GeForce RTX 3060 Ti', 'target_inventory_ready'),
                                         ('NVIDIA GeForce MX330', 'awaiting_target_desktop')])
def test_hardware_match_never_claims_cuda_training_or_admission(monkeypatch, device, state):
    monkeypatch.setattr(d.shutil, 'which', lambda name: 'constructed-nvidia-smi')
    def query(argv, **kwargs):
        assert argv == ['constructed-nvidia-smi', *d.QUERY]
        assert kwargs['timeout'] == 15 and kwargs['check'] is True
        return subprocess.CompletedProcess(argv, 0, f'{device}, 555.12, 8192, 7000\n', '')
    monkeypatch.setattr(d.subprocess, 'run', query)
    result = d.collect_inventory()
    assert result['state'] == state
    for key in ['gpu_training_qualified','source_admission_changed','packages_installed','model_loaded','news_processed']:
        assert result[key] is False


@pytest.mark.parametrize('where', ['outside','artifact-root','existing','symlink'])
def test_unsafe_or_existing_output_refused_before_query(tmp_path, monkeypatch, where):
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'
    artifacts.mkdir(parents=True)
    output = artifacts / 'new'
    if where == 'outside': output = tmp_path / 'unrelated'
    if where == 'artifact-root': output = artifacts
    if where == 'existing': output.mkdir()
    if where == 'symlink':
        outside = tmp_path / 'outside'; outside.mkdir()
        try: output.symlink_to(outside, target_is_directory=True)
        except OSError: pytest.skip('symlink creation unavailable')
    def forbidden(): raise AssertionError('unsafe output must not query hardware')
    monkeypatch.setattr(d, 'collect_inventory', forbidden)
    with pytest.raises(ValueError): d.save_inventory(output, tmp_path)


def test_failed_inventory_is_saved_with_bound_hash(tmp_path, monkeypatch):
    output = tmp_path / 'backend/training/flood_ner/artifacts/new'
    monkeypatch.setattr(d, 'collect_inventory', lambda: {'state':'inventory_failed','system':{},'errors':['driver missing']})
    result = d.save_inventory(output, tmp_path)
    assert result['errors'] == ['driver missing']
    manifest = json.loads((output / 'manifest.json').read_text())
    assert manifest['files']['inventory.json'] == hashlib.sha256((output / 'inventory.json').read_bytes()).hexdigest()
    assert manifest['gpu_training_qualified'] is False
    with pytest.raises(ValueError): d.save_inventory(output, tmp_path)
