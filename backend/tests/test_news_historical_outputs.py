"""Fictional complete lifecycle on disposable PostGIS and real geometry code."""
from copy import deepcopy
from datetime import timedelta
import hashlib
import httpx
from concurrent.futures import ThreadPoolExecutor

from geoalchemy2.shape import from_shape
import pytest
from shapely.geometry import mapping, shape, box
from sqlalchemy import event, func, select

from app import models
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimDecision, NewsClaimEvaluation
from app.services import news_historical_outputs as outputs
from app.services.news_historical_processing import HistoricalPackage
from app.services.news_ner_durable.contracts import RunEvidence, sha
from app.services.news_ner_durable.adapter import build_native_result
from app.services.news_ner.location_pipeline import from_neural_mentions
from app.services.news_estimated_road_service import build_estimated_road_zone
from app.services.news_historical_preparation import save_private_package
from app.crud.news_historical_processing import enqueue_historical_captures
from app.services.flood_event_service import deactivate_zone_and_end_event_if_final, build_flood_event_history_query, get_flood_event_planning_analytics, serialize_flood_event_planning_records
from app.services.spatial_browse_service import history_cards, planning_metrics, map_read, history_overview
from app.services.historical_news_metadata import DATASET, event_metadata
from app.services.flood_routing_policy import get_active_flood_zones
from app.services.report_service import get_active_floods
from app.services.news_zone_projection_service import zone_responses_with_news
from app.services.news_ner_durable.readers import read_native_group
from app.services.news_results_service import browse_news_results
from app.services.news_native_read_context import SavedNativeReadContext
from historical_processing_fixtures import fictional_documents
from test_news_historical_processing_postgres import isolation, SOURCES, c3b_db, trusted, NOW
from test_news_ner_durable import make_case
from test_news_placement_preview import service
from test_news_road_placement import write_catalog, ways

BODY = 'On October 20, 2026 at 10 AM PHT, Fictional Crescent in Pasig City was flooded knee-deep near Guazon Street.'
_HTTP_SEND = httpx.Client.send


