"""Freeze and execute one source-only junction-repair feasibility study."""
from copy import deepcopy
import argparse
import json
from pathlib import Path

from .context_study_v42 import read, sha, lines, write, bound, command, preservation, IMAGE, ROOT, ART
from .location_repair_cases_v44 import location_cases
from .location_repair_v44 import METHODS, object_text_sha

P40 = ART/'location-repair-prepared-20261019-v40'
E40 = ART/'location-repair-execution-20261019-v40'
P42 = ART/'context-repair-prepared-20261019-v42'
E42 = ART/'context-repair-execution-20261019-v42'
A43 = ART/'recognition-gap-assessment-20261020-v43'
WORKER = {f'news_ner/{n}': 'backend/app/services/news_ner/'+n for n in
          ('__init__.py', 'contract.py', 'context_association.py', 'context_association_v38.py', 'context_association_v42.py')}
WORKER.update({f'training/flood_ner/{n}': 'backend/training/flood_ner/'+n for n in ('__init__.py', 'location_repair_v40.py', 'location_repair_v44.py')})
WORKER['training/__init__.py'] = 'backend/training/__init__.py'
WORKER['location_repair_worker_v44.py'] = 'backend/training/flood_ner/location_repair_worker_v44.py'
CODE = sorted(set(WORKER.values()) | {'backend/training/flood_ner/'+n for n in
              ('location_repair_study_v44.py', 'location_repair_scoring_v44.py', 'location_repair_cases_v44.py')} |
              {'backend/tests/test_location_repair_v44.py', 'backend/tests/test_location_repair_study_v44.py', 'backend/scripts/verify_location_v44.py'})


def preserved() -> dict:
    value = preservation()
    for freeze_path in (P40/'freeze.json', P42/'freeze.json'):
        freeze = read(freeze_path)
        for name, digest in freeze['implementation'].items(): assert sha(ROOT/name) == digest, name
    for name, digest in read(ART/'context-repair-verification-20261019-v42/promotion.json')['source_hashes'].items():
        assert sha(ROOT/name) == digest, name
    for name, digest in read(A43/'input-bindings.json').items(): assert sha(ROOT/name) == digest, name
    for name, digest in read(A43/'manifest.json')['files'].items(): assert sha(A43/name) == digest, name
    value['v40_v42_and_promoted_application_unchanged'] = True
    return value


def normalize(raw: dict) -> dict:
    return {'record_id': raw['record_id'], 'text': raw['text'], 'text_sha256': object_text_sha(raw['text']),
            'publication': deepcopy(raw.get('publication')), 'mentions': deepcopy(raw['mentions'])}


def envelope(raw: dict, control: list[dict]) -> dict:
    return {'record_id': raw['record_id'], 'raw': normalize(raw), 'control_mentions': deepcopy(control)}


