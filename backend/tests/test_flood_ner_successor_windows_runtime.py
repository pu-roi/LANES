"""Constructed Windows bootstrap checks; no model, corpus or training access."""
import builtins
import gc
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import weakref

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner import successor_training as trainer


def test_windows_lookup_uses_only_interpreter_libraries_and_retains_handles(tmp_path, monkeypatch):
    site = tmp_path / 'Lib/site-packages'
    directories = [site / p for p in ('torch/lib', 'nvidia/cuda_runtime/bin', 'nvidia/cuda_nvrtc/bin')]
    for directory in directories:
        directory.mkdir(parents=True)
    monkeypatch.setattr(trainer.sys, 'platform', 'win32')
    monkeypatch.setattr(trainer.sys, 'prefix', str(tmp_path))
    monkeypatch.setenv('CUDA_PATH', 'unrelated-system-toolkit')
    calls = []
    handles = [SimpleNamespace(close=lambda: None) for _ in directories]
    def add(directory):
        calls.append(directory)
        return handles[len(calls) - 1]
    monkeypatch.setattr(trainer.os, 'add_dll_directory', add, raising=False)
    assert trainer.prepare_gpu_runtime() == handles
    assert calls == [str(p) for p in directories]
    assert trainer.os.environ['CUDA_PATH'] == str(site / 'nvidia/cuda_runtime')


def test_non_windows_bootstrap_does_not_change_environment(monkeypatch):
    monkeypatch.setattr(trainer.sys, 'platform', 'linux')
    monkeypatch.setenv('CUDA_PATH', 'existing')
    monkeypatch.setattr(trainer.os, 'add_dll_directory', lambda *_: pytest.fail('Windows-only call'), raising=False)
    assert trainer.prepare_gpu_runtime() == []
    assert trainer.os.environ['CUDA_PATH'] == 'existing'


def test_missing_library_directory_fails_before_changing_lookup(tmp_path, monkeypatch):
    monkeypatch.setattr(trainer.sys, 'platform', 'win32')
    monkeypatch.setattr(trainer.sys, 'prefix', str(tmp_path))
    monkeypatch.setenv('CUDA_PATH', 'existing')
    monkeypatch.setattr(trainer.os, 'add_dll_directory', lambda *_: pytest.fail('partial setup'), raising=False)
    with pytest.raises(ValueError, match='missing qualified CUDA library directory'):
        trainer.prepare_gpu_runtime()
    assert trainer.os.environ['CUDA_PATH'] == 'existing'


def test_dll_registration_failure_closes_partial_handles(tmp_path, monkeypatch):
    for name in ('torch/lib', 'nvidia/cuda_runtime/bin', 'nvidia/cuda_nvrtc/bin'):
        (tmp_path / 'Lib/site-packages' / name).mkdir(parents=True)
    monkeypatch.setattr(trainer.sys, 'platform', 'win32')
    monkeypatch.setattr(trainer.sys, 'prefix', str(tmp_path))
    closed = []
    def add(directory):
        if directory.endswith(str(Path('torch/lib'))):
            return SimpleNamespace(close=lambda: closed.append(True))
        raise OSError('constructed DLL failure')
    monkeypatch.setattr(trainer.os, 'add_dll_directory', add, raising=False)
    with pytest.raises(ValueError, match='constructed DLL failure'):
        trainer.prepare_gpu_runtime()
    assert closed == [True]


def test_probe_bootstraps_before_torch_and_spacy_and_preserves_isolation(tmp_path, monkeypatch):
    calls = []
    def run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps({
            'python_version': '3.11.17', 'spacy_version': '3.7.5'}))
    monkeypatch.setattr(trainer.subprocess, 'run', run)
    trainer.probe(tmp_path / 'python.exe', gpu=True)
    args, kwargs = calls[0]
    code = args[-1]
    assert args[1:4] == ['-I', '-B', '-c']
    assert code.index('dll_handles=module.prepare_gpu_runtime()') < code.index('import torch') < code.index('import spacy')
    assert str(Path(trainer.__file__).resolve()) in code.replace('\\\\', '\\')
    assert kwargs['timeout'] == 60
    assert not any(token in code for token in ('spacy.load', 'cli.train', 'nlp('))


@pytest.mark.parametrize('timeout', [False, True])
def test_probe_exposes_bounded_failure_diagnostics_without_fallback(tmp_path, monkeypatch, timeout):
    def run(*args, **kwargs):
        if timeout:
            raise subprocess.TimeoutExpired(args[0], 60, stderr=b'constructed missing CUDA DLL')
        return SimpleNamespace(returncode=1, stdout='', stderr='constructed missing CUDA DLL')
    monkeypatch.setattr(trainer.subprocess, 'run', run)
    with pytest.raises(ValueError, match='no CPU fallback\nconstructed missing CUDA DLL'):
        trainer.probe(tmp_path / 'python.exe', gpu=True)


