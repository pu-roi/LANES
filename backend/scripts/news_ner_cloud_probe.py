"""Inference-only qualification probe. No ORM, credentials, HTTP or cloud SDK."""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import signal
import sys
import time

sys.path.insert(0, '/app')
from app.services.news_ner.bundle import digest, verify_bundle
from app.services.news_ner.contract import object_sha, require
from app.services.news_ner_runtime.protocol import code_bindings, validate_request
from app.services.news_ner_runtime.supervisor import Session

SCHEMA = 'lanes-ner-cloud-check-v1'
MEMORY_BYTES = 3 * 1024**3
HEADROOM_BYTES = 2688 * 1024**2
COUNTS = {'passage': 345, 'article': 6, 'stress': 3, 'reviewed': 1}
FORBIDDEN_NAMES = {'DATABASE_URL', 'SECRET_KEY', 'GOOGLE_APPLICATION_CREDENTIALS',
                   'OPENROUTER_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY'}
DIAGNOSTIC_SCHEMA = 'lanes-ner-cloud-environment-v3'
STRICT_PROFILE = 'local-strict-v1'
CLOUD_PROFILE = 'cloud-run-v1'
RESOURCE_PROFILES = (STRICT_PROFILE, CLOUD_PROFILE)
RESOURCE_FILES = {
    'v2_cpu': 'cpu.max', 'v2_memory_limit': 'memory.max',
    'v2_swap_limit': 'memory.swap.max', 'v2_memory_peak': 'memory.peak',
    'v1_cpu_quota': 'cpu/cpu.cfs_quota_us', 'v1_cpu_period': 'cpu/cpu.cfs_period_us',
    'v1_cpu_combined_quota': 'cpu,cpuacct/cpu.cfs_quota_us',
    'v1_cpu_combined_period': 'cpu,cpuacct/cpu.cfs_period_us',
    'v1_memory_limit': 'memory/memory.limit_in_bytes',
    'v1_memory_peak': 'memory/memory.max_usage_in_bytes',
    'v1_memory_and_swap_limit': 'memory/memory.memsw.limit_in_bytes',
    'v1_memory_and_swap_peak': 'memory/memory.memsw.max_usage_in_bytes',
}
STARTUP_FILES = {'/input/check.json': 'check_configuration', '/input/request.json': 'request_configuration',
                 '/input/workload.json': 'qualification_workload', '/assets/manifest.json': 'model_manifest'}


class StartupFailure(RuntimeError):
    """Safe startup context; never retain exception messages or arbitrary filenames."""

    def __init__(self, stage: str, error: Exception) -> None:
        super().__init__('startup_check_failed')
        self.stage = stage
        self.error_type = type(error).__name__
        self.resource_key = getattr(error, 'resource_key', None)
        self.startup_file = STARTUP_FILES.get(str(getattr(error, 'filename', '')))


def emit(event: str, package_id: str, **values: object) -> None:
    """Only hashes, bounded identities and measurements leave the container."""
    print(json.dumps({'schema': SCHEMA, 'event': event, 'package_id': package_id, **values},
                     allow_nan=False, separators=(',', ':')), flush=True)


def guard_environment(environ: dict[str, str]) -> None:
    require(environ.get('LANES_NER_CHECK_PROFILE') == 'isolated', 'check_profile_required')
    require(not any(name in environ for name in FORBIDDEN_NAMES), 'credentials_prohibited')
    require(not any(name.endswith(('_API_KEY', '_PASSWORD', '_SECRET', '_TOKEN'))
                    for name in environ), 'credentials_prohibited')
    require(environ.get('CLOUD_RUN_TASK_ATTEMPT', '0') == '0', 'retry_prohibited')
    require(environ.get('CLOUD_RUN_TASK_COUNT', '1') == '1'
            and environ.get('CLOUD_RUN_TASK_INDEX', '0') == '0', 'single_task_required')


def read_resource(root: Path, key: str) -> str:
    try:
        with (root / RESOURCE_FILES[key]).open(encoding='ascii') as stream:
            value = stream.read(129).strip()
        require(len(value) <= 128, 'resource_text_limit')
        return value
    except OSError as error:
        error.resource_key = key
        raise


