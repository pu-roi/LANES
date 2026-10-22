"""Coordinator-only strict scoring and conservative baseline projection."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import re
from typing import Any

from .context_association import validate_output, depth_scope

PLACE = frozenset({'ROAD','LANDMARK','LOCAL_AREA','BARANGAY','CITY','PROVINCE'})
TYPE_MAP = {'street':'ROAD','landmark':'LANDMARK','barangay':'BARANGAY','city':'CITY','province':'PROVINCE'}


def span_key(entity: dict) -> tuple:
    return entity['start'],entity['end'],entity['label']


def fact_key(fact: dict, entities: dict) -> tuple:
    evidence=tuple(sorted(span_key(entities[e])for e in fact['entity_ids']))
    return (fact['kind'],evidence,fact['value']if fact['kind']in{'status','access'}else None,
            fact.get('temporal_role')if fact['kind']=='time'else None,
            fact.get('depth_scope')if fact['kind']=='depth'else None)


def reference_keys(record: dict) -> dict:
    if record.get('complete')is not True or record.get('review_status')!='accepted' or record.get('entities')is None:
        raise ValueError('incomplete/missing references never become negatives')
    entities={e['id']:e for e in record['entities']};facts={f['id']:f for f in record['facts']}
    links=set();unresolved=[]
    for relation in record['relations']:
        if relation['scope']=='unresolved':unresolved.append(relation);continue
        links.add((fact_key(facts[relation['fact_id']],entities),
                   tuple(sorted(span_key(entities[e])for e in relation['target_entity_ids'])),relation['scope']))
    return {'locations':{span_key(e)for e in record['entities']if e['label']in PLACE},
            'DEPTH':{span_key(e)for e in record['entities']if e['label']=='DEPTH'},
            'TIME':{span_key(e)for e in record['entities']if e['label']=='TIME'},
            'links':links,'unresolved':unresolved,
            'unassigned_facts':set(facts)-{r['fact_id']for r in record['relations']}}


def output_keys(output: dict) -> dict:
    entities={e['id']:e for e in output['expressions']};facts={f['id']:f for f in output['facts']};mentions={m['id']:m for m in output['mentions']}
    links=set()
    for r in output['relations']:
        if r['scope']=='unresolved':continue
        links.add((fact_key(facts[r['fact_id']],entities),tuple(sorted(span_key(mentions[e])for e in r['target_entity_ids'])),r['scope']))
    return {'locations':{span_key(m)for m in output['mentions']},
            'DEPTH':{span_key(e)for e in output['expressions']if e['label']=='DEPTH'},
            'TIME':{span_key(e)for e in output['expressions']if e['label']=='TIME'},'links':links,
            'unassigned_count':len(output['unassigned']),
            'unresolved_count':sum(r['scope']=='unresolved'for r in output['relations'])}


def strict_counts(reference: set, prediction: set) -> dict:
    tp=len(reference&prediction);fp=len(prediction-reference);fn=len(reference-prediction)
    supported=bool(reference)
    precision=tp/(tp+fp)if tp+fp else 0.0
    recall=tp/(tp+fn)if supported else None
    return {'tp':tp,'fp':fp,'fn':fn,'support':len(reference),'predicted':len(prediction),
            'precision':precision if prediction or supported else None,'recall':recall,
            'f1':2*tp/(2*tp+fp+fn)if supported else None,'measured':supported}


def json_key(value: Any) -> str:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def join_outputs(rows: list[dict], outputs: list[dict]) -> dict:
    expected={r['record_id']:r for r in rows};actual={r['record_id']:r for r in outputs}
    if len(expected)!=len(rows)or len(actual)!=len(outputs)or set(expected)!=set(actual):
        raise ValueError('missing/duplicate/unexpected output identities')
    if any(expected[k]['text_sha256']!=actual[k]['text_sha256']for k in expected):
        raise ValueError('output original-text hash mismatch')
    return actual


def baseline_projection(raw: dict, row: dict) -> dict:
    """Use only returned baseline evidence. Do not consult any references.

    Local assertions are projected as returned. No shared/collective group is
    fabricated from co-occurrence. Missing/ambiguous raw-expression provenance
    is retained as unscored, never recovered by a first-occurrence lookup.
    """
    if raw['record_id']!=row['record_id']or raw['text_sha256']!=row['text_sha256']:raise ValueError('baseline identity mismatch')
    text=row['text'];mentions=[];expressions=[];facts=[];relations=[];unscored=[]
    def emit(kind: str,c: dict,target: dict,value: str,span: list | None=None,role: str | None=None) -> None:
        evidence={'start':c['evidence_sentence_offset'][0],'end':c['evidence_sentence_offset'][1],'text':c['evidence_sentence']}
        ids=[];ds=None
        if span is not None:
            e={'id':f'bx{len(expressions)}','start':span[0],'end':span[1],'text':text[span[0]:span[1]],'label':'DEPTH'if kind=='depth'else'TIME'}
            expressions.append(e);ids=[e['id']]
            if kind=='depth':ds=depth_scope(value)[0]
        f={'id':f'bf{len(facts)}','kind':kind,'value':value,'entity_ids':ids,'temporal_role':role,'depth_scope':ds,
           'evidence':[evidence],'qualifiers':[],'uncertainty':[]};facts.append(f)
        relations.append({'id':f'br{len(relations)}','fact_id':f['id'],'target_entity_ids':[target['id']],
                          'scope':'local','evidence':[evidence],'uncertainty':[],'overrides_relation_id':None})
    for i,c in enumerate(raw['claims']):
        label=TYPE_MAP.get(c['place_type'])
        if not label:
            unscored.append({'claim':i,'reason':'unknown_rules_location_type'});continue
        a,b=c['place_char_start'],c['place_char_end'];sa,sb=c['evidence_sentence_offset']
        if not(c['place_source_exact']and c['sentence_source_exact']and text[a:b]==c['raw_place_name']and text[sa:sb]==c['evidence_sentence']):
            raise ValueError('invalid baseline source offsets')
        target={'id':f'bp{i}','start':a,'end':b,'text':text[a:b],'label':label,
                'provenance_sha256':hashlib.sha256(json_key(c).encode()).hexdigest()};mentions.append(target)
        if {'location_context_only','photo_caption_only','metadata_only_lead','non_observation_list_context'}.intersection(c['uncertainty_reasons']):
            unscored.append({'claim':i,'reason':'context_only_not_resolved_assertion'});continue
        for kind,field,spans in [('depth','depth_raw','depth_span_candidates'),('time','event_time_raw','time_span_candidates')]:
            if c[field]:
                if len(c[spans])==1:
                    pair=c[spans][0]
                    if not(sa<=pair[0]<pair[1]<=sb)or text[pair[0]:pair[1]]!=c[field]:raise ValueError('invalid baseline contextual evidence')
                    emit(kind,c,target,c[field],pair,role=c['event_time_kind']if kind=='time'else None)
                else:unscored.append({'claim':i,'reason':kind+'_evidence_missing_or_ambiguous'})
        if c['condition']!='unknown':emit('status',c,target,c['condition'])
        for flag,state in [('is_forecast','forecast'),('is_negated','negated'),('is_historical','historical')]:
            if c[flag]:emit('status',c,target,state)
        if c['road_passability']!='unknown':
            if re.search(r'\b(?:passable|madaanan|madaan|sasakyan)\b',c['evidence_sentence'],re.I):
                emit('access',c,target,c['road_passability'])
            else:unscored.append({'claim':i,'reason':'access_evidence_not_explicit_in_returned_sentence'})
    return {'record_id':row['record_id'],'text_sha256':row['text_sha256'],'mentions':mentions,
            'expressions':expressions,'facts':facts,'relations':relations,'unassigned':[],
            'unscored':unscored,'projection':'returned_source_exact_local_assertions_only'}


def compare_record(reference: dict, row: dict, baseline: dict, candidate: dict) -> dict:
    if reference['text']!=row['text']or reference['text_sha256']!=row['text_sha256']:raise ValueError('reference/text join mismatch')
    validate_output(row,candidate)
    gold=reference_keys(reference);bk=output_keys(baseline);ck=output_keys(candidate)
    slices={}
    for name in ('locations','DEPTH','TIME','links'):
        slices[name]={'baseline':strict_counts(gold[name],bk[name]),'candidate':strict_counts(gold[name],ck[name])}
    for label in sorted(PLACE):
        slices[label]={'baseline':strict_counts({s for s in gold['locations']if s[2]==label},{s for s in bk['locations']if s[2]==label}),
                       'candidate':strict_counts({s for s in gold['locations']if s[2]==label},{s for s in ck['locations']if s[2]==label})}
    for kind in ('depth','time','status','access'):
        slices['links_'+kind]={'baseline':strict_counts({s for s in gold['links']if s[0][0]==kind},{s for s in bk['links']if s[0][0]==kind}),
                              'candidate':strict_counts({s for s in gold['links']if s[0][0]==kind},{s for s in ck['links']if s[0][0]==kind})}
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


def fixture_result(case: dict, row: dict, output: dict) -> dict:
    validate_output(row,output)
    g=reference_keys(case['record']);p=output_keys(output)
    # Fixtures specify behavior facets, not an exhaustive status annotation for
    # every sentence. Score all specified fact kinds strictly; expose additional
    # kinds as unmeasured rather than using them as evidence of success.
    kinds={f['kind']for f in case['record']['facts']}
    expected={x for x in g['links']if x[0][0]in kinds};actual={x for x in p['links']if x[0][0]in kinds}
    expressions_ok=all(g[label]==p[label]for label,kind in [('DEPTH','depth'),('TIME','time')]if kind in kinds)
    no_invented_values=not output['absolute_instants']and not output['numeric_depths']
    # Every reference-unassigned expression must remain unassigned; extra links
    # of an evaluated kind are rejected by exact set equality above.
    passed=expected==actual and expressions_ok and no_invented_values
    return {'case_id':case['case_id'],'family':case['family'],'language':case['language'],'contrast':case['contrast'],
            'passed':passed,'association_counts':strict_counts(expected,actual),'expression_equality':expressions_ok,
            'unmeasured_additional_fact_kinds':sorted({f['kind']for f in output['facts']}-kinds),
            'expected_links':sorted(expected),'actual_links':sorted(actual),
            'unassigned_reference_facts':len(g['unassigned_facts']),
            'numeric_or_absolute_invention':not no_invented_values}


def combine_counts(rows: list[dict], key: str, method: str) -> dict:
    fields=('tp','fp','fn','support','predicted');n={k:sum(r['metrics'][key][method][k]for r in rows)for k in fields}
    n['measured']=n['support']>0
    n['precision']=n['tp']/n['predicted']if n['predicted']else 0.0 if n['support']else None
    n['recall']=n['tp']/n['support']if n['support']else None
    n['f1']=2*n['tp']/(2*n['tp']+n['fp']+n['fn'])if n['support']else None
    return n


def aggregate(reviews: list[dict], fixture_results: list[dict]) -> dict:
    if len(reviews)!=24 or len({r['record_id']for r in reviews})!=24 or len(fixture_results)!=40 or len({r['case_id']for r in fixture_results})!=40:
        raise ValueError('exact completed workload required')
    keys=list(reviews[0]['metrics']);metrics={k:{m:combine_counts(reviews,k,m)for m in('baseline','candidate')}for k in keys}
    gained=sum(len(r['transitions']['gained_correct'])for r in reviews)
    lost=sum(len(r['transitions']['lost_correct'])for r in reviews)
    introduced=sum(len(r['transitions']['introduced_incorrect'])for r in reviews)
    blockers=[]
    if not all(r['passed']for r in fixture_results):blockers.append('fictional_behavior_failures')
    if introduced:blockers.append('introduced_incorrect_resolved_associations')
    if lost:blockers.append('lost_supported_baseline_correct_associations')
    if not gained:blockers.append('no_demonstrated_targeted_correction')
    evidence_gaps=sum(x['reason']not in{'context_only_not_resolved_assertion'}for r in reviews for x in r['baseline_unscored'])
    if evidence_gaps:blockers.append('baseline_evidence_projection_incomplete')
    return {'status':'qualifies_for_separate_read_only_connection_proposal'if not blockers else'not_qualified',
            'eligible_training_records':24,'held_records_unscored':2,'fictional_cases':40,
            'fictional_passed':sum(r['passed']for r in fixture_results),'fictional_failed':sum(not r['passed']for r in fixture_results),
            'gained_correct_links':gained,'lost_correct_links':lost,'introduced_incorrect_links':introduced,
            'lost_links_missing_neural_target':sum(len(r['transitions']['lost_due_to_missing_neural_target'])for r in reviews),
            'baseline_evidence_gaps':evidence_gaps,'blockers':blockers,'metrics':metrics,
            'application_connected':False,'neural_inference':False,'training_started':False,
            'claims_generalization':False,'ai_assisted_silver':True}