def test_internal_training_bootstraps_its_own_process_and_keeps_handles(tmp_path, monkeypatch):
    output = tmp_path / 'backend/training/flood_ner/artifacts/new-run'
    output.mkdir(parents=True)
    (output.parent / 'successor-training-active.lock').write_text(str(output), encoding='utf-8')
    registry = tmp_path / 'backend/training/flood_ner/experiment_registry.py'
    registry.write_text('from spacy.cli.train import train\n', encoding='utf-8')
    request = {'checkout': str(tmp_path), 'output': str(output), 'preparation': str(tmp_path),
               'model_dir': str(tmp_path), 'explicit_training_action': True,
               'handoff_sha256': 'digest', 'config_sha256': 'digest'}
    monkeypatch.setattr(trainer, 'read', lambda _: request)
    monkeypatch.setattr(trainer, 'digest', lambda _: 'digest')
    monkeypatch.setattr(trainer, 'verify_package', lambda *a: None)
    monkeypatch.setattr(trainer, 'verify_gpu', lambda *a: None)
    monkeypatch.setattr(trainer, 'probe', lambda *a, **k: {})
    events, references = [], []
    class Handle:
        pass
    def bootstrap():
        events.append('bootstrap')
        handle = Handle()
        references.append(weakref.ref(handle))
        return [handle]
    monkeypatch.setattr(trainer, 'prepare_gpu_runtime', bootstrap)
    def train(*a, **k):
        gc.collect()
        assert references[0]() is not None
        assert k['use_gpu'] == 0
        events.append('train')
    original_import = builtins.__import__
    def importing(name, *a, **k):
        if name == 'torch':
            events.append('torch')
            return SimpleNamespace()
        if name == 'spacy.cli.train':
            assert events[:2] == ['bootstrap', 'torch']
            events.append('spacy')
            return SimpleNamespace(train=train)
        return original_import(name, *a, **k)
    monkeypatch.setattr(builtins, '__import__', importing)
    trainer.internal_training(tmp_path / 'request.json')
    assert events == ['bootstrap', 'torch', 'spacy', 'spacy', 'train']


def test_schema_validation_bootstraps_before_gpu_imports_and_keeps_handles(tmp_path, monkeypatch):
    import spacy.util
    import importlib.util
    events, references = [], []
    class Handle:
        pass
    def bootstrap():
        events.append('bootstrap')
        handle = Handle()
        references.append(weakref.ref(handle))
        return [handle]
    monkeypatch.setattr(trainer, 'prepare_gpu_runtime', bootstrap)
    monkeypatch.setattr(trainer, 'verify_template', lambda *a: None)
    monkeypatch.setattr(trainer, 'digest', lambda *a: 'constructed')
    monkeypatch.setattr(trainer, 'render_config', lambda *a: '[constructed]\nvalue = 1\n')
    for seed in range(3):
        (tmp_path / f'train-seed-{seed}.cfg').write_text('constructed', encoding='utf-8')
    fake_spec = SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module: None))
    monkeypatch.setattr(importlib.util, 'spec_from_file_location', lambda *a: fake_spec)
    monkeypatch.setattr(importlib.util, 'module_from_spec', lambda *a: SimpleNamespace())
    def resolve(*a, **k):
        gc.collect()
        assert references[0]() is not None
        events.append('resolve')
        return {'training': {'optimizer': SimpleNamespace(nr_update=0)}}
    monkeypatch.setattr(spacy.util.registry, 'resolve', resolve)
    original_import = builtins.__import__
    def importing(name, *a, **k):
        if name in ('torch', 'spacy'):
            events.append(name)
        return original_import(name, *a, **k)
    monkeypatch.setattr(builtins, '__import__', importing)
    result = trainer.validate_config_schemas(tmp_path)
    assert events[:3] == ['bootstrap', 'torch', 'spacy']
    assert events.count('resolve') == 3
    assert result['training_started'] is False and result['optimizer_updates'] == 0


@pytest.mark.parametrize('diagnostic', ['constructed schema timeout', b'constructed schema timeout'])
def test_schema_timeout_surfaces_diagnostics_without_training(tmp_path, monkeypatch, diagnostic):
    def run(*a, **k):
        raise subprocess.TimeoutExpired(a[0], 120, stderr=diagnostic)
    monkeypatch.setattr(trainer.subprocess, 'run', run)
    with pytest.raises(ValueError, match='no CPU fallback\nconstructed schema timeout'):
        trainer.validate_runtime_configs(tmp_path / 'python.exe', tmp_path)
