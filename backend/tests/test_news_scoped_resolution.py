"""Source-scoped V2 qualification; provider calls are mocked, never paid."""
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace

import httpx
import pytest

from app.services.news_gemini_receipts import BatchJournal, replay_bundle
from app.services.news_ner_durable.adapter import build_native_result, verify_saved_result
from app.services.news_ner_durable.assets import with_resolution_assets
from app.services.news_ner_durable.contracts import RunEvidence, sha
from app.services.news_ner_durable.gemini_resolution import GeminiResolver
from app.services.news_ner_durable.read_projection import build_read_projection
from app.services.news_ner_durable.resolution import (ResolvedMention, ResolutionError, apply_resolution,
                                                     resolve_rows, targets)
from app.services.news_ner_durable.scoped_resolution import CONTRACT, VERSION, evaluate_rows, source_layout, replay_scoped_batch
from test_news_gemini_receipts import Receipts, envelope, bundle
from test_news_native_resolution import answer, resolver, TEXT
from test_news_ner_durable import trusted, make_case, NOW

LIST = ('Flooded roads on October 20, 2026\nBelow is a list of flooded areas.\n'
        'Pasig City (as of 10 AM)\n▶️ Knee-deep (19 inches)\nBrgy. Kapitolyo\n'
        '- Fictional Crescent\n- Fictional Lane\n▶️ Ankle-deep (9 inches)\n'
        'Brgy. Kapitolyo\n- Fictional Avenue')
LABELS = [('Pasig City','CITY'),('Brgy. Kapitolyo','BARANGAY'),
          ('Fictional Crescent','ROAD'),('Fictional Lane','ROAD'),('Fictional Avenue','ROAD')]


def case(trusted, text=LIST, labels=LABELS, *, batch_size=4):
    run, version, _, inference, original = make_case(trusted, text, labels=labels)
    service = GeminiResolver(replace(resolver().config,batch_size=batch_size), evidence_contract=CONTRACT)
    derived = with_resolution_assets(trusted, service.identity)
    context = RunEvidence.from_records(SimpleNamespace(id=12,article_version_id=version.id,
        mode='ner_rules_v1',pipeline_version=derived.pipeline_version),version)
    baseline = build_native_result(context,inference,derived,extracted_at=NOW)
    service.catalog = derived.catalog
    return service, derived, context, baseline, run, original


def list_answer(target):
    if target['label'] != 'ROAD':
        return answer(target)
    last = target['text'] == 'Fictional Avenue'
    q = {'Fictional Crescent':5,'Fictional Lane':6,'Fictional Avenue':9}[target['text']]
    return answer(target,place_evidence=[2,8 if last else 4,q],status_evidence=[1,q],
        time_evidence=[0,2,q],depth_evidence=[7 if last else 3,q],depth_scope='shared',
        depth_text='Ankle-deep (9 inches)' if last else 'Knee-deep (19 inches)')


def parsed(rows):
    return [ResolvedMention.model_validate_json(json.dumps(r),strict=True) for r in rows]


def test_layout_binds_exact_repeated_occurrences_and_resets_depth(trusted):
    _,_,context,baseline,_,_=case(trusted)
    layout = source_layout(LIST, targets(baseline))
    assert len(layout['targets']) == len(targets(baseline))
    roads = {m['text']:next(r for r in layout['targets'] if r['target_id']==m['id'])
             for m in targets(baseline) if m['label']=='ROAD'}
    assert roads['Fictional Crescent']['target_passages']==[5]
    assert roads['Fictional Crescent']['list_context']==dict(city_heading=2,barangay_heading=4,depth_heading=3,clock_heading=2)
    assert roads['Fictional Avenue']['list_context']['barangay_heading']==8
    assert roads['Fictional Avenue']['list_context']['depth_heading']==7
    assert all(r['context_only_heading'] for m in targets(baseline) if m['label']=='BARANGAY'
               for r in layout['targets'] if r['target_id']==m['id'])
    assert 0 in layout['date_candidates'] and 1 in layout['affirmative_status_candidates']


