"""Manual release gates and deterministic no-provider cloud contract."""
import json
from pathlib import Path

import pytest

from app.services.news_verified_cloud import release_file,require_provider_execution
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_ner_durable.contracts import sha
from scripts.news_verified_contract import check_contract
from test_news_ner_durable import trusted
from test_news_native_resolution import resolver
from test_news_ner_integration import c3b_db


def test_provider_gate_defaults_disabled_even_with_authority(tmp_path,monkeypatch):
    monkeypatch.delenv('LANES_NEWS_GEMINI_EXECUTION_ENABLED',raising=False)
    with pytest.raises(ResolutionError,match='execution_disabled'):
        require_provider_execution({},authority=tmp_path/'grant.json',authority_sha256='a'*64)


def test_enabled_provider_gate_requires_exact_authority_arguments(monkeypatch):
    monkeypatch.setenv('LANES_NEWS_GEMINI_EXECUTION_ENABLED','1')
    with pytest.raises(ResolutionError,match='authority_required'):
        require_provider_execution({},authority=None,authority_sha256=None)


def test_modified_release_pin_rejected(tmp_path):
    value={'schema_version':'news-verified-cloud-release-v1','application_files':{}}
    path=tmp_path/'release.json';path.write_text(json.dumps(value))
    with pytest.raises(ResolutionError,match='release_invalid'):release_file(path,'a'*64)
    assert release_file(path,sha(value))==value


def test_cloud_preflight_keeps_engine_bound_session_and_read_only_transaction(c3b_db,monkeypatch):
    from types import SimpleNamespace
    from sqlalchemy import text
    from app.services import news_verified_cloud as cloud
    from app.services.news_historical_processing import database_identity
    from app.services.news_native_read_context import SavedNativeReadContext
    raw='ner-v1:'+'1'*64;resolved='ner-v1:'+'2'*64
    with c3b_db() as db:
        engine=db.get_bind()
        db.execute(text("INSERT INTO system_settings(key,value) VALUES (:key,CAST(:value AS jsonb))"),
            {'key':'operational_configuration_v1','value':json.dumps({'settings':{
                'news_collection_enabled':False,'news_processing_enabled':False,'news_publication_enabled':False}})})
        db.commit()
    release={'confirmed_database':engine.url.database,'database_identity_sha256':database_identity(engine),
             'resolved_pipeline_version':resolved}
    monkeypatch.setattr(cloud,'assets_for_release',lambda _:SimpleNamespace(pipeline_version=raw))
    monkeypatch.setattr(cloud,'resolver_for_release',lambda _:SimpleNamespace(identity={'model':'mock-only'}))
    monkeypatch.setattr('app.services.news_native_read_context.configured_native_read_context',
        lambda:SavedNativeReadContext(resolved,database_identity(engine),(raw,)))
    result=cloud.preflight(release,database_url=engine.url.render_as_string(hide_password=False))
    assert result['status']=='preflight_passed' and result['database_read_only']
    assert result['database_writes']==result['external_provider_requests']==0


@pytest.mark.asyncio
async def test_cloud_contract_has_zero_database_provider_or_inference(trusted):
    result=await check_contract(trusted,resolver())
    assert result['status']=='passed' and len(result['checks'])==7
    assert result['external_provider_requests']==result['database_writes']==result['model_inferences']==0


@pytest.mark.asyncio
@pytest.mark.parametrize('status',[200,401,429,503])
async def test_provider_smoke_is_one_request_without_database_writes(trusted,status):
    import httpx
    from scripts.news_verified_contract import row
    from scripts.news_verified_provider_check import check_provider
    def handler(request):
        if status!=200:return httpx.Response(status)
        document=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        return httpx.Response(200,json={'modelVersion':'mock-only','candidates':[
            {'finishReason':'STOP','content':{'parts':[{'text':json.dumps({'results':[
                row(target) for target in document['targets']]})}]}}]})
    receipt=await check_provider(trusted,resolver(),transport=httpx.MockTransport(handler))
    assert receipt['external_provider_requests']==1 and receipt['database_writes']==0
    assert receipt['http_status']==status
    assert receipt['status']==('passed' if status==200 else 'failed')


@pytest.mark.parametrize('failure,target,status',[
    ('import','app.services.news_verified_cloud',1),
    ('interrupt','app.services.news_verified_cloud',130),
    ('cancel','app.services.news_verified_cloud',130)])
def test_cloud_worker_bootstrap_fails_without_side_effects(tmp_path,monkeypatch,failure,target,status):
    import test_news_ner_processing_cli as probes
    monkeypatch.setattr(probes,'BOOTSTRAP_PROBE',probes.BOOTSTRAP_PROBE.replace(
        'scripts.run_news_ner_processing','scripts.run_news_verified_cloud'))
    result=probes.run_fresh_cli(tmp_path,failure,target,['preflight'])
    assert result.returncode==status and result.stderr==''
    value=json.loads(result.stdout)
    assert value['status']=='interrupted' if status==130 else value['status']=='failed'
