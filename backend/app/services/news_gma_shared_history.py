"""Explicit GMA-only inactive archives from immutable, shared-depth evidence.

No provider, inference, correction, activation or operational-policy fallback.
The old continuation grants and finalized evaluations remain immutable.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
from typing import Any

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import shape
from shapely.ops import unary_union
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.crud.news_publication import NewsPublicationError
from app.models.news import NewsArticleVersion, NewsExtractionRun
from app.models.news_publication import NewsClaimEvaluation, NewsClaimSource
from app.models.report import FloodAvoidanceZone
from app.services.news_ner_durable.contracts import RunEvidence, sha
from app.services.news_ner_durable.resolution import ResolutionError, ResolvedMention, quote_options, targets

VERSION = 'gma-shared-depth-history-v1'
SESSION = 'gma-shared-history-20261023-v1'
GROUPS = ('resolved-n13', 'resolved-n14', 'resolved-n16', 'resolved-n17', 'resolved-n18')


def depth_policy() -> dict:
    from app.services.flood_depth import FLOOD_DEPTH_MEASUREMENTS
    return {'schema_version': VERSION, 'scope': 'inactive_history_only',
        'groups': list(GROUPS), 'individual_depth': None, 'infer_passability': False,
        'gauges': {key: {'inches': FLOOD_DEPTH_MEASUREMENTS[key].inches,
            'severity': FLOOD_DEPTH_MEASUREMENTS[key].severity.value} for key in ('waist', 'tires')}}


def need(condition: bool, code: str) -> None:
    if not condition:
        raise NewsPublicationError(code)


def shared_depth_attributes(result: Any, group: dict, *, context: RunEvidence) -> tuple[dict, dict]:
    """Classify only exact, cited shared headings; never assign road depth."""
    from app.services.news_ner_durable.scoped_resolution import source_layout, CONTRACT
    from app.services.taglish_extraction_service import extract_depth_from_text, NUMERIC_DEPTH_PATTERN
    from app.services.flood_depth import get_flood_depth_measurement
    need(group['group_id'] in GROUPS and group['disposition'] == 'historical_archive',
         'shared_depth_archive_only')
    source = context.source()
    payload = result.provenance['llm_resolution']
    target_id = group['group_id'].removeprefix('resolved-')
    need(group['target_entity_ids'] == [target_id], 'shared_depth_target_invalid')
    rows = [r for r in payload['results'] if r['target_id'] == target_id]
    need(len(rows) == 1, 'shared_depth_target_invalid')
    row = ResolvedMention.model_validate_json(json.dumps(rows[0]), strict=True)
    outcomes = [r for r in payload['row_outcomes'] if r['target_id'] == target_id]
    need(len(outcomes) == 1 and outcomes[0]['outcome'] == 'accepted' and not outcomes[0]['issues'],
         'shared_depth_row_not_accepted')
    need(row.verdict == 'observed' and row.depth_scope == 'shared' and bool(row.depth_text)
         and row.status in {'active', 'rising', 'receding'} and row.time_role == 'observation'
         and not row.contradictory, 'shared_depth_source_not_supported')
    candidates = targets(result)
    layout = source_layout(source.article_text, candidates)
    need(payload['identity'].get('evidence_contract') == CONTRACT
         and payload['source_layout_sha256'] == sha(layout), 'shared_depth_layout_changed')
    navigation = next(r for r in layout['targets'] if r['target_id'] == target_id)
    heading = navigation['list_context'].get('depth_heading')
    options = quote_options(source.article_text)
    refs = list(row.depth_evidence)
    need(len(refs) == len(set(refs)) and all(type(i) is int and 0 <= i < len(options) for i in refs),
         'shared_depth_references_invalid')
    need(heading is not None and heading in refs and len(navigation['target_passages']) == 1
         and set(navigation['target_passages']) <= set(refs) and not navigation['context_only_heading'],
         'shared_depth_membership_missing')
    need(set(refs) == {heading, *navigation['target_passages']}, 'shared_depth_cross_scope_evidence')
    phrase = options[heading]['quote']
    need(row.depth_text in phrase, 'shared_depth_heading_mismatch')
    _, gauge, _, reasons = extract_depth_from_text(phrase)
    need(gauge in depth_policy()['gauges'] and not reasons
         and len(list(NUMERIC_DEPTH_PATTERN.finditer(phrase))) == 1
         and not re.search(r'\b(?:about|around|approximately|roughly|up to|as high as|between|or)\b', phrase, re.I),
         'shared_depth_measurement_unresolved')
    # Also bind the provider's raw phrase to the same exact gauge.
    _, row_gauge, _, row_reasons = extract_depth_from_text(row.depth_text)
    need(row_gauge == gauge and not row_reasons, 'shared_depth_measurement_conflict')
    expected = 'waist' if target_id in {'n13', 'n14'} else 'tires'
    need(gauge == expected, 'shared_depth_measurement_conflict')
    claim = result.claims[group['claim_index']]
    need(claim.depth_canonical is None and claim.depth_raw == row.depth_text
         and claim.road_passability == 'unknown' and row.access == 'unknown', 'shared_depth_scalar_or_access_changed')
    audit = group['source_check'].get('evidence') or {}
    need(audit.get('depth', {}).get('raw') == row.depth_text
         and audit.get('depth', {}).get('canonical') is None, 'shared_depth_audit_changed')
    members = sorted(n['target_id'] for n in layout['targets']
        if n['list_context'].get('depth_heading') == heading and not n['context_only_heading']
        and any(m['id'] == n['target_id'] and m['label'] == 'ROAD' for m in candidates))
    selected_members = sorted(g.removeprefix('resolved-') for g in GROUPS
        if any(n['target_id'] == g.removeprefix('resolved-')
               and n['list_context'].get('depth_heading') == heading for n in layout['targets']))
    proof = {'schema_version': VERSION, 'policy_sha256': sha(depth_policy()),
        'target_id': target_id, 'scope': 'shared', 'raw': row.depth_text,
        'heading_passage': heading, 'member_target_ids': members, 'selected_member_target_ids': selected_members,
        'evidence_refs': refs, 'evidence': [options[i] for i in refs], 'source_layout_sha256': sha(layout),
        'input_sha256': context.input_fingerprint, 'resolution_sha256': sha(payload),
        'gauge_for_severity_only': gauge, 'severity': get_flood_depth_measurement(gauge).severity.value,
        'individual_depth': None, 'passability_inferred': False}
    return {'severity_override': proof['severity'], 'depth_override': None,
        'passable_vehicles_override': None}, proof


@dataclass(frozen=True)
class SharedHistoryAuthority:
    policy: dict
    policy_sha256: str
    trusted: Any

    def delegate(self) -> Any:
        from app.services.news_gma_scoped_continuation import VERSION as OLD_VERSION
        from app.services.news_gma_scoped_budget import SESSION as OLD_SESSION
        from app.services.news_three_article_pilot import PilotAuthority
        policy = {**self.policy, 'schema_version': OLD_VERSION,
            'session_id': OLD_SESSION, 'allowed_operations': ['archive']}
        return PilotAuthority(policy, sha(policy), self.trusted)

    def validate(self, engine: Any) -> None:
        p = self.policy
        if (sha(p) != self.policy_sha256 or p.get('schema_version') != VERSION
                or p.get('session_id') != SESSION or p.get('historical_depth_policy') != depth_policy()
                or p.get('allowed_operations') not in (['archive_preview'], ['archive_apply'])
                or p.get('allowed_group_ids') != list(GROUPS) or p.get('allowed_run_ids') != [380]
                or p.get('active_output_allowed') is not False or p.get('live_publication_allowed') is not False
                or any(not isinstance(p.get(k), str) or re.fullmatch(r'[a-f0-9]{64}', p[k]) is None
                    for k in ('saved_result_sha256', 'resolution_sha256', 'retained_bundle_sha256', 'depth_evidence_sha256'))):
            raise ResolutionError('shared_history_authority_invalid')
        d = self.delegate()
        d.validate(engine)

    def validate_session(self, db: Session, *, apply: bool) -> tuple:
        self.validate(db.get_bind())
        if self.policy['allowed_operations'] != ['archive_apply' if apply else 'archive_preview']:
            raise ResolutionError('shared_history_operation_not_authorized')
        d = self.delegate()
        d.validate_session(db, (380,), self.policy_sources, operation='archive')
        from app.services.news_ner_durable.assets import with_resolution_assets
        from app.services.news_ner_durable.adapter import verify_saved_result
        run = db.get(NewsExtractionRun, 380)
        version = db.get(NewsArticleVersion, 574)
        if (run.status != 'completed' or sha(run.result) != self.policy['saved_result_sha256']
                or sha(run.result['provenance']['llm_resolution']) != self.policy['resolution_sha256']):
            raise ResolutionError('shared_history_saved_result_changed')
        derived = with_resolution_assets(self.trusted, self.policy['resolver'])
        context = RunEvidence.from_records(run, version)
        result = verify_saved_result(context, run.result, derived)
        if tuple(g['group_id'] for g in result.projection['groups']) != GROUPS:
            raise ResolutionError('shared_history_groups_changed')
        return run, version, derived, context, result

    @property
    def policy_sources(self) -> tuple:
        from app.services.news_sources import load_news_sources
        return load_news_sources()


def evaluation_identity(authority: SharedHistoryAuthority, group_id: str) -> str:
    return sha({'schema': VERSION, 'session': SESSION, 'run_id': 380, 'group_id': group_id,
        'result': authority.policy['saved_result_sha256'], 'depth_policy': sha(depth_policy())})


def _qualify(db: Session, authority: SharedHistoryAuthority, *, apply: bool,
             placement_service: Any = None) -> tuple:
    from app.services.news_pilot_outputs import PilotPackage
    from app.services.news_historical_outputs import (qualify_outputs, _reviewable_match, archive_assumed_closure)
    from app.services.news_historical_interpretation import historical_placement_claim
    run, version, derived, context, result = authority.validate_session(db, apply=apply)
    package = PilotPackage(authority, db)
    if apply:
        # Match locks precede lookup and insertion, in a deterministic order.
        keys = []
        for group in result.projection['groups']:
            claim, _ = historical_placement_claim(result, group['group_id'])
            keys.append(sha({'scope': 'historical-archive-match-v1',
                'road': (claim.canonical_road or claim.raw_place_name).casefold(),
                'city': (claim.canonical_city or '').casefold(),
                'day': group['normalizations']['time']['occurrence_date']}))
        for key in sorted(set(keys)):
            db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': int(key[:15], 16)})
    outputs = qualify_outputs(db, package, derived, authority.policy,
        now=datetime.fromisoformat(authority.policy['previewed_at']), sources=authority.policy_sources,
        placement_service=placement_service, records=[(run, version)], archive_attributes=shared_depth_attributes)
    proofs = {o['group_id']: o.get('shared_depth_evidence') for o in outputs}
    if sha(proofs) != authority.policy['depth_evidence_sha256']:
        raise ResolutionError('shared_history_evidence_changed')
    for output in outputs:
        if output['outcome'] != 'geometry_qualified':
            continue
        claim, _ = historical_placement_claim(result, output['group_id'])
        match = _reviewable_match(db, package, output, claim, lock=apply)
        output['matched_event_id'] = match[0].id if match else None
        if match:
            footprints = list(db.scalars(select(FloodAvoidanceZone).where(FloodAvoidanceZone.event_id == match[0].id)))
            if not unary_union([to_shape(z.geometry) for z in footprints]).equals(shape(output['geometry'])):
                output.update(outcome='unresolved', reasons=[*output['reasons'], 'historical_geometry_disagreement'])
        overlap = db.scalar(select(FloodAvoidanceZone.id).where(FloodAvoidanceZone.is_active.is_(True),
            func.ST_Intersects(FloodAvoidanceZone.geometry, from_shape(shape(output['geometry']), srid=4326))).limit(1))
        if overlap:
            output.update(outcome='unresolved', reasons=[*output['reasons'], 'shared_history_active_overlap'])
        timing = output['interpretation']['time']; clearance = output['interpretation']['closure']
        assumed_end, basis = archive_assumed_closure(timing, clearance)
        output['proposed_closure'] = {'ended_at': clearance.get('observed_at') or
            (assumed_end.isoformat() if assumed_end else None),
            'basis': 'original_history' if match else 'source_supported' if clearance.get('observed_at') else basis}
    return outputs, package, derived, run, version, result


def archive_outputs(engine: Any, authority: SharedHistoryAuthority, *, apply: bool = False,
                    placement_service: Any = None, before_commit: Any = None) -> dict:
    from app.crud.news_historical_processing import readonly_historical_session
    from app.services.news_historical_outputs import _materialize
    from app.services.news_historical_interpretation import historical_placement_claim
    from app.services.news_history_protection import protected_fingerprints, verify_protected
    if type(authority) is not SharedHistoryAuthority:
        raise ResolutionError('shared_history_authority_required')
    if not apply:
        with readonly_historical_session(engine, engine.url.database) as db:
            outputs, *_ = _qualify(db, authority, apply=False, placement_service=placement_service)
            return {'status': 'preview', 'outputs': outputs, 'outputs_sha256': sha(outputs),
                'provider_requests': 0, 'database_writes': 0}
    with Session(engine) as db, db.begin():
        db.execute(text("SET LOCAL lock_timeout='30000'"))
        db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': int(sha('three-article-pilot')[:15], 16)})
        # Operational writers do not all use the historical advisory namespace.
        # Keep their zone inserts/lifecycle changes outside the match/insert
        # window as well. Ordinary SELECT readers continue during this lock.
        db.execute(text('LOCK TABLE flood_events, flood_avoidance_zones IN SHARE ROW EXCLUSIVE MODE'))
        before = protected_fingerprints(db)
        outputs, package, derived, run, version, result = _qualify(db, authority, apply=True, placement_service=placement_service)
        sources = list(db.scalars(select(NewsClaimSource).where(NewsClaimSource.extraction_run_id == 380)))
        source_by_ordinal = {s.claim_ordinal: s for s in sources}
        if set(source_by_ordinal) != set(range(5)):
            raise ResolutionError('shared_history_existing_sources_changed')
        from app.crud.news_evaluation import canonical_claim_sha256
        if any(source_by_ordinal[i].claim_sha256 != canonical_claim_sha256(result.claims[i]) for i in range(5)):
            raise ResolutionError('shared_history_existing_sources_changed')
        previous = {o['group_id']: db.scalar(select(NewsClaimEvaluation).where(
            NewsClaimEvaluation.claim_source_id == source_by_ordinal[o['claim_index']].id,
            NewsClaimEvaluation.policy_fingerprint == evaluation_identity(authority, o['group_id']))) for o in outputs}
        if any(previous.values()):
            if not all(v is not None and v.status == 'completed'
                and v.result.get('approved_preview_sha256') == authority.policy.get('outputs_sha256')
                and v.result.get('archive_policy_sha256') == sha(depth_policy()) for v in previous.values()):
                raise ResolutionError('shared_history_partial_or_changed_completion')
            return {'status': 'completed', 'outputs': [{**v.result, 'repeat': True} for v in previous.values()],
                'provider_requests': 0, 'database_writes': 0, 'active_instances_created': 0}
        if not authority.policy.get('outputs_sha256') or sha(outputs) != authority.policy['outputs_sha256']:
            raise ResolutionError('shared_history_preview_changed')
        now = datetime.now(timezone.utc); persisted = []
        for original in outputs:
            output = deepcopy(original)
            claim, _ = historical_placement_claim(result, output['group_id'])
            if output['outcome'] == 'geometry_qualified':
                output = _materialize(db, package, derived, output, run, version, claim, now)
            output.update(approved_preview_sha256=authority.policy['outputs_sha256'], archive_policy_sha256=sha(depth_policy()))
            db.add(NewsClaimEvaluation(claim_source_id=source_by_ordinal[output['claim_index']].id,
                policy_fingerprint=evaluation_identity(authority, output['group_id']), status='completed', attempt_count=0,
                result=output, created_at=now, updated_at=now, completed_at=now))
            persisted.append(output)
        db.flush()
        verify_protected(before, protected_fingerprints(db))
        if before_commit is not None:
            before_commit(db)
        return {'status': 'completed', 'outputs': persisted, 'provider_requests': 0,
            'database_writes': True, 'active_instances_created': 0}
