"""Owned, disposable PostGIS verification; never uses configured application storage."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
from uuid import uuid4
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend'
ART = BACKEND / 'training/flood_ner/artifacts'
DOCKER = 'C:/Program Files/Docker/Docker/resources/bin/docker.exe'
IMAGE = 'sha256:3f4a5d48e0be9580ed70ed618cd039ce57bbb2dd113053d3836e28513f1f87cd'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, value: object) -> None:
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')


def docker(*args: str) -> bytes:
    result = subprocess.run([DOCKER, *args], capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError('owned_docker_operation_failed')
    return result.stdout


def assert_owner(state: dict) -> dict:
    current = json.loads(docker('inspect', state['container']))[0]
    assert current['Id'] == state['container_id']
    assert current['Config']['Labels']['lanes.schema-test.owner'] == state['owner']
    assert current['Image'] == IMAGE
    return current


def prepare(output: Path) -> dict:
    assert output.parent == ART.resolve() and not output.exists()
    image = json.loads(docker('image', 'inspect', IMAGE))[0]
    assert image['Os'] == 'linux' and image['Architecture'] == 'amd64' and image['Id'] == IMAGE
    output.mkdir()
    owner = uuid4().hex
    password = secrets.token_urlsafe(32)
    env_file = output / 'postgres.env'
    env_file.write_text('POSTGRES_PASSWORD=' + password + '\n', encoding='utf-8')
    container = 'lanes-ner-schema-' + owner[:12]
    identity = docker('create', '--name', container, '--label', 'lanes.schema-test.owner=' + owner,
        '--publish', '127.0.0.1::5432', '--cpus', '1', '--memory', '1g', '--memory-swap', '1g',
        '--tmpfs', '/var/lib/postgresql/data:rw,size=536870912', '--env-file', str(env_file), IMAGE).decode().strip()
    docker('start', identity)
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        probe = subprocess.run([DOCKER, 'exec', identity, 'pg_isready', '-U', 'postgres'], capture_output=True, timeout=5)
        if probe.returncode == 0:
            break
        time.sleep(.25)
    else:
        raise RuntimeError('owned_postgis_not_ready')
    current = json.loads(docker('inspect', identity))[0]
    ports = current['NetworkSettings']['Ports']['5432/tcp']
    assert len(ports) == 1 and ports[0]['HostIp'] == '127.0.0.1'
    port = int(ports[0]['HostPort'])
    state = {'owner': owner, 'container': container, 'container_id': identity, 'port': port, 'password': password,
             'image': IMAGE, 'prefix': 'lanes_ner_mode_test_' + owner[:12]}
    write(output / 'private-state.json', state)
    before = {}
    for name in ('backend/app/models/news.py', 'backend/tests/test_news_publication_storage.py'):
        path = ROOT / name
        before[name] = sha(path)
        snapshot = output / 'snapshot' / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, snapshot)
    qualified = ART / 'rss-ner-runtime-phase-b-3g-20261020-v1'
    frozen = read(qualified / 'freeze.json')
    for name, expected in frozen['bindings'].items():
        if name == 'backend/app/models/news.py' and sha(ROOT / name) != expected:
            original = ART / 'rss-ner-runtime-phase-b-20261020-v5/snapshot' / name
            assert sha(original) == expected
            previous_model = original.read_text(encoding='utf-8')
            assert (ROOT / name).read_text(encoding='utf-8') == previous_model.replace(
                'CheckConstraint("mode = \'rules_only\'", name="rules_only_mode")',
                'CheckConstraint("mode IN (\'rules_only\', \'ner_rules_v1\')", name="rules_only_mode")')
        else:
            assert sha(ROOT / name) == expected, name
    for name, expected in read(qualified / 'final-package-manifest.json')['files'].items():
        assert sha(qualified / name) == expected, name
    write(output / 'preservation-before.json', {'current_source': before,
        'qualification_freeze_sha256': sha(qualified / 'freeze.json'),
        'qualification_manifest_sha256': sha(qualified / 'final-package-manifest.json'),
        'qualification_audit_sha256': sha(qualified / 'independent-audit.json')})
    return {'status': 'prepared', 'owned_container': container, 'loopback_only': True, 'image': IMAGE}


def environment(state: dict, output: Path) -> dict:
    # Do not inherit provider credentials, dotenv settings or shared DB URLs.
    env = {key: os.environ[key] for key in ('PATH', 'SystemRoot', 'WINDIR', 'TEMP', 'TMP', 'COMSPEC') if key in os.environ}
    base = f"postgresql+psycopg://postgres:{state['password']}@127.0.0.1:{state['port']}/"
    env.update(PYTHONPATH=str(BACKEND), PYTHONDONTWRITEBYTECODE='1', ENVIRONMENT='test',
               DATABASE_URL=base + state['prefix'] + '_base', LANES_NEWS_AUDITOR_BATCH_SIZE='8',
               LANES_NER_MODE_TEST_DATABASE_URL=base + state['prefix'] + '_base',
               TEST_NEWS_PUBLICATION_DATABASE_URL=base + 'lanes_publication_test_' + state['owner'][:12],
               LANES_NEWS_TEST_DATABASE_URL=base + 'lanes_p3_verify_' + state['owner'][:12],
               LANES_NER_MODE_TEST_RECEIPTS=str(output))
    return env


def test(output: Path) -> dict:
    state = read(output / 'private-state.json')
    assert_owner(state)
    try:
        return run_checks(output, state)
    finally:
        current = assert_owner(state)
        write(output / 'private-container-before-stop.json', current)
        docker('stop', '--time', '5', state['container_id'])
        write(output / 'private-container-stopped.json', assert_owner(state))


def run_checks(output: Path, state: dict) -> dict:
    env = environment(state, output)
    for name in (state['prefix'] + '_base', 'lanes_publication_test_' + state['owner'][:12], 'lanes_p3_verify_' + state['owner'][:12]):
        assert name.replace('_', '').isalnum()
        docker('exec', state['container_id'], 'createdb', '-U', 'postgres', name)
    # The existing queue suite expects a fully migrated dedicated DB.
    setup = "from app.core.config import settings;import os;settings.DATABASE_URL=os.environ['LANES_NEWS_TEST_DATABASE_URL'];from alembic.config import Config;from alembic import command;c=Config(r'" + str(BACKEND / 'alembic.ini') + "');command.upgrade(c,'head')"
    with (output / 'queue-upgrade-stdout.bin').open('xb') as out, (output / 'queue-upgrade-stderr.bin').open('xb') as err:
        result = subprocess.run([sys.executable, '-B', '-c', setup], cwd=output, env=env, stdout=out, stderr=err, timeout=90)
    assert result.returncode == 0, 'queue_upgrade_failed'
    args = [sys.executable, '-B', '-m', 'pytest', '--noconftest', '-p', 'no:cacheprovider', '-q',
            '--junitxml=' + str(output / 'tests.xml'), str(BACKEND / 'tests/test_news_ner_mode_schema.py'),
            str(BACKEND / 'tests/test_news_publication_storage.py'), str(BACKEND / 'tests/test_news_processing_postgres.py')]
    with (output / 'tests-stdout.bin').open('xb') as out, (output / 'tests-stderr.bin').open('xb') as err:
        result = subprocess.run(args, cwd=output, env=env, stdout=out, stderr=err, timeout=240)
    write(output / 'test-exit.json', {'returncode': result.returncode})
    return {'status': 'tests_passed' if result.returncode == 0 else 'tests_failed', 'returncode': result.returncode}


def verify(output: Path) -> dict:
    """Audit stored tests, owned resource state and authorized source delta; no SQL."""
    state = read(output / 'private-state.json')
    current = assert_owner(state)
    assert not current['State']['Running'] and current['State']['Pid'] == 0
    assert current['HostConfig']['PortBindings']['5432/tcp'][0]['HostIp'] == '127.0.0.1'
    assert read(output / 'test-exit.json')['returncode'] == read(output / 'runner-test-exit.json')['returncode'] == 0
    cases = []
    for name in ('tests.xml', 'runner-tests.xml'):
        cases.extend(ET.parse(output / name).getroot().iter('testcase'))
    assert len(cases) == 66 and all(not list(case) for case in cases)
    counts = dict(Counter(case.attrib['classname'] for case in cases))
    assert sorted(counts.values()) == [2, 4, 23, 37]
    before = read(output / 'preservation-before.json')
    model_name = 'backend/app/models/news.py'
    old_model = output / 'snapshot' / model_name
    assert sha(old_model) == before['current_source'][model_name]
    assert (ROOT / model_name).read_text(encoding='utf-8') == old_model.read_text(encoding='utf-8').replace(
        'CheckConstraint("mode = \'rules_only\'", name="rules_only_mode")',
        'CheckConstraint("mode IN (\'rules_only\', \'ner_rules_v1\')", name="rules_only_mode")')
    name = 'backend/tests/test_news_publication_storage.py'
    old_test = output / 'snapshot' / name
    assert sha(old_test) == before['current_source'][name]
    expected_test = old_test.read_text(encoding='utf-8').replace(
        'def test_publication_migration_extends_one_head_and_registers_relationships()',
        'def test_publication_migration_remains_in_single_chain_and_registers_relationships()').replace(
        '    assert scripts.get_heads() == [REVISION]',
        '    assert len(scripts.get_heads()) == 1\n    assert REVISION in {step.revision for step in scripts.walk_revisions()}').replace(
        'assert connection.scalar(text("SELECT version_num FROM alembic_version")) == REVISION',
        'assert connection.scalar(text("SELECT version_num FROM alembic_version")) == ScriptDirectory.from_config(config).get_current_head()')
    assert (ROOT / name).read_text(encoding='utf-8') == expected_test
    qualified = ART / 'rss-ner-runtime-phase-b-3g-20261020-v1'
    assert sha(qualified / 'freeze.json') == before['qualification_freeze_sha256']
    assert sha(qualified / 'final-package-manifest.json') == before['qualification_manifest_sha256']
    assert sha(qualified / 'independent-audit.json') == before['qualification_audit_sha256']
    frozen = read(qualified / 'freeze.json')
    differences = [name for name, expected in frozen['bindings'].items() if sha(ROOT / name) != expected]
    assert differences == [model_name]
    for filename, expected in read(qualified / 'final-package-manifest.json')['files'].items():
        assert sha(qualified / filename) == expected, filename
    assert subprocess.run(['git', 'diff', '--quiet', '--', 'backend/alembic'], cwd=ROOT).returncode == 0
    revisions = {}
    for path in (BACKEND / 'alembic/versions').glob('*.py'):
        values = {}
        for node in ast.parse(path.read_text(encoding='utf-8-sig')).body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                for target in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                    if isinstance(target, ast.Name) and target.id in ('revision', 'down_revision'):
                        values[target.id] = ast.literal_eval(node.value)
        if 'revision' in values:
            revisions[values['revision']] = values.get('down_revision')
    parents = {parent for value in revisions.values() for parent in (value if isinstance(value, (tuple, list)) else [value])}
    assert set(revisions) - parents == {'e8a6f1c2d903'} and revisions['e8a6f1c2d903'] == 'd7e4b9a21c60'
    measurements = read(output / 'migration-measurements.json')
    assert len(measurements) == 34
    assert [(m['action'], m['target'], m['success']) for m in measurements[:6]] == [
        ('upgrade', 'head', True), ('upgrade', 'head', True), ('upgrade', 'd7e4b9a21c60', True),
        ('upgrade', 'head', True), ('downgrade', 'd7e4b9a21c60', True), ('upgrade', 'head', True)]
    result = {'status': 'passed_local_schema_verification', 'tests_passed': len(cases), 'test_groups': counts,
              'head': 'e8a6f1c2d903', 'predecessor': 'd7e4b9a21c60', 'migration_count': len(revisions),
              'postgres_image': IMAGE, 'loopback_owned_container_stopped': True,
              'fresh_upgrade_seconds': measurements[0]['seconds'], 'mode_step_upgrade_seconds': measurements[3]['seconds'],
              'mode_step_downgrade_seconds': measurements[4]['seconds'], 'mode_step_reupgrade_seconds': measurements[5]['seconds'],
              'contended_guard_total_seconds': measurements[-1]['seconds'],
              'mode_check_name_preserved': True, 'legacy_rows_links_and_other_schema_preserved': True,
              'native_rows_and_drift_block_downgrade': True, 'generated_sql_executed': True, 'lock_contention_verified': True,
              'authorized_qualification_source_deltas': differences, 'other_qualification_bindings_preserved': len(frozen['bindings']) - 1,
              'qualification_receipts_and_assets_preserved': True, 'neural_inference_runs': 0,
              'application_writers_changed': False, 'public_apis_changed': False, 'shared_or_cloud_database_changed': False,
              'source_hashes': {name: sha(ROOT / name) for name in (model_name,
                'backend/alembic/versions/e8a6f1c2d903_allow_ner_news_extraction_mode.py',
                'backend/tests/test_news_ner_mode_schema.py', 'backend/tests/test_news_publication_storage.py',
                'backend/tests/test_news_ner_mode_schema_runner.py', 'backend/scripts/verify_news_ner_mode_schema.py')}}
    write(output / 'independent-verification.json', result)
    write(output / 'final-package-manifest.json', {'files': {p.relative_to(output).as_posix(): sha(p)
          for p in output.rglob('*') if p.is_file()}})
    return {key: value for key, value in result.items() if key != 'source_hashes'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'test', 'verify'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.parent == ART.resolve()
    result = {'prepare': prepare, 'test': test, 'verify': verify}[args.operation](output)
    print(json.dumps(result))
    sys.exit(result.get('returncode', 0))
