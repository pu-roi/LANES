"""Explicit local materialization of authenticated historical extraction.

This path never calls inference or the live-news publisher. E1 processing-only
authority cannot authorize these writes. Shared-target qualification is Phase 2.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import hashlib
import json
import os

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import mapping, shape
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimCase, NewsClaimSource, NewsClaimEvaluation
from app.models.report import FloodEvent, FloodAvoidanceZone, FloodEventTimelineEntry as Timeline, FloodEventStatus
from app.schemas.historical_news import HistoricalNewsMetadata
from app.services.historical_news_metadata import ENTRY, DEMO_LABEL
from app.services.news_historical_processing import (require, database_identity, disposable_target,
    inspect_sources)
from app.crud.news_historical_processing import readonly_historical_session
from app.services.news_ner_durable.contracts import RunEvidence, sha

VERSION = 'historical-output-v1'
OUTPUT_REVISION = 'f1a9c7e2b604'


def output_code_identity() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    names = ('app/services/news_historical_outputs.py', 'app/services/historical_news_metadata.py',
        'app/schemas/historical_news.py', 'scripts/materialize_news_historical_outputs.py',
        'app/services/news_historical_interpretation.py', 'app/services/news_historical_processing.py',
        'app/crud/news_historical_processing.py')
    return {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names}


def expected_output_policy(package: object, trusted: object, engine: object) -> dict:
    package.validate(); trusted.validate()
    return {'schema_version': VERSION, 'parent_manifest_sha256': package.manifest_sha256,
        'dataset_id': package.manifest['dataset_id'],
        'demonstration_session_id': package.manifest['demonstration_session_id'],
        'database_identity_sha256': database_identity(engine), 'confirmed_database': engine.url.database,
        'assets_sha256': sha(trusted.manifest), 'pipeline_version': trusted.pipeline_version,
        'selection': package.manifest['candidates'], 'application_sha256': output_code_identity(),
        'operations': ['qualify_saved_runs', 'reuse_or_archive_history'] +
            ([] if package.manifest.get('policy', {}).get('archive_only') else ['selected_demo_lifecycle']),
        'live_news_publication_allowed': False}


def authenticate_policy(package: object, trusted: object, engine: object, policy: dict,
                        policy_sha256: str, confirmed_database: str) -> None:
    require(sha(policy) == policy_sha256 and sha(policy) == sha(expected_output_policy(package, trusted, engine)),
            'historical_output_policy_mismatch')
    from app.services.news_history_authority import valid_shared_connection
    require(valid_shared_connection(engine)
        and engine.url.database == confirmed_database, 'historical_output_target_mismatch')


def _runs(db: Session, package: object, trusted: object, sources: tuple | None) -> list:
    blockers, state = inspect_sources(db, package, trusted, sources)
    require(not blockers, blockers[0] if blockers else 'historical_output_sources_invalid')
    require(state['revision'] == OUTPUT_REVISION, 'historical_output_migration_required')
    runs = state['runs']
    require(len(runs) == len(package.captures) and all(r.status == 'completed' for r in runs),
            'historical_completed_runs_required')
    return [(r, db.get(NewsArticleVersion, r.article_version_id)) for r in runs]


def qualify_outputs(db: Session, package: object, trusted: object, policy: dict, *, now: datetime,
                    sources: tuple | None = None, placement_service: object | None = None,
                    records: list | None = None, archive_attributes: object | None = None) -> list[dict]:
    from app.services.news_historical_interpretation import interpret_historical, historical_placement_claim
    from app.services.news_ner_durable.adapter import verify_saved_result
    from app.services.news_estimated_road_service import build_estimated_road_zone
    from app.crud.news_publication import NewsPublicationError
    from app.services.news_publication_service import _operational_zone_attributes
    from app.schemas.news_audit import IndependentAuditResult
    execution = {'parent_manifest_sha256': package.manifest_sha256, 'assets_sha256': sha(trusted.manifest),
        'pipeline_version': trusted.pipeline_version, 'output_policy_sha256': sha(policy)}
    outputs = []
    for run, version in (_runs(db, package, trusted, sources) if records is None else records):
        interpretation = interpret_historical(run, version, trusted, package, execution,
            now=now, placement_service=placement_service)
        result = verify_saved_result(RunEvidence.from_records(run, version), run.result, trusted)
        from app.services.news_ner_durable.read_projection import build_read_projection
        read_projection = build_read_projection(RunEvidence.from_records(run, version).source(), result, trusted.catalog)
        for group in interpretation['groups']:
            output = {'schema_version': VERSION, 'run_id': run.id, 'article_id': version.article_id,
                'article_version_id': version.id, 'group_id': group['group_id'],
                'claim_index': group['claim_index'], 'interpretation': group,
                'outcome': 'unresolved', 'reasons': list(group['reasons']), 'geometry': None,
                'event_id': None, 'zone_ids': [], 'disposition': group['disposition']}
            output['read_projection'] = read_projection.model_dump(mode='json')
            if group['qualification'] == 'source_qualified_for_historical_placement':
                claim = result.claims[group['claim_index']]
                try:
                    if archive_attributes is None:
                        attributes = _operational_zone_attributes(claim, IndependentAuditResult.model_validate_json(json.dumps(group['source_check'])))
                    else:
                        # A separately authenticated archive policy may classify
                        # shared source depth, but can never produce live output.
                        if group['disposition'] != 'historical_archive':
                            raise NewsPublicationError('shared_depth_archive_only')
                        attributes, proof = archive_attributes(result, group, context=RunEvidence.from_records(run, version))
                        output['shared_depth_evidence'] = proof
                    placement_claim, _adapter = historical_placement_claim(result, group['group_id'])
                    corridor = build_estimated_road_zone(placement_claim, service=placement_service)
                    output.update(outcome='geometry_qualified', geometry=corridor.geometry,
                        geometry_checksum=corridor.checksum, geometry_evidence=corridor.evidence.model_dump(mode='json'),
                        zone_attributes={k: getattr(v, 'value', v) for k, v in attributes.items()})
                except NewsPublicationError as exc:
                    output['reasons'].append(str(exc))
            outputs.append(output)
    # Only one selected primary/backup may be displayed. Archive outputs remain independent.
    qualified = [o for o in outputs if o['outcome'] == 'geometry_qualified' and o['disposition'] == 'active_demo']
    qualified.sort(key=lambda o: (o['interpretation'].get('candidate_role') != 'primary', o['run_id'], o['group_id']))
    for output in qualified[1:]:
        output.update(outcome='unresolved', reasons=[*output['reasons'], 'historical_backup_not_selected'])
    return outputs


def _source(db: Session, run: object, ordinal: int, claim: object, now: datetime) -> NewsClaimSource:
    from app.crud.news_evaluation import canonical_claim_sha256
    source = db.scalar(select(NewsClaimSource).where(NewsClaimSource.extraction_run_id == run.id,
        NewsClaimSource.claim_ordinal == ordinal))
    if source is None:
        case = NewsClaimCase(created_at=now); db.add(case); db.flush()
        source = NewsClaimSource(case_id=case.id, extraction_run_id=run.id, claim_ordinal=ordinal,
            claim_sha256=canonical_claim_sha256(claim), created_at=now)
        db.add(source); db.flush()
    require(source.claim_sha256 == canonical_claim_sha256(claim), 'historical_claim_binding_changed')
    return source


def _existing_match(db: Session, package: object, output: dict, claim: object, *, lock: bool = True) -> tuple | None:
    from app.services.news_history_incident_matching import citizen_archive_match
    citizen = citizen_archive_match(db, output, claim, lock=lock)
    news = _news_existing_match(db, package, output, claim, lock=lock)
    require(not (citizen and news) or (citizen[0].id, citizen[1].id) == (news[0].id, news[1].id),
        'historical_existing_match_unresolved')
    return citizen or news


def _news_existing_match(db: Session, package: object, output: dict, claim: object, *, lock: bool = True) -> tuple | None:
    candidate = next((c for c in package.manifest['candidates']
        if c['candidate_id'] == output['interpretation'].get('selected_candidate_id')), None)
    if candidate is None:
        # Never guess a match based only on road proximity. Unselected groups
        # must be reviewed if pre-existing source history could be duplicated.
        from app.models.news_publication import NewsClaimZoneLink, NewsClaimDecision
        legacy_claim = NewsExtractionRun.result['claims'][NewsClaimSource.claim_ordinal]
        from app.services.news_ner_durable.fields import PHT
        observed_day = date.fromisoformat(output['interpretation']['time']['occurrence_date'])
        day_start = datetime.combine(observed_day, time.min, PHT)
        possible = list(db.execute(select(FloodAvoidanceZone.id, FloodAvoidanceZone.event_id,
            NewsArticleVersion.article_id, legacy_claim.label('claim'), NewsClaimDecision.observed_at).select_from(NewsClaimSource).join(NewsExtractionRun,
            NewsExtractionRun.id == NewsClaimSource.extraction_run_id).join(NewsArticleVersion,
            NewsArticleVersion.id == NewsExtractionRun.article_version_id).join(NewsClaimDecision,
            NewsClaimDecision.snapshot['claim_source_id'].as_integer() == NewsClaimSource.id).join(NewsClaimZoneLink,
            NewsClaimZoneLink.decision_id == NewsClaimDecision.id).where(
                NewsClaimDecision.observed_at >= day_start,
                NewsClaimDecision.observed_at < day_start + timedelta(days=1),
                func.lower(func.coalesce(legacy_claim['canonical_road'].as_string(), legacy_claim['raw_place_name'].as_string()))
                    == (claim.canonical_road or claim.raw_place_name).casefold()).join(
                        FloodAvoidanceZone, FloodAvoidanceZone.id == NewsClaimZoneLink.zone_id)).all())
        from types import SimpleNamespace
        from app.services.news_source_repair import superseded_event
        imported = db.execute(select(FloodAvoidanceZone.id, FloodAvoidanceZone.event_id, Timeline.snapshot_json)
            .join(Timeline, Timeline.event_id == FloodAvoidanceZone.event_id).where(Timeline.entry_type == ENTRY,
                ~superseded_event(FloodAvoidanceZone.event_id),
                Timeline.snapshot_json['schema_version'].as_string() == 'historical-import-v1',
                Timeline.snapshot_json['disposition'].as_string() == 'historical_archive',
                Timeline.snapshot_json['occurrence_date'].as_string() == observed_day.isoformat(),
                func.lower(Timeline.snapshot_json['canonical_road'].as_string()) == (claim.canonical_road or claim.raw_place_name).casefold()))
        for row in imported:
            metadata = HistoricalNewsMetadata.model_validate(row.snapshot_json)
            possible.append(SimpleNamespace(id=row.id, event_id=row.event_id, article_id=metadata.article_id,
                observed_at=metadata.observed_at, claim={'canonical_city': metadata.canonical_city,
                    'condition': metadata.condition, 'evidence_sentence': metadata.source_excerpt}))
        matches = {}
        for row in possible:
            old = row.claim or {}
            same_city = (old.get('canonical_city') or '').casefold() == (claim.canonical_city or '').casefold()
            quote = claim.evidence_sentence
            old_quote = old.get('evidence_sentence') or ''
            same_evidence = bool(quote and old_quote and (quote in old_quote or old_quote in quote))
            instant = output['interpretation']['time']['observed_at']
            same_time = (row.observed_at is not None and
                (row.observed_at == datetime.fromisoformat(instant) if instant else
                 row.observed_at.astimezone(PHT).date().isoformat() == output['interpretation']['time']['occurrence_date']))
            same_source = row.article_id == output['article_id']
            supported_identity = same_evidence if same_source else bool(instant)
            if same_city and supported_identity and same_time and old.get('condition') == claim.condition:
                matches[(row.event_id, row.id)] = row
        # Similar source history without an exact evidence/time match needs review.
        require(not possible or (len({key[0] for key in matches}) == 1
            and {(row.event_id, row.id) for row in possible} <= set(matches)),
            'historical_existing_match_unresolved')
        if not matches:
            return None
        event_id, zone_id = next(iter(matches))
        event_query = select(FloodEvent).where(FloodEvent.id == event_id)
        zone_query = select(FloodAvoidanceZone).where(FloodAvoidanceZone.id == zone_id)
        event = db.scalar(event_query.with_for_update() if lock else event_query)
        zone = db.scalar(zone_query.with_for_update() if lock else zone_query)
        require(event.status == FloodEventStatus.ENDED and not zone.is_active,
            'historical_existing_match_unresolved')
        return event, zone
    zone_query = select(FloodAvoidanceZone).where(FloodAvoidanceZone.id == candidate['existing_zone_id'])
    event_query = select(FloodEvent).where(FloodEvent.id == candidate['existing_event_id'])
    zone = db.scalar(zone_query.with_for_update() if lock else zone_query)
    event = db.scalar(event_query.with_for_update() if lock else event_query)
    require(zone is not None and event is not None and zone.event_id == event.id and not zone.is_active
        and event.status == FloodEventStatus.ENDED, 'historical_original_history_changed')
    actual = db.scalar(select(func.encode(func.ST_AsEWKB(FloodAvoidanceZone.geometry), 'hex'))
        .where(FloodAvoidanceZone.id == zone.id))
    require(hashlib.sha256(bytes.fromhex(actual)).hexdigest() == candidate['existing_geometry_sha256'],
            'historical_original_geometry_changed')
    legacy = db.get(NewsExtractionRun, candidate['legacy_run_id'])
    require(legacy is not None and legacy.mode == 'rules_only' and legacy.status == 'completed'
        and sha(legacy.result['claims'][candidate['legacy_claim_ordinal']]) == candidate['legacy_claim_sha256'],
            'historical_original_claim_changed')
    legacy_version = db.get(NewsArticleVersion, legacy.article_version_id)
    require(legacy_version.article_id == output['article_id'], 'historical_original_source_changed')
    # Named-place selection alone cannot collapse distinct observation times.
    old = legacy.result['claims'][candidate['legacy_claim_ordinal']]
    quote = claim.evidence_sentence
    old_quote = old.get('evidence_sentence', '')
    require(bool(quote and old_quote and (quote in old_quote or old_quote in quote)),
            'historical_source_occurrence_match_unresolved')
    old_time = old.get('event_time_resolved')
    if old_time:
        from app.services.news_ner_durable.fields import PHT
        require(datetime.fromisoformat(old_time).astimezone(PHT).date().isoformat() == output['interpretation']['time']['occurrence_date'],
                'historical_observation_match_conflict')
        instant = output['interpretation']['time']['observed_at']
        require(not instant or datetime.fromisoformat(old_time) == datetime.fromisoformat(instant),
            'historical_observation_match_conflict')
    return event, zone


def _reviewable_match(db: Session, package: object, output: dict, claim: object, *, lock: bool = True) -> tuple | None:
    from app.services.news_historical_preparation import PreparationError
    try:
        return _existing_match(db, package, output, claim, lock=lock)
    except PreparationError as exc:
        if str(exc) != 'historical_existing_match_unresolved':
            raise
        output.update(outcome='unresolved', reasons=[*output['reasons'], str(exc)])
        return None


def archive_assumed_closure(observation: dict, clearance: dict) -> tuple[datetime | None, str]:
    """Storage endpoint assumptions never establish observed flood duration."""
    if clearance.get('source_clearance_present'):
        return None, 'unknown'
    if observation.get('precision') == 'instant' and observation.get('observed_at'):
        return datetime.fromisoformat(observation['observed_at']) + timedelta(hours=2), 'assumed_two_hours'
    if observation.get('precision') == 'date' and observation.get('occurrence_date'):
        day = date.fromisoformat(observation['occurrence_date']) + timedelta(days=1)
        return datetime.combine(day, time.min, ZoneInfo('Asia/Manila')), 'assumed_source_day_end'
    return None, 'unknown'


def _capture_origin(package: object, version: object) -> tuple[dict, date | None]:
    capture = next(c for c in package.captures if c['article_id'] == version.article_id
        and c['native_input_fingerprint'] == version.input_fingerprint)
    original = next(r['input_snapshot'] for r in package.documents['inventory.json']['sources']
        if r['version_id'] == capture['source_version_id'])
    raw = (original.get('historical_source_capture') or {}).get('published_at')
    try:
        publication_date = date.fromisoformat(raw[:10]) if raw else None
    except (ValueError, TypeError):
        publication_date = None
    return capture, publication_date


def _materialize(db: Session, package: object, trusted: object, output: dict, run: object,
                 version: object, claim: object, now: datetime) -> dict:
    from app.services.flood_event_service import record_event_locations
    from app.models.report import FloodEventLocationType as Kind
    # Different articles/sessions can describe the same observation. Serialize
    # the match lookup before either transaction can create a competing archive.
    incident_lock = sha({'scope': 'historical-archive-match-v1',
        'road': (claim.canonical_road or claim.raw_place_name).casefold(),
        'city': (claim.canonical_city or '').casefold(),
        'day': output['interpretation']['time']['occurrence_date']})
    db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': int(incident_lock[:15], 16)})
    match = _reviewable_match(db, package, output, claim)
    if output['outcome'] == 'unresolved':
        return output
    disposition = output['disposition']
    attributes = output['zone_attributes']
    geometry = shape(output['geometry'])
    capture, publication_date = _capture_origin(package, version)
    key = sha({'dataset': package.manifest['dataset_id'] if disposition == 'active_demo' else None,
        'source': version.input_snapshot['canonical_url'],
        'road': (claim.canonical_road or claim.raw_place_name).casefold(), 'city': claim.canonical_city,
        'observation_date': output['interpretation']['time']['occurrence_date'],
        'observation_instant': output['interpretation']['time']['observed_at'],
        'condition': claim.condition, 'section': claim.road_segment_raw, 'disposition': disposition,
        'session': package.manifest['demonstration_session_id'] if disposition == 'active_demo' else None})
    db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': int(key[:15], 16)})
    previous = db.scalar(select(Timeline).where(Timeline.entry_type == ENTRY,
        Timeline.snapshot_json['observation_key'].as_string() == key))
    if previous is not None:
        saved = HistoricalNewsMetadata.model_validate(previous.snapshot_json)
        require(saved.geometry_sha256 == sha(output['geometry']),
                'historical_completed_output_changed')
        if saved.run_id != run.id:
            lineage = saved.model_copy(update={'run_id': run.id, 'group_id': output['group_id'],
                'article_version_id': version.id, 'result_sha256': sha(run.result),
                'source_article_version_id': capture['source_version_id'], 'source_published_date': publication_date,
                'source_excerpt': claim.evidence_sentence,
                'pipeline_version': run.pipeline_version, 'assets_sha256': sha(trusted.manifest), 'imported_at': now})
            db.add(Timeline(event_id=previous.event_id, entry_type=ENTRY, occurred_at=now,
                summary='Additional historical extraction lineage; original lifecycle retained.',
                snapshot_json=lineage.model_dump(mode='json')))
        zones = list(db.scalars(select(FloodAvoidanceZone.id).where(FloodAvoidanceZone.event_id == previous.event_id)))
        return {**output, 'outcome': 'reused', 'event_id': previous.event_id, 'zone_ids': zones}
    if disposition == 'historical_archive' and match:
        event, zone = match
        from shapely.ops import unary_union
        footprints = list(db.scalars(select(FloodAvoidanceZone).where(FloodAvoidanceZone.event_id == event.id)))
        if not unary_union([to_shape(z.geometry) for z in footprints]).equals(geometry):
            return {**output, 'outcome': 'unresolved', 'reasons': [*output['reasons'], 'historical_geometry_disagreement']}
        zones = [z.id for z in footprints]; closure = 'original_history'
    else:
        instant = output['interpretation']['time']['observed_at']
        observed = datetime.fromisoformat(instant) if instant else None
        clearance = output['interpretation'].get('closure', {})
        source_end = datetime.fromisoformat(clearance['observed_at']) if clearance.get('observed_at') else None
        assumed_end, assumed_basis = archive_assumed_closure(output['interpretation']['time'], clearance)
        demo = disposition == 'active_demo'
        if not demo and source_end is None and assumed_end is None:
            return {**output, 'outcome': 'unresolved', 'reasons': [*output['reasons'], 'historical_closure_unresolved']}
        event = FloodEvent(status=FloodEventStatus.ACTIVE if demo else FloodEventStatus.ENDED,
            verified_at=now, first_reported_at=observed,
            ended_at=None if demo else source_end or assumed_end,
            peak_severity=attributes['severity_override'], peak_depth=attributes['depth_override'])
        db.add(event); db.flush()
        zones = []
        parts = [geometry] if geometry.geom_type == 'Polygon' else list(geometry.geoms)
        for part, centerline in zip(parts, output['geometry_evidence']['component_centerlines'], strict=True):
            zone = FloodAvoidanceZone(event_id=event.id, geometry=from_shape(part, srid=4326),
                source_geometry=from_shape(shape(centerline), srid=4326), is_active=demo,
                name=claim.canonical_road or claim.raw_place_name, **attributes,
                created_at=now, updated_at=now, admin_notes=claim.evidence_sentence[:1000])
            db.add(zone); db.flush(); zones.append(zone.id)
        closure = ('demo_administration' if demo else 'source_supported' if source_end else
                   assumed_basis if assumed_end else 'unknown')
        record_event_locations(db, event, ((Kind.ROAD, claim.canonical_road or claim.raw_place_name),
            (Kind.CITY, claim.canonical_city), (Kind.BARANGAY, claim.canonical_barangay)))
    time = output['interpretation']['time']
    metadata = HistoricalNewsMetadata(dataset_id=package.manifest['dataset_id'], observation_key=key,
        disposition=disposition, demonstration_session_id=package.manifest['demonstration_session_id'],
        label=DEMO_LABEL if disposition == 'active_demo' else 'Historical news — September 2026',
        article_id=version.article_id, article_version_id=version.id, run_id=run.id, group_id=output['group_id'],
        source_article_version_id=capture['source_version_id'], source_published_date=publication_date,
        source_url=version.input_snapshot['canonical_url'], source_publisher=version.input_snapshot['publisher'],
        source_excerpt=claim.evidence_sentence, occurrence_date=time['occurrence_date'], observed_at=time['observed_at'],
        canonical_road=claim.canonical_road, canonical_city=claim.canonical_city, canonical_barangay=claim.canonical_barangay,
        condition=claim.condition,
        precision=time['precision'], date_basis=time['date_basis'], timezone_basis=time['timezone_basis'],
        closure_basis=closure, simulated_interval_minutes=120 if closure == 'assumed_two_hours' else None,
        original_event_id=match[0].id if match else None, original_zone_id=match[1].id if match else None,
        geometry_sha256=sha(output['geometry']), assets_sha256=sha(trusted.manifest),
        input_fingerprint=version.input_fingerprint, result_sha256=sha(run.result),
        pipeline_version=run.pipeline_version, imported_at=now)
    db.add(Timeline(event_id=event.id, entry_type=ENTRY, occurred_at=now,
        summary=metadata.label, snapshot_json=metadata.model_dump(mode='json')))
    return {**output, 'outcome': 'saved', 'event_id': event.id, 'zone_ids': zones,
        'reused_existing_event': bool(match and disposition == 'historical_archive')}


def historical_outputs(engine: object, package: object, trusted: object, *, policy: dict,
        policy_sha256: str, confirmed_database: str, environment: str, apply: bool = False,
        sources: tuple | None = None, placement_service: object | None = None,
        now: datetime | None = None, authorization: object | None = None) -> dict:
    authenticate_policy(package, trusted, engine, policy, policy_sha256, confirmed_database)
    now = now or datetime.now(timezone.utc)
    require(now.tzinfo is not None, 'historical_output_clock_invalid')
    if authorization is not None:
        from app.services.news_history_authority import ArchiveAuthority
        require(type(authorization) is ArchiveAuthority, 'historical_shared_authority_invalid')
        require(package.manifest.get('policy', {}).get('archive_only') is True
            and not package.manifest['candidates'], 'historical_shared_archive_only_required')
        authorization.validate(engine, 'save_archives', sha(policy), sha(trusted.manifest))
    elif apply:
        require(disposable_target(engine, environment), 'historical_output_shared_release_not_qualified')
    if not apply:
        with readonly_historical_session(engine, confirmed_database) as db:
            outputs = qualify_outputs(db, package, trusted, policy, now=now,
                sources=sources, placement_service=placement_service)
            for output in outputs:
                if output['outcome'] == 'geometry_qualified':
                    run = db.get(NewsExtractionRun, output['run_id'])
                    from app.schemas.news_ner_result import parse_saved_result
                    from app.services.news_historical_interpretation import historical_placement_claim
                    claim, _adapter = historical_placement_claim(parse_saved_result(run.mode, run.result), output['group_id'])
                    match = _reviewable_match(db, package, output, claim, lock=False)
                    if (output['disposition'] == 'historical_archive' and match
                            and not to_shape(match[1].geometry).equals(shape(output['geometry']))):
                        output.update(outcome='unresolved', reasons=[*output['reasons'],
                            'historical_geometry_disagreement'])
        return {'status': 'ready', 'database_writes_performed': False, 'outputs': outputs}
    with Session(engine) as db, db.begin():
        from app.services.news_history_protection import protected_fingerprints, verify_protected
        before = protected_fingerprints(db)
        if authorization is not None:
            authorization.validate(engine, 'save_archives', sha(policy), sha(trusted.manifest))
        # A second invocation waits for the first bounded geometry/save transaction.
        db.execute(text("SET LOCAL lock_timeout = '30000'"))
        require(db.scalar(text('SELECT current_database()')) == confirmed_database, 'historical_output_target_mismatch')
        authenticate_policy(package, trusted, engine, policy, policy_sha256, confirmed_database)
        # Dataset/session lock also serializes fallback selection and archive ownership.
        lock = int(sha({'dataset': policy['dataset_id'], 'session': policy['demonstration_session_id']})[:15], 16)
        db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': lock})
        records = _runs(db, package, trusted, sources)
        for run, _version in records:
            db.scalar(select(NewsExtractionRun).where(NewsExtractionRun.id == run.id).with_for_update())
        outputs = qualify_outputs(db, package, trusted, policy, now=now, sources=sources, placement_service=placement_service)
        if authorization is not None:
            require(all(o['disposition'] in (None, 'historical_archive') for o in outputs),
                'historical_shared_archive_only_required')
        by_id = {r.id: (r, v) for r, v in records}
        from app.services.news_ner_durable.adapter import verify_saved_result
        persisted = []
        for output in outputs:
            run, version = by_id[output['run_id']]
            if output['claim_index'] is None:
                persisted.append(output); continue
            result = verify_saved_result(RunEvidence.from_records(run, version), run.result, trusted)
            claim = result.claims[output['claim_index']]
            source = _source(db, run, output['claim_index'], claim, now)
            fingerprint = sha({'version': VERSION, 'policy': policy_sha256, 'group': output['group_id']})
            previous = db.scalar(select(NewsClaimEvaluation).where(NewsClaimEvaluation.claim_source_id == source.id,
                NewsClaimEvaluation.policy_fingerprint == fingerprint))
            if previous is not None:
                require(previous.status == 'completed' and previous.result.get('schema_version') == VERSION,
                        'historical_output_state_conflict')
                persisted.append(previous.result); continue
            if output['outcome'] == 'geometry_qualified':
                from app.services.news_historical_interpretation import historical_placement_claim
                placement_claim, _adapter = historical_placement_claim(result, output['group_id'])
                output = _materialize(db, package, trusted, output, run, version, placement_claim, now)
            db.add(NewsClaimEvaluation(claim_source_id=source.id, policy_fingerprint=fingerprint,
                status='completed', attempt_count=0, result=output, created_at=now, updated_at=now, completed_at=now))
            persisted.append(output)
        db.flush()
        if authorization is not None and os.environ.get('LANES_HISTORY_RESOURCE_PROFILE') == 'cloud-run-v1':
            from app.services.news_history_resources import checkpoint
            checkpoint()
        verify_protected(before, protected_fingerprints(db))
        return {'status': 'completed', 'database_writes_performed': True, 'outputs': json.loads(json.dumps(persisted))}
