"""Retained article lineage and truthful news history, on owned PostGIS only."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from geoalchemy2.shape import from_shape
from shapely.geometry import box
from sqlalchemy import event as sql_event

from app import models
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimCase, NewsClaimSource, NewsClaimDecision, NewsClaimZoneLink
from app.crud.news_publication import reserve_decision_id
from app.services.news_history_evidence import event_projections
from app.services.spatial_browse_service import history_overview, history_collection, planning_metrics
from app.services.flood_event_service import build_flood_event_history_query, serialize_flood_event_planning_records, get_flood_event_planning_analytics
from test_operational_settings_postgres import isolated_db

NOW = datetime(2026, 10, 22, tzinfo=timezone.utc)
OBSERVED = datetime(2026, 9, 9, 0, 55, tzinfo=timezone.utc)


def saved_news(db, staff, *, public_state='expired', observed=OBSERVED, relation='created'):
    article = NewsArticle(canonical_url=f'https://example.org/history/{uuid4()}', publisher_source_id='fictional',
        title='Latest corrected article', content_fingerprint='a'*64)
    db.add(article); db.flush()
    version = NewsArticleVersion(article_id=article.id, input_fingerprint='b'*64,
        input_snapshot={'title':'Original morning article', 'publisher':'Fictional publisher',
            'canonical_url':article.canonical_url, 'published_at':OBSERVED.isoformat(), 'article_text':'Original full body.'})
    db.add(version); db.flush()
    run = NewsExtractionRun(article_version_id=version.id, pipeline_version='fixture', mode='rules_only',
        status='completed', completed_at=NOW, result={'claims':[{'canonical_road':'Original Road',
            'canonical_city':'Quezon City', 'depth_raw':'26 inches', 'depth_canonical':'tires',
            'road_passability':'unknown', 'condition':'flooded', 'evidence_sentence':'Original full body.'}]})
    case = NewsClaimCase(revision=2)
    incident = models.FloodEvent(status=models.FloodEventStatus.ENDED, first_reported_at=observed,
        verified_at=NOW-timedelta(days=8), ended_at=NOW, peak_severity=models.ReportSeverity.HIGH)
    db.add_all([run, case, incident]); db.flush()
    source=NewsClaimSource(case_id=case.id, extraction_run_id=run.id, claim_ordinal=0, claim_sha256='c'*64)
    zone=models.FloodAvoidanceZone(event_id=incident.id, geometry=from_shape(box(121,14.6,121.001,14.601), srid=4326), is_active=False)
    db.add_all([source, zone]); db.flush()
    decision=NewsClaimDecision(id=reserve_decision_id(db), case_id=case.id, revision=1, request_id=uuid4(),
        actor_kind='staff', actor_user_id=staff.id, operation='correct', public_state='active_zone',
        review_state='resolved', reason_code='fixture', observed_at=observed or OBSERVED,
        expires_at=OBSERVED+timedelta(hours=2), decided_at=NOW,
        snapshot={'claim_source_id':source.id, 'public':{'geometry_basis':'estimated_road_corridor'}})
    db.add(decision);db.flush()
    db.add(NewsClaimZoneLink(decision_id=decision.id, zone_id=zone.id, relation=relation))
    db.flush()
    if public_state == 'expired':
        db.add(NewsClaimDecision(id=reserve_decision_id(db),case_id=case.id,revision=2,request_id=uuid4(),
            actor_kind='staff',actor_user_id=staff.id,operation='expire',public_state='expired',
            review_state='resolved',reason_code='fixture',decided_at=NOW,
            snapshot={'claim_source_id':source.id}))
    if observed is None:
        from app.schemas.historical_news import HistoricalNewsMetadata
        metadata=HistoricalNewsMetadata(dataset_id='fixture-history',observation_key='d'*64,
            disposition='historical_archive',demonstration_session_id=str(uuid4()),label='Historical news',
            article_id=article.id,article_version_id=version.id,run_id=run.id,group_id='fixture-group',
            source_url=article.canonical_url,source_publisher='fictional',source_excerpt='Original full body.',
            precision='unknown',closure_basis='unknown',geometry_sha256='e'*64,assets_sha256='f'*64,
            input_fingerprint=version.input_fingerprint,result_sha256='a'*64,pipeline_version='fixture',imported_at=NOW)
        db.add(models.FloodEventTimelineEntry(event_id=incident.id,entry_type='historical_import',
            occurred_at=NOW,summary='Retained source',snapshot_json=metadata.model_dump(mode='json')))
    db.commit()
    return incident, zone, version, run


def test_expired_original_source_survives_corrected_article_and_inactive_zone(isolated_db):
    db, staff=isolated_db
    incident, zone, version, run=saved_news(db, staff)
    overview=history_overview(db,incident.id)
    assert overview['origin']=='news' and overview['news_article_count']==1
    assert overview['supporting_report_count']==0 and overview['reporter_count']==0
    assert overview['occurrence_date']=='2026-09-09' and overview['duration_minutes'] is None
    statements=[]
    def capture(_c,_u,s,_p,_ctx,_many): statements.append(s)
    sql_event.listen(db.connection(),'before_cursor_execute',capture)
    try:
        page=history_collection(db,incident.id,'news_sources',1)
    finally:
        sql_event.remove(db.connection(),'before_cursor_execute',capture)
    assert len(statements)<=3
    item=page.items[0]
    assert item['title']=='Original morning article' and item['article_version_id']==version.id and item['run_id']==run.id
    assert item['depth_raw']=='26 inches' and item['depth_normalized']=='tires' and item['passability']=='unknown'
    assert item['geometry_basis']=='estimated_road_corridor'
    assert not any(s.lstrip().startswith(('INSERT','UPDATE','DELETE')) for s in statements)
    zones=history_collection(db,incident.id,'zones',1)
    assert not zones.items[0]['is_active'] and zones.items[0]['news']==[]
    assert history_collection(db,incident.id,'reports',1).total==0
    query=build_flood_event_history_query(db,date_from=datetime(2026,9,1),date_to=datetime(2026,9,30))
    assert [e.id for e in query]==[incident.id]
    metrics=planning_metrics(db,query)
    python_metrics=get_flood_event_planning_analytics(db,[incident])
    assert metrics['events_over_time']==python_metrics['events_over_time']==[{'date':'2026-09-09','event_count':1}]
    assert metrics['duration']['ended_event_count']==python_metrics['duration']['ended_event_count']==0
    export=serialize_flood_event_planning_records(db,[incident])[0]
    assert export['occurrence_date']=='2026-09-09' and export['official_duration_minutes'] is None


def test_mixed_support_preserves_citizen_timing_and_unknown_is_not_citizen(isolated_db):
    db, staff=isolated_db
    incident, zone, _, _=saved_news(db,staff,public_state='active_zone',relation='supported')
    db.add(models.FloodReport(event_id=incident.id,zone_id=zone.id,user_id=staff.id,
        source=models.ReportSource.USER_REPORT,raw_text='Citizen evidence',severity=models.ReportSeverity.HIGH,
        status=models.ReportStatus.APPROVED))
    unknown=models.FloodEvent(status=models.FloodEventStatus.ACTIVE,verified_at=NOW,peak_severity=models.ReportSeverity.LOW)
    db.add(unknown);db.commit()
    projections=event_projections(db,[incident.id,unknown.id])
    assert projections[incident.id]['origin']=='mixed' and not projections[incident.id]['news_timing']
    assert projections[unknown.id]['origin']=='unknown'
    assert history_overview(db,incident.id)['duration_minutes']==8*24*60


def test_citizen_support_does_not_replace_news_origin_timing(isolated_db):
    db,staff=isolated_db
    incident,zone,_,_=saved_news(db,staff)
    report=models.FloodReport(event_id=incident.id,zone_id=zone.id,user_id=staff.id,
        source=models.ReportSource.USER_REPORT,raw_text='Later citizen support',severity=models.ReportSeverity.HIGH,
        status=models.ReportStatus.APPROVED,created_at=NOW)
    db.add(report);db.commit()
    value=history_overview(db,incident.id)
    assert value['origin']=='mixed' and value['occurrence_date']=='2026-09-09'
    assert value['duration_minutes'] is None
    # A durable originating report remains authoritative even if a news-created
    # zone was later attached and the report was subsequently soft-deleted.
    report.created_at=incident.first_reported_at;report.deleted_at=NOW;db.commit()
    assert history_overview(db,incident.id)['duration_minutes']==8*24*60
    report=db.query(models.FloodReport).filter_by(event_id=incident.id).one()
    report.deleted_at=NOW;db.commit()
    retained=event_projections(db,[incident.id])[incident.id]
    assert retained['origin']=='mixed' and not retained['news_timing']
    assert history_overview(db,incident.id)['duration_minutes']==8*24*60


def test_unknown_source_time_does_not_become_publication_or_administrative_date(isolated_db):
    db,staff=isolated_db
    incident,_,_,_=saved_news(db,staff,observed=None)
    value=history_overview(db,incident.id)
    assert value['observation_precision']=='unknown' and value['occurrence_date'] is None
    assert value['duration_minutes'] is None
    assert planning_metrics(db,build_flood_event_history_query(db))['events_over_time']==[{'date':'Unknown','event_count':1}]
