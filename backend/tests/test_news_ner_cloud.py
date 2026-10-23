"""Cloud-check boundaries and independent verification; no model, DB or cloud calls."""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1] / 'scripts')]
import qualify_news_ner_cloud as controller
import news_ner_cloud_probe as probe
import news_ner_cloud_entrypoint as launcher

requires_retained_artifacts = pytest.mark.skipif(
    not (controller.PREVIOUS / 'final-package-manifest.json').is_file()
    or not (controller.BUNDLE / 'manifest.json').is_file(),
    reason='Authenticated private model/qualification receipts must be provisioned for artifact checks')


@requires_retained_artifacts
def test_runtime_code_and_model_are_the_previously_qualified_identities():
    request = controller.read(controller.PREVIOUS / 'input/request.json')
    assert controller.code_bindings(controller.BACKEND / 'app/services') == request['code']
    assert request['bundle_sha256'] == controller.BUNDLE_SHA
    assert controller.verify_bundle(controller.BUNDLE, controller.BUNDLE_SHA)


@requires_retained_artifacts
def test_retained_oracles_cover_full_workload_without_inference():
    assert controller.authenticate_previous() == controller.PREVIOUS_PINS
    expected = controller.expected_records()
    assert len(expected) == 355
    assert sum(row['predictions_sha256'] is not None for row in expected) == 352


@pytest.mark.parametrize('name', ['DATABASE_URL', 'SECRET_KEY', 'GOOGLE_APPLICATION_CREDENTIALS',
                                 'GEMINI_API_KEY', 'OTHER_API_KEY', 'SERVICE_PASSWORD', 'SERVICE_TOKEN'])
def test_probe_rejects_inherited_credentials_even_if_empty(name):
    with pytest.raises(ValueError, match='credentials_prohibited'):
        probe.guard_environment({'LANES_NER_CHECK_PROFILE': 'isolated', name: ''})


@pytest.mark.parametrize('changes', [{'LANES_NER_CHECK_PROFILE': 'production'}, {'CLOUD_RUN_TASK_ATTEMPT': '1'},
                                   {'CLOUD_RUN_TASK_COUNT': '2'}, {'CLOUD_RUN_TASK_INDEX': '1'}])
def test_probe_rejects_unapproved_profile_retries_and_parallel_tasks(changes):
    with pytest.raises(ValueError):
        probe.guard_environment({'LANES_NER_CHECK_PROFILE': 'isolated', **changes})


def test_probe_allows_only_credential_free_first_execution():
    probe.guard_environment({'LANES_NER_CHECK_PROFILE': 'isolated', 'CLOUD_RUN_TASK_ATTEMPT': '0',
                             'CLOUD_RUN_TASK_COUNT': '1', 'CLOUD_RUN_TASK_INDEX': '0', 'GPG_KEY': 'public'})


@pytest.fixture
def cgroup(tmp_path):
    for name, value in {'cpu.max': '100000 100000', 'memory.max': str(probe.MEMORY_BYTES),
                        'memory.swap.max': '0', 'memory.peak': '1024'}.items():
        (tmp_path / name).write_text(value, encoding='utf-8')
    return tmp_path


@pytest.mark.parametrize('name,value', [('cpu.max', 'max 100000'), ('cpu.max', '200000 100000'),
                                      ('memory.max', str(1024**3)), ('memory.max', 'max'),
                                      ('memory.swap.max', '1024')])
def test_insufficient_or_unbounded_cloud_resources_fail_closed(cgroup, name, value):
    (cgroup / name).write_text(value, encoding='utf-8')
    with pytest.raises(ValueError):
        probe.resources(cgroup)


def test_unavailable_cgroup_measurement_is_not_a_pass(cgroup):
    (cgroup / 'memory.peak').unlink()
    with pytest.raises(FileNotFoundError):
        probe.resources(cgroup)


def test_local_container_has_no_database_or_oracle_mount_and_has_same_limits():
    args = controller.container_args('docker', 'fictional', 'image', 'a' * 64)
    assert args[args.index('--cpus') + 1] == '1'
    assert args[args.index('--memory') + 1] == args[args.index('--memory-swap') + 1] == str(3 * 1024**3)
    assert args[args.index('--network') + 1] == 'none'
    assert '--mount' not in args and '--env' not in args and '--volume' not in args
    assert '--init' not in args  # The image supplies its own reviewed supervisor.
    assert '--read-only' in args and '--cap-drop=ALL' in args and '--security-opt=no-new-privileges' in args


def test_digest_covers_graph_and_predictions_without_volatile_timings():
    original = {'proposal': {'text': 'evidence'}, 'graph': {'groups': []}, 'provenance': {'bundle': 'pin'},
                'measurements': {'seconds': 1}}
    repeated = deepcopy(original)
    repeated['measurements']['seconds'] = 20
    assert controller.object_sha(probe.stable_result(original)) == controller.object_sha(probe.stable_result(repeated))
    repeated['graph']['groups'].append({'id': 'changed'})
    assert controller.object_sha(probe.stable_result(original)) != controller.object_sha(probe.stable_result(repeated))


@pytest.mark.parametrize('data', [b'{"schema":"x"}\n',
                                b'{"schema":"lanes-ner-cloud-check-v1","x":1,"x":2}\n',
                                b'{"schema":"lanes-ner-cloud-check-v1","elapsed":NaN}\n',
                                b'{}' * (1024**2 + 1)], ids=['schema', 'duplicate-key', 'nonfinite', 'oversize'])