@pytest.fixture
def prepared(c3b_db, trusted, tmp_path, request):
    variant = getattr(request, "param", "existing")
    body = BODY.replace(" at 10 AM PHT,", ",") if variant == "missing_date" else BODY
    from types import SimpleNamespace
    placement = service(tmp_path, city='City of Pasig')
    roads = ways(); roads[0]['name'] = 'Fictional Crescent'; roads[1]['name'] = 'Guazon Street'
    placement.roads = write_catalog(tmp_path/'roads', roads, cities=[dict(name='City of Pasig', relation_id=106569,
        boundary=mapping(box(120.99,14.60,121.03,14.67)))])
    _run, _version, _context, inference, result = make_case(trusted, body)
    assert result.claims, result.projection
    from app.services.news_historical_interpretation import historical_placement_claim
    adapted, _ = historical_placement_claim(result, result.projection['groups'][0]['group_id'])
    corridor = build_estimated_road_zone(adapted, service=placement)
    documents = fictional_documents(trusted, body)
    if variant.startswith('missing'):
        documents['inventory.json']['history'] = documents['inventory.json']['history'][:1]
    with c3b_db() as db, db.begin():
        for row in documents['inventory.json']['sources']:
            snapshot = row['input_snapshot']
            db.add(NewsArticle(id=row['article_id'], canonical_url=snapshot['canonical_url'], publisher_source_id='fictional',
                title=snapshot['title'], excerpt='', article_text=body, published_at=NOW, content_fingerprint='0'*64))
            db.flush()
            db.add(NewsArticleVersion(id=row['version_id'], article_id=row['article_id'], input_fingerprint=row['input_fingerprint'], input_snapshot=snapshot))
        db.flush()
        for row in documents['inventory.json']['history']:
            db.add(models.FloodEvent(id=row['event_id'], status=models.FloodEventStatus.ENDED,
                verified_at=NOW-timedelta(hours=3), ended_at=NOW, peak_severity=models.ReportSeverity.MEDIUM))
            db.flush()
            zone = models.FloodAvoidanceZone(id=row['zone_id'], event_id=row['event_id'], geometry=from_shape(shape(corridor.geometry), srid=4326), is_active=False)
            db.add(zone)
            db.add(NewsExtractionRun(id=row['run_id'], article_version_id=201+row['article_id']-101,
                pipeline_version='legacy-fictional', mode='rules_only', status='completed', completed_at=NOW,
                result={'claims': [row['claim']]}))
            db.flush()
            raw = db.scalar(select(func.encode(func.ST_AsEWKB(models.FloodAvoidanceZone.geometry), 'hex')).where(models.FloodAvoidanceZone.id==zone.id))
            row['geometry_sha256'] = hashlib.sha256(bytes.fromhex(raw)).hexdigest()
    # Rebuild the authenticated package with actual fictional original geometry bindings.
    from app.services.news_historical_preparation import build_preparation, SourceSpec
    specs = tuple(SourceSpec(i['article_id'], i['version_id'], i['input_fingerprint'], hashlib.sha256(body.encode()).hexdigest(),
        i['input_snapshot']['canonical_url'], 'fictional', NOW.isoformat()) for i in documents['inventory.json']['sources'])
    candidates = tuple((r['article_id'],r['run_id'],0,r['zone_id'],'primary' if i==0 else 'historical',
        'active_demo' if i==0 else 'historical_archive','Fictional Crescent','City of Pasig') for i,r in enumerate(documents['inventory.json']['history']))
    documents = build_preparation(documents['inventory.json'], documents['manifest.json']['assets'], specs=specs, candidates=candidates)
    package = HistoricalPackage(sha(documents['manifest.json']), documents)
    with c3b_db() as db, db.begin():
        ids = enqueue_historical_captures(db, package.captures, trusted.pipeline_version)
        for run in db.scalars(select(NewsExtractionRun).where(NewsExtractionRun.id.in_(ids))):
            version = db.get(NewsArticleVersion, run.article_version_id)
            context = RunEvidence.from_records(run, version)
            pure = from_neural_mentions({**context.source().runtime_request(context.input_fingerprint), 'mentions': inference['proposal']['neural_mentions']})
            result = build_native_result(context, {**pure, 'provenance': trusted.provenance, 'measurements': inference['measurements']}, trusted, extracted_at=NOW)
            run.status = 'completed'; run.completed_at = NOW; run.result = result.model_dump(mode='json', by_alias=True)
    engine = c3b_db.kw['bind']; policy=outputs.expected_output_policy(package, trusted, engine)
    options = dict(policy=policy, policy_sha256=sha(policy), confirmed_database=engine.url.database,
        environment='test', sources=SOURCES, placement_service=placement, now=NOW)
    return SimpleNamespace(factory=c3b_db,engine=engine,package=package,trusted=trusted,options=options,ids=ids)


def snapshot(h):
    with h.factory() as db:
        return [(r.id, deepcopy(r.result)) for r in db.scalars(select(NewsExtractionRun).order_by(NewsExtractionRun.id))]


def test_general_archive_reuses_confirmed_observation_across_articles(prepared):
    from app.services.news_historical_preparation import build_preparation, SourceSpec, text_sha
    h=prepared;before=snapshot(h)
    inventory=deepcopy(h.package.documents['inventory.json']);inventory['history']=[]
    specs=tuple(SourceSpec(r['article_id'],r['version_id'],r['input_fingerprint'],text_sha(r['input_snapshot']['article_text']),
        r['input_snapshot']['canonical_url'],r['input_snapshot']['publisher'],r['input_snapshot']['published_at'])
        for r in inventory['sources'])
    documents=build_preparation(inventory,h.package.manifest['assets'],specs=specs,candidates=(),dataset_id='general-archive-fixture')
    package=HistoricalPackage(sha(documents['manifest.json']),documents)
    policy=outputs.expected_output_policy(package,h.trusted,h.engine)
    assert 'selected_demo_lifecycle' not in policy['operations']
    options={**h.options,'policy':policy,'policy_sha256':sha(policy)}
    result=outputs.historical_outputs(h.engine,package,h.trusted,apply=True,**options)
    assert len({o['event_id'] for o in result['outputs']})==1
    assert result['outputs'][1]['reused_existing_event'] is True
    assert snapshot(h)==before
    with h.factory() as db:
        event_id=result['outputs'][0]['event_id']
        assert db.get(models.FloodEvent,event_id).status==models.FloodEventStatus.ENDED
        assert not any(db.scalars(select(models.FloodAvoidanceZone.is_active).where(models.FloodAvoidanceZone.event_id==event_id)))
        from app.services.spatial_browse_service import history_collection
        assert history_collection(db,event_id,'news_sources',1,dataset_id='general-archive-fixture').total==2


