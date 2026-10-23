"""Real native projection plus mocked Gemini; never paid calls or model inference."""
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace

import httpx
import pytest

from app.services.news_claim_auditor import AuditorConfig
from app.services.news_ner_durable.adapter import build_native_result, verify_saved_result
from app.services.news_ner_durable.assets import with_resolution_assets
from app.services.news_ner_durable.contracts import RunEvidence, sha
from app.services.news_ner_durable.gemini_resolution import GeminiResolver
from app.services.news_ner_durable.read_projection import build_read_projection
from app.services.news_ner_durable.resolution import ResolutionError, apply_resolution, targets, resolution_audit
from test_news_ner_durable import trusted, make_case, NOW

TEXT='On October 20, 2026 as of 10 AM, Fictional Crescent in Pasig City was flooded knee-deep.'


def resolver():
    return GeminiResolver(AuditorConfig(provider='gemini',model='fixture-model',gemini_api_key='synthetic-key'))


def answer(target, **changes):
    value=dict(target_id=target['id'],verdict='unsupported',city=None,barangay=None,place_evidence=[],
        status='unclear',historical=False,contradictory=False,status_evidence=[],time_role='unknown',
        date_text=None,clock_text=None,contemporaneous=False,time_evidence=[],depth_text=None,depth_scope='unknown',
        depth_evidence=[],access='unknown',access_evidence=[],road_section=None,section_evidence=[])
    if target['label']=='ROAD':
        value.update(verdict='observed',city='Pasig City',place_evidence=[0],status='active',status_evidence=[0],
            time_role='observation',date_text='October 20, 2026',clock_text='10 AM',time_evidence=[0],
            depth_text='knee-deep',depth_scope='individual',depth_evidence=[0])
    value.update(changes)
    return value


def setup(trusted,text=TEXT,labels=None):
    run,version,context,inference,original=make_case(trusted,text,labels=labels)
    service=resolver();derived=with_resolution_assets(trusted,service.identity)
    child=SimpleNamespace(id=12,article_version_id=version.id,mode='ner_rules_v1',pipeline_version=derived.pipeline_version)
    child_context=RunEvidence.from_records(child,version)
    baseline=build_native_result(child_context,inference,derived,extracted_at=NOW)
    payload=dict(schema_version='native-gemini-resolution-v1',identity=service.identity,input_sha256=context.input_fingerprint,
        parent_run_id=run.id,parent_result_sha256=sha(original.model_dump(mode='json',by_alias=True)),
        results=[answer(m) for m in targets(baseline)])
    return service,derived,child_context,baseline,payload,original


def test_missing_time_is_corrected_without_mutating_native_graph(trusted):
    service,derived,context,baseline,payload,original=setup(trusted)
    assert original.claims[0].event_time_resolved is None
    before=original.model_dump(mode='json',by_alias=True)
    result=apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)
    assert result.claims[0].event_time_resolved.isoformat()=='2026-10-20T10:00:00+08:00'
    assert result.claims[0].canonical_road=='Fictional Crescent'
    assert original.model_dump(mode='json',by_alias=True)==before
    assert result.native.model_dump(mode='json',by_alias=True)==original.native.model_dump(mode='json',by_alias=True)
    result.read_projection=build_read_projection(context.source(),result,derived.catalog)
    assert verify_saved_result(context,result,derived).claims[0].event_time_resolved==result.claims[0].event_time_resolved
    assert resolution_audit(context,result,0).outcome=='verified'


def test_unassigned_time_and_native_only_group_can_be_resolved(trusted):
    text='As of 10 AM on October 20, 2026\nPasig City\nFictional Crescent was flooded knee-deep.'
    service,derived,context,baseline,payload,original=setup(trusted,text)
    road=next(r for r in payload['results'] if r['verdict']=='observed')
    road.update(place_evidence=[1,2],status_evidence=[2],time_evidence=[0,2],depth_evidence=[2])
    result=apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)
    assert len(result.claims)==1 and result.claims[0].event_time_resolved is not None
    assert result.claims[0].canonical_city=='City of Pasig'
    assert result.projection['groups'][0]['target_entity_ids']==[road['target_id']]