def swap_inventory(proc: Path = Path('/proc')) -> dict:
    """Bounded host swap facts, never filenames or a substitute for a swap limit."""
    try:
        with (proc / 'swaps').open(encoding='ascii') as stream:
            text = stream.read(65537)
        require(len(text) <= 65536, 'swap_inventory_limit')
        lines = text.splitlines()
        require(bool(lines) and lines[0].split() == ['Filename', 'Type', 'Size', 'Used', 'Priority'],
                'swap_inventory_format')
        rows = [line.split() for line in lines[1:] if line.strip()]
        require(all(len(row) == 5 and row[2].isdigit() and row[3].isdigit() for row in rows),
                'swap_inventory_format')
        with (proc / 'meminfo').open(encoding='ascii') as stream:
            info = stream.read(65537)
        require(len(info) <= 65536, 'swap_inventory_limit')
        selected = {}
        for line in info.splitlines():
            parts = line.split()
            if parts and parts[0] in ('SwapTotal:', 'SwapFree:'):
                require(len(parts) == 3 and parts[1].isdigit() and parts[2] == 'kB'
                        and parts[0] not in selected, 'swap_inventory_format')
                selected[parts[0]] = int(parts[1]) * 1024
        require(set(selected) == {'SwapTotal:', 'SwapFree:'}, 'swap_inventory_incomplete')
        return {'status': 'readable', 'active_devices': len(rows),
                'total_bytes': selected['SwapTotal:'], 'free_bytes': selected['SwapFree:'],
                'host_reports_no_swap': not rows and selected['SwapTotal:'] == selected['SwapFree:'] == 0,
                'establishes_container_swap_limit': False}
    except (OSError, ValueError) as error:
        return {'status': 'unavailable', 'error_type': type(error).__name__,
                'establishes_container_swap_limit': False}


def resource_readings(root: Path = Path('/sys/fs/cgroup')) -> dict:
    """Read either controller layout; never fall back from invalid partial v2 data."""
    if (root / RESOURCE_FILES['v2_cpu']).exists():
        words = read_resource(root, 'v2_cpu').split()
        require(len(words) == 2 and all(word.isdecimal() for word in words), 'cpu_limit_required')
        quota, period = map(int, words)
        memory = int(read_resource(root, 'v2_memory_limit'))
        swap = int(read_resource(root, 'v2_swap_limit'))
        peak = int(read_resource(root, 'v2_memory_peak'))
        layout = 'v2'
        combined = None
    else:
        combined_cpu = (root / RESOURCE_FILES['v1_cpu_combined_quota']).exists()
        prefix = 'v1_cpu_combined_' if combined_cpu else 'v1_cpu_'
        quota = int(read_resource(root, prefix + 'quota'))
        period = int(read_resource(root, prefix + 'period'))
        memory = int(read_resource(root, 'v1_memory_limit'))
        combined = int(read_resource(root, 'v1_memory_and_swap_limit'))
        require(combined >= memory, 'memory_swap_limit_invalid')
        # Large kernel sentinel values mean effectively unbounded; do not invent
        # zero swap. Strings preserve these integers through Cloud Logging Struct.
        swap = combined - memory if combined < 2**60 else None
        peak = int(read_resource(root, 'v1_memory_peak'))
        layout = 'v1'
    require(period > 0 and peak >= 0 and memory > 0 and (swap is None or swap >= 0), 'resource_values_invalid')
    return {'layout': layout, 'cpu_quota': quota, 'cpu_period': period,
            'memory_max': memory, 'swap_max': swap, 'peak': peak,
            'memory_and_swap_limit_decimal': str(combined) if combined is not None else None}


def resource_snapshot(root: Path = Path('/sys/fs/cgroup'), *, profile: str = STRICT_PROFILE,
                      proc: Path = Path('/proc')) -> dict:
    require(profile in RESOURCE_PROFILES, 'resource_profile_invalid')
    value = resource_readings(root)
    value['profile'] = profile
    if profile == CLOUD_PROFILE:
        host = swap_inventory(proc)
        basis = 'enforced_zero_limit' if value['swap_max'] == 0 else 'host_no_swap'
        value['swap_evidence'] = {'basis': basis, 'host': host}
    return value


