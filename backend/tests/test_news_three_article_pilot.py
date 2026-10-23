"""Manual pilot must not reopen ordinary processing or weaken source selection."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json

import httpx
import pytest
from sqlalchemy import select

from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.setting import SystemSetting
from app.schemas.configuration import OperationalSettings
from app.services.configuration_service import CONFIG_KEY
from app.services.news_historical_processing import database_identity
from app.services.news_pilot_budget import PilotBudget, MODEL
from app.services.news_three_article_pilot import PilotAuthority, pilot_application_identity
from app.services.news_ner_durable.assets import with_resolution_assets
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.gemini_resolution import GeminiResolver
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_ner_durable.resolution_worker import resolve_native_runs
from test_news_native_resolution import resolver, answer, TEXT, NOW
from test_news_pilot_budget import Store
from test_news_ner_integration import c3b_db, operational_trusted, base_trusted, save_native, SOURCES


def grant(factory, trusted, service, ids, operation='resolve'):
    with factory() as db:
        inputs = []
        for run_id in ids:
            run = db.get(NewsExtractionRun, run_id)
            version = db.get(NewsArticleVersion, run.article_version_id)
            inputs.append({'article_id': version.article_id, 'source_version_id': version.id,
                'source_input_fingerprint': version.input_fingerprint, 'native_input_fingerprint': version.input_fingerprint,
                'input_snapshot': version.input_snapshot,
                'body_sha256': hashlib.sha256(version.input_snapshot['article_text'].encode()).hexdigest()})
        policy = {'schema_version': 'news-three-article-pilot-v1', 'application_sha256': pilot_application_identity(),
            'database_identity_sha256': database_identity(db.get_bind()), 'confirmed_database': db.get_bind().url.database,
            'assets_sha256': sha(trusted.manifest), 'pipeline_version': trusted.pipeline_version,
            'resolved_pipeline_version': with_resolution_assets(trusted, service.identity).pipeline_version,
            'resolver': service.identity, 'resource_profile': 'cloud-run-v1', 'live_publication_allowed': False,
            'allowed_operations': [operation], 'session_id': 'fictional-pilot', 'inputs': inputs}
    return PilotAuthority(policy, sha(policy), trusted)


@pytest.fixture
def selected(c3b_db, operational_trusted, request):
    body = getattr(request, 'param', TEXT)
    ids = tuple(save_native(c3b_db, operational_trusted, body=body)[0] for _ in range(3))
    config = OperationalSettings().model_copy(update={**{key: False for key in (
        'news_collection_enabled', 'news_processing_enabled', 'news_publication_enabled',
        'automatic_expiry_enabled', 'pasig_ml_expiry_enabled')}, 'news_source_ids': ['fictional']})
    with c3b_db() as db, db.begin():
        db.add(SystemSetting(key=CONFIG_KEY, value={'revision': 1, 'settings': config.model_dump(mode='json')}))
    service = GeminiResolver(replace(resolver().config, model=MODEL), budget=PilotBudget(Store(), 'selection'))
    authority = grant(c3b_db, operational_trusted, service, ids)
    return ids, service, authority


@pytest.mark.asyncio
async def test_paused_ordinary_worker_stays_paused_and_exact_pilot_reuses(c3b_db, operational_trusted, selected):
    ids, service, authority = selected
    with pytest.raises(ResolutionError, match='processing_paused'):
        await resolve_native_runs(c3b_db, (ids[0],), trusted=operational_trusted,
            resolver=service, sources=SOURCES, clock=lambda: NOW)
    calls = []
    def handler(request):
        doc = json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        calls.append(doc)
        return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'text': json.dumps({'results': [answer(m) for m in doc['targets']]})}]}}]})
    with c3b_db() as db:
        parent = sha(db.get(NewsExtractionRun, ids[0]).result)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        for expected in ('completed', 'reused'):
            outcome = await resolve_native_runs(c3b_db, (ids[0],), trusted=operational_trusted,
                resolver=service, sources=SOURCES, clock=lambda: NOW, client=client, pilot_authorization=authority)
            assert outcome[expected] == 1
    assert len(calls) == 1
    with c3b_db() as db:
        assert sha(db.get(NewsExtractionRun, ids[0]).result) == parent


def test_pilot_rejects_wrong_selection_operation_and_changed_configuration(c3b_db, operational_trusted, selected):
    ids, service, authority = selected
    with c3b_db() as db:
        with pytest.raises(ResolutionError, match='one_article'):
            authority.validate_session(db, ids[:2], SOURCES, operation='resolve')
        with pytest.raises(ResolutionError, match='operation'):
            authority.validate_session(db, (ids[0],), SOURCES)
        altered = deepcopy(authority.policy); altered['inputs'][0]['body_sha256'] = '0'*64
        with pytest.raises(ResolutionError, match='input_changed'):
            PilotAuthority(altered, sha(altered), operational_trusted).validate(db.get_bind())
        config = db.get(SystemSetting, CONFIG_KEY)
        changed = deepcopy(config.value); changed['settings']['automatic_expiry_enabled'] = True
        config.value = changed; db.flush()
        with pytest.raises(ResolutionError, match='configuration_changed'):
            authority.validate_session(db, (ids[0],), SOURCES, operation='resolve')


def test_pilot_rejects_an_intact_old_input_when_collection_has_been_corrected(c3b_db, selected):
    from app.models.news import NewsArticle
    ids, _service, authority = selected
    with c3b_db() as db, db.begin():
        run = db.get(NewsExtractionRun, ids[0])
        version = db.get(NewsArticleVersion, run.article_version_id)
        original = deepcopy(version.input_snapshot)
        db.get(NewsArticle, version.article_id).article_text = 'A different publisher update.'
        db.flush()
        with pytest.raises(ResolutionError, match='pilot_source_capture_requires_review'):
            authority.validate_session(db, (ids[0],), SOURCES, operation='resolve')
        assert version.input_snapshot == original
