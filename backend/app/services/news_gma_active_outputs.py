"""Restricted active-only GMA presentation output; no historical counterpart.

Coordinates are operator hints, never substitutes for qualified road geometry.
The same source and spatial gates run for preview and the locked transaction.
"""
from __future__ import annotations

from datetime import datetime, timezone

from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.report import FloodAvoidanceZone, FloodEvent, FloodEventLocationType, FloodEventStatus
from app.models.report import FloodEventTimelineEntry as Timeline
from app.services.historical_news_metadata import ENTRY, HistoricalNewsMetadata
from app.services.news_ner_durable.contracts import RunEvidence, sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_source_repair import BODY

VERSION = 'gma-active-only-output-v1'
CONNECTED_VERSION = 'gma-connected-active-only-output-v2'
DATASET = 'gma-active-only-20260909-v1'
SESSION = 'gma-active-only-20261023-v1'
HINTS = {'resolved-n6': [14.6589525, 120.9532479],
         'resolved-n8': [14.6572628, 120.9512603],
         'resolved-n10': [14.6252445, 121.0832429]}


def active_only_event(event_column: object = None) -> object:
    column = FloodEvent.id if event_column is None else event_column
    return select(Timeline.id).where(Timeline.event_id == column, Timeline.entry_type == ENTRY,
        Timeline.snapshot_json['schema_version'].as_string() == 'historical-import-v1',
        Timeline.snapshot_json['dataset_id'].as_string() == DATASET,
        Timeline.snapshot_json['disposition'].as_string() == 'active_demo').correlate_except(Timeline).exists()


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ResolutionError(reason)


def validate_authority(authority: dict, pin: str, engine: object, trusted: object) -> None:
    from app.services.news_historical_processing import database_identity
    require(sha(authority) == pin and authority.get('schema_version') in (VERSION, CONNECTED_VERSION)
        and authority.get('session_id') == SESSION and authority.get('dataset_id') == DATASET
        and authority.get('allowed_operations') in (['preview'], ['apply'])
        and authority.get('run_id') == 388 and authority.get('native_version_id') == 569
        and authority.get('source_version_id') == 140 and authority.get('article_id') == 47
        and authority.get('source_body_sha256') == BODY and authority.get('coordinate_hints') == HINTS
        and authority.get('provider_requests_allowed') == 0
        and authority.get('database_identity_sha256') == database_identity(engine)
        and authority.get('assets_sha256') == sha(trusted.manifest), 'gma_active_authority_invalid')
    if authority.get('schema_version') == CONNECTED_VERSION:
        from pathlib import Path
        import hashlib
        from app.services.news_connected_road_service import VERSION as ROAD_POLICY
        require(authority.get('road_policy') == ROAD_POLICY and bool(authority.get('placement_identity'))
            and authority.get('saved_release_sha256') == 'ca6befd3719e1882a37d9183bb933848e8545faa6a65da05f7956613221a961b'
            and authority.get('saved_assets_sha256') == sha(trusted.manifest), 'gma_active_compatibility_invalid')
        path = Path(__file__).with_name('news_connected_road_service.py')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == authority.get('road_code_sha256'),
                'gma_active_road_policy_changed')