def test_cross_article_sessions_concurrently_reuse_one_archive(prepared,monkeypatch):
    from app.services.news_historical_preparation import build_preparation, SourceSpec, text_sha
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    h=prepared;packages=[]
    for index,row in enumerate(h.package.documents['inventory.json']['sources']):
        inventory=deepcopy(h.package.documents['inventory.json']);inventory['sources']=[row];inventory['history']=[]
        raw=row['input_snapshot']
        spec=SourceSpec(row['article_id'],row['version_id'],row['input_fingerprint'],text_sha(raw['article_text']),
            raw['canonical_url'],raw['publisher'],raw['published_at'])
        docs=build_preparation(inventory,h.package.manifest['assets'],specs=(spec,),candidates=(),dataset_id=f'concurrent-history-{index}')
        package=HistoricalPackage(sha(docs['manifest.json']),docs)
        policy=outputs.expected_output_policy(package,h.trusted,h.engine)
        packages.append((package,{**h.options,'policy':policy,'policy_sha256':sha(policy)}))
    ready=Barrier(2);qualify=outputs.qualify_outputs
    def together(*args,**kwargs):
        result=qualify(*args,**kwargs);ready.wait(timeout=20);return result
    monkeypatch.setattr(outputs,'qualify_outputs',together)
    def apply(item):
        package,options=item
        return outputs.historical_outputs(h.engine,package,h.trusted,apply=True,**options)
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts=list(pool.map(apply,packages))
    assert len({r['outputs'][0]['event_id'] for r in receipts})==1
    with h.factory() as db:
        event_id=receipts[0]['outputs'][0]['event_id']
        from app.services.spatial_browse_service import history_collection
        assert history_collection(db,event_id,'news_sources',1).total==2


