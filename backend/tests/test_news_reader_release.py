"""Deployment regressions: an HTTP-ready container must also read saved results."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from app.services import news_native_read_context as reader
from app.services.news_reader_release import READER_MANIFEST_SHA256, READER_SOURCE_PATH
from app.services.news_saved_run_service import SavedRunReadError
from scripts.verify_news_reader_package import verify_package
from scripts.deploy_api_checked import check_job, deploy
from scripts.check_news_reader import checked_url, get_json, check_detail


def test_packaged_manifest_preserves_existing_selection():
    result = verify_package(READER_SOURCE_PATH)
    assert result['manifest_sha256'] == READER_MANIFEST_SHA256
    assert result['provider_requests'] == result['database_writes'] == 0
    assert result['pipeline_version'] == 'ner-v1:abb4e0674b807a124328dbabc65cd71f2df9c4f8362a4280a197a1b9672482f6'


@pytest.mark.parametrize('failure', ['missing', 'hash', 'pipeline', 'fallback'])
def test_missing_or_changed_package_rejected(tmp_path, failure):
    value = json.loads(READER_SOURCE_PATH.read_text())
    path = tmp_path / 'reader.json'
    if failure == 'pipeline': value['pipeline_version'] = 'legacy-unversioned'
    if failure == 'fallback': value['fallback_pipeline_versions'] = [value['pipeline_version']]
    if failure != 'missing': path.write_text(json.dumps(value))
    pin = READER_MANIFEST_SHA256 if failure != 'hash' else '0' * 64
    if failure in {'pipeline', 'fallback'}:
        from app.services.news_ner_durable.contracts import sha
        pin = sha(value)
    with pytest.raises(SavedRunReadError): verify_package(path, pin)


def test_required_native_reader_cannot_silently_become_legacy(monkeypatch):
    monkeypatch.delenv('LANES_NEWS_NATIVE_READ_CONTEXT', raising=False)
    monkeypatch.delenv('LANES_NEWS_NATIVE_READ_CONTEXT_SHA256', raising=False)
    monkeypatch.setenv('LANES_NEWS_NATIVE_READ_REQUIRED', '1')
    with pytest.raises(RuntimeError, match='startup_failed'): reader.validate_native_reader_startup(None)
    monkeypatch.delenv('LANES_NEWS_NATIVE_READ_REQUIRED')
    reader.validate_native_reader_startup(None)


@pytest.mark.parametrize('database_failure', [True, False])
def test_startup_uses_read_only_sql_and_propagates_binding_failure(monkeypatch, database_failure):
    calls = []
    context = SimpleNamespace(validate=lambda db: (_ for _ in ()).throw(ValueError('private connection'))
                              if database_failure else calls.append('validated'))
    monkeypatch.setattr(reader, 'configured_native_read_context', lambda: context)
    class Session:
        def __init__(self, engine): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, statement): calls.append(str(statement))
    monkeypatch.setattr('sqlalchemy.orm.Session', Session)
    if database_failure:
        with pytest.raises(RuntimeError, match='^news_native_reader_startup_failed$'):
            reader.validate_native_reader_startup(None)
    else: reader.validate_native_reader_startup(None)
    assert calls[0] == 'SET TRANSACTION READ ONLY'


@pytest.mark.parametrize('url', ['http://example.run.app', 'https://example.com',
    'https://a.run.app@evil.example', 'https://a.run.app/x', 'https://a.run.app?token=x'])
def test_canary_cannot_send_staff_token_to_arbitrary_urls(url):
    with pytest.raises(ValueError): checked_url(url)


def service():
    return {'spec': {'template': {'metadata': {'annotations': {'run.googleapis.com/cloudsql-instances': 'binding'}},
        'spec': {'serviceAccountName': 'existing-api-identity', 'containers': [{'env': [
            {'name': 'DATABASE_URL', 'value': 'private-db-placeholder'},
            {'name': 'SECRET_KEY', 'value': 'private-key-placeholder'},
            {'name': 'GEMINI_API_KEY', 'value': 'must-not-copy'}]}]}}},
        'status': {'url': 'https://api.run.app', 'traffic': [{'revisionName': 'api-working', 'percent': 100}]}}


def test_probe_has_only_read_credentials_and_zero_retries():
    result = check_job(service(), name='probe', image='image', candidate='https://new.run.app', baseline='https://old.run.app')
    task = result['spec']['template']['spec']['template']['spec']
    assert task['maxRetries'] == 0
    assert task['containers'][0]['command'] == ['python']
    assert 'must-not-copy' not in json.dumps(result)
    assert task['serviceAccountName'] == 'existing-api-identity'
    assert task['containers'][0]['args'][1] == 'scripts.check_news_reader'


@pytest.mark.parametrize('failure', ['probe', 'deployment', 'concurrent', None])
def test_promotion_requires_probe_success_and_unchanged_traffic(monkeypatch, failure):
    calls = []
    original = service()
    staged = deepcopy(original)
    staged['status']['traffic'].append({'tag': 'reader-check', 'revisionName': 'api-release', 'url': 'https://new.run.app'})
    descriptions = iter([original, staged, deepcopy(staged)])
    def run(args, **kwargs):
        calls.append(args)
        command = ' '.join(args)
        if 'services describe' in command:
            value = next(descriptions)
            if failure == 'concurrent' and len(calls) > 5:
                value['status']['traffic'][0]['revisionName'] = 'api-other-release'
            return SimpleNamespace(returncode=0, stdout=json.dumps(value).encode())
        bad = (failure == 'probe' and 'jobs execute' in command) or (failure == 'deployment' and 'run deploy' in command)
        return SimpleNamespace(returncode=int(bad), stdout=b'{}')
    monkeypatch.setattr('subprocess.run', run)
    if failure:
        with pytest.raises(RuntimeError): deploy(project='project', region='region', service='api', image='image', suffix='release')
    else:
        assert deploy(project='project', region='region', service='api', image='image', suffix='release')['status'] == 'reader_release_promoted'
    promotions = [call for call in calls if 'update-traffic' in call]
    assert len(promotions) == (0 if failure else 1)
    assert all('lanes-news-discovery' not in str(call) for call in calls)


def test_bad_http_status_stops_canary():
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(503))) as client:
        with pytest.raises(ValueError, match='reader_check_http_503'):
            get_json(client, 'https://api.run.app', '/api/v1/admin/news/results')


@pytest.mark.parametrize('metadata_only', [True, False])
def test_detail_gate_preserves_truthful_legacy_metadata_only_records(metadata_only):
    detail = {'item': {'key': '1:0'}, 'captured_input': {'article_text': None},
              'is_metadata_only': metadata_only}
    if metadata_only:
        check_detail({'key': '1:0'}, detail)
    else:
        with pytest.raises(ValueError, match='detail_mismatch'):
            check_detail({'key': '1:0'}, detail)


def test_detail_from_another_run_cannot_pass():
    with pytest.raises(ValueError, match='detail_mismatch'):
        check_detail({'key': '1:0'}, {'item': {'key': '2:0'}, 'is_metadata_only': True})


@pytest.mark.skipif(not (Path(__file__).resolve().parents[2] / 'cloudbuild.yaml').exists(),
                    reason='Cloud Build source is checked in the repository, outside the backend runtime image')
def test_cloudbuild_promotes_only_through_reader_gate():
    source = (Path(__file__).resolve().parents[2] / 'cloudbuild.yaml').read_text()
    assert 'scripts/deploy_api_checked.py' in source
    assert "- 'lanes-news-discovery'" not in source
    assert "- 'lanes-news-verified'" not in source
    assert "- 'update-traffic'" not in source
