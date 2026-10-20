"""Saved-output scoring across immutable and independently revised references."""
from __future__ import annotations

from collections import Counter
import re

from . import context_association_scoring as strict
from .context_acceptance import object_sha


def qualifier_errors(output: dict) -> list[str]:
    """Verify explicit raw qualifiers survive; explanatory reference prose is not a metric."""
    entities={e['id']:e for e in output['expressions']};errors=[]
    for fact in output['facts']:
        if fact['kind']!='depth':continue
        raw=' '.join(entities[i]['text']for i in fact['entity_ids'])
        if fact['value']!=raw:errors.append('raw_depth_value_changed')
        tags=set(fact['qualifiers'])
        if re.search(r'\b(?:almost|about|around|approximately|roughly|nearly|halos)\b',raw,re.I) and 'approximate'not in tags:
            errors.append('approximation_qualifier_lost')
        if re.search(r'\b(?:above|below)\b',raw,re.I) and 'relative_gauge'not in tags:
            errors.append('relative_gauge_qualifier_lost')
        if fact['depth_scope']=='maximum' and 'upper_bound'not in tags:errors.append('upper_bound_qualifier_lost')
        if fact['depth_scope']=='range' and 'not_a_point_measurement'not in tags:errors.append('range_qualifier_lost')
    return errors


def compare(reference: dict, raw: dict, baseline: dict, v34: dict, candidate: dict) -> dict:
    result=strict.compare_record(reference,raw,baseline,candidate)
    old=strict.compare_record(reference,raw,baseline,v34)
    for name,metrics in result['metrics'].items():metrics['v34']=old['metrics'][name]['candidate']
    gold=strict.reference_keys(reference)['links'];oldkeys=strict.output_keys(v34)['links']
    newkeys=strict.output_keys(candidate)['links']
    result['v34_transitions']={'retained_correct':sorted(gold&oldkeys&newkeys),
        'lost_correct':sorted((gold&oldkeys)-newkeys),'gained_correct':sorted((gold&newkeys)-oldkeys)}
    result['qualifier_errors']=qualifier_errors(candidate)
    result['reference_sha256']=object_sha(reference)
    return result


def map_previous_correct(original: dict, revised: dict|None, baseline: dict, v34: dict,
                         change_entry: dict|list|None) -> list[dict]:
    """Account for every formerly correct key; no silent denominator removal."""
    oldgold=strict.reference_keys(original)['links']
    bk=strict.output_keys(baseline)['links'];vk=strict.output_keys(v34)['links']
    newgold=strict.reference_keys(revised)['links']if revised is not None else set()
    entries=[]
    for key in sorted(oldgold&(bk|vk)):
        if revised is None:disposition='unresolved';related=[]
        elif key in newgold:disposition='retained';related=[key]
        else:
            if not change_entry:raise ValueError('previously correct association removed without independent source review')
            disposition='corrected'
            related=sorted(k for k in newgold if k[0][0]==key[0][0] and (
                k[0][1]==key[0][1] or bool(set(k[1])&set(key[1]))))
        entries.append({'original_key':key,'previous_methods':(['rules']if key in bk else[])+(['v34']if key in vk else[]),
            'disposition':disposition,'revised_related_keys':related,
            'source_review_change_bound':bool(change_entry)if disposition=='corrected'else None})
    return entries


def summarize(reviews: list[dict], fixtures: list[dict], mapping: list[dict],
              eligible_ids: set[str], held_ids: set[str]) -> dict:
    if len(reviews)!=len(eligible_ids) or {r['record_id']for r in reviews}!=eligible_ids or eligible_ids&held_ids:
        raise ValueError('exact eligible/held scoring accounting required')
    if len(eligible_ids)+len(held_ids)!=24 or len(fixtures)!=64 or len({f['case_id']for f in fixtures})!=64:
        raise ValueError('all 24 counterparts and 64 fictional cases required')
    keys=list(reviews[0]['metrics'])if reviews else[]
    metrics={key:{method:strict.combine_counts(reviews,key,method)for method in ('baseline','v34','candidate')}for key in keys}
    gained=sum(len(r['transitions']['gained_correct'])for r in reviews)
    lost=sum(len(r['transitions']['lost_correct'])for r in reviews)
    introduced=sum(len(r['transitions']['introduced_incorrect'])for r in reviews)
    previous_unresolved=sum(entry['disposition']=='unresolved'for row in mapping for entry in row['associations'])
    evidence_gaps=sum(e['reason']!='context_only_not_resolved_assertion'for r in reviews for e in r['baseline_unscored'])
    qualifier_failures=sum(len(r['qualifier_errors'])for r in reviews)
    blockers=[]
    if not all(f['passed']for f in fixtures):blockers.append('fictional_behavior_failures')
    if introduced:blockers.append('introduced_incorrect_resolved_associations')
    if lost:blockers.append('lost_supported_baseline_correct_associations')
    if previous_unresolved:blockers.append('previously_correct_association_reference_unresolved')
    if evidence_gaps:blockers.append('baseline_evidence_incomplete')
    if qualifier_failures:blockers.append('raw_qualifier_preservation_failures')
    if not gained:blockers.append('no_demonstrated_targeted_correction')
    return {'status':'qualifies_for_separate_read_only_connection_proposal'if not blockers else'not_qualified',
        'eligible_references':len(reviews),'new_holds':len(held_ids),'carried_holds':2,'raw_training_inputs':24,
        'fictional_cases':64,'fictional_passed':sum(f['passed']for f in fixtures),
        'fictional_failed':sum(not f['passed']for f in fixtures),
        'gained_correct_links':gained,'lost_correct_links':lost,'introduced_incorrect_links':introduced,
        'v34_correct_links_lost':sum(len(r['v34_transitions']['lost_correct'])for r in reviews),
        'v34_correct_links_gained':sum(len(r['v34_transitions']['gained_correct'])for r in reviews),
        'previously_correct_reference_dispositions':dict(Counter(e['disposition']for row in mapping for e in row['associations'])),
        'baseline_evidence_gaps':evidence_gaps,'qualifier_failures':qualifier_failures,
        'metrics':metrics,'blockers':blockers,'application_connected':False,'neural_inference':False,
        'training_started':False,'ai_assisted_silver':True,'generalization_claim':False}
