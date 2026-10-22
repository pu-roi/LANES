"""Constructed references only; no private articles or predictions."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.flood_ner import context_review_v36 as review
from training.flood_ner.context_cases_v36 import core_cases,FAMILIES
from training.flood_ner.context_acceptance import object_sha


def output_of(case):
    r=case['record'];places={'ROAD','LANDMARK','LOCAL_AREA','BARANGAY','CITY','PROVINCE'}
    return {'record_id':r['record_id'],'text_sha256':r['text_sha256'],
        'mentions':[deepcopy(e) for e in r['entities']if e['label']in places],
        'expressions':[deepcopy(e) for e in r['entities']if e['label']not in places],
        'facts':deepcopy(r['facts']),'relations':deepcopy(r['relations']),'unassigned':[]}


def test_complete_three_language_matrix():
    cases=core_cases()
    assert len(cases)==len({c['case_id']for c in cases})==96
    assert {(c['family'],c['language'],c['contrast'])for c in cases}=={
        (f,l,c)for f in FAMILIES for l in ('english','tagalog','taglish')for c in ('supported','counterexample')}
    assert all(c['record']['split']is None and c['record']['quality']=='constructed'for c in cases)


@pytest.mark.parametrize('case',core_cases(),ids=lambda c:c['case_id'])
def test_expected_reference_is_source_exact(case):
    r=case['record'];end=-1
    for e in sorted(r['entities'],key=lambda e:e['start']):
        assert r['text'][e['start']:e['end']]==e['text']and e['start']>=end
        end=e['end']
    for link in r['relations']:
        assert link['target_entity_ids']
    assert not review.error_inventory(r,output_of(case))


def test_strict_errors_do_not_disappear_when_boundary_explanation_pairs_them():
    case=core_cases()[0];r=case['record'];out=output_of(case)
    out['expressions'][0]['end']-=1
    entries=review.error_inventory(r,out)
    assert {e['polarity']for e in entries}=={'incorrect','missed'}and len(entries)==2
    assert len({e['error_id']for e in entries})==2


@pytest.mark.parametrize('damage',['missing','duplicate','stale','reason','category'])
def test_disposition_rejects_unaccounted_or_unbound_errors(damage):
    case=core_cases()[0];out=output_of(case);out['relations']=[]
    inv=review.error_inventory(case['record'],out)
    rows=[{'error_id':e['error_id'],'inventory_sha256':object_sha(e),'category':'code_defect',
        'reason':'Constructed omitted link','evidence':e['evidence']}for e in inv]
    if damage=='missing':rows.pop()
    if damage=='duplicate':rows.append(deepcopy(rows[0]))
    if damage=='stale':rows[0]['inventory_sha256']='a'*64
    if damage=='reason':rows[0]['reason']=''
    if damage=='category':rows[0]['category']='ignore'
    with pytest.raises(ValueError):review.validate_dispositions(inv,rows)


def test_incomplete_references_are_not_empty_negatives():
    case=core_cases()[0];r=deepcopy(case['record']);r['complete']=False
    with pytest.raises(ValueError):review.error_inventory(r,output_of(case))


def test_previously_correct_key_requires_review_evidence_before_removal():
    case=core_cases()[0];r=case['record'];out=output_of(case);new=deepcopy(r);new['relations']=[]
    with pytest.raises(ValueError):review.map_previous(r,new,{'v35':out},[])
    rows=review.map_previous(r,None,{'v35':out},[])
    assert all(e['disposition']=='unresolved'for e in rows)


@pytest.mark.parametrize('field',['fp','lost','gained','refs','targets','qualifiers','fixtures'])
def test_readiness_rejects_every_independent_blocker(field):
    fixtures=[{'case_id':str(i),'passed':True}for i in range(160)]
    args=dict(fixture_results=fixtures,metrics={'fp':0},retained_lost=0,gained=1,
        unresolved_references=0,missing_required_targets=0,qualifier_failures=0)
    if field=='fp':args['metrics']['fp']=1
    if field=='lost':args['retained_lost']=1
    if field=='gained':args['gained']=0
    if field=='refs':args['unresolved_references']=1
    if field=='targets':args['missing_required_targets']=1
    if field=='qualifiers':args['qualifier_failures']=1
    if field=='fixtures':fixtures[-1]['passed']=False
    result=review.readiness(**args)
    assert result['status']=='blocked'and result['blockers']
    assert result['pure_tagalog_real_performance']=='unmeasured'
