"""Exact-source repair grants and append-only withdrawal of disputed news archives."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimEvaluation, NewsClaimSource
from app.models.report import FloodEvent, FloodAvoidanceZone, FloodEventTimelineEntry as Timeline, FloodReport
from app.services.news_ner_durable.contracts import RunEvidence, sha
from app.services.news_ner_durable.resolution import ResolutionError

VERSION = 'gma-source-repair-v1'
SESSION = 'gma-source-repair-20261023-v1'
BODY = 'f5ff7d13e255ed82ab9c024bcd1aae02fee4ce5806c4a7411bc818e2f58ed763'
OLD_EVENTS = (71, 72, 73, 74, 75)
SUPERSEDED = 'news_source_superseded'


def superseded_event(event_column: Any = None) -> Any:
    column = FloodEvent.id if event_column is None else event_column
    return select(Timeline.id).where(Timeline.event_id == column, Timeline.entry_type == SUPERSEDED,
        Timeline.snapshot_json['schema_version'].as_string() == VERSION).correlate_except(Timeline).exists()


def delegate(authority: Any) -> Any:
    from app.services.news_three_article_pilot import PilotAuthority
    p = {**authority.policy, 'schema_version': 'news-three-article-pilot-v1', 'allowed_operations': ['resolve']}
    return PilotAuthority(p, sha(p), authority.trusted)


def validate_authority(authority: Any, engine: Any) -> None:
    p = authority.policy
    if (sha(p) != authority.policy_sha256 or p.get('schema_version') != VERSION
            or p.get('session_id') != SESSION or p.get('allowed_operations') not in (['ner'], ['count'], ['resolve'], ['archive'])
            or p.get('allowed_article_ids') != [47] or p.get('source_version_id') != 140
            or p.get('native_version_id') != 569 or p.get('source_body_sha256') != BODY
            or p.get('old_event_ids') != list(OLD_EVENTS) or p.get('active_output_allowed') is not False):
        raise ResolutionError('source_repair_authority_invalid')
    selected = [i for i in p['inputs'] if i['article_id'] == 47]
    if len(selected) != 1 or selected[0]['source_version_id'] != 140 or selected[0]['body_sha256'] != BODY:
        raise ResolutionError('source_repair_capture_invalid')
    delegate(authority).validate(engine)


def validate_session(authority: Any, db: Session, run_ids: tuple | None, sources: tuple | None,
                     operation: str) -> None:
    authority.validate(db.get_bind())
    p = authority.policy
    if p['allowed_operations'] != [operation]:
        raise ResolutionError('source_repair_operation_invalid')
    delegate(authority).validate_session(db, None, sources, operation='resolve')
    version = db.get(NewsArticleVersion, 569)
    if version is None or version.article_id != 47 or version.input_fingerprint != p['inputs'][0]['native_input_fingerprint']:
        raise ResolutionError('source_repair_native_capture_invalid')
    if run_ids is not None:
        if len(run_ids) != 1:
            raise ResolutionError('source_repair_one_article_required')
        run = db.get(NewsExtractionRun, run_ids[0])
        pipeline = p['resolved_pipeline_version'] if operation == 'archive' else p['pipeline_version']
        if run is None or run.article_version_id != 569 or run.pipeline_version != pipeline or run.mode != 'ner_rules_v1':
            raise ResolutionError('source_repair_run_invalid')
        if operation != 'ner' and (run.status != 'completed' or sha(run.result) != p['parent_result_sha256']):
            raise ResolutionError('source_repair_parent_changed')


def qualify_repair(db: Session, authority: Any, run_id: int, sources: tuple) -> tuple:
    from app.services.news_ner_durable.assets import with_resolution_assets
    from app.services.news_ner_durable.adapter import verify_saved_result
    from app.services.news_pilot_outputs import PilotPackage
    from app.services.news_historical_outputs import qualify_outputs, _reviewable_match, archive_assumed_closure
    from app.services.news_historical_interpretation import historical_placement_claim
    authority.validate_session(db, (run_id,), sources, operation='archive')
    run = db.get(NewsExtractionRun, run_id); version = db.get(NewsArticleVersion, run.article_version_id)
    derived = with_resolution_assets(authority.trusted, authority.policy['resolver'])
    result = verify_saved_result(RunEvidence.from_records(run, version), run.result, derived)
    package = PilotPackage(authority, db)
    outputs = qualify_outputs(db, package, derived, authority.policy,
        now=datetime.fromisoformat(authority.policy['previewed_at']), sources=sources, records=[(run, version)])
    for output in outputs:
        if output['disposition'] not in ('historical_archive', None):
            raise ResolutionError('source_repair_archive_only')
        if output['outcome'] == 'geometry_qualified':
            claim, _ = historical_placement_claim(result, output['group_id'])
            match = _reviewable_match(db, package, output, claim)
            output['matched_event_id'] = match[0].id if match else None
            end, basis = archive_assumed_closure(output['interpretation']['time'], output['interpretation'].get('closure', {}))
            output['proposed_closure'] = {'ended_at': end.isoformat() if end else None, 'basis': basis}
    return outputs, package, derived, run, version, result


def repair_outputs(engine: Any, authority: Any, run_id: int, sources: tuple, *, apply: bool = False) -> dict:
    from app.services.news_historical_outputs import _source, _materialize
    from app.services.news_historical_interpretation import historical_placement_claim
    from app.services.news_history_protection import protected_fingerprints, verify_protected
    with Session(engine) as db, db.begin():
        if apply:
            db.execute(text("SET LOCAL lock_timeout='30000'"))
            db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': int(sha('three-article-pilot')[:15], 16)})
            db.execute(text('LOCK TABLE flood_events, flood_avoidance_zones IN SHARE ROW EXCLUSIVE MODE'))
        else:
            db.execute(text('SET TRANSACTION READ ONLY'))
        outputs, package, derived, run, version, result = qualify_repair(db, authority, run_id, sources)
        markers = list(db.scalars(select(Timeline).where(Timeline.event_id.in_(OLD_EVENTS), Timeline.entry_type == SUPERSEDED)))
        if markers:
            if len(markers) != 5 or any(m.snapshot_json.get('replacement_run_id') != run_id for m in markers):
                raise ResolutionError('source_repair_partial_state')
            saved = list(db.scalars(select(NewsClaimEvaluation.result).join(NewsClaimSource).where(
                NewsClaimSource.extraction_run_id == run_id).order_by(NewsClaimEvaluation.id)))
            if len(saved) != len(outputs):
                raise ResolutionError('source_repair_partial_state')
            return {'status': 'reused', 'outputs': saved, 'database_writes': 0}
        old = list(db.scalars(select(Timeline).where(Timeline.event_id.in_(OLD_EVENTS), Timeline.entry_type == 'historical_import')))
        zones = list(db.scalars(select(FloodAvoidanceZone).where(FloodAvoidanceZone.event_id.in_(OLD_EVENTS))))
        if (len(old) != 5 or len(zones) != 5 or any(z.is_active for z in zones)
                or any(t.snapshot_json.get('run_id') != 380 for t in old)
                or db.scalar(select(FloodReport.id).where(FloodReport.event_id.in_(OLD_EVENTS)).limit(1))
                or sha([t.snapshot_json for t in sorted(old, key=lambda t:t.event_id)]) != authority.policy['old_lineage_sha256']):
            raise ResolutionError('source_repair_old_lineage_changed')
        if not apply:
            return {'status': 'preview', 'outputs': outputs, 'outputs_sha256': sha(outputs),
                'superseded_event_ids': list(OLD_EVENTS), 'database_writes': 0}
        if sha(outputs) != authority.policy.get('outputs_sha256'):
            raise ResolutionError('source_repair_preview_changed')
        before = protected_fingerprints(db);now = datetime.now(timezone.utc)
        saved = []
        for output in outputs:
            ordinal = output['claim_index']
            if ordinal is None:
                saved.append(output); continue
            source = _source(db, run, ordinal, result.claims[ordinal], now)
            if output['outcome'] == 'geometry_qualified':
                claim, _ = historical_placement_claim(result, output['group_id'])
                output = _materialize(db, package, derived, deepcopy(output), run, version, claim, now)
            db.add(NewsClaimEvaluation(claim_source_id=source.id, policy_fingerprint=sha({'schema':VERSION,'run':run_id,'group':output['group_id']}),
                status='completed', attempt_count=0, result=output, created_at=now, updated_at=now, completed_at=now))
            saved.append(output)
        for event_id in OLD_EVENTS:
            db.add(Timeline(event_id=event_id, entry_type=SUPERSEDED, occurred_at=now,
                summary='Source capture replaced after publisher comparison; earlier archive withdrawn from current history.',
                snapshot_json={'schema_version': VERSION, 'session_id': SESSION, 'old_run_id':380,
                    'replacement_run_id':run_id, 'replacement_version_id':version.id, 'replacement_result_sha256':sha(run.result),
                    'source_body_sha256':BODY, 'reason':'indexed_capture_replaced_by_original_publisher',
                    'replacement_event_ids':[o['event_id'] for o in saved if o.get('event_id')]}))
        db.flush();verify_protected(before, protected_fingerprints(db))
        return {'status':'completed', 'outputs':saved, 'superseded_event_ids':list(OLD_EVENTS), 'active_instances_created':0}