def test_today_uses_existing_time_field_and_retains_publication_fallback_basis(trusted):
    text='Today, Fictional Crescent in Pasig City was flooded knee-deep.'
    service,derived,context,baseline,payload,_=setup(trusted,text)
    road=next(r for r in payload['results'] if r['verdict']=='observed')
    road.update(date_text='Today',clock_text=None,contemporaneous=True)
    result=apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)
    assert result.claims[0].event_time_resolved==NOW
    assert 'publication_time_fallback' in result.claims[0].uncertainty_reasons
    assert result.projection['groups'][0]['normalizations']['time']['date_basis']=='publication_time_fallback'


@pytest.mark.parametrize('change',[{'historical':True},{'contradictory':True},{'time_role':'report'},
    {'date_text':None,'contemporaneous':False}])
def test_fallback_does_not_create_an_instant_for_unsupported_observations(trusted,change):
    text='Today, Fictional Crescent in Pasig City was flooded knee-deep.'
    service,derived,context,baseline,payload,_=setup(trusted,text)
    road=next(r for r in payload['results'] if r['verdict']=='observed')
    road.update({'date_text':'Today','clock_text':None,'contemporaneous':True,**change})
    result=apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)
    assert not result.claims or result.claims[0].event_time_resolved is None


@pytest.mark.parametrize('mutation',['quote_index','clock','depth','target','identity','parent_hash','duplicate','missing'])
def test_tampered_or_incomplete_resolution_is_rejected(trusted,mutation):
    service,derived,context,baseline,payload,_=setup(trusted)
    road=next(r for r in payload['results'] if r['verdict']=='observed')
    if mutation=='quote_index':road['time_evidence']=[255]
    if mutation=='clock':road['clock_text']='11 PM'
    if mutation=='depth':road['depth_text']='waist-deep'
    if mutation=='target':road['target_id']='invented'
    if mutation=='identity':payload['identity']={**payload['identity'],'model':'other-model'}
    if mutation=='parent_hash':payload['parent_result_sha256']='bad'
    if mutation=='duplicate':payload['results'].append(deepcopy(road))
    if mutation=='missing':payload['results'].pop()
    with pytest.raises(ResolutionError):
        apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)


def test_edited_saved_corrected_fact_fails_recomputation(trusted):
    service,derived,context,baseline,payload,_=setup(trusted)
    result=apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)
    result.claims[0].depth_raw='fabricated'
    with pytest.raises(ValueError):verify_saved_result(context,result,derived)


@pytest.mark.asyncio
@pytest.mark.parametrize('profile', ['normalized', 'compact', 'inline'])
async def test_gemini_receives_full_original_and_unassigned_evidence_with_existing_key(trusted, profile):
    service,derived,context,baseline,payload,_=setup(trusted)
    service = GeminiResolver(replace(service.config, gemini_schema_profile=profile))
    requests=[]
    def handler(request):
        assert request.headers['x-goog-api-key']=='synthetic-key'
        document=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        schema = json.loads(request.content)['generationConfig']['responseJsonSchema']
        assert schema['properties']['results']['minItems'] == len(document['targets'])
        assert schema['properties']['results']['maxItems'] == len(document['targets'])
        row = schema['properties']['results']['items'] if profile == 'inline' else schema['$defs']['ResolvedMention']
        assert row['properties']['target_id']['enum'] == [m['id'] for m in document['targets']]
        for field in ('place','status','time','depth','access','section'):
            assert row['properties'][field+'_evidence']['items'] == {
                'type':'integer','enum':list(range(len(document['quote_options'])))}
        if profile == 'compact':
            assert 'maxItems' not in schema['$defs']['ResolvedMention']['properties']['place_evidence']
        assert document['evidence_text']==TEXT
        assert document['native_facts']==baseline.native.graph.model_dump(mode='json',by_alias=True)['facts']
        assert document['article']['published_at']==context.source().published_at.isoformat()
        requests.append(request.url.path)
        response={'results':[answer(m) for m in document['targets']]}
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(response)}]}}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        saved=await service.resolve(context.source(),baseline,parent_run_id=11,parent_result_sha256='a'*64,client=client)
    result=apply_resolution(context.source(),baseline,saved,derived.catalog,service.identity)
    assert requests==['/v1beta/models/fixture-model:generateContent']
    assert result.claims[0].event_time_resolved is not None


