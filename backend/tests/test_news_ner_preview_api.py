"""Small FastAPI test app: no scheduler startup or database connections."""
import asyncio
from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api import deps
from app.api.v1.endpoints import admin_news_ner as endpoint
from app.core.database import get_db
from app.core.limiter import limiter
from app.services.news_ner.runtime import PreviewError
from app.services.news_ner_preview_service import preview_article
from test_news_ner_preview import article, config, fake_runner


@pytest.fixture
def harness(monkeypatch):
    state=SimpleNamespace(row=article(),reads=0,error=None)
    class ReadOnlyDB:
        def get(self,model,identity):
            state.reads+=1
            if state.error:raise state.error
            assert identity==7
            return state.row
        def __getattr__(self,name):raise AssertionError('unexpected DB operation: '+name)
    app=FastAPI()
    app.state.limiter=limiter
    app.include_router(endpoint.router,prefix='/api/v1/admin/news')
    app.dependency_overrides[get_db]=lambda:ReadOnlyDB()
    monkeypatch.setattr(limiter,'enabled',False)
    monkeypatch.setattr(endpoint.settings,'NEWS_NER_PREVIEW_ENABLED',True)
    monkeypatch.setattr(endpoint.settings,'ENVIRONMENT','test')
    async def extract(row):return await preview_article(row,config(),fake_runner)
    monkeypatch.setattr(endpoint,'preview_article',extract)
    with TestClient(app) as client:yield client,app,state


def test_unauthenticated_denied_without_storage_or_inference(harness):
    client,app,state=harness
    response=client.post('/api/v1/admin/news/articles/7/ner-preview')
    assert response.status_code==401
    assert response.headers['cache-control']=='no-store'
    assert state.reads==0


def test_commuter_denied_before_storage(harness):
    client,app,state=harness
    app.dependency_overrides[deps.get_current_user]=lambda:SimpleNamespace(role=SimpleNamespace(name='Commuter'))
    response=client.post('/api/v1/admin/news/articles/7/ner-preview')
    assert response.status_code==403
    assert state.reads==0
    assert response.headers['cache-control']=='no-store'


def admin(app):app.dependency_overrides[deps.get_current_active_admin]=lambda:object()


def test_admin_success_and_invalid_id(harness):
    client,app,state=harness;admin(app)
    response=client.post('/api/v1/admin/news/articles/7/ner-preview')
    assert response.status_code==200,response.text
    value=response.json()
    assert value['schema_version']=='lanes-ner-preview-v1'
    assert value['source']['canonical_url']==state.row.canonical_url
    assert value['graph']['schema']
    assert value['groups'][0]['target_entity_ids']==['n0']
    assert state.reads==1
    assert response.headers['cache-control']=='no-store'
    invalid=client.post('/api/v1/admin/news/articles/0/ner-preview')
    assert invalid.status_code==422
    assert invalid.headers['cache-control']=='no-store'


@pytest.mark.parametrize('status,code',[(409,'article_body_unavailable'),(413,'article_too_large'),
    (429,'preview_busy'),(503,'preview_assets_unavailable'),(504,'preview_timeout'),(502,'preview_worker_failed')])
def test_worker_failures_are_visible_and_not_cacheable(harness,monkeypatch,status,code):
    client,app,state=harness;admin(app)
    async def fail(row):raise PreviewError(status,code)
    monkeypatch.setattr(endpoint,'preview_article',fail)
    response=client.post('/api/v1/admin/news/articles/7/ner-preview')
    assert response.status_code==status
    assert response.json()['detail']['code']==code
    assert response.headers['cache-control']=='no-store'


def test_not_found_storage_failure_and_disabled(harness,monkeypatch):
    client,app,state=harness;admin(app)
    state.row=None
    assert client.post('/api/v1/admin/news/articles/7/ner-preview').status_code==404
    state.error=SQLAlchemyError('private storage detail')
    result=client.post('/api/v1/admin/news/articles/7/ner-preview')
    assert result.status_code==503
    assert 'private storage detail' not in result.text
    reads=state.reads
    monkeypatch.setattr(endpoint.settings,'NEWS_NER_PREVIEW_ENABLED',False)
    result=client.post('/api/v1/admin/news/articles/7/ner-preview')
    assert result.json()['detail']['code']=='preview_disabled'
    assert state.reads==reads


def test_rate_limit(harness,monkeypatch):
    client,app,state=harness;admin(app)
    limiter._storage.reset()
    monkeypatch.setattr(limiter,'enabled',True)
    results=[client.post('/api/v1/admin/news/articles/7/ner-preview') for _ in range(4)]
    assert [r.status_code for r in results]==[200,200,200,429]
    assert results[-1].headers['cache-control']=='no-store'
