"""Philstar-only authority, partial outcomes, immutable budget and ended history."""
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services import news_philstar_pilot as pilot
from app.services.news_philstar_budget import PhilstarBudget, extend, effective_commitment
from app.services.news_pilot_budget import MODEL, LIMIT
from test_news_gma_heading_budget import selection
from test_news_pilot_accounting import Objects


def grant_fixture(monkeypatch):
    from app.services.news_three_article_pilot import PilotAuthority
    from app.services.news_ner_durable.contracts import NativeInput
    import hashlib
    source = NativeInput.model_validate(dict(capture_schema='lanes-news-ner-input-v1',
        canonical_url='https://example.invalid/flood',publisher='fixture',title='Flood observation',
        excerpt='',article_text='A fixture street flooded on September 9.',published_at='2026-09-09T17:03:00+08:00',
        publication_evidence={'raw':'2026-09-09T17:03:00+08:00','timezone_known':True,'basis':'publisher_feed'})).model_dump(mode='json')
    digest=hashlib.sha256(source['article_text'].encode()).hexdigest()
    monkeypatch.setattr(pilot,'BODY',digest)
    monkeypatch.setattr('app.services.news_three_article_pilot.pilot_application_identity',lambda:'code')
    monkeypatch.setattr('app.services.news_historical_processing.database_identity',lambda e:'database')
    monkeypatch.setattr('app.services.news_history_authority.valid_shared_connection',lambda e:True)
    trusted=SimpleNamespace(validate=lambda:None,manifest={'qualified':'fixture'},pipeline_version='ner-v1:'+'a'*64)
    policy=dict(schema_version=pilot.VERSION,session_id=pilot.SESSION,dataset_id=pilot.DATASET,
        allowed_operations=['ner'],application_sha256='code',database_identity_sha256='database',
        confirmed_database='fixture',assets_sha256=sha(trusted.manifest),pipeline_version=trusted.pipeline_version,
        resource_profile='cloud-run-v1',live_publication_allowed=False,inputs=[dict(article_id=274,
            source_version_id=573,body_sha256=digest,native_input_fingerprint=sha(source),input_snapshot=source)])
    return PilotAuthority(policy,sha(policy),trusted),SimpleNamespace(url=SimpleNamespace(database='fixture'))


def test_exact_single_article_authority_is_separate_from_gma(monkeypatch):
    authority,engine=grant_fixture(monkeypatch)
    authority.validate(engine)


@pytest.mark.parametrize('field,value',[
    ('schema_version','gma-source-repair-v1'),('session_id','other'),('dataset_id','other'),
    ('allowed_operations',['ner','resolve']),('allowed_operations',['archive']),
    ('application_sha256','other'),('database_identity_sha256','other'),('confirmed_database','other'),
    ('assets_sha256','other'),('pipeline_version','other'),('resource_profile','local-strict-v1'),
    ('live_publication_allowed',True),('inputs',[]),
])
def test_rehashed_broader_or_changed_authority_is_rejected(monkeypatch,field,value):
    authority,engine=grant_fixture(monkeypatch)
    authority.policy[field]=value
    from app.services.news_three_article_pilot import PilotAuthority
    changed=PilotAuthority(authority.policy,sha(authority.policy),authority.trusted)
    with pytest.raises((ResolutionError,ValueError)):
        changed.validate(engine)


