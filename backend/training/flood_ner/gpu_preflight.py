"""Offline GPU qualification on fixed constructed fixtures; no corpus admission."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from .preflight import load_cases, verify_model, MODEL_REVISION

CASES_SHA256 = '62f317b78101dd8abacf5c60155c05948b990cef79be803e71ecb4e1fc5ea1b9'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_worker(result: dict, cases: list, mode: str) -> None:
    if not isinstance(result, dict):
        raise ValueError('worker output must be an object')
    if (result.get('mode') != mode or result.get('python_version', '').split('.')[:2] != ['3', '11']
            or result.get('spacy_version') != '3.7.5' or result.get('model_revision') != MODEL_REVISION):
        raise ValueError('worker interpreter/model identity mismatch')
    for key, labels in (
        ('baseline_predictions', {'LOC', 'ORG', 'PER'}),
        ('trial_predictions', {'ROAD', 'LANDMARK', 'LOCAL_AREA', 'BARANGAY', 'CITY', 'PROVINCE'}),
    ):
        rows = result.get(key)
        if not isinstance(rows, list) or len(rows) != len(cases):
            raise ValueError('constructed prediction count differs')
        for row, case in zip(rows, cases):
            if row.get('case_id') != case.case_id or row.get('text_sha256') != case.text_sha256:
                raise ValueError('constructed prediction identity differs')
            end = 0
            for ent in row['entities']:
                a, z = ent['start'], ent['end']
                if (type(a) is not int or type(z) is not int or not end <= a < z <= len(case.text)
                        or ent['text'] != case.text[a:z] or ent['label'] not in labels):
                    raise ValueError('invalid constructed entity prediction')
                end = z
    if mode == 'gpu':
        if not all(result.get(k) is True for k in ('cupy_kernel_passed', 'torch_cuda_passed', 'spacy_gpu_selected', 'parameters_on_gpu')):
            raise ValueError('GPU execution was not verified')
        if set(result.get('trial_labels', [])) != {'ROAD', 'LANDMARK', 'LOCAL_AREA', 'BARANGAY', 'CITY', 'PROVINCE'}:
            raise ValueError('six-class trial head differs')
        steps = result.get('training_steps', [])
        if len(steps) != 3 or [s['batch_size'] for s in steps] != [1, 4, 8]:
            raise ValueError('constructed training measurements incomplete')
        for step in steps:
            if (not math.isfinite(step['loss']) or step['loss'] < 0
                    or not math.isfinite(step['elapsed_ms']) or step['elapsed_ms'] <= 0):
                raise ValueError('invalid training resource/loss measurement')
    if len(result.get('trial_predictions', [])) != len(cases):
        raise ValueError('trial replay count differs')


def run(python: Path, model_manifest: Path, output: Path, root: Path) -> dict:
    root = root.resolve()
    artifacts = root / 'backend/training/flood_ner/artifacts'
    output = output.resolve()
    python = python.resolve()
    if output == artifacts or not output.is_relative_to(artifacts) or output.exists():
        raise ValueError('GPU output must be a new directory under ignored artifacts')
    if not python.is_relative_to(artifacts) or not python.is_file():
        raise ValueError('explicit isolated research Python under artifacts required')
    case_file = root / 'backend/training/flood_ner/configs/preflight_constructed_cases.jsonl'
    if digest(case_file) != CASES_SHA256:
        raise ValueError('GPU qualification accepts only the fixed constructed probes')
    cases = load_cases(case_file)
    manifest, model = verify_model(model_manifest, artifacts)
    output.mkdir(parents=True)
    request = {'model_dir': str(model), 'model_revision': MODEL_REVISION,
               'trial_model': str(output / 'trial-model'), 'cases': [c.model_dump(mode='json') for c in cases]}
    request_file = output / 'request.json'
    request_file.write_text(json.dumps(request, ensure_ascii=False), encoding='utf-8')
    report = {'schema_version': 'lanes-desktop-gpu-qualification-v1', 'state': 'failed',
              'constructed_only': True, 'news_samples_processed': 0, 'source_admission_changed': False,
              'production_runtime_qualified': False, 'six_class_accuracy_measured': False,
              'cases_sha256': digest(case_file), 'model_manifest_sha256': digest(model_manifest),
              'model_revision': manifest['revision'], 'research_interpreter': str(python)}
    env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH'}}
    env.update({'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'TOKENIZERS_PARALLELISM': 'false',
                'OMP_NUM_THREADS': '2', 'MKL_NUM_THREADS': '2', 'CUPY_CACHE_DIR': str(output / 'cupy-cache'),
                'HF_HOME': str(output / 'hf-cache'), 'TORCH_HOME': str(output / 'torch-cache')})
    try:
        results = {}
        for mode in ('gpu', 'cpu'):
            try:
                child = subprocess.run([str(python), '-I', '-X', 'utf8', str(Path(__file__).with_name('gpu_worker.py')),
                                        str(request_file), mode], cwd=output, env=env, capture_output=True, timeout=600)
            except subprocess.TimeoutExpired as exc:
                # Preserve partial diagnostics before the outer handler saves failure.
                (output / f'{mode}-stdout.log').write_bytes(exc.stdout or b'')
                (output / f'{mode}-stderr.log').write_bytes(exc.stderr or b'')
                raise
            (output / f'{mode}-stdout.log').write_bytes(child.stdout)
            (output / f'{mode}-stderr.log').write_bytes(child.stderr)
            if child.returncode:
                raise RuntimeError(f'{mode} worker exited {child.returncode}: ' + child.stderr.decode('utf-8', errors='replace')[-6000:])
            result = json.loads(child.stdout)
            validate_worker(result, cases, mode)
            (output / f'{mode}-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            results[mode] = result
        report['baseline_cpu_gpu_identical'] = results['cpu']['baseline_predictions'] == results['gpu']['baseline_predictions']
        report['trained_cpu_gpu_identical'] = results['cpu']['trial_predictions'] == results['gpu']['trial_predictions']
        verify_model(model_manifest, artifacts)
        if not report['baseline_cpu_gpu_identical'] or not report['trained_cpu_gpu_identical']:
            raise ValueError('CPU/GPU constructed replay differs; qualification needs investigation')
        report.update({'state': 'passed', 'gpu_environment_qualified': True,
                       'constructed_training_performed': True, 'pinned_model_files_unchanged': True,
                       'training_steps': results['gpu']['training_steps'], 'resources': results['gpu']['resources']})
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        report.update({'error': str(exc), 'gpu_environment_qualified': False})
    report['files'] = {p.relative_to(output).as_posix(): digest(p) for p in sorted(output.rglob('*'))
                       if p.is_file() and 'cupy-cache' not in p.parts}
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--model-manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.python, args.model_manifest, args.output, Path(__file__).resolve().parents[3])
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report['state'] == 'passed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
