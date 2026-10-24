"""Source-bound Tribune processing and active-to-history output policy.

This opt-in policy never changes scheduled ingestion or the frozen GMA grants.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any
from zoneinfo import ZoneInfo

from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.report import FloodEvent, FloodAvoidanceZone, FloodEventTimelineEntry as Timeline
from app.services.news_ner_durable.contracts import NativeInput, RunEvidence, sha
from app.services.news_ner_durable.resolution import ResolutionError

VERSION = 'tribune-saved-article-pilot-v1'
DATASET = 'tribune-active-history-20260924-v1'
SESSION = 'tribune-pilot-20261024-v1'
BODY = 'dc4773d602277a22fb0660705e21eb45f64125f4bd8167cd55ad21ec3350bc0f'


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ResolutionError(reason)


def pending_history_event(event_column: Any = None) -> Any:
    """Only this session's still-active events wait outside unified history."""
    from app.services.historical_news_metadata import ENTRY
    column = FloodEvent.id if event_column is None else event_column
    return select(Timeline.id).where(
        Timeline.event_id == column, Timeline.entry_type == ENTRY,
        Timeline.snapshot_json['schema_version'].as_string() == 'historical-import-v1',
        Timeline.snapshot_json['dataset_id'].as_string() == DATASET,
        Timeline.snapshot_json['disposition'].as_string() == 'active_demo',
    ).correlate_except(Timeline).exists() & (FloodEvent.status != 'ended')


def validate_authority(authority: Any, engine: Any) -> None:
    from app.services.news_three_article_pilot import pilot_application_identity
    from app.services.news_historical_processing import database_identity
    from app.services.news_history_authority import valid_shared_connection
    p = authority.policy
    authority.trusted.validate()
    require(sha(p) == authority.policy_sha256 and p.get('schema_version') == VERSION
        and p.get('session_id') == SESSION and p.get('dataset_id') == DATASET
        and p.get('allowed_operations') in (['ner'], ['count'], ['resolve'], ['outputs'])
        and p.get('application_sha256') == pilot_application_identity()
        and p.get('database_identity_sha256') == database_identity(engine)
        and p.get('confirmed_database') == engine.url.database and valid_shared_connection(engine)
        and p.get('assets_sha256') == sha(authority.trusted.manifest)
        and p.get('pipeline_version') == authority.trusted.pipeline_version
        and p.get('resource_profile') == 'cloud-run-v1'
        and p.get('live_publication_allowed') is False, 'tribune_authority_invalid')
    if 'output_group_ids' in p:
        from app.services.news_tribune_replay import SHARED_TIME_REVIEW
        require(p['allowed_operations'] == ['outputs']
            and p['output_group_ids'] == ['resolved-n5', 'resolved-n7']
            and p.get('shared_time_review') == SHARED_TIME_REVIEW,
            'tribune_output_selection_invalid')
    inputs = p.get('inputs', [])
    require(len(inputs) == 1 and inputs[0].get('article_id') == 25
        and inputs[0].get('source_version_id') == 568
        and inputs[0].get('body_sha256') == BODY, 'tribune_source_selection_invalid')
    source = NativeInput.model_validate(inputs[0]['input_snapshot'])
    require(sha(inputs[0]['input_snapshot']) == inputs[0]['native_input_fingerprint']
        and hashlib.sha256(source.article_text.encode()).hexdigest() == BODY,
        'tribune_source_changed')