@pytest.mark.parametrize('over_cap',[False,True])
def test_count_stage_reaches_tokenizer_without_generation_or_database_writes(monkeypatch, over_cap):
    from unittest.mock import MagicMock, AsyncMock
    from scripts import run_news_philstar_pilot as stage
    from app.services import news_verified_cloud as cloud, news_pilot_accounting as accounting
    from app.services.news_three_article_pilot import PilotAuthority
    packet={'payload':{'fixture':'complete request'},'context':{}}
    release={'resolver':{}}
    policy=dict(schema_version=pilot.VERSION,release_sha256=sha(release),resolver={},receipts_prefix='private/fixture/',
        allowed_operations=['count'],budget_cap_nanodollars=1_500_000_000,cap_approval=__import__('app.services.news_philstar_budget',fromlist=['CAP_APPROVAL']).CAP_APPROVAL,budget_object='budget',run_id=390,result_sha256=sha({}),request_sha256s=[sha(packet['payload'])])
    monkeypatch.setenv('LANES_NEWS_RECEIPTS_PREFIX',policy['receipts_prefix'])
    class Store:
        def __init__(self,bucket,name): self.name=name
        def read(self): return (policy if self.name=='authority' else {'status':'stopped','tribune_policy':{}}),'1'
    monkeypatch.setattr(stage,'GCSLedgerStore',Store)
    journal=Objects()
    monkeypatch.setattr(stage,'GCSReceiptStore',lambda prefix:journal)
    monkeypatch.setattr(cloud,'preflight',lambda *a,**k:None)
    monkeypatch.setattr(cloud,'assets_for_release',lambda r:None)
    resolver=SimpleNamespace(config=None,request_packets=lambda *a,**k:[packet])
    monkeypatch.setattr(cloud,'resolver_for_release',lambda r:resolver)
    engine=Mock();monkeypatch.setattr(stage,'create_engine',lambda *a,**k:engine)
    db=Mock();db.get.side_effect=[SimpleNamespace(article_version_id=568,result={}),SimpleNamespace()]
    session=MagicMock();session.__enter__.return_value=db
    monkeypatch.setattr(stage,'sessionmaker',lambda **k:lambda:session)
    monkeypatch.setattr(PilotAuthority,'validate',lambda *a:None)
    calls=[]
    def validate(self,db,run_ids=None,sources=None,*,operation='ner'):
        calls.append(operation)
    monkeypatch.setattr(PilotAuthority,'validate_session',validate)
    monkeypatch.setattr(stage.RunEvidence,'from_records',lambda *a:SimpleNamespace(source=lambda:None))
    monkeypatch.setattr('app.services.news_ner_durable.adapter.verify_saved_result',lambda *a:None)
    tokenizer=AsyncMock(return_value={'total_tokens':123})
    monkeypatch.setattr(accounting,'count_request',tokenizer)
    monkeypatch.setattr('app.services.news_tribune_budget.effective_commitment',lambda *a:768326100)
    monkeypatch.setattr('app.services.news_philstar_budget.schedule_floor',lambda *a,**k:dict(requires_token_count=not over_cap))
    args=SimpleNamespace(authority_object='authority',authority_sha256=sha(policy),mode='philstar-count',run_id=[390])
    if over_cap:
        with pytest.raises(ResolutionError,match='complete_schedule_over_cap'):
            stage.run_philstar(args,release)
        tokenizer.assert_not_awaited()
        db.commit.assert_not_called()
        return
    result=stage.run_philstar(args,release)
    assert result['status']=='completed' and result['provider_requests']==0
    assert calls==['count'] and tokenizer.await_count==1
    db.commit.assert_not_called()



def budget_fixture():
    from test_news_tribune_pilot import budget_fixture as old_fixture
    from test_news_pilot_budget import payload
    from app.services.news_tribune_budget import TribuneBudget, extend as previous_extend
    from app.services.news_tribune_pilot import SESSION as OLD_SESSION
    from app.services.news_pilot_accounting import reservation, accounting_policy
    store, old, _, _, _, _ = old_fixture()
    store.state = deepcopy(old)
    packets, policy, counts = selection(OLD_SESSION, 1800)
    fourth = payload(1803); packets.append(fourth)
    policy['request_sha256s'].append(sha(fourth))
    counts['requests'].append(dict(request_sha256=sha(fourth),total_tokens=6000,
        reserved_nanodollars=reservation(fourth,6000),model=MODEL,accounting_policy_sha256=sha(accounting_policy())))
    policy['counts_sha256']=sha(counts); objects=Objects()
    previous_extend(store,policy,sha(old),objects)
    guard=TribuneBudget(store,'selection',policy=policy,counts=counts,journal=objects)
    store.state['status']='ready';store.state['manual_resumptions'].append({'id':OLD_SESSION})
    for packet in packets:
        key=guard.reserve(MODEL,packet,{})
        store.state['settlements'].append(dict(attempt_id=key,usage_estimate_nanodollars=3958100,
            policy_sha256=sha(policy),response_bundle_sha256=sha(key)))
        guard.finish(key,succeeded=True)
    store.state['status']='stopped'; old=deepcopy(store.state)
    packets,policy,counts=selection(pilot.SESSION,2800);policy['counts_sha256']=sha(counts)
    from app.services.news_philstar_budget import APPROVED_LIMIT,CAP_APPROVAL
    policy.update(limit_nanodollars=APPROVED_LIMIT,cap_approval=deepcopy(CAP_APPROVAL))
    extend(store,policy,sha(old),objects)
    return store,old,packets,policy,counts,objects


