"""Coordinator-only scoring of five saved methods against explicit reference versions."""
from __future__ import annotations
from collections import Counter
from . import context_association_scoring as strict
from .context_association_scoring_v35 import qualifier_errors as scalar_qualifier_errors
from .context_review_v37 import readiness,time_regressions
from .context_association_v37 import validate_output

METHODS=('baseline','v34','v35','v36','candidate')


def qualifier_errors(output: dict) -> list[str]:
    """A schema-valid null inventory retains constituents, not one scalar string."""
    from copy import deepcopy
    checked=deepcopy(output)
    checked['facts']=[f for f in checked['facts']if not(f['kind']=='depth'and f['value']is None and f['depth_scope']=='collective')]
    return scalar_qualifier_errors(checked)


def compare(reference: dict, raw: dict, methods: dict) -> dict:
    if set(methods)!=set(METHODS):raise ValueError('all saved comparison methods required')
    result=compare_record(reference,raw,methods['baseline'],methods['candidate'])
    for name in ('v34','v35','v36'):
        old=compare_record(reference,raw,methods['baseline'],methods[name])
        for key,values in result['metrics'].items():values[name]=old['metrics'][key]['candidate']
    gold=strict.reference_keys(reference)['links'];new=strict.output_keys(methods['candidate'])
    previous=strict.output_keys(methods['v36'])['links']
    result['v36_retained_correct']=sorted(gold&previous&new['links'])
    result['v36_lost_correct']=sorted((gold&previous)-new['links'])
    result['v36_gained_correct']=sorted((gold&new['links'])-previous)
    missing=gold-new['links']
    result['missed_due_to_missing_neural_targets']=sorted(k for k in missing if any(t not in new['locations']for t in k[1]))
    result['time_regressions']=time_regressions(reference,methods['v36'],methods['candidate'])
    result['qualifier_errors']=qualifier_errors(methods['candidate'])
    return result


def aggregate(reviews: list[dict], fixtures: list[dict], *, unresolved_references: int,
              previous_mapping: list[dict],expected_eligible_ids: set[str],
              mapped_retention_failures: int=0) -> dict:
    if not 0<len(reviews)<=23 or len({r['record_id']for r in reviews})!=len(reviews)or {r['record_id']for r in reviews}!=expected_eligible_ids:
        raise ValueError('every frozen eligible reference required; holds must be separately accounted')
    keys=list(reviews[0]['metrics'])
    metrics={k:{m:strict.combine_counts(reviews,k,m)for m in METHODS}for k in keys}
    lost=sum(len(r['transitions']['lost_correct'])for r in reviews)
    gained=sum(len(r['transitions']['gained_correct'])for r in reviews)
    missing=sum(len(r['missed_due_to_missing_neural_targets'])for r in reviews)
    qualifier=sum(len(r['qualifier_errors'])for r in reviews)
    retained_lost=max(lost,sum(len(r['v36_lost_correct'])for r in reviews),mapped_retention_failures)
    decision=readiness(fixture_results=fixtures,metrics=metrics['links']['candidate'],retained_lost=retained_lost,
        gained=gained,unresolved_references=unresolved_references,missing_required_targets=missing,
        qualifier_failures=qualifier,new_time_fp=sum(len(r['time_regressions']['new_fp'])for r in reviews),
        new_time_fn=sum(len(r['time_regressions']['new_fn'])for r in reviews))
    return {**decision,'metrics':metrics,'real_inputs':24,'eligible_references':len(reviews),'carried_holds':3,
        'mapped_retention_failures':mapped_retention_failures,
        'fictional_cases':208,'fictional_passed':sum(r['passed']for r in fixtures),
        'fictional_by_language':{lang:{'cases':sum(r['language']==lang for r in fixtures),
            'passed':sum(r['language']==lang and r['passed']for r in fixtures)}for lang in ('english','tagalog','taglish')},
        'eligible_languages':dict(Counter(r['language']for r in reviews)),
        'gained_correct_links':gained,'lost_baseline_correct_links':lost,
        'v36_correct_links_lost':sum(len(r['v36_lost_correct'])for r in reviews),
        'v36_correct_links_gained':sum(len(r['v36_gained_correct'])for r in reviews),
        'missed_links_with_missing_neural_target':missing,'qualifier_failures':qualifier,
        'new_time_span_fp':sum(len(r['time_regressions']['new_fp'])for r in reviews),
        'new_time_span_fn':sum(len(r['time_regressions']['new_fn'])for r in reviews),
        'unassigned_facts':sum(r['candidate_unassigned_facts']for r in reviews),
        'unresolved_links':sum(r['candidate_unresolved_links']for r in reviews),
        'reference_unresolved_links':sum(r['unresolved_reference_links']for r in reviews),
        'reference_unassigned_facts':sum(r['unassigned_reference_facts']for r in reviews),
        'previous_correct_dispositions':dict(Counter(e['disposition']for e in previous_mapping)),
        'ai_assisted_silver':True,'generalization_claim':False}


