"""Versioned, non-mutating historical evidence adapter; never publishes floods."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import re

from app.services.news_ner_durable.contracts import RunEvidence, sha
from app.services.news_ner_durable.fields import _dates, time_fields, PHT

ADAPTER_VERSION = 'historical-source-interpretation-v2'
TEMPORAL_REASONS = {'missing_supported_observation_time', 'observation_outside_admission_window',
                    'observation_evidence_expired'}


def historical_placement_claim(result: object, group_id: str) -> tuple[object, dict]:
    """Adapt a saved single ROAD target to the existing scalar placement API.

    Original predictions/projection are immutable. Only an exact target spelling
    and one source-local road qualifier are passed in this labeled adapter.
    """
    group = next(g for g in result.projection['groups'] if g['group_id'] == group_id)
    claim = result.claims[group['claim_index']]
    mentions = {m.id: m for m in result.native.graph.mentions}
    targets = [mentions[i] for i in group['target_entity_ids']]
    changes = {}
    if len(targets) == 1 and targets[0].label == 'ROAD' and claim.raw_place_name == targets[0].text:
        if claim.canonical_road is None:
            changes['canonical_road'] = targets[0].text
        if not claim.road_segment_raw:
            from app.services.taglish_extraction_service import ROAD_SEGMENT_PATTERN
            near = re.compile(r'\b(?:near|corner of|at the corner of|at the intersection with)\s+(?:[A-Z][\w.\u2019-]*\s+){1,5}(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Boulevard|Blvd\.?)\b')
            choices = [m for pattern in (ROAD_SEGMENT_PATTERN, near) for m in pattern.finditer(claim.evidence_sentence)]
            # Another observation target between this road and a qualifier
            # prevents ownership by proximity alone.
            if len(choices) == 1:
                match = choices[0]
                start = claim.evidence_sentence_offset[0] + match.start()
                other_targets = {i for g in result.projection['groups'] if g['group_id'] != group_id for i in g['target_entity_ids']}
                if not any(targets[0].end <= mentions[i].start < start for i in other_targets):
                    changes['road_segment_raw'] = match.group()
    return claim.model_copy(update=changes), {'version': 'historical-placement-fields-v1', 'changes': changes,
        'source_evidence_span': list(claim.evidence_sentence_offset)}


@dataclass(frozen=True)
class HistoricalPlacementContext:
    """Historical preview intent; never authorizes operational publication."""
    dataset_id: str
    demonstration_session_id: str
    input_fingerprint: str
    group_id: str
    disposition: str
    occurrence_date: str
    precision: str
    publication_allowed: bool = False


def preview_historical_claim(claim: object, context: HistoricalPlacementContext,
                             trusted: object, placement_service: object | None = None) -> dict | None:
    from app.services.news_historical_processing import require
    from app.services.news_ner_durable.assets import placement_identity
    from app.services.news_placement_preview_service import get_news_placement_preview_service
    require(type(context) is HistoricalPlacementContext and not context.publication_allowed
        and context.disposition in {'historical_archive', 'active_demo'}
        and context.precision in {'date', 'instant'}, 'historical_placement_context_invalid')
    trusted.validate()
    if placement_service is None and trusted.manifest['geography'].get('placement') is None:
        return None
    require(placement_service is not None or trusted.manifest['geography']['placement'] == placement_identity(),
            'historical_placement_assets_changed')
    provider = placement_service or get_news_placement_preview_service()
    return provider.preview(claim).model_dump(mode='json')


def historical_time(source: object, graph: dict, facts: list[dict]) -> dict:
    """Only observation-role evidence can establish an occurrence date."""
    selected = [f for f in facts if f['kind'] == 'time' and f['temporal_role'] == 'observation']
    evidence = [e for f in selected for e in f['evidence']]
    from app.services.news_historical_processing import require
    require(all(type(e['start']) is int and type(e['end']) is int
        and 0 <= e['start'] < e['end'] <= len(source.article_text)
        and source.article_text[e['start']:e['end']] == e['text'] for e in evidence),
        'historical_time_evidence_invalid')
    output = {'precision': 'unknown', 'occurrence_date': None, 'observed_at': None,
              'date_basis': None, 'timezone_basis': None, 'fact_ids': [f['id'] for f in selected],
              'evidence': evidence, 'reasons': []}
    if not selected or any(f['uncertainty'] for f in selected):
        output['reasons'] = ['historical_observation_time_unknown']
        return output
    try:
        context = '\n'.join(e['text'] for e in evidence)
        dates = _dates(context)
        relative = {m.group().casefold() for m in re.finditer(r'\b(?:today|yesterday)\b', context, re.I)}
        if relative:
            if len(relative) != 1 or not source.publication_evidence.timezone_known or source.published_at is None:
                raise ValueError('historical_relative_date_unbound')
            day = source.published_at.astimezone(PHT).date() - timedelta(days='yesterday' in relative)
            if dates and dates != {day}:
                raise ValueError('historical_observation_dates_conflict')
            dates = {day}; basis = 'authenticated_publisher_relative_date'
        else:
            basis = 'explicit_observation_body_date'
        if len(dates) != 1:
            raise ValueError('historical_observation_dates_conflict' if dates else 'historical_observation_date_unknown')
        output.update(precision='date', occurrence_date=next(iter(dates)).isoformat(), date_basis=basis)
        resolved, _, _ = time_fields(selected, source, graph)
        if resolved['event_time_resolved'] is not None:
            output.update(precision='instant', observed_at=resolved['event_time_resolved'].isoformat(),
                          timezone_basis='source_observation_pht_or_utc_plus_08')
        else:
            output['reasons'] = ['historical_observation_instant_unknown']
    except (ValueError, OverflowError) as exc:
        code = str(exc)
        output['reasons'] = [code if code.startswith('historical_') else 'historical_observation_date_invalid']
    return output


def interpret_historical(run: object, version: object, trusted: object, package: object,
                         execution: dict, *, now: datetime, placement_service: object | None = None) -> dict:
    from app.services.news_historical_processing import require
    from app.services.news_ner_durable.adapter import verify_saved_result
    from app.services.news_ner_durable.source_check import check_native_sources
    package.validate(); trusted.validate()
    context = RunEvidence.from_records(run, version)
    require(run.status == 'completed' and run.completed_at is not None, 'historical_run_not_completed')
    capture = next((c for c in package.captures if c['article_id'] == context.article_id
                   and c['native_input_fingerprint'] == context.input_fingerprint), None)
    require(capture is not None and capture['input_snapshot'] == context.input_snapshot,
            'historical_saved_capture_invalid')
    require(execution['parent_manifest_sha256'] == package.manifest_sha256
            and execution['assets_sha256'] == sha(trusted.manifest)
            and execution['pipeline_version'] == trusted.pipeline_version,
            'historical_interpretation_execution_mismatch')
    result = verify_saved_result(context, run.result, trusted)
    graph = result.native.graph.model_dump(mode='json', by_alias=True)
    source = context.source()
    facts = {f['id']: f for f in graph['facts']}
    checks = check_native_sources(run, version, run.result, tuple(range(len(result.claims))), trusted, now=now)
    candidates = [c for c in package.manifest['candidates'] if c['article_id'] == context.article_id]
    groups = []
    for group in result.projection['groups']:
        date = historical_time(source, graph, [facts[i] for i in group['fact_ids']])
        if 'llm_resolution' in result.provenance and group['claim_index'] is not None:
            resolved_claim=result.claims[group['claim_index']]
            if resolved_claim.condition!='subsided':
                observed=resolved_claim.event_time_resolved
                audit=group['normalizations']['audit']['time']
                normalization=group['normalizations']['time']
                day=normalization['occurrence_date']
                date={'precision':'instant' if observed else 'date' if day else 'unknown',
                    'occurrence_date':day,
                    'observed_at':observed.isoformat() if observed else None,
                    'date_basis':normalization['date_basis'] if observed else 'verified_source_calendar_day' if day else None,
                    'timezone_basis':'resolved_manila_source_or_publication_proxy' if observed else None,
                    'fact_ids':[i for i in group['fact_ids'] if facts[i]['kind']=='time'],
                    'evidence':[{'start':e['start'],'end':e['end'],'text':e['quote']} for e in audit['evidence']],
                    'reasons':[] if observed else ['historical_observation_time_unknown']}
        clearance = [facts[i] for i in group['fact_ids'] if facts[i]['kind'] == 'time'
                     and facts[i]['temporal_role'] == 'clearance']
        closure = historical_time(source, graph, [{**f, 'temporal_role': 'observation'} for f in clearance])
        closure['source_clearance_present'] = bool(clearance)
        if closure['observed_at'] is not None and (datetime.fromisoformat(closure['observed_at']) > now
                or date['observed_at'] is not None
                    and datetime.fromisoformat(closure['observed_at']) < datetime.fromisoformat(date['observed_at'])):
            closure.update(precision='unknown', observed_at=None, reasons=['historical_clearance_time_conflict'])
        entry = {'group_id': group['group_id'], 'claim_index': group['claim_index'],
            'scope': group['scope'], 'target_entity_ids': group['target_entity_ids'],
            'fact_ids': group['fact_ids'], 'time': date, 'qualification': 'unresolved',
            'reasons': list(group['reasons']), 'disposition': None, 'source_check': None, 'placement': None,
            'closure': closure}
        index = group['claim_index']
        if index is None or group['disposition'] != 'projected':
            entry['reasons'].append('historical_native_only_or_context_group')
        else:
            claim = result.claims[index]
            # Selection matches the supported named place, never a legacy ordinal/polygon.
            def key(value: str) -> str:
                return ' '.join(re.findall(r'\w+', value.casefold()))
            matching = [c for c in candidates if key(c['target']['road']) in
                {key(claim.raw_place_name), key(claim.canonical_road or '')}
                and key(c['target']['city']).removeprefix('city of ') == key(claim.canonical_city or '').removeprefix('city of ')]
            if len(matching) == 1:
                entry['disposition'] = matching[0]['intended_disposition']
                entry['selected_candidate_id'] = matching[0]['candidate_id']
                entry['candidate_role'] = matching[0]['role']
            elif not matching:
                entry['disposition'] = 'historical_archive'
            else:
                entry['reasons'].append('historical_candidate_selection_ambiguous')
            audit = checks[index]
            entry['source_check'] = audit.model_dump(mode='json')
            if audit.outcome != 'verified' and audit.reason_code not in TEMPORAL_REASONS:
                entry['reasons'].append(audit.reason_code)
            elif 'historical_clearance_time_conflict' in closure['reasons']:
                entry['reasons'].append('historical_clearance_time_conflict')
            elif date['precision'] == 'unknown':
                entry['reasons'].extend(date['reasons'])
            elif (date['occurrence_date'] > now.astimezone(PHT).date().isoformat()
                    or date['observed_at'] is not None and datetime.fromisoformat(date['observed_at']) > now):
                entry['reasons'].append('historical_observation_in_future')
            elif claim.condition == 'subsided':
                entry['reasons'].append('historical_clearance_not_flood_zone_candidate')
            elif entry['disposition'] is not None and len(matching) <= 1:
                # No claim mutation: native extraction already refers to the observed
                # event, while the explicit receipt carries its historical context.
                entry['qualification'] = 'source_qualified_for_historical_placement'
                placement_context = HistoricalPlacementContext(package.manifest['dataset_id'],
                    package.manifest['demonstration_session_id'], context.input_fingerprint,
                    group['group_id'], entry['disposition'], date['occurrence_date'], date['precision'])
                entry['placement_context'] = asdict(placement_context)
                placement_claim, adapter = historical_placement_claim(result, group['group_id'])
                entry['placement_adapter'] = adapter
                entry['placement'] = preview_historical_claim(placement_claim, placement_context, trusted, placement_service)
                if entry['placement'] is None:
                    entry['reasons'].append('historical_placement_assets_not_bound')
                entry['geometry_acceptance'] = 'pending_e2'
        entry['reasons'] = sorted(set(entry['reasons']))
        groups.append(entry)
    return {'schema': 'lanes-historical-interpretation-v1', 'adapter_version': ADAPTER_VERSION,
        'execution_manifest_sha256': sha(execution), 'target_policy_sha256': execution.get('target_policy_sha256'),
        'parent_manifest_sha256': package.manifest_sha256, 'dataset_id': package.manifest['dataset_id'],
        'demonstration_session_id': package.manifest['demonstration_session_id'],
        'run_id': context.run_id, 'article_id': context.article_id, 'article_version_id': context.article_version_id,
        'input_fingerprint': context.input_fingerprint, 'result_sha256': sha(run.result),
        'publication_evidence': source.publication_evidence.model_dump(mode='json'),
        'groups': groups, 'unassigned_fact_ids': [f['fact_id'] for f in result.projection['fact_accounting']
                                                 if f['disposition'] == 'unassigned'],
        'status': 'qualified' if any(g['qualification'] != 'unresolved' for g in groups) else 'unresolved',
        'evaluated_at': now.isoformat(), 'publication_performed': False}
