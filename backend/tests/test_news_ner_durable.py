"""C2 source-authored fixtures. No model inference, sockets, SQL or publication."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace

import pytest
from sqlalchemy.engine import Engine

from app.schemas.news_extraction import NewsArticleExtractorInput
from app.schemas.news_ner_result import parse_saved_result
from app.services.news_ner.contract import object_sha
from app.services.news_ner.location_pipeline import from_neural_mentions
from app.services.news_ner_runtime.protocol import code_bindings
from app.services.news_ner_durable.adapter import build_native_result, verify_saved_result
from app.services.news_ner_durable.assets import TrustedAssets, load_trusted_assets, normalizer_bindings
from app.services.news_ner_durable.contracts import NerEvidenceError, NativeInput, PublicationEvidence, RunEvidence, capture_native_input, sha
from app.services.news_ner_durable.locality import Catalog
from app.services.news_ner_durable.source_check import check_native_source, source_policy_fingerprint
from app.services.philippine_location_service import NATIONWIDE_PSGC_CSV, PhilippineLocationService

NOW=datetime(2026,10,20,3,tzinfo=timezone.utc)
LEAD='On October 20, 2026 at 10 AM PHT, '
BODY=LEAD+'Fictional Crescent in Pasig City was flooded knee-deep.'


@pytest.fixture(autouse=True)
def no_external_execution(monkeypatch):
    from app.services.news_ner_runtime.supervisor import Session
    def forbidden(*_args,**_kwargs):pytest.fail('C2 attempted SQL or neural inference')
    monkeypatch.setattr(Engine,'connect',forbidden)
    monkeypatch.setattr(Session,'start',forbidden)


@pytest.fixture(scope='module')
def trusted():
    """Explicit fictional model digests; real reference/runtime code, never inference."""
    services=Path(__file__).resolve().parents[1]/'app/services';code=code_bindings(services);bindings=normalizer_bindings()
    manifest={'model':{'name':'v19-control-seed-0','bundle_sha256':'1'*64,'model_manifest_sha256':'2'*64,'resource_manifest_sha256':'3'*64},
              'tokenizer':{'sha256':'4'*64},'runtime':{'version':'lanes-ner-subprocess-v1','code_sha256':object_sha(code)},
              'location_rules':{'version':'lanes-location-repair-v40+v44','method':'combined'},'context_rules':{'version':'lanes-context-association-v42'},
              'projection':{'version':'ner-claim-projection-v1','code_sha256':sha(bindings)},
              'source_check':{'version':'source-ner-v1','code_sha256':sha(bindings)},
              'geography':{'scope':'metro_manila','psgc_sha256':hashlib.sha256(NATIONWIDE_PSGC_CSV.read_bytes()).hexdigest(),
                           'lookup_code_sha256':hashlib.sha256((services/'philippine_location_service.py').read_bytes()).hexdigest()}}
    return TrustedAssets(manifest,code,bindings,sha(manifest),Catalog(PhilippineLocationService(NATIONWIDE_PSGC_CSV)))


def make_case(trusted, text=BODY, labels=None, publication=None):
    source=NewsArticleExtractorInput(article_id=1,canonical_url='https://example.org/fictional-c2',publisher='fictional',
                                   title='Fictional source-bound fixture',article_text=text,published_at=NOW)
    snapshot,fingerprint=capture_native_input(source,publication_evidence=publication)
    version=SimpleNamespace(id=7,article_id=1,input_snapshot=snapshot,input_fingerprint=fingerprint)
    run=SimpleNamespace(id=11,article_version_id=7,mode='ner_rules_v1',pipeline_version=trusted.pipeline_version,
                        status='completed',completed_at=NOW)
    context=RunEvidence.from_records(run,version);request=context.source().runtime_request(fingerprint)
    labels=labels if labels is not None else [('Fictional Crescent','ROAD'),('Pasig City','CITY')]
    mentions=[]
    for name,label in labels:
        for match in re.finditer(re.escape(name),text):
            mentions.append(dict(id='pending',start=match.start(),end=match.end(),text=match.group(),label=label,
                provenance_sha256=object_sha({'bundle':trusted.provenance['bundle_sha256'],'tokenizer':trusted.provenance['tokenizer_sha256'],'text':request['text_sha256']})))
    mentions.sort(key=lambda m:(m['start'],m['end']))
    for i,m in enumerate(mentions):m['id']='m'+str(i)
    native=from_neural_mentions({**request,'mentions':mentions})
    inference={**native,'provenance':trusted.provenance,'measurements':{'extraction_seconds':.001,'peak_worker_rss_bytes':0}}
    result=build_native_result(context,inference,trusted,extracted_at=NOW)
    return run,version,context,inference,result


def test_exact_native_capture_and_legacy_fingerprints_are_independent():
    from app.services.news_discovery_service import extraction_input_snapshot
    article=NewsArticleExtractorInput(article_id=1,canonical_url='https://example.org/fiction',publisher='fiction',
        title='Original',article_text='  🌧️\nFictional Crescent was flooded.\n ',published_at=NOW.replace(tzinfo=None))
    old=extraction_input_snapshot(article)
    snapshot,fingerprint=capture_native_input(article)
    assert snapshot['article_text']==article.article_text and snapshot['publication_evidence']=={'raw':None,'timezone_known':False,'basis':'legacy_unknown'}
    assert fingerprint!=old[1] and extraction_input_snapshot(article)==old
    changed=article.model_copy(update={'article_id':22,'fetched_at':NOW})
    assert capture_native_input(changed)==(snapshot,fingerprint)
    assert capture_native_input(article.model_copy(update={'article_text':article.article_text+' '}))[1]!=fingerprint


@pytest.mark.parametrize('raw',['2026-10-20T11:00:00+08:00','Tue, 20 Oct 2026 11:00:00 +0800'])
def test_known_publication_provenance_is_exact(trusted,raw):
    pub=PublicationEvidence(raw=raw,timezone_known=True,basis='publisher_feed')
    *_,result=make_case(trusted,'Today at 10 AM PHT, Fictional Crescent in Pasig City was flooded knee-deep.',publication=pub)
    assert result.claims[0].event_time_resolved.isoformat()=='2026-10-20T10:00:00+08:00'
    assert result.projection['groups'][0]['normalizations']['time']['date_basis']=='publisher_feed_relative_date'


@pytest.mark.parametrize('raw',['2026-10-20 11:00:00','2026-10-19T11:00:00+08:00'])
def test_naive_or_different_publisher_clock_cannot_be_labeled_known(trusted,raw):
    with pytest.raises(NerEvidenceError,match='ner_input_binding_invalid'):
        make_case(trusted,publication=PublicationEvidence(raw=raw,timezone_known=True,basis='publisher_feed'))


def test_projection_and_source_check_accept_exact_ner_occurrence_without_old_recognizer(trusted,monkeypatch):
    text='  🌧️ '+BODY+'  '
    run,version,context,inference,result=make_case(trusted,text)
    assert len(result.claims)==1 and result.claims[0].confidence_score is None
    claim=result.claims[0]
    assert text[claim.place_char_start:claim.place_char_end]=='Fictional Crescent'
    assert claim.canonical_city=='City of Pasig' and claim.canonical_road is None
    from app.services import taglish_extraction_service as old
    original=old.extract_taglish_flood_facts(NewsArticleExtractorInput(article_id=1,**{k:v for k,v in version.input_snapshot.items() if k not in ('capture_schema','publication_evidence')}))
    assert not any(c.raw_place_name=='Fictional Crescent' for c in original.claims)
    monkeypatch.setattr(old,'extract_taglish_flood_facts',lambda *_:pytest.fail('Native checker reran old recognition'))
    audit=check_native_source(run,version,result,0,trusted,now=NOW)
    assert audit.outcome=='verified' and audit.prompt_version=='source-ner-v1'
    for fact in (audit.evidence.place,audit.evidence.status,audit.evidence.time,audit.evidence.depth,audit.evidence.access):
        for e in fact.evidence:assert text[e.start:e.end]==e.quote
    assert verify_saved_result(context,result,trusted).model_dump(mode='json')==result.model_dump(mode='json')
    assert parse_saved_result('ner_rules_v1',result).native.graph.model_dump(by_alias=True)==inference['graph']


@pytest.mark.parametrize('lead',['At 10 AM, ','Today at 10 AM PHT, ','On October 20, 2026 at 10 AM, '])
def test_unknown_day_or_timezone_remains_publication_ineligible(trusted,lead):
    run,version,_,_,result=make_case(trusted,lead+'Fictional Crescent in Pasig City was flooded knee-deep.')
    assert len(result.claims)==1 and result.claims[0].event_time_resolved is None
    check=check_native_source(run,version,result,0,trusted,now=NOW)
    assert check.outcome=='review' and check.reason_code=='missing_supported_observation_time'


@pytest.mark.parametrize('fragment',['will be flooded knee-deep','is not flooded','is flood-prone','had flooding last year',
    'was cleared of floodwater','has a flood-control prevention project'])
def test_non_observations_do_not_become_compatibility_claims(trusted,fragment):
    *_,result=make_case(trusted,LEAD+'Fictional Crescent in Pasig City '+fragment+'.')
    assert result.claims==[] and result.errors==[]
    assert result.projection['disposition'] in ('native_only','no_eligible_observations')
    assert len(result.projection['fact_accounting'])==len(result.native.graph.facts)


def test_caption_is_retained_but_never_an_observation(trusted):
    *_,result=make_case(trusted,'Photo: '+BODY)
    assert result.claims==[]
    assert any('photo_caption_only' in g['reasons'] for g in result.projection['groups'])


@pytest.mark.parametrize('text,labels,reason',[
    (LEAD+'Fictional Crescent and Sample Road in Pasig City were flooded knee-deep.',[('Fictional Crescent','ROAD'),('Sample Road','ROAD'),('Pasig City','CITY')],'joint_or_collective_requires_native_consumer'),
    (LEAD+'Fictional Pocket in Pasig City was flooded knee-deep.',[('Fictional Pocket','LOCAL_AREA'),('Pasig City','CITY')],'local_area_requires_native_consumer'),
    (LEAD+'Fictional Crescent was flooded knee-deep.',[('Fictional Crescent','ROAD')],'locality_not_supported'),
    (LEAD+'Fictional Crescent in Cebu City was flooded knee-deep.',[('Fictional Crescent','ROAD'),('Cebu City','CITY')],'non_metro_locality'),
    ('PASIG CITY — Fictional Crescent was flooded knee-deep.',[('Fictional Crescent','ROAD'),('PASIG CITY','CITY')],'locality_not_supported'),
])
def test_native_only_target_and_locality_reasons_are_explicit(trusted,text,labels,reason):
    *_,result=make_case(trusted,text,labels)
    assert result.claims==[] and any(reason in g['reasons'] for g in result.projection['groups'])


def test_repeated_names_remain_distinct_observations(trusted):
    text=BODY+'\nOn October 20, 2026 at 11 AM PHT, Fictional Crescent in Quezon City was flooded waist-deep.'
    *_,result=make_case(trusted,text,[('Fictional Crescent','ROAD'),('Pasig City','CITY'),('Quezon City','CITY')])
    assert len(result.claims)==2
    assert [c.canonical_city for c in result.claims]==['City of Pasig','Quezon City']
    assert [c.depth_canonical for c in result.claims]==['knee','waist']
    assert len({g['group_id'] for g in result.projection['groups']})==len(result.projection['groups'])


@pytest.mark.parametrize('phrase',['1 to 2 feet','up to 2 feet','above knee-deep'])
def test_non_point_measurements_keep_raw_evidence_without_scalar(trusted,phrase):
    *_,result=make_case(trusted,LEAD+'Fictional Crescent in Pasig City was flooded '+phrase+'.')
    assert len(result.claims)==1
    assert result.claims[0].depth_canonical is None and result.claims[0].depth_meters is None
    assert result.native.graph.facts
    assert 'depth_scalar_not_supported' in result.claims[0].uncertainty_reasons


@pytest.mark.parametrize('phrase,canonical,meters',[('8 inches (knee-deep)','gutter',.2032),('20 cm',None,.2),('knee-deep','knee',None)])
def test_bound_numeric_measurement_precedes_paired_gauge(trusted,phrase,canonical,meters):
    *_,result=make_case(trusted,LEAD+'Fictional Crescent in Pasig City was flooded '+phrase+'.')
    assert result.claims[0].depth_canonical==canonical
    assert result.claims[0].depth_meters==meters


@pytest.mark.parametrize('name,mutate',[
    ('body',lambda d:d['source'].__setitem__('text_sha256','a'*64)),
    ('manifest',lambda d:d['provenance']['manifest']['model'].__setitem__('bundle_sha256','a'*64)),
    ('mention',lambda d:d['native']['neural_mentions'][0].__setitem__('start',0)),
    ('effective',lambda d:d['native']['effective_mentions'][0].__setitem__('label','CITY')),
    ('proposal',lambda d:d['native']['proposals'].append({'invented':'repair'})),
    ('graph',lambda d:d['native']['graph']['facts'][0].__setitem__('value','waist-deep')),
    ('groups',lambda d:d['native']['groups'].clear()),
    ('projection',lambda d:d['projection']['groups'][0].__setitem__('group_id','g-forged')),
    ('claim',lambda d:d['claims'][0].__setitem__('condition','rising')),
    ('confidence',lambda d:d['claims'][0].__setitem__('confidence_score',1)),
])
def test_tampered_envelope_cannot_pass_source_consistency(trusted,name,mutate):
    run,version,context,_,result=make_case(trusted)
    data=result.model_dump(mode='json',by_alias=True);mutate(data)
    with pytest.raises(NerEvidenceError,match='ner_result_contract_invalid'):
        verify_saved_result(context,data,trusted)


def test_input_revision_and_mode_substitution_are_rejected(trusted):
    run,version,_,_,result=make_case(trusted)
    changed=deepcopy(version);changed.input_snapshot['article_text']+=' changed'
    with pytest.raises(NerEvidenceError,match='ner_input_binding_invalid'):check_native_source(run,changed,result,0,trusted,now=NOW)
    run.mode='rules_only'
    with pytest.raises(NerEvidenceError,match='ner_input_binding_invalid'):check_native_source(run,version,result,0,trusted,now=NOW)


def test_c1_inspection_fixture_is_readable_but_not_operational(trusted):
    from test_news_ner_method_boundary import native_fixture
    # Its marker is intentionally not the new capture contract; no SQL needed.
    run,version,_,_,_=make_case(trusted,'As of 10 AM, abot-tuhod ang baha sa Maybunga, Pasig City.',
        [('Maybunga','BARANGAY'),('Pasig City','CITY')])
    version.input_snapshot.pop('capture_schema');version.input_snapshot.pop('publication_evidence')
    version.input_fingerprint=sha(version.input_snapshot)
    old=native_fixture(version)
    assert parse_saved_result('ner_rules_v1',old).provenance['fixture']=='source_authored_not_inference'
    with pytest.raises(NerEvidenceError,match='ner_input_binding_invalid'):
        verify_saved_result(RunEvidence.from_records(run,version),old,trusted)


def test_missing_assets_fail_with_bounded_code(tmp_path,trusted):
    with pytest.raises(NerEvidenceError) as exc:
        load_trusted_assets(tmp_path,'a'*64,expected_worker_code_sha256=trusted.provenance['code_sha256'])
    assert str(exc.value)=='ner_assets_unavailable' and str(tmp_path) not in str(exc.value)


def test_native_source_identity_cannot_reuse_legacy_policy(trusted):
    from app.services.news_claim_auditor import NewsClaimAuditor,AuditorConfig
    legacy=NewsClaimAuditor(AuditorConfig(provider='source_rules',model='source-rules-v1')).policy_identity()
    assert source_policy_fingerprint(trusted)!=sha(legacy)
    assert source_policy_fingerprint(trusted,publication_policy=SimpleNamespace(fingerprint='other'))!=source_policy_fingerprint(trusted)


def test_stale_observation_is_review_only_even_if_source_is_consistent(trusted):
    run,version,_,_,result=make_case(trusted)
    check=check_native_source(run,version,result,0,trusted,now=NOW+timedelta(days=4))
    assert check.outcome=='review' and check.reason_code=='observation_outside_admission_window'


@pytest.mark.parametrize('role',['onset','observation','report','publication','recession','clearance','unspecified'])
def test_time_normalizer_preserves_roles_without_substitution(trusted,role):
    from app.services.news_ner_durable.fields import time_fields
    _,_,context,_,result=make_case(trusted)
    graph=result.native.graph.model_dump(mode='json',by_alias=True);original=sha(graph)
    times=deepcopy([f for f in graph['facts'] if f['kind']=='time'])
    for f in times:f['temporal_role']=role
    fields,details,_=time_fields(times,context.source(),graph)
    assert (fields['event_time_resolved'] is not None)==(role=='observation')
    assert fields['event_time_kind']==(role if role in ('observation','report','unspecified') else 'unspecified')
    assert sha(graph)==original and graph['absolute_instants']==[]


@pytest.mark.parametrize('lead',[
    'On February 30, 2026 at 10 AM PHT, ',
    'On October 20, 2026 at 10:75 AM PHT, ',
    'On October 20, 2026 at 10 AM UTC+09:00, ',
    'On October 20, 2026 at 10 AM UTC+08:30, ',
    'On October 20, 2026 at 10 AM and 11 AM PHT, ',
])
def test_invalid_or_conflicting_clocks_are_unresolved(trusted,lead):
    *_,result=make_case(trusted,lead+'Fictional Crescent in Pasig City was flooded knee-deep.')
    assert len(result.claims)==1 and result.claims[0].event_time_resolved is None


def test_yesterday_requires_real_publication_provenance_in_time_normalizer(trusted):
    from app.services.news_ner_durable.fields import time_fields
    text='Yesterday at 10 PM PHT, Fictional Crescent in Pasig City was flooded knee-deep.'
    pub=PublicationEvidence(raw=NOW.isoformat(),timezone_known=True,basis='publisher_feed')
    _,_,context,_,result=make_case(trusted,text,publication=pub)
    graph=result.native.graph.model_dump(mode='json',by_alias=True)
    times=deepcopy([f for f in graph['facts'] if f['kind']=='time'])
    for f in times:f['temporal_role']='observation'  # Role-unit fixture only; never replace the actual qualified graph.
    fields,details,_=time_fields(times,context.source(),graph)
    assert fields['event_time_resolved'].isoformat()=='2026-10-19T22:00:00+08:00'
    unknown=context.source().model_copy(update={'publication_evidence':PublicationEvidence()})
    assert time_fields(times,unknown,graph)[0]['event_time_resolved'] is None


def test_explicit_heading_is_bounded_and_does_not_cross_narrative(trusted):
    heading='Pasig City\nAs of 10 AM PHT on October 20, 2026, the following roads were affected by flooding:\n'
    labels=[('Pasig City','CITY'),('Fictional Crescent','ROAD'),('Sample Road','ROAD')]
    *_,good=make_case(trusted,heading+'Fictional Crescent: knee-deep\nSample Road: 20 cm',labels)
    assert len(good.claims)==2 and all(c.canonical_city=='City of Pasig' for c in good.claims)
    *_,bad=make_case(trusted,heading+'Fictional Crescent: knee-deep\nA separate narrative update follows.\nSample Road was flooded knee-deep.',labels)
    assert not any(c.raw_place_name=='Sample Road' for c in bad.claims)


def test_ambiguous_city_parent_is_not_selected_as_first_match(trusted):
    *_,result=make_case(trusted,LEAD+'Fictional Crescent in San Juan was flooded knee-deep.',
        [('Fictional Crescent','ROAD'),('San Juan','CITY')])
    assert not result.claims and any('locality_ambiguous' in g['reasons'] for g in result.projection['groups'])


def test_city_only_remains_observation_and_exact_same_time_summary_can_be_context(trusted):
    *_,only=make_case(trusted,LEAD+'Pasig City was flooded knee-deep.',[('Pasig City','CITY')])
    assert len(only.claims)==1 and only.claims[0].place_type=='city'
    *_,with_road=make_case(trusted,LEAD+'Pasig City was flooded knee-deep.\n'+BODY)
    assert len(with_road.claims)==1 and with_road.claims[0].place_type=='street'
    assert any(g['disposition']=='context_only' for g in with_road.projection['groups'])
    assert any(f['disposition']=='context_only' for f in with_road.projection['fact_accounting'])


@pytest.mark.parametrize('status',['was rising','was receding','had subsided'])
def test_changed_conditions_keep_status_and_do_not_reuse_onset_clock(trusted,status):
    *_,result=make_case(trusted,LEAD+'Fictional Crescent in Pasig City '+status+' as floodwater remained knee-deep.')
    assert result.claims and result.claims[0].condition in ('rising','receding','subsided')
    for f in result.native.graph.facts:
        if f.kind=='time' and f.temporal_role in ('recession','clearance'):
            assert result.claims[0].event_time_resolved is None


def test_mixed_status_updates_are_separate_even_when_they_reuse_target_anchor(trusted):
    text=BODY+'\nAt 11 AM PHT, the floodwater had subsided.'
    *_,result=make_case(trusted,text)
    assert [c.condition for c in result.claims]==['active','subsided']
    assert result.claims[1].depth_canonical is None
    assert result.claims[1].event_time_resolved is None


def test_evidence_and_claim_limits_retain_native_facts(trusted,monkeypatch):
    *_,large=make_case(trusted,LEAD+'Fictional Crescent in Pasig City '+('quiet '*700)+'was flooded knee-deep.')
    assert large.claims==[] and any('evidence_exceeds_legacy_contract' in g['reasons'] for g in large.projection['groups'])
    from app.services.news_ner_durable import projection
    assert projection.MAX_CLAIMS==500
    monkeypatch.setattr(projection,'MAX_CLAIMS',1)
    *_,limited=make_case(trusted,BODY+'\n'+BODY)
    assert len(limited.claims)==1 and any('legacy_projection_limit' in g['reasons'] for g in limited.projection['groups'])
    assert len(limited.projection['fact_accounting'])==len(limited.native.graph.facts)
    for group in limited.projection['groups']:
        if group['disposition']=='native_only':
            assert group['evidence_storage']=='native_graph' and not group['evidence']
            assert group['fact_ids'] and group['relation_ids']
            assert all(any(f.id==fact_id and f.evidence for f in limited.native.graph.facts) for fact_id in group['fact_ids'])


def test_placement_enrichment_is_hashed_without_becoming_geometry_confirmation(trusted):
    from app.services.news_claim_auditor import canonical_claim_sha256
    run,version,context,_,result=make_case(trusted)
    data=result.model_dump(mode='json',by_alias=True)
    data['claims'][0]['road_placement']={'status':'unresolved','reason':'fictional_unplaced_road'}
    enriched=verify_saved_result(context,data,trusted)
    assert canonical_claim_sha256(enriched.claims[0])!=canonical_claim_sha256(result.claims[0])
    check=check_native_source(run,version,enriched,0,trusted,now=NOW)
    assert check.outcome=='verified' and check.claim_sha256==canonical_claim_sha256(enriched.claims[0])
    assert enriched.claims[0].road_placement.may_affect_routing is False


@pytest.mark.parametrize('ordinal',[-1,True,999])
def test_invalid_claim_ordinal_is_bounded(trusted,ordinal):
    run,version,_,_,result=make_case(trusted)
    with pytest.raises(NerEvidenceError,match='ner_result_contract_invalid'):
        check_native_source(run,version,result,ordinal,trusted,now=NOW)


def test_actual_run_result_substitution_and_wrong_pipeline_are_rejected(trusted):
    run,version,context,_,result=make_case(trusted)
    run.result={'different':'saved artifact'}
    with pytest.raises(NerEvidenceError,match='ner_result_contract_invalid'):
        check_native_source(run,version,result,0,trusted,now=NOW)
    bad=context.model_copy(update={'pipeline_version':'ner-v1:'+'f'*64})
    with pytest.raises(NerEvidenceError,match='ner_configuration_invalid'):
        verify_saved_result(bad,result,trusted)


@pytest.mark.parametrize('prefix',['PASIG CITY, Philippines — ','PASIG CITY (Fixture) - '])
def test_wire_datelines_do_not_supply_missing_affected_parent(trusted,prefix):
    *_,result=make_case(trusted,prefix+'Fictional Crescent was flooded knee-deep.',
        [('Fictional Crescent','ROAD'),('PASIG CITY','CITY')])
    assert not result.claims


@pytest.mark.parametrize('zone',['PHT','(PHT)','UTC+08','UTC+08:00'])
def test_supported_explicit_observation_timezone_forms(trusted,zone):
    *_,result=make_case(trusted,'On October 20, 2026 at 10 AM '+zone+', Fictional Crescent in Pasig City was flooded knee-deep.')
    assert result.claims[0].event_time_resolved.isoformat()=='2026-10-20T10:00:00+08:00'


@pytest.mark.parametrize('access,expected',[('passable to all vehicles','passable_all'),
    ('not passable to light vehicles','light_vehicle_closed'),('passable with caution','passable_with_caution'),
    ('passable to motorcycles and cars','unknown')])
def test_access_only_uses_explicit_supported_vehicle_meaning(trusted,access,expected):
    *_,result=make_case(trusted,BODY.rstrip('.')+', '+access+'.')
    assert result.claims[0].road_passability==expected


def test_conflicting_measurements_keep_all_facts_without_choosing_one(trusted):
    *_,result=make_case(trusted,LEAD+'Fictional Crescent in Pasig City was flooded 1 foot and 2 feet.')
    assert result.claims[0].depth_meters is None and result.claims[0].depth_canonical is None
    assert len([f for f in result.native.graph.facts if f.kind=='depth'])==2


def test_graph_and_projection_are_deterministic_and_input_is_not_mutated(trusted):
    run,version,context,inference,result=make_case(trusted)
    before=sha(inference)
    repeated=build_native_result(context,inference,trusted,extracted_at=NOW)
    assert repeated.model_dump(mode='json')==result.model_dump(mode='json') and sha(inference)==before
    assert len({f['fact_id'] for f in result.projection['fact_accounting']})==len(result.native.graph.facts)


@pytest.mark.parametrize('clock',[None,NOW.replace(tzinfo=None)])
def test_invalid_checker_configuration_is_not_an_article_failure(trusted,clock):
    run,version,_,_,result=make_case(trusted)
    with pytest.raises(NerEvidenceError,match='ner_configuration_invalid'):
        check_native_source(run,version,result,0,trusted,now=clock)


def test_nonfinite_numeric_depth_is_preserved_without_nonfinite_json(trusted):
    *_,result=make_case(trusted,LEAD+'Fictional Crescent in Pasig City was flooded '+('9'*400)+' meters.')
    assert result.claims[0].depth_meters is None and result.claims[0].depth_canonical is None
    assert 'depth_scalar_not_supported' in result.claims[0].uncertainty_reasons
    json.dumps(result.model_dump(mode='json'),allow_nan=False)