def validate_resources(value: dict, *, profile: str = STRICT_PROFILE) -> None:
    require(profile in RESOURCE_PROFILES, 'resource_profile_invalid')
    if profile == STRICT_PROFILE:
        require(value['cpu_quota'] == value['cpu_period'] > 0, 'cpu_limit_required')
        require(value['memory_max'] == MEMORY_BYTES and value['swap_max'] == 0, 'memory_limit_required')
    else:
        require(value['cpu_quota'] > 0 and value['cpu_period'] > 0, 'cpu_limit_required')
        require(value['memory_max'] == MEMORY_BYTES, 'memory_limit_required')
        evidence = value['swap_evidence']
        if evidence['basis'] == 'enforced_zero_limit':
            require(value['swap_max'] == 0, 'swap_evidence_required')
        else:
            host = evidence['host']
            require(evidence['basis'] == 'host_no_swap' and host.get('status') == 'readable'
                    and host.get('host_reports_no_swap') is True
                    and host.get('active_devices') == host.get('total_bytes') == host.get('free_bytes') == 0
                    and host.get('establishes_container_swap_limit') is False, 'swap_evidence_required')


def resources(root: Path = Path('/sys/fs/cgroup'), *, profile: str = STRICT_PROFILE,
              proc: Path = Path('/proc')) -> dict:
    value = resource_snapshot(root, profile=profile, proc=proc)
    validate_resources(value, profile=profile)
    return value


def resource_inventory(root: Path = Path('/sys/fs/cgroup')) -> dict[str, dict]:
    """Read only known resource files; report numbers, not arbitrary file contents."""
    result = {}
    for key, relative in RESOURCE_FILES.items():
        try:
            with (root / relative).open(encoding='utf-8') as stream:
                text = stream.read(129).strip()
            require(len(text) <= 128, 'resource_text_limit')
            words = text.split()
            require(0 < len(words) <= 2 and all(w == 'max' or w.lstrip('-').isdigit() for w in words),
                    'resource_format')
            result[key] = {'status': 'readable', 'values': [w if w == 'max' or abs(int(w)) > 2**53 - 1 else int(w) for w in words]}
        except FileNotFoundError:
            result[key] = {'status': 'missing'}
        except (OSError, ValueError) as error:
            result[key] = {'status': 'unavailable', 'error_type': type(error).__name__}
    return result


def cgroup_mounts(path: Path = Path('/proc/self/mountinfo')) -> list[dict]:
    """Bounded mount metadata only; no environment, credentials or source text."""
    with path.open(encoding='utf-8') as stream:
        text = stream.read(65537)
    require(len(text) <= 65536, 'mount_metadata_limit')
    result = []
    for line in text.splitlines():
        before, separator, after = line.partition(' - ')
        if not separator:
            continue
        fields, tail = before.split(), after.split()
        if tail and tail[0] in ('cgroup', 'cgroup2'):
            require(len(fields) >= 5 and len(tail) >= 3, 'mount_metadata_invalid')
            require(fields[4].startswith('/sys/fs/cgroup') and len(fields[4]) <= 160, 'mount_location_invalid')
            result.append({'type': tail[0], 'mount_point': fields[4],
                           'controllers': [word for word in tail[2].split(',')
                                           if word in ('cpu', 'cpuacct', 'memory', 'pids')]})
    require(len(result) <= 32, 'mount_count_limit')
    return result


async def isolation_diagnostic() -> dict:
    """Exercise unchanged isolation in a short child; never import/load the model."""
    program = '''import json,os,sys
sys.path.insert(0,"/app")
from app.services.news_ner_runtime.isolation import install
value={"pid":os.getpid(),"parent_pid":os.getppid()}
try:
 value.update(status="passed",isolation=install())
except Exception as error:
 codes={"isolation_unsupported","parent_guard_failed","seccomp_failed","socket_denial_failed","raw_socket_denial_failed"}
 value.update(status="failed",error_type=type(error).__name__,error_code=str(error) if str(error) in codes else "isolation_check_failed")
print(json.dumps(value))
'''
    environment = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}
    process = await asyncio.create_subprocess_exec(sys.executable, '-I', '-B', '-c', program,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, env=environment,
        close_fds=True, start_new_session=True, limit=8192)
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(), 10)
        require(len(stdout) <= 8192 and process.returncode == 0, 'diagnostic_child_failed')
        value = json.loads(stdout)
        require(value.get('status') in ('passed', 'failed'), 'diagnostic_child_invalid')
        return value
    finally:
        if process.returncode is None:
            process.kill()
        await asyncio.wait_for(process.wait(), 5)