def test_malformed_ambiguous_or_unbounded_logs_are_rejected(data):
    with pytest.raises((ValueError, json.JSONDecodeError)):
        controller.parse_events(data)


@pytest.fixture
def execution():
    rows, expected, records = [], [], []
    timings = {kind: [] for kind in probe.COUNTS}
    for kind, count in probe.COUNTS.items():
        for index in range(count):
            record_id = f'{kind}_{index}'
            rows.append({'kind': kind, 'record_id': record_id})
            expected.append({'record_id': record_id, 'result_sha256': 'result',
                             'predictions_sha256': None if kind == 'stress' else 'prediction',
                             'mention_count': 53 if kind == 'reviewed' else 2})
            records.append({'event': 'record', 'package_id': 'package', 'record_id': record_id, 'kind': kind,
                            'result_sha256': 'result', 'predictions_sha256': 'prediction',
                            'mention_count': 53 if kind == 'reviewed' else 2,
                            'elapsed_seconds': .1, 'memory_peak': 1024})
            timings[kind].append(.1)
    checks = probe.timing_checks(timings, 2, .1, 40, 1024, 0)
    events = [{'event': 'preflight', 'package_id': 'package', 'preflight_only': False, 'inference_started': False},
              {'event': 'ready', 'package_id': 'package', 'cold_seconds': 2,
               'isolation': {'seccomp': True, 'socket_families_denied': [2, 10, 1],
                             'raw_socket_denied': True, 'parent_death_signal': True},
               'provenance': {'bundle_sha256': controller.BUNDLE_SHA}}, *records,
              {'event': 'completed', 'package_id': 'package', 'completed': 355, 'counts': probe.COUNTS,
               'timings': timings, 'checks': checks, 'cold_seconds': 2, 'cleanup_seconds': .1,
               'session_seconds': 40, 'child_exit': 0,
               'resources': {'memory_max': probe.MEMORY_BYTES, 'swap_max': 0,
                             'cpu_quota': 100000, 'cpu_period': 100000, 'peak': 1024}}]
    return events, {'package_id': 'package', 'identity': {'provenance': {'bundle_sha256': controller.BUNDLE_SHA}}}, expected, rows


def test_complete_matching_results_are_independently_verified(execution):
    result = controller.verify_events(*execution)
    assert result['records'] == 355 and result['retained_prediction_records'] == 352
    assert result['reviewed_article_mentions'] == 53 and all(result['checks'].values())


@pytest.mark.parametrize('tamper', ['duplicate', 'missing', 'graph', 'neural', 'isolation', 'model', 'memory',
                                  'retry_binding', 'cleanup', 'forged_performance', 'timing', 'unknown_hour', 'negative_time'])
def test_success_or_count_claims_cannot_hide_corruption(execution, tamper):
    events, frozen, expected, rows = execution
    if tamper == 'duplicate':
        events[3] = deepcopy(events[2])
    elif tamper == 'missing':
        events.pop(3)
    elif tamper == 'graph':
        events[2]['result_sha256'] = 'modified'
    elif tamper == 'neural':
        events[2]['predictions_sha256'] = 'modified'
    elif tamper == 'isolation':
        events[1]['isolation']['seccomp'] = False
    elif tamper == 'model':
        events[1]['provenance']['bundle_sha256'] = 'modified'
    elif tamper == 'memory':
        events[-1]['resources']['peak'] = probe.HEADROOM_BYTES
    elif tamper == 'retry_binding':
        events[3]['package_id'] = 'other-attempt'
    elif tamper == 'cleanup':
        events[-1]['child_exit'] = 137
    elif tamper == 'forged_performance':
        events[-1]['session_seconds'] = 451
    elif tamper == 'timing':
        events[2]['elapsed_seconds'] = float('inf')
    elif tamper == 'negative_time':
        events[-1]['cleanup_seconds'] = -1
    else:
        # A changed source-time interpretation changes the retained full graph hash.
        events[2]['result_sha256'] = 'invented-observation-hour'
    with pytest.raises(ValueError):
        controller.verify_events(events, frozen, expected, rows)


@requires_retained_artifacts
def test_oracles_and_credentials_are_not_added_to_prepared_context(tmp_path, monkeypatch):
    monkeypatch.setattr(controller, 'ROOT', tmp_path)
    (tmp_path / 'data').mkdir()
    for name in controller.SOURCES:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# fixture source\n', encoding='utf-8')
    output = tmp_path / 'data/ner-cloud-check-fixture'
    result = controller.prepare(output)
    assert result['status'] == 'prepared_no_inference'
    members = controller.file_map(output / 'context')
    assert 'input/check.json' in members and 'input/workload.json' in members
    assert not any('expected' in name or '.env' in name or 'alembic' in name or '/tests/' in name for name in members)
    assert (output / 'expected.json').exists()
    controller.check_freeze(output, result['freeze_sha256'])
    (output / 'context/input/unselected.json').write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError, match='context_changed'):
        controller.check_freeze(output, result['freeze_sha256'])