def test_append_only_budget_preserves_all_46_attempts_and_rejects_repeat():
    store,old,packets,policy,counts,objects=budget_fixture()
    assert effective_commitment(store.state,policy)==768326100
    assert store.state['attempts']==old['attempts']
    assert store.state['settlements']==old['settlements']
    guard=PhilstarBudget(store,'selection',policy=policy,counts=counts,journal=objects)
    with pytest.raises(ResolutionError,match='stopped'):guard.reserve(MODEL,packets[0],{})
    store.state['status']='ready';store.state['manual_resumptions'].append({'id':pilot.SESSION})
    key=guard.reserve(MODEL,packets[0],{});guard.finish(key,succeeded=True)
    with pytest.raises(ResolutionError,match='already_dispatched'):guard.reserve(MODEL,packets[0],{})


def test_budget_tampering_and_complete_schedule_over_cap_fail_closed():
    store,old,packets,policy,counts,objects=budget_fixture()
    guard=PhilstarBudget(store,'selection',policy=policy,counts=counts,journal=objects)
    store.state['attempts'][0]['reserved_nanodollars']+=1
    with pytest.raises(ResolutionError,match='history_changed'):guard._read()
    store.state['attempts']=deepcopy(old['attempts'])
    store.state['status']='ready';store.state['manual_resumptions'].append({'id':pilot.SESSION})
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr('app.services.news_philstar_budget.effective_commitment',lambda *a:1_500_000_000)
        with pytest.raises(ResolutionError,match='schedule_exhausted'):guard.reserve(MODEL,packets[0],{})
    assert len(store.state['attempts'])==46


def test_active_philstar_events_wait_for_deactivation_in_history():
    from app.models.report import FloodEvent
    from app.services.news_tribune_pilot import pending_history_event
    sql=str(select(FloodEvent.id).where(pending_history_event()).compile(
        dialect=postgresql.dialect(),compile_kwargs={'literal_binds':True}))
    assert pilot.DATASET in sql and 'tribune-active-history-20260924-v1' in sql
    assert "!= 'ended'" in sql


def test_intersecting_candidate_estimates_remain_unresolved():
    def candidate(x):
        return dict(outcome='geometry_qualified',reasons=[],geometry={'type':'Polygon',
            'coordinates':[[[x,0],[x+1,0],[x+1,1],[x,1],[x,0]]]})
    outputs=[candidate(0),candidate(.5),candidate(5)]
    pilot.reject_candidate_overlaps(outputs)
    assert [x['outcome'] for x in outputs]==['unresolved','unresolved','geometry_qualified']
    assert outputs[0]['geometry'] is None and outputs[1]['geometry'] is None


def test_retained_response_replay_requires_exact_source_and_forbids_dispatch():
    from app.services.news_philstar_replay import PhilstarReplayBatchPlan,ZeroProviderBudget,VERSION
    manifest=dict(schema_version=VERSION,generation_requests_allowed=0,source_version_id=573,
        body_sha256=pilot.BODY,batch_sizes=[4,2],bundle_sha256s=['a'*64,'b'*64],targets_sha256=sha(list(range(6))))
    plan=PhilstarReplayBatchPlan(manifest)
    assert plan.batches(list(range(6)))==[list(range(4)),[4,5]]
    with pytest.raises(ResolutionError,match='targets_changed'):plan.batches(list(range(5)))
    manifest['source_version_id']=569
    with pytest.raises(ResolutionError,match='manifest_invalid'):PhilstarReplayBatchPlan(manifest)
    with pytest.raises(ResolutionError,match='provider_forbidden'):ZeroProviderBudget().reserve()


from test_operational_settings_postgres import isolated_db