def test_readonly_preflight_then_complete_saved_demo_archive_lifecycle(prepared):
    h=prepared; before=snapshot(h); statements=[]
    def record(_c,_u,s,_p,_context,_m): statements.append(s.strip())
    event.listen(h.engine, 'before_cursor_execute', record)
    try:
        preflight=outputs.historical_outputs(h.engine,h.package,h.trusted,**h.options)
    finally: event.remove(h.engine,'before_cursor_execute',record)
    assert statements[0]=='SET TRANSACTION READ ONLY'
    assert not any(s.split()[0].upper() in {'INSERT','UPDATE','DELETE'} for s in statements)
    assert [o['outcome'] for o in preflight['outputs']]==['geometry_qualified','geometry_qualified'],preflight
    applied=outputs.historical_outputs(h.engine,h.package,h.trusted,apply=True,**h.options)
    assert [o['outcome'] for o in applied['outputs']]==['saved','saved'],applied
    assert snapshot(h)==before
    demo, archive=applied['outputs']
    assert archive['event_id']==502 and demo['event_id'] not in (501,502)
    with h.factory() as db:
        assert db.scalar(select(func.count()).select_from(NewsClaimDecision))==0
        assert len(get_active_flood_zones(db))==0
        sync=get_active_floods(db)
        assert len(sync)==1 and sync[0]['affects_routing'] is False and sync[0]['historical']['disposition']=='active_demo'
        zones=list(db.scalars(select(models.FloodAvoidanceZone).where(models.FloodAvoidanceZone.id.in_(demo['zone_ids']))))
        assert zone_responses_with_news(db,zones)[0].historical.label.startswith('Historical demonstration')
        context=SavedNativeReadContext(h.trusted.pipeline_version,outputs.database_identity(h.engine))
        page=browse_news_results(db,page=1,page_size=12,search='',publisher=None,condition=None,placement=None,order='extraction_newest',processing_context=context)
        assert page.total==2
        assert read_native_group(db,demo['run_id'],demo['group_id'],{}).historical_outputs
        query=build_flood_event_history_query(db,dataset_id=DATASET)
        assert query.count()==2
        sql=planning_metrics(db,query); py=get_flood_event_planning_analytics(db,query.all())
        assert sql['total_events']==py['total_events']==1 and sql['duration']['ended_event_count']==py['duration']['ended_event_count']==0
        assert sql['events_over_time']==py['events_over_time']==[{'date':'2026-10-20','event_count':1}]
        assert history_overview(db,demo['event_id'])['historical']['disposition']=='active_demo'
        from app.services.spatial_browse_service import history_collection
        native_source=history_collection(db,demo['event_id'],'news_sources',1).items[0]
        assert native_source['run_id']==demo['run_id'] and native_source['group_id']==demo['group_id']
        assert native_source['claim_index']==demo['claim_index'] and native_source['depth_raw']
        for zone in zones: deactivate_zone_and_end_event_if_final(db,zone,occurred_at=NOW+timedelta(minutes=15))
        assert get_active_floods(db)==[]
        assert db.get(models.FloodEvent,demo['event_id']).status==models.FloodEventStatus.ENDED
        assert event_metadata(db,[demo['event_id']])[demo['event_id']].is_demo
        assert db.get(models.FloodEvent,501).status==models.FloodEventStatus.ENDED
    repeated=outputs.historical_outputs(h.engine,h.package,h.trusted,apply=True,**h.options)
    assert repeated['outputs']==applied['outputs'] and snapshot(h)==before
    with h.factory() as db: assert get_active_floods(db)==[]


def test_tampered_policy_and_shared_target_refused_before_write(prepared):
    h=prepared; original=snapshot(h)
    changed=deepcopy(h.options['policy']); changed['operations'].append('publish_live')
    with pytest.raises(ValueError,match='historical_output_policy_mismatch'):
        outputs.historical_outputs(h.engine,h.package,h.trusted,**{**h.options,'policy':changed,'policy_sha256':sha(changed)},apply=True)
    with pytest.raises(ValueError,match='historical_output_shared_release_not_qualified'):
        outputs.historical_outputs(h.engine,h.package,h.trusted,**{**h.options,'environment':'production'},apply=True)
    assert snapshot(h)==original


def test_concurrent_repeats_reuse_the_same_instances(prepared):
    h=prepared
    def apply(): return outputs.historical_outputs(h.engine,h.package,h.trusted,apply=True,**h.options)
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(lambda _:apply(),range(2)))
    assert results[0]['outputs']==results[1]['outputs']
    with h.factory() as db:
        assert db.scalar(select(func.count()).select_from(models.FloodEvent))==3
        assert db.scalar(select(func.count()).select_from(NewsClaimEvaluation))==2


def test_source_suppression_blocks_output_without_partial_writes(prepared):
    from app.models.setting import SystemSetting
    from app.schemas.configuration import OperationalSettings
    from app.services.configuration_service import CONFIG_KEY
    h=prepared
    config=OperationalSettings().model_dump(mode='json'); config['news_source_ids']=[]
    with h.factory() as db, db.begin(): db.add(SystemSetting(key=CONFIG_KEY,value={'revision':1,'settings':config}))
    with pytest.raises(ValueError,match='historical_source_not_selected_or_approved'):
        outputs.historical_outputs(h.engine,h.package,h.trusted,apply=True,**h.options)
    with h.factory() as db:
        assert db.scalar(select(func.count()).select_from(models.FloodEvent))==2
        assert db.scalar(select(func.count()).select_from(NewsClaimEvaluation))==0