def test_cloud_plan_never_deploys_and_requires_matching_local_verification(tmp_path, monkeypatch):
    frozen = {'package_id': 'a' * 64}
    monkeypatch.setattr(controller, 'check_freeze', lambda *_args: frozen)
    with pytest.raises(FileNotFoundError):
        controller.cloud_plan(tmp_path, 'freeze')
    controller.write(tmp_path / 'local-verification.json', {'freeze_sha256': 'freeze', 'package_id': 'a' * 64,
                     'status': 'passed_local_cloud_check_package', 'image': 'sha256:' + 'b' * 64})
    plan = controller.cloud_plan(tmp_path, 'freeze')
    assert plan['approval_required'] and not plan['database_access'] and not plan['scheduled']
    assert plan['runtime_project_roles'] == plan['secrets'] == []
    assert plan['limits'] == {'cpu': 1, 'memory_bytes': 3 * 1024**3, 'headroom_bytes': 2688 * 1024**2,
                              'task_count': 1, 'parallelism': 1, 'timeout_seconds': 600, 'max_retries': 0}
    assert not plan['cloud_changes_performed']


def test_existing_local_claim_is_never_overwritten_or_retried(tmp_path, monkeypatch):
    (tmp_path / 'data').mkdir()
    monkeypatch.setattr(controller, 'ROOT', tmp_path)
    monkeypatch.setattr(controller, 'check_freeze', lambda *_args: {'package_id': 'package'})
    monkeypatch.setattr(controller, 'inspect_image', lambda *_args: {'Id': 'image'})
    controller.write(tmp_path / 'build-ready.json', {'image': 'image', 'freeze_sha256': 'freeze', 'package_id': 'package'})
    claim = tmp_path / 'data' / controller.CLAIM_NAME
    claim.write_text('preserved failure', encoding='utf-8')
    with pytest.raises(FileExistsError):
        controller.execute_local(tmp_path, 'freeze', 'docker')
    assert claim.read_text(encoding='utf-8') == 'preserved failure'


def test_session_is_reaped_when_request_fails(monkeypatch):
    class FakeSession:
        instance = None

        def __init__(self, *_args):
            FakeSession.instance = self
            self.closed = False

        async def start(self):
            return {'provenance': {}, 'isolation': {}}

        async def request(self, *_args, **_kwargs):
            raise RuntimeError('fixture failure')

        async def close(self):
            self.closed = True

    monkeypatch.setattr(probe, 'Session', FakeSession)
    monkeypatch.setattr(probe, 'resources', lambda **_kwargs: {'peak': 1024})
    monkeypatch.setattr(probe, 'emit', lambda *_args, **_kwargs: None)
    row = {'record_id': 'fixture', 'kind': 'article', 'text': 'fixture', 'text_sha256': 'sha', 'publication': None}
    with pytest.raises(RuntimeError, match='fixture failure'):
        asyncio.run(probe.qualify({'package_id': 'package'}, {'bundle_sha256': 'bundle', 'code': {}}, [row]))
    assert FakeSession.instance.closed


@pytest.fixture
def legacy_cgroup(tmp_path):
    files = {'cpu/cpu.cfs_quota_us': '100000', 'cpu/cpu.cfs_period_us': '100000',
             'memory/memory.limit_in_bytes': str(probe.MEMORY_BYTES),
             'memory/memory.max_usage_in_bytes': '12345',
             'memory/memory.memsw.limit_in_bytes': str(probe.MEMORY_BYTES)}
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    return tmp_path


def test_reproduce_missing_file_on_legacy_resource_layout_without_inference(legacy_cgroup):
    readings = probe.resources(legacy_cgroup)
    assert readings['layout'] == 'v1' and readings['cpu_quota'] == readings['cpu_period']
    assert readings['memory_max'] == probe.MEMORY_BYTES and readings['swap_max'] == 0
    inventory = probe.resource_inventory(legacy_cgroup)
    assert inventory['v2_cpu'] == {'status': 'missing'}
    assert inventory['v1_cpu_quota'] == {'status': 'readable', 'values': [100000]}
    assert inventory['v1_memory_limit']['values'] == [3 * 1024**3]
    # Compatible layout retains exact limits; unavailable optional inventory remains explicit.
    assert inventory['v1_memory_and_swap_peak'] == {'status': 'missing'}


def test_diagnostic_does_not_hide_invalid_existing_resource_limits(cgroup):
    (cgroup / 'cpu.max').write_text('200000 100000', encoding='utf-8')
    assert probe.resource_inventory(cgroup)['v2_cpu']['values'] == [200000, 100000]
    with pytest.raises(ValueError, match='cpu_limit_required'):
        probe.resources(cgroup)


def test_resource_inventory_does_not_echo_malformed_or_secret_file_contents(cgroup):
    (cgroup / 'memory.max').write_text('private-secret-not-resource-data', encoding='utf-8')
    report = probe.resource_inventory(cgroup)
    assert report['v2_memory_limit']['status'] == 'unavailable'
    assert 'private-secret' not in json.dumps(report)


def test_startup_failure_reports_only_fixed_aliases_not_private_paths():
    error = FileNotFoundError(2, 'private source text', '/private/credentials.env')
    failure = probe.StartupFailure('resource_check', error)
    assert failure.stage == 'resource_check' and failure.error_type == 'FileNotFoundError'
    assert failure.resource_key is None and failure.startup_file is None
    assert 'private' not in str(failure)
    known = probe.StartupFailure('input_and_asset_validation', FileNotFoundError(2, 'missing', '/input/check.json'))
    assert known.startup_file == 'check_configuration'