def test_philstar_history_waits_for_final_polygon_deactivation_and_gma_stays_hidden(isolated_db):
    from app.models.report import FloodEvent, FloodAvoidanceZone, FloodEventTimelineEntry
    from app.services.flood_event_service import build_flood_event_history_query, deactivate_zone_and_end_event_if_final
    from app.services.spatial_browse_service import require_event
    from app.services.historical_news_metadata import HistoricalNewsMetadata, ENTRY
    from fastapi import HTTPException
    from geoalchemy2.shape import from_shape
    from shapely.geometry import box
    from app.services.news_gma_active_outputs import DATASET as GMA
    db,_ = isolated_db
    now = datetime.now(timezone.utc)
    events = [FloodEvent(status='active',verified_at=now,peak_severity='low') for _ in range(2)]
    db.add_all(events); db.flush()
    for event,dataset in zip(events,[pilot.DATASET,GMA]):
        meta = HistoricalNewsMetadata(dataset_id=dataset,observation_key='a'*64,disposition='active_demo',
            demonstration_session_id=pilot.SESSION,label='Retained source road',article_id=274,article_version_id=573,
            run_id=1,group_id='n1',source_url='https://example.invalid/article',source_publisher='fixture',source_excerpt='source',
            occurrence_date='2026-09-09',precision='date',closure_basis='demo_administration',geometry_sha256='a'*64,
            assets_sha256='b'*64,input_fingerprint='c'*64,result_sha256='d'*64,pipeline_version='ner-v1:'+'e'*64,imported_at=now)
        db.add(FloodEventTimelineEntry(event_id=event.id,entry_type=ENTRY,occurred_at=now,summary='source',snapshot_json=meta.model_dump(mode='json')))
    zones = [FloodAvoidanceZone(event_id=events[0].id,is_active=True,severity_override='low',
        geometry=from_shape(box(121+i*.01,14,121.001+i*.01,14.001),srid=4326)) for i in range(2)]
    db.add_all(zones); db.commit()
    assert build_flood_event_history_query(db).count() == 0
    with pytest.raises(HTTPException) as error: require_event(db,events[0].id)
    assert error.value.status_code == 404
    deactivate_zone_and_end_event_if_final(db,zones[0],now)
    assert build_flood_event_history_query(db).count() == 0
    deactivate_zone_and_end_event_if_final(db,zones[1],now)
    assert [e.id for e in build_flood_event_history_query(db)] == [events[0].id]
    assert require_event(db,events[0].id).ended_at is not None
    events[1].status='ended'; events[1].ended_at=now; db.commit()
    assert [e.id for e in build_flood_event_history_query(db)] == [events[0].id]
    from app.services.flood_routing_policy import get_active_flood_zones
    assert get_active_flood_zones(db) == []


def test_complete_schedule_over_cap_stops_before_token_count(monkeypatch):
    from app.services.news_philstar_budget import schedule_floor
    from test_news_pilot_budget import payload
    import hashlib,json
    body='Fixture full article: flooded road at 4:30 p.m.'
    monkeypatch.setattr(pilot,'BODY',hashlib.sha256(body.encode()).hexdigest())
    packets=[]
    for i in range(16):
        value=payload(i)
        value['contents']=[{'parts':[{'text':json.dumps({'evidence_text':body,'targets':[{'id':str(i)}]})}]}]
        packets.append({'payload':value})
    gate=schedule_floor(packets,768326100)
    assert gate['minimum_cumulative_nanodollars']>1_000_000_000
    assert not gate['requires_token_count'] and not gate['generation_authorized']
    assert schedule_floor(packets[:1],768326100)['requires_token_count']
    value=json.loads(packets[0]['payload']['contents'][0]['parts'][0]['text']);value['targets']=[{}]*5
    packets[0]['payload']['contents'][0]['parts'][0]['text']=json.dumps(value)
    with pytest.raises(ResolutionError,match='source_or_batch_changed'):schedule_floor(packets,768326100)