def test_unavailable_geometry_is_saved_as_unresolved_and_browsable(prepared,monkeypatch):
    from app.crud.news_publication import NewsPublicationError
    from app.services import news_estimated_road_service
    h=prepared
    def unavailable(*args,**kwargs): raise NewsPublicationError('estimated_road_requires_noah_overlap')
    monkeypatch.setattr(news_estimated_road_service,'build_estimated_road_zone',unavailable)
    result=outputs.historical_outputs(h.engine,h.package,h.trusted,apply=True,**h.options)
    assert all(o['outcome']=='unresolved' and o['event_id'] is None for o in result['outputs'])
    with h.factory() as db:
        assert db.scalar(select(func.count()).select_from(models.FloodEvent))==2
        detail=read_native_group(db,h.ids[0],'g0',{})
        assert 'estimated_road_requires_noah_overlap' in detail.historical_outputs[0]['reasons']


def test_late_original_history_failure_rolls_back_demo_and_evaluations(prepared):
    h=prepared
    with h.factory() as db,db.begin():
        db.get(models.FloodAvoidanceZone,302).is_active=True
    with pytest.raises(ValueError,match='historical_original_history_changed'):
        outputs.historical_outputs(h.engine,h.package,h.trusted,apply=True,**h.options)
    with h.factory() as db:
        assert db.scalar(select(func.count()).select_from(models.FloodEvent))==2
        assert db.scalar(select(func.count()).select_from(NewsClaimEvaluation))==0
        assert db.scalar(select(func.count()).select_from(models.FloodEventTimelineEntry))==0


def test_geometry_disagreement_is_unresolved_in_preflight_and_apply(prepared, monkeypatch):
    from dataclasses import replace
    from shapely.affinity import translate
    from app.services import news_estimated_road_service
    h = prepared
    original_builder = news_estimated_road_service.build_estimated_road_zone
    def changed_geometry(*args, **kwargs):
        corridor = original_builder(*args, **kwargs)
        return replace(corridor, geometry=mapping(translate(shape(corridor.geometry), xoff=0.00001)))
    monkeypatch.setattr(news_estimated_road_service, 'build_estimated_road_zone', changed_geometry)
    before = snapshot(h)
    preflight = outputs.historical_outputs(h.engine, h.package, h.trusted, **h.options)
    assert preflight['outputs'][1]['outcome'] == 'unresolved'
    assert 'historical_geometry_disagreement' in preflight['outputs'][1]['reasons']
    assert snapshot(h) == before
    result = outputs.historical_outputs(h.engine, h.package, h.trusted, apply=True, **h.options)
    assert result['outputs'][1]['outcome'] == 'unresolved'
    with h.factory() as db:
        assert not event_metadata(db, [502])
        assert db.get(models.FloodEvent, 502).ended_at == NOW


def test_normal_zone_routing_is_preserved_alongside_demo(prepared):
    h=prepared
    result=outputs.historical_outputs(h.engine,h.package,h.trusted,apply=True,**h.options)
    with h.factory() as db,db.begin():
        db.add(models.FloodAvoidanceZone(id=901,geometry=from_shape(box(121,14.63,121.001,14.631),srid=4326),
            is_active=True,severity_override=models.ReportSeverity.HIGH))
    with h.factory() as db:
        assert [z.id for z in get_active_flood_zones(db)]==[901]
        sync=get_active_floods(db)
        assert len(sync)==2
        assert next(z for z in sync if z['id']==901)['routing_restrictions']['light']=='blocked'