async def diagnose(config: dict, root: Path = Path('/sys/fs/cgroup')) -> None:
    inventory = resource_inventory(root)
    profile = config.get('resource_profile', STRICT_PROFILE)
    measured = {'status': 'unavailable'}
    try:
        measured = {'status': 'readable', 'values': resource_snapshot(root, profile=profile)}
        validate_resources(measured['values'], profile=profile)
        limits = {'passed': True, 'resources': measured['values']}
    except (OSError, ValueError) as error:
        if measured['status'] == 'unavailable':
            measured.update(error_type=type(error).__name__, resource_key=getattr(error, 'resource_key', None))
        limits = {'passed': False, 'error_type': type(error).__name__,
                  'resource_key': getattr(error, 'resource_key', None),
                  'error_code': str(error) if str(error) in ('cpu_limit_required', 'memory_limit_required',
                                'resource_values_invalid', 'memory_swap_limit_invalid', 'swap_evidence_required') else 'resource_check_failed'}
    try:
        mounts = {'status': 'readable', 'entries': cgroup_mounts()}
    except (OSError, ValueError) as error:
        mounts = {'status': 'unavailable', 'error_type': type(error).__name__}
    isolation = await isolation_diagnostic()
    emit('diagnostics', config['package_id'], diagnostic_schema=DIAGNOSTIC_SCHEMA,
         inference_started=False, qualification_passed=False, asset_validation_passed=True,
         process={'pid': os.getpid(), 'parent_pid': os.getppid()}, resource_files=inventory,
         resource_profile=profile, resource_check=limits, resource_readings=measured,
         swap_inventory=(measured['values']['swap_evidence']['host']
                         if profile == CLOUD_PROFILE and measured['status'] == 'readable' else swap_inventory()),
         cgroup_mounts=mounts, isolation_probe=isolation)


def stable_result(result: dict) -> dict:
    return {name: result[name] for name in ('proposal', 'graph', 'provenance')}


def load_inputs(root: Path = Path('/input'), services: Path = Path('/app/app/services'),
                assets: Path = Path('/assets')) -> tuple[dict, dict, list[dict]]:
    config = json.loads((root / 'check.json').read_text(encoding='utf-8'))
    require(set(config) == {'schema', 'package_id', 'request_sha256', 'workload_sha256', 'counts', 'resource_profile'},
            'configuration_membership')
    require(config['schema'] == SCHEMA and config['counts'] == COUNTS
            and config['resource_profile'] in RESOURCE_PROFILES, 'configuration_invalid')
    require(digest(root / 'request.json') == config['request_sha256']
            and digest(root / 'workload.json') == config['workload_sha256'], 'input_changed')
    request = json.loads((root / 'request.json').read_text(encoding='utf-8'))
    require(set(request) == {'bundle_sha256', 'code'}, 'request_configuration')
    verify_bundle(assets, request['bundle_sha256'])
    require(code_bindings(services) == request['code'], 'runtime_code_changed')
    rows = json.loads((root / 'workload.json').read_text(encoding='utf-8'))['rows']
    require(dict(Counter(row['kind'] for row in rows)) == COUNTS, 'workload_membership')
    require(len({row['record_id'] for row in rows}) == len(rows), 'duplicate_record')
    for row in rows:
        validate_request({name: row[name] for name in ('record_id', 'text', 'text_sha256', 'publication')})
    require({path.name for path in root.iterdir()} == {'check.json', 'request.json', 'workload.json'},
            'unexpected_input')
    return config, request, rows


def timing_checks(timings: dict[str, list[float]], cold: float, cleanup: float,
                  session: float, peak: int, child_exit: int) -> dict[str, bool]:
    passages = sorted(timings['passage'])
    longest = max(value for values in timings.values() for value in values)
    return {'cold': cold <= 60, 'passage_p95': passages[math.ceil(.95 * len(passages)) - 1] <= 1,
            'articles': max(timings['article'] + timings['reviewed']) <= 30,
            'stress': max(timings['stress']) <= 60, 'headroom': peak < HEADROOM_BYTES,
            'cleanup': cleanup <= 5 and child_exit == 0, 'session': session < 450,
            'startup_request_cleanup': cold + longest + cleanup <= 125}