def test_mount_inventory_excludes_other_mounts_and_source_names(tmp_path):
    path = tmp_path / 'mountinfo'
    path.write_text('1 0 0:1 / /private/secret rw - ext4 /private/disk rw\n'
                    '2 0 0:2 / /sys/fs/cgroup/memory ro - cgroup cgroup rw,memory\n'
                    '3 0 0:3 / /sys/fs/cgroup ro - cgroup2 cgroup rw\n', encoding='utf-8')
    report = probe.cgroup_mounts(path)
    assert report == [{'type': 'cgroup', 'mount_point': '/sys/fs/cgroup/memory', 'controllers': ['memory']},
                      {'type': 'cgroup2', 'mount_point': '/sys/fs/cgroup', 'controllers': []}]
    assert 'private' not in json.dumps(report)


def test_diagnostics_collect_missing_resources_without_model_or_claiming_acceptance(legacy_cgroup, monkeypatch):
    captured = []
    def prohibit_model(*_args, **_kwargs):
        raise AssertionError('A diagnostic must not start a model session')
    async def isolated_child():
        return {'status': 'failed', 'error_code': 'parent_guard_failed', 'pid': 2, 'parent_pid': 1}
    monkeypatch.setattr(probe, 'Session', prohibit_model)
    monkeypatch.setattr(probe, 'isolation_diagnostic', isolated_child)
    monkeypatch.setattr(probe, 'cgroup_mounts', lambda: [])
    monkeypatch.setattr(probe, 'emit', lambda event, package_id, **values:
                        captured.append({'schema': probe.SCHEMA, 'event': event, 'package_id': package_id, **values}))
    asyncio.run(probe.diagnose({'package_id': 'package'}, legacy_cgroup))
    event = controller.verify_diagnostics(captured, 'package')
    assert event['resource_check']['passed'] is True
    assert event['resource_readings']['values']['layout'] == 'v1'
    assert event['isolation_probe']['error_code'] == 'parent_guard_failed'
    assert event['inference_started'] is False and event['qualification_passed'] is False
    with pytest.raises(ValueError, match='incomplete_execution'):
        controller.verify_events(captured, {'package_id': 'package'}, [], [])