def validate_session(authority: Any, db: Session, run_ids: tuple | None,
                     sources: tuple | None, operation: str) -> None:
    from app.services.configuration_service import read_configuration, selected_news_sources
    from app.services.news_evaluation_service import source_is_approved
    from app.services.news_source_read_service import require_current_pilot_capture
    authority.validate(db.get_bind())
    p = authority.policy
    require(p['allowed_operations'] == [operation], 'tribune_operation_not_authorized')
    require(db.scalar(text('SELECT version_num FROM alembic_version')) == 'f1a9c7e2b604'
        and bool(db.scalar(text('SELECT postgis_version()'))), 'tribune_storage_changed')
    config = read_configuration(db)
    require(all(getattr(config, k) is False for k in ('news_collection_enabled', 'news_processing_enabled',
        'news_publication_enabled', 'automatic_expiry_enabled', 'pasig_ml_expiry_enabled')),
        'tribune_paused_configuration_changed')
    item = p['inputs'][0]
    original = db.get(NewsArticleVersion, 568)
    require(original is not None and original.article_id == 25
        and original.input_fingerprint == item['source_input_fingerprint']
        and sha(original.input_snapshot) == item['source_input_fingerprint']
        and original.input_snapshot['article_text'] == item['input_snapshot']['article_text'],
        'tribune_original_changed')
    require_current_pilot_capture(db, original)
    source = NativeInput.model_validate(item['input_snapshot'])
    from app.schemas.news_extraction import NewsArticleExtractorInput
    article = NewsArticleExtractorInput(article_id=25,
        **source.model_dump(exclude={'capture_schema', 'publication_evidence'}))
    require(source_is_approved(article, selected_news_sources(db, sources)), 'tribune_source_suppressed')
    if run_ids is None:
        return
    require(len(run_ids) == 1, 'tribune_one_run_required')
    run = db.get(NewsExtractionRun, run_ids[0])
    version = db.get(NewsArticleVersion, run.article_version_id) if run else None
    pipeline = (p['resolved_pipeline_version'] if operation == 'outputs' else
        p.get('parent_pipeline_version', p['pipeline_version']))
    require(run is not None and version is not None and version.article_id == 25
        and version.input_snapshot == item['input_snapshot']
        and version.input_fingerprint == item['native_input_fingerprint']
        and run.mode == 'ner_rules_v1' and run.pipeline_version == pipeline,
        'tribune_run_changed')
    if operation != 'ner':
        require(run.status == 'completed' and run.id == p.get('run_id')
            and sha(run.result) == p.get('result_sha256'), 'tribune_result_changed')


def qualify(db: Session, authority: Any, run_id: int, sources: tuple,
            placement_service: Any = None) -> tuple:
    from app.services.news_ner_durable.assets import with_resolution_assets
    from app.services.news_ner_durable.adapter import verify_saved_result
    from app.services.news_ner_durable.source_check import check_native_sources
    from app.services.news_publication_service import _operational_zone_attributes
    from app.services.news_estimated_road_service import build_estimated_road_zone
    from app.crud.news_publication import NewsPublicationError
    authority.validate_session(db, (run_id,), sources, operation='outputs')
    run = db.get(NewsExtractionRun, run_id)
    version = db.get(NewsArticleVersion, run.article_version_id)
    trusted = with_resolution_assets(authority.trusted, authority.policy['resolver'])
    result = verify_saved_result(RunEvidence.from_records(run, version), run.result, trusted)
    require('llm_resolution' in result.provenance, 'tribune_gemini_result_required')
    projected = [g for g in result.projection['groups'] if g['claim_index'] is not None]
    audits = check_native_sources(run, version, run.result, tuple(g['claim_index'] for g in projected),
        trusted, now=datetime.fromisoformat(authority.policy['previewed_at']))
    outputs = []
    for group in result.projection['groups']:
        if ('output_group_ids' in authority.policy
                and group['group_id'] not in authority.policy['output_group_ids']):
            continue
        item = dict(group_id=group['group_id'], claim_index=group['claim_index'],
            outcome='unresolved', reasons=list(group.get('reasons', [])), geometry=None)
        if group['claim_index'] is None:
            outputs.append(item)
            continue
        claim = result.claims[group['claim_index']]
        audit = audits[group['claim_index']]
        try:
            require(claim.condition == 'active' and not claim.is_forecast and not claim.is_negated,
                'tribune_not_reported_flooded')
            require(claim.event_time_resolved is not None
                and claim.event_time_resolved.date().isoformat() == '2026-09-24', 'tribune_observation_date_unresolved')
            require(audit.outcome == 'verified', 'tribune_source_audit_unresolved')
            attributes = _operational_zone_attributes(claim, audit)
            corridor = build_estimated_road_zone(claim, service=placement_service)
            geometry = shape(corridor.geometry)
            require(db.scalar(select(FloodAvoidanceZone.id).where(FloodAvoidanceZone.is_active.is_(True),
                func.ST_Intersects(FloodAvoidanceZone.geometry, from_shape(geometry, srid=4326))).limit(1)) is None,
                'tribune_existing_active_overlap')
            item.update(outcome='geometry_qualified', geometry=corridor.geometry,
                geometry_evidence=corridor.evidence.model_dump(mode='json'), geometry_checksum=corridor.checksum,
                zone_attributes={k:getattr(v, 'value', v) for k,v in attributes.items()})
        except (ResolutionError, NewsPublicationError) as exc:
            item['reasons'].append(exc.code if isinstance(exc, ResolutionError) else str(exc))
        outputs.append(item)
    return outputs, run, version, result, trusted