def prepare(destination: Path, test_receipt: Path) -> dict:
    assert not destination.exists() and destination.parent.resolve() == ART.resolve()
    kept = preserved()
    test = read(test_receipt)
    assert test['returncode'] == 0 and test['source_hashes'] == {n: sha(ROOT/n) for n in CODE}
    p40 = read(P40/'request.json'); p42 = read(P42/'request.json')['groups']; freeze40 = read(P40/'freeze.json')
    inputs = [P40/'freeze.json', P40/'request.json', P42/'freeze.json', P42/'request.json',
              P42/'article-oracle.json', A43/'case-ledger.json', A43/'verification.json', A43/'manifest.json', test_receipt]
    for execution in (E40, E42):
        inputs.append(execution/'output-manifest.json')
        for b in read(execution/'output-manifest.json')['files']:
            assert sha(ROOT/b['path']) == b['sha256']; inputs.append(ROOT/b['path'])
    for key in ('training_references', 'context_references', 'existing_fixtures', 'seven_errors', 'location_fixtures', 'temporal_fixtures'):
        b = freeze40[key]; assert sha(ROOT/b['path']) == b['sha256']; inputs.append(ROOT/b['path'])
    # Original + combined controls come only from saved outputs. No v40 rule rerun.
    controls = {group: {r['record_id']: r for r in lines(E40/'worker-output'/(group+'.jsonl'))}
                for group in ('training_rows', 'location_rows')}
    groups = {}
    for key, oldkey in (('training', 'training_rows'), ('location_fixtures', 'location_rows')):
        groups[key] = [envelope(r, controls[oldkey][r['record_id']]['methods']['combined']['repair']['effective_mentions'])
                       for r in p40[oldkey]]
    for key, oldkey in (('contexts', 'context_rows'), ('existing', 'existing_rows')):
        groups[key] = [envelope(r['views']['original'], r['views']['combined']['mentions']) for r in p42[oldkey]]
    groups['article'] = [envelope(r, r['mentions']) for r in p42['article_rows']]
    for key, oldkey in (('temporal', 'temporal_rows'), ('v41', 'old_regressions'), ('v42', 'new_regressions')):
        groups[key] = [envelope(r, r['mentions']) for r in p42[oldkey]]
    cases = location_cases(); groups['new'] = [envelope(c['raw'], c['raw']['mentions']) for c in cases]
    assert sum(map(len, groups.values())) == 788
    destination.mkdir()
    request = {'schema': 'lanes-location-worker-v44', 'implementation': {n: sha(ROOT/p) for n, p in WORKER.items()}, 'groups': groups}
    write(destination/'request.json', request); write(destination/'new-fixtures.json', cases); write(destination/'preservation.json', kept)
    acceptance = {'new_fictional_cases': 36, 'preserved_location_cases': 36, 'preserved_context_temporal_cases': 346,
                  'strict_new_location_fp': 0, 'lost_correct_locations': 0, 'new_wrong_associations': 0,
                  'lost_supported_associations': 0, 'strict_span_regressions': 0, 'qualifier_loss': 0,
                  'at_least_one_source_supported_real_correction_per_qualifying_method': True,
                  'all_original_expectations_preserved': True, 'article_cases': 34, 'article_unresolved_rows': 19,
                  'article_facts_accounted': 93, 'three_holds_unchanged': True,
                  'article_diagnostics_not_gold_revisions': True, 'backend_promotion': False}
    write(destination/'acceptance.json', acceptance)
    freeze = {'schema': 'lanes-location-freeze-v44', 'image': IMAGE, 'attempts': 1, 'raw_records': 788,
              'methods': list(METHODS), 'implementation': {n: sha(ROOT/n) for n in CODE},
              'inputs': [bound(p) for p in sorted(set(inputs))],
              'package_files': {n: sha(destination/n) for n in ('request.json', 'new-fixtures.json', 'preservation.json', 'acceptance.json')},
              'no_post_result_tuning': True, 'neural_inference': False, 'backend_promotion': False}
    write(destination/'freeze.json', freeze)
    return {'status': 'frozen', 'raw_records': 788, 'freeze_sha256': sha(destination/'freeze.json')}


def check(package: Path) -> dict:
    freeze = read(package/'freeze.json')
    assert freeze['schema'] == 'lanes-location-freeze-v44' and freeze['image'] == IMAGE and freeze['attempts'] == 1
    for n, h in freeze['implementation'].items(): assert sha(ROOT/n) == h, n
    for b in freeze['inputs']: assert sha(ROOT/b['path']) == b['sha256'], b['path']
    for n, h in freeze['package_files'].items(): assert sha(package/n) == h, n
    preserved()
    return freeze