@pytest.mark.asyncio
@pytest.mark.parametrize('overflow', ['observations', 'evidence'])
async def test_compact_provider_schema_still_rejects_oversized_results_locally(trusted, overflow):
    service,_,context,baseline,_,_=setup(trusted)
    service = GeminiResolver(replace(service.config, gemini_schema_profile='compact'))
    calls = []
    def handler(request):
        document = json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        rows = [answer(m) for m in document['targets']]
        if overflow == 'observations':
            rows = [rows[0]] * 9
        else:
            rows[0]['place_evidence'] = [0] * 13
        calls.append(request.url.path)
        return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP',
            'content': {'parts': [{'text': json.dumps({'results': rows})}]}}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ResolutionError, match='native_resolution_response_invalid'):
            await service.resolve(context.source(), baseline, parent_run_id=11,
                parent_result_sha256='a'*64, client=client)
    assert len(calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('status,retryable',[(401,False),(429,True),(503,True),(302,False)])
async def test_provider_failure_is_visible_without_silent_fallback_or_retry(trusted,status,retryable):
    service,_,context,baseline,_,_=setup(trusted)
    calls=[]
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(status,headers={'location':'https://example.org/never-forward-key'})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler),follow_redirects=True) as client:
        with pytest.raises(ResolutionError) as caught:
            await service.resolve(context.source(),baseline,parent_run_id=11,parent_result_sha256='a'*64,client=client)
    assert caught.value.retryable==retryable and len(calls)==1


@pytest.mark.parametrize('change',[{'access':'impassable_all','access_evidence':[0]},
    {'road_section':'invented intersection','section_evidence':[0]}])
def test_unsupported_access_and_section_cannot_become_operational_facts(trusted,change):
    service,derived,context,baseline,payload,_=setup(trusted)
    road=next(r for r in payload['results'] if r['verdict']=='observed');road.update(change)
    with pytest.raises(ResolutionError):apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)


@pytest.mark.parametrize('tail',['was forecast to flood knee-deep.','floodwater completely subsided.'])
def test_false_active_claim_cannot_override_forecast_or_clearance_wording(trusted,tail):
    text='On October 20, 2026 at 10 AM, Fictional Crescent in Pasig City '+tail
    service,derived,context,baseline,payload,_=setup(trusted,text)
    road=next(r for r in payload['results'] if r['verdict']=='observed');road.update(depth_text=None,depth_evidence=[])
    with pytest.raises(ResolutionError):apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)


def test_shared_depth_cannot_become_a_scalar_measurement(trusted):
    service,derived,context,baseline,payload,_=setup(trusted)
    road=next(r for r in payload['results'] if r['verdict']=='observed');road['depth_scope']='shared'
    result=apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)
    assert result.claims[0].depth_raw=='knee-deep' and result.claims[0].depth_canonical is None


def test_publication_fallback_cannot_replace_a_clock_that_was_ignored(trusted):
    service,derived,context,baseline,payload,_=setup(trusted,
        'Today as of 10 AM, Fictional Crescent in Pasig City was flooded knee-deep.')
    road=next(r for r in payload['results'] if r['verdict']=='observed')
    road.update(date_text='Today',clock_text=None,contemporaneous=True)
    result=apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)
    assert result.claims[0].event_time_resolved is None


def test_date_only_observation_retains_calendar_day_without_inventing_start_clock(trusted):
    service,derived,context,baseline,payload,_=setup(trusted,
        'On October 20, 2026, Fictional Crescent in Pasig City was flooded knee-deep.')
    road=next(r for r in payload['results'] if r['verdict']=='observed');road['clock_text']=None
    result=apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)
    assert result.claims[0].event_time_resolved is None
    assert result.projection['groups'][0]['normalizations']['time']['occurrence_date']=='2026-10-20'


@pytest.mark.parametrize('wording',['not passable','no longer passable','never passable'])
def test_negative_passability_cannot_become_a_positive_fact(trusted,wording):
    service,derived,context,baseline,payload,_=setup(trusted,TEXT+' The road is '+wording+'.')
    road=next(r for r in payload['results'] if r['verdict']=='observed')
    road.update(access='passable_unspecified',access_evidence=[0])
    with pytest.raises(ResolutionError,match='access_evidence_missing'):
        apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)


