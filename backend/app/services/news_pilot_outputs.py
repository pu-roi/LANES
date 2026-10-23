"""Paired ended archives and separate active instances, one atomic article batch."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimEvaluation
from app.models.report import FloodAvoidanceZone, FloodEventTimelineEntry as Timeline
from app.services.historical_news_metadata import ENTRY
from app.services.news_historical_outputs import qualify_outputs, _materialize, _source, _reviewable_match
from app.services.news_ner_durable.adapter import verify_saved_result
from app.services.news_ner_durable.assets import with_resolution_assets
from app.services.news_ner_durable.contracts import RunEvidence, sha
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_three_article_pilot import PilotAuthority


class PilotPackage:
    """Adapter for historical qualification, independent of deleted legacy run IDs."""
    def __init__(self, authority: PilotAuthority, db: Session) -> None:
        self.captures = tuple(deepcopy(authority.policy['inputs']))
        self.manifest = {'dataset_id': 'three-article-september-2026-v1',
            'demonstration_session_id': authority.policy['session_id'], 'candidates': []}
        self.documents = {'inventory.json': {'sources': [
            {'version_id': i['source_version_id'], 'input_snapshot':
                db.get(NewsArticleVersion, i['source_version_id']).input_snapshot}
            for i in self.captures]}}
        self.manifest_sha256 = sha({'manifest': self.manifest, 'captures': self.captures})

    def validate(self) -> None:
        if sha({'manifest': self.manifest, 'captures': self.captures}) != self.manifest_sha256:
            raise ResolutionError('pilot_package_changed')


def _qualify(db: Session, authority: PilotAuthority, run_id: int, sources: tuple,
             placement_service: object | None = None, *, operation: str = 'outputs') -> tuple:
    authority.validate_session(db, (run_id,), sources, operation=operation)
    derived = with_resolution_assets(authority.trusted, authority.policy['resolver'])
    if derived.pipeline_version != authority.policy['resolved_pipeline_version']:
        raise ResolutionError('pilot_resolved_assets_changed')
    run = db.get(NewsExtractionRun, run_id)
    version = db.get(NewsArticleVersion, run.article_version_id)
    if run.status != 'completed':
        raise ResolutionError('pilot_completed_correction_required')
    result = verify_saved_result(RunEvidence.from_records(run, version), run.result, derived)
    if 'llm_resolution' not in result.provenance:
        raise ResolutionError('pilot_gemini_result_required')
    package = PilotPackage(authority, db)
    now = datetime.fromisoformat(authority.policy['previewed_at'])
    outputs = qualify_outputs(db, package, derived, authority.policy, now=now,
        sources=sources, placement_service=placement_service, records=[(run, version)])
    return outputs, package, derived, run, version, result


def pilot_outputs(engine: object, authority: PilotAuthority, run_id: int, *, sources: tuple,
                  apply: bool = False, placement_service: object | None = None) -> dict:
    if type(authority) is not PilotAuthority:
        raise ResolutionError('pilot_output_authority_required')
    from app.crud.news_historical_processing import readonly_historical_session
    if not apply:
        with readonly_historical_session(engine, engine.url.database) as db:
            outputs, *_ = _qualify(db, authority, run_id, sources, placement_service)
            return {'status': 'preview', 'outputs': outputs, 'outputs_sha256': sha(outputs), 'database_writes': 0}
    with Session(engine) as db, db.begin():
        from app.services.news_history_protection import protected_fingerprints, verify_protected
        # All pilot article batches share this transaction lock; per-incident locks
        # in the archive writer also coordinate with other historical importers.
        db.execute(text("SET LOCAL lock_timeout='30000'"))
        db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': int(sha('three-article-pilot')[:15], 16)})
        before = protected_fingerprints(db)
        outputs, package, derived, run, version, result = _qualify(db, authority, run_id, sources, placement_service)
        if not authority.policy.get('outputs_sha256') or sha(outputs) != authority.policy['outputs_sha256']:
            raise ResolutionError('pilot_output_preview_changed')
        now = datetime.now(timezone.utc)
        persisted = []
        for output in outputs:
            if output['claim_index'] is None:
                persisted.append(output)
                continue
            from app.services.news_historical_interpretation import historical_placement_claim
            claim, _ = historical_placement_claim(result, output['group_id'])
            source = _source(db, run, output['claim_index'], result.claims[output['claim_index']], now)
            fingerprint = sha({'schema': 'paired-pilot-output-v1', 'session': authority.policy['session_id'],
                               'run_id': run.id, 'group_id': output['group_id'], 'result': sha(run.result)})
            previous = db.scalar(select(NewsClaimEvaluation).where(
                NewsClaimEvaluation.claim_source_id == source.id,
                NewsClaimEvaluation.policy_fingerprint == fingerprint))
            if previous is not None:
                if previous.status != 'completed':
                    raise ResolutionError('pilot_output_state_conflict')
                persisted.append({**previous.result, 'repeat': True})
                continue
            archive = output
            active = None
            if output['outcome'] == 'geometry_qualified':
                # Another active presentation instance can only be reused after
                # matching its linked real archive; ordinary overlaps stay unresolved.
                match = _reviewable_match(db, package, output, claim)
                ordinary_overlap = db.scalar(select(FloodAvoidanceZone.id).where(
                    FloodAvoidanceZone.is_active.is_(True),
                    func.ST_Intersects(FloodAvoidanceZone.geometry, from_shape(shape(output['geometry']), srid=4326)),
                    ~select(Timeline.id).where(Timeline.event_id == FloodAvoidanceZone.event_id,
                        Timeline.entry_type == ENTRY,
                        Timeline.snapshot_json['demonstration_session_id'].as_string() == authority.policy['session_id'],
                        Timeline.snapshot_json['disposition'].as_string() == 'active_demo',
                        Timeline.snapshot_json['original_event_id'].as_integer() == (match[0].id if match else -1),
                        Timeline.snapshot_json['geometry_sha256'].as_string() == sha(output['geometry'])).exists()))
                if output['outcome'] == 'unresolved':
                    archive = output
                elif ordinary_overlap:
                    archive = {**output, 'outcome': 'unresolved', 'reasons': [*output['reasons'], 'pilot_active_overlap']}
                else:
                    archive = _materialize(db, package, derived, deepcopy(output), run, version, claim, now)
                if archive['outcome'] in {'saved', 'reused'}:
                    # The archive ID, not article/group identity, owns the active
                    # instance. Different articles describing it reuse that instance.
                    existing = db.scalar(select(Timeline).where(Timeline.entry_type == ENTRY,
                        Timeline.snapshot_json['disposition'].as_string() == 'active_demo',
                        Timeline.snapshot_json['demonstration_session_id'].as_string() == authority.policy['session_id'],
                        Timeline.snapshot_json['original_event_id'].as_integer() == archive['event_id']))
                    if existing:
                        if existing.snapshot_json['geometry_sha256'] != sha(output['geometry']):
                            raise ResolutionError('pilot_active_geometry_changed')
                        active = {'outcome': 'reused', 'event_id': existing.event_id,
                            'zone_ids': list(db.scalars(select(FloodAvoidanceZone.id).where(
                                FloodAvoidanceZone.event_id == existing.event_id)))}
                    else:
                        active = _materialize(db, package, derived,
                            {**deepcopy(output), 'disposition': 'active_demo'}, run, version, claim, now)
                        # The archive match is independently checked by _materialize;
                        # require the resulting immutable lineage to name this archive.
                        lineage = db.scalar(select(Timeline).where(Timeline.event_id == active['event_id'],
                            Timeline.entry_type == ENTRY))
                        if lineage is None or lineage.snapshot_json['original_event_id'] != archive['event_id']:
                            raise ResolutionError('pilot_archive_active_link_mismatch')
            receipt = {'schema_version': 'paired-pilot-output-v1', 'group_id': output['group_id'],
                       'archive': archive, 'active': active}
            db.add(NewsClaimEvaluation(claim_source_id=source.id, policy_fingerprint=fingerprint,
                status='completed', attempt_count=0, result=receipt, created_at=now, updated_at=now, completed_at=now))
            persisted.append(receipt)
        db.flush()
        verify_protected(before, protected_fingerprints(db))
        return {'status': 'completed', 'outputs': persisted, 'database_writes': True}