@pytest.mark.asyncio
async def test_full_article_scoped_projection_saved_recompute_and_replay(trusted):
    service,derived,context,baseline,run,original=case(trusted)
    storage=Receipts();service.receipts=BatchJournal(storage,secrets=(service.config.gemini_api_key,))
    calls=[]
    def handler(request):
        payload=json.loads(request.content);doc=json.loads(payload['contents'][0]['parts'][0]['text'])
        assert doc['evidence_text']==LIST
        assert doc['quote_options'][5]['quote']=='- Fictional Crescent'
        assert doc['evidence_contract']==CONTRACT
        assert doc['source_layout']==source_layout(LIST,targets(baseline))
        assert 'BOTH exact date' in str(payload['generationConfig']['responseJsonSchema'])
        calls.append(1)
        value=envelope([list_answer(m) for m in doc['targets']])
        value['usageMetadata']['thoughtsTokenCount']=3
        return httpx.Response(200,json=value)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        saved=await service.resolve(context.source(),baseline,parent_run_id=run.id,
            parent_result_sha256=sha(original.model_dump(mode='json',by_alias=True)),client=client)
    assert len(calls)==2 and saved['schema_version']==VERSION
    assert len([r for r in saved['row_outcomes'] if r['outcome']=='accepted'])==3
    before=sha(baseline.model_dump(mode='json',by_alias=True))
    result=apply_resolution(context.source(),baseline,saved,derived.catalog,service.identity)
    assert sha(baseline.model_dump(mode='json',by_alias=True))==before
    assert len(result.claims)==3 and {c.event_time_resolved.hour for c in result.claims}=={10}
    assert all(c.depth_canonical is None and c.depth_raw for c in result.claims)
    assert len({g['claim_index'] for g in result.projection['groups']})==3
    result.read_projection=build_read_projection(context.source(),result,derived.catalog)
    assert len(verify_saved_result(context,result,derived).claims)==3
    for intent in [v for k,v in storage.items.items() if k.endswith('/intent.json')]:
        receipt={'intent':intent,'response':storage.items[intent['request_identity']+'/response.json']}
        for _ in range(2):
            assert replay_bundle(receipt,sha(receipt),config=service.config)['provider_requests']==0
            replayed=replay_scoped_batch(receipt,sha(receipt),resolver=service,source=context.source(),baseline=baseline,
                parent_run_id=run.id,parent_result_sha256=sha(original.model_dump(mode='json',by_alias=True)))
            assert replayed['status']=='row_outcomes_recorded' and replayed['provider_requests']==0
        with pytest.raises(ResolutionError,match='replay_request_mismatch'):
            replay_scoped_batch(receipt,sha(receipt),resolver=service,source=context.source(),baseline=baseline,
                parent_run_id=999,parent_result_sha256=sha(original.model_dump(mode='json',by_alias=True)))
    assert len(calls)==2 and service.config.gemini_api_key not in json.dumps(storage.items)
    changed=deepcopy(saved);changed['row_outcomes'][0]['outcome']='accepted'
    with pytest.raises(ResolutionError,match='outcomes_mismatch'):
        apply_resolution(context.source(),baseline,changed,derived.catalog,service.identity)


def test_simultaneous_missing_evidence_is_row_local_and_old_contract_stays_strict(trusted):
    service,derived,context,baseline,_,_=case(trusted)
    rows=[list_answer(m) for m in targets(baseline)]
    bad=next(r for r in rows if r['verdict']=='observed')
    bad.update(place_evidence=[2,4],status_evidence=[2,4,5],time_evidence=[2])
    claims,groups,_,outcomes,_=evaluate_rows(context.source(),baseline,parsed(rows),derived.catalog)
    assert len(claims)==2
    row=next(r for r in outcomes if r['target_id']==bad['target_id'])
    assert row['outcome']=='unresolved'
    assert {'native_resolution_place_evidence_missing','native_resolution_status_evidence_missing',
            'native_resolution_date_evidence_missing'} <= {i['code'] for i in row['issues']}
    with pytest.raises(ResolutionError,match='place_evidence_missing'):
        resolve_rows(context.source(),baseline,parsed(rows),derived.catalog)