def test_missing_resource_is_reported_after_profile_input_authentication(monkeypatch):
    monkeypatch.setattr(probe, 'guard_environment', lambda _env: None)
    monkeypatch.setattr(probe.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(probe.platform, 'machine', lambda: 'x86_64')
    monkeypatch.setattr(probe.sys, 'version_info', (3, 12))
    monkeypatch.setattr(probe.importlib.metadata, 'version', lambda _: '3.7.5')
    def missing(**_kwargs):
        error = FileNotFoundError(2, 'missing', '/sys/fs/cgroup/cpu.max')
        error.resource_key = 'v2_cpu'
        raise error
    monkeypatch.setattr(probe, 'resources', missing)
    monkeypatch.setattr(probe, 'load_inputs', lambda: ({'resource_profile': probe.STRICT_PROFILE}, {}, []))
    with pytest.raises(probe.StartupFailure) as caught:
        asyncio.run(probe.run(False))
    assert caught.value.stage == 'resource_check' and caught.value.resource_key == 'v2_cpu'
    assert caught.value.error_type == 'FileNotFoundError'


def test_diagnostic_plan_requires_matching_non_inference_local_receipt(tmp_path, monkeypatch):
    monkeypatch.setattr(controller, 'check_freeze', lambda *_args: {'package_id': 'a' * 64, 'identity': {'resource_profile': probe.STRICT_PROFILE}})
    with pytest.raises(FileNotFoundError):
        controller.diagnostic_plan(tmp_path, 'freeze')
    controller.write(tmp_path / 'local-diagnostics.json', {'status': 'passed_local_diagnostic_collection',
                     'freeze_sha256': 'freeze', 'package_id': 'a' * 64, 'image': 'image', 'supervision_verified': True})
    plan = controller.diagnostic_plan(tmp_path, 'freeze')
    assert plan['args'] == ['--diagnostic-only'] and plan['approval_required']
    assert plan['execution_requires_separate_approval'] and plan['scope'] == 'diagnostic_only_no_model_session'
    assert not plan['qualification_passed'] and not plan['cloud_changes_performed']


@pytest.mark.parametrize('quota', ['80600', '-1', '0', '200000'])
def test_cloud_layout_does_not_convert_different_cpu_quota_into_one_cpu(legacy_cgroup, quota):
    (legacy_cgroup / 'cpu/cpu.cfs_quota_us').write_text(quota, encoding='utf-8')
    measured = probe.resource_readings(legacy_cgroup)
    assert measured['cpu_quota'] == int(quota)
    with pytest.raises(ValueError, match='cpu_limit_required'):
        probe.resources(legacy_cgroup)


def test_combined_cpu_mount_and_unbounded_swap_are_truthful(legacy_cgroup):
    (legacy_cgroup / 'cpu').rename(legacy_cgroup / 'cpu,cpuacct')
    (legacy_cgroup / 'memory/memory.memsw.limit_in_bytes').write_text(str(2**63 - 4096), encoding='utf-8')
    value = probe.resource_readings(legacy_cgroup)
    assert value['layout'] == 'v1' and value['swap_max'] is None
    assert value['memory_and_swap_limit_decimal'] == str(2**63 - 4096)
    assert probe.resource_inventory(legacy_cgroup)['v1_memory_and_swap_limit']['values'] == [str(2**63 - 4096)]
    with pytest.raises(ValueError, match='memory_limit_required'):
        probe.resources(legacy_cgroup)


def test_invalid_present_v2_data_cannot_fall_back_to_valid_v1(legacy_cgroup):
    (legacy_cgroup / 'cpu.max').write_text('not-resource-data', encoding='utf-8')
    with pytest.raises(ValueError, match='cpu_limit_required'):
        probe.resources(legacy_cgroup)


@pytest.mark.parametrize('memsw', [str(probe.MEMORY_BYTES - 1), str(probe.MEMORY_BYTES + 1024)])
def test_v1_invalid_combined_limit_or_swap_allowance_is_rejected(legacy_cgroup, memsw):
    (legacy_cgroup / 'memory/memory.memsw.limit_in_bytes').write_text(memsw, encoding='utf-8')
    with pytest.raises(ValueError):
        probe.resources(legacy_cgroup)


def test_host_swap_evidence_does_not_claim_a_container_limit(tmp_path):
    (tmp_path / 'swaps').write_text('Filename Type Size Used Priority\n', encoding='ascii')
    (tmp_path / 'meminfo').write_text('MemTotal: 1234 kB\nSwapTotal: 0 kB\nSwapFree: 0 kB\n', encoding='ascii')
    evidence = probe.swap_inventory(tmp_path)
    assert evidence['host_reports_no_swap'] is True
    assert evidence['establishes_container_swap_limit'] is False
    (tmp_path / 'swaps').write_text('Filename Type Size Used Priority\n/private/swap file 1024 0 -2\n', encoding='ascii')
    evidence = probe.swap_inventory(tmp_path)
    assert evidence['host_reports_no_swap'] is False and evidence['active_devices'] == 1
    assert 'private' not in json.dumps(evidence)


@pytest.mark.parametrize('case', ['missing', 'malformed', 'oversized', 'duplicate'])
def test_incomplete_or_invalid_swap_evidence_is_not_a_pass(tmp_path, case):
    if case != 'missing':
        (tmp_path / 'swaps').write_text('Filename Type Size Used Priority\n', encoding='ascii')
        info = 'SwapTotal: 0 kB\nSwapFree: 0 kB\n'
        if case == 'malformed':
            info = 'SwapTotal: private-secret\n'
        elif case == 'oversized':
            info = 'x' * 65537
        else:
            info += 'SwapTotal: 0 kB\n'
        (tmp_path / 'meminfo').write_text(info, encoding='ascii')
    value = probe.swap_inventory(tmp_path)
    assert value['status'] == 'unavailable' and value['establishes_container_swap_limit'] is False
    assert 'private' not in json.dumps(value)


def test_new_diagnostic_verifier_rejects_forged_resource_success(legacy_cgroup, monkeypatch):
    captured = []
    async def isolated():
        return {'status': 'failed', 'error_code': 'parent_guard_failed', 'pid': 2, 'parent_pid': 1}
    monkeypatch.setattr(probe, 'isolation_diagnostic', isolated)
    monkeypatch.setattr(probe, 'cgroup_mounts', lambda: [])
    monkeypatch.setattr(probe, 'emit', lambda event, package_id, **values:
                        captured.append({'schema': probe.SCHEMA, 'event': event, 'package_id': package_id, **values}))
    asyncio.run(probe.diagnose({'package_id': 'package'}, legacy_cgroup))
    captured[0]['resource_readings']['values']['cpu_quota'] = 80600
    with pytest.raises(ValueError, match='diagnostic_resource_claim'):
        controller.verify_diagnostics(captured, 'package')


@pytest.mark.parametrize('code', [0, 7, -15])
def test_launcher_preserves_child_success_failure_and_signal_status(monkeypatch, code):
    class Lib:
        def prctl(self, *_args):
            return 0
    class Child:
        pid = 41
        returncode = None
    monkeypatch.setattr(launcher.sys, 'platform', 'linux')
    monkeypatch.setattr(launcher.ctypes, 'CDLL', lambda *_args, **_kwargs: Lib())
    monkeypatch.setattr(launcher.subprocess, 'Popen', lambda *_args, **_kwargs: Child())
    statuses = iter([(41, code), (0, 0)])
    monkeypatch.setattr(launcher.os, 'waitpid', lambda *_args: next(statuses), raising=False)
    monkeypatch.setattr(launcher.os, 'WNOHANG', 1, raising=False)
    monkeypatch.setattr(launcher.os, 'waitstatus_to_exitcode', lambda value: value, raising=False)
    monkeypatch.setattr(launcher.signal, 'signal', lambda *_args: None)
    monkeypatch.setattr(launcher, 'child_pids', lambda: [])
    assert launcher.supervise(['fixed-fixture']) == (code if code >= 0 else 128 - code)


def test_launcher_rejects_arbitrary_commands_before_spawning(monkeypatch):
    monkeypatch.setattr(launcher.sys, 'argv', ['entrypoint', '--execute', 'arbitrary-command'])
    monkeypatch.setattr(launcher, 'supervise', lambda *_args: pytest.fail('No arbitrary command may run'))
    assert launcher.main() == 2


def test_launcher_uses_fixed_probe_and_isolated_python_flags(monkeypatch):
    captured = []
    monkeypatch.setattr(launcher.sys, 'argv', ['entrypoint', '--diagnostic-only'])
    monkeypatch.setattr(launcher, 'supervise', lambda args: captured.append(args) or 0)
    assert launcher.main() == 0
    assert captured == [[sys.executable, '-I', '-B', '/app/scripts/news_ner_cloud_probe.py', '--diagnostic-only']]



def test_diagnostic_binds_one_resource_snapshot_when_peak_can_change(cgroup, monkeypatch):
    captured, calls = [], []
    original = probe.resource_readings
    def changing(root):
        calls.append(root)
        value = original(root)
        value['peak'] += len(calls)
        return value
    async def isolated():
        return {'status': 'passed', 'pid': 3, 'parent_pid': 2}
    monkeypatch.setattr(probe, 'resource_readings', changing)
    monkeypatch.setattr(probe, 'isolation_diagnostic', isolated)
    monkeypatch.setattr(probe, 'cgroup_mounts', lambda: [])
    monkeypatch.setattr(probe, 'emit', lambda event, package_id, **values:
                        captured.append({'schema': probe.SCHEMA, 'event': event, 'package_id': package_id, **values}))
    asyncio.run(probe.diagnose({'package_id': 'package'}, cgroup))
    assert len(calls) == 1
    assert controller.verify_diagnostics(captured, 'package')['resource_check']['passed']


@pytest.fixture
def no_host_swap(tmp_path):
    folder = tmp_path / 'proc'
    folder.mkdir()
    (folder / 'swaps').write_text('Filename Type Size Used Priority\n', encoding='ascii')
    (folder / 'meminfo').write_text('SwapTotal: 0 kB\nSwapFree: 0 kB\n', encoding='ascii')
    return folder


@pytest.mark.parametrize('quota', [80600, 104300])
def test_cloud_profile_records_actual_quota_and_labels_host_swap_basis(legacy_cgroup, no_host_swap, quota):
    (legacy_cgroup / 'cpu/cpu.cfs_quota_us').write_text(str(quota), encoding='ascii')
    (legacy_cgroup / 'memory/memory.memsw.limit_in_bytes').write_text(str(2**63 - 4096), encoding='ascii')
    value = probe.resources(legacy_cgroup, profile=probe.CLOUD_PROFILE, proc=no_host_swap)
    assert value['cpu_quota'] == quota and value['swap_max'] is None
    assert value['swap_evidence']['basis'] == 'host_no_swap'
    assert value['swap_evidence']['host']['establishes_container_swap_limit'] is False
    controller.verify_resource_snapshot(value, probe.CLOUD_PROFILE)
    with pytest.raises(ValueError):
        probe.resources(legacy_cgroup)
    with pytest.raises(ValueError):
        controller.verify_resource_snapshot(value, probe.STRICT_PROFILE)


@pytest.mark.parametrize('quota', ['-1', '0'])
def test_cloud_profile_never_accepts_unbounded_or_zero_cpu(legacy_cgroup, no_host_swap, quota):
    (legacy_cgroup / 'cpu/cpu.cfs_quota_us').write_text(quota, encoding='ascii')
    with pytest.raises(ValueError, match='cpu_limit_required'):
        probe.resources(legacy_cgroup, profile=probe.CLOUD_PROFILE, proc=no_host_swap)


@pytest.mark.parametrize('change', ['missing', 'capacity', 'device', 'malformed'])
def test_cloud_profile_rejects_missing_or_nonzero_host_swap(legacy_cgroup, no_host_swap, change):
    (legacy_cgroup / 'memory/memory.memsw.limit_in_bytes').write_text(str(2**63 - 4096), encoding='ascii')
    if change == 'missing':
        (no_host_swap / 'swaps').unlink()
    elif change == 'capacity':
        (no_host_swap / 'meminfo').write_text('SwapTotal: 1024 kB\nSwapFree: 1024 kB\n', encoding='ascii')
    elif change == 'device':
        (no_host_swap / 'swaps').write_text('Filename Type Size Used Priority\n/private/swap file 1 0 -2\n', encoding='ascii')
    else:
        (no_host_swap / 'swaps').write_text('private-untrusted-text', encoding='ascii')
    with pytest.raises(ValueError, match='swap_evidence_required'):
        probe.resources(legacy_cgroup, profile=probe.CLOUD_PROFILE, proc=no_host_swap)


def test_cloud_profile_accepts_enforced_zero_even_with_host_swap(cgroup, no_host_swap):
    (no_host_swap / 'swaps').unlink()
    value = probe.resources(cgroup, profile=probe.CLOUD_PROFILE, proc=no_host_swap)
    assert value['swap_evidence']['basis'] == 'enforced_zero_limit'
    assert value['swap_evidence']['host']['status'] == 'unavailable'
    controller.verify_resource_snapshot(value, probe.CLOUD_PROFILE)


@pytest.fixture
def cloud_snapshot():
    return {'profile': probe.CLOUD_PROFILE, 'layout': 'v1', 'cpu_quota': 104300, 'cpu_period': 100000,
            'memory_max': probe.MEMORY_BYTES, 'swap_max': None, 'peak': 1024,
            'swap_evidence': {'basis': 'host_no_swap', 'host': {'status': 'readable', 'active_devices': 0,
                'total_bytes': 0, 'free_bytes': 0, 'host_reports_no_swap': True,
                'establishes_container_swap_limit': False}}}


@pytest.mark.parametrize('tamper', ['quota', 'period', 'boolean', 'memory', 'swap_missing',
                                  'swap_device', 'swap_total', 'swap_claim', 'wrong_basis', 'wrong_profile'])
def test_independent_cloud_resource_verifier_rejects_false_claims(cloud_snapshot, tamper):
    if tamper == 'quota':
        cloud_snapshot['cpu_quota'] = -1
    elif tamper == 'period':
        cloud_snapshot['cpu_period'] = 0
    elif tamper == 'boolean':
        cloud_snapshot['cpu_quota'] = True
    elif tamper == 'memory':
        cloud_snapshot['memory_max'] = 4 * 1024**3
    elif tamper == 'swap_missing':
        cloud_snapshot.pop('swap_evidence')
    elif tamper == 'swap_device':
        cloud_snapshot['swap_evidence']['host']['active_devices'] = 1
    elif tamper == 'swap_total':
        cloud_snapshot['swap_evidence']['host']['total_bytes'] = 1
    elif tamper == 'swap_claim':
        cloud_snapshot['swap_evidence']['host']['establishes_container_swap_limit'] = True
    elif tamper == 'wrong_basis':
        cloud_snapshot['swap_evidence']['basis'] = 'enforced_zero_limit'
    else:
        cloud_snapshot['profile'] = probe.STRICT_PROFILE
    with pytest.raises(ValueError):
        controller.verify_resource_snapshot(cloud_snapshot, probe.CLOUD_PROFILE)


@pytest.fixture
def cloud_execution(execution, cloud_snapshot):
    events, frozen, expected, rows = execution
    frozen['identity']['resource_profile'] = probe.CLOUD_PROFILE
    for event in events:
        event['resources'] = deepcopy(cloud_snapshot)
    events[0]['resource_profile'] = events[1]['resource_profile'] = probe.CLOUD_PROFILE
    return events, frozen, expected, rows


def test_cloud_results_keep_original_oracles_and_check_every_resource_snapshot(cloud_execution):
    value = controller.verify_events(*cloud_execution)
    assert value['records'] == 355 and value['retained_prediction_records'] == 352
    assert value['reviewed_article_mentions'] == 53 and all(value['checks'].values())
    assert value['resource_profile'] == probe.CLOUD_PROFILE and value['resource_snapshots'] == 358
    assert value['measured_cpu_fraction_min'] == value['measured_cpu_fraction_max'] == 1.043
    assert value['separate_cloud_configuration_verification_required'] is True


@pytest.mark.parametrize('index', [0, 1, 2, 100, -1])
def test_cloud_resource_regression_at_any_stage_invalidates_qualification(cloud_execution, index):
    events, frozen, expected, rows = cloud_execution
    events[index]['resources']['swap_evidence']['host']['active_devices'] = 1
    with pytest.raises(ValueError, match='swap_evidence_required'):
        controller.verify_events(events, frozen, expected, rows)


@pytest.fixture
def cloud_control_plane():
    index = f'{controller.REGION}-docker.pkg.dev/{controller.PROJECT}/lanes/{controller.JOB}@sha256:' + 'a' * 64
    platform = index[:-64] + 'b' * 64
    task = {'containers': [{'image': index, 'resources': {'limits': {'cpu': '1', 'memory': '3Gi'}},
                           'env': [{'name': 'LANES_NER_CHECK_PROFILE', 'value': 'isolated'}]}],
            'maxRetries': 0, 'timeoutSeconds': '600', 'serviceAccountName': controller.SERVICE_ACCOUNT}
    metadata = {'name': controller.JOB, 'namespace': '557679867071',
                'labels': {'cloud.googleapis.com/location': controller.REGION}}
    spec = {'taskCount': 1, 'parallelism': 1, 'template': {'spec': task}}
    job = {'metadata': deepcopy(metadata), 'spec': {'template': {'spec': deepcopy(spec)}}}
    execution = {'metadata': deepcopy(metadata), 'spec': deepcopy(spec),
                 'status': {'succeededCount': 1, 'completionTime': '2026-10-22T00:00:00Z'}}
    execution['metadata']['name'] += '-fixture'
    execution['metadata']['labels']['run.googleapis.com/job'] = controller.JOB
    execution['spec']['template']['spec']['containers'][0]['image'] = platform
    return job, execution, index, platform


def test_cloud_configured_cpu_is_verified_separately_from_measured_quota(cloud_control_plane):
    job, execution, index, platform = cloud_control_plane
    value = controller.verify_cloud_configuration(job, execution, image_index=index, platform_image=platform)
    assert value['configured_cpu'] == 1 and value['configured_memory_bytes'] == probe.MEMORY_BYTES
    assert not value['database_credentials']


@pytest.mark.parametrize('tamper', ['cpu', 'memory', 'retry', 'timeout', 'tasks', 'account', 'environment',
                                  'mount', 'image', 'diagnostic_args', 'command', 'cloudsql', 'namespace',
                                  'region', 'failed', 'retried'])
def test_cloud_control_plane_tampering_cannot_be_overridden_by_matching_predictions(cloud_control_plane, tamper):
    job, execution, index, platform = cloud_control_plane
    task = execution['spec']['template']['spec']
    container = task['containers'][0]
    if tamper == 'cpu': container['resources']['limits']['cpu'] = '2'
    elif tamper == 'memory': container['resources']['limits']['memory'] = '4Gi'
    elif tamper == 'retry': task['maxRetries'] = 1
    elif tamper == 'timeout': task['timeoutSeconds'] = '1200'
    elif tamper == 'tasks': execution['spec']['taskCount'] = 2
    elif tamper == 'account': task['serviceAccountName'] = 'different-account'
    elif tamper == 'environment': container['env'].append({'name': 'DATABASE_URL', 'value': 'fictional'})
    elif tamper == 'mount': task['volumes'] = [{'name': 'unexpected'}]
    elif tamper == 'image': container['image'] = index
    elif tamper == 'diagnostic_args': container['args'] = ['--diagnostic-only']
    elif tamper == 'command': container['command'] = ['unexpected']
    elif tamper == 'cloudsql': execution['metadata']['annotations'] = {'run.googleapis.com/cloudsql-instances': 'fictional'}
    elif tamper == 'namespace': execution['metadata']['namespace'] = 'different-project'
    elif tamper == 'region': execution['metadata']['labels']['cloud.googleapis.com/location'] = 'different-region'
    elif tamper == 'failed': execution['status']['failedCount'] = 1
    else: execution['status']['retriedCount'] = 1
    with pytest.raises(ValueError):
        controller.verify_cloud_configuration(job, execution, image_index=index, platform_image=platform)


def test_cloud_profile_cannot_be_used_to_bypass_local_inference_claim(monkeypatch, tmp_path):
    monkeypatch.setattr(controller, 'check_freeze', lambda *_args: {'identity': {'resource_profile': probe.CLOUD_PROFILE}})
    with pytest.raises(ValueError, match='local_strict_profile_required'):
        controller.execute_local(tmp_path, 'freeze', 'docker')


def test_cloud_qualification_proposal_is_not_execution_authorization(monkeypatch, tmp_path):
    frozen = {'package_id': 'a' * 64, 'identity': {'resource_profile': probe.CLOUD_PROFILE}}
    monkeypatch.setattr(controller, 'check_freeze', lambda *_args: frozen)
    controller.write(tmp_path / 'local-diagnostics.json', {'status': 'passed_local_diagnostic_collection',
        'freeze_sha256': 'freeze', 'package_id': 'a' * 64, 'image': 'image', 'supervision_verified': True,
        'diagnostics': {'resource_check': {'passed': True}}})
    plan = controller.cloud_qualification_plan(tmp_path, 'freeze')
    assert plan['args'] == [] and plan['resource_profile'] == probe.CLOUD_PROFILE
    assert plan['execution_requires_separate_approval'] and not plan['inference_authorized']
    assert not plan['cloud_changes_performed']



def test_cloud_live_resource_failure_closes_session_before_more_requests(monkeypatch, cloud_snapshot):
    class FakeSession:
        instance = None
        def __init__(self, *_args):
            FakeSession.instance = self
            self.closed = False
            self.requests = 0
        async def start(self):
            return {'provenance': {}, 'isolation': {}}
        async def request(self, *_args, **_kwargs):
            self.requests += 1
            return {'proposal': {'neural_mentions': []}, 'graph': {}, 'provenance': {}}
        async def close(self):
            self.closed = True
    calls = []
    def resource_check(**kwargs):
        assert kwargs['profile'] == probe.CLOUD_PROFILE
        calls.append(1)
        if len(calls) > 1:
            raise ValueError('swap_evidence_required')
        return deepcopy(cloud_snapshot)
    monkeypatch.setattr(probe, 'Session', FakeSession)
    monkeypatch.setattr(probe, 'resources', resource_check)
    monkeypatch.setattr(probe, 'emit', lambda *_args, **_kwargs: None)
    row = {'record_id': 'fixture', 'kind': 'article', 'text': 'fixture', 'text_sha256': 'sha', 'publication': None}
    with pytest.raises(ValueError, match='swap_evidence_required'):
        asyncio.run(probe.qualify({'package_id': 'package', 'resource_profile': probe.CLOUD_PROFILE},
                                  {'bundle_sha256': 'bundle', 'code': {}}, [row, row]))
    assert FakeSession.instance.closed and FakeSession.instance.requests == 1 and len(calls) == 2


@requires_retained_artifacts
def test_cloud_profile_is_frozen_in_image_inputs_and_cannot_switch_after_prepare(tmp_path, monkeypatch):
    monkeypatch.setattr(controller, 'ROOT', tmp_path)
    (tmp_path / 'data').mkdir()
    for name in controller.SOURCES:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# fixture source\n', encoding='utf-8')
    output = tmp_path / 'data/ner-cloud-check-cloud-fixture'
    ready = controller.prepare(output, probe.CLOUD_PROFILE)
    frozen = controller.check_freeze(output, ready['freeze_sha256'])
    assert frozen['identity']['resource_profile'] == probe.CLOUD_PROFILE
    path = output / 'context/input/check.json'
    check = controller.read(path)
    assert check['resource_profile'] == probe.CLOUD_PROFILE
    check['resource_profile'] = probe.STRICT_PROFILE
    path.write_text(json.dumps(check), encoding='utf-8')
    with pytest.raises(ValueError, match='context_changed'):
        controller.check_freeze(output, ready['freeze_sha256'])


def test_saved_job_configuration_also_must_match_one_cpu(cloud_control_plane):
    job, execution, index, platform = cloud_control_plane
    job['spec']['template']['spec']['template']['spec']['containers'][0]['resources']['limits']['cpu'] = '2'
    with pytest.raises(ValueError, match='cloud_configured_resources'):
        controller.verify_cloud_configuration(job, execution, image_index=index, platform_image=platform)
