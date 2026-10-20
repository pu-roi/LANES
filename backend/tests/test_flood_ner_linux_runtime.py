"""Constructed workloads and mocked Docker processes; no real model or corpus."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner import linux_runtime_qualification as q
from training.flood_ner import linux_runtime_worker as w


@pytest.fixture
def training():
    raw, meta = [], []
    for i in range(345):
        rid = f'train-{i:020x}'; text = f'Fictional Piña Road case {i}.'
        raw.append({'record_id': rid, 'text': text, 'prediction': [[10, 19, 'ROAD']]})
        meta.append({'record_id': rid, 'partition': 'train', 'text_sha256': q.text_hash(text),
                     'language': 'english' if i < 170 else 'taglish'})
    return raw, meta


def article(i, length, languages=None, supported=True):
    text = (f'Fictional article {i}. ' * 100)[:length]
    return {'article_id': f'article-{i:020x}', 'text': text, 'source_sha256': q.text_hash(text),
            'languages': languages or ['english', 'taglish'], 'complete_capture': True, 'partition': 'train',
            'full_extent_use_review': {'supported': supported, 'evidence_sha256': 'a' * 64,
                'source_sha256': q.text_hash(text), 'start': 0, 'end': len(text), 'purpose': 'private_runtime_qualification'}}


def workload(training):
    rows, expected = q.project_training(*training)
    articles, coverage = q.select_articles([article(i, 80 + 20 * i) for i in range(3)])
    return rows + articles + q.stress_rows(), expected


def test_raw_projection_separates_references_predictions_and_language(training):
    rows, expected = q.project_training(*training)
    assert len(rows) == len(expected) == 345
    assert all(set(r) == {'record_id', 'text', 'text_sha256', 'kind'} for r in rows)
    q.validate_workload(workload(training)[0])


@pytest.mark.parametrize('change', ['duplicate', 'missing', 'text', 'partition', 'language', 'annotation', 'bad_span', 'nonopaque'])
def test_training_identity_scope_and_reference_rejection(training, change):
    raw, meta = deepcopy(training)
    if change == 'duplicate': raw[-1] = raw[0]
    if change == 'missing': raw.pop()
    if change == 'text': raw[0]['text'] += 'changed'
    if change == 'partition': meta[0]['partition'] = 'dev'
    if change == 'language': meta[0]['language'] = 'taglish'
    if change == 'annotation': raw[0]['reference'] = []
    if change == 'bad_span': raw[0]['prediction'] = [[0, 1000, 'ROAD']]
    if change == 'nonopaque': raw[0]['record_id'] = 'a-title'
    with pytest.raises(ValueError): q.project_training(raw, meta)


@pytest.mark.parametrize('change', ['reference', 'prediction', 'language', 'empty', 'oversized', 'hash', 'duplicate', 'missing_article', 'stress'])
def test_worker_workload_rejection(training, change):
    rows, _ = workload(training)
    if change in ('reference', 'prediction', 'language'): rows[0][change] = []
    if change == 'empty': rows[0]['text'] = ''
    if change == 'oversized': rows[0]['text'] = 'a' * 100001
    if change == 'hash': rows[0]['text_sha256'] = '0' * 64
    if change == 'duplicate': rows[1] = rows[0]
    if change == 'missing_article': rows = [r for r in rows if r['kind'] != 'article']
    if change == 'stress': rows[-1]['text'] = 'changed'
    with pytest.raises(ValueError): q.validate_workload(rows)


def test_article_extremes_are_deterministic_and_deduplicated():
    candidates = [article(i, 100 + 10 * i) for i in range(7)]
    selected, coverage = q.select_articles(candidates[::-1])
    assert [r['record_id'] for r in selected] == [f'article-{i:020x}' for i in (0, 3, 6)]
    assert coverage['article_coverage_complete']
    assert len(selected) == 3  # Shared language associations do not duplicate sources.


def test_held_use_does_not_supply_article_coverage():
    selected, coverage = q.select_articles([article(i, 100 + i, supported=False) for i in range(3)])
    assert selected == [] and not coverage['article_coverage_complete']


@pytest.mark.parametrize('change', ['extent', 'purpose', 'source', 'duplicate', 'incomplete', 'dev'])
def test_article_use_and_origin_not_inherited(change):
    rows = [article(i, 100 + i) for i in range(3)]
    if change == 'extent': rows[0]['full_extent_use_review']['end'] -= 1
    if change == 'purpose': rows[0]['full_extent_use_review']['purpose'] = 'training_passage_only'
    if change == 'source': rows[0]['full_extent_use_review']['source_sha256'] = '0' * 64
    if change == 'duplicate': rows.append(rows[0])
    if change == 'incomplete': rows[0]['complete_capture'] = False
    if change == 'dev': rows[0]['partition'] = 'dev'
    with pytest.raises(ValueError): q.select_articles(rows)


def test_parity_is_exact_and_unicode_offsets_are_preserved(training):
    rows, expected = workload(training)
    predictions = [{'record_id': row['record_id'], 'text_sha256': row['text_sha256'],
                    'prediction': expected[row['record_id']]} for row in rows if row['kind'] == 'passage']
    assert q.strict_parity(rows, predictions, expected)['mismatch_count'] == 0
    predictions[0]['prediction'] = [[10, 19, 'LANDMARK']]
    result = q.strict_parity(rows, predictions, expected)
    assert result['mismatch_count'] == 1 and result['records_compared'] == 345


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'text', 'reference', 'wrong_id'])
def test_prediction_join_rejection(training, change):
    rows, expected = workload(training)
    guesses = [{'record_id': row['record_id'], 'text_sha256': row['text_sha256'],
                'prediction': expected[row['record_id']]} for row in rows if row['kind'] == 'passage']
    if change == 'missing': guesses.pop()
    if change == 'duplicate': guesses[-1] = guesses[0]
    if change == 'text': guesses[0]['text_sha256'] = '0' * 64
    if change == 'reference': guesses[0]['reference'] = []
    if change == 'wrong_id': guesses[0]['record_id'] = 'holdout-identity'
    with pytest.raises(ValueError): q.strict_parity(rows, guesses, expected)


def metrics():
    return {'passage_seconds': [1.0] * 345, 'article_seconds': [30.0] * 3,
            'stress_seconds': [60.0] * 3, 'peak_rss_bytes': 3 * 1024**3}


def test_limits_are_inclusive_and_nearest_rank_p95():
    assert q.performance(metrics(), 60)['passed']
    assert q.percentile95(list(range(1, 101))) == 95


@pytest.mark.parametrize('change', ['cold', 'passage', 'article', 'stress', 'rss', 'missing_rss', 'nan', 'count', 'missing_articles'])
def test_measurement_failures_cannot_raise_limits(change):
    m = metrics(); cold = 60
    if change == 'cold': cold = 60.01
    if change == 'passage': m['passage_seconds'] = [1.01] * 345
    if change == 'article': m['article_seconds'][0] = 30.01
    if change == 'stress': m['stress_seconds'][0] = 60.01
    if change == 'rss': m['peak_rss_bytes'] += 1
    if change == 'missing_rss': m['peak_rss_bytes'] = None
    if change == 'nan': m['passage_seconds'][0] = float('nan')
    if change == 'count': m['passage_seconds'].pop()
    if change == 'missing_articles': m['article_seconds'] = []
    if change in ('missing_rss', 'nan', 'count', 'missing_articles'):
        with pytest.raises(ValueError): q.performance(m, cold)
    else: assert not q.performance(m, cold)['passed']


def mounts(tmp_path):
    targets = ['/assets/MANIFEST.json', '/assets/models/control-seed-0/model', '/assets/resource.json',
               '/assets/base', '/input', '/output', *('/code/training/flood_ner/' + s for s in q.SOURCES)]
    result = {}
    for i, target in enumerate(targets):
        path = tmp_path / str(i); path.mkdir()
        result[target] = (path, target != '/output')
    return result


def inspect_value(m):
    return {'HostConfig': {'NetworkMode': 'none', 'Memory': 4 * 1024**3, 'MemorySwap': 4 * 1024**3,
            'NanoCpus': 2_000_000_000, 'ReadonlyRootfs': True, 'RestartPolicy': {'Name': 'no'},
            'PidsLimit': 128, 'CapDrop': ['ALL'], 'SecurityOpt': ['no-new-privileges']},
            'Mounts': [{'Destination': key, 'Type': 'bind', 'RW': not ro} for key, (_, ro) in m.items()],
            'Config': {'Env': ['PATH=/usr/bin', 'PYTHONDONTWRITEBYTECODE=1']}}


def test_container_command_is_fixed_and_predictions_are_not_mounted(tmp_path):
    m = mounts(tmp_path)
    args = q.container_args('docker', 'sha256:' + 'a' * 64, 'lanes-ner-qual-' + 'b' * 16, m, 'c' * 64)
    assert args[1] == 'create' and '--read-only' in args and '--restart=no' in args
    assert args[args.index('--network') + 1] == 'none'
    assert '--memory' in args and '--cpus' in args and '--gpus' not in args
    assert 'expected-predictions' not in ' '.join(args) and '--env-file' not in args
    q.verify_isolation(inspect_value(m), m)


@pytest.mark.parametrize('change', ['network', 'memory', 'cpu', 'rw', 'restart', 'credentials', 'extra_mount'])
def test_actual_container_inspection_required(tmp_path, change):
    m = mounts(tmp_path); value = inspect_value(m)
    if change == 'network': value['HostConfig']['NetworkMode'] = 'bridge'
    if change == 'memory': value['HostConfig']['Memory'] = 0
    if change == 'cpu': value['HostConfig']['NanoCpus'] = 0
    if change == 'rw': value['Mounts'][0]['RW'] = True
    if change == 'restart': value['HostConfig']['RestartPolicy']['Name'] = 'always'
    if change == 'credentials': value['Config']['Env'].append('DATABASE_URL=fictional')
    if change == 'extra_mount': value['Mounts'].append({'Destination': '/extra', 'Type': 'bind', 'RW': True})
    with pytest.raises(ValueError): q.verify_isolation(value, m)


def test_build_pins_base_without_editing_dockerfile(tmp_path):
    args = q.build_args('docker', tmp_path, 'python@sha256:' + 'a' * 64, tmp_path / 'new')
    assert 'python:3.12-slim=docker-image://python@sha256:' + 'a' * 64 in args
    assert str(tmp_path / 'Dockerfile') in args and '--push' not in args and '--load' in args
    with pytest.raises(ValueError): q.build_args('docker', tmp_path, 'python:latest', tmp_path)


def test_lock_concurrency_occupied_receipts_and_explicit_new_attempt(tmp_path):
    lock = tmp_path / 'active.lock'
    with q.exclusive(lock):
        with pytest.raises(FileExistsError):
            with q.exclusive(lock): pass
    assert not lock.exists()
    with pytest.raises(RuntimeError):
        with q.exclusive(lock): raise RuntimeError('interrupted')
    assert lock.exists()  # Never automatically refund an uncertain live owner.
    p = tmp_path / 'receipt.json'; q.write_new(p, {'original': True})
    with pytest.raises(FileExistsError): q.write_new(p, {})
    q.write_new(tmp_path / 'new-attempt.json', {})
    assert json.loads(p.read_text()) == {'original': True}


@pytest.mark.parametrize('failure', ['timeout', 'exit', 'missing'])
def test_command_preserves_partial_failure_without_retry(tmp_path, monkeypatch, failure):
    calls = []
    def run(*a, **k):
        calls.append((a, k))
        k['stdout'].write(b'partial'); k['stderr'].write(b'error')
        if failure == 'timeout': raise subprocess.TimeoutExpired(a[0], 1)
        if failure == 'missing': raise OSError('missing')
        return SimpleNamespace(returncode=2, stdout='partial', stderr='error')
    monkeypatch.setattr(q.subprocess, 'run', run)
    p = tmp_path / 'receipt.json'; result = q.command(['docker', 'probe'], p, 1)
    assert len(calls) == 1 and result['returncode'] != 0 and p.exists()
    if failure != 'missing': assert result['stdout'] == 'partial'
    with pytest.raises(ValueError): q.successful(result)


def test_command_reserves_before_dispatch_and_blocks_second_writer(tmp_path, monkeypatch):
    p = tmp_path / 'receipt.json'; calls = []
    def run(*args, **kwargs):
        calls.append(args)
        assert p.with_name('receipt-reservation.json').exists()
        with pytest.raises(FileExistsError): q.command(['second'], p)
        return SimpleNamespace(returncode=0, stdout='{}', stderr='')
    monkeypatch.setattr(q.subprocess, 'run', run)
    assert q.command(['first'], p)['returncode'] == 0
    assert len(calls) == 1


def test_interrupted_command_keeps_reservation_and_outcome(tmp_path, monkeypatch):
    def run(*a, **k): raise KeyboardInterrupt()
    monkeypatch.setattr(q.subprocess, 'run', run)
    p = tmp_path / 'receipt.json'
    with pytest.raises(KeyboardInterrupt): q.command(['owned'], p)
    assert p.with_name('receipt-reservation.json').exists()
    assert json.loads(p.read_text())['output_complete'] is False


def test_command_uses_exclusive_files_instead_of_inherited_pipes(tmp_path, monkeypatch):
    def run(*a, **k):
        assert 'capture_output' not in k and k['stdout'] != subprocess.PIPE and k['stderr'] != subprocess.PIPE
        k['stdout'].write('partial ñ'.encode())
        raise subprocess.TimeoutExpired(a[0], 1)
    monkeypatch.setattr(q.subprocess, 'run', run)
    p = tmp_path / 'receipt.json'; result = q.command(['owned'], p)
    assert result['stdout'] == 'partial ñ' and not result['output_complete']
    assert p.with_name('receipt-stdout.bin').read_bytes() == 'partial ñ'.encode()


def test_forged_failure_readiness_cannot_dispatch(tmp_path, monkeypatch):
    grant = {key: None for key in ('schema', 'policy', 'implementation', 'test_binding', 'view', 'articles',
                                  'model_manifest', 'resource_manifest', 'resource_dir', 'backend_bindings', 'failure_probe_evidence')}
    grant.update(schema='lanes-linux-runtime-grant-v1', policy=deepcopy(q.POLICY), failure_probe_evidence={'passed': True})
    path = tmp_path / 'grant.json'; q.write_new(path, grant)
    def forbidden(*a, **k): raise AssertionError('dispatch forbidden')
    monkeypatch.setattr(q, 'command', forbidden)
    with pytest.raises(ValueError, match='inherited readiness'): q.execute(tmp_path, 'docker', path, q.digest(path), tmp_path)


def test_unavailable_engine_cannot_claim_qualification(tmp_path, monkeypatch):
    monkeypatch.setattr(q, 'command', lambda *a, **k: {'returncode': 1, 'stdout': '{}'})
    status = q.engine_preflight('docker', tmp_path)
    assert status['status'] == 'blocked_engine'
    assert status['compatibility'] == status['performance'] == 'unmeasured'
    assert not status['gate_3_cleared'] and not status['linux_inference_run']


@pytest.mark.parametrize('state', [
    {'Running': False, 'ExitCode': 137, 'OOMKilled': True},
    {'Running': False, 'ExitCode': 2, 'OOMKilled': False},
    {'Running': True, 'ExitCode': 0, 'OOMKilled': False},
])
def test_monitor_stops_owned_container_on_crash_oom_or_timeout(tmp_path, monkeypatch, state):
    calls = []
    def command(args, *a, **k):
        calls.append(args)
        return {'returncode': 0, 'stdout': json.dumps(state)}
    monkeypatch.setattr(q, 'command', command)
    monkeypatch.setattr(q.time, 'monotonic', lambda: 61 if state['Running'] else 1)
    with pytest.raises(ValueError): q.monitor('docker', 'owned', tmp_path, tmp_path, 0)
    assert any(c[1:3] == ['kill', 'owned'] for c in calls)
    assert all('other-container' not in c for c in calls)


def test_monitor_cold_clock_includes_time_before_docker_start(tmp_path, monkeypatch):
    q.write_new(tmp_path / 'ready.json', {'cold_worker_seconds': 3})
    monkeypatch.setattr(q.time, 'monotonic', lambda: 15)
    monkeypatch.setattr(q, 'command', lambda *a, **k: {'returncode': 0, 'stdout': json.dumps({'Running': False, 'ExitCode': 0, 'OOMKilled': False})})
    _, cold = q.monitor('docker', 'owned', tmp_path, tmp_path, 10)
    assert cold == 5


def test_worker_rejects_host_runtime_before_importing_neural_libraries(tmp_path, monkeypatch):
    monkeypatch.setattr(w.platform, 'system', lambda: 'Windows')
    with pytest.raises(ValueError, match='Linux Python'): w.run({}, tmp_path, tmp_path)


def test_worker_rejects_wrong_python_before_asset_access(tmp_path, monkeypatch):
    monkeypatch.setattr(w.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(w.sys, 'version_info', (3, 11, 0))
    with pytest.raises(ValueError, match='Linux Python'): w.run({}, tmp_path, tmp_path)


def test_worker_request_valid_without_references(tmp_path):
    value = {'schema': 'lanes-linux-runtime-worker-v1', 'policy': deepcopy(q.POLICY),
             'model_manifest_sha256': 'a' * 64, 'resource_manifest_sha256': 'b' * 64,
             'workload_sha256': 'c' * 64, 'requirements_sha256': 'd' * 64,
             'implementation': {name: q.digest(Path(q.__file__).parent / name) for name in q.SOURCES}}
    p = tmp_path / 'request.json'; q.write_new(p, value)
    assert w.checked_request(p, q.digest(p)) == value


@pytest.mark.parametrize('change', ['hash', 'policy', 'reference', 'implementation'])
def test_worker_request_bindings_and_reference_separation(tmp_path, change):
    value = {'schema': 'lanes-linux-runtime-worker-v1', 'policy': deepcopy(q.POLICY),
             'model_manifest_sha256': 'a' * 64, 'resource_manifest_sha256': 'b' * 64,
             'workload_sha256': 'c' * 64, 'requirements_sha256': 'd' * 64,
             'implementation': {name: q.digest(Path(q.__file__).parent / name) for name in q.SOURCES}}
    if change == 'policy': value['policy']['cpus'] = 4
    if change == 'reference': value['references'] = []
    if change == 'implementation': value['implementation'][q.SOURCES[0]] = '0' * 64
    p = tmp_path / 'request.json'; q.write_new(p, value)
    sha = '0' * 64 if change == 'hash' else q.digest(p)
    with pytest.raises(ValueError): w.checked_request(p, sha)
