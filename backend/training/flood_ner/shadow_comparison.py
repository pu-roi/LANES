"""Explicit, file-only Linux location comparison; default is read-only preflight."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from typing import Any

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner import linux_runtime_v29 as q
from training.flood_ner.runtime_preflight import authenticate, bound_json, checked_path, digest, require
from app.services import ner_shadow_service as service

SCHEMA = 'lanes-shadow-grant-v30'
CODE = ('backend/app/services/ner_shadow_service.py',
        'backend/training/__init__.py', 'backend/training/flood_ner/__init__.py',
        'backend/training/flood_ner/shadow_comparison.py',
        'backend/training/flood_ner/shadow_worker.py',
        'backend/training/flood_ner/corrected_rules_worker.py',
        *('backend/training/flood_ner/' + n for n in q.SOURCES))
TESTS = ('backend/tests/test_ner_shadow_service.py', 'backend/tests/test_flood_ner_shadow_comparison.py')
RULE_ASSETS = ('runtime_data/flooded_areas_pasig_clean.csv', 'runtime_data/pasig_barangay_reference.csv',
               'runtime_data/philippines_psgc_reference.csv')
GRANT_KEYS = {'schema', 'implementation', 'tests', 'test_receipt', 'image_id', 'qualification',
              'model_manifest', 'resource_manifest', 'resource_dir', 'workload',
              'use_reviews', 'rules_files', 'requirements_sha256'}


def binding(root: Path, value: dict) -> Path:
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}, 'exact file binding required')
    path = checked_path(root, value['path'])
    require(digest(path) == value['sha256'], 'stale input binding')
    return path


def workload(value: dict) -> list[dict]:
    require(isinstance(value, dict) and set(value) == {'rows'} and isinstance(value['rows'], list),
            'raw workload required')
    rows = value['rows']; seen = set()
    require(bool(rows), 'empty workload')
    for row in rows:
        require(isinstance(row, dict) and set(row) == {'article_id', 'text', 'text_sha256', 'kind'},
                'no references, saved predictions or source identity fields')
        service.validate_input({k: row[k] for k in ('article_id', 'text', 'text_sha256')})
        require(row['article_id'] not in seen and row['kind'] in ('training_article', 'fictional'),
                'duplicate ID or unauthorized input kind')
        seen.add(row['article_id'])
    return rows


def preflight(root: Path, grant_path: Path, sha: str) -> tuple[dict, list[dict], dict]:
    grant = bound_json(grant_path, sha)
    require(set(grant) == GRANT_KEYS and grant['schema'] == SCHEMA, 'complete shadow authorization required')
    require(set(grant['implementation']) == set(CODE) and set(grant['tests']) == set(TESTS),
            'exact implementation and test bindings required')
    for group in ('implementation', 'tests'):
        for name, expected in grant[group].items():
            require(digest(checked_path(root, name)) == expected, 'stale implementation/tests')
    receipt = json.loads(binding(root, grant['test_receipt']).read_text(encoding='utf-8'))
    require(receipt['returncode'] == 0 and receipt['implementation'] == grant['implementation'] and
            receipt['tests'] == grant['tests'], 'matching passing pre-execution checks required')
    raw_tests = json.loads(binding(root, receipt['raw_receipt']).read_text(encoding='utf-8'))
    require(raw_tests['returncode'] == 0 and raw_tests['output_complete'] is True and
            all(name in raw_tests['args'] for name in TESTS), 'authentic complete test command receipt required')
    require(re.fullmatch(r'sha256:[a-f0-9]{64}', grant['image_id']) is not None, 'immutable image required')
    qual = json.loads(binding(root, grant['qualification']).read_text(encoding='utf-8'))
    require(qual['gate_3_cleared'] is True and qual['image_id'] == grant['image_id'] and
            all(qual[k] == 'passed' for k in ('compatibility', 'performance', 'failure_handling')),
            'qualified predecessor required')
    require(digest(root / 'backend/requirements.txt') == grant['requirements_sha256'], 'requirements changed')
    expected_rules = {p.relative_to(root / 'backend').as_posix() for p in (root / 'backend/app').rglob('*.py')} | set(RULE_ASSETS)
    require(set(grant['rules_files']) == expected_rules, 'complete current application-source and rules-asset bindings required')
    for name, expected in grant['rules_files'].items():
        require(digest(checked_path(root / 'backend', name)) == expected, 'rules source/asset changed')
    require('app/services/taglish_extraction_service.py' in grant['rules_files'], 'rules source missing')
    model_manifest = binding(root, grant['model_manifest'])
    resource_manifest = binding(root, grant['resource_manifest'])
    model = authenticate(model_manifest, grant['model_manifest']['sha256'], resource_manifest,
                         grant['resource_manifest']['sha256'], checked_path(root, grant['resource_dir']))
    rows = workload(json.loads(binding(root, grant['workload']).read_text(encoding='utf-8')))
    reviews = json.loads(binding(root, grant['use_reviews']).read_text(encoding='utf-8'))
    require(set(reviews) == {'predecessor', 'reviews'}, 'source-bound use reviews required')
    prior = json.loads(binding(root, reviews['predecessor']).read_text(encoding='utf-8'))
    expected = {r['source_sha256']: r['text'] for r in prior['candidates']}
    article_rows = [r for r in rows if r['kind'] == 'training_article']
    require(len(article_rows) == len(expected) == 6 and
            {r['text_sha256'] for r in article_rows} == set(expected), 'exact six previously reviewed articles required')
    supported = {r['source_sha256'] for r in reviews['reviews'] if
                 r['supported'] is True and r['purpose'] == 'private_offline_location_comparison' and
                 r['start'] == 0 and r['end'] == len(expected.get(r['source_sha256'], '')) and
                 r['no_policy_expansion'] is True}
    require(set(expected) <= supported and all(expected[r['text_sha256']] == r['text'] for r in article_rows),
            'full-extent use basis missing or original article changed')
    return grant, rows, model


def mounts_for(root: Path, grant: dict, model: dict, inputs: Path, output: Path) -> dict:
    mounts = {'/assets/MANIFEST.json': (binding(root, grant['model_manifest']), True),
              '/assets/models/control-seed-0/model': (model['model'], True),
              '/assets/resource.json': (binding(root, grant['resource_manifest']), True),
              '/assets/base': (checked_path(root, grant['resource_dir']), True),
              '/input': (inputs, True), '/output': (output, False)}
    for name in CODE:
        target = '/app/' + name[len('backend/'):] if name.startswith('backend/app/') else '/code/' + name[len('backend/'):]
        mounts[target] = (checked_path(root, name), True)
    return mounts


def container_args(docker: str, image: str, name: str, mounts: dict, request_sha: str) -> list[str]:
    require(re.fullmatch(r'sha256:[a-f0-9]{64}', image) is not None and
            re.fullmatch(r'lanes-ner-shadow-[a-f0-9]{16}', name) is not None, 'immutable container identity required')
    expected = {'/assets/MANIFEST.json', '/assets/models/control-seed-0/model', '/assets/resource.json',
                '/assets/base', '/input', '/output', '/app/app/services/ner_shadow_service.py',
                *('/code/' + n[len('backend/'):] for n in CODE if not n.startswith('backend/app/'))}
    require(set(mounts) == expected, 'exact scoped mounts required')
    args = [docker, 'create', '--name', name, '--network', 'none', '--cpus', '2', '--memory', '4g',
            '--memory-swap', '4g', '--pids-limit', '128', '--read-only', '--restart=no', '--cap-drop=ALL',
            '--security-opt=no-new-privileges', '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m', '--entrypoint', 'python']
    for target, (source, readonly) in mounts.items():
        require(source.exists() and ',' not in str(source) and readonly is (target != '/output'), 'unsafe mount')
        require(not any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)() for p in (source, *source.parents)), 'linked mount')
        args += ['--mount', f'type=bind,source={source.resolve()},target={target}' + (',readonly' if readonly else '')]
    for k, v in {'PYTHONDONTWRITEBYTECODE': '1', 'CUDA_VISIBLE_DEVICES': '', 'OMP_NUM_THREADS': '1',
                 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}.items():
        args += ['--env', k + '=' + v]
    return args + [image, '-I', '-B', '/code/training/flood_ner/shadow_worker.py',
                   '--request', '/input/request.json', '--request-sha256', request_sha]


def aggregate(rows: list[dict], outputs: list[dict], provenance: dict) -> dict:
    require(len(rows) == len(outputs), 'incomplete comparison')
    counts = {'articles': 0, 'fictional_cases': 0, 'neural_mentions': 0, 'rules_mentions': 0,
              'exact_pairs': 0, 'same_span_type_pairs': 0, 'boundary_links': 0,
              'unmatched_neural': 0, 'unmatched_rules': 0, 'unknown_rules_types': 0,
              'overlapping_rules_candidates': 0}
    for row, result in zip(rows, outputs):
        require(result['article_id'] == row['article_id'] and result['text_sha256'] == row['text_sha256'] and
                result['provenance'] == provenance and result['status'] == 'completed' and
                result['application_connected'] is False, 'comparison identity/status differs')
        neural, rules = result['neural']['mentions'], result['rules']['mentions']
        require(service.neural_mentions(row['text'], lambda _: neural) == neural, 'invalid neural output')
        for item in rules:
            service.validate_span(item, row['text'])
            require(item['label'] == service.TYPE_MAP.get(item['rules_type']), 'rules label mismatch')
        require(result['comparison'] == service.compare_mentions(neural, rules), 'fabricated disagreement totals')
        counts['articles' if row['kind'] == 'training_article' else 'fictional_cases'] += 1
        counts['neural_mentions'] += len(neural); counts['rules_mentions'] += len(rules)
        counts['unknown_rules_types'] += sum(r['label'] is None for r in rules)
        counts['overlapping_rules_candidates'] += sum(r['overlaps_other_rules_candidate'] for r in rules)
        for key in ('exact_pairs', 'same_span_type_pairs', 'boundary_links', 'unmatched_neural', 'unmatched_rules'):
            counts[key] += len(result['comparison'][key])
    return counts


def execute(root: Path, docker: str, grant_path: Path, sha: str, output: Path) -> dict:
    grant, rows, model = preflight(root, grant_path, sha)
    artifacts = Path(__file__).parent / 'artifacts'
    require(output.resolve().parent == artifacts.resolve() and not output.exists(), 'new direct private destination required')
    q.private_destination(output, artifacts)
    with q.exclusive(artifacts / 'shadow-active.lock', {'grant_sha256': sha, 'output': str(output)}):
        claims = artifacts / 'shadow-claims'; claims.mkdir(exist_ok=True)
        q.write_new(claims / (sha + '.json'), {'grant_sha256': sha, 'attempt': output.name})
        output.mkdir(); inputs = output / 'input'; inputs.mkdir(); worker_output = output / 'worker-output'; worker_output.mkdir()
        q.write_new(inputs / 'workload.json', {'rows': rows})
        provenance = {'model': grant['model_manifest']['sha256'], 'tokenizer': model['tokenizer_sha256'],
                      'rules': hashlib.sha256(json.dumps(grant['rules_files'], sort_keys=True).encode()).hexdigest()}
        request = {'schema': 'lanes-shadow-worker-v30', 'implementation': grant['implementation'],
                   'model_sha256': grant['model_manifest']['sha256'], 'resource_sha256': grant['resource_manifest']['sha256'],
                   'workload_sha256': digest(inputs / 'workload.json'), 'rules_files': grant['rules_files'],
                   'provenance': provenance, 'requirements_sha256': grant['requirements_sha256']}
        q.write_new(inputs / 'request.json', request)
        try:
            inspected = q.command([docker, 'image', 'inspect', grant['image_id']], output / 'image.json'); q.successful(inspected)
            image = json.loads(inspected['stdout'])[0]
            require(image['Id'] == grant['image_id'] and image['Os'] == 'linux', 'qualified image unavailable')
            mounts = mounts_for(root, grant, model, inputs, worker_output)
            name = 'lanes-ner-shadow-' + sha[:16]
            q.successful(q.command(container_args(docker, grant['image_id'], name, mounts, digest(inputs / 'request.json')), output / 'create.json'))
            inspected = q.command([docker, 'inspect', name], output / 'container.json'); q.successful(inspected)
            q.verify_isolation(json.loads(inspected['stdout'])[0], mounts)
            started = time.monotonic()
            try:
                q.successful(q.command([docker, 'start', name], output / 'start.json'))
                _, cold = q.monitor(docker, name, output, worker_output, started)
            except BaseException:
                q.command([docker, 'kill', name], output / 'failed-owned-stop.json', 10)
                q.command([docker, 'inspect', name], output / 'failed-owned-state.json', 10)
                raise
            measurements = json.loads((worker_output / 'measurements.json').read_text(encoding='utf-8'))
            results = [json.loads(line) for line in (worker_output / 'comparisons.jsonl').read_text(encoding='utf-8').splitlines()]
            counts = aggregate(rows, results, provenance)
            require(measurements['status'] == 'completed' and measurements['tokenizer_verified'] is True and
                    measurements['training_started'] is False and measurements['application_connected'] is False,
                    'worker did not complete safely')
            timings = measurements['row_seconds']
            require(len(timings) == len(rows), 'missing timing receipts')
            q.percentile95(timings)
            require(cold <= 60 and max(timings) <= 30 and 0 < measurements['peak_rss_bytes'] <= 3 * 1024**3,
                    'frozen runtime limit failed')
            preflight(root, grant_path, sha)  # Inputs must still match after processing.
            result = {'schema': 'lanes-shadow-aggregate-v30', 'status': 'offline_comparison_completed',
                      'counts': counts, 'cold_seconds': cold, 'row_p95_seconds': q.percentile95(timings),
                      'max_row_seconds': max(timings), 'peak_rss_bytes': measurements['peak_rss_bytes'],
                      'accuracy_measured': False, 'application_connected': False, 'training_started': False,
                      'validation_evaluated': False, 'holdout_accessed': False,
                      'grant_sha256': sha, 'image_id': grant['image_id']}
            q.write_new(output / 'aggregate.json', result)
            return result
        except BaseException as exc:
            q.write_new(output / 'failure.json', {'status': 'failed', 'error_type': type(exc).__name__,
                                                'application_connected': False, 'training_started': False})
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grant', type=Path, required=True); parser.add_argument('--grant-sha256', required=True)
    parser.add_argument('--execute', action='store_true'); parser.add_argument('--output', type=Path)
    parser.add_argument('--docker', default=r'C:\Program Files\Docker\Docker\resources\bin\docker.exe')
    args = parser.parse_args(); root = Path(__file__).resolve().parents[3]
    if args.execute:
        require(args.output is not None, 'new output required')
        result = execute(root, args.docker, args.grant, args.grant_sha256, args.output)
    else:
        preflight(root, args.grant, args.grant_sha256)
        result = {'status': 'verified_read_only', 'inference_started': False, 'application_connected': False}
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
