"""Prepare/verify the isolated NER cloud check. This tool never changes Google Cloud."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend'
sys.path[:0] = [str(BACKEND), str(BACKEND / 'scripts')]
from app.services.news_ner.bundle import digest, safe_file, verify_bundle
from app.services.news_ner.contract import IMAGE, object_sha, require
from app.services.news_ner_runtime.protocol import code_bindings
from news_ner_cloud_probe import (COUNTS, DIAGNOSTIC_SCHEMA, HEADROOM_BYTES, MEMORY_BYTES, RESOURCE_FILES,
                                  SCHEMA, STRICT_PROFILE, CLOUD_PROFILE, RESOURCE_PROFILES, stable_result, timing_checks)

ART = BACKEND / 'training/flood_ner/artifacts'
PREVIOUS = ART / 'rss-ner-runtime-phase-b-3g-20261020-v1'
PREVIOUS_PINS = {
    'freeze.json': '2c1c43bacf6e8ba94913c8ea53bc818cfaa33c27b64707498d6e118fee0c4f2b',
    'independent-audit.json': '68d56b8d64342635970bb45366fc45d1878dd840e5e8d1f1ddee9071809d8b03',
    'final-package-manifest.json': '8b079765472409592b99e4d2f380c95b3846ad799aa5ef437b6db46857c7d488',
}
BUNDLE = ART / 'ner-preview-bundle-20261019-v1'
BUNDLE_SHA = '13137f64b216d2a9f2978f0eb3d278950754dc56731688495b8348f2ad43a8cd'
BASE_TAG = 'lanes-ner-qualified-base:phase-b'
PROJECT = 'lanes-project-508809'
REGION = 'asia-east1'
JOB = 'lanes-ner-check'
SERVICE_ACCOUNT = f'{JOB}@{PROJECT}.iam.gserviceaccount.com'
CLAIM_NAME = 'ner-cloud-check-20261022-local.claim.json'
SOURCES = ['infrastructure/ner-check/Dockerfile', 'backend/scripts/qualify_news_ner_cloud.py',
           'backend/scripts/news_ner_cloud_probe.py', 'backend/scripts/news_ner_cloud_entrypoint.py',
           'backend/tests/test_news_ner_cloud.py']
LIMITS = {'cpu': 1, 'memory_bytes': MEMORY_BYTES, 'headroom_bytes': HEADROOM_BYTES,
          'task_count': 1, 'parallelism': 1, 'timeout_seconds': 600, 'max_retries': 0}


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, value: object) -> None:
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def file_map(folder: Path) -> dict[str, str]:
    files = {}
    for path in sorted(folder.rglob('*')):
        require(not path.is_symlink() and not getattr(path, 'is_junction', lambda: False)(), 'linked_file')
        if path.is_file():
            name = path.relative_to(folder).as_posix()
            files[name] = digest(safe_file(folder, name))
    return files


def authenticate_previous() -> dict:
    for name, expected in PREVIOUS_PINS.items():
        require(digest(PREVIOUS / name) == expected, 'previous_identity_changed')
    for name, expected in read(PREVIOUS / 'final-package-manifest.json')['files'].items():
        require(digest(safe_file(PREVIOUS, name)) == expected, 'previous_evidence_changed')
    audit = read(PREVIOUS / 'independent-audit.json')
    require(audit['status'] == 'passed_local_3g_qualification' and all(audit['checks'].values()),
            'previous_qualification_required')
    return dict(PREVIOUS_PINS)


def expected_records() -> list[dict]:
    expected = read(PREVIOUS / 'expected-predictions.json')
    result = []
    for line in (PREVIOUS / 'output/responses.jsonl').read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        result.append({'record_id': row['record_id'], 'result_sha256': object_sha(stable_result(row['result'])),
                       'predictions_sha256': object_sha(expected[row['record_id']]) if row['record_id'] in expected else None,
                       'mention_count': len(row['result']['proposal']['neural_mentions'])})
    require(len(result) == 355 and sum(r['predictions_sha256'] is not None for r in result) == 352,
            'previous_predictions_incomplete')
    return result


def require_private_output(output: Path) -> None:
    require(output.parent == (ROOT / 'data').resolve() and re.fullmatch(r'ner-cloud-check-[a-z0-9-]+', output.name)
            is not None, 'private_direct_child_required')
    require(not output.is_symlink() and not getattr(output, 'is_junction', lambda: False)(), 'linked_output')


def prepare(output: Path, resource_profile: str = STRICT_PROFILE) -> dict:
    require(resource_profile in RESOURCE_PROFILES, 'resource_profile_invalid')
    require_private_output(output)
    require(not output.exists(), 'new_destination_required')
    previous = authenticate_previous()
    verify_bundle(BUNDLE, BUNDLE_SHA)
    request = read(PREVIOUS / 'input/request.json')
    require(request['bundle_sha256'] == BUNDLE_SHA
            and request['code'] == code_bindings(BACKEND / 'app/services'), 'runtime_identity_changed')
    rows = read(PREVIOUS / 'input/workload.json')['rows']
    require(dict(Counter(row['kind'] for row in rows)) == COUNTS, 'previous_workload_changed')
    expected = expected_records()
    output.mkdir()
    context = output / 'context'
    services = context / 'app/services'
    services.mkdir(parents=True)
    for name in request['code']:
        source = safe_file(BACKEND / 'app/services', name)
        target = services / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copytree(BUNDLE, context / 'assets')
    (context / 'scripts').mkdir()
    for script in ('news_ner_cloud_probe.py', 'news_ner_cloud_entrypoint.py'):
        shutil.copy2(BACKEND / 'scripts' / script, context / 'scripts' / script)
    shutil.copy2(ROOT / 'infrastructure/ner-check/Dockerfile', context / 'Dockerfile')
    (context / 'input').mkdir()
    for name in ('request.json', 'workload.json'):
        shutil.copy2(PREVIOUS / 'input' / name, context / 'input' / name)
    inputs = {name: digest(context / 'input' / name) for name in ('request.json', 'workload.json')}
    sources = {name: digest(ROOT / name) for name in SOURCES}
    identity = {'previous': previous, 'sources': sources, 'inputs': inputs, 'bundle_sha256': BUNDLE_SHA,
                'base_image': IMAGE, 'limits': LIMITS, 'resource_profile': resource_profile, 'expected_sha256': object_sha(expected),
                'provenance': read(PREVIOUS / 'output/ready.json')['provenance']}
    package_id = object_sha(identity)
    write(context / 'input/check.json', {'schema': SCHEMA, 'package_id': package_id, 'counts': COUNTS,
          'request_sha256': inputs['request.json'], 'workload_sha256': inputs['workload.json'],
          'resource_profile': resource_profile})
    write(output / 'expected.json', {'records': expected})  # Never copied to the image.
    freeze = {'schema': SCHEMA, 'package_id': package_id, 'identity': identity,
              'context': file_map(context), 'expected_file_sha256': digest(output / 'expected.json')}
    write(output / 'freeze.json', freeze)
    return {'status': 'prepared_no_inference', 'package_id': package_id,
            'freeze_sha256': digest(output / 'freeze.json'), 'cloud_changes': False}


def check_freeze(output: Path, freeze_sha: str) -> dict:
    require_private_output(output)
    require(digest(output / 'freeze.json') == freeze_sha, 'freeze_identity_changed')
    frozen = read(output / 'freeze.json')
    require(frozen['schema'] == SCHEMA and object_sha(frozen['identity']) == frozen['package_id'], 'package_identity')
    require(frozen['identity']['resource_profile'] in RESOURCE_PROFILES, 'resource_profile_invalid')
    require(frozen['identity']['limits'] == LIMITS and frozen['identity']['base_image'] == IMAGE, 'limits_changed')
    require(frozen['identity']['previous'] == authenticate_previous(), 'previous_identity_changed')
    require(frozen['identity']['sources'] == {name: digest(ROOT / name) for name in SOURCES}, 'source_changed')
    require(file_map(output / 'context') == frozen['context'], 'context_changed')
    require(digest(output / 'expected.json') == frozen['expected_file_sha256'], 'expectations_changed')
    require(object_sha(read(output / 'expected.json')['records']) == frozen['identity']['expected_sha256'],
            'expectations_changed')
    return frozen


def command(args: list[str], output: Path, name: str, *, timeout: int = 60) -> subprocess.CompletedProcess:
    write(output / f'{name}-command.json', {'args': args, 'timeout_seconds': timeout})
    with (output / f'{name}-stdout.bin').open('xb') as stdout, (output / f'{name}-stderr.bin').open('xb') as stderr:
        try:
            result = subprocess.run(args, stdout=stdout, stderr=stderr, check=False, timeout=timeout)
        except subprocess.TimeoutExpired:
            write(output / f'{name}-exit.json', {'timed_out': True})
            raise
    write(output / f'{name}-exit.json', {'returncode': result.returncode})
    return result


def inspect_image(docker: str, image: str) -> dict:
    result = subprocess.run([docker, 'image', 'inspect', image], capture_output=True, check=True, timeout=30)
    return json.loads(result.stdout)[0]


def container_args(docker: str, name: str, image: str, package_id: str) -> list[str]:
    return [docker, 'create', '--name', name, '--label', f'lanes.ner-check.package={package_id}',
            '--cpus', '1', '--memory', str(MEMORY_BYTES), '--memory-swap', str(MEMORY_BYTES),
            '--pids-limit', '128', '--network', 'none', '--read-only', '--cap-drop=ALL',
            '--security-opt=no-new-privileges', '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m', image]


def build(output: Path, freeze_sha: str, docker: str) -> dict:
    frozen = check_freeze(output, freeze_sha)
    base = inspect_image(docker, BASE_TAG)
    require(base['Id'] == IMAGE and base['Os'] == 'linux' and base['Architecture'] == 'amd64', 'base_identity')
    result = command([docker, 'build', '--pull=false', '--network=none', '--build-arg', f'QUALIFIED_BASE={BASE_TAG}',
                      '--iidfile', str(output / 'image.id'), str(output / 'context')], output, 'build', timeout=300)
    require(result.returncode == 0, 'build_failed')
    image = (output / 'image.id').read_text(encoding='utf-8').strip()
    require(re.fullmatch(r'sha256:[a-f0-9]{64}', image) is not None, 'image_identity')
    info = inspect_image(docker, image)
    require(info['Config']['User'] == '65532:65532' and info['Os'] == 'linux'
            and info['Architecture'] == 'amd64'
            and info['Config']['Entrypoint'] == ['python', '-I', '-B', '/app/scripts/news_ner_cloud_entrypoint.py']
            and info['Config'].get('Cmd') in (None, []), 'image_configuration')
    require(inspect_image(docker, BASE_TAG)['Id'] == IMAGE, 'base_changed')
    name = output.name + '-preflight'
    args = container_args(docker, name, image, frozen['package_id']) + ['--preflight-only']
    require(command(args, output, 'preflight-create').returncode == 0, 'preflight_create_failed')
    require(command([docker, 'start', '-a', name], output, 'preflight', timeout=60).returncode == 0, 'preflight_failed')
    events = parse_events((output / 'preflight-stdout.bin').read_bytes())
    require(len(events) == 1 and events[0]['event'] == 'preflight' and events[0]['preflight_only'] is True
            and events[0]['package_id'] == frozen['package_id'] and events[0]['inference_started'] is False,
            'preflight_receipt_invalid')
    value = {'status': 'built_preflight_passed', 'image': image, 'package_id': frozen['package_id'],
             'freeze_sha256': freeze_sha, 'inference_started': False, 'cloud_changes': False}
    write(output / 'build-ready.json', value)
    return value


def execute_local(output: Path, freeze_sha: str, docker: str) -> dict:
    frozen = check_freeze(output, freeze_sha)
    require(frozen.get('identity', {}).get('resource_profile', STRICT_PROFILE) == STRICT_PROFILE,
            'local_strict_profile_required')
    ready = read(output / 'build-ready.json')
    image = ready['image']
    require(ready['freeze_sha256'] == freeze_sha and ready['package_id'] == frozen['package_id']
            and inspect_image(docker, image)['Id'] == image, 'build_binding')
    # Separate authorization record. Never remove it to retry an unsuccessful run.
    claim = {'package_id': frozen['package_id'], 'freeze_sha256': freeze_sha, 'image': image,
             'output': output.name, 'scope': 'one_local_inference_attempt', 'automatic_retry': False}
    write(ROOT / 'data' / CLAIM_NAME, claim)
    write(output / 'local-attempt.json', claim)
    name = output.name + '-measurement'
    require(command(container_args(docker, name, image, frozen['package_id']), output, 'local-create').returncode == 0,
            'container_create_failed')
    try:
        result = command([docker, 'start', '-a', name], output, 'local-run', timeout=610)
    except subprocess.TimeoutExpired:
        command([docker, 'kill', name], output, 'local-deadline-kill')
        command([docker, 'inspect', name], output, 'local-inspect')
        return {'status': 'failed_preserved_no_retry', 'error_code': 'local_deadline', 'cloud_changes': False}
    command([docker, 'inspect', name], output, 'local-inspect')
    return {'status': 'verification_required' if result.returncode == 0 else 'failed_preserved_no_retry',
            'automatic_retry': False, 'cloud_changes': False}


def parse_events(data: bytes) -> list[dict]:
    require(len(data) <= 2 * 1024**2, 'log_limit')
    def pairs(items: list[tuple]) -> dict:
        result = {}
        for name, value in items:
            require(name not in result, 'duplicate_log_key')
            result[name] = value
        return result
    def nonfinite(_value: str) -> None:
        raise ValueError('nonfinite_log')
    events = [json.loads(line, object_pairs_hook=pairs, parse_constant=nonfinite)
              for line in data.decode('utf-8').splitlines() if line.strip()]
    require(all(isinstance(event, dict) and event.get('schema') == SCHEMA for event in events), 'log_schema')
    return events


def verify_resource_snapshot(value: dict, profile: str) -> None:
    """Independent criteria check; configured cloud CPU is checked separately."""
    require(profile in RESOURCE_PROFILES and isinstance(value, dict), 'resource_profile_invalid')
    require(all(type(value.get(key)) is int for key in ('cpu_quota', 'cpu_period', 'memory_max', 'peak')),
            'resource_values_invalid')
    require(value['cpu_quota'] > 0 and value['cpu_period'] > 0 and value['peak'] >= 0
            and value['memory_max'] == MEMORY_BYTES, 'resource_binding')
    require(value.get('swap_max') is None or type(value['swap_max']) is int and value['swap_max'] >= 0,
            'resource_binding')
    if profile == STRICT_PROFILE:
        require(value['cpu_quota'] == value['cpu_period'] and value['swap_max'] == 0, 'resource_binding')
        return
    require(value.get('profile') == CLOUD_PROFILE, 'resource_profile_binding')
    evidence = value.get('swap_evidence', {})
    if evidence.get('basis') == 'enforced_zero_limit':
        require(value['swap_max'] == 0, 'swap_evidence_required')
    else:
        host = evidence.get('host', {})
        require(evidence.get('basis') == 'host_no_swap' and host.get('status') == 'readable'
                and host.get('host_reports_no_swap') is True
                and host.get('establishes_container_swap_limit') is False
                and all(type(host.get(key)) is int and host[key] == 0 for key in
                        ('active_devices', 'total_bytes', 'free_bytes')), 'swap_evidence_required')


def verify_cloud_configuration(job: dict, execution: dict, *, image_index: str, platform_image: str) -> dict:
    """Verify saved control-plane evidence; never invoke the SDK or change cloud."""
    prefix = f'{REGION}-docker.pkg.dev/{PROJECT}/lanes/{JOB}@sha256:'
    require(all(image.startswith(prefix) and re.fullmatch(r'[a-f0-9]{64}', image[len(prefix):])
                for image in (image_index, platform_image)), 'cloud_image_binding')
    require(job['metadata']['name'] == JOB
            and execution['metadata']['labels']['run.googleapis.com/job'] == JOB
            and execution['metadata']['name'].startswith(JOB + '-'), 'cloud_job_binding')
    for document in (job, execution):
        require(document['metadata']['namespace'] == '557679867071'
                and document['metadata']['labels']['cloud.googleapis.com/location'] == REGION,
                'cloud_project_region_binding')
    specs = [job['spec']['template']['spec'], execution['spec']]
    for spec, expected_image in zip(specs, (image_index, platform_image), strict=True):
        task = spec['template']['spec']
        require(type(spec['taskCount']) is int and spec['taskCount'] == 1
                and type(spec['parallelism']) is int and spec['parallelism'] == 1
                and type(task['maxRetries']) is int and task['maxRetries'] == 0
                and str(task['timeoutSeconds']) == '600'
                and task['serviceAccountName'] == SERVICE_ACCOUNT, 'cloud_task_limits')
        require(len(task['containers']) == 1 and not task.get('volumes'), 'cloud_container_scope')
        container = task['containers'][0]
        require(container['image'] == expected_image and not container.get('command')
                and not container.get('args') and not container.get('volumeMounts'), 'cloud_inference_entrypoint')
        limits = container['resources']['limits']
        require(limits['cpu'] in ('1', '1000m') and limits['memory'] == '3Gi', 'cloud_configured_resources')
        require(container.get('env') == [{'name': 'LANES_NER_CHECK_PROFILE', 'value': 'isolated'}],
                'cloud_environment_scope')
    require(execution['status'].get('succeededCount') == 1 and execution['status'].get('completionTime')
            and not execution['status'].get('failedCount') and not execution['status'].get('retriedCount'),
            'cloud_execution_incomplete')
    require(not any('cloudsql' in str(item).lower() for item in
            (job['metadata'].get('annotations', {}), job['spec']['template'].get('metadata', {}),
             job['spec']['template']['spec']['template'].get('metadata', {}),
             execution['metadata'].get('annotations', {}))), 'cloud_sql_binding_prohibited')
    return {'configured_cpu': 1, 'configured_memory_bytes': MEMORY_BYTES, 'tasks': 1,
            'max_retries': 0, 'timeout_seconds': 600, 'execution': execution['metadata']['name'],
            'image_index': image_index, 'platform_image': platform_image, 'database_credentials': False}


def verify_events(events: list[dict], frozen: dict, expected: list[dict], rows: list[dict]) -> dict:
    require(len(events) == len(rows) + 3 and [events[i]['event'] for i in (0, 1, -1)]
            == ['preflight', 'ready', 'completed'], 'incomplete_execution')
    require(all(event['package_id'] == frozen['package_id'] for event in events), 'execution_binding')
    require(events[0]['preflight_only'] is False and events[0]['inference_started'] is False, 'preflight_binding')
    ready, completed = events[1], events[-1]
    require(ready['isolation'] == {'seccomp': True, 'socket_families_denied': [2, 10, 1],
            'raw_socket_denied': True, 'parent_death_signal': True}, 'isolation_failed')
    require(ready['provenance'] == frozen['identity']['provenance']
            and ready['provenance']['bundle_sha256'] == BUNDLE_SHA, 'model_binding')
    timings: dict[str, list[float]] = {kind: [] for kind in COUNTS}
    predictions = 0
    previous_peak = 0
    for source, oracle, event in zip(rows, expected, events[2:-1], strict=True):
        require(event['event'] == 'record' and source['record_id'] == oracle['record_id'] == event['record_id']
                and source['kind'] == event['kind'], 'record_binding')
        require(event['result_sha256'] == oracle['result_sha256']
                and event['mention_count'] == oracle['mention_count'], 'prediction_or_graph_changed')
        if oracle['predictions_sha256'] is not None:
            require(event['predictions_sha256'] == oracle['predictions_sha256'], 'predictions_changed')
            predictions += 1
        require(isinstance(event['elapsed_seconds'], (int, float)) and event['elapsed_seconds'] >= 0
                and math.isfinite(event['elapsed_seconds']), 'timing_invalid')
        timings[source['kind']].append(event['elapsed_seconds'])
        require(previous_peak <= event['memory_peak'] < HEADROOM_BYTES, 'memory_headroom')
        previous_peak = event['memory_peak']
    require(completed['counts'] == COUNTS and completed['completed'] == 355 and predictions == 352
            and completed['timings'] == timings, 'completion_counts')
    profile = frozen['identity'].get('resource_profile', STRICT_PROFILE)
    memory = completed['resources']
    verify_resource_snapshot(memory, profile)
    require(memory['peak'] >= previous_peak, 'resource_binding')
    if profile == CLOUD_PROFILE:
        require(events[0].get('resource_profile') == ready.get('resource_profile') == CLOUD_PROFILE,
                'resource_profile_binding')
        for event in events:
            verify_resource_snapshot(event.get('resources', {}), profile)
            require(event['resources']['peak'] < HEADROOM_BYTES, 'memory_headroom')
            if event['event'] == 'record':
                require(event['resources']['peak'] == event['memory_peak'], 'resource_peak_binding')
        peaks = [event['resources']['peak'] for event in events]
        require(peaks == sorted(peaks), 'resource_peak_regressed')
    require(completed['cold_seconds'] == ready['cold_seconds'], 'cold_binding')
    require(all(isinstance(completed[name], (int, float)) and not isinstance(completed[name], bool)
                and math.isfinite(completed[name]) and completed[name] >= 0
                for name in ('cold_seconds', 'cleanup_seconds', 'session_seconds')), 'timing_invalid')
    checks = timing_checks(timings, completed['cold_seconds'], completed['cleanup_seconds'],
                           completed['session_seconds'], memory['peak'], completed['child_exit'])
    require(completed['checks'] == checks and all(checks.values()), 'performance_failed')
    result = {'checks': checks, 'records': 355, 'retained_prediction_records': predictions,
            'reviewed_article_mentions': next(event['mention_count'] for event in events[2:-1] if event['kind'] == 'reviewed'),
            'peak_bytes': memory['peak'], 'cold_seconds': completed['cold_seconds'],
            'cleanup_seconds': completed['cleanup_seconds'], 'session_seconds': completed['session_seconds']}
    result['resource_profile'] = profile
    if profile == CLOUD_PROFILE:
        quotas = [event['resources']['cpu_quota'] / event['resources']['cpu_period'] for event in events]
        result.update(resource_snapshots=len(events), measured_cpu_fraction_min=min(quotas),
                      measured_cpu_fraction_max=max(quotas),
                      swap_basis_counts=dict(Counter(event['resources']['swap_evidence']['basis'] for event in events)),
                      separate_cloud_configuration_verification_required=True)
    return result


def verify_local(output: Path, freeze_sha: str, docker: str) -> dict:
    frozen = check_freeze(output, freeze_sha)
    claim = read(output / 'local-attempt.json')
    require(claim == read(ROOT / 'data' / CLAIM_NAME), 'attempt_binding')
    require(claim['freeze_sha256'] == freeze_sha and claim['package_id'] == frozen['package_id'], 'attempt_binding')
    info = json.loads((output / 'local-inspect-stdout.bin').read_bytes())[0]
    current = subprocess.run([docker, 'inspect', info['Id']], capture_output=True, check=True, timeout=30)
    require(json.loads(current.stdout)[0] == info, 'container_evidence_changed')
    host, state = info['HostConfig'], info['State']
    require(info['Image'] == claim['image'] and info['Config']['Labels']['lanes.ner-check.package'] == frozen['package_id'],
            'container_identity')
    require(host['NanoCpus'] == 1000000000 and host['Memory'] == host['MemorySwap'] == MEMORY_BYTES
            and host['NetworkMode'] == 'none' and host['ReadonlyRootfs'] and not host.get('Init')
            and host['PidsLimit'] == 128 and host['CapDrop'] == ['ALL']
            and 'no-new-privileges' in host['SecurityOpt'] and not info['Mounts'], 'container_isolation')
    require(not state['Running'] and state['Pid'] == 0 and state['ExitCode'] == 0 and not state['OOMKilled'],
            'container_failed')
    require(info['Config']['User'] == '65532:65532', 'container_user')
    require(read(output / 'local-run-exit.json') == {'returncode': 0}, 'execution_failed')
    events = parse_events((output / 'local-run-stdout.bin').read_bytes())
    rows = read(output / 'context/input/workload.json')['rows']
    result = verify_events(events, frozen, read(output / 'expected.json')['records'], rows)
    result.update(status='passed_local_cloud_check_package', image=claim['image'], freeze_sha256=freeze_sha,
                  package_id=frozen['package_id'], neural_attempts=1, cloud_verified=False, cloud_changes=False,
                  database_connections=0, automatic_processing_connected=False,
                  logs_sha256=digest(output / 'local-run-stdout.bin'), verifier_sha256=digest(Path(__file__)))
    write(output / 'local-verification.json', result)
    return result


def cloud_plan(output: Path, freeze_sha: str) -> dict:
    frozen = check_freeze(output, freeze_sha)
    verified = read(output / 'local-verification.json')
    require(verified['freeze_sha256'] == freeze_sha and verified['package_id'] == frozen['package_id']
            and verified['status'] == 'passed_local_cloud_check_package', 'local_verification_required')
    return {'approval_required': True, 'project': PROJECT, 'region': REGION, 'job': JOB,
            'service_account': SERVICE_ACCOUNT, 'runtime_project_roles': [], 'secrets': [],
            'database_access': False, 'scheduled': False, 'limits': LIMITS,
            'local_image': verified['image'], 'package_id': frozen['package_id'],
            'registry_tag': f'{REGION}-docker.pkg.dev/{PROJECT}/lanes/{JOB}:{frozen["package_id"][:20]}',
            'registry_digest_required_before_create': True, 'cloud_changes_performed': False}


def verify_diagnostics(events: list[dict], package_id: str) -> dict:
    """Diagnostic success means evidence collected, never successful inference."""
    require(len(events) == 1, 'diagnostic_event_count')
    event = events[0]
    require(event['schema'] == SCHEMA and event['event'] == 'diagnostics'
            and event['diagnostic_schema'] == DIAGNOSTIC_SCHEMA and event['package_id'] == package_id,
            'diagnostic_binding')
    require(event['inference_started'] is False and event['qualification_passed'] is False
            and event['asset_validation_passed'] is True, 'diagnostic_scope')
    require(set(event['resource_files']) == set(RESOURCE_FILES), 'diagnostic_membership')
    require(all(value['status'] in ('readable', 'missing', 'unavailable')
                for value in event['resource_files'].values()), 'diagnostic_file_status')
    require(isinstance(event['resource_check']['passed'], bool), 'diagnostic_resource_status')
    require(event['isolation_probe']['status'] in ('passed', 'failed'), 'diagnostic_isolation_status')
    require(event['process']['pid'] > 0 and event['process']['parent_pid'] >= 0, 'diagnostic_process')
    readings = event['resource_readings']
    require(readings['status'] in ('readable', 'unavailable'), 'diagnostic_readings_status')
    require(event['swap_inventory']['status'] in ('readable', 'unavailable')
            and event['swap_inventory']['establishes_container_swap_limit'] is False, 'diagnostic_swap_scope')
    swap = event['swap_inventory']
    if swap['status'] == 'readable':
        require(all(type(swap[key]) is int and swap[key] >= 0 for key in
                ('active_devices', 'total_bytes', 'free_bytes')) and swap['free_bytes'] <= swap['total_bytes'],
                'diagnostic_swap_invalid')
        require(swap['host_reports_no_swap'] is (swap['active_devices'] == swap['total_bytes'] == swap['free_bytes'] == 0),
                'diagnostic_swap_claim')
    if readings['status'] == 'readable':
        values = readings['values']
        require(values['layout'] in ('v1', 'v2') and all(type(values[key]) is int for key in
                ('cpu_quota', 'cpu_period', 'memory_max', 'peak')), 'diagnostic_readings_invalid')
        require(values['cpu_period'] > 0 and values['memory_max'] > 0 and values['peak'] >= 0
                and (values['swap_max'] is None or type(values['swap_max']) is int and values['swap_max'] >= 0),
                'diagnostic_readings_invalid')
        require(event['resource_profile'] in RESOURCE_PROFILES
                and values['profile'] == event['resource_profile'], 'diagnostic_profile_binding')
        if event['resource_profile'] == CLOUD_PROFILE:
            require(values['swap_evidence']['host'] == event['swap_inventory'], 'diagnostic_swap_binding')
        try:
            verify_resource_snapshot(values, event['resource_profile'])
            expected_pass = True
        except ValueError:
            expected_pass = False
        require(event['resource_check']['passed'] is expected_pass, 'diagnostic_resource_claim')
        if expected_pass:
            require(event['resource_check']['resources'] == values, 'diagnostic_resource_binding')
    else:
        require(event['resource_check']['passed'] is False, 'diagnostic_resource_claim')
    return event


def diagnose_local(output: Path, freeze_sha: str, docker: str) -> dict:
    frozen = check_freeze(output, freeze_sha)
    ready = read(output / 'build-ready.json')
    require(ready['freeze_sha256'] == freeze_sha and ready['package_id'] == frozen['package_id'], 'build_binding')
    image = ready['image']
    require(inspect_image(docker, image)['Id'] == image, 'image_identity')
    write(output / 'diagnostic-attempt.json', {'scope': 'local_environment_diagnostics_only',
          'package_id': frozen['package_id'], 'image': image, 'inference_authorized': False})
    name = output.name + '-diagnostics'
    args = container_args(docker, name, image, frozen['package_id']) + ['--diagnostic-only']
    require(command(args, output, 'diagnostic-create').returncode == 0, 'diagnostic_create_failed')
    require(command([docker, 'start', '-a', name], output, 'diagnostic-run', timeout=60).returncode == 0,
            'diagnostic_failed')
    event = verify_diagnostics(parse_events((output / 'diagnostic-run-stdout.bin').read_bytes()), frozen['package_id'])
    require(event['process']['pid'] > 1 and event['isolation_probe']['parent_pid'] == event['process']['pid']
            and event['isolation_probe']['status'] == 'passed'
            and event['isolation_probe']['isolation'] == {'seccomp': True, 'socket_families_denied': [2, 10, 1],
                 'raw_socket_denied': True, 'parent_death_signal': True}, 'local_supervision_isolation_failed')
    require(command([docker, 'inspect', name], output, 'diagnostic-inspect').returncode == 0, 'diagnostic_inspect_failed')
    info = json.loads((output / 'diagnostic-inspect-stdout.bin').read_bytes())[0]
    require(info['Image'] == image and not info['State']['Running'] and info['State']['ExitCode'] == 0
            and info['Config']['Labels']['lanes.ner-check.package'] == frozen['package_id'], 'diagnostic_container_binding')
    host = info['HostConfig']
    require(not host.get('Init') and host['NanoCpus'] == 1000000000
            and host['Memory'] == host['MemorySwap'] == MEMORY_BYTES and host['NetworkMode'] == 'none'
            and host['ReadonlyRootfs'] and host['CapDrop'] == ['ALL']
            and 'no-new-privileges' in host['SecurityOpt'] and not info['Mounts'], 'diagnostic_container_isolation')
    result = {'status': 'passed_local_diagnostic_collection', 'package_id': frozen['package_id'], 'image': image,
              'freeze_sha256': freeze_sha, 'inference_started': False, 'cloud_changes': False,
              'supervision_verified': True, 'diagnostics': event}
    write(output / 'local-diagnostics.json', result)
    return result


def diagnostic_plan(output: Path, freeze_sha: str) -> dict:
    frozen = check_freeze(output, freeze_sha)
    verified = read(output / 'local-diagnostics.json')
    require(verified['status'] == 'passed_local_diagnostic_collection' and verified['freeze_sha256'] == freeze_sha
            and verified['package_id'] == frozen['package_id'] and verified['supervision_verified'] is True,
            'local_diagnostics_required')
    return {'approval_required': True, 'scope': 'diagnostic_only_no_model_session', 'project': PROJECT,
            'region': REGION, 'job': JOB, 'service_account': SERVICE_ACCOUNT, 'limits': LIMITS,
            'local_image': verified['image'], 'package_id': frozen['package_id'],
            'resource_profile': frozen['identity'].get('resource_profile', STRICT_PROFILE), 'args': ['--diagnostic-only'],
            'registry_tag': f'{REGION}-docker.pkg.dev/{PROJECT}/lanes/{JOB}:diagnostic-{frozen["package_id"][:20]}',
            'registry_digest_required_before_update': True, 'execution_requires_separate_approval': True,
            'cloud_changes_performed': False, 'qualification_passed': False}


def cloud_qualification_plan(output: Path, freeze_sha: str) -> dict:
    frozen = check_freeze(output, freeze_sha)
    require(frozen['identity']['resource_profile'] == CLOUD_PROFILE, 'cloud_profile_required')
    proposal = diagnostic_plan(output, freeze_sha)
    local = read(output / 'local-diagnostics.json')
    require(local['diagnostics']['resource_check']['passed'] is True, 'local_resource_preflight_required')
    proposal.update(scope='proposed_single_full_cloud_qualification', args=[],
                    execution_requires_separate_approval=True, inference_authorized=False,
                    resource_profile=CLOUD_PROFILE, external_cloud_configuration_verification_required=True,
                    external_frozen_prediction_comparison_required=True,
                    cpu_measurement_is_not_configured_cpu=True,
                    swap_basis='enforced_zero_limit_or_repeated_no_host_swap',
                    registry_tag=f'{REGION}-docker.pkg.dev/{PROJECT}/lanes/{JOB}:cloud-profile-{frozen["package_id"][:20]}')
    return proposal


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resource-profile', choices=RESOURCE_PROFILES, default=STRICT_PROFILE)
    parser.add_argument('operation', choices=['prepare', 'build', 'execute-local', 'verify-local', 'cloud-plan',
                                            'diagnose-local', 'diagnostic-plan', 'cloud-qualification-plan'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--freeze-sha256', default='')
    parser.add_argument('--docker', default='docker')
    args = parser.parse_args()
    output = args.output.resolve()
    operations = {'build': build, 'execute-local': execute_local, 'verify-local': verify_local,
                  'diagnose-local': diagnose_local}
    try:
        require(args.operation == 'prepare' or args.resource_profile == STRICT_PROFILE,
                'profile_is_frozen_during_prepare')
        if args.operation == 'prepare':
            result = prepare(output, args.resource_profile)
        elif args.operation == 'cloud-plan':
            result = cloud_plan(output, args.freeze_sha256)
        elif args.operation == 'diagnostic-plan':
            result = diagnostic_plan(output, args.freeze_sha256)
        elif args.operation == 'cloud-qualification-plan':
            result = cloud_qualification_plan(output, args.freeze_sha256)
        else:
            result = operations[args.operation](output, args.freeze_sha256, args.docker)
    except Exception as exc:
        code = str(exc) if isinstance(exc, ValueError) and re.fullmatch(r'[a-z_]{1,80}', str(exc)) else 'ner_cloud_check_failed'
        print(json.dumps({'status': 'requires_attention', 'error_code': code,
                          'error_type': type(exc).__name__, 'cloud_changes': False}))
        return 1
    print(json.dumps(result, allow_nan=False))
    return int(result.get('status', '').startswith('failed'))


if __name__ == '__main__':
    raise SystemExit(main())
