"""Independent inference-free audit of the authorized 3-GiB follow-up, pass or fail."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/scripts')]
from app.services.news_ner.bundle import digest, verify_bundle
from app.services.news_ner.contract import object_sha, validate_raw_input
from app.services.news_ner.location_pipeline import from_neural_mentions


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, value: object) -> None:
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')


def verify(package: Path, freeze_sha: str) -> dict:
    assert digest(package / 'freeze.json') == freeze_sha
    frozen = read(package / 'freeze.json')
    limits = frozen['limits']
    assert limits['cpus'] == 1 and limits['memory'] == limits['memory_swap'] == 3 * 1024**3
    assert limits['headroom'] == 2688 * 1024**2
    for filename, expected in frozen['bindings'].items(): assert digest(ROOT / filename) == expected, filename
    assert read(package / 'attempt.json')['attempts'] == 1
    claim = read(ROOT / 'backend/training/flood_ner/artifacts/rss-ner-phase-b-3g-qualification.claim.json')
    assert claim == {'attempts': 1, 'destination': package.name, 'freeze_sha256': freeze_sha}
    previous = ROOT / 'backend/training/flood_ner/artifacts/rss-ner-runtime-phase-b-2g-20261020-v1'
    assert digest(previous / 'freeze.json') == frozen['previous']['freeze_sha256']
    assert digest(previous / 'independent-audit.json') == frozen['previous']['audit_sha256']
    for name, sha in read(previous / 'final-package-manifest.json')['files'].items(): assert digest(previous / name) == sha
    request = read(package / 'input/request.json')
    bundle = ROOT / 'backend/training/flood_ner/artifacts/ner-preview-bundle-20261019-v1'
    verify_bundle(bundle, request['bundle_sha256'])
    rows = read(package / 'input/workload.json')['rows']
    assert digest(package / 'input/workload.json') == digest(previous / 'input/workload.json')
    expected = read(package / 'expected-predictions.json')
    assert digest(package / 'expected-predictions.json') == digest(previous / 'expected-predictions.json')
    path = package / 'output/responses.jsonl'
    responses = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
    ready_file = package / 'output/ready.json'
    ready = read(ready_file) if ready_file.exists() else None
    counts = {kind: 0 for kind in frozen['counts']}
    timings = {kind: [] for kind in counts}
    compared = 0
    previous_peak = 0
    for row, response in zip(rows, responses, strict=False):
        assert row['record_id'] == response['record_id']
        result = response['result']
        assert ready and result['provenance'] == ready['provenance']
        provenance = result['provenance']
        assert provenance['code_sha256'] == object_sha(request['code'])
        assert provenance['tokenizer_sha256'] == digest(bundle / 'model/tokenizer')
        raw = {k: row[k] for k in ('record_id', 'text', 'text_sha256', 'publication')}
        raw['mentions'] = result['proposal']['neural_mentions']
        validate_raw_input(raw)
        binding = object_sha({'bundle': request['bundle_sha256'], 'tokenizer': provenance['tokenizer_sha256'], 'text': row['text_sha256']})
        assert all(m['provenance_sha256'] == binding for m in raw['mentions'])
        pure = from_neural_mentions(raw)
        assert result['proposal'] == pure['proposal'] and result['graph'] == pure['graph']
        if row['record_id'] in expected:
            assert [[m['start'], m['end'], m['label']] for m in raw['mentions']] == expected[row['record_id']]
            compared += 1
        if row['kind'] == 'reviewed':
            saved = read(ROOT / 'backend/training/flood_ner/artifacts/backend-location-live-20261020-v46/worker-response.json')
            assert len(raw['mentions']) == 53 and result['graph'] == saved['graph'] and result['proposal'] == saved['proposal']
        peak = response['memory']['memory.peak']
        assert previous_peak <= peak
        previous_peak = peak
        counts[row['kind']] += 1
        timings[row['kind']].append(response['elapsed_seconds'])
    saved_container = json.loads((package / 'measurement-inspect-stdout.bin').read_bytes())[0]
    docker = 'C:/Program Files/Docker/Docker/resources/bin/docker.exe'
    current = json.loads(subprocess.run([docker, 'inspect', package.name + '-measurement'], capture_output=True, check=True, timeout=30).stdout)[0]
    assert saved_container['Id'] == current['Id'] and saved_container['Image'] == current['Image']
    host, state = current['HostConfig'], current['State']
    assert host['NanoCpus'] == 1000000000 and host['Memory'] == host['MemorySwap'] == 3 * 1024**3
    assert host['ReadonlyRootfs'] and host['Init'] and host['NetworkMode'] == 'none' and host['CapDrop'] == ['ALL']
    assert host['PidsLimit'] == 128 and 'no-new-privileges' in host['SecurityOpt']
    assert host['Tmpfs'] == {'/tmp': 'rw,noexec,nosuid,size=67108864'}
    assert not state['Running'] and state['Pid'] == 0
    mounts = {m['Destination']: m for m in current['Mounts']}
    assert set(mounts) == {'/input', '/output', '/app/app'}
    assert not mounts['/input']['RW'] and not mounts['/app/app']['RW']
    assert Path(mounts['/input']['Source']).resolve() == (package / 'input').resolve()
    assert not (package / 'input/expected-predictions.json').exists()
    baseline_file = package / 'output/baseline.json'
    baseline = read(baseline_file) if baseline_file.exists() else None
    if baseline:
        assert baseline['storage'] == 'fake' and baseline['connections'] == 0
        for name, sha in baseline['imported_source_hashes'].items(): assert digest(ROOT / 'backend' / name) == sha
    faults = json.loads((package / 'faults-run-stdout.bin').read_bytes())
    assert len(faults) == 8 and faults['parent_death']['terminated_and_reaped']
    assert all(v['reaped'] and v['cleanup_seconds'] <= 5 for k, v in faults.items() if k != 'parent_death')
    oom = json.loads((package / 'oom-inspect-stdout.bin').read_bytes())[0]
    assert oom['State']['OOMKilled'] and oom['State']['ExitCode'] == 137 and not oom['State']['Running']
    cached = read(package / 'cached-result.json')
    assert cached['cached_records'] == 788 and cached['saved_context_graphs_matched'] == 407 and not cached['neural_inference']
    complete = len(rows) == len(responses) == 355 and counts == frozen['counts']
    checks = {'full_workload': complete, 'prediction_count': compared == 352,
              'container_success': state['ExitCode'] == 0 and not state['OOMKilled'],
              'isolation': bool(ready and ready['isolation'] == {'seccomp': True, 'socket_families_denied': [2, 10, 1], 'raw_socket_denied': True, 'parent_death_signal': True}),
              'current_code_baseline': baseline is not None}
    result = {'status': 'failed', 'checks': checks, 'freeze_sha256': freeze_sha, 'verifier_sha256': digest(Path(__file__)),
              'counts': counts, 'neural_attempts': 1, 'automatic_retry': False, 'exact_prediction_records': compared,
              'graphs_verified': len(responses), 'cached_inputs': 788, 'cached_saved_graphs': 407,
              'previous_failed_attempt_preserved': True, 'runtime_model_and_rules_unchanged': True,
              'cloud_verified': False, 'cloud_changed': False, 'automatic_processing_connected': False}
    measurements = package / 'output/measurements.json'
    if measurements.exists():
        metric = read(measurements)
        assert metric['timings'] == timings
        p95 = sorted(timings['passage'])[math.ceil(.95 * len(timings['passage'])) - 1]
        assert metric['memory']['memory.peak'] >= previous_peak
        checks.update(cold=metric['cold_seconds'] <= 60, passage_p95=p95 <= 1,
                      articles=max(timings['article'] + timings['reviewed']) <= 30,
                      stress=max(timings['stress']) <= 60, headroom=metric['memory']['memory.peak'] < 2688 * 1024**2,
                      cleanup=metric['child_exit'] == 0 and metric['cleanup_seconds'] <= 5, session=metric['session_seconds'] < 450)
        envelope = metric['cold_seconds'] + max(value for values in timings.values() for value in values) + metric['cleanup_seconds']
        checks['startup_request_cleanup_envelope'] = envelope <= 125
        result.update(status='passed_local_3g_qualification' if all(checks.values()) else 'failed', cold_seconds=metric['cold_seconds'],
                      passage_p95_seconds=p95, article_max_seconds=max(timings['article']), reviewed_seconds=timings['reviewed'][0],
                      stress_max_seconds=max(timings['stress']), peak_container_bytes=metric['memory']['memory.peak'],
                      cleanup_seconds=metric['cleanup_seconds'], session_seconds=metric['session_seconds'],
                      measured_startup_request_cleanup_seconds=envelope,
                      max_completed_worker_rss_bytes=max(r['result']['measurements']['peak_worker_rss_bytes'] for r in responses))
    else:
        failure_path = package / 'output/failure.json'
        if failure_path.exists(): result['failure'] = read(failure_path)
    write(package / 'independent-audit.json', result)
    write(package / 'final-package-manifest.json', {'files': {p.relative_to(package).as_posix(): digest(p) for p in package.rglob('*')
          if p.is_file() and 'context' not in p.relative_to(package).parts and 'snapshot' not in p.relative_to(package).parts}})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--freeze-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.package.resolve(), args.freeze_sha256)))