def qualify(db: Session, authority: dict, trusted: object, *, placement_service: object = None) -> list[dict]:
    import hashlib
    from app.services.configuration_service import read_configuration, selected_news_sources
    from app.services.news_sources import load_news_sources
    from app.services.news_evaluation_service import source_is_approved
    from app.services.news_source_read_service import require_current_pilot_capture
    from app.services.news_ner_durable.adapter import verify_saved_result
    from app.services.news_ner_durable.source_check import check_native_sources
    from app.services.news_publication_service import _operational_zone_attributes
    from app.services.news_estimated_road_service import build_estimated_road_zone
    from app.crud.news_publication import NewsPublicationError

    require(db.scalar(text('SELECT version_num FROM alembic_version')) == 'f1a9c7e2b604',
            'gma_active_schema_changed')
    config = read_configuration(db)
    require(all(getattr(config, k) is False for k in ('news_collection_enabled', 'news_processing_enabled',
        'news_publication_enabled', 'automatic_expiry_enabled', 'pasig_ml_expiry_enabled')), 'gma_active_configuration_changed')
    run = db.get(NewsExtractionRun, 388)
    version = db.get(NewsArticleVersion, 569)
    original = db.get(NewsArticleVersion, 140)
    require(run is not None and version is not None and original is not None and run.status == 'completed'
        and run.article_version_id == version.id and version.article_id == original.article_id == 47
        and sha(run.result) == authority['result_sha256'], 'gma_active_saved_result_changed')
    require_current_pilot_capture(db, version)
    require(all(hashlib.sha256(v.input_snapshot['article_text'].encode('utf-8')).hexdigest() == BODY
                for v in (version, original)), 'gma_active_source_changed')
    context = RunEvidence.from_records(run, version)
    require(source_is_approved(context.source(), selected_news_sources(db, load_news_sources())),
            'gma_active_source_ineligible')
    result = verify_saved_result(context, run.result, trusted)
    groups = [g for g in result.projection['groups'] if g['disposition'] == 'projected']
    require(len(groups) == len(result.claims) == 3 and {g['group_id'] for g in groups} == set(HINTS),
            'gma_active_three_observations_required')
    audits = check_native_sources(run, version, run.result, tuple(range(3)), trusted,
                                 now=datetime.now(timezone.utc))
    outputs = []
    for group in groups:
        claim = result.claims[group['claim_index']]
        require(claim.condition == 'active' and claim.depth_canonical == 'gutter'
            and claim.depth_inches is None and claim.depth_meters is None
            and claim.road_passability == 'passable_all' and claim.event_time_resolved is not None
            and claim.event_time_resolved.isoformat() == '2026-09-09T14:47:00+08:00', 'gma_active_source_facts_changed')
        audit = audits[group['claim_index']]
        require(audit.outcome == 'verified', 'gma_active_source_audit_failed')
        item = {'group_id': group['group_id'], 'claim_index': group['claim_index'],
            'coordinate_hint': {'latitude_longitude': HINTS[group['group_id']], 'origin': 'user_supplied',
                                'establishes_geometry': False},
            'outcome': 'unresolved', 'reasons': [], 'geometry': None}
        try:
            attributes = _operational_zone_attributes(claim, audit)
            if authority.get('schema_version') == CONNECTED_VERSION:
                require(placement_service is not None and placement_service.identity == authority['placement_identity'],
                        'gma_active_placement_assets_changed')
                corridor = placement_service.build(claim, hint=HINTS[group['group_id']])
                geometry_evidence = corridor.evidence
            else:
                corridor = build_estimated_road_zone(claim, service=placement_service)
                geometry_evidence = corridor.evidence.model_dump(mode='json')
            item.update(outcome='geometry_qualified', geometry=corridor.geometry,
                geometry_checksum=corridor.checksum,
                geometry_evidence=geometry_evidence,
                zone_attributes={k: getattr(v, 'value', v) for k, v in attributes.items()})
        except NewsPublicationError as exc:
            item['reasons'].append(str(exc))
        outputs.append(item)
    if authority.get('schema_version') == CONNECTED_VERSION:
        from app.services.news_connected_road_service import qualified_junction_overlap
        for i, first in enumerate(outputs):
            for second in outputs[i+1:]:
                if first['outcome'] != 'geometry_qualified' or second['outcome'] != 'geometry_qualified':
                    continue
                try:
                    proof = qualified_junction_overlap(first, second)
                    if proof:
                        first.setdefault('shared_junctions', []).append(proof)
                        second.setdefault('shared_junctions', []).append({**proof, 'other_group_id': first['group_id']})
                except NewsPublicationError as exc:
                    for item in (first, second):
                        item.update(outcome='unresolved', reasons=[*item['reasons'], str(exc)])
    return outputs