PUBLIC_KEYS=frozenset({'status','blockers','pure_tagalog_real_performance','application_connected','training_started',
    'metrics','real_inputs','eligible_references','carried_holds','fictional_cases','fictional_passed','fictional_by_language',
    'eligible_languages','gained_correct_links','lost_baseline_correct_links','v36_correct_links_lost',
    'v36_correct_links_gained','missed_links_with_missing_neural_target','qualifier_failures','unassigned_facts','new_time_span_fp','new_time_span_fn',
    'unresolved_links','reference_unresolved_links','reference_unassigned_facts','previous_correct_dispositions',
    'ai_assisted_silver','generalization_claim','mapped_retention_failures'})


def public_aggregate(value: dict) -> dict:
    """Exact schema rejects identities and free-form source-bearing fields."""
    if set(value)!=PUBLIC_KEYS:raise ValueError('aggregate allowlist mismatch')
    if value['status']not in {'blocked','eligible_for_separate_read_only_demo_plan'}:raise ValueError('unsafe status')
    if set(value['blockers'])-{'fictional_behavior_failures','known_incorrect_resolved_associations',
            'supported_correct_associations_lost','no_targeted_correction','unresolved_reference_questions',
            'required_neural_targets_missing','qualifier_preservation_failures','time_span_regression'}:raise ValueError('unsafe blocker')
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


def compare_record(reference: dict, row: dict, baseline: dict, candidate: dict) -> dict:
    if reference['text']!=row['text']or reference['text_sha256']!=row['text_sha256']:raise ValueError('reference/text join mismatch')
    validate_output(row,candidate)
    gold=strict.reference_keys(reference);bk=strict.output_keys(baseline);ck=strict.output_keys(candidate)
    slices={}
    for name in ('locations','DEPTH','TIME','links'):
        slices[name]={'baseline':strict.strict_counts(gold[name],bk[name]),'candidate':strict.strict_counts(gold[name],ck[name])}
    for label in sorted(strict.PLACE):
        slices[label]={'baseline':strict.strict_counts({s for s in gold['locations']if s[2]==label},{s for s in bk['locations']if s[2]==label}),
                       'candidate':strict.strict_counts({s for s in gold['locations']if s[2]==label},{s for s in ck['locations']if s[2]==label})}
    for kind in ('depth','time','status','access'):
        slices['links_'+kind]={'baseline':strict.strict_counts({s for s in gold['links']if s[0][0]==kind},{s for s in bk['links']if s[0][0]==kind}),
                              'candidate':strict.strict_counts({s for s in gold['links']if s[0][0]==kind},{s for s in ck['links']if s[0][0]==kind})}
    baseline_correct=gold['links']&bk['links'];candidate_correct=gold['links']&ck['links']
    lost=baseline_correct-candidate_correct;gained=candidate_correct-baseline_correct
    introduced=(ck['links']-gold['links'])-(bk['links']-gold['links'])
    missing_location=[link for link in lost if any(t not in ck['locations']for t in link[1])]
    return {'record_id':row['record_id'],'text_sha256':row['text_sha256'],'metrics':slices,
            'transitions':{'baseline_correct':sorted(baseline_correct),'candidate_correct':sorted(candidate_correct),
                           'gained_correct':sorted(gained),'lost_correct':sorted(lost),
                           'introduced_incorrect':sorted(introduced),'lost_due_to_missing_neural_target':sorted(missing_location)},
            'unassigned_reference_facts':len(gold['unassigned_facts']),'unresolved_reference_links':len(gold['unresolved']),
            'candidate_unassigned_facts':ck['unassigned_count'],'candidate_unresolved_links':ck['unresolved_count'],
            'baseline_unscored':baseline['unscored'],
            'reference_relation_support':len(gold['links']),'silver_not_human_gold':True}
