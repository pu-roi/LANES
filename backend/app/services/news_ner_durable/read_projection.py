"""Compact persisted card selection; original graph and compatibility stay intact."""
from __future__ import annotations

from collections import Counter

from app.schemas.news_ner_result import NativeReadGroup, NativeReadDisplay, NativeReadProjection
from app.services.news_evidence_policy import has_flood_observation
from app.services.news_ner.context_association_v42 import segments
from .contracts import NativeInput, MAX_QUOTE
from .fields import depth_fields, time_fields, access_fields
from .locality import Catalog, resolve_locality


def build_read_projection(source: NativeInput, result: object, catalog: Catalog) -> NativeReadProjection:
    if 'llm_resolution' in result.provenance:
        return NativeReadProjection(groups=[NativeReadGroup(group_id=g['group_id'],claim_index=g['claim_index'])
            for g in result.projection['groups'] if g['claim_index'] is not None],omitted_counts={})
    graph = result.native.graph.model_dump(mode='json', by_alias=True)
    mentions = {m['id']: m for m in graph['mentions']}
    facts = {f['id']: f for f in graph['facts']}
    bounds = segments(source.article_text, graph['mentions'])
    groups = []; omitted = Counter()
    for group in result.projection['groups']:
        if group['disposition'] == 'context_only':
            omitted['location_context_only'] += 1
            continue
        if group['claim_index'] is not None:
            groups.append(NativeReadGroup(group_id=group['group_id'], claim_index=group['claim_index']))
            continue
        targets = [mentions[i] for i in group['target_entity_ids']]
        fs = [facts[i] for i in group['fact_ids']]
        status = [f for f in fs if f['kind'] == 'status']
        states = {f['value'] for f in status}
        if (not targets or group['scope'] == 'unresolved' or len(states) != 1
                or not states <= {'active', 'rising', 'receding', 'subsided'}
                or any(f['uncertainty'] for f in status)
                or {'photo_caption_only', 'observation_context_unresolved', 'ambiguous_observation_partition'} & set(group['reasons'])
                or not any(has_flood_observation(e['text']) for f in status for e in f['evidence'])):
            omitted['native_observation_not_supported'] += 1
            continue
        localities = [resolve_locality(source.article_text, t, graph, catalog, clause_segments=bounds) for t in targets]
        if any(l['reason'] for l in localities) or len({l['canonical_city'] for l in localities}) != 1:
            omitted['native_locality_not_supported'] += 1
            continue
        evidence = [e for f in fs for e in f['evidence']]
        start = min([t['start'] for t in targets] + [e['start'] for e in evidence])
        end = max([t['end'] for t in targets] + [e['end'] for e in evidence])
        label = ' / '.join(t['text'] for t in targets)
        if end - start > MAX_QUOTE or len(label) > 500:
            omitted['native_display_limit'] += 1
            continue
        depth, _, depth_reasons = depth_fields(fs, graph, source.article_text)
        clock, _, clock_reasons = time_fields(fs, source, graph)
        access, _, access_reasons = access_fields(fs)
        # Display original expressions, including shared/range qualifications.
        raw_depths = list(dict.fromkeys(f['value'] for f in fs if f['kind'] == 'depth' and f['value']))
        raw = ' / '.join(raw_depths) or None
        if raw and len(raw) > 500:
            raw = None; depth_reasons = [*depth_reasons, 'depth_display_limit']
        display = NativeReadDisplay(raw_place_name=label, canonical_city=localities[0]['canonical_city'],
            condition=next(iter(states)), depth_raw=raw, **{k: clock[k] for k in ('event_time_resolved', 'event_time_kind')},
            road_passability=access, evidence_span=(start, end),
            uncertainty_reasons=sorted(set(group['reasons'] + depth_reasons + clock_reasons + access_reasons)))
        groups.append(NativeReadGroup(group_id=group['group_id'], claim_index=None, display=display))
    return NativeReadProjection(groups=groups, omitted_counts=dict(sorted(omitted.items())))