def active_outputs(engine: object, authority: dict, pin: str, trusted: object, *,
                   apply: bool = False, placement_service: object = None) -> dict:
    validate_authority(authority, pin, engine, trusted)
    require(authority['allowed_operations'] == (['apply'] if apply else ['preview']), 'gma_active_operation_denied')
    with Session(engine) as db, db.begin():
        if apply:
            db.execute(text("SET LOCAL lock_timeout='8000'"))
            db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': int(sha(SESSION)[:15], 16)})
            db.execute(text('LOCK TABLE flood_events, flood_avoidance_zones IN SHARE ROW EXCLUSIVE MODE'))
        else:
            db.execute(text('SET TRANSACTION READ ONLY'))
        outputs = qualify(db, authority, trusted, placement_service=placement_service)
        if not apply:
            return {'status': 'completed', 'stage': 'preview', 'outputs': outputs, 'outputs_sha256': sha(outputs),
                    'all_three_qualified': all(o['outcome'] == 'geometry_qualified' for o in outputs),
                    'database_writes': 0, 'provider_requests': 0}
        require(all(o['outcome'] == 'geometry_qualified' for o in outputs), 'gma_active_all_three_must_qualify')
        require(sha(outputs) == authority.get('outputs_sha256'), 'gma_active_preview_changed')
        existing = list(db.scalars(select(Timeline).where(Timeline.entry_type == ENTRY,
            Timeline.snapshot_json['dataset_id'].as_string() == DATASET,
            Timeline.snapshot_json['demonstration_session_id'].as_string() == SESSION)))
        require(not existing or len(existing) == 3 and {t.snapshot_json['group_id'] for t in existing} == set(HINTS),
                'gma_active_partial_state')
        if existing:
            from shapely.ops import unary_union
            from geoalchemy2.shape import to_shape
            for entry in existing:
                output = next(o for o in outputs if o['group_id'] == entry.snapshot_json['group_id'])
                require(entry.snapshot_json['geometry_sha256'] == sha(output['geometry'])
                    and entry.snapshot_json['result_sha256'] == authority['result_sha256'], 'gma_active_existing_changed')
                zones = list(db.scalars(select(FloodAvoidanceZone).where(FloodAvoidanceZone.event_id == entry.event_id)))
                require(bool(zones) and unary_union([to_shape(z.geometry) for z in zones]).equals(shape(output['geometry'])),
                        'gma_active_existing_geometry_changed')
            return {'status': 'completed', 'stage': 'reused', 'event_ids': sorted(t.event_id for t in existing),
                    'database_writes': 0, 'provider_requests': 0}
        from app.services.news_history_protection import protected_fingerprints, verify_protected
        from app.services.flood_event_service import record_event_locations
        before = protected_fingerprints(db)
        run, version = db.get(NewsExtractionRun, 388), db.get(NewsArticleVersion, 569)
        saved = []
        now = datetime.now(timezone.utc)
        shapes = [shape(o['geometry']) for o in outputs]
        if authority.get('schema_version') == CONNECTED_VERSION:
            from app.services.news_connected_road_service import qualified_junction_overlap
            for i, first in enumerate(outputs):
                for second in outputs[i+1:]:
                    qualified_junction_overlap(first, second)
        else:
            require(not any(a.intersects(b) for i, a in enumerate(shapes) for b in shapes[i+1:]), 'gma_active_selected_overlap')
        # Check the pre-existing state before inserting any member of this
        # atomic set. Selected shared junctions were authenticated above;
        # our first insert must not masquerade as an unrelated active zone.
        for geometry in shapes:
            overlap = db.scalar(select(FloodAvoidanceZone.id).where(FloodAvoidanceZone.is_active.is_(True),
                func.ST_Intersects(FloodAvoidanceZone.geometry, from_shape(geometry, srid=4326))).limit(1))
            require(overlap is None, 'gma_active_existing_overlap')
        for output, geometry in zip(outputs, shapes, strict=True):
            claim = run.result['claims'][output['claim_index']]
            attributes = output['zone_attributes']
            event = FloodEvent(status=FloodEventStatus.ACTIVE, first_reported_at=datetime.fromisoformat(claim['event_time_resolved']),
                verified_at=now, ended_at=None, peak_severity=attributes['severity_override'], peak_depth='gutter')
            db.add(event); db.flush()
            parts = [geometry] if geometry.geom_type == 'Polygon' else list(geometry.geoms)
            zone_ids = []
            for polygon, core in zip(parts, output['geometry_evidence']['component_centerlines'], strict=True):
                zone = FloodAvoidanceZone(event_id=event.id, is_active=True, geometry=from_shape(polygon, srid=4326),
                    source_geometry=from_shape(shape(core), srid=4326),
                    name=claim['road_segment_raw'] or claim['canonical_road'] or claim['raw_place_name'],
                    **attributes, expires_at=None, admin_notes=claim['evidence_sentence'][:1000])
                db.add(zone); db.flush(); zone_ids.append(zone.id)
            record_event_locations(db, event, ((FloodEventLocationType.ROAD, claim['road_segment_raw'] or claim['raw_place_name']),
                (FloodEventLocationType.CITY, claim['canonical_city']), (FloodEventLocationType.BARANGAY, claim['canonical_barangay'])))
            metadata = HistoricalNewsMetadata(dataset_id=DATASET, observation_key=sha({'session': SESSION, 'group': output['group_id']}),
                disposition='active_demo', demonstration_session_id=SESSION, label=claim['road_segment_raw'] or claim['raw_place_name'],
                article_id=47, article_version_id=569, source_article_version_id=140, run_id=388, group_id=output['group_id'],
                source_url=version.input_snapshot['canonical_url'], source_publisher=version.input_snapshot['publisher'],
                source_excerpt=claim['evidence_sentence'], source_published_date='2026-09-09', occurrence_date='2026-09-09',
                observed_at=claim['event_time_resolved'], canonical_road=claim['canonical_road'], canonical_city=claim['canonical_city'],
                canonical_barangay=claim['canonical_barangay'], condition='active', precision='instant',
                date_basis='explicit_observation_body_date', timezone_basis='source_observation_pht_or_utc_plus_08',
                closure_basis='demo_administration', geometry_sha256=sha(output['geometry']), assets_sha256=authority['assets_sha256'],
                input_fingerprint=version.input_fingerprint, result_sha256=authority['result_sha256'],
                pipeline_version=run.pipeline_version, imported_at=now)
            db.add(Timeline(event_id=event.id, entry_type=ENTRY, occurred_at=now, summary=metadata.label,
                            snapshot_json=metadata.model_dump(mode='json')))
            db.add(Timeline(event_id=event.id, entry_type='news_presentation_placement', occurred_at=now,
                summary=metadata.label, snapshot_json={'schema_version': authority['schema_version'], 'group_id': output['group_id'],
                    'coordinate_hint': output['coordinate_hint'], 'geometry_evidence': output['geometry_evidence'],
                    'shared_junctions': output.get('shared_junctions', []),
                    'authority_sha256': pin, 'outputs_sha256': authority['outputs_sha256']}))
            saved.append({'group_id': output['group_id'], 'event_id': event.id, 'zone_ids': zone_ids})
        db.flush()
        verify_protected(before, protected_fingerprints(db))
        return {'status': 'completed', 'stage': 'saved', 'outputs': saved, 'provider_requests': 0}
