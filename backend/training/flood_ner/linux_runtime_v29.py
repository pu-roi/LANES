"""Versioned v29 offline Linux qualification controller; never an application or trainer.

Default CLI records engine preflight only. Real execution requires a hash-bound
grant and an absent private attempt directory. Failed attempts are never retried.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time
from typing import Any, Iterator

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner.runtime_preflight import authenticate, bound_json, checked_path, digest, private_destination, require

POLICY = {'cpus': 2, 'memory_bytes': 4 * 1024**3, 'rss_limit_bytes': 3 * 1024**3,
          'cold_seconds': 60, 'passage_p95_seconds': 1, 'article_seconds': 30,
          'stress_seconds': 60, 'max_chars': 100000, 'total_seconds': 1200,
          'network': 'none', 'concurrency': 1, 'training_count': 345,
          'languages': {'english': 170, 'taglish': 175}}
SOURCES = ('linux_runtime_v29.py', 'linux_runtime_worker_v29.py', 'runtime_preflight.py', 'runtime_probe_worker.py')
FAULTS = ('missing_asset', 'mismatched_asset', 'malformed_input', 'oversized_input', 'timeout', 'crash', 'oom', 'new_attempt_restart')


def write_new(path: Path, value: Any) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write('\n')


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def checked_spans(rows: list, text: str) -> list:
    require(isinstance(rows, list), 'explicit prediction list required')
    end = 0
    for row in rows:
        require(isinstance(row, list) and len(row) == 3, 'span triples required')
        start, stop, label = row
        from training.flood_ner.runtime_preflight import LABELS
        require(type(start) is int and type(stop) is int and end <= start < stop <= len(text)
                and isinstance(label, str) and label in LABELS, 'invalid, overlapping or unsupported span')
        end = stop
    return rows


def project_training(raw: list, metadata: list) -> tuple[list, dict]:
    require(len(raw) == len(metadata) == POLICY['training_count'], '345 training records required')
    meta = {r['record_id']: r for r in metadata}
    require(len(meta) == len(metadata), 'duplicate metadata ID')
    require(dict(Counter(r['language'] for r in metadata)) == POLICY['languages'], 'training languages differ')
    result, expected = [], {}
    for row in raw:
        require(set(row) == {'record_id', 'text', 'prediction'}, 'unexpected view fields')
        rid, text = row['record_id'], row['text']
        require(isinstance(rid, str) and re.fullmatch(r'train-[a-f0-9]{20}', rid) is not None
                and rid not in expected and rid in meta, 'invalid or duplicate opaque training ID')
        require(isinstance(text, str) and 0 < len(text) <= POLICY['max_chars'], 'invalid training text')
        m = meta[rid]
        require(set(m) == {'record_id', 'partition', 'language', 'text_sha256'}
                and m['partition'] == 'train' and m['text_sha256'] == text_hash(text), 'nontraining or mismatched input')
        expected[rid] = checked_spans(row['prediction'], text)
        result.append({'record_id': rid, 'text': text, 'text_sha256': text_hash(text), 'kind': 'passage'})
    require(set(meta) == set(expected), 'training join differs')
    return result, expected


def training_view(path: Path, sha: str) -> tuple[list, dict]:
    manifest = bound_json(path, sha)
    require(manifest.get('schema') == 'lanes-context-training-view-v1'
            and manifest.get('capability') == 'training_only' and manifest.get('count') == 345
            and manifest.get('primary_seed') == 0 and manifest.get('validation_emitted') is False,
            'authenticated primary training-only view required')
    paths = {name: checked_path(path.parent, name) for name in ('raw-predictions.jsonl', 'references.jsonl')}
    for name, p in paths.items(): require(digest(p) == manifest['files'][name], 'stale training view')
    raw = [json.loads(line) for line in paths['raw-predictions.jsonl'].read_text(encoding='utf-8').splitlines()]
    # Training annotations are not exported. Only partition/language/text metadata
    # is projected by the coordinator; the worker never receives references.
    metadata = [{k: row[k] for k in ('record_id', 'partition', 'language', 'text_sha256')}
                for row in map(json.loads, paths['references.jsonl'].read_text(encoding='utf-8').splitlines())]
    return project_training(raw, metadata)


def select_articles(candidates: list) -> tuple[list, dict]:
    """Candidates must carry reviewed full-extent use bindings, never inherit them."""
    eligible = []
    seen = set()
    for c in candidates:
        require(set(c) == {'article_id', 'text', 'source_sha256', 'languages', 'complete_capture',
                          'partition', 'full_extent_use_review'}, 'article review fields differ')
        require(c['partition'] == 'train' and c['complete_capture'] is True
                and c['source_sha256'] == text_hash(c['text']) and c['source_sha256'] not in seen,
                'duplicate, nontraining or incomplete article')
        require(isinstance(c['article_id'], str) and re.fullmatch(r'article-[a-f0-9]{20}', c['article_id'])
                and 0 < len(c['text']) <= POLICY['max_chars'] and c['languages']
                and set(c['languages']) <= {'english', 'taglish'}, 'invalid article identity/language')
        seen.add(c['source_sha256'])
        review = c['full_extent_use_review']
        require(set(review) == {'supported', 'evidence_sha256', 'source_sha256', 'start', 'end', 'purpose'}
                and isinstance(review['supported'], bool), 'explicit source-use decision required')
        if review['supported'] is not True: continue
        require(re.fullmatch(r'[a-f0-9]{64}', review['evidence_sha256']) is not None
                and review['source_sha256'] == c['source_sha256'] and type(review['start']) is int
                and type(review['end']) is int and review['start'] == 0 and review['end'] == len(c['text'])
                and review['purpose'] == 'private_runtime_qualification', 'unsupported full-extent use expansion')
        eligible.append(c)
    chosen, coverage = {}, {}
    for language in ('english', 'taglish'):
        rows = sorted((c for c in eligible if language in c['languages']), key=lambda c: (len(c['text']), c['source_sha256']))
        coverage[language] = len(rows)
        if rows:
            for i in (0, (len(rows) - 1) // 2, len(rows) - 1): chosen[rows[i]['source_sha256']] = rows[i]
    output = [{'record_id': c['article_id'], 'text': c['text'], 'text_sha256': c['source_sha256'], 'kind': 'article'}
              for c in sorted(chosen.values(), key=lambda c: c['article_id'])]
    return output, {'eligible_articles_per_language': coverage,
                    'article_coverage_complete': all(n >= 3 for n in coverage.values()), 'selected_articles': len(output)}


def stress_rows() -> list:
    texts = ['  PiÃ±a Road / PiÃ±a Road\n', 'May baha sa Aster Road; open ang kabilang street.',
             ('May baha sa PiÃ±a Road. ' * 5000)[:POLICY['max_chars']]]
    require(len(texts[-1]) == POLICY['max_chars'], 'maximum stress extent differs')
    return [{'record_id': f'stress-{i}', 'text': text, 'text_sha256': text_hash(text), 'kind': 'stress'}
            for i, text in enumerate(texts)]


def validate_workload(rows: list) -> None:
    require(isinstance(rows, list) and rows, 'nonempty workload required')
    seen = set()
    for row in rows:
        require(set(row) == {'record_id', 'text', 'text_sha256', 'kind'} and row['kind'] in ('passage', 'article', 'stress'),
                'worker accepts raw workload only')
        require(isinstance(row['record_id'], str) and row['record_id'] not in seen, 'duplicate workload ID')
        seen.add(row['record_id'])
        require(isinstance(row['text'], str) and 0 < len(row['text']) <= POLICY['max_chars']
                and row['text_sha256'] == text_hash(row['text']), 'invalid or changed workload text')
        pattern = {'passage': r'train-[a-f0-9]{20}', 'article': r'article-[a-f0-9]{20}', 'stress': r'stress-[0-2]'}[row['kind']]
        require(re.fullmatch(pattern, row['record_id']) is not None, 'nonopaque or wrong-kind ID')
    require(sum(r['kind'] == 'passage' for r in rows) == 345, 'complete training workload required')
    require(3 <= sum(r['kind'] == 'article' for r in rows) <= 6, 'complete deduplicated article workload required')
    require([r for r in rows if r['kind'] == 'stress'] == stress_rows(), 'frozen fictional probes differ')


def strict_parity(rows: list, predictions: list, expected: dict) -> dict:
    index = {r['record_id']: r for r in rows if r['kind'] == 'passage'}
    require(set(index) == set(expected), 'expected prediction membership differs')
    found, mismatches = set(), []
    for p in predictions:
        require(set(p) == {'record_id', 'text_sha256', 'prediction'}, 'unexpected prediction fields')
        rid = p['record_id']; require(rid in index and rid not in found, 'unexpected/duplicate prediction ID')
        found.add(rid); row = index[rid]
        require(p['text_sha256'] == row['text_sha256'], 'prediction text differs')
        if checked_spans(p['prediction'], row['text']) != checked_spans(expected[rid], row['text']): mismatches.append(rid)
    require(found == set(index), 'missing prediction')
    return {'records_compared': len(found), 'mismatch_count': len(mismatches), 'mismatch_ids': mismatches}


def percentile95(values: list[float]) -> float:
    require(bool(values) and all(type(v) in (float, int) and math.isfinite(v) and v >= 0 for v in values), 'finite timings required')
    return sorted(values)[math.ceil(.95 * len(values)) - 1]


def performance(metrics: dict, cold: float) -> dict:
    require(set(metrics) == {'passage_seconds', 'article_seconds', 'stress_seconds', 'peak_rss_bytes'}, 'measurement fields differ')
    require(len(metrics['passage_seconds']) == 345 and len(metrics['article_seconds']) > 0
            and len(metrics['stress_seconds']) == 3, 'complete measurements required')
    p95 = percentile95(metrics['passage_seconds'])
    for values in (metrics['article_seconds'], metrics['stress_seconds']): percentile95(values)
    require(type(cold) in (float, int) and math.isfinite(cold) and cold >= 0
            and type(metrics['peak_rss_bytes']) is int and metrics['peak_rss_bytes'] > 0, 'missing RSS/cold measurement')
    checks = {'cold': cold <= POLICY['cold_seconds'], 'passage_p95': p95 <= POLICY['passage_p95_seconds'],
              'articles': max(metrics['article_seconds']) <= POLICY['article_seconds'],
              'stress': max(metrics['stress_seconds']) <= POLICY['stress_seconds'],
              'rss': metrics['peak_rss_bytes'] <= POLICY['rss_limit_bytes']}
    summary = {}
    for kind in ('passage', 'article', 'stress'):
        values = metrics[kind + '_seconds']
        summary[kind] = {'calls': len(values), 'median_seconds': statistics.median(values),
                         'p95_seconds': percentile95(values), 'max_seconds': max(values),
                         'calls_per_second': len(values) / sum(values) if sum(values) > 0 else None}
    return {'checks': checks, 'passed': all(checks.values()), 'passage_p95_seconds': p95, 'timing_summary': summary}


@contextmanager
def exclusive(lock: Path, owner: dict | None = None) -> Iterator[None]:
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(owner or {'state': 'active'}, stream)
        stream.flush(); os.fsync(stream.fileno())
    try:
        yield
    except BaseException:
        # An interrupted owner may still have a container. Reconcile explicitly.
        raise
    else:
        lock.unlink()


def command(args: list[str], receipt: Path, timeout: int = 30) -> dict:
    require(not receipt.exists(), 'command receipt already exists')
    started = time.time()
    # Reserve exclusively before dispatch. Interrupted invocations retain this
    # record; a second writer cannot send a command under the same identity.
    write_new(receipt.with_name(receipt.stem + '-reservation.json'), {'args': args, 'started_unix': started})
    stdout_path = receipt.with_name(receipt.stem + '-stdout.bin')
    stderr_path = receipt.with_name(receipt.stem + '-stderr.bin')
    interrupted = None
    # File-backed output avoids communicate() waiting forever on inherited pipe
    # handles held by Windows daemon descendants after the CLI has timed out.
    with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
        try:
            r = subprocess.run(args, stdout=stdout, stderr=stderr, timeout=timeout, check=False)
            result = {'returncode': r.returncode, 'output_complete': True}
        except subprocess.TimeoutExpired:
            result = {'returncode': None, 'error': 'timeout', 'output_complete': False}
        except OSError as exc:
            result = {'returncode': None, 'error': type(exc).__name__, 'detail': str(exc), 'output_complete': False}
        except BaseException as exc:
            interrupted = exc
            result = {'returncode': None, 'error': type(exc).__name__, 'output_complete': False,
                      'dispatch_outcome': 'interrupted_reconciliation_required'}
        stdout.flush(); stderr.flush()
    result.update(stdout=stdout_path.read_bytes().decode('utf-8', errors='replace'),
                  stderr=stderr_path.read_bytes().decode('utf-8', errors='replace'))
    result.update(args=args, started_unix=started, completed_unix=time.time())
    write_new(receipt, result)
    if interrupted is not None: raise interrupted
    return result


def build_args(docker: str, backend: Path, base_digest: str, output: Path) -> list[str]:
    require(re.fullmatch(r'python@sha256:[a-f0-9]{64}', base_digest) is not None, 'pinned Python base digest required')
    return [docker, 'buildx', 'build', '--load', '--progress=plain',
            '--build-context', 'python:3.12-slim=docker-image://' + base_digest,
            '--metadata-file', str(output / 'build-metadata.json'), '--iidfile', str(output / 'image.id'),
            '-f', str(backend / 'Dockerfile'), str(backend)]


def container_args(docker: str, image: str, name: str, mounts: dict[str, tuple[Path, bool]], request_sha: str) -> list[str]:
    require(re.fullmatch(r'sha256:[a-f0-9]{64}', image) is not None, 'immutable image ID required')
    require(re.fullmatch(r'lanes-ner-qual-[a-f0-9]{16}', name) is not None, 'private container identity required')
    require(set(mounts) == {'/assets/MANIFEST.json', '/assets/models/control-seed-0/model', '/assets/resource.json',
            '/assets/base', '/input', '/output', *('/code/training/flood_ner/' + s for s in SOURCES)}, 'exact private mounts required')
    args = [docker, 'create', '--name', name, '--network', 'none', '--cpus', '2', '--memory', '4g', '--memory-swap', '4g',
            '--pids-limit', '128', '--read-only', '--restart=no', '--cap-drop=ALL', '--security-opt=no-new-privileges',
            '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m', '--entrypoint', 'python']
    for target, (source, readonly) in mounts.items():
        require(readonly is (target != '/output') and source.exists() and ',' not in str(source), 'unsafe mount')
        require(not any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)() for p in (source, *source.parents)), 'linked mount')
        args += ['--mount', f'type=bind,source={source.resolve()},target={target}' + (',readonly' if readonly else '')]
    for key, value in {'PYTHONDONTWRITEBYTECODE': '1', 'CUDA_VISIBLE_DEVICES': '', 'OMP_NUM_THREADS': '1',
                       'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}.items(): args += ['--env', key + '=' + value]
    return args + [image, '-I', '-B', '/code/training/flood_ner/linux_runtime_worker_v29.py',
                   '--request', '/input/request.json', '--request-sha256', request_sha]


def engine_preflight(docker: str, output: Path) -> dict:
    r = command([docker, 'info', '--format', '{{json .}}'], output / 'engine-info.json', 15)
    info = {}
    if r['returncode'] == 0:
        try: info = json.loads(r['stdout'])
        except ValueError: pass
    available = isinstance(info, dict) and info.get('OSType') == 'linux' and bool(info.get('ServerVersion'))
    return {'engine_available': available, 'image_built': False, 'linux_inference_run': False,
            'status': 'engine_available_qualification_pending' if available else 'blocked_engine',
            'compatibility': 'unmeasured', 'performance': 'unmeasured', 'failure_handling': 'constructed_tests_only',
            'gate_3_cleared': False, 'training_started': False, 'application_connected': False}


def verify_isolation(value: dict, mounts: dict[str, tuple[Path, bool]]) -> None:
    host = value['HostConfig']
    require(host['NetworkMode'] == 'none' and host['Memory'] == POLICY['memory_bytes']
            and host['MemorySwap'] == POLICY['memory_bytes'] and host['NanoCpus'] == 2_000_000_000
            and host['ReadonlyRootfs'] is True and host['RestartPolicy']['Name'] == 'no'
            and host['PidsLimit'] == 128 and 'ALL' in host['CapDrop']
            and any(s.startswith('no-new-privileges') for s in host['SecurityOpt']), 'container isolation differs')
    actual = {m['Destination']: m for m in value['Mounts'] if m['Type'] == 'bind'}
    require(set(actual) == set(mounts), 'unexpected bind mounts')
    for target, (_, readonly) in mounts.items(): require(actual[target]['RW'] is (not readonly), 'mount mutability differs')
    for item in value['Config']['Env']:
        key = item.split('=', 1)[0].upper()
        require(not any(s in key for s in ('PASSWORD', 'SECRET', 'TOKEN', 'CREDENTIAL', 'DATABASE', 'API_KEY')), 'credential-bearing image environment forbidden')


def successful(result: dict) -> None:
    require(result['returncode'] == 0, 'command failed; preserve receipt and stop')


def fault_program(case: str) -> str:
    require(case in FAULTS, 'unknown fault probe')
    common = "import json,os,sys,time\nsys.path.insert(0,'/code')\n"
    if case in ('missing_asset', 'mismatched_asset'):
        return common + "from pathlib import Path\nfrom training.flood_ner.runtime_preflight import verify_files\ntry:\n verify_files(Path('/probe'), {'fictional.bin': '" + '0' * 64 + "'})\nexcept (ValueError,OSError):\n print(json.dumps({'expected_rejection':True}));sys.exit(0)\nsys.exit(7)"
    if case in ('malformed_input', 'oversized_input'):
        text = '17' if case == 'malformed_input' else "'x'*100001"
        return common + "from training.flood_ner.linux_runtime_v29 import validate_workload,text_hash\ntext=" + text + "\ntry:\n validate_workload([{'record_id':'train-'+'0'*20,'text':text,'text_sha256':text_hash(text) if isinstance(text,str) else '', 'kind':'passage'}])\nexcept ValueError:\n print(json.dumps({'expected_rejection':True}));sys.exit(0)\nsys.exit(7)"
    if case == 'timeout': return common + "print('fault-timeout-started',flush=True)\ntime.sleep(30)"
    if case == 'crash': return common + "print('fault-crash-started',flush=True)\nos._exit(23)"
    if case == 'oom':
        return common + "print('fault-oom-started',flush=True)\na=[]\nwhile True:\n a.append(bytearray(8*1024*1024))"
    return common + "from pathlib import Path\np=Path('/output/restart.json')\nwith p.open('x') as f: json.dump({'explicit_new_attempt':True},f)\nprint('explicit-new-attempt-ok',flush=True)"


def executed_faults(docker: str, image: str, code: Path, output: Path, binding_sha: str) -> dict:
    """Eight explicit constructed container probes, no models/corpus/host stress."""
    suite = output / 'fault-probes'; suite.mkdir()
    checks, receipts = {}, {}
    for case in FAULTS:
        attempt = suite / case; attempt.mkdir()
        writable = attempt / 'output'; writable.mkdir()
        fixture = attempt / 'fixture'; fixture.mkdir()
        if case == 'mismatched_asset': (fixture / 'fictional.bin').write_bytes(b'fictional changed bytes')
        name = 'lanes-ner-fault-' + hashlib.sha256((binding_sha + str(output) + case).encode()).hexdigest()[:16]
        args = [docker, 'create', '--name', name, '--network', 'none', '--cpus', '1', '--memory', '128m',
                '--memory-swap', '128m', '--pids-limit', '32', '--read-only', '--restart=no', '--cap-drop=ALL',
                '--security-opt=no-new-privileges', '--entrypoint', 'python', '--env', 'PYTHONDONTWRITEBYTECODE=1',
                '--mount', f'type=bind,source={writable.resolve()},target=/output',
                '--mount', f'type=bind,source={fixture.resolve()},target=/probe,readonly']
        for source in SOURCES:
            args += ['--mount', f'type=bind,source={(code/source).resolve()},target=/code/training/flood_ner/{source},readonly']
        args += [image, '-I', '-B', '-c', fault_program(case)]
        successful(command(args, attempt / 'create.json'))
        successful(command([docker, 'start', name], attempt / 'start.json'))
        try:
            limit = 2 if case == 'timeout' else 20
            result = command([docker, 'wait', name], attempt / 'wait.json', limit)
            if case == 'timeout':
                require(result.get('error') == 'timeout', 'timeout probe unexpectedly exited')
                successful(command([docker, 'kill', name], attempt / 'kill.json', 10))
                successful(command([docker, 'wait', name], attempt / 'stopped-wait.json', 10))
            else: successful(result)
            result = command([docker, 'inspect', '--format', '{{json .State}}', name], attempt / 'state.json'); successful(result)
            state = json.loads(result['stdout']); require(state['Running'] is False, 'fault container still running')
            if case == 'oom': passed = state['OOMKilled'] is True and state['ExitCode'] == 137
            elif case == 'crash': passed = state['ExitCode'] == 23 and state['OOMKilled'] is False
            elif case == 'timeout': passed = state['ExitCode'] != 0
            else: passed = state['ExitCode'] == 0 and state['OOMKilled'] is False
            logs = command([docker, 'logs', name], attempt / 'logs.json'); successful(logs)
            if case in FAULTS[:4]: passed = passed and json.loads(logs['stdout']) == {'expected_rejection': True}
            if case == 'new_attempt_restart':
                passed = passed and json.loads((writable/'restart.json').read_text()) == {'explicit_new_attempt': True}
                passed = passed and not (suite/'crash/output/restart.json').exists()
            require(passed, 'executed fault outcome does not match frozen expectation')
            checks[case] = True
            receipts[case] = {p.name: digest(p) for p in attempt.iterdir() if p.is_file()}
        except BaseException:
            command([docker, 'kill', name], attempt / 'unexpected-stop.json', 10)
            raise
    result = {'schema':'lanes-executed-linux-faults-v29', 'image_id': image, 'binding_sha256': binding_sha,
              'checks': checks, 'receipts': receipts, 'passed': len(checks) == len(FAULTS) and all(checks.values())}
    write_new(suite / 'verification.json', result)
    return result


def monitor(docker: str, name: str, output: Path, worker_output: Path, started: float) -> tuple[dict, float]:
    """Watch the owned container only. Never leave a timed-out worker running."""
    ready = None; phase = None; phase_started = started; iteration = 0
    try:
        while True:
            elapsed = time.monotonic() - started
            if ready is None and (worker_output / 'ready.json').exists(): ready = elapsed
            hb = worker_output / 'heartbeat.json'
            if hb.exists():
                h = json.loads(hb.read_text(encoding='utf-8'))
                require(set(h) == {'phase', 'index'} and h['phase'] in ('passage', 'article', 'stress')
                        and type(h['index']) is int and h['index'] >= 0, 'invalid worker heartbeat')
                current = (h['phase'], h['index'])
                if current != phase: phase = current; phase_started = time.monotonic()
            limit = POLICY['article_seconds'] if phase and phase[0] == 'article' else POLICY['stress_seconds']
            require(elapsed <= POLICY['total_seconds'] and (ready is not None or elapsed <= POLICY['cold_seconds'])
                    and time.monotonic() - phase_started <= limit, 'container phase/total timeout')
            result = command([docker, 'inspect', '--format', '{{json .State}}', name], output / f'state-{iteration:05}.json', 5)
            successful(result); state = json.loads(result['stdout']); iteration += 1
            if not state['Running']:
                require(not state.get('OOMKilled') and state['ExitCode'] == 0 and not state.get('Error'), 'worker crash, OOM or unsuccessful exit')
                if ready is None and (worker_output / 'ready.json').exists(): ready = time.monotonic() - started
                require(ready is not None, 'worker never became ready')
                return state, ready
            time.sleep(.25)
    except BaseException:
        command([docker, 'kill', name], output / 'owned-container-stop.json', 10)
        command([docker, 'inspect', '--format', '{{json .State}}', name], output / 'failed-container-state.json', 10)
        raise


def execute(root: Path, docker: str, grant_path: Path, grant_sha: str, output: Path) -> dict:
    """Explicit execution path; callers must run engine_preflight first."""
    grant = bound_json(grant_path, grant_sha)
    require(set(grant) == {'schema', 'policy', 'implementation', 'test_binding', 'view', 'articles',
            'model_manifest', 'resource_manifest', 'resource_dir', 'backend_bindings', 'failure_probe_evidence'}
            and grant['schema'] == 'lanes-linux-runtime-grant-v29' and grant['policy'] == POLICY,
            'complete frozen Linux grant required')
    require(grant['failure_probe_evidence'] is None,
            'this measurement controller cannot accept inherited readiness/failure claims')
    code = Path(__file__).parent
    require(set(grant['implementation']) == set(SOURCES), 'implementation bindings incomplete')
    for name, sha in grant['implementation'].items(): require(digest(code / name) == sha, 'stale implementation')
    def binding(b: dict) -> Path:
        require(set(b) == {'path', 'sha256'}, 'exact file binding required')
        p = checked_path(root, b['path']); require(p.is_file() and digest(p) == b['sha256'], 'stale grant input')
        return p
    require(grant['test_binding']['path'] == 'backend/tests/test_flood_ner_linux_runtime_v29.py', 'constructed qualification tests required')
    binding(grant['test_binding'])
    require(set(grant['backend_bindings']) == {'Dockerfile', 'requirements.txt', '.dockerignore'}, 'backend build inputs incomplete')
    backend = root / 'backend'
    for name, sha in grant['backend_bindings'].items(): require(digest(backend / name) == sha, 'backend build source changed')
    ignore = (backend / '.dockerignore').read_text(encoding='utf-8').splitlines()
    require(all(s in ignore for s in ('training/flood_ner/artifacts/', '.env*', '.venv/', 'data/')), 'private Docker exclusions missing')
    model_manifest = binding(grant['model_manifest']); resources = binding(grant['resource_manifest'])
    resource_dir = checked_path(root, grant['resource_dir'])
    authenticated = authenticate(model_manifest, grant['model_manifest']['sha256'], resources,
                                 grant['resource_manifest']['sha256'], resource_dir)
    view = binding(grant['view']); passages, expected = training_view(view, grant['view']['sha256'])
    articles_path = binding(grant['articles']); article_ledger = json.loads(articles_path.read_text(encoding='utf-8'))
    require(set(article_ledger) == {'candidates', 'evidence'}, 'bound article reviews required')
    for b in article_ledger['evidence']: binding(b)
    evidence_hashes = {b['sha256'] for b in article_ledger['evidence']}
    require(all(c['full_extent_use_review']['evidence_sha256'] in evidence_hashes
                for c in article_ledger['candidates'] if c['full_extent_use_review']['supported']), 'missing article-use evidence payload')
    articles, coverage = select_articles(article_ledger['candidates'])
    require(coverage['article_coverage_complete'], 'saved article use/length coverage remains incomplete')
    rows = passages + articles + stress_rows(); validate_workload(rows)
    inputs = output / 'worker-input'; inputs.mkdir()
    worker_output = output / 'worker-output'; worker_output.mkdir()
    write_new(inputs / 'workload.json', {'rows': rows})
    write_new(output / 'expected-predictions.json', expected)  # Never mounted.
    request = {'schema': 'lanes-linux-runtime-worker-v29', 'policy': POLICY,
               'model_manifest_sha256': grant['model_manifest']['sha256'], 'resource_manifest_sha256': grant['resource_manifest']['sha256'],
               'workload_sha256': digest(inputs / 'workload.json'), 'implementation': grant['implementation'],
               'requirements_sha256': grant['backend_bindings']['requirements.txt']}
    write_new(inputs / 'request.json', request)
    write_new(output / 'frozen-workload.json', {'grant_sha256': grant_sha, 'policy': POLICY,
        'input_sha256': digest(inputs / 'workload.json'), 'request_sha256': digest(inputs / 'request.json'), 'coverage': coverage})
    with exclusive(code / 'artifacts/linux-runtime-active.lock', {'attempt': str(output.resolve()), 'grant_sha256': grant_sha}):
        successful(command([docker, 'pull', 'python:3.12-slim'], output / 'base-pull.json', 600))
        result = command([docker, 'image', 'inspect', 'python:3.12-slim'], output / 'base-inspect.json'); successful(result)
        base = json.loads(result['stdout'])[0]
        choices = sorted(d for d in base['RepoDigests'] if re.fullmatch(r'python@sha256:[a-f0-9]{64}', d))
        require(bool(choices) and base['Os'] == 'linux', 'Python Linux base digest unavailable')
        successful(command(build_args(docker, backend, choices[0], output), output / 'image-build.json', 1200))
        image = (output / 'image.id').read_text().strip()
        require(re.fullmatch(r'sha256:[a-f0-9]{64}', image) is not None, 'immutable build image missing')
        result = command([docker, 'image', 'inspect', image], output / 'image-inspect.json'); successful(result)
        built = json.loads(result['stdout'])[0]
        require(built['Id'] == image and built['Os'] == 'linux', 'build image identity/platform differs')
        for name, sha in grant['backend_bindings'].items(): require(digest(backend / name) == sha, 'build inputs changed during build')
        mounts = {'/assets/MANIFEST.json': (model_manifest, True), '/assets/models/control-seed-0/model': (authenticated['model'], True),
                  '/assets/resource.json': (resources, True), '/assets/base': (resource_dir, True),
                  '/input': (inputs, True), '/output': (worker_output, False)}
        mounts.update({'/code/training/flood_ner/' + name: (code / name, True) for name in SOURCES})
        name = 'lanes-ner-qual-' + hashlib.sha256((grant_sha + str(output.resolve())).encode()).hexdigest()[:16]
        successful(command(container_args(docker, image, name, mounts, digest(inputs / 'request.json')), output / 'create.json'))
        result = command([docker, 'inspect', name], output / 'container-inspect.json'); successful(result)
        verify_isolation(json.loads(result['stdout'])[0], mounts)
        startup_started = time.monotonic()
        try:
            successful(command([docker, 'start', name], output / 'start.json'))
        except BaseException:
            command([docker, 'kill', name], output / 'ambiguous-start-stop.json', 10)
            command([docker, 'inspect', '--format', '{{json .State}}', name], output / 'ambiguous-start-state.json', 10)
            raise
        state, cold = monitor(docker, name, output, worker_output, startup_started)
        measurements = json.loads((worker_output / 'measurements.json').read_text(encoding='utf-8'))
        require(measurements['status'] == 'worker_completed' and measurements['system'] == 'Linux'
                and measurements['python'][:2] == [3, 12] and measurements['spacy'] == '3.7.5'
                and measurements['tokenizer_verified'] is True and measurements['device'] == 'cpu', 'worker identity/result differs')
        predictions = [json.loads(s) for s in (worker_output / 'predictions.jsonl').read_text(encoding='utf-8').splitlines()]
        parity = strict_parity(rows, predictions, expected); write_new(output / 'private-parity.json', parity)
        require(len(measurements['metrics']['article_seconds']) == len(articles), 'article measurement count differs')
        perf = performance(measurements['metrics'], cold)
        # Real operational failure-probe evidence remains a distinct gate.
        # Constructed tests alone can never manufacture a Gate 3 pass.
        # Unexpected compatibility/performance failure stops the sequence.
        require(parity['mismatch_count'] == 0 and perf['passed'], 'compatibility or performance failed; no further dispatch')
        faults = executed_faults(docker, image, code, output, grant_sha)
        failure_status = 'passed' if faults['passed'] else 'failed'
        result = {'status': 'linux_measurements_completed', 'image_id': image, 'base_digest': choices[0],
                  'compatibility': 'passed' if parity['mismatch_count'] == 0 else 'failed_prediction_parity',
                  'records_compared': parity['records_compared'], 'parity_mismatches': parity['mismatch_count'],
                  'performance': 'passed' if perf['passed'] else 'failed', 'performance_checks': perf,
                  'failure_handling': failure_status, 'cold_host_seconds': cold,
                  'gate_3_cleared': parity['mismatch_count'] == 0 and perf['passed'] and failure_status == 'passed',
                  'training_started': False, 'application_connected': False}
        authenticate(model_manifest, grant['model_manifest']['sha256'], resources, grant['resource_manifest']['sha256'], resource_dir)
        return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--docker', required=True)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--grant', type=Path)
    p.add_argument('--grant-sha256')
    p.add_argument('--execute', action='store_true')
    args = p.parse_args()
    private_destination(args.output, Path(__file__).resolve().parent / 'artifacts')
    require(args.output.resolve().parent == (Path(__file__).resolve().parent / 'artifacts').resolve(),
            'attempt must be a direct new artifact subdirectory, outside frozen inputs')
    args.output.mkdir(parents=True, exist_ok=False)
    result = engine_preflight(args.docker, args.output)
    if args.execute and result['engine_available']:
        require(args.grant is not None and args.grant_sha256, 'explicit frozen execution grant required')
        try:
            result = execute(Path(__file__).resolve().parents[3], args.docker, args.grant, args.grant_sha256, args.output)
        except Exception as exc:
            result = {'status': 'execution_failed', 'error_type': type(exc).__name__, 'detail': str(exc),
                      'gate_3_cleared': False, 'training_started': False, 'application_connected': False}
    write_new(args.output / 'status.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
