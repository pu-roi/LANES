"""Tribune-only authority, partial outcomes, immutable budget and ended history."""
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services import news_tribune_pilot as pilot
from app.services.news_tribune_budget import TribuneBudget, extend, effective_commitment
from app.services.news_pilot_budget import MODEL, LIMIT
from test_news_gma_inline_budget import setup as previous_setup
from test_news_gma_heading_budget import selection
from test_news_pilot_accounting import Objects


def grant_fixture(monkeypatch):
    from app.services.news_three_article_pilot import PilotAuthority
    from app.services.news_ner_durable.contracts import NativeInput
    import hashlib
    source = NativeInput.model_validate(dict(capture_schema='lanes-news-ner-input-v1',
        canonical_url='https://example.invalid/flood',publisher='fixture',title='Flood observation',
        excerpt='',article_text='A fixture street flooded on September 24.',published_at='2026-09-25T04:41:00+08:00',
        publication_evidence={'raw':'2026-09-25T04:41:00+08:00','timezone_known':True,'basis':'publisher_feed'})).model_dump(mode='json')
    digest=hashlib.sha256(source['article_text'].encode()).hexdigest()
    monkeypatch.setattr(pilot,'BODY',digest)
    monkeypatch.setattr('app.services.news_three_article_pilot.pilot_application_identity',lambda:'code')
    monkeypatch.setattr('app.services.news_historical_processing.database_identity',lambda e:'database')
    monkeypatch.setattr('app.services.news_history_authority.valid_shared_connection',lambda e:True)
    trusted=SimpleNamespace(validate=lambda:None,manifest={'qualified':'fixture'},pipeline_version='ner-v1:'+'a'*64)
    policy=dict(schema_version=pilot.VERSION,session_id=pilot.SESSION,dataset_id=pilot.DATASET,
        allowed_operations=['ner'],application_sha256='code',database_identity_sha256='database',
        confirmed_database='fixture',assets_sha256=sha(trusted.manifest),pipeline_version=trusted.pipeline_version,
        resource_profile='cloud-run-v1',live_publication_allowed=False,inputs=[dict(article_id=25,
            source_version_id=568,body_sha256=digest,native_input_fingerprint=sha(source),input_snapshot=source)])
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


def test_count_stage_reaches_tokenizer_without_generation_or_database_writes(monkeypatch):
    from unittest.mock import MagicMock, AsyncMock
    from scripts import run_news_tribune_pilot as stage
    from app.services import news_verified_cloud as cloud, news_pilot_accounting as accounting
    from app.services.news_three_article_pilot import PilotAuthority
    packet={'payload':{'fixture':'complete request'},'context':{}}
    release={'resolver':{}}
    policy=dict(schema_version=pilot.VERSION,release_sha256=sha(release),resolver={},receipts_prefix='private/fixture/',
        allowed_operations=['count'],budget_object='budget',run_id=390,result_sha256=sha({}),request_sha256s=[sha(packet['payload'])])
    monkeypatch.setenv('LANES_NEWS_RECEIPTS_PREFIX',policy['receipts_prefix'])
    class Store:
        def __init__(self,bucket,name): self.name=name
        def read(self): return (policy if self.name=='authority' else {'status':'stopped'}),'1'
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
    args=SimpleNamespace(authority_object='authority',authority_sha256=sha(policy),mode='tribune-count',run_id=[390])
    result=stage.run_tribune(args,release)
    assert result['status']=='completed' and result['provider_requests']==0
    assert calls==['count'] and tokenizer.await_count==1
    db.commit.assert_not_called()


def budget_fixture():
    from app.services.news_gma_inline_budget import InlineBudget
    from app.services.news_gma_inline_continuation import SESSION
    store, _, packet, old_policy, old_counts, objects = previous_setup()
    guard = InlineBudget(store, 'selection', policy=old_policy, counts=old_counts, journal=objects)
    store.state['status'] = 'ready'
    store.state['manual_resumptions'].append({'id':SESSION})
    key = guard.reserve(MODEL, packet, {})
    store.state['settlements'].append(dict(attempt_id=key, usage_estimate_nanodollars=3652700,
        policy_sha256=sha(old_policy), response_bundle_sha256=sha(key)))
    guard.finish(key, succeeded=True)
    store.state['status'] = 'stopped'
    packets, policy, counts = selection(pilot.SESSION, 800)
    policy['counts_sha256'] = sha(counts)
    old = deepcopy(store.state)
    journal = Objects()
    extend(store, policy, sha(old), journal)
    return store, old, packets, policy, counts, journal


def test_budget_preserves_42_attempts_and_forbids_resend():
    store, old, packets, policy, counts, journal = budget_fixture()
    assert effective_commitment(store.state, policy) == 752493700
    assert store.state['attempts'] == old['attempts']
    assert store.state['settlements'] == old['settlements']
    guard = TribuneBudget(store, 'selection', policy=policy, counts=counts, journal=journal)
    with pytest.raises(ResolutionError):
        guard.reserve(MODEL, packets[0], {})
    store.state['status'] = 'ready'
    store.state['manual_resumptions'].append({'id':pilot.SESSION})
    key = guard.reserve(MODEL, packets[0], {})
    assert len(store.state['attempts']) == 43
    with pytest.raises(ResolutionError):
        guard.reserve(MODEL, packets[1], {})
    guard.finish(key, succeeded=False)
    store.state['status'] = 'ready'
    with pytest.raises(ResolutionError):
        guard.reserve(MODEL, packets[0], {})