def execute(package: Path, destination: Path, docker: str) -> dict:
    check(package)
    assert not destination.exists() and destination.parent.resolve() == ART.resolve()
    write(ART/('location-v44-'+sha(package/'freeze.json')+'.claim.json'), {'destination': destination.name, 'attempts': 1})
    destination.mkdir(); raw = destination/'input'; raw.mkdir(); output = destination/'worker-output'; output.mkdir()
    write(raw/'request.json', read(package/'request.json'))
    name = 'lanes-location-v44-'+sha(package/'freeze.json')[:16]
    mounts = {'/input': (raw, True), '/output': (output, False), **{'/code/'+n: (ROOT/p, True) for n, p in WORKER.items()}}
    args = [docker, 'create', '--name', name, '--network', 'none', '--cpus', '2', '--memory', '4g', '--memory-swap', '4g',
            '--pids-limit', '128', '--read-only', '--restart=no', '--cap-drop=ALL', '--security-opt=no-new-privileges',
            '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m', '--entrypoint', 'python', '--pull=never']
    for target, (source, readonly) in mounts.items():
        assert ',' not in str(source)
        args += ['--mount', f'type=bind,source={source.resolve()},target={target}'+(',readonly' if readonly else '')]
    args += ['--env', 'PYTHONDONTWRITEBYTECODE=1', IMAGE, '-I', '-B', '/code/location_repair_worker_v44.py', sha(raw/'request.json')]
    created = False
    try:
        assert command([docker, 'image', 'inspect', IMAGE], destination/'image.json')['returncode'] == 0
        assert command(args, destination/'create.json')['returncode'] == 0; created = True
        assert command([docker, 'inspect', name], destination/'container.json')['returncode'] == 0
        state = json.loads(read(destination/'container.json')['stdout'])[0]; host = state['HostConfig']
        assert state['Config']['Image'] == IMAGE and host['NetworkMode'] == 'none' and host['ReadonlyRootfs']
        assert host['Memory'] == host['MemorySwap'] == 4294967296 and host['NanoCpus'] == 2000000000
        assert host['PidsLimit'] == 128 and host['CapDrop'] == ['ALL'] and 'no-new-privileges' in host['SecurityOpt']
        actual = {m['Destination']: m for m in state['Mounts']}; assert set(actual) == set(mounts)
        for target, (source, readonly) in mounts.items():
            assert actual[target]['RW'] is not readonly and Path(actual[target]['Source']).resolve() == source.resolve()
        assert command([docker, 'start', '--attach', name], destination/'run.json', 300)['returncode'] == 0
        assert command([docker, 'inspect', name], destination/'completed-state.json')['returncode'] == 0
        state = json.loads(read(destination/'completed-state.json')['stdout'])[0]['State']
        assert not state['Running'] and state['Pid'] == 0 and state['ExitCode'] == 0 and not state['OOMKilled']
        status = read(output/'status.json'); assert status['status'] == 'completed' and status['raw_records'] == 788
        check(package)
        write(destination/'output-manifest.json', {'files': [bound(p) for p in sorted(output.iterdir()) if p.is_file()]})
        return {'status': 'completed', 'raw_records': 788, 'neural_inference': False, 'backend_promotion': False}
    except BaseException as exc:
        if created: command([docker, 'kill', name], destination/'failed-stop.json')
        write(destination/'failure.json', {'error_type': type(exc).__name__, 'retry_allowed': False})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'check', 'execute', 'score'))
    parser.add_argument('--package', type=Path, required=True); parser.add_argument('--output', type=Path)
    parser.add_argument('--execution', type=Path); parser.add_argument('--test-receipt', type=Path)
    parser.add_argument('--docker', default='C:/Program Files/Docker/Docker/resources/bin/docker.exe')
    a = parser.parse_args()
    if a.action == 'prepare': result = prepare(a.package.resolve(), a.test_receipt.resolve())
    elif a.action == 'execute': result = execute(a.package.resolve(), a.output.resolve(), a.docker)
    elif a.action == 'score':
        from .location_repair_scoring_v44 import score
        result = score(a.package.resolve(), a.execution.resolve(), a.output.resolve())
    else: check(a.package.resolve()); result = {'status': 'verified'}
    print(json.dumps(result))
