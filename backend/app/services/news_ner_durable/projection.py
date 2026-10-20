"""Conservative operational projection of an already validated native graph."""
from __future__ import annotations

import re

from app.schemas.news_ner_result import NerProjectedClaim
from app.services.news_evidence_policy import has_flood_observation
from app.services.news_ner.context_association_v42 import segments
from .contracts import MAX_CLAIMS, MAX_QUOTE, FactAccounting, NativeInput, Observation, Projection
from .fields import access_fields, depth_fields, time_fields
from .grouping import observations
from .locality import Catalog, resolve_locality

PLACE_TYPES={'ROAD':'street','BARANGAY':'barangay','CITY':'city','PROVINCE':'province','LANDMARK':'landmark'}
SUPPORTED_STATUS={'active','rising','receding','subsided'}


def project_observations(source: NativeInput, graph: dict, catalog: Catalog) -> tuple[list[NerProjectedClaim], Projection]:
    text=source.article_text;mentions={m['id']:m for m in graph['mentions']};facts={f['id']:f for f in graph['facts']}
    clause_segments=segments(text,graph['mentions'])
    claims=[];groups=[]
    for unit in observations(graph):
        targets=[mentions[i] for i in unit['target_entity_ids']];fs=[facts[i] for i in unit['fact_ids']]
        reasons=[];norm={};status=[f for f in fs if f['kind']=='status'];states={f['value'] for f in status}
        primary=[e for f in status for e in f['evidence']]
        if unit['partition_ambiguous']:reasons.append('ambiguous_observation_partition')
        if len(targets)!=1 or unit['scope'] in ('collective','shared','unresolved'):
            reasons.append('joint_or_collective_requires_native_consumer')
        if any(t['label']=='LOCAL_AREA' for t in targets):reasons.append('local_area_requires_native_consumer')
        if len(states)!=1 or not states<=SUPPORTED_STATUS:reasons.append('status_not_supported' if len(states)<=1 else 'status_conflict')
        if any(f['uncertainty'] for f in status) or any(r['uncertainty'] for r in unit['relations']):reasons.append('observation_context_unresolved')
        if any(re.match(r'^\s*(?:photo|file\s+photo|image|caption|larawan)\s*[:—-]',e['text'],re.I) for e in primary):
            reasons.append('photo_caption_only')
        if not primary or not any(has_flood_observation(e['text']) for e in primary):reasons.append('not_observed_flood_evidence')
        begin=min([t['start'] for t in targets]+[e['start'] for e in unit['evidence']])
        end=max([t['end'] for t in targets]+[e['end'] for e in unit['evidence']])
        if end-begin>MAX_QUOTE or any(e['end']-e['start']>MAX_QUOTE for e in unit['evidence']):reasons.append('evidence_exceeds_legacy_contract')
        target=targets[0]
        locality=resolve_locality(text,target,graph,catalog,clause_segments=clause_segments);norm['locality']=locality
        if locality['reason']:reasons.append(locality['reason'])
        if target['label'] not in PLACE_TYPES:reasons.append('location_type_not_supported')
        if len(claims)>=MAX_CLAIMS:reasons.append('legacy_projection_limit')
        disposition='native_only';index=None
        if not reasons:
            depth,dmeta,dreasons=depth_fields(fs,graph,text)
            time,tmeta,treasons=time_fields(fs,source,graph)
            access,ameta,areasons=access_fields(fs)
            omitted=dreasons+treasons+areasons
            # Native graph keeps all non-observation roles and unselected facts.
            projected_ids={f['id'] for f in status}|set(tmeta['fact_ids'])
            if dmeta['selected_fact_id']:projected_ids.add(dmeta['selected_fact_id'])
            elif depth['depth_raw']:projected_ids.update(f['id'] for f in fs if f['kind']=='depth' and f['value']==depth['depth_raw'])
            if access!='unknown':projected_ids.update(ameta['fact_ids'])
            norm.update(depth=dmeta,time=tmeta,access=ameta,status_evidence=primary,
                        projected_fact_ids=sorted(projected_ids),omitted_field_reasons=omitted)
            quote_spans=locality['evidence']+primary+dmeta['evidence']+tmeta['evidence']+ameta['evidence']
            if any(e['end']-e['start']>MAX_QUOTE for e in quote_spans) or any(
                    len({(e['start'],e['end']) for e in es})>12 for es in (locality['evidence'],primary,tmeta['evidence'],dmeta['evidence'],ameta['evidence'])):
                reasons.append('evidence_exceeds_legacy_contract')
            else:
                claim=NerProjectedClaim(raw_place_name=target['text'],place_char_start=target['start'],place_char_end=target['end'],
                    place_type=PLACE_TYPES[target['label']],canonical_city=locality['canonical_city'],
                    canonical_barangay=locality['canonical_barangay'],canonical_province=locality['canonical_province'],
                    psgc_code=locality['psgc_code'],flood_mentioned=True,is_forecast=False,is_negated=False,is_historical=False,
                    condition=next(iter(states)),road_passability=access,**depth,**time,
                    evidence_sentence=text[begin:end],evidence_sentence_offset=(begin,end),
                    uncertainty_reasons=sorted(set(omitted)),confidence_score=None)
                index=len(claims);claims.append(claim);disposition='projected'
        groups.append(Observation(group_id=unit['group_id'],target_entity_ids=unit['target_entity_ids'],
            relation_ids=unit['relation_ids'],fact_ids=unit['fact_ids'],scope=unit['scope'],evidence=unit['evidence'],
            disposition=disposition,reasons=sorted(set(reasons)),claim_index=index,normalizations=norm))
    # A reliable specific observation at the same explicitly resolved instant can
    # make a city summary context. Unknown clocks never establish sameness.
    for i,group in enumerate(groups):
        if group.claim_index is None:continue
        claim=claims[group.claim_index]
        if claim.place_type!='city' or claim.event_time_resolved is None:continue
        if any(c.place_type in ('street','landmark','barangay') and c.canonical_city==claim.canonical_city
               and c.event_time_resolved==claim.event_time_resolved and c.condition==claim.condition for c in claims):
            groups[i]=group.model_copy(update={'disposition':'context_only','claim_index':None,'reasons':['location_context_only']})
    retained=[(g.claim_index,g.group_id) for g in groups if g.claim_index is not None]
    old_to_new={old:new for new,(old,_) in enumerate(retained)}
    claims=[claims[old] for old,_ in retained]
    groups=[g.model_copy(update={'claim_index':old_to_new[g.claim_index]}) if g.claim_index is not None else g for g in groups]
    unresolved={u['fact_id']:u['reason'] for u in graph['unassigned']};accounting=[]
    for fact in graph['facts']:
        related=[g for g in groups if fact['id'] in g.fact_ids]
        projected=[g for g in related if g.disposition=='projected' and fact['id'] in g.normalizations.get('projected_fact_ids',[])]
        context=[g for g in related if g.disposition=='context_only']
        kind='projected' if projected else 'native_only' if related and not context else 'context_only' if related else 'unassigned'
        why=sorted({r for g in related for r in g.reasons})
        if not projected:
            if fact['id'] in unresolved:why=[unresolved[fact['id']]]+why
            elif not why:why=['fact_retained_outside_legacy_fields']
        accounting.append(FactAccounting(fact_id=fact['id'],group_ids=[g.group_id for g in related],disposition=kind,reasons=why))
    # Unprojectable units refer to the complete, immutable graph rather than
    # duplicating every quote/context again inside the compatibility envelope.
    # Target/fact/relation IDs preserve exact occurrence and evidence lookup.
    groups=[g.model_copy(update={'evidence':[], 'evidence_storage':'native_graph', 'normalizations':{}})
            if g.disposition=='native_only' else g for g in groups]
    observed={i for g in groups for i in g.target_entity_ids}
    result=Projection(disposition='projected' if claims else 'native_only' if groups else 'no_eligible_observations',groups=groups,
        fact_accounting=accounting,mentions_without_observation=[m['id'] for m in graph['mentions'] if m['id'] not in observed])
    return claims,result
