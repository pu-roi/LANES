"""Constructed grouping-reference and temporal regression guards."""
from copy import deepcopy
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.flood_ner import context_review_v37 as review
from training.flood_ner.context_cases_v37 import core_cases,FAMILIES
from training.flood_ner.context_acceptance import object_sha
from test_flood_ner_context_review_v36 import output_of


def test_complete_fictional_matrix_and_no_membership():
    cases=core_cases()
    assert len(cases)==len({c['case_id']for c in cases})==48
    assert {(c['family'],c['language'],c['contrast'])for c in cases}=={
        (f,l,c)for f in FAMILIES for l in ('english','tagalog','taglish')for c in ('supported','counterexample')}
    assert all(c['record']['quality']=='constructed'and c['record']['split']is None for c in cases)


@pytest.mark.parametrize('case',core_cases(),ids=lambda c:c['case_id'])
def test_frozen_expected_source_spans_are_nonoverlapping(case):
    r=case['record'];end=-1
    for e in sorted(r['entities'],key=lambda e:e['start']):
        assert r['text'][e['start']:e['end']]==e['text']and e['start']>=end
        end=e['end']
    assert not review.error_inventory(r,output_of(case))


def test_collective_multirow_fact_does_not_invent_one_scalar():
    case=next(c for c in core_cases()if c['family']=='multirow_summaries'and c['contrast']=='supported')
    fact=next(f for f in case['record']['facts']if f['id']=='summary')
    assert fact['value']is None and len(fact['entity_ids'])==2 and fact['depth_scope']=='collective'


@pytest.mark.parametrize('field',['entities','qualifiers','temporal_role'])
def test_protected_contextual_fields_cannot_be_changed_for_grouping(field):
    record=core_cases()[4]['record'];new=deepcopy(record)
    if field=='entities':new['entities'][0]['end']-=1
    else:new['facts'][0][field]=['different']if field=='qualifiers'else'onset'
    assert review.representation_errors(record,new)


def test_time_span_regression_uses_set_differences_not_aggregate_count_ties():
    case=next(c for c in core_cases()if c['family']=='temporal_context'and c['contrast']=='supported')
    r=case['record'];old=output_of(case);new=deepcopy(old)
    new['expressions'][0]['start']+=1
    result=review.time_regressions(r,old,new)
    assert len(result['new_fp'])==len(result['new_fn'])==1


@pytest.mark.parametrize('field',['new_time_fp','new_time_fn'])
def test_time_regression_independently_blocks_readiness(field):
    args={'fixture_results':[{'case_id':str(i),'passed':True}for i in range(208)],
        'metrics':{'fp':0},'retained_lost':0,'gained':1,'unresolved_references':0,
        'missing_required_targets':0,'qualifier_failures':0,field:1}
    assert 'time_span_regression'in review.readiness(**args)['blockers']


def test_missing_reference_and_unmapped_disposition_rejected():
    case=core_cases()[0];r=deepcopy(case['record']);r['complete']=False
    with pytest.raises(ValueError):review.error_inventory(r,output_of(case))
    out=output_of(case);out['relations']=[]
    inv=review.error_inventory(case['record'],out)
    with pytest.raises(ValueError):review.validate_dispositions(inv,[])


def test_readiness_does_not_accept_always_abstaining_method():
    result=review.readiness(fixture_results=[{'case_id':str(i),'passed':True}for i in range(208)],
        metrics={'fp':0},retained_lost=0,gained=0,unresolved_references=0,missing_required_targets=0,qualifier_failures=0)
    assert 'no_targeted_correction'in result['blockers']


def test_group_dictionary_field_names_do_not_create_false_links():
    rows=[{'record_id':'a','groups':{'article':'x','event':'u'}},{'record_id':'b','groups':{'article':'y','event':'v'}}]
    assert review.connected_components(rows)==[['a'],['b']]


def test_source_event_groups_join_transitively():
    rows=[{'record_id':'a','groups':{'article':'x','event':'u'}},{'record_id':'b','groups':{'article':'x','event':'v'}},
        {'record_id':'c','groups':{'article':'z','event':'v'}}]
    assert review.connected_components(rows)==[['a','b','c']]


@pytest.mark.parametrize('damage',['duplicate','empty','nonstring'])
def test_grouping_rejects_malformed_member_accounting(damage):
    rows=[{'record_id':'a','groups':{'article':'x'}}]
    if damage=='duplicate':rows.append(deepcopy(rows[0]))
    if damage=='empty':rows[0]['groups']['article']=''
    if damage=='nonstring':rows[0]['groups']['article']=[]
    with pytest.raises(ValueError):review.connected_components(rows)
