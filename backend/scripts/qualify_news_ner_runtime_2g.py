"""Separate local follow-up at one CPU / 2 GiB. Preserve the failed 1-GiB controller."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/scripts')]
import qualify_news_ner_runtime as original
from app.services.news_ner.bundle import digest, verify_bundle
from app.services.news_ner.contract import IMAGE, require

ART = original.ART
PREVIOUS = ART / 'rss-ner-runtime-phase-b-20261020-v5'
PREVIOUS_SHA = '3a89a9bc768f13f40da34a37d75396f0026ba80d9ca1ec123553919b0eb5f4f1'
LIMITS = {**original.LIMITS, 'memory': 2 * 1024**3, 'memory_swap': 2 * 1024**3, 'headroom': 1792 * 1024**2}
SOURCES = ['backend/scripts/qualify_news_ner_runtime_2g.py', 'backend/scripts/news_ner_runtime_probe_2g.py',
           'backend/scripts/verify_news_ner_subprocess_2g.py', 'backend/tests/test_news_ner_runtime_2g.py']


def preserved_previous() -> dict:
    original.check_freeze(PREVIOUS, PREVIOUS_SHA)
    original.authenticate_manifest(PREVIOUS, 'final-package-manifest.json', {})
    audit = original.read(PREVIOUS / 'independent-audit.json')
    require(audit['neural_attempts'] == 1 and audit['status'] == 'failed_memory_gate_independently_verified', 'previous_attempt_required')
    return {'freeze_sha256': PREVIOUS_SHA, 'audit_sha256': digest(PREVIOUS / 'independent-audit.json'),
            'manifest_sha256': digest(PREVIOUS / 'final-package-manifest.json')}


def prepare(output: Path) -> dict:
    require(not output.exists() and output.parent == ART.resolve(), 'new_private_destination_required')
    previous = preserved_previous()
    verify_bundle(ART / 'ner-preview-bundle-20261019-v1', original.BUNDLE_SHA)
    output.mkdir()
    bindings = dict(original.read(PREVIOUS / 'freeze.json')['bindings'])
    for name in ('freeze.json', 'independent-audit.json', 'final-package-manifest.json'):
        path = PREVIOUS / name
        bindings[path.relative_to(ROOT).as_posix()] = digest(path)
    original.write(output / 'previous.json', previous)
    result = original.command([sys.executable, '-B', '-m', 'pytest', '--noconftest', '-p', 'no:cacheprovider',
        str(ROOT / 'backend/tests/test_news_ner_subprocess.py'), str(ROOT / 'backend/tests/test_news_ner_runtime_2g.py'), '-q'],
        output, 'constructed')
    require(result.returncode == 0, 'constructed_tests_failed')
    from check_ner_location_v46 import cached
    cache = cached(output.parent / (output.name + '-cached'))
    require(cache['cached_records'] == 788 and cache['saved_context_graphs_matched'] == 407, 'cached_parity')
    original.write(output / 'cached-result.json', cache)
    shutil.copytree(PREVIOUS / 'context', output / 'context')
    shutil.copy2(ROOT / 'backend/scripts/news_ner_runtime_probe_2g.py', output / 'context/scripts/news_ner_runtime_probe_2g.py')
    shutil.copytree(PREVIOUS / 'input', output / 'input')
    shutil.copy2(PREVIOUS / 'expected-predictions.json', output / 'expected-predictions.json')
    for path in [*(output / 'context').rglob('*'), *(output / 'input').rglob('*'), output / 'expected-predictions.json']:
        if path.is_file(): bindings[path.relative_to(ROOT).as_posix()] = digest(path)
    for name in SOURCES:
        bindings[name] = digest(ROOT / name)
        snapshot = output / 'snapshot' / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, snapshot)
    freeze = {'schema': 'lanes-ner-runtime-2g-qualification-v1', 'limits': LIMITS, 'bindings': bindings,
              'previous': previous, 'base_image': IMAGE, 'counts': {'passage': 345, 'article': 6, 'stress': 3, 'reviewed': 1},
              'neural_attempts_allowed': 1, 'expected_predictions_mounted': False,
              'automatic_processing_connected': False, 'cloud_changes': False}
    original.write(output / 'freeze.json', freeze)
    return {'status': 'prepared', 'freeze_sha256': digest(output / 'freeze.json')}


def check_freeze(output: Path, sha: str) -> dict:
    require(digest(output / 'freeze.json') == sha, 'freeze_hash')
    value = original.read(output / 'freeze.json')
    require(value['limits'] == LIMITS and value['previous'] == preserved_previous(), 'frozen_profile_changed')
    for name, expected in value['bindings'].items(): require(digest(ROOT / name) == expected, 'frozen_file_changed')
    return value


def container_args(output: Path, name: str, image: str) -> list[str]:
    return original.container_args(output, name, image, memory=LIMITS['memory'])


def build(output: Path, sha: str) -> dict:
    check_freeze(output, sha)
    base = json.loads(subprocess.run([original.DOCKER, 'image', 'inspect', original.BASE_TAG], capture_output=True, check=True, timeout=30).stdout)[0]
    require(base['Id'] == IMAGE, 'base_image_identity')
    require(original.command([original.DOCKER, 'build', '--pull=false', '--network=none', '--iidfile', str(output / 'image.id'),
                             str(output / 'context')], output, 'build', 300).returncode == 0, 'image_build_failed')
    image = (output / 'image.id').read_text().strip()
    (output / 'output').mkdir()
    for suffix, script, extra in [('faults', 'news_ner_runtime_faults.py', []),
                                   ('baseline', 'news_ner_runtime_probe.py', ['--baseline-only'])]:
        args = container_args(output, output.name + '-' + suffix, image) + ['python', '-I', '-B', '/app/scripts/' + script, *extra]
        require(original.command(args, output, suffix + '-create').returncode == 0, suffix + '_create')
        require(original.command([original.DOCKER, 'start', '-a', output.name + '-' + suffix], output, suffix + '-run', 60).returncode == 0, suffix + '_failed')
    baseline = original.read(output / 'output/baseline-preflight.json')
    require(all(digest(ROOT / 'backend' / name) == value for name, value in baseline['imported_source_hashes'].items()), 'baseline_bindings')
    args = container_args(output, output.name + '-oom', image) + ['python', '-I', '-B', '-c', 'x=bytearray(4*1024**3)']
    require(original.command(args, output, 'oom-create').returncode == 0, 'oom_create')
    require(original.command([original.DOCKER, 'start', '-a', output.name + '-oom'], output, 'oom-run', 30).returncode == 137, 'oom_exit')
    require(original.command([original.DOCKER, 'inspect', output.name + '-oom'], output, 'oom-inspect').returncode == 0, 'oom_inspect')
    require(json.loads((output / 'oom-inspect-stdout.bin').read_bytes())[0]['State']['OOMKilled'], 'oom_not_observed')
    original.write(output / 'build-ready.json', {'image': image, 'freeze_sha256': sha,
                   'checks': ['constructed', 'cached', 'faults', 'baseline', 'disposable_oom']})
    return {'status': 'built_software_fault_and_baseline_checks_passed', 'image': image}


def execute(output: Path, sha: str) -> dict:
    check_freeze(output, sha)
    ready = original.read(output / 'build-ready.json')
    require(ready['freeze_sha256'] == sha and ready['image'] == (output / 'image.id').read_text().strip(), 'build_binding')
    original.write(ART / 'rss-ner-phase-b-2g-qualification.claim.json', {'attempts': 1, 'destination': output.name, 'freeze_sha256': sha})
    original.write(output / 'attempt.json', {'attempts': 1, 'freeze_sha256': sha, 'image': ready['image']})
    name = output.name + '-measurement'
    args = container_args(output, name, ready['image']) + ['python', '-I', '-B', '/app/scripts/news_ner_runtime_probe_2g.py']
    require(original.command(args, output, 'measurement-create').returncode == 0, 'measurement_create')
    try:
        result = original.command([original.DOCKER, 'start', '-a', name], output, 'measurement', 460)
    except subprocess.TimeoutExpired:
        original.command([original.DOCKER, 'kill', name], output, 'guard-owned-kill')
        original.command([original.DOCKER, 'inspect', name], output, 'measurement-inspect')
        original.write(output / 'guard-failure.json', {'code': 'container_deadline', 'retry': False})
        return {'status': 'qualification_failed', 'code': 'container_deadline', 'retry': False}
    original.command([original.DOCKER, 'inspect', name], output, 'measurement-inspect')
    return {'status': 'completed_verification_required' if result.returncode == 0 else 'qualification_failed', 'retry': False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'build', 'execute'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--freeze-sha256', default='')
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.parent == ART.resolve(), 'private_direct_child_required')
    operation = {'prepare': prepare, 'build': build, 'execute': execute}[args.operation]
    print(json.dumps(operation(output) if args.operation == 'prepare' else operation(output, args.freeze_sha256)))


if __name__ == '__main__': main()