def test_saved_read_configuration_is_pinned_and_independent_of_processing(prepared,tmp_path,monkeypatch):
    import json
    from app.services.news_native_read_context import configured_native_read_context
    from app.services.news_saved_run_service import SavedRunReadError
    h=prepared
    descriptor={'schema_version':'saved-native-read-context-v1','pipeline_version':h.trusted.pipeline_version,
        'database_identity_sha256':outputs.database_identity(h.engine)}
    path=tmp_path/'read.json';path.write_text(json.dumps(descriptor),encoding='utf-8')
    monkeypatch.setenv('LANES_NEWS_NATIVE_READ_CONTEXT',str(path));monkeypatch.setenv('LANES_NEWS_NATIVE_READ_CONTEXT_SHA256',sha(descriptor))
    with h.factory() as db: configured_native_read_context().validate(db)
    path.write_text(json.dumps({**descriptor,'pipeline_version':'ner-v1:'+'0'*64}),encoding='utf-8')
    with pytest.raises(SavedRunReadError,match='news_native_reader_unavailable'): configured_native_read_context()


@pytest.mark.parametrize('prepared',['missing','missing_date'],indirect=True)
def test_new_archive_dates_and_intervals_have_python_sql_export_parity(prepared,request):
    h=prepared
    result=outputs.historical_outputs(h.engine,h.package,h.trusted,apply=True,**h.options)
    archive=result['outputs'][1]
    assert archive['outcome']=='saved'
    with h.factory() as db:
        metadata=event_metadata(db,[archive['event_id']])[archive['event_id']]
        exact=metadata.precision=='instant'
        assert metadata.closure_basis==('assumed_two_hours' if exact else 'assumed_source_day_end')
        event=db.get(models.FloodEvent,archive['event_id'])
        assert event.status==models.FloodEventStatus.ENDED
        assert event.ended_at is not None
        if not exact:
            from zoneinfo import ZoneInfo
            assert event.ended_at.astimezone(ZoneInfo('Asia/Manila')).isoformat() == '2026-10-21T00:00:00+08:00'
            assert event.first_reported_at is None and metadata.simulated_interval_minutes is None
        query=build_flood_event_history_query(db,dataset_id=DATASET)
        sql=planning_metrics(db,query); py=get_flood_event_planning_analytics(db,query.all())
        assert sql['historical_intervals']==py['historical_intervals']=={'assumed_two_hour_events':int(exact),'unknown_endpoints':0}
        assert sql['duration']['ended_event_count']==py['duration']['ended_event_count']==0
        assert all(row['official_duration_minutes'] is None for row in serialize_flood_event_planning_records(db,query.all()))
        assert history_cards(db,{'dataset_id':DATASET},page=1,focus_event_id=None).total==2


def test_authenticated_http_deactivation_and_dataset_consistent_reads(prepared):
    from fastapi import HTTPException
    from fastapi.testclient import TestClient
    from app.api import deps
    from app.core.database import get_db
    from app.main import app
    h=prepared
    result=outputs.historical_outputs(h.engine,h.package,h.trusted,apply=True,**h.options)
    demo=result['outputs'][0]; zone_id=demo['zone_ids'][0]
    with h.factory() as db:
        role=models.Role(name='historical-test-admin',permissions={'map':'full'}); db.add(role); db.flush()
        user=models.User(username='historical-test-admin',email='historical@example.invalid',hashed_password='fictional',role_id=role.id)
        db.add(user);db.commit()
        overrides=dict(app.dependency_overrides)
        app.dependency_overrides[get_db]=lambda:db
        app.dependency_overrides[deps.get_current_active_admin]=lambda:user
        try:
            client=TestClient(app)
            # Keep external HTTP forbidden; only the in-process ASGI transport
            # uses the original client method for this authenticated API check.
            client.send = lambda request, **kwargs: _HTTP_SEND(client, request, **kwargs)
            prefix='/api/v1/admin/flood-events'
            overview=client.get(f'{prefix}/{demo["event_id"]}/inspection?dataset_id={DATASET}')
            assert overview.status_code==200 and overview.json()['historical']['disposition']=='active_demo'
            assert client.get(f'{prefix}/501/inspection?dataset_id={DATASET}').status_code==404
            assert client.get(f'{prefix}/{demo["event_id"]}/inspection?dataset_id=unknown').status_code==422
            response=client.patch(f'/api/v1/admin/zones/{zone_id}/deactivate')
            assert response.status_code==200 and response.json()['historical']['disposition']=='active_demo'
            assert response.json()['affects_routing'] is False and response.json()['is_active'] is False
            assert response.json()['reporter_role'] == 'News report'
            assert not client.get('/api/v1/reports/active-zones').json()
            assert client.get(f'{prefix}/{demo["event_id"]}/inspection?dataset_id={DATASET}').json()['status']=='ended'
            def denied(): raise HTTPException(403,'Staff access required')
            app.dependency_overrides[deps.get_current_active_admin]=denied
            assert client.patch(f'/api/v1/admin/zones/{zone_id}/deactivate').status_code==403
            assert client.get(f'{prefix}/{demo["event_id"]}/inspection?dataset_id={DATASET}').status_code==403
        finally:
            app.dependency_overrides.clear();app.dependency_overrides.update(overrides)


