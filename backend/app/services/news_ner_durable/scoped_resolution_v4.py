"""Source-bound inline locality ownership; original provider rows stay immutable."""
from __future__ import annotations

import re
from copy import deepcopy

from . import scoped_resolution_v3 as v3
from .contracts import sha
from .resolution import quote_options,targets

VERSION = 'native-gemini-resolution-v4'
CONTRACT = 'scoped-quote-options-v4'
INSTRUCTIONS = v3.INSTRUCTIONS + """
INLINE LOCALITY CONTRACT v4:
An inline_locality_owner identifies a barangay qualifier inside one exact road-list
entry, not a separate area-wide flood report. Keep that target row as unsupported
context; return the independently observed road with its supported barangay.
Do not suppress genuine locality-only reports, distinct observations, conflicting
times or ambiguous ownership. Context hints do not replace any required citation.
"""


def source_layout(text: str, candidates: list[dict]) -> dict:
    layout=v3.source_layout(text,candidates);layout['schema_version']=CONTRACT
    options=quote_options(text);scopes={s['target_id']:s for s in layout['targets']}
    for locality in candidates:
        if locality['label']!='BARANGAY':continue
        ids=scopes[locality['id']]['target_passages']
        if len(ids)!=1:continue
        index=ids[0];q=options[index]
        roads=[m for m in candidates if m['label']=='ROAD' and scopes[m['id']]['target_passages']==ids]
        if len(roads)!=1:continue
        road=roads[0]
        # A road followed directly by a named barangay and detail separator.
        # Independent narrative clauses and multiple-road entries are excluded.
        if (road['end']>locality['start'] or text[q['start']:road['start']].strip(' \t-•')
                or text[road['end']:locality['start']].strip(' \t,')
                or not re.match(r'(?i)^(?:brgy\.?|barangay)\s+',locality['text'])
                or not re.match(r'\s*[-–—]\s*\S',text[locality['end']:q['end']])
                or re.search(r'(?i)\b(?:entire|whole|throughout|buong|also|separately)\b',q['quote'])
                or scopes[road['id']]['city_context'] is None):
            continue
        scopes[locality['id']]['inline_locality_owner']={'target_id':road['id'],'passage_index':index,
            'locality_start':locality['start'],'locality_end':locality['end']}
    return layout


def evaluate_rows(source: object, baseline: object, rows: list | tuple, catalog: object, *,
                  reviewed_time_context: bool = False) -> tuple:
    # First run every unchanged strict field/reference check. Context cannot
    # conceal an invalid provider fact or an unsupported owning road.
    claims,groups,audits,outcomes,_=v3.evaluate_rows(source,baseline,rows,catalog,
        reviewed_time_context=reviewed_time_context)
    layout=source_layout(source.article_text,targets(baseline));options=quote_options(source.article_text)
    scopes={r['target_id']:r for r in layout['targets']};by_row={r.target_id:r for r in rows}
    by_group={g['target_entity_ids'][0]:g for g in groups};by_outcome={o['target_id']:o for o in outcomes}
    for target,scope in scopes.items():
        owner=scope.get('inline_locality_owner')
        if not owner or target not in by_group or owner['target_id'] not in by_group:continue
        child_group=by_group[target];road_group=by_group[owner['target_id']]
        child,road=claims[child_group['claim_index']],claims[road_group['claim_index']]
        child_row,road_row=by_row[target],by_row[owner['target_id']]
        equal=('canonical_city','canonical_barangay','event_time_resolved','condition','depth_raw',
               'depth_canonical','depth_inches','depth_meters','road_passability','is_historical','is_forecast','is_negated')
        if (any(getattr(child,k)!=getattr(road,k) for k in equal)
                or road.event_time_resolved is None or not road.canonical_barangay
                or child_row.depth_scope!=road_row.depth_scope
                or child_row.time_role!=road_row.time_role):continue
        index=owner['passage_index']
        # Every dimension must use the shared entry; other evidence is limited
        # to the governing city, date and article-level flood introduction.
        allowed={index,*layout['date_candidates'],*layout['affirmative_status_candidates']}
        city=scope.get('city_context')
        if city:allowed.add(city['option_index'])
        for other in targets(baseline):
            if other['id']!=owner['target_id'] and other['label'] in {'ROAD','LANDMARK'}:
                allowed.difference_update(scopes[other['id']]['target_passages'])
        cited={i for field in ('place','status','time','depth','access','section')
            for i in getattr(child_row,field+'_evidence')}
        if not cited<=allowed or any(index not in getattr(child_row,field+'_evidence')
            for field in ('place','status','time','depth','access')):continue
        if any(i!=index and re.search(r'(?i)\b(?:entire|whole|throughout|buong)\b',options[i]['quote']) for i in cited):continue
        child_group.update(disposition='context_only',claim_index=None,reasons=['inline_locality_context'])
        child_group['normalizations']['inline_locality_owner']=deepcopy(owner)
        by_outcome[target].update(outcome='context_only',issues=[],context_owner=deepcopy(owner),
            reason='inline_locality_context')
    retained=[(g['claim_index'],g['target_entity_ids'][0]) for g in groups if g['claim_index'] is not None]
    remap={old:new for new,(old,_) in enumerate(retained)}
    for group in groups:
        if group['claim_index'] is not None:group['claim_index']=remap[group['claim_index']]
    return [claims[i] for i,_ in retained],groups,[audits[i] for i,_ in retained],outcomes,sha(layout)