@pytest.mark.parametrize('field,value,code',[
    ('depth_evidence',[7,5],'scope_mismatch'),
    ('place_evidence',[2,8,5],'scope_mismatch'),
    ('status_evidence',[1,5,6],'fact_target_mismatch'),
    ('section_evidence',[6],'fact_target_mismatch'),
    ('date_text','October 21, 2026','date_evidence_missing'),
    ('clock_text','11 AM','clock_evidence_missing'),
    ('depth_text','waist-deep','depth_evidence_missing'),
    ('access','impassable_all','access_evidence_missing'),
    ('contradictory',True,'observation_not_supported'),
    ('status','forecast','observation_not_supported')])
def test_unsupported_fields_never_create_claims(trusted,field,value,code):
    _,derived,context,baseline,_,_=case(trusted)
    target=next(m for m in targets(baseline) if m['text']=='Fictional Crescent')
    row=list_answer(target);row[field]=value
    claims,_,_,outcomes,_=evaluate_rows(context.source(),baseline,parsed([row]),derived.catalog)
    assert not claims
    assert any(code in i['code'] for i in outcomes[0]['issues'])


@pytest.mark.parametrize('field,value', [('place_evidence',[5,5]),('time_evidence',[-1]),('depth_evidence',[999])])
def test_invalid_references_are_hard_failures_even_for_unsupported_rows(trusted,field,value):
    _,derived,context,baseline,_,_=case(trusted)
    row=answer(targets(baseline)[0],**{field:value})
    with pytest.raises(ResolutionError,match='evidence_invalid'):
        evaluate_rows(context.source(),baseline,parsed([row]),derived.catalog)


@pytest.mark.parametrize('text,labels',[
    ('On October 20, 2026 as of 10 AM, Pasig City was flooded.', [('Pasig City','CITY')]),
    ('On October 20, 2026 as of 10 AM, Brgy. Kapitolyo in Pasig City was flooded.',
     [('Brgy. Kapitolyo','BARANGAY'),('Pasig City','CITY')])])
def test_real_locality_only_observation_is_preserved(trusted,text,labels):
    _,derived,context,baseline,_,_=case(trusted,text,labels)
    target=targets(baseline)[0]
    row=answer(target,verdict='observed',city='Pasig City',place_evidence=[0],status='active',status_evidence=[0],
               time_role='observation',date_text='October 20, 2026',clock_text='10 AM',time_evidence=[0])
    claims,_,_,outcomes,_=evaluate_rows(context.source(),baseline,parsed([row]),derived.catalog)
    assert len(claims)==1 and outcomes[0]['outcome']=='accepted'


def test_heading_claim_is_unresolved_instead_of_duplicate_incident(trusted):
    _,derived,context,baseline,_,_=case(trusted)
    target=next(m for m in targets(baseline) if m['label']=='BARANGAY')
    row=answer(target,verdict='observed',city='Pasig City',barangay='Brgy. Kapitolyo',place_evidence=[2,4],
               status='active',status_evidence=[1,4],time_role='observation',date_text='October 20, 2026',
               clock_text='10 AM',time_evidence=[0,2,4])
    claims,_,_,outcomes,_=evaluate_rows(context.source(),baseline,parsed([row]),derived.catalog)
    assert not claims and any(i['code']=='native_resolution_context_heading' for i in outcomes[0]['issues'])


def test_narrative_and_city_change_stop_layout_inheritance():
    text='Pasig City\n- Road A\nThe flooding subsided at 11 AM.\n- Road B\nQuezon City\n- Road C'
    candidates=[]
    for i,(name,label) in enumerate([('Pasig City','CITY'),('Road A','ROAD'),('Road B','ROAD'),
                                    ('Quezon City','CITY'),('Road C','ROAD')]):
        start=text.index(name);candidates.append(dict(id=str(i),text=name,label=label,start=start,end=start+len(name)))
    rows={r['target_id']:r for r in source_layout(text,candidates)['targets']}
    assert rows['1']['list_context']['city_heading']==0
    assert rows['2']['list_context']['city_heading'] is None
    assert rows['4']['list_context']['city_heading']==4


@pytest.mark.asyncio
async def test_malformed_first_response_still_prevents_second_request(trusted):
    service,_,context,baseline,run,original=case(trusted)
    calls=[]
    def handler(request):
        calls.append(1)
        return httpx.Response(200,json=envelope([]))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ResolutionError,match='target_mismatch'):
            await service.resolve(context.source(),baseline,parent_run_id=run.id,
                parent_result_sha256=sha(original.model_dump(mode='json',by_alias=True)),client=client)
    assert len(calls)==1