def test_new_cap_is_source_scoped_and_preserves_historical_root_limit():
    from app.services.news_philstar_budget import APPROVED_LIMIT,CAP_APPROVAL
    from app.services.news_pilot_budget import LIMIT as historical_limit
    store,old,_,policy,_,_=budget_fixture()
    assert historical_limit==1_000_000_000
    assert store.state['limit_nanodollars']==old['limit_nanodollars']==historical_limit
    assert policy['limit_nanodollars']==APPROVED_LIMIT==1_500_000_000
    assert policy['cap_approval']==CAP_APPROVAL
    policy['limit_nanodollars']+=1
    with pytest.raises(ResolutionError,match='history_changed'):effective_commitment(store.state,policy)


@pytest.mark.parametrize('text,expected',[
 ('Impassable to all types of vehicles',True),('Impassable to all vehicles',True),
 ('Impassable to all kinds of vehicles',True),('Impassable to light vehicles',False),
 ('Passable to all types of vehicles',False),('Passable with caution',False)])
def test_exact_all_vehicle_closure_heading(text,expected):
    from app.services.news_ner_durable.resolution import _access_supported
    from app.schemas.news_audit import AuditEvidenceSpan
    assert _access_supported('impassable_all',(AuditEvidenceSpan(start=0,end=len(text),quote=text),)) is expected


def test_source_bound_replay_preserves_caution_and_excludes_caption(monkeypatch):
    from app.services.news_philstar_replay import source_rows
    from app.services.news_ner_durable.resolution import ResolvedMention
    import hashlib
    body='Caption road flooded.\nMANILA, Philippines reported flooding.\nPassable with caution\nRoad X - gutter deep'
    monkeypatch.setattr('app.services.news_philstar_replay.BODY',hashlib.sha256(body.encode()).hexdigest())
    base=dict(target_id='r',verdict='observed',city='Manila',barangay=None,place_evidence=(3,),status='active',
        historical=False,contradictory=False,status_evidence=(1,3),time_role='unknown',date_text=None,
        clock_text=None,contemporaneous=True,time_evidence=(),depth_text=None,depth_scope='unknown',
        depth_evidence=(),access='passable_unspecified',access_evidence=(2,3),road_section=None,section_evidence=())
    row=ResolvedMention(**base);doc=dict(evidence_text=body,targets=[dict(id='r',text='Road X',start=body.index('Road X'),end=len(body))])
    fixed,proof=source_rows((row,),doc,[])
    assert fixed[0].access=='passable_with_caution' and row.access=='passable_unspecified'
    assert proof[0]['reason']=='retain_cited_caution_heading'
    doc['targets'][0].update(start=0,end=12)
    fixed,proof=source_rows((row,),doc,[])
    assert fixed[0].verdict=='unsupported' and row.verdict=='observed'
    assert proof[0]['reason']=='photo_caption_only'


@pytest.mark.parametrize('cited,expected',[(True,'Road X cor. Street Y'),(False,'Road X')])
def test_replay_retains_only_own_cited_intersection(monkeypatch,cited,expected):
    from app.services.news_philstar_replay import source_rows
    from app.services.news_ner_durable.resolution import ResolvedMention,quote_options
    import hashlib
    body='MANILA, Philippines reported flooding.\nRoad X cor. Street Y - knee deep\nRoad Z cor. Street W - gutter deep'
    monkeypatch.setattr('app.services.news_philstar_replay.BODY',hashlib.sha256(body.encode()).hexdigest())
    options=quote_options(body)
    own=next(i for i,v in enumerate(options) if v['quote'].startswith('Road X'))
    other=next(i for i,v in enumerate(options) if v['quote'].startswith('Road Z'))
    row=ResolvedMention(target_id='r',verdict='observed',city='Quezon City',barangay=None,
        place_evidence=(own,),status='active',historical=False,contradictory=False,
        status_evidence=(own,),time_role='unknown',date_text=None,clock_text=None,
        contemporaneous=True,time_evidence=(),depth_text=None,depth_scope='unknown',depth_evidence=(),
        access='unknown',access_evidence=(),road_section='Road X',section_evidence=(own if cited else other,))
    start=body.index('Road X');doc=dict(evidence_text=body,targets=[dict(id='r',text='Road X',start=start,end=start+6)])
    fixed,proof=source_rows((row,),doc,[])
    assert fixed[0].road_section==expected and row.road_section=='Road X'
    assert bool(proof) is cited
