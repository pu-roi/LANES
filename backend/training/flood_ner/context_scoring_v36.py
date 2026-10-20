"""Coordinator-only scoring of four saved methods against explicit reference versions."""
from __future__ import annotations
from collections import Counter
from . import context_association_scoring as strict
from .context_association_scoring_v35 import qualifier_errors
from .context_review_v36 import readiness

METHODS=('baseline','v34','v35','candidate')


def compare(reference: dict, raw: dict, methods: dict) -> dict:
    if set(methods)!=set(METHODS):raise ValueError('all saved comparison methods required')
    result=strict.compare_record(reference,raw,methods['baseline'],methods['candidate'])
    for name in ('v34','v35'):
        old=strict.compare_record(reference,raw,methods['baseline'],methods[name])
        for key,values in result['metrics'].items():values[name]=old['metrics'][key]['candidate']
    gold=strict.reference_keys(reference)['links'];new=strict.output_keys(methods['candidate'])
    previous=strict.output_keys(methods['v35'])['links']
    result['v35_retained_correct']=sorted(gold&previous&new['links'])
    result['v35_lost_correct']=sorted((gold&previous)-new['links'])
    result['v35_gained_correct']=sorted((gold&new['links'])-previous)
    missing=gold-new['links']
    result['missed_due_to_missing_neural_targets']=sorted(k for k in missing if any(t not in new['locations']for t in k[1]))
    result['qualifier_errors']=qualifier_errors(methods['candidate'])
    return result


def aggregate(reviews: list[dict], fixtures: list[dict], *, unresolved_references: int,
              previous_mapping: list[dict]) -> dict:
    if len(reviews)!=23 or len({r['record_id']for r in reviews})!=23:raise ValueError('all 23 references required')
    keys=list(reviews[0]['metrics'])
    metrics={k:{m:strict.combine_counts(reviews,k,m)for m in METHODS}for k in keys}
    lost=sum(len(r['transitions']['lost_correct'])for r in reviews)
    gained=sum(len(r['transitions']['gained_correct'])for r in reviews)
    missing=sum(len(r['missed_due_to_missing_neural_targets'])for r in reviews)
    qualifier=sum(len(r['qualifier_errors'])for r in reviews)
    decision=readiness(fixture_results=fixtures,metrics=metrics['links']['candidate'],retained_lost=lost,
        gained=gained,unresolved_references=unresolved_references,missing_required_targets=missing,
        qualifier_failures=qualifier)
    return {**decision,'metrics':metrics,'real_inputs':24,'eligible_references':23,'carried_holds':3,
        'fictional_cases':160,'fictional_passed':sum(r['passed']for r in fixtures),
        'fictional_by_language':{lang:{'cases':sum(r['language']==lang for r in fixtures),
            'passed':sum(r['language']==lang and r['passed']for r in fixtures)}for lang in ('english','tagalog','taglish')},
        'eligible_languages':dict(Counter(r['language']for r in reviews)),
        'gained_correct_links':gained,'lost_baseline_correct_links':lost,
        'v35_correct_links_lost':sum(len(r['v35_lost_correct'])for r in reviews),
        'v35_correct_links_gained':sum(len(r['v35_gained_correct'])for r in reviews),
        'missed_links_with_missing_neural_target':missing,'qualifier_failures':qualifier,
        'unassigned_facts':sum(r['candidate_unassigned_facts']for r in reviews),
        'unresolved_links':sum(r['candidate_unresolved_links']for r in reviews),
        'reference_unresolved_links':sum(r['unresolved_reference_links']for r in reviews),
        'reference_unassigned_facts':sum(r['unassigned_reference_facts']for r in reviews),
        'previous_correct_dispositions':dict(Counter(e['disposition']for e in previous_mapping)),
        'ai_assisted_silver':True,'generalization_claim':False}


PUBLIC_KEYS=frozenset({'status','blockers','pure_tagalog_real_performance','application_connected','training_started',
    'metrics','real_inputs','eligible_references','carried_holds','fictional_cases','fictional_passed','fictional_by_language',
    'eligible_languages','gained_correct_links','lost_baseline_correct_links','v35_correct_links_lost',
    'v35_correct_links_gained','missed_links_with_missing_neural_target','qualifier_failures','unassigned_facts',
    'unresolved_links','reference_unresolved_links','reference_unassigned_facts','previous_correct_dispositions',
    'ai_assisted_silver','generalization_claim'})


def public_aggregate(value: dict) -> dict:
    """Exact schema rejects identities and free-form source-bearing fields."""
    if set(value)!=PUBLIC_KEYS:raise ValueError('aggregate allowlist mismatch')
    if value['status']not in {'blocked','eligible_for_separate_read_only_demo_plan'}:raise ValueError('unsafe status')
    if set(value['blockers'])-{'fictional_behavior_failures','known_incorrect_resolved_associations',
            'supported_correct_associations_lost','no_targeted_correction','unresolved_reference_questions',
            'required_neural_targets_missing','qualifier_preservation_failures'}:raise ValueError('unsafe blocker')
    if value['pure_tagalog_real_performance']!='unmeasured':raise ValueError('unmeasured language claim changed')
    import json,re
    serialized=json.dumps(value,ensure_ascii=False)
    if re.search(r'https?://|(?:train|fictional|continuation|location|cohort|revision)-[a-f0-9]{10,}',serialized):
        raise ValueError('individual identity disclosure')
    for key,methods in value['metrics'].items():
        if key not in {'locations','DEPTH','TIME','links',*strict.PLACE,'links_depth','links_time','links_status','links_access'}:
            raise ValueError('unknown aggregate metric')
        if set(methods)!=set(METHODS):raise ValueError('method aggregate incomplete')
        for m in methods.values():
            if set(m)!={'tp','fp','fn','support','predicted','measured','precision','recall','f1'}:raise ValueError('metric fields unsafe')
            if any(type(m[k])is not int or m[k]<0 for k in ('tp','fp','fn','support','predicted')):
                raise ValueError('unsafe metric counts')
            if any(m[k]is not None and(type(m[k])not in (int,float)or not 0<=m[k]<=1)for k in ('precision','recall','f1')):
                raise ValueError('unsafe metric rate')
            if type(m['measured'])is not bool:raise ValueError('unsafe support flag')
    if any(k not in {'english','tagalog','taglish'}for k in value['eligible_languages']):raise ValueError('unexpected language key')
    if any(type(v)is not int or v<0 for v in value['eligible_languages'].values()):raise ValueError('unsafe language count')
    if set(value['fictional_by_language'])!={'english','tagalog','taglish'}or any(set(v)!={'cases','passed'}
            or any(type(n)is not int or n<0 for n in v.values())for v in value['fictional_by_language'].values()):
        raise ValueError('unsafe fictional counts')
    if set(value['previous_correct_dispositions'])-{'retained','corrected','unresolved'}or any(type(n)is not int or n<0
            for n in value['previous_correct_dispositions'].values()):raise ValueError('unsafe retention counts')
    for key in PUBLIC_KEYS-{'status','blockers','pure_tagalog_real_performance','metrics','fictional_by_language',
            'eligible_languages','previous_correct_dispositions','application_connected','training_started','ai_assisted_silver','generalization_claim'}:
        if type(value[key])is not int or value[key]<0:raise ValueError('unsafe aggregate count')
    if value['application_connected']is not False or value['training_started']is not False or value['generalization_claim']is not False or value['ai_assisted_silver']is not True:
        raise ValueError('scope claim changed')
    return value
