"""Independent, inference-free verifier for the frozen Phase B local attempt."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from app.services.news_ner.bundle import digest, verify_bundle
from app.services.news_ner.contract import object_sha, validate_raw_input
from app.services.news_ner.location_pipeline import from_neural_mentions


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def verify(package: Path, expected_freeze: str) -> dict:
    assert digest(package / 'freeze.json') == expected_freeze
    freeze = read(package / 'freeze.json')
    for filename, expected in freeze['bindings'].items():
        assert digest(ROOT / filename) == expected, filename
    request = read(package / 'input/request.json')
    bundle = ROOT / 'backend/training/flood_ner/artifacts/ner-preview-bundle-20261019-v1'
    verify_bundle(bundle, request['bundle_sha256'])
    # Reconcile the controller's private manifest without rewriting any earlier receipt.
    for filename, expected in read(package / 'final-package-manifest.json')['files'].items():
        assert digest(package / filename) == expected
    rows = read(package / 'input/workload.json')['rows']
    expected = read(package / 'expected-predictions.json')
    responses = [json.loads(line) for line in (package / 'output/responses.jsonl').read_text(encoding='utf-8').splitlines()]
    ready = read(package / 'output/ready.json')
    provenance = ready['provenance']
    assert provenance['code_sha256'] == object_sha(request['code'])
    assert provenance['tokenizer_sha256'] == digest(bundle / 'model/tokenizer')
    assert provenance['model'] == 'v19-control-seed-0'
    assert ready['isolation'] == {'seccomp': True, 'socket_families_denied': [2, 10, 1],
                                  'raw_socket_denied': True, 'parent_death_signal': True}
    counts = {kind: 0 for kind in ('passage', 'article', 'reviewed', 'stress')}
    timings = {kind: [] for kind in counts}
    predictions = 0
    previous_peak = 0
    for row, response in zip(rows, responses, strict=False):
        assert response['record_id'] == row['record_id']
        result = response['result']
        assert result['provenance'] == provenance
        assert hashlib.sha256(row['text'].encode('utf-8')).hexdigest() == row['text_sha256']
        raw = {k: row[k] for k in ('record_id', 'text', 'text_sha256', 'publication')}
        raw['mentions'] = result['proposal']['neural_mentions']
        validate_raw_input(raw)
        binding = object_sha({'bundle': request['bundle_sha256'], 'tokenizer': provenance['tokenizer_sha256'], 'text': row['text_sha256']})
        assert all(m['provenance_sha256'] == binding for m in raw['mentions'])
        reproduced = from_neural_mentions(raw)
        assert result['proposal'] == reproduced['proposal'] and result['graph'] == reproduced['graph']
        if row['record_id'] in expected:
            assert [[m['start'], m['end'], m['label']] for m in raw['mentions']] == expected[row['record_id']]
            predictions += 1
        peak = response['memory']['memory.peak']
        assert previous_peak <= peak < 896 * 1024**2
        previous_peak = peak
        counts[row['kind']] += 1
        timings[row['kind']].append(response['elapsed_seconds'])
    # Verify the actual stopped container rather than deriving health from a final exit alone.
    docker = 'C:/Program Files/Docker/Docker/resources/bin/docker.exe'
    current = json.loads(subprocess.run([docker, 'inspect', package.name + '-measurement'],
        capture_output=True, check=True, timeout=30).stdout)[0]
    saved = json.loads((package / 'measurement-inspect-stdout.bin').read_bytes())[0]
    assert current['Id'] == saved['Id'] and current['Image'] == saved['Image']
    state, host = current['State'], current['HostConfig']
    assert not state['Running'] and state['Pid'] == 0 and state['ExitCode'] == 2 and state['OOMKilled']
    assert host['NanoCpus'] == 1000000000 and host['Memory'] == host['MemorySwap'] == 1024**3
    assert host['PidsLimit'] == 128 and host['ReadonlyRootfs'] and host['Init']
    assert host['NetworkMode'] == 'none' and host['CapDrop'] == ['ALL'] and 'no-new-privileges' in host['SecurityOpt']
    mounts = {m['Destination']: m for m in current['Mounts']}
    # Assets are in the image; expected predictions are never mounted.
    assert set(mounts) == {'/input', '/output', '/app/app'}
    assert host['Tmpfs'] == {'/tmp': 'rw,noexec,nosuid,size=67108864'}
    assert not mounts['/input']['RW'] and not mounts['/app/app']['RW']
    assert Path(mounts['/input']['Source']).resolve() == (package / 'input').resolve()
    assert not (package / 'input/expected-predictions.json').exists()
    baseline = read(package / 'output/baseline.json')
    for filename, expected_sha in baseline['imported_source_hashes'].items():
        assert digest(ROOT / 'backend' / filename) == expected_sha
    assert baseline['storage'] == 'fake' and baseline['connections'] == 0
    failure = read(package / 'output/failure.json')
    assert failure['completed_counts'] == counts and failure['child_exit'] == -9
    assert failure['memory']['memory.peak'] == 1024**3 and failure['cleanup_seconds'] <= 5
    assert read(package / 'output/begin-0353.json') == {'index': 353, 'kind': 'stress'}
    assert len(rows[353]['text']) == 100000 and len(responses) == 353
    assert counts == {'passage': 345, 'article': 6, 'reviewed': 0, 'stress': 2} and predictions == 351
    faults = json.loads((package / 'fault-run-stdout.bin').read_bytes())
    assert faults['parent_death']['terminated_and_reaped']
    for name, probe in faults.items():
        if name != 'parent_death': assert probe['reaped'] and probe['cleanup_seconds'] < 5
    oom = json.loads((package / 'oom-inspect-stdout.bin').read_bytes())[0]
    assert oom['State']['OOMKilled'] and not oom['State']['Running'] and oom['State']['ExitCode'] == 137
    cached = read(package / 'cached-result.json')
    assert cached['cached_records'] == 788 and cached['saved_context_graphs_matched'] == 407 and not cached['neural_inference']
    result = {'status': 'failed_memory_gate_independently_verified', 'freeze_sha256': expected_freeze,
              'verifier_sha256': digest(Path(__file__)), 'neural_attempts': 1, 'automatic_retry': False,
              'completed': counts, 'exact_prediction_records': predictions, 'completed_graphs_verified': len(responses),
              'cached_inputs': 788, 'cached_saved_graphs': 407,
              'cold_seconds': ready['supervisor_cold_seconds'],
              'passage_p95_seconds': sorted(timings['passage'])[math.ceil(.95 * len(timings['passage'])) - 1],
              'article_max_seconds': max(timings['article']), 'completed_container_peak_bytes': previous_peak,
              'failed_container_peak_bytes': failure['memory']['memory.peak'],
              'normal_worker_baseline_bytes': baseline['memory']['memory.peak'],
              'max_completed_worker_rss_bytes': max(r['result']['measurements']['peak_worker_rss_bytes'] for r in responses),
              'measurement_cleanup_seconds': failure['cleanup_seconds'], 'fictional_fault_checks': len(faults),
              'separate_container_oom_verified': True, 'source_and_receipt_preservation_verified': True,
              'unmeasured': ['maximum_length_response_and_latency', 'reviewed_53_prediction_article', 'successful_full_session_shutdown'],
              'cloud_verified': False, 'automatic_processing_connected': False}
    with (package / 'independent-audit.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--freeze-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.package.resolve(), args.freeze_sha256)))
