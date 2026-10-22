"""Freeze a scoring-only reassessment; never execute a study worker."""
from __future__ import annotations

import argparse
import hashlib
import importlib.abc
import json
from pathlib import Path
import sys

from .location_scoring_v45 import author_repaired_expectations

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT/'backend/training/flood_ner/artifacts'
P44 = ART/'location-repair-prepared-20261020-v44'
E44 = ART/'location-repair-execution-20261020-v44'
A44 = ART/'location-repair-analysis-20261020-v44'
CODE = ('backend/training/flood_ner/location_scoring_v45.py',
        'backend/training/flood_ner/location_reanalysis_v45.py',
        'backend/training/flood_ner/location_reassessment_v45.py',
        'backend/scripts/verify_location_v45.py', 'backend/tests/test_location_scoring_v45.py')


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def lines(path: Path) -> list[dict]:
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True); stream.write('\n')


def bound(path: Path) -> dict:
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def checked(binding: dict, root: Path = ROOT) -> Path:
    name = binding['path']
    if not isinstance(name, str) or '\\' in name or ':' in name or Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('unsafe evidence binding')
    target = (root/name).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file() or sha(target) != binding['sha256']:
        raise ValueError('missing or stale evidence binding')
    return target


def authenticate_v44() -> tuple[dict, list[Path]]:
    from .location_repair_study_v44 import check, preserved
    check(P44)
    inputs = []
    for folder in (P44, E44, A44):
        manifest = folder/'final-package-manifest.json'; inputs.append(manifest)
        for name, digest in read(manifest)['files'].items():
            file = folder/name
            if not file.resolve().is_relative_to(folder.resolve()) or sha(file) != digest:
                raise ValueError('historical v44 package mismatch')
            inputs.append(file)
    # Bind unchanged historical public interpretation as well as private evidence.
    for folder in (ROOT/'docs/evaluations/flood-ner-location-repair-v44-20261020',):
        inputs.extend(p for p in folder.iterdir() if p.is_file())
    inputs += [ROOT/'docs/plans/ner-location-repair-v44.md', ROOT/'docs/guides/ner-location-repair-v44.md']
    return preserved(), sorted(set(inputs))


def prepare(package: Path, test_receipt: Path) -> dict:
    assert not package.exists() and package.parent.resolve() == ART.resolve()
    preservation, inputs = authenticate_v44()
    test = read(test_receipt)
    assert test['returncode'] == 0 and test['source_hashes'] == {n: sha(ROOT/n) for n in CODE}
    # Oracles are authored solely from unchanged source fixtures, never outputs.
    source_cases = ROOT/'backend/training/flood_ner/artifacts/context-repair-prepared-20261019-v42/new-fixtures.json'
    oracles = author_repaired_expectations(read(source_cases))
    inputs += [source_cases, test_receipt]
    workload = {'saved_raw_inputs': 788, 'training': 345, 'contexts': 24, 'eligible_context_references': 23,
                'fictional_cases': 418, 'additional_repaired_view_expectations': 3,
                'article_occurrences': 34, 'article_rows': 19, 'article_facts': 93,
                'previous_complete_article_rows': 8, 'historical_misses': 7, 'three_holds_retained': True}
    acceptance = {'representation_only_normalization': True, 'old_control_expectations_unchanged': True,
                  'enabled_family_repaired_expectations_only': True, 'zero_new_strict_errors': True,
                  'no_supported_losses': True, 'no_span_qualifier_or_temporal_role_losses': True,
                  'real_correction_required_per_method': True, 'no_extraction_or_inference': True,
                  'saved_exposed_evidence_not_new_experiment': True, 'no_promotion': True}
    package.mkdir()
    for name, value in [('repaired-expectations.json', oracles), ('workload.json', workload),
                        ('acceptance.json', acceptance), ('preservation.json', preservation)]: write(package/name, value)
    freeze = {'schema': 'lanes-location-scoring-freeze-v45', 'implementation': {n: sha(ROOT/n) for n in CODE},
              'inputs': [bound(p) for p in sorted(set(inputs))],
              'package_files': {n: sha(package/n) for n in ('repaired-expectations.json', 'workload.json', 'acceptance.json', 'preservation.json')},
              'analysis_attempts': 1, 'extraction_attempts': 0, 'historical_v44_unchanged': True}
    write(package/'freeze.json', freeze)
    return {'status': 'frozen', 'freeze_sha256': sha(package/'freeze.json'), 'extraction_attempts': 0}


def check(package: Path) -> dict:
    freeze = read(package/'freeze.json')
    if freeze['schema'] != 'lanes-location-scoring-freeze-v45' or freeze['extraction_attempts'] != 0:
        raise ValueError('wrong scoring-only freeze')
    for n, digest in freeze['implementation'].items(): checked({'path': n, 'sha256': digest})
    for binding in freeze['inputs']: checked(binding)
    for name, digest in freeze['package_files'].items():
        if sha(package/name) != digest: raise ValueError('changed scoring expectation or workload')
    authenticate_v44()
    return freeze


class NoNeuralDatabase(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path: object = None, target: object = None) -> None:
        if fullname.split('.')[0] in {'spacy', 'torch', 'transformers', 'sqlalchemy', 'psycopg', 'psycopg2', 'asyncpg'}:
            raise RuntimeError('scoring-only: neural/database import prohibited')


def forbid_extraction(frame, event: str, arg: object) -> None:
    if event == 'call' and frame.f_code.co_name in {'extract', 'propose'}:
        raise RuntimeError('scoring-only: extraction/recognition call prohibited')


def forbid_external_actions(event: str, args: tuple) -> None:
    if event in {'subprocess.Popen', 'os.system', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise RuntimeError('scoring-only: worker/process/network action prohibited')


def reanalyze(package: Path, destination: Path) -> dict:
    check(package)
    assert not destination.exists() and destination.parent.resolve() == ART.resolve()
    write(ART/('location-v45-'+sha(package/'freeze.json')+'.claim.json'), {'destination': destination.name, 'analysis_attempts': 1, 'extraction_attempts': 0})
    destination.mkdir()
    guard = NoNeuralDatabase(); sys.meta_path.insert(0, guard)
    sys.addaudithook(forbid_external_actions); old_profile = sys.getprofile(); sys.setprofile(forbid_extraction)
    try:
        from .location_reassessment_v45 import assess
        result = assess(package, destination)
        check(package)
        write(destination/'execution-receipt.json', {'status': 'completed', 'extraction_calls': 0, 'inference': False,
              'worker_started': False, 'process_network_audit_guard': True, 'extraction_profile_guard': True,
              'historical_v44_unchanged': True, 'freeze_sha256': sha(package/'freeze.json')})
        write(destination/'manifest.json', {'files': [bound(p) for p in sorted(destination.iterdir()) if p.is_file()]})
        return result
    except BaseException as exc:
        write(destination/'failure.json', {'error_type': type(exc).__name__, 'no_automatic_retry': True, 'extraction_attempts': 0})
        raise
    finally:
        sys.setprofile(old_profile); sys.meta_path.remove(guard)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'check', 'reanalyze'))
    parser.add_argument('--package', type=Path, required=True); parser.add_argument('--output', type=Path)
    parser.add_argument('--test-receipt', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare': result = prepare(args.package.resolve(), args.test_receipt.resolve())
    elif args.action == 'reanalyze': result = reanalyze(args.package.resolve(), args.output.resolve())
    else: check(args.package.resolve()); result = {'status': 'verified'}
    print(json.dumps(result))