@pytest.mark.asyncio
async def test_semantic_receipt_failure_stops_later_batches(trusted):
    service,_,context,baseline,run,original=case(trusted)
    storage=Receipts('semantic-validation.json');service.receipts=BatchJournal(storage)
    calls=[]
    def handler(request):
        doc=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        calls.append(1)
        return httpx.Response(200,json=envelope([list_answer(m) for m in doc['targets']]))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ResolutionError,match='receipt_storage_failed'):
            await service.resolve(context.source(),baseline,parent_run_id=run.id,
                parent_result_sha256=sha(original.model_dump(mode='json',by_alias=True)),client=client)
    assert len(calls)==1 and any(k.endswith('/response.json') for k in storage.items)


@pytest.mark.parametrize('clock,date_value', [(None,'October 20, 2026'),(None,None)])
def test_date_only_and_unknown_starts_remain_unknown_instants(trusted,clock,date_value):
    _,derived,context,baseline,_,_=case(trusted,TEXT,[('Fictional Crescent','ROAD'),('Pasig City','CITY')])
    row=answer(next(m for m in targets(baseline) if m['label']=='ROAD'),clock_text=clock,date_text=date_value)
    claims,groups,_,outcomes,_=evaluate_rows(context.source(),baseline,parsed([row]),derived.catalog)
    assert len(claims)==1 and claims[0].event_time_resolved is None
    assert groups[0]['normalizations']['time']['occurrence_date']==('2026-10-20' if date_value else None)


@pytest.mark.asyncio
async def test_provider_usage_survives_invalid_evidence_references(trusted):
    service,_,context,baseline,run,original=case(trusted)
    calls=[]
    def handler(request):
        doc=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        rows=[list_answer(m) for m in doc['targets']];rows[0]['place_evidence']=[999]
        calls.append(1)
        value=envelope(rows);value['usageMetadata']['thoughtsTokenCount']=2
        return httpx.Response(200,json=value)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ResolutionError,match='evidence_invalid'):
            await service.resolve(context.source(),baseline,parent_run_id=run.id,
                parent_result_sha256=sha(original.model_dump(mode='json',by_alias=True)),client=client)
    assert len(calls)==1
    assert service.last_usage==[dict(request_id='safe-id',actual_model='gemini-3.5-flash-lite',
                                   input_tokens=10,output_tokens=20,thinking_tokens=2)]


def test_unknown_contract_is_not_silently_selected():
    with pytest.raises(ResolutionError,match='contract_invalid'):
        GeminiResolver(resolver().config,evidence_contract='typo')


@pytest.mark.parametrize('prefix,accepted', [('FLOOD ALERT',True),('WEATHER UPDATE',True),('Flood Alert Road',False)])
def test_editorial_ner_false_positive_does_not_own_headline_date(trusted,prefix,accepted):
    text=prefix+': Flooded roads in Pasig City on October 20, 2026\nAs of 10 AM\nFictional Crescent was flooded knee-deep.'
    _,derived,context,baseline,_,_=case(trusted,text,[(prefix,'ROAD'),('Pasig City','CITY'),('Fictional Crescent','ROAD')])
    target=next(m for m in targets(baseline) if m['text']=='Fictional Crescent')
    row=answer(target,place_evidence=[0,2],status_evidence=[2],time_evidence=[0,1,2],depth_evidence=[2])
    claims,_,_,outcomes,_=evaluate_rows(context.source(),baseline,parsed([row]),derived.catalog)
    assert bool(claims)==accepted
    with pytest.raises(ResolutionError,match='fact_target_mismatch'):
        resolve_rows(context.source(),baseline,parsed([row]),derived.catalog)
    if accepted:
        assert claims[0].event_time_resolved.hour==10
        rubric=next(m for m in targets(baseline) if m['text']==prefix)
        wrong=answer(rubric,verdict='observed',city='Pasig City',place_evidence=[0],status='active',status_evidence=[0])
        rubric_claims,_,_,rubric_outcomes,_=evaluate_rows(context.source(),baseline,parsed([wrong]),derived.catalog)
        assert not rubric_claims and any(i['code']=='native_resolution_editorial_context' for i in rubric_outcomes[0]['issues'])