def test_neighbour_road_clock_is_not_borrowed(trusted):
    text='On October 20, 2026, Fictional Crescent in Pasig City was flooded knee-deep.\nAt 10 AM, Other Road in Pasig City was flooded.'
    service,derived,context,baseline,payload,_=setup(trusted,text,labels=[('Fictional Crescent','ROAD'),('Other Road','ROAD'),('Pasig City','CITY')])
    for row in payload['results']:
        if row['verdict']=='observed':row.update(verdict='unsupported')
    road=next(r for r in payload['results'] if next(m for m in targets(baseline) if m['id']==r['target_id'])['text']=='Fictional Crescent')
    road.update(verdict='observed',time_evidence=[0,1])
    with pytest.raises(ResolutionError,match='fact_target_mismatch'):
        apply_resolution(context.source(),baseline,payload,derived.catalog,service.identity)


@pytest.mark.asyncio
async def test_native_dispatch_selects_gemini_from_existing_auditor_configuration(monkeypatch):
    from app.services.news_pipeline_service import run_news_pipeline
    from app.services.news_ner_durable import pipeline
    captured={}
    async def fake(*_args,**kwargs):captured.update(kwargs);return {'status':'fixture'}
    monkeypatch.setattr(pipeline,'run_native_news_pipeline',fake)
    context=SimpleNamespace(trusted=object(),environment='test',database_url='fixture-only')
    service=resolver()
    result=await run_news_pipeline(lambda:pytest.fail('Unexpected DB access'),native_context=context,
        auditor=SimpleNamespace(config=service.config),sources=())
    assert result=={'status':'fixture'}
    assert captured['resolver'].config.gemini_api_key==service.config.gemini_api_key


def test_pinned_reader_context_v2_accepts_only_named_versions(tmp_path,monkeypatch):
    from app.services.news_native_read_context import configured_native_read_context
    from app.services.news_saved_run_service import SavedRunReadError
    value={'schema_version':'saved-native-read-context-v2','pipeline_version':'ner-v1:'+'a'*64,
        'database_identity_sha256':'b'*64,'fallback_pipeline_versions':['ner-v1:'+'c'*64]}
    path=tmp_path/'context.json';path.write_text(json.dumps(value))
    monkeypatch.setenv('LANES_NEWS_NATIVE_READ_CONTEXT',str(path))
    monkeypatch.setenv('LANES_NEWS_NATIVE_READ_CONTEXT_SHA256',sha(value))
    context=configured_native_read_context()
    assert context.pipeline_selection==('ner-v1:'+'a'*64,'ner-v1:'+'c'*64)
    value['fallback_pipeline_versions']=['rules-spatial-preview-v21'];path.write_text(json.dumps(value))
    monkeypatch.setenv('LANES_NEWS_NATIVE_READ_CONTEXT_SHA256',sha(value))
    with pytest.raises(SavedRunReadError):configured_native_read_context()


@pytest.mark.parametrize('failure,target,status',[
    ('settings','',1),('import','pydantic',1),
    ('import','app.services.news_ner_durable.gemini_resolution',1),
    ('interrupt','app.services.news_ner_durable.gemini_resolution',130),
    ('cancel','app.services.news_ner_durable.gemini_resolution',130)])
def test_resolution_cli_bootstrap_does_not_leak_or_start_work(tmp_path,monkeypatch,failure,target,status):
    import test_news_ner_processing_cli as probes
    monkeypatch.setattr(probes,'BOOTSTRAP_PROBE',probes.BOOTSTRAP_PROBE.replace(
        'scripts.run_news_ner_processing','scripts.resolve_news_native'))
    result=probes.run_fresh_cli(tmp_path,failure,target,['preflight','--run-id','1','--model','fixture-model',
        '--bundle','unused','--bundle-sha256','0'*64,'--worker-code-sha256','0'*64,
        '--confirm-database','lanes_p3_verify_cli_bootstrap','--receipt-directory','unused'])
    assert result.returncode==status and result.stderr==''
    assert json.loads(result.stdout)=={'status':'failed','error_code':
        'native_resolution_cancelled' if status==130 else 'native_resolution_failed'}
