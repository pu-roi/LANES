"""Strict fixed-reference saved-output analysis. Never invokes an extractor."""
from __future__ import annotations
from collections import Counter
from . import context_association_scoring as strict
from .context_scoring_v37 import compare_record, qualifier_errors
from .context_review_v37 import fixture_result,error_inventory

METHODS=('baseline','v37','candidate')


def expression_regressions(reference: dict, previous: dict, candidate: dict) -> dict:
    gold=strict.reference_keys(reference);old=strict.output_keys(previous);new=strict.output_keys(candidate)
    return {label:{'new_fp':sorted((new[label]-gold[label])-(old[label]-gold[label])),
                   'new_fn':sorted((gold[label]-new[label])-(gold[label]-old[label]))}
            for label in ('DEPTH','TIME')}


def compare(reference: dict, raw: dict, baseline: dict, previous: dict, candidate: dict) -> dict:
    result=compare_record(reference,raw,baseline,candidate)
    old=compare_record(reference,raw,baseline,previous)
    for key,values in result['metrics'].items():values['v37']=old['metrics'][key]['candidate']
    gold=strict.reference_keys(reference)['links'];prior=strict.output_keys(previous)['links'];new=strict.output_keys(candidate)
    result['v37_lost_correct']=sorted((gold&prior)-new['links'])
    result['v37_gained_correct']=sorted((gold&new['links'])-prior)
    result['expression_regressions']=expression_regressions(reference,previous,candidate)
    result['qualifier_errors']=qualifier_errors(candidate)
    result['missing_required_targets']=sorted(k for k in gold-new['links'] if any(t not in new['locations'] for t in k[1]))
    return result


def error_outcomes(inventory: list[dict], outputs: dict) -> list[dict]:
    if len(inventory)!=19 or len({r['error_id'] for r in inventory})!=19:raise ValueError('exact 19 error dispositions required')
    result=[]
    for error in inventory:
        keys={strict.json_key(k)for k in strict.output_keys(outputs[error['opaque_id']])['links']}
        present=strict.json_key(error['strict_key'])in keys
        resolved=not present if error['polarity']=='incorrect' else present
        result.append({**error,'resolved':resolved,'outcome':('incorrect_removed'if resolved else'incorrect_retained')
            if error['polarity']=='incorrect'else('miss_recovered'if resolved else'miss_retained')})
    return result


def summarize(reviews: list[dict], fixtures: list[dict], outcomes: list[dict], *, expected_ids: set[str],
              mapped_retention_failures: int) -> dict:
    if len(reviews)!=23 or len({r['record_id']for r in reviews})!=23 or {r['record_id']for r in reviews}!=expected_ids:
        raise ValueError('exact 23 eligible records required')
    if len(fixtures)!=238 or len({r['case_id']for r in fixtures})!=238:raise ValueError('all 238 behavior checks required')
    if len(outcomes)!=19 or len({r['error_id']for r in outcomes})!=19:raise ValueError('all 19 error outcomes required')
    wrong=[r for r in outcomes if r['polarity']=='incorrect']
    recognition=[r for r in outcomes if r['missing_neural_targets']]
    contextual=[r for r in outcomes if r['polarity']=='missed' and not r['missing_neural_targets']]
    if (len(wrong),len(contextual),len(recognition))!=(4,8,7):raise ValueError('error categories changed')
    metrics={k:{m:strict.combine_counts(reviews,k,m)for m in METHODS}for k in reviews[0]['metrics']}
    lost_baseline=sum(len(r['transitions']['lost_correct'])for r in reviews)
    lost_v37=sum(len(r['v37_lost_correct'])for r in reviews)
    reg={label:{kind:sum(len(r['expression_regressions'][label][kind])for r in reviews)for kind in ('new_fp','new_fn')}
         for label in ('DEPTH','TIME')}
    failures=sum(len(r['qualifier_errors'])for r in reviews)
    blockers=[]
    if not all(r['passed']for r in fixtures):blockers.append('fictional_behavior_failures')
    if metrics['links']['candidate']['fp']:blockers.append('known_incorrect_resolved_associations')
    if lost_baseline or lost_v37 or mapped_retention_failures:blockers.append('supported_correct_associations_lost')
    if not all(r['resolved']for r in contextual):blockers.append('contextual_omissions_remaining')
    if not any(r['resolved']for r in wrong+contextual):blockers.append('no_targeted_correction')
    if failures:blockers.append('qualifier_preservation_failures')
    if any(n for v in reg.values()for n in v.values()):blockers.append('expression_span_regression')
    contextual_pass=not blockers
    if sum(len(r['missing_required_targets'])for r in reviews):blockers.append('required_neural_targets_missing')
    blockers.extend(['unresolved_reference_questions','pure_tagalog_real_performance_unmeasured'])
    return {'status':'blocked','contextual_acceptance_passed':contextual_pass,'blockers':blockers,
        'metrics':metrics,'real_inputs':24,'eligible_references':23,'carried_holds':3,
        'fictional_cases':238,'fictional_passed':sum(r['passed']for r in fixtures),
        'fictional_by_language':{lang:{'cases':sum(r['language']==lang for r in fixtures),
            'passed':sum(r['language']==lang and r['passed']for r in fixtures)}for lang in ('english','tagalog','taglish')},
        'eligible_languages':dict(Counter(r['language']for r in reviews)),
        'incorrect_removed':sum(r['resolved']for r in wrong),'contextual_misses_recovered':sum(r['resolved']for r in contextual),
        'recognition_dependent_misses_recovered':sum(r['resolved']for r in recognition),
        'lost_baseline_correct':lost_baseline,'lost_v37_correct':lost_v37,'mapped_retention_failures':mapped_retention_failures,
        'expression_regressions':reg,'qualifier_failures':failures,
        'missing_required_targets':sum(len(r['missing_required_targets'])for r in reviews),
        'pure_tagalog_real_performance':'unmeasured','references_unchanged':True,'ai_assisted_silver':True,
        'generalization_claim':False,'training_started':False,'application_connected':False}


