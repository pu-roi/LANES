"""Constructed grants and mocked execution; no private content or model loading."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner import shadow_comparison as c
from training.flood_ner import shadow_worker as w


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')
    return {'path': path.as_posix(), 'sha256': c.digest(path)}


@pytest.fixture
def frozen(tmp_path, monkeypatch):
    root = tmp_path
    for name in (*c.CODE, *c.TESTS, 'backend/requirements.txt', *('backend/' + n for n in c.RULE_ASSETS),
                 'backend/app/services/taglish_extraction_service.py'):
        p = root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('fixture', encoding='utf-8')
    def bound(name, value):
        b = write(root / name, value); b['path'] = name; return b
    rows = [{'article_id': f'fictional-{i}', 'kind': 'training_article', 'text': f'Fictional source {i}.',
             'text_sha256': c.service.text_hash(f'Fictional source {i}.')} for i in range(6)]
    prior = bound('prior.json', {'candidates': [{'source_sha256': r['text_sha256'], 'text': r['text']} for r in rows]})
    reviews = {'predecessor': prior, 'reviews': [{'source_sha256': r['text_sha256'], 'supported': True,
                'purpose': 'private_offline_location_comparison', 'start': 0, 'end': len(r['text']),
                'no_policy_expansion': True} for r in rows]}
    implementation = {n: c.digest(root / n) for n in c.CODE}; tests = {n: c.digest(root / n) for n in c.TESTS}
    raw_receipt = bound('raw-tests.json', {'returncode': 0, 'output_complete': True, 'args': list(c.TESTS)})
    image = 'sha256:' + 'a' * 64
    grant = {'schema': c.SCHEMA, 'implementation': implementation, 'tests': tests,
        'test_receipt': bound('test.json', {'returncode': 0, 'implementation': implementation, 'tests': tests, 'raw_receipt': raw_receipt}),
        'image_id': image, 'qualification': bound('qual.json', {'gate_3_cleared': True, 'image_id': image,
             'compatibility': 'passed', 'performance': 'passed', 'failure_handling': 'passed'}),
        'model_manifest': bound('model.json', {}), 'resource_manifest': bound('resource.json', {}),
        'resource_dir': 'resources', 'workload': bound('workload.json', {'rows': rows}),
        'use_reviews': bound('reviews.json', reviews), 'rules_files': {
            n: c.digest(root / 'backend' / n) for n in
            ({p.relative_to(root / 'backend').as_posix() for p in (root / 'backend/app').rglob('*.py')} | set(c.RULE_ASSETS))},
        'requirements_sha256': c.digest(root / 'backend/requirements.txt')}
    monkeypatch.setattr(c, 'authenticate', lambda *a: {'tokenizer_sha256': 'b' * 64, 'model': root / 'resources'})
    path = root / 'grant.json'; write(path, grant)
    return root, path, grant, rows


def test_preflight_is_read_only(frozen, monkeypatch):
    root, path, grant, rows = frozen
    before = sorted(p.relative_to(root).as_posix() for p in root.rglob('*'))
    monkeypatch.setattr(c.q, 'command', lambda *a: pytest.fail('network/process dispatch'))
    assert c.preflight(root, path, c.digest(path))[1] == rows
    assert before == sorted(p.relative_to(root).as_posix() for p in root.rglob('*'))


@pytest.mark.parametrize('damage', ['stale_grant', 'code', 'tests', 'test_failure', 'test_stale', 'qualification',
                                   'image', 'requirements', 'rules', 'model', 'source_use', 'text', 'references', 'duplicate'])
def test_preflight_rejects_missing_stale_and_unauthorized_inputs(frozen, damage):
    root, path, grant, rows = frozen; sha = c.digest(path)
    if damage == 'stale_grant': sha = 'f' * 64
    elif damage in ('code', 'tests'):
        (root / next(iter(grant['implementation' if damage == 'code' else 'tests']))).write_text('changed')
    elif damage == 'test_failure' or damage == 'test_stale':
        p = root / grant['test_receipt']['path']; v = json.loads(p.read_text())
        if damage == 'test_failure': v['returncode'] = 1
        else: v['implementation'] = {}
        write(p, v); grant['test_receipt']['sha256'] = c.digest(p)
    elif damage == 'qualification':
        p = root / grant['qualification']['path']; v = json.loads(p.read_text()); v['gate_3_cleared'] = False
        write(p, v); grant['qualification']['sha256'] = c.digest(p)
    elif damage == 'image': grant['image_id'] = 'mutable:latest'
    elif damage == 'requirements': (root / 'backend/requirements.txt').write_text('changed')
    elif damage == 'rules': grant['rules_files'] = {}
    elif damage == 'model': (root / 'model.json').write_text('changed')
    elif damage == 'source_use':
        p = root / grant['use_reviews']['path']; v = json.loads(p.read_text()); v['reviews'][0]['supported'] = False
        write(p, v); grant['use_reviews']['sha256'] = c.digest(p)
    else:
        if damage == 'text': rows[0]['text'] = 'changed'
        if damage == 'references': rows[0]['annotations'] = []
        if damage == 'duplicate': rows[1]['article_id'] = rows[0]['article_id']
        p = root / 'workload.json'; write(p, {'rows': rows}); grant['workload']['sha256'] = c.digest(p)
    if damage != 'stale_grant': write(path, grant); sha = c.digest(path)
    with pytest.raises((ValueError, FileNotFoundError)):
        c.preflight(root, path, sha)


def test_container_contract_has_no_credentials_fallback_or_writable_inputs(tmp_path):
    mounts = {target: (tmp_path, target != '/output') for target in
              {'/assets/MANIFEST.json', '/assets/models/control-seed-0/model', '/assets/resource.json',
               '/assets/base', '/input', '/output', '/app/app/services/ner_shadow_service.py',
               *('/code/' + n[len('backend/'):] for n in c.CODE if not n.startswith('backend/app/'))}}
    args = c.container_args('docker', 'sha256:' + 'a' * 64, 'lanes-ner-shadow-' + 'b' * 16, mounts, 'c' * 64)
    assert args[args.index('--network') + 1] == 'none'
    assert args[args.index('--memory') + 1] == '4g'
    assert '--restart=no' in args and '--read-only' in args
    assert args[-5] == '/code/training/flood_ner/shadow_worker.py'
    assert not any('PASSWORD' in a or 'DATABASE' in a or 'API_KEY' in a for a in args)
    mounts['/references'] = (tmp_path, True)
    with pytest.raises(ValueError): c.container_args('docker', 'sha256:' + 'a' * 64, 'lanes-ner-shadow-' + 'b' * 16, mounts, 'c' * 64)


def test_aggregate_is_derived_and_has_no_individual_content():
    text = 'Sample City'; row = {'article_id': 'fictional-1', 'text': text,
           'text_sha256': c.service.text_hash(text), 'kind': 'fictional'}
    provenance = dict(model='a'*64, tokenizer='b'*64, rules='c'*64)
    result = c.service.compare_article({k:v for k,v in row.items() if k!='kind'}, lambda _: [],
                    provenance=provenance, splitter=lambda t: [], finder=lambda *_: [])
    aggregate = c.aggregate([row], [result], provenance)
    assert aggregate['fictional_cases'] == 1 and aggregate['exact_pairs'] == 0
    assert all(type(v) is int for v in aggregate.values())
    assert 'Sample City' not in json.dumps(aggregate) and 'fictional-1' not in json.dumps(aggregate)
    result['comparison']['exact_pairs'] = [[0, 0]]
    with pytest.raises(ValueError): c.aggregate([row], [result], provenance)


def test_occupied_destination_rejected_before_dispatch(frozen, monkeypatch):
    root, path, grant, rows = frozen
    monkeypatch.setattr(c.q, 'command', lambda *a: pytest.fail('dispatch'))
    with pytest.raises(ValueError): c.execute(root, 'docker', path, c.digest(path), root)


def test_exclusive_and_interrupted_receipts_are_not_reused(tmp_path):
    lock = tmp_path / 'lock'
    with pytest.raises(RuntimeError):
        with c.q.exclusive(lock):
            with pytest.raises(FileExistsError):
                with c.q.exclusive(lock): pass
            raise RuntimeError('interrupted owner')
    assert lock.exists()
    with pytest.raises(FileExistsError):
        with c.q.exclusive(lock): pass


def test_worker_rejects_stale_request_before_inference(tmp_path):
    p = tmp_path / 'request.json'; write(p, {'schema': 'not-allowed'})
    with pytest.raises(ValueError): w.checked_request(p, '0'*64)
    with pytest.raises(ValueError): w.checked_request(p, c.digest(p))


def test_worker_is_cpu_only_and_explicitly_blocks_training_and_io():
    source = Path(w.__file__).read_text(encoding='utf-8')
    for guard in ('spacy.require_cpu()', 'Language.initialize = Language.update',
                  'socket.socket.connect', 'sqlalchemy.create_engine', "'OfflineEngine'", 'install_guards()'):
        assert guard in source
    assert 'resume_training = blocked' in source


def test_offline_rules_import_uses_inert_engine_and_blocks_connections_and_network(tmp_path):
    import subprocess
    backend = Path(__file__).resolve().parents[1]
    script = '''import sys,json,socket
sys.path.insert(0,sys.argv[1])
from training.flood_ner.corrected_rules_worker import install_guards
install_guards()
from app.services.taglish_extraction_service import find_place_mentions
from app.core.database import engine
assert type(engine).__name__ == 'OfflineEngine'
assert isinstance(find_place_mentions('Baha sa Sample Road.',0),list)
for operation in (engine.connect,engine.raw_connection,lambda: socket.getaddrinfo('example.invalid',443)):
 try: operation()
 except RuntimeError: pass
 else: raise AssertionError('I/O guard did not reject access')
assert not any(n in sys.modules for n in ['psycopg','psycopg2','asyncpg'])
print(json.dumps({'fictional_rules_probe':'passed','connections_blocked':True}))
'''
    result = subprocess.run([sys.executable, '-I', '-B', '-c', script, str(backend)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['connections_blocked'] is True


def test_private_failure_trace_is_preserved_without_public_exception_content():
    source = Path(w.__file__).read_text(encoding='utf-8')
    assert "'private-failure-traceback.txt').open('x'" in source
    assert "'error_type': type(exc).__name__" in source


@pytest.mark.parametrize('failure', ['unavailable_image', 'command_timeout', 'interrupted'])
def test_failed_execution_preserves_claim_and_failure_without_retry(frozen, monkeypatch, failure):
    root, path, grant, rows = frozen
    code = root / 'backend/training/flood_ner/shadow_comparison.py'
    monkeypatch.setattr(c, '__file__', str(code))
    artifacts = code.parent / 'artifacts'; artifacts.mkdir()
    output = artifacts / 'fictional-new-attempt'; calls = []
    def command(*args):
        calls.append(args)
        if failure == 'interrupted': raise KeyboardInterrupt()
        if failure == 'command_timeout': raise TimeoutError()
        return {'returncode': 1}
    monkeypatch.setattr(c.q, 'command', command)
    with pytest.raises((ValueError, TimeoutError, KeyboardInterrupt)):
        c.execute(root, 'docker', path, c.digest(path), output)
    assert len(calls) == 1 and (output / 'failure.json').exists()
    assert (artifacts / 'shadow-active.lock').exists()
    assert (artifacts / 'shadow-claims' / (c.digest(path) + '.json')).exists()
    with pytest.raises(FileExistsError):
        c.execute(root, 'docker', path, c.digest(path), artifacts / 'different-attempt')
    assert len(calls) == 1


@pytest.mark.parametrize('damage', ['incomplete', 'missing', 'tests_not_run'])
def test_incomplete_test_evidence_blocks_dispatch(frozen, damage):
    root, path, grant, rows = frozen
    raw = root / 'raw-tests.json'; value = json.loads(raw.read_text())
    if damage == 'incomplete': value['output_complete'] = False
    elif damage == 'tests_not_run': value['args'] = ['unrelated.py']
    if damage == 'missing': raw.unlink()
    else:
        write(raw, value)
        receipt = root / 'test.json'; v = json.loads(receipt.read_text())
        v['raw_receipt']['sha256'] = c.digest(raw); write(receipt, v)
        grant['test_receipt']['sha256'] = c.digest(receipt)
    write(path, grant)
    with pytest.raises((ValueError, FileNotFoundError)): c.preflight(root, path, c.digest(path))