@pytest.mark.parametrize('prepared', ['missing_date'], indirect=True)
def test_unknown_endpoint_requires_retained_archive_lineage_and_safe_downgrade(prepared):
    from sqlalchemy import delete, text
    from sqlalchemy.exc import IntegrityError
    from test_news_ner_mode_schema import migrate
    h = prepared
    # The deferred rule rejects ordinary ended events at commit, after flush.
    with pytest.raises(IntegrityError, match='Ended events require an endpoint'):
        with h.factory() as db, db.begin():
            db.add(models.FloodEvent(status=models.FloodEventStatus.ENDED,
                verified_at=NOW, peak_severity=models.ReportSeverity.MEDIUM))
            db.flush()
    result = outputs.historical_outputs(h.engine, h.package, h.trusted, apply=True, **h.options)
    archive_id = result['outputs'][1]['event_id']
    # Exercise the previously approved unknown-endpoint exception independently
    # of the new default next-day archive assumption.
    with h.factory() as db, db.begin():
        db.get(models.FloodEvent, archive_id).ended_at = None
        lineage = db.scalar(select(models.FloodEventTimelineEntry).where(models.FloodEventTimelineEntry.event_id == archive_id))
        lineage.snapshot_json = {**lineage.snapshot_json, 'closure_basis': 'unknown'}
    with pytest.raises(IntegrityError, match='Ended events require an endpoint'):
        with h.factory() as db, db.begin():
            db.execute(delete(models.FloodEventTimelineEntry).where(
                models.FloodEventTimelineEntry.event_id == archive_id))
    with pytest.raises(IntegrityError, match='Ended events require an endpoint'):
        with h.factory() as db, db.begin():
            lineage = db.scalar(select(models.FloodEventTimelineEntry).where(
                models.FloodEventTimelineEntry.event_id == archive_id))
            lineage.snapshot_json = {**lineage.snapshot_json, 'disposition': 'active_demo'}
    # A supported exact start does not establish a missing clearance endpoint.
    with h.factory() as db, db.begin():
        lineage = db.scalar(select(models.FloodEventTimelineEntry).where(
            models.FloodEventTimelineEntry.event_id == archive_id))
        lineage.snapshot_json = {**lineage.snapshot_json, 'precision': 'instant',
            'observed_at': NOW.isoformat()}
    # Downgrade must fail transactionally rather than fabricate archive closure.
    with pytest.raises(IntegrityError):
        migrate(h.engine, 'e8a6f1c2d903', down=True)
    with h.factory() as db:
        assert db.scalar(text('SELECT version_num FROM alembic_version')) == 'f1a9c7e2b604'
        assert db.get(models.FloodEvent, archive_id).ended_at is None
    # On a compatible database both directions and repeated upgrade are safe.
    with h.factory() as db, db.begin():
        db.get(models.FloodEvent, archive_id).ended_at = NOW
    migrate(h.engine, 'e8a6f1c2d903', down=True)
    migrate(h.engine, 'f1a9c7e2b604')
    migrate(h.engine, 'f1a9c7e2b604')
    with h.factory() as db:
        assert db.scalar(text('SELECT version_num FROM alembic_version')) == 'f1a9c7e2b604'