PUBLIC_KEYS={'status','contextual_acceptance_passed','blockers','metrics','real_inputs','eligible_references','carried_holds',
    'fictional_cases','fictional_passed','fictional_by_language','eligible_languages','incorrect_removed','contextual_misses_recovered',
    'recognition_dependent_misses_recovered','lost_baseline_correct','lost_v37_correct','mapped_retention_failures',
    'expression_regressions','qualifier_failures','missing_required_targets','pure_tagalog_real_performance','references_unchanged',
    'ai_assisted_silver','generalization_claim','training_started','application_connected'}
BLOCKERS={'fictional_behavior_failures','known_incorrect_resolved_associations','supported_correct_associations_lost',
    'contextual_omissions_remaining','no_targeted_correction','qualifier_preservation_failures','expression_span_regression',
    'required_neural_targets_missing','unresolved_reference_questions','pure_tagalog_real_performance_unmeasured'}


def public_aggregate(value: dict) -> dict:
    if set(value)!=PUBLIC_KEYS:raise ValueError('exact aggregate allowlist required')
    if value['status']!='blocked' or not isinstance(value['blockers'],list) or any(b not in BLOCKERS for b in value['blockers']):
        raise ValueError('unsafe readiness claim')
    if value['pure_tagalog_real_performance']!='unmeasured':raise ValueError('unsupported language claim')
    flags={'contextual_acceptance_passed','references_unchanged','ai_assisted_silver','generalization_claim','training_started','application_connected'}
    if any(type(value[k])is not bool for k in flags):raise ValueError('invalid aggregate flag')
    if value['training_started']or value['application_connected']or value['generalization_claim']or not value['references_unchanged']or not value['ai_assisted_silver']:
        raise ValueError('scope claim changed')
    structured={'metrics','fictional_by_language','eligible_languages','expression_regressions','status','blockers','pure_tagalog_real_performance'}
    def count(n):
        if type(n)is not int or n<0:raise ValueError('invalid count')
    for key in PUBLIC_KEYS-flags-structured:count(value[key])
    allowed={'locations','DEPTH','TIME','links',*strict.PLACE,'links_depth','links_time','links_status','links_access'}
    if set(value['metrics'])!=allowed:raise ValueError('metric allowlist changed')
    for metric in value['metrics'].values():
        if set(metric)!=set(METHODS):raise ValueError('comparison methods changed')
        for rates in metric.values():
            if set(rates)!={'tp','fp','fn','support','predicted','measured','precision','recall','f1'}:raise ValueError('unsafe metric fields')
            for k in ('tp','fp','fn','support','predicted'):count(rates[k])
            if rates['support']!=rates['tp']+rates['fn']or rates['predicted']!=rates['tp']+rates['fp']:raise ValueError('unreconciled metric')
            if type(rates['measured'])is not bool:raise ValueError('invalid measurement flag')
            for k in ('precision','recall','f1'):
                if rates[k]is not None and(type(rates[k])not in(int,float)or not 0<=rates[k]<=1):raise ValueError('invalid metric rate')
    if set(value['eligible_languages'])-{'english','taglish'}:raise ValueError('unknown real language')
    for v in value['eligible_languages'].values():count(v)
    if set(value['fictional_by_language'])!={'english','tagalog','taglish'}:raise ValueError('unsafe fictional language')
    for v in value['fictional_by_language'].values():
        if set(v)!={'cases','passed'}:raise ValueError('unsafe fictional details')
        for n in v.values():count(n)
    if set(value['expression_regressions'])!={'DEPTH','TIME'}:raise ValueError('unsafe expression details')
    for v in value['expression_regressions'].values():
        if set(v)!={'new_fp','new_fn'}:raise ValueError('unsafe expression fields')
        for n in v.values():count(n)
    return value
