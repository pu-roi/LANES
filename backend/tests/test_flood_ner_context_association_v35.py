"""Fictional-only repair checks; real comparison runs only after the freeze."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.flood_ner import context_association_v35 as engine
from training.flood_ner import context_association_scoring as scoring
from training.flood_ner.context_acceptance import exact_occurrence
from training.flood_ner.context_acceptance_cases import core_cases as original_cases
from training.flood_ner.context_association_cases_v35 import core_cases as additional_cases


def raw_case(case):
    ref=case['record'];return {'record_id':'fictional-'+hashlib.sha256(case['case_id'].encode()).hexdigest()[:20],
        'text':ref['text'],'text_sha256':ref['text_sha256'],'publication':None,
        'mentions':[{'id':e['id'],'start':e['start'],'end':e['end'],'text':e['text'],
            'label':e['label'],'provenance_sha256':'c'*64}for e in ref['entities']if e['label']in scoring.PLACE]}


@pytest.mark.parametrize('case',original_cases()+additional_cases(),ids=lambda c:c['case_id'])
def test_fictional_behavior(case):
    row=raw_case(case);before=deepcopy(row);output=engine.extract(row)
    result=scoring.fixture_result(case,row,output)
    assert result['passed'],result
    assert row==before and output==engine.extract(row)
    assert output['mentions']==row['mentions']


def test_new_matrix_is_exact_and_fixture_only():
    cases=additional_cases()
    assert len(cases)==len({r['case_id']for r in cases})==24
    assert len({(r['family'],r['language'],r['contrast'])for r in cases})==24
    assert all(r['record']['split']is None and r['record']['quality']=='constructed'for r in cases)


@pytest.mark.parametrize('damage',['hash','references','predictions','publication','span','label'])
def test_malformed_stale_or_reference_bearing_input_is_rejected(damage):
    row=raw_case(additional_cases()[0])
    if damage=='hash':row['text_sha256']='f'*64
    if damage=='references':row['reference']={}
    if damage=='predictions':row['expected']={}
    if damage=='publication':row['publication']={'value':'2026-01-01','basis':'unknown'}
    if damage=='span':row['mentions'][0]['end']-=1
    if damage=='label':row['mentions'][0]['label']='DEPTH'
    with pytest.raises((ValueError,TypeError)):engine.extract(row)


def test_ambiguous_same_clause_range_is_not_a_named_shared_measurement():
    text='Violet Road and Piña Road: one had 11 to 23 cm; which one was not identified.'
    row={'record_id':'constructed','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
        'publication':None,'mentions':[{'id':f'p{i}','label':'ROAD','provenance_sha256':'c'*64,
            **exact_occurrence(text,name,0)}for i,name in enumerate(['Violet Road','Piña Road'])]}
    out=engine.extract(row)
    assert not [r for r in out['relations']if out['facts'][int(r['fact_id'][1:])]['kind']=='depth']


def test_unsupported_numeric_road_prediction_is_preserved_but_not_grouped():
    text='Purok 6 and 7 were flooded.'
    row={'record_id':'constructed','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
        'publication':None,'mentions':[{'id':'p0','label':'LOCAL_AREA','provenance_sha256':'c'*64,**exact_occurrence(text,'Purok 6',0)},
            {'id':'p1','label':'ROAD','provenance_sha256':'c'*64,**exact_occurrence(text,'7',0)}]}
    out=engine.extract(row)
    assert out['mentions']==row['mentions'] and out['relations']==[]


def test_raw_qualifiers_are_preserved_in_span_value_and_semantics():
    text='Violet Road had about knee-deep floodwater.'
    row={'record_id':'constructed','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
        'publication':None,'mentions':[{'id':'p','label':'ROAD','provenance_sha256':'c'*64,**exact_occurrence(text,'Violet Road',0)}]}
    out=engine.extract(row);fact=next(f for f in out['facts']if f['kind']=='depth')
    assert fact['value']=='about knee-deep' and 'approximate'in fact['qualifiers']
