"""Freeze, execute once, and score the isolated training-only location study."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from . import context_run_v38 as previous
from . import context_association_run as transport
from . import linux_runtime_v29 as runtime
from .location_repair_v40 import METHODS, object_sha, validate

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / 'backend/training/flood_ner/artifacts'
IMAGE = 'sha256:a51ce2a6b0f19f382ce96bf63c265e060b37112098176c97c66c23e887794680'
NEW = tuple('training/flood_ner/'+n for n in ('location_repair_v40.py', 'location_repair_worker_v40.py'))
WORKER_FILES = tuple(sorted(set(previous.WORKER_FILES) | set(NEW)))
CODE = tuple(sorted(set(previous.CODE) | {'backend/'+n for n in WORKER_FILES} | {
    'backend/training/flood_ner/location_repair_cases_v40.py',
    'backend/training/flood_ner/location_repair_scoring_v40.py',
    'backend/training/flood_ner/location_repair_study_v40.py',
    'backend/tests/test_location_repair_v40.py'}))
PREVIOUS = ART / 'context-association-fixed-links-20261019-v38'
ASSESSMENT = ART / 'extraction-gap-assessment-20261019-v39'
VIEW = ART / 'context-safeguard-training-view-20261019-v23'


def require(ok: bool, reason: str) -> None:
    if not ok: raise ValueError(reason)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def lines(path: Path) -> list[dict]:
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s]


def write(path: Path, value: Any) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, sort_keys=True); f.write('\n')


def binding(path: Path) -> dict:
    return {'path': path.resolve().relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def checked(value: dict) -> Path:
    path = transport.checked_path(ROOT, value['path'])
    require(sha(path) == value['sha256'], 'stale input: '+value['path'])
    return path


def preserve() -> dict:
    snapshot = read(ASSESSMENT / 'preservation-before.json')
    for name, b in snapshot['hash_bound'].items():
        require(sha(ROOT/name) == b['sha256'], 'changed protected training evidence')
    for group in ('historical_metadata_only', 'validation_holdout_metadata_only'):
        for name, b in snapshot[group].items():
            s = (ROOT/name).stat()
            require(s.st_size == b['bytes'] and s.st_mtime_ns == b['mtime_ns'], 'protected metadata changed')
    return {'hash_bound_files': len(snapshot['hash_bound']),
            'historical_metadata_only': len(snapshot['historical_metadata_only']),
            'validation_holdout_metadata_only': len(snapshot['validation_holdout_metadata_only']),
            'validation_holdout_contents_opened': False}


def fresh(path: Path) -> None:
    require(path.absolute().parent.resolve() == ART.resolve() and not path.exists(), 'absent direct private destination required')
    runtime.private_destination(path, ART)


def prepare(package: Path, test_receipt: Path) -> dict:
    from .location_repair_cases_v40 import location_cases, temporal_cases
    from .context_acceptance import validate_raw_input
    fresh(package)
    require(sha(PREVIOUS/'execution-grant.json') == 'e9384d69b016550cf30a6c69547f6141e21140c509d321423f1a744dfc4b7f69', 'v38 grant changed')
    require(read(test_receipt)['returncode'] == 0, 'passing test receipt required')
    test = read(test_receipt)
    code = {name: sha(ROOT/name) for name in CODE}
    require(test['source_hashes'] == code and test['output_complete'] is True and
            'backend/tests/test_location_repair_v40.py' in test['args'], 'tests not bound to final implementation')
    preservation = preserve()
    protocol = read(PREVIOUS/'protocol.json')
    raw_path = checked(read(PREVIOUS/'execution-grant.json')['request'])
    v38_raw = read(raw_path)['rows']
    old_protocol = read(ART/'context-association-coordination-20261019-v34/protocol.json')
    require(sha(VIEW/'manifest.json') == old_protocol['training_prediction_manifest_sha256'], 'training manifest changed')
    require(sha(VIEW/'raw-predictions.jsonl') == old_protocol['training_prediction_bytes_sha256'], 'saved v19 predictions changed')
    vm = read(VIEW/'manifest.json')
    require(vm['capability'] == 'training_only' and vm['count'] == 345 and vm['primary_seed'] == 0 and
            vm['validation_emitted'] is False and vm['holdout_accessed'] is False, 'training-only seed-0 view required')
    for name, h in vm['files'].items(): require(sha(VIEW/name) == h, 'stale training-only view file')
    raw_training = lines(VIEW/'raw-predictions.jsonl'); refs = lines(VIEW/'references.jsonl')
    require(len(raw_training) == len(refs) == 345 and len({r['record_id'] for r in raw_training}) == 345,
            'complete unique training workload required')
    ref_map = {r['record_id']: r for r in refs}
    require(len(ref_map) == 345 and set(ref_map) == {r['record_id'] for r in raw_training} and
            all(r['partition'] == 'train' for r in refs), 'reference partition/identity differs')
    training = []
    for row in raw_training:
        text = row['text']; reference = ref_map[row['record_id']]
        require(hashlib.sha256(text.encode('utf-8')).hexdigest() == reference['text_sha256'], 'training text join differs')
        mentions = []
        for i, (a, b, label) in enumerate(row['prediction']):
            provenance = {'prediction_file_sha256': sha(VIEW/'raw-predictions.jsonl'),
                          'row': row['record_id'], 'span': [a, b, label], 'seed': 0}
            h = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
            mentions.append({'id': f'n{i}', 'start': a, 'end': b, 'text': text[a:b], 'label': label, 'provenance_sha256': h})
        value = {'record_id': row['record_id'], 'text': text, 'mentions': mentions}; validate(value); training.append(value)
    real = [r for r in v38_raw if r['record_id'].startswith('train-')]
    existing = [r for r in v38_raw if r['record_id'].startswith('fictional-')]
    require(len(real) == 24 and len(existing) == 238, 'frozen contextual workload differs')
    loc = location_cases(); times = temporal_cases()
    require(len(loc) == len(times) == 36, '72 constructed cases required')
    for row in [*real, *existing, *(c['raw'] for c in times)]: validate_raw_input(row)
    for row in [c['raw'] for c in loc]: validate(row)
    package.mkdir()
    write(package/'location-fixtures.json', loc); write(package/'temporal-fixtures.json', times)
    write(package/'preservation.json', preservation)
    request = {'schema': 'lanes-location-study-v40', 'training_rows': training, 'context_rows': real,
               'location_rows': [c['raw'] for c in loc], 'temporal_rows': [c['raw'] for c in times],
               'existing_rows': existing, 'implementation': {n: code['backend/'+n] for n in WORKER_FILES}}
    write(package/'request.json', request)
    # Exact existing fixture/reference bytes remain outside worker mounts.
    prior = read(PREVIOUS/'private-manifest.json')
    outputs_path = ART/'context-association-execution-20261019-v38/worker-output/results.jsonl'
    inputs = [VIEW/'manifest.json', VIEW/'raw-predictions.jsonl', VIEW/'references.jsonl',
              checked(protocol['scoring_inputs']), PREVIOUS/'fixtures-final.json',
              PREVIOUS/'analysis-v1/remaining-errors.json', outputs_path,
              ASSESSMENT/'preservation-before.json', ASSESSMENT/'manifest.json',
              ART/'context-reference-review-20261019-v37/input/held-dispositions.json',
              test_receipt, PREVIOUS/'private-manifest.json']
    for n in ('location-fixtures.json', 'temporal-fixtures.json', 'request.json', 'preservation.json'):
        inputs.append(package/n)
    study = {'schema': 'lanes-location-freeze-v40', 'image_id': IMAGE, 'implementation': code,
             'inputs': [binding(p) for p in inputs], 'request': binding(package/'request.json'),
             'test_receipt': binding(test_receipt), 'training_references': binding(VIEW/'references.jsonl'),
             'context_references': protocol['scoring_inputs'], 'previous_context': binding(outputs_path),
             'existing_fixtures': binding(PREVIOUS/'fixtures-final.json'),
             'location_fixtures': binding(package/'location-fixtures.json'), 'temporal_fixtures': binding(package/'temporal-fixtures.json'),
             'seven_errors': binding(PREVIOUS/'analysis-v1/remaining-errors.json'),
             'methods': list(METHODS), 'attempts': 1, 'counts': {'training': 345, 'context': 24, 'eligible': 23,
             'location': 36, 'temporal': 36, 'existing': 238, 'total': 679},
             'decision': 'zero_new_strict_fp_zero_correct_loss_positive_correction_all_behavior_and_temporal_checks',
             'no_post_result_tuning': True, 'no_validation_holdout_content': True,
             'reference_manifest_sha256': prior['reference_manifest_sha256']}
    write(package/'freeze.json', study)
    return {'status': 'frozen', 'freeze_sha256': sha(package/'freeze.json'), 'records': 679, 'preservation': preservation}


def preflight(path: Path, expected_sha: str) -> tuple[dict, dict]:
    require(sha(path) == expected_sha, 'stale freeze')
    freeze = read(path)
    require(freeze['schema'] == 'lanes-location-freeze-v40' and freeze['methods'] == list(METHODS) and
            freeze['attempts'] == 1 and freeze['no_post_result_tuning'] and
            freeze['decision'] == 'zero_new_strict_fp_zero_correct_loss_positive_correction_all_behavior_and_temporal_checks', 'changed protocol')
    require(set(freeze['implementation']) == set(CODE), 'incomplete implementation binding')
    for name, h in freeze['implementation'].items(): require(sha(ROOT/name) == h, 'implementation/tests changed')
    for b in freeze['inputs']: checked(b)
    request = read(checked(freeze['request']))
    require(request['implementation'] == {n: freeze['implementation']['backend/'+n] for n in WORKER_FILES}, 'worker closure changed')
    for name, count in [('training_rows', 345), ('context_rows', 24), ('location_rows', 36), ('temporal_rows', 36), ('existing_rows', 238)]:
        rows = request[name]
        require(len(rows) == len({r['record_id'] for r in rows}) == count, 'raw workload changed')
        for row in rows:
            allowed = {'record_id', 'text', 'mentions'} if name in {'training_rows', 'location_rows'} else {'record_id', 'text', 'text_sha256', 'publication', 'mentions'}
            require(set(row) == allowed, 'references/expectations in worker input')
    preserve()
    return freeze, request


def execute(path: Path, expected_sha: str, output: Path, docker: str) -> dict:
    freeze, request = preflight(path, expected_sha); fresh(output)
    with runtime.exclusive(ART/'location-repair-v40-active.lock', {'freeze_sha256': expected_sha}):
        claims = ART/'location-repair-v40-claims'; claims.mkdir(exist_ok=True)
        write(claims/(expected_sha+'.json'), {'output': output.name, 'freeze_sha256': expected_sha})
        output.mkdir()
        name = 'lanes-context-candidate-'+expected_sha[:16]
        created = False
        try:
            receipt = runtime.command([docker, 'image', 'inspect', freeze['image_id']], output/'image.json')
            runtime.successful(receipt); require(json.loads(receipt['stdout'])[0]['Id'] == IMAGE, 'qualified image differs')
            input_dir = output/'input'; input_dir.mkdir(); worker = output/'worker-output'; worker.mkdir()
            write(input_dir/'request.json', request)
            mounts = {'/input': (input_dir, True), '/output': (worker, False)}
            mounts.update({'/code/'+n: (ROOT/'backend'/n, True) for n in WORKER_FILES})
            cmd = transport.container_args(docker, IMAGE, name, mounts, 'training/flood_ner/location_repair_worker_v40.py',
                                           sha(input_dir/'request.json'), WORKER_FILES)
            runtime.successful(runtime.command(cmd, output/'create.json')); created = True
            r = runtime.command([docker, 'inspect', name], output/'container.json'); runtime.successful(r)
            runtime.verify_isolation(json.loads(r['stdout'])[0], mounts)
            started = time.monotonic(); runtime.successful(runtime.command([docker, 'start', name], output/'start.json'))
            _, cold = runtime.monitor(docker, name, output, worker, started)
            r = runtime.command([docker, 'inspect', name], output/'completed-state.json'); runtime.successful(r)
            state = json.loads(r['stdout'])[0]; runtime.verify_isolation(state, mounts)
            require(not state['State']['Running'] and state['State']['Pid'] == 0 and state['State']['ExitCode'] == 0 and
                    not state['State']['OOMKilled'], 'unsuccessful worker')
            status = read(worker/'status.json')
            require(status['status'] == 'completed' and status['processed'] == 679 and
                    not status['neural_libraries_loaded'] and status['network_database_blocked'], 'incomplete output')
            preflight(path, expected_sha)
            result = {'status': 'completed', 'records': 679, 'cold_seconds': cold,
                      'wall_seconds': time.monotonic()-started, 'image_id': IMAGE,
                      'neural_inference': False, 'application_connected': False, 'training_started': False}
            write(output/'execution.json', result)
            write(output/'output-manifest.json', {'files': [binding(f) for f in sorted(worker.iterdir()) if f.is_file()]})
            return result
        except BaseException as exc:
            if created:
                runtime.command([docker, 'kill', name], output/'failed-owned-stop.json', 10)
                runtime.command([docker, 'inspect', name], output/'failed-owned-state.json', 10)
            write(output/'failure.json', {'error_type': type(exc).__name__, 'reason': str(exc), 'retry_allowed': False})
            raise


def score(path: Path, expected_sha: str, execution: Path, destination: Path) -> dict:
    from . import location_repair_scoring_v40 as s
    from .context_review_v37 import fixture_result
    from .context_association_scoring import output_keys, json_key
    freeze, request = preflight(path, expected_sha)
    require(not destination.exists() and destination.parent == path.parent, 'new private analysis directory required')
    require(read(execution/'execution.json')['status'] == 'completed', 'completed single execution required')
    for b in read(execution/'output-manifest.json')['files']: checked(b)
    worker = execution/'worker-output'
    groups = {}
    for name, count in [('training_rows', 345), ('context_rows', 24), ('location_rows', 36), ('temporal_rows', 36), ('existing_rows', 238)]:
        rows = lines(worker/(name+'.jsonl')); actual = {r['record_id']: r for r in rows}
        require(len(rows) == len(actual) == count and actual.keys() == {r['record_id'] for r in request[name]}, 'missing/duplicate worker outputs')
        groups[name] = actual
    refs = {r['record_id']: r for r in lines(checked(freeze['training_references']))}
    contexts = {r['record_id']: r for r in read(checked(freeze['context_references']))}
    old = {r['record_id']: r for r in lines(checked(freeze['previous_context']))}
    loc_cases = read(checked(freeze['location_fixtures'])); times = read(checked(freeze['temporal_fixtures']))
    old_cases = read(checked(freeze['existing_fixtures']))
    errors = read(checked(freeze['seven_errors']))
    temporal = [s.temporal_result(c, groups['temporal_rows'][c['raw']['record_id']]['output']) for c in times]
    destination.mkdir(); summaries = {}; details = {}; dispositions = {}
    # A baseline fixture rerun cannot silently diverge from its saved predecessor.
    baseline_fixtures = []
    for case in old_cases:
        rid = 'fictional-'+hashlib.sha256(case['case_id'].encode()).hexdigest()[:20]
        value = groups['existing_rows'][rid]['baseline']
        require(value == old[rid], 'unchanged v38 fixture output differs from saved output')
        raw = next(r for r in request['existing_rows'] if r['record_id'] == rid)
        baseline_fixtures.append(fixture_result(case, raw, value, exhaustive=case['case_id'].startswith(('fictional-v36_', 'fictional-v37_', 'fictional-v38_'))))
    require(all(r['passed'] for r in baseline_fixtures), 'existing v38 fixture baseline failed')
    for method in METHODS:
        training = []
        for row in request['training_rows']:
            repair = groups['training_rows'][row['record_id']]['methods'][method]['repair']
            require(repair['neural_mentions'] == row['mentions'], 'original predictions changed')
            training.append({'record_id': row['record_id'], **s.recognition(refs[row['record_id']]['reference'], row['mentions'], repair['effective_mentions'])})
        down = [dict(record_id=rid, **s.context(item['revised_reference'], old[rid], groups['context_rows'][rid]['methods'][method]['context']))
                for rid, item in contexts.items()]
        fixtures = [s.location_result(c, groups['location_rows'][c['raw']['record_id']]['methods'][method]['repair'])
                    for c in loc_cases if method == 'combined' or c['family'] == method]
        existing = []
        for case in old_cases:
            rid = 'fictional-'+hashlib.sha256(case['case_id'].encode()).hexdigest()[:20]
            record = groups['existing_rows'][rid]['methods'][method]
            raw = next(r for r in request['existing_rows'] if r['record_id'] == rid)
            effective = {**raw, 'mentions': record['repair']['effective_mentions']}
            existing.append(fixture_result(case, effective, record['context'], exhaustive=case['case_id'].startswith(('fictional-v36_', 'fictional-v37_', 'fictional-v38_'))))
        summaries[method] = s.aggregate(training, down, fixtures, existing, temporal)
        details[method] = {'training': training, 'context': down, 'location_fixtures': fixtures, 'existing_fixtures': existing}
        dispositions[method] = []
        for error in errors:
            out = groups['context_rows'][error['opaque_id']]['methods'][method]['context']
            keys = {json_key(k) for k in output_keys(out)['links']}
            dispositions[method].append({'error_id': error['error_id'], 'kind': error['strict_key'][0][0],
                                          'recovered': json_key(error['strict_key']) in keys})
        summaries[method]['seven_misses_recovered'] = sum(d['recovered'] for d in dispositions[method])
    write(destination/'details.json', details); write(destination/'temporal-results.json', temporal)
    write(destination/'seven-error-dispositions.json', dispositions)
    write(destination/'summary.json', {'methods': summaries, 'temporal_passed': sum(r['passed'] for r in temporal),
                                      'temporal_total': 36, 'existing_baseline_passed': 238,
                                      'three_reference_holds_retained': True, 'pure_tagalog_real_performance': 'unmeasured',
                                      'system_connection_cleared': False, 'new_neural_inference': False,
                                      'new_training': False, 'no_post_result_tuning': True})
    write(destination/'preservation.json', preserve())
    write(destination/'manifest.json', {'files': [binding(f) for f in sorted(destination.iterdir()) if f.is_file()]})
    return {'methods': summaries, 'temporal_passed': sum(r['passed'] for r in temporal), 'temporal_total': 36,
            'existing_baseline_passed': 238, 'application_connected': False}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('action', choices=('prepare', 'verify', 'execute', 'score'))
    p.add_argument('--package', type=Path); p.add_argument('--test-receipt', type=Path)
    p.add_argument('--freeze', type=Path); p.add_argument('--sha256'); p.add_argument('--output', type=Path)
    p.add_argument('--execution', type=Path)
    p.add_argument('--docker', default=r'C:\Program Files\Docker\Docker\resources\bin\docker.exe')
    args = p.parse_args()
    if args.action == 'prepare': result = prepare(args.package, args.test_receipt)
    elif args.action == 'execute': result = execute(args.freeze, args.sha256, args.output, args.docker)
    elif args.action == 'score': result = score(args.freeze, args.sha256, args.execution, args.output)
    else:
        preflight(args.freeze, args.sha256); result = {'status': 'verified_read_only', 'records': 679}
    print(json.dumps(result))


if __name__ == '__main__': main()
