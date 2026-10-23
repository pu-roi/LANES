"""Package, execution identity and CLI boundaries; no SQL or neural execution."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy.engine import Engine, URL

from app.services import news_historical_processing as service
from app.services.news_historical_preparation import PreparationError, save_private_package
from app.services.news_ner_durable.contracts import sha
from historical_processing_fixtures import fictional_documents
from test_news_ner_durable import trusted


@pytest.fixture(autouse=True)
def no_sql_or_model(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail('Pure command tests attempted SQL or model startup')
    monkeypatch.setattr(Engine, 'connect', forbidden)
    from app.services.news_ner_runtime.supervisor import Session
    monkeypatch.setattr(Session, 'start', forbidden)


@pytest.fixture
def package(tmp_path, trusted):
    documents = fictional_documents(trusted)
    path = tmp_path/'e0'
    save_private_package(path, documents)
    return path, documents, service.load_historical_package(path/'manifest.json', sha(documents['manifest.json']))


def test_exact_e0_package_and_session_reconstructed_without_rewriting(package):
    path, documents, loaded = package
    times = {p.name: p.stat().st_mtime_ns for p in path.iterdir()}
    assert loaded.manifest == documents['manifest.json']
    assert service.load_historical_package(path/'manifest.json', loaded.manifest_sha256).documents == documents
    assert times == {p.name: p.stat().st_mtime_ns for p in path.iterdir()}
    assert len(loaded.captures) == 2


@pytest.mark.parametrize('filename', ['manifest.json', 'inventory.json', 'native-101.json', 'native-102.json', 'receipt.json'])
def test_tampered_package_member_rejected(package, filename):
    path, _, loaded = package
    changed = json.loads((path/filename).read_text(encoding='utf-8'))
    changed['tampered'] = True
    (path/filename).write_text(json.dumps(changed), encoding='utf-8')
    with pytest.raises((PreparationError, ValueError)):
        service.load_historical_package(path/'manifest.json', loaded.manifest_sha256)


def test_unknown_extra_package_file_rejected(package):
    path, _, loaded = package
    (path/'extra.json').write_text('{}')
    with pytest.raises(PreparationError, match='historical_package_set_invalid'):
        service.load_historical_package(path/'manifest.json', loaded.manifest_sha256)


def test_loaded_capture_cannot_be_changed_by_rehashing_its_mutable_receipt(package):
    _, _, loaded = package
    loaded.documents['native-101.json']['runtime_request']['text'] = 'Modified after loading'
    loaded.documents['receipt.json']['document_sha256']['native-101.json'] = sha(loaded.documents['native-101.json'])
    with pytest.raises(PreparationError, match='historical_loaded_package_changed'):
        loaded.validate()


def test_duplicate_json_keys_rejected_before_authentication(package):
    path, _, loaded = package
    (path/'receipt.json').write_text('{"schema":1,"schema":2}', encoding='utf-8')
    with pytest.raises(PreparationError, match='historical_duplicate_json_key'):
        service.load_historical_package(path/'manifest.json', loaded.manifest_sha256)


def test_native_offset_or_session_change_rejected_even_with_rehashed_receipt(package):
    path, documents, _ = package
    for member, key, value in [('native-101.json', 'runtime_request', {}),
                               ('manifest.json', 'demonstration_session_id', 'forged-session')]:
        changed = deepcopy(documents)
        changed[member][key] = value
        changed['receipt.json']['document_sha256'][member] = sha(changed[member])
        changed['receipt.json']['manifest_sha256'] = sha(changed['manifest.json'])
        for name, data in changed.items():
            (path/name).write_text(json.dumps(data), encoding='utf-8')
        with pytest.raises(PreparationError, match='historical_e0_reconstruction_failed'):
            service.load_historical_package(path/'manifest.json', sha(changed['manifest.json']))


def engine(database='lanes_p3_verify_historical', host='127.0.0.1', query=None):
    return SimpleNamespace(url=URL.create('postgresql+psycopg', host=host, database=database, query=query or {}))


@pytest.mark.parametrize('database,host,environment,query,allowed', [
    ('lanes_p3_verify_historical', '127.0.0.1', 'test', {}, True),
    ('lanes', '127.0.0.1', 'test', {}, False),
    ('lanes_p3_verify_historical', 'cloud.invalid', 'test', {}, False),
    ('lanes_p3_verify_historical', 'localhost', 'production', {}, False),
    ('lanes_p3_verify_historical', 'localhost', 'test', {'host': 'cloud.invalid'}, False)])
def test_disposable_policy_cannot_be_bypassed(database, host, environment, query, allowed):
    assert service.disposable_target(engine(database, host, query), environment) is allowed


def test_execution_manifest_records_parent_delta_and_target(package, trusted):
    _, _, loaded = package
    first, errors = service.execution_manifest(loaded, trusted, sha(trusted.manifest), engine(), 'test')
    assert not errors
    assert set(first['changed_asset_families']) == {'projection', 'source_check'}
    assert first['parent_manifest_sha256'] == loaded.manifest_sha256
    assert first['demonstration_session_id'] == loaded.manifest['demonstration_session_id']
    assert first['assets_sha256'] != loaded.manifest['assets']['manifest_sha256']
    assert len(first['operator_code_sha256']) == 3
    assert service.execution_manifest(loaded, trusted, sha(trusted.manifest), engine(), 'test')[0] == first


def test_execution_assets_pin_and_protected_families_cannot_change(package, trusted):
    _, _, loaded = package
    assert 'historical_execution_assets_mismatch' in service.execution_manifest(loaded, trusted, '0'*64, engine(), 'test')[1]
    manifest = deepcopy(trusted.manifest)
    manifest['model']['name'] = 'different-model'
    altered = SimpleNamespace(manifest=manifest, pipeline_version='ner-v1:'+sha(manifest), validate=lambda: None)
    assert 'historical_protected_assets_changed' in service.execution_manifest(loaded, altered, sha(manifest), engine(), 'test')[1]


@pytest.mark.asyncio
async def test_cloud_process_refused_before_connecting_or_inference(package, trusted):
    _, _, loaded = package
    target = engine('lanes', 'cloud.invalid')
    result = await service.process_historical(target, loaded, trusted, assets_sha256=sha(trusted.manifest),
        confirmed_database='lanes', environment='production')
    assert result['status'] == 'blocked' and result['database_writes_performed'] is False
    assert result['blockers'] == ['historical_cloud_processing_not_qualified']


def test_wrong_database_confirmation_refused_before_connect(package, trusted):
    _, _, loaded = package
    with pytest.raises(PreparationError, match='historical_database_confirmation_mismatch'):
        service.preflight_historical(engine(), loaded, trusted, assets_sha256=sha(trusted.manifest),
            confirmed_database='other', environment='test')


def test_receipts_append_and_preserve_execution_identity(package, trusted, tmp_path):
    execution, _ = service.execution_manifest(package[2], trusted, sha(trusted.manifest), engine(), 'test')
    receipt = {'status': 'ready', 'execution_manifest': execution}
    output = tmp_path/'receipts'
    service.save_attempt(output, receipt, 'first')
    identity = output/f'execution-{sha(execution)}.json'
    before = identity.stat().st_mtime_ns
    service.save_attempt(output, receipt, 'second')
    assert identity.stat().st_mtime_ns == before and len(list(output.iterdir())) == 3
    identity.write_text('{}')
    with pytest.raises(PreparationError, match='historical_execution_receipt_changed'):
        service.save_attempt(output, receipt, 'third')
    assert not (output/'attempt-third.json').exists()


@pytest.mark.parametrize('memory,cpu,expected', [('3221225472', '100000 100000', False),
    ('max', '100000 100000', True), ('3221225472', '200000 100000', True)])
def test_runtime_preflight_checks_qualified_envelope_without_startup(trusted, monkeypatch, memory, cpu, expected):
    monkeypatch.setattr(service.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(service.platform, 'machine', lambda: 'x86_64')
    monkeypatch.setattr(service.sys, 'version_info', (3, 12))
    monkeypatch.setattr(service.signal, 'ITIMER_REAL', 0, raising=False)
    monkeypatch.setattr(service.signal, 'getitimer', lambda _timer: (0, 0), raising=False)
    monkeypatch.setattr(service.importlib.metadata, 'version', lambda _name: '3.7.5')
    read = Path.read_text
    def values(path, *args, **kwargs):
        return memory if path.as_posix().endswith('/memory.max') else cpu if path.as_posix().endswith('/cpu.max') else read(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', values)
    from app.services.news_ner import bundle
    monkeypatch.setattr(bundle, 'verify_bundle', lambda path, digest: {})
    assert ('historical_resource_envelope_unqualified' in service.runtime_blockers(trusted)) is expected


@pytest.mark.parametrize('mode,status,expected_exit', [('preflight', 'ready', 0), ('process', 'completed', 0),
                                                      ('process', 'interrupted', 130)])
def test_cli_delegates_and_preserves_private_receipts(package, trusted, tmp_path, monkeypatch, capsys, mode, status, expected_exit):
    import scripts.run_news_historical_processing as cli
    import app.services.news_ner_durable.assets as assets
    import sqlalchemy
    from app.core.config import settings
    path, _, loaded = package
    receipt_dir = tmp_path/'project/data/receipts'
    monkeypatch.setattr(cli, '__file__', str(tmp_path/'project/backend/scripts/run.py'))
    monkeypatch.setattr(cli.subprocess, 'run', lambda *_args, **_kwargs: SimpleNamespace(returncode=0))
    monkeypatch.setattr(assets, 'load_trusted_assets', lambda *_args, **_kwargs: trusted)
    monkeypatch.setattr(assets, 'with_placement_assets', lambda value: value)
    target = engine(); target.dispose = lambda: None
    monkeypatch.setattr(sqlalchemy, 'create_engine', lambda *_args, **_kwargs: target)
    monkeypatch.setattr(settings, 'ENVIRONMENT', 'test')
    execution, _ = service.execution_manifest(loaded, trusted, sha(trusted.manifest), target, 'test')
    result = {'status': status, 'mode': mode, 'execution_manifest': execution, 'blockers': [], 'database_writes_performed': mode == 'process'}
    def preflight(actual_engine, actual_package, actual_assets, **kwargs):
        assert actual_engine is target and actual_package.manifest_sha256 == loaded.manifest_sha256 and actual_assets is trusted
        return result
    async def process(*args, **kwargs):
        return preflight(*args, **kwargs)
    monkeypatch.setattr(service, 'preflight_historical', preflight)
    monkeypatch.setattr(service, 'process_historical', process)
    monkeypatch.setattr(cli.sys if hasattr(cli, 'sys') else __import__('sys'), 'argv', ['historical', mode,
        '--manifest', str(path/'manifest.json'), '--manifest-sha256', loaded.manifest_sha256,
        '--confirm-database', target.url.database, '--bundle', 'fictional-bundle', '--bundle-sha256', '1'*64,
        '--worker-code-sha256', '2'*64, '--assets-sha256', sha(trusted.manifest), '--receipt-directory', str(receipt_dir)])
    assert cli.main() == expected_exit
    public = json.loads(capsys.readouterr().out)
    assert public['status'] == status and 'execution_manifest' not in public
    assert len(list(receipt_dir.glob('attempt-*.json'))) == 1
    assert len(list(receipt_dir.glob('execution-*.json'))) == 1


def test_attempt_path_escape_is_rejected_before_file_creation(tmp_path):
    with pytest.raises(PreparationError, match='historical_attempt_identity_invalid'):
        service.save_attempt(tmp_path/'receipts', {}, '../escape')
    assert not (tmp_path/'receipts').exists()


@pytest.mark.parametrize('selection', [[], (1, 1), (True,), ([1],)])
@pytest.mark.asyncio
async def test_invalid_exact_worker_selection_fails_before_sql(selection):
    from app.services.news_ner_durable.processing import process_native_saved_news
    from app.services.news_ner_durable.contracts import NerEvidenceError
    with pytest.raises(NerEvidenceError, match='ner_configuration_invalid'):
        await process_native_saved_news(lambda: pytest.fail('invalid selection opened SQL'), load_assets=lambda: None,
            environment='test', database_url='postgresql+psycopg://localhost/lanes_p3_verify_fixture', run_ids=selection)
