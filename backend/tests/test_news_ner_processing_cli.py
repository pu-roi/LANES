"""Thin entrypoint errors only; never open SQL or start inference."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy.engine import URL

from app.services.news_ner_durable.contracts import NerEvidenceError
from scripts import run_news_ner_processing as cli


@pytest.mark.parametrize('failure,code,status',[
    (KeyboardInterrupt(),'ner_runtime_cancelled',130),
    (asyncio.CancelledError(),'ner_runtime_cancelled',130),
    (NerEvidenceError('ner_assets_unavailable'),'ner_assets_unavailable',1),
    (RuntimeError('private diagnostic must not escape'),'ner_runtime_failed',1)])
def test_cli_bounded_failure_and_interrupt(monkeypatch,capsys,failure,code,status):
    import sqlalchemy
    closed=[]
    class Engine:
        def dispose(self):closed.append(True)
    monkeypatch.setattr(sqlalchemy,'create_engine',lambda *a,**kw:Engine())
    monkeypatch.setattr(cli.platform,'system',lambda:'Linux')
    monkeypatch.setenv('ENVIRONMENT','test')
    monkeypatch.setenv('DATABASE_URL',URL.create('postgresql+psycopg',database='lanes_p3_verify_cli').render_as_string(hide_password=False))
    monkeypatch.setattr('sys.argv',['worker','--bundle','unused','--bundle-sha256','0'*64,'--worker-code-sha256','0'*64])
    def interrupted(coroutine):coroutine.close();raise failure
    monkeypatch.setattr(cli.asyncio,'run',interrupted)
    assert cli.main()==status and closed==[True]
    output=capsys.readouterr();assert json.loads(output.out)=={'error_code':code} and output.err==''


@pytest.mark.parametrize('environment,platform',[('production','Linux'),('test','Windows')])
def test_cli_refuses_before_engine_creation(monkeypatch,capsys,environment,platform):
    import sqlalchemy
    def forbidden(*args,**kwargs):pytest.fail('guard attempted engine creation')
    monkeypatch.setattr(sqlalchemy,'create_engine',forbidden)
    monkeypatch.setattr(cli.platform,'system',lambda:platform)
    monkeypatch.setenv('ENVIRONMENT',environment)
    monkeypatch.setenv('DATABASE_URL',URL.create('postgresql+psycopg',database='lanes_p3_verify_cli').render_as_string(hide_password=False))
    monkeypatch.setattr('sys.argv',['worker','--bundle','unused','--bundle-sha256','0'*64,'--worker-code-sha256','0'*64])
    assert cli.main()==1
    assert json.loads(capsys.readouterr().out)=={'error_code':'ner_configuration_invalid'}


def test_malformed_database_url_is_configuration_failure(monkeypatch,capsys):
    monkeypatch.setenv('ENVIRONMENT','test');monkeypatch.setenv('DATABASE_URL','not-a-database-url')
    monkeypatch.setattr('sys.argv',['worker','--bundle','unused','--bundle-sha256','0'*64,'--worker-code-sha256','0'*64])
    assert cli.main()==1
    assert json.loads(capsys.readouterr().out)=={'error_code':'ner_configuration_invalid'}


# Each child starts before application settings/modules are cached. Its cwd has
# no .env, and it inherits no application settings or credentials from pytest.
BOOTSTRAP_PROBE = r'''
import asyncio
import builtins
import runpy
import sys

backend, failure, target, *arguments = sys.argv[1:]
sys.path.insert(0, backend)
assert not any(name == 'app' or name.startswith('app.') for name in sys.modules)
import sqlalchemy

forbidden = []
def deny(action):
    forbidden.append(action)
    raise RuntimeError('forbidden startup side effect')
sqlalchemy.engine.Engine.connect = lambda *a, **kw: deny('database connection')
def audit(event, args):
    if event in ('socket.connect', 'subprocess.Popen', 'os.system', 'os.posix_spawn'):
        deny(event)
sys.addaudithook(audit)

original_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    if name == target:
        if failure == 'import':
            raise ImportError('private-bootstrap-sentinel /private/path credential-sentinel')
        if failure == 'interrupt':
            raise KeyboardInterrupt('private-bootstrap-sentinel')
        if failure == 'cancel':
            raise asyncio.CancelledError('private-bootstrap-sentinel')
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded_import
sys.argv = ['worker', *arguments]
try:
    runpy.run_module('scripts.run_news_ner_processing', run_name='__main__')
finally:
    assert not forbidden, 'startup attempted forbidden work'
'''


def run_fresh_cli(tmp_path, failure: str, target: str, arguments: list[str]):
    # SystemRoot is needed by Windows; everything application-specific is explicit.
    environment = {key: os.environ[key] for key in ('SystemRoot', 'WINDIR') if key in os.environ}
    environment.update(ENVIRONMENT='test', DATABASE_URL=URL.create(
        'postgresql+psycopg', database='lanes_p3_verify_cli_bootstrap').render_as_string(hide_password=False))
    if failure == 'settings':
        environment['NEWS_NER_PREVIEW_ENABLED'] = 'private-bootstrap-sentinel'
    return subprocess.run(
        [sys.executable, '-I', '-B', '-c', BOOTSTRAP_PROBE,
         str(Path(__file__).resolve().parents[1]), failure, target, *arguments],
        cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30,
    )


@pytest.mark.parametrize('failure,target,code,status', [
    ('settings', '', 'ner_configuration_invalid', 1),
    ('import', 'pydantic', 'ner_runtime_failed', 1),
    ('import', 'app.services.news_ner_durable.processing', 'ner_runtime_failed', 1),
    ('import', 'app.services.news_ner_durable.assets', 'ner_runtime_failed', 1),
    ('import', 'app.services.news_ner_durable.contracts', 'ner_runtime_failed', 1),
    ('interrupt', 'app.services.news_ner_durable.processing', 'ner_runtime_cancelled', 130),
    ('cancel', 'app.services.news_ner_durable.contracts', 'ner_runtime_cancelled', 130),
])
def test_fresh_cli_bootstrap_is_bounded(tmp_path, failure, target, code, status):
    result = run_fresh_cli(tmp_path, failure, target, [
        '--bundle', 'unused', '--bundle-sha256', '0' * 64,
        '--worker-code-sha256', '0' * 64,
    ])
    assert result.returncode == status
    assert result.stdout.splitlines() == [json.dumps({'error_code': code})]
    assert result.stderr == ''


@pytest.mark.parametrize('arguments,status', [(['--help'], 0), ([], 2)])
def test_fresh_cli_preserves_argument_handling(tmp_path, arguments, status):
    # Application imports are deliberately broken: argparse must finish first.
    result = run_fresh_cli(tmp_path, 'import', 'app.services.news_ner_durable.processing', arguments)
    assert result.returncode == status
    assert 'usage:' in result.stdout + result.stderr
    assert 'Traceback' not in result.stderr
    assert 'error_code' not in result.stdout + result.stderr
