"""Explicit local-only Phase B controller. No inference unless --execute is selected."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend'
ART = BACKEND / 'training/flood_ner/artifacts'
sys.path[:0] = [str(BACKEND), str(BACKEND / 'scripts')]
from app.services.news_ner.bundle import digest, verify_bundle
from app.services.news_ner.contract import IMAGE, require
from app.services.news_ner_runtime.protocol import HEADROOM_BYTES, code_bindings

BUNDLE_SHA = '13137f64b216d2a9f2978f0eb3d278950754dc56731688495b8348f2ad43a8cd'
DOCKER = 'C:/Program Files/Docker/Docker/resources/bin/docker.exe'
BASE_TAG = 'lanes-ner-qualified-base:phase-b'
LIMITS = {'cpus': 1, 'memory': 1024**3, 'memory_swap': 1024**3, 'headroom': HEADROOM_BYTES,
          'cold_seconds': 60, 'passage_p95_seconds': 1, 'article_seconds': 30, 'stress_seconds': 60,
          'cleanup_seconds': 5, 'session_seconds': 450, 'startup_request_cleanup_seconds': 125,
          'input_chars': 100000, 'response_bytes': 8 * 1024**2, 'concurrency': 1}


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, value: object) -> None:
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write('\n')


def lines(path: Path) -> list:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]


def command(args: list[str], output: Path, name: str, timeout: int = 60) -> subprocess.CompletedProcess:
    write(output / (name + '-command.json'), {'args': args, 'timeout': timeout})
    with (output / (name + '-stdout.bin')).open('xb') as stdout, (output / (name + '-stderr.bin')).open('xb') as stderr:
        result = subprocess.run(args, stdout=stdout, stderr=stderr, timeout=timeout, check=False)
    write(output / (name + '-exit.json'), {'returncode': result.returncode})
    return result


def authenticate_manifest(folder: Path, filename: str, bindings: dict) -> None:
    manifest = folder / filename
    bindings[manifest.relative_to(ROOT).as_posix()] = digest(manifest)
    for name, entry in read(manifest)['files'].items():
        path = ROOT / name if name.startswith(('backend/', 'docs/')) else folder / name
        expected = entry['sha256'] if isinstance(entry, dict) else entry
        require(digest(path) == expected, 'predecessor_receipt_mismatch')
        bindings[path.relative_to(ROOT).as_posix()] = expected


def prepare(output: Path) -> dict:
    require(not output.exists() and output.parent.resolve() == ART.resolve(), 'new_private_destination_required')
    output.mkdir()
    verify_bundle(ART / 'ner-preview-bundle-20261019-v1', BUNDLE_SHA)
    bindings = {}
    for folder, manifest in [('backend-location-live-20261020-v46', 'final-package-manifest.json'),
                             ('backend-location-cached-20261020-v46', 'final-package-manifest.json'),
                             ('linux-runtime-coordination-20261019-v29', 'completion-manifest.json'),
                             ('shadow-execution-20261019-v31', 'completion-manifest.json')]:
        authenticate_manifest(ART / folder, manifest, bindings)
    old = read(ART / 'backend-location-live-20261020-v46/freeze.json')['implementation']
    for name, expected in old.items():
        require(digest(ROOT / name) == expected, 'v46_code_changed')
        bindings[name] = expected
    base = subprocess.run([DOCKER, 'image', 'inspect', IMAGE], capture_output=True, timeout=30, check=True)
    image = json.loads(base.stdout)[0]
    require(image['Id'] == IMAGE and image['Architecture'] == 'amd64' and image['Os'] == 'linux', 'qualified_image_required')
    write(output / 'base-image.json', image)
    subprocess.run([DOCKER, 'image', 'tag', IMAGE, BASE_TAG], check=True, timeout=30)
    from check_ner_location_v46 import cached
    cached_result = cached(output.parent / (output.name + '-cached'))
    require(cached_result['cached_records'] == 788 and cached_result['saved_context_graphs_matched'] == 407, 'cached_parity')
    write(output / 'cached-result.json', cached_result)
    result = command([sys.executable, '-B', '-m', 'pytest', '--noconftest', '-p', 'no:cacheprovider',
                      str(BACKEND / 'tests/test_news_ner_subprocess.py'), '-q'], output, 'constructed')
    require(result.returncode == 0, 'constructed_checks_failed')
    # Training-only view and original complete-article extent assessments are inherited unchanged.
    old_workload = ART / 'linux-runtime-execution-20261019-v29/worker-input/workload.json'
    expected_file = ART / 'linux-runtime-execution-20261019-v29/expected-predictions.json'
    bindings[old_workload.relative_to(ROOT).as_posix()] = digest(old_workload)
    bindings[expected_file.relative_to(ROOT).as_posix()] = digest(expected_file)
    rows = read(old_workload)['rows']
    from training.flood_ner.linux_runtime_v29 import validate_workload
    validate_workload(rows)
    expected = read(expected_file)
    shadow = lines(ART / 'shadow-execution-20261019-v31/worker-output/comparisons.jsonl')
    for row in rows:
        row['publication'] = None
        if row['kind'] == 'article':
            matched = [r for r in shadow if r['text_sha256'] == row['text_sha256']]
            require(len(matched) == 1, 'saved_article_predictions_required')
            expected[row['record_id']] = [[m['start'], m['end'], m['label']] for m in matched[0]['neural']['mentions']]
    source_file = ART / 'ner-preview-source-link-20261019-v2/saved-article-input.json'
    source = read(source_file)
    reviewed = read(ART / 'backend-location-live-20261020-v46/worker-response.json')
    # Use the exact reviewed record identity/publication coordinates from its authenticated graph.
    group_requests = read(ART / 'location-repair-prepared-20261020-v44/request.json')['groups']['article']
    require(len(group_requests) == 1, 'single_reviewed_article')
    raw = group_requests[0]['raw']
    require(raw['text'] == source['article_text'] and len(reviewed['proposal']['neural_mentions']) == 53, 'reviewed_binding')
    rows.append({**{k: raw[k] for k in ('record_id', 'text', 'text_sha256', 'publication')}, 'kind': 'reviewed'})
    expected[raw['record_id']] = [[m['start'], m['end'], m['label']] for m in reviewed['proposal']['neural_mentions']]
    # Existing fictional stress cases have no retained neural oracle; group parity uses their returned mentions.
    context = output / 'context'
    services = context / 'app/services'
    services.mkdir(parents=True)
    for name in ('news_ner', 'news_ner_runtime'):
        target = services / name
        target.mkdir()
        for path in (BACKEND / 'app/services' / name).iterdir():
            if path.is_file() and (path.suffix == '.py' or path.name == 'promotion.json'):
                shutil.copy2(path, target / path.name)
    shutil.copytree(ART / 'ner-preview-bundle-20261019-v1', context / 'assets')
    (context / 'scripts').mkdir()
    for name in ('news_ner_runtime_probe.py', 'news_ner_runtime_faults.py'):
        shutil.copy2(BACKEND / 'scripts' / name, context / 'scripts' / name)
    (context / 'Dockerfile').write_text('FROM ' + BASE_TAG + '\nCOPY app/services/ /app/app/services/\nCOPY assets/ /assets/\nCOPY scripts/ /app/scripts/\n', encoding='utf-8')
    request = {'bundle_sha256': BUNDLE_SHA, 'code': code_bindings(BACKEND / 'app/services')}
    (output / 'input').mkdir()
    write(output / 'input/workload.json', {'rows': rows})
    write(output / 'input/request.json', request)
    write(output / 'expected-predictions.json', expected)  # Never mounted in inference container.
    for path in [*sorted((BACKEND / 'app').rglob('*.py')), BACKEND / 'Dockerfile', BACKEND / '.dockerignore',
                 BACKEND / 'requirements.txt', BACKEND / 'scripts/run_news_discovery.py',
                 BACKEND / 'tests/test_news_ner_subprocess.py', *sorted((BACKEND / 'scripts').glob('*news_ner_runtime*.py'))]:
        bindings[path.relative_to(ROOT).as_posix()] = digest(path)
    for path in context.rglob('*'):
        if path.is_file(): bindings[path.relative_to(ROOT).as_posix()] = digest(path)
    for path in [output / 'input/workload.json', output / 'input/request.json', output / 'expected-predictions.json']:
        bindings[path.relative_to(ROOT).as_posix()] = digest(path)
    # Snapshot every affected source before the single measured attempt.
    for name in bindings:
        if name.startswith('backend/app/') or name.startswith('backend/scripts/') or name.startswith('backend/tests/'):
            dest = output / 'snapshot' / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, dest)
    freeze = {'limits': LIMITS, 'base_image': IMAGE, 'bindings': bindings, 'request': request,
              'counts': {'passage': 345, 'article': 6, 'reviewed': 1, 'stress': 3}, 'neural_attempts_allowed': 1,
              'expected_predictions_mounted': False, 'schema_changes': False, 'cloud_changes': False}
    write(output / 'freeze.json', freeze)
    return {'status': 'prepared', 'freeze_sha256': digest(output / 'freeze.json')}


def check_freeze(output: Path, sha: str) -> dict:
    require(digest(output / 'freeze.json') == sha, 'freeze_hash')
    freeze = read(output / 'freeze.json')
    require(freeze['limits'] == LIMITS, 'limits_changed')
    for name, expected in freeze['bindings'].items(): require(digest(ROOT / name) == expected, 'frozen_file_changed')
    return freeze


def container_args(output: Path, name: str, image: str, *, memory: int = 1024**3) -> list[str]:
    return [DOCKER, 'create', '--name', name, '--init', '--cpus', '1', '--memory', str(memory),
            '--memory-swap', str(memory), '--pids-limit', '128', '--network', 'none', '--read-only',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,noexec,nosuid,size=67108864',
            '--env', 'LANES_NEWS_AUDITOR_BATCH_SIZE=8', '--mount', f'type=bind,src={output / "input"},dst=/input,readonly',
            '--mount', f'type=bind,src={BACKEND / "app"},dst=/app/app,readonly',
            '--mount', f'type=bind,src={output / "output"},dst=/output', image]


def build(output: Path, sha: str) -> dict:
    check_freeze(output, sha)
    base = json.loads(subprocess.run([DOCKER, 'image', 'inspect', BASE_TAG], capture_output=True, check=True, timeout=30).stdout)[0]
    require(base['Id'] == IMAGE, 'base_tag_identity')
    result = command([DOCKER, 'build', '--pull=false', '--network=none', '--iidfile', str(output / 'image.id'),
                      str(output / 'context')], output, 'build', 300)
    require(result.returncode == 0, 'image_build_failed')
    image = (output / 'image.id').read_text().strip()
    # Constructed real subprocess tests run before neural execution.
    (output / 'output').mkdir()
    args = container_args(output, output.name + '-faults', image) + ['python', '-I', '-B', '/app/scripts/news_ner_runtime_faults.py']
    require(command(args, output, 'fault-create').returncode == 0, 'fault_create')
    require(command([DOCKER, 'start', '-a', output.name + '-faults'], output, 'fault-run', 60).returncode == 0, 'fault_checks_failed')
    args = container_args(output, output.name + '-baseline', image) + ['python', '-I', '-B', '/app/scripts/news_ner_runtime_probe.py', '--baseline-only']
    require(command(args, output, 'baseline-create').returncode == 0, 'baseline_create')
    require(command([DOCKER, 'start', '-a', output.name + '-baseline'], output, 'baseline-run', 60).returncode == 0, 'baseline_failed')
    baseline = read(output / 'output/baseline-preflight.json')
    require(all(digest(BACKEND / name) == value for name, value in baseline['imported_source_hashes'].items()), 'baseline_source_mismatch')
    # Deliberate OOM only in this owned disposable container, never the host/model worker.
    args = container_args(output, output.name + '-oom', image) + ['python', '-I', '-B', '-c', 'x=bytearray(2*1024**3)']
    require(command(args, output, 'oom-create').returncode == 0, 'oom_create')
    require(command([DOCKER, 'start', '-a', output.name + '-oom'], output, 'oom-run', 30).returncode == 137, 'oom_exit')
    require(command([DOCKER, 'inspect', output.name + '-oom'], output, 'oom-inspect').returncode == 0, 'oom_inspect')
    require(json.loads((output / 'oom-inspect-stdout.bin').read_bytes())[0]['State']['OOMKilled'], 'oom_not_observed')
    return {'status': 'built_and_constructed_faults_passed', 'image': image}


def execute(output: Path, sha: str) -> dict:
    freeze = check_freeze(output, sha)
    require(read(output / 'fault-run-exit.json')['returncode'] == 0, 'faults_required')
    image = (output / 'image.id').read_text().strip()
    write(ART / 'rss-ner-phase-b-qualification.claim.json', {'attempts': 1, 'destination': output.name, 'freeze_sha256': sha})
    write(output / 'attempt.json', {'freeze_sha256': sha, 'image': image, 'attempts': 1})
    name = output.name + '-measurement'
    args = container_args(output, name, image) + ['python', '-I', '-B', '/app/scripts/news_ner_runtime_probe.py']
    require(command(args, output, 'measurement-create').returncode == 0, 'measurement_create')
    try:
        result = command([DOCKER, 'start', '-a', name], output, 'measurement', 460)
    except subprocess.TimeoutExpired:
        command([DOCKER, 'kill', name], output, 'guard-owned-kill')
        command([DOCKER, 'inspect', name], output, 'guard-inspect')
        write(output / 'guard-failure.json', {'code': 'container_deadline', 'retry': False})
        return {'status': 'qualification_failed', 'code': 'container_deadline', 'retry': False}
    command([DOCKER, 'inspect', name], output, 'measurement-inspect')
    if result.returncode != 0:
        return {'status': 'qualification_failed', 'receipt': 'output/failure.json', 'retry': False}
    return {'status': 'measurement_completed_verification_required'}


def verify(output: Path, sha: str) -> dict:
    freeze = check_freeze(output, sha)
    responses_path = output / 'output/responses.jsonl'
    responses = lines(responses_path) if responses_path.exists() else []
    workload = read(output / 'input/workload.json')['rows']
    expected = read(output / 'expected-predictions.json')
    from app.services.news_ner_runtime.protocol import verify_result
    compared = 0
    for row, response in zip(workload, responses, strict=False):
        require(row['record_id'] == response['record_id'], 'response_order')
        verify_result({k: row[k] for k in ('record_id', 'text', 'text_sha256', 'publication')}, response['result'],
                      BUNDLE_SHA, freeze['request']['code'])
        if row['record_id'] in expected:
            spans = [[m['start'], m['end'], m['label']] for m in response['result']['proposal']['neural_mentions']]
            require(spans == expected[row['record_id']], 'neural_parity_failed')
            compared += 1
    complete = len(responses) == len(workload)
    result = {'status': 'failed' if not complete else 'verification_pending', 'responses': len(responses), 'prediction_records_compared': compared,
              'partial_graph_bindings_verified': True, 'frozen_files_preserved': True, 'cloud_verified': False, 'automatic_processing_connected': False}
    if complete and (output / 'output/measurements.json').exists():
        metrics = read(output / 'output/measurements.json')
        times = metrics['timings']
        p95 = sorted(times['passage'])[math.ceil(.95 * len(times['passage'])) - 1]
        checks = {'prediction_count': compared == 352, 'cold': metrics['cold_seconds'] <= 60,
                  'passage_p95': p95 <= 1, 'articles': max(times['article'] + times['reviewed']) <= 30,
                  'stress': max(times['stress']) <= 60, 'memory': metrics['memory']['memory.peak'] < HEADROOM_BYTES,
                  'cleanup': metrics['cleanup_seconds'] <= 5 and metrics['child_exit'] == 0,
                  'session': metrics['session_seconds'] < 450}
        baseline = read(output / 'output/baseline.json')
        # The imported normal-worker source must match this checkout, not just an old image snapshot.
        checks['normal_worker_bindings'] = all((BACKEND / name).is_file() and digest(BACKEND / name) == value
                                                for name, value in baseline['imported_source_hashes'].items())
        result.update(status='passed' if all(checks.values()) else 'failed', checks=checks, passage_p95_seconds=p95,
                      peak_container_bytes=metrics['memory']['memory.peak'], cold_seconds=metrics['cold_seconds'])
    write(output / 'independent-verification.json', result)
    write(output / 'final-package-manifest.json', {'files': {p.relative_to(output).as_posix(): digest(p)
          for p in output.rglob('*') if p.is_file() and 'context' not in p.relative_to(output).parts and 'snapshot' not in p.relative_to(output).parts}})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'build', 'execute', 'verify'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--freeze-sha256', default='')
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.parent == ART.resolve(), 'private_artifact_child_required')
    operation = {'prepare': prepare, 'build': build, 'execute': execute, 'verify': verify}[args.operation]
    result = operation(output) if args.operation == 'prepare' else operation(output, args.freeze_sha256)
    print(json.dumps(result))


if __name__ == '__main__': main()