@pytest.mark.parametrize('field', ['attempt','settlement','counts','cap','session'])
def test_tampering_stops_before_new_reservation(field):
    store, _, packets, policy, counts, journal = budget_fixture()
    guard = TribuneBudget(store, 'selection', policy=policy, counts=counts, journal=journal)
    store.state['status'] = 'ready'
    store.state['manual_resumptions'].append({'id':pilot.SESSION})
    if field == 'attempt': store.state['attempts'][0]['reserved_nanodollars'] += 1
    if field == 'settlement': store.state['settlements'][0]['usage_estimate_nanodollars'] += 1
    if field == 'counts': guard.counts['requests'][0]['total_tokens'] += 1
    if field == 'cap': store.state['limit_nanodollars'] = LIMIT + 1
    if field == 'session': store.state['manual_resumptions'][-1]['id'] = 'other'
    with pytest.raises(ResolutionError): guard.reserve(MODEL, packets[0], {})
    assert len(store.state['attempts']) == 42


def test_qualified_claim_proceeds_while_cleared_and_undated_claims_remain_unresolved(monkeypatch):
    from app.services.news_ner_durable import assets, adapter, source_check
    from app.services import news_publication_service, news_estimated_road_service
    claim = lambda status, when: SimpleNamespace(condition=status, event_time_resolved=when,
        is_forecast=False, is_negated=False)
    when = datetime(2026,9,24,16,34,tzinfo=timezone.utc)
    result = SimpleNamespace(claims=[claim('active',when), claim('subsided',when), claim('active',None)],
        provenance={'llm_resolution':{}}, projection={'groups':[
            {'group_id':str(i),'claim_index':i,'reasons':[]} for i in range(3)]})
    version = SimpleNamespace()
    run = SimpleNamespace(article_version_id=1, result={})
    db = Mock(); db.get.side_effect = [run,version]; db.scalar.return_value = None
    authority = SimpleNamespace(trusted=None, policy={'resolver':{},'previewed_at':when.isoformat()}, validate_session=Mock())
    monkeypatch.setattr(assets,'with_resolution_assets',lambda *a:None)
    monkeypatch.setattr(adapter,'verify_saved_result',lambda *a:result)
    monkeypatch.setattr(pilot.RunEvidence,'from_records',lambda *a:None)
    monkeypatch.setattr(source_check,'check_native_sources',lambda *a,**k:{i:SimpleNamespace(outcome='verified') for i in range(3)})
    monkeypatch.setattr(news_publication_service,'_operational_zone_attributes',lambda *a:{})
    from shapely.geometry import mapping, box
    corridor = SimpleNamespace(geometry=mapping(box(121,14,121.001,14.001)),checksum='qualified',
        evidence=SimpleNamespace(model_dump=lambda **k:{}))
    builder = Mock(return_value=corridor)
    monkeypatch.setattr(news_estimated_road_service,'build_estimated_road_zone',builder)
    outputs, *_ = pilot.qualify(db,authority,7,())
    assert [o['outcome'] for o in outputs] == ['geometry_qualified','unresolved','unresolved']
    assert builder.call_count == 1


from test_operational_settings_postgres import isolated_db


def test_native_cleared_list_filters_before_pagination_and_keeps_saved_evidence(isolated_db):
    from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
    from app.crud.news_ner_results import list_native_result_rows
    db, _ = isolated_db
    now = datetime.now(timezone.utc)
    article = NewsArticle(canonical_url='https://example.invalid/context', publisher_source_id='fixture',
        title='Flood update', article_text='Floodwaters receded in Quezon City.', content_fingerprint='a'*64)
    db.add(article); db.flush()
    version = NewsArticleVersion(article_id=article.id, input_fingerprint='b'*64, input_snapshot=dict(
        article_text=article.article_text, title=article.title, publisher='fixture', published_at=now.isoformat()))
    db.add(version); db.flush()
    claims = [dict(raw_place_name=name, condition=condition) for name, condition in
        [('Quezon City','subsided'),('Road A','active'),('Road B','receding')]]
    result = dict(schema_version='lanes-news-ner-result-v1', processing_method='ner_rules_v1',
        extracted_at=now.isoformat(), claims=claims, read_projection=dict(version='ner-result-read-v1',
            groups=[dict(group_id='resolved-n'+str(i), claim_index=i) for i in range(3)]))
    pipeline = 'ner-v1:'+'c'*64
    run = NewsExtractionRun(article_version_id=version.id, pipeline_version=pipeline,
        mode='ner_rules_v1', status='completed', result=result, completed_at=now)
    db.add(run); db.commit()
    options = dict(pipeline_version=pipeline, page=1, page_size=1, search='', publisher=None,
        condition=None, placement=None, order='extraction_newest')
    first, total, page, publishers = list_native_result_rows(db, **options)
    assert total == 2 and page == 1 and publishers == ['fixture']
    assert first[0]['claim']['condition'] == 'active'
    second, total, page, _ = list_native_result_rows(db, **{**options, 'page':99})
    assert page == 2 and second[0]['claim']['condition'] == 'receding'
    assert list_native_result_rows(db, **{**options, 'condition':'subsided'})[1] == 0
    from app.crud.news_collection import native_collection_rows
    from sqlalchemy import select
    collection, _ = native_collection_rows(db, pipeline)
    assert db.execute(collection).one()[5] == 2
    assert db.get(NewsExtractionRun,run.id).result['claims'][0]['condition'] == 'subsided'


def test_tribune_history_waits_for_final_polygon_deactivation_and_gma_stays_hidden(isolated_db):
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
            demonstration_session_id=pilot.SESSION,label='Retained source road',article_id=25,article_version_id=568,
            run_id=1,group_id='n1',source_url='https://example.invalid/article',source_publisher='fixture',source_excerpt='source',
            occurrence_date='2026-09-24',precision='date',closure_basis='demo_administration',geometry_sha256='a'*64,
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