async def qualify(config: dict, request: dict, rows: list[dict]) -> None:
    package_id = config['package_id']
    profile = config.get('resource_profile', STRICT_PROFILE)
    timings: dict[str, list[float]] = {kind: [] for kind in COUNTS}
    session = Session(request['bundle_sha256'], request['code'])
    completed = 0
    try:
        started = time.monotonic()
        ready = await session.start()
        cold = time.monotonic() - started
        require(cold <= 60, 'cold_deadline')
        emit('ready', package_id, provenance=ready['provenance'], isolation=ready['isolation'], cold_seconds=cold,
             resource_profile=profile, resources=resources(profile=profile))
        for row in rows:
            source = {name: row[name] for name in ('record_id', 'text', 'text_sha256', 'publication')}
            started = time.monotonic()
            result = await session.request(source, timeout=60 if row['kind'] == 'stress' else 30)
            elapsed = time.monotonic() - started
            timings[row['kind']].append(elapsed)
            memory = resources(profile=profile)
            require(memory['peak'] < HEADROOM_BYTES, 'memory_headroom')
            mentions = result['proposal']['neural_mentions']
            predictions = [[mention['start'], mention['end'], mention['label']] for mention in mentions]
            emit('record', package_id, record_id=row['record_id'], kind=row['kind'],
                 result_sha256=object_sha(stable_result(result)), predictions_sha256=object_sha(predictions),
                 mention_count=len(mentions), elapsed_seconds=elapsed, memory_peak=memory['peak'], resources=memory)
            completed += 1
    finally:
        await session.close()
    memory = resources(profile=profile)
    checks = timing_checks(timings, cold, session.cleanup_seconds, time.monotonic() - session.started,
                           memory['peak'], session.proc.returncode)
    require(all(checks.values()), 'performance_checks_failed')
    emit('completed', package_id, checks=checks, completed=completed,
         counts={kind: len(values) for kind, values in timings.items()}, timings=timings,
         cold_seconds=cold, cleanup_seconds=session.cleanup_seconds, child_exit=session.proc.returncode,
         session_seconds=time.monotonic() - session.started, resources=memory)


async def run(preflight_only: bool, diagnostic_only: bool = False) -> None:
    stage = 'environment'
    try:
        guard_environment(dict(os.environ))
        stage = 'platform'
        require(platform.system() == 'Linux' and platform.machine() == 'x86_64'
                and sys.version_info[:2] == (3, 12), 'platform_required')
        require(importlib.metadata.version('spacy') == '3.7.5', 'spacy_version_required')
        if diagnostic_only:
            stage = 'input_and_asset_validation'
            config, _request, _rows = load_inputs()
            stage = 'environment_diagnostics'
            await diagnose(config)
            return
        stage = 'input_and_asset_validation'
        config, request, rows = load_inputs()
        stage = 'resource_check'
        limits = resources(profile=config['resource_profile'])
    except Exception as error:
        raise StartupFailure(stage, error) from None
    emit('preflight', config['package_id'], resources=limits, workload_count=len(rows),
         inference_started=False, preflight_only=preflight_only, resource_profile=config['resource_profile'])
    if preflight_only:
        return
    task = asyncio.current_task()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, task.cancel)
    try:
        await qualify(config, request, rows)
    finally:
        loop.remove_signal_handler(signal.SIGTERM)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--preflight-only', action='store_true')
    mode.add_argument('--diagnostic-only', action='store_true')
    args = parser.parse_args()
    try:
        asyncio.run(run(args.preflight_only, args.diagnostic_only))
    except StartupFailure as error:
        emit('failed', '', error_code='ner_check_failed', error_type=error.error_type,
             startup_stage=error.stage, required_resource=error.resource_key, required_startup_file=error.startup_file)
        return 1
    except BaseException as exc:
        emit('failed', '', error_code='ner_check_failed', error_type=type(exc).__name__)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