def outputs(engine: Any, authority: Any, run_id: int, sources: tuple, *,
            apply: bool = False, placement_service: Any = None) -> dict:
    from app.services.historical_news_metadata import ENTRY, HistoricalNewsMetadata
    from app.services.news_history_protection import protected_fingerprints, verify_protected
    from app.services.flood_event_service import record_event_locations
    from app.models.report import FloodEventLocationType as Location
    with Session(engine) as db, db.begin():
        db.execute(text("SET LOCAL lock_timeout='30000'"))
        if not apply:
            db.execute(text('SET TRANSACTION READ ONLY'))
        else:
            db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key':int(sha(SESSION)[:15],16)})
            db.execute(text('LOCK TABLE flood_events, flood_avoidance_zones IN SHARE ROW EXCLUSIVE MODE'))
        authority.validate_session(db, (run_id,), sources, operation='outputs')
        saved = list(db.scalars(select(Timeline).where(Timeline.entry_type == 'news_tribune_pilot_output',
            Timeline.snapshot_json['session_id'].as_string() == SESSION)))
        if 'output_group_ids' in authority.policy:
            saved = [t for t in saved if t.snapshot_json.get('group_id') in authority.policy['output_group_ids']]
        if saved:
            require(all(t.snapshot_json['result_sha256'] == authority.policy['result_sha256']
                and t.snapshot_json['outputs_sha256'] == authority.policy.get('outputs_sha256') for t in saved),
                'tribune_existing_output_changed')
            if 'output_group_ids' in authority.policy:
                require(sorted(t.snapshot_json['group_id'] for t in saved) == authority.policy['output_group_ids'],
                    'tribune_existing_output_incomplete')
            return dict(status='completed', stage='reused', event_ids=sorted(t.event_id for t in saved), database_writes=0)
        preview, run, version, result, trusted = qualify(db, authority, run_id, sources, placement_service)
        if not apply:
            return dict(status='completed', stage='preview', outputs=preview, outputs_sha256=sha(preview), database_writes=0)
        require(sha(preview) == authority.policy.get('outputs_sha256'), 'tribune_preview_changed')
        qualified = [o for o in preview if o['outcome'] == 'geometry_qualified']
        require(bool(qualified), 'tribune_no_qualified_geometry')
        geometries = [shape(o['geometry']) for o in qualified]
        require(not any(a.intersects(b) for i,a in enumerate(geometries) for b in geometries[i+1:]),
            'tribune_selected_geometry_overlap')
        before = protected_fingerprints(db)
        now = datetime.now(timezone.utc)
        created = []
        for item, geometry in zip(qualified, geometries, strict=True):
            claim = result.claims[item['claim_index']]
            attributes = item['zone_attributes']
            event = FloodEvent(status='active', first_reported_at=claim.event_time_resolved, verified_at=now,
                peak_severity=attributes['severity_override'], peak_depth=claim.depth_canonical)
            db.add(event); db.flush()
            parts = [geometry] if geometry.geom_type == 'Polygon' else list(geometry.geoms)
            cores = item['geometry_evidence']['component_centerlines']
            require(len(parts) == len(cores), 'tribune_geometry_cores_changed')
            zone_ids = []
            for polygon, core in zip(parts, cores, strict=True):
                zone = FloodAvoidanceZone(event_id=event.id, is_active=True,
                    geometry=from_shape(polygon, srid=4326), source_geometry=from_shape(shape(core), srid=4326),
                    name=claim.road_segment_raw or claim.raw_place_name, expires_at=None,
                    admin_notes=claim.evidence_sentence[:1000], **attributes)
                db.add(zone); db.flush(); zone_ids.append(zone.id)
            record_event_locations(db, event, ((Location.ROAD, claim.road_segment_raw or claim.raw_place_name),
                (Location.CITY, claim.canonical_city), (Location.BARANGAY, claim.canonical_barangay)))
            metadata = HistoricalNewsMetadata(dataset_id=DATASET, observation_key=sha({'session':SESSION,'group':item['group_id']}),
                disposition='active_demo', demonstration_session_id=SESSION, label=claim.road_segment_raw or claim.raw_place_name,
                article_id=25, article_version_id=version.id, source_article_version_id=568, run_id=run.id,
                group_id=item['group_id'], source_url=version.input_snapshot['canonical_url'],
                source_publisher=version.input_snapshot['publisher'], source_excerpt=claim.evidence_sentence,
                source_published_date=RunEvidence.from_records(run, version).source().published_at.astimezone(ZoneInfo('Asia/Manila')).date(),
                occurrence_date='2026-09-24',
                observed_at=claim.event_time_resolved, canonical_road=claim.canonical_road,
                canonical_city=claim.canonical_city, canonical_barangay=claim.canonical_barangay,
                condition=claim.condition, precision='instant', date_basis='source_linked_observation',
                timezone_basis='source_observation_pht_or_utc_plus_08', closure_basis='demo_administration',
                geometry_sha256=sha(item['geometry']), assets_sha256=sha(trusted.manifest),
                input_fingerprint=version.input_fingerprint, result_sha256=sha(run.result),
                pipeline_version=run.pipeline_version, imported_at=now)
            db.add(Timeline(event_id=event.id, entry_type=ENTRY, occurred_at=now, summary=metadata.label,
                snapshot_json=metadata.model_dump(mode='json')))
            db.add(Timeline(event_id=event.id, entry_type='news_tribune_pilot_output', occurred_at=now,
                summary=metadata.label, snapshot_json=dict(schema_version=VERSION, session_id=SESSION,
                    result_sha256=sha(run.result), outputs_sha256=sha(preview),
                    group_id=item['group_id'], geometry_evidence=item['geometry_evidence'],
                    **({'shared_time_review': authority.policy['shared_time_review']}
                       if 'shared_time_review' in authority.policy else {}))))
            created.append(dict(group_id=item['group_id'], event_id=event.id, zone_ids=zone_ids))
        from app.services.news_historical_outputs import _source
        from app.models.news_publication import NewsClaimEvaluation
        for item in preview:
            if item['claim_index'] is None:
                continue
            source = _source(db, run, item['claim_index'], result.claims[item['claim_index']], now)
            db.add(NewsClaimEvaluation(claim_source_id=source.id,
                policy_fingerprint=sha(dict(schema=VERSION,session=SESSION,result=sha(run.result),group=item['group_id'])),
                status='completed', attempt_count=0, result=item, created_at=now,updated_at=now,completed_at=now))
        db.flush()
        verify_protected(before, protected_fingerprints(db))
        return dict(status='completed', stage='saved', outputs=created, database_writes=True)
