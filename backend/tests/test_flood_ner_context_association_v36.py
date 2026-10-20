"""Fictional behavior matrix; no empirical passages in these tests."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.flood_ner import context_association_v36 as engine
from training.flood_ner import context_review_v36 as review
from training.flood_ner import context_association_scoring as scoring
from training.flood_ner.context_acceptance_cases import core_cases as original
from training.flood_ner.context_association_cases_v35 import core_cases as previous
from training.flood_ner.context_cases_v36 import core_cases as additional


def raw_case(case):
    r=case['record'];return {'record_id':'fictional-'+hashlib.sha256(case['case_id'].encode()).hexdigest()[:20],
        'text':r['text'],'text_sha256':r['text_sha256'],'publication':None,
        'mentions':[{k:e[k]for k in ('id','start','end','text','label')}|{'provenance_sha256':'c'*64}
            for e in r['entities']if e['label']in scoring.PLACE]}


@pytest.mark.parametrize('case',original()+previous()+additional(),ids=lambda c:c['case_id'])
def test_frozen_fictional_behavior(case):
    row=raw_case(case);before=deepcopy(row);output=engine.extract(row)
    result=review.fixture_result(case,row,output,exhaustive=case['case_id'].startswith('fictional-v36_'))
    assert result['passed'],result
    assert row==before and output==engine.extract(row)
    assert output['mentions']==row['mentions']


@pytest.mark.parametrize('damage',['hash','reference','expected','publication','offset','label'])
def test_malformed_or_reference_bearing_inputs_are_rejected(damage):
    row=raw_case(additional()[0])
    if damage=='hash':row['text_sha256']='f'*64
    if damage=='reference':row['reference']={}
    if damage=='expected':row['expected']=[]
    if damage=='publication':row['publication']={'value':'today','basis':'guess'}
    if damage=='offset':row['mentions'][0]['end']-=1
    if damage=='label':row['mentions'][0]['label']='DEPTH'
    with pytest.raises((ValueError,TypeError)):engine.extract(row)


def test_no_io_or_neural_imports_in_decision_module():
    import ast
    tree=ast.parse(Path(engine.__file__).read_text(encoding='utf-8'))
    imports=[n.module or''for n in ast.walk(tree)if isinstance(n,ast.ImportFrom)]
    imports+=[a.name for n in ast.walk(tree)if isinstance(n,ast.Import)for a in n.names]
    assert not any(n.split('.')[0]in{'requests','httpx','socket','sqlalchemy','spacy','torch','thinc','subprocess'}for n in imports)


def test_no_case_identity_or_language_switch_can_drive_decisions():
    row=raw_case(additional()[0]);a=engine.extract(row)
    row['record_id']='opaque-another';b=engine.extract(row);a['record_id']=b['record_id']
    assert a==b
