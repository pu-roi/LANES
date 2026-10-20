"""Constructed strict-scoring and privacy checks without private data."""
from copy import deepcopy
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.flood_ner import context_scoring_v38 as score
from training.flood_ner import context_association_v38 as engine
from training.flood_ner import context_run_v38 as runner
from training.flood_ner import context_review_v38 as qualification
from training.flood_ner.context_cases_v38 import core_cases
from test_flood_ner_context_association_v37 import raw_case


def example():
    c=core_cases()[0];raw=raw_case(c);out=engine.extract(raw);baseline={**deepcopy(out),'unscored':[]}
    return c,raw,baseline,out


def test_strict_fixed_reference_identity_and_repeat_occurrences():
    c=core_cases()[2];raw=raw_case(c);out=engine.extract(raw);baseline={**deepcopy(out),'unscored':[]}
    r=score.compare(c['record'],raw,baseline,out,out)
    assert r['metrics']['links']['candidate']['fp']==r['metrics']['links']['candidate']['fn']==0
    assert not r['v37_lost_correct'] and not r['transitions']['lost_correct']
    assert len({t[0][2] for t in score.strict.output_keys(out)['links']})==3


def test_relocated_repeated_occurrence_is_a_strict_fp_and_fn():
    c=core_cases()[2];raw=raw_case(c);out=engine.extract(raw);baseline={**deepcopy(out),'unscored':[]}
    wrong=deepcopy(out);f=next(f for f in wrong['facts']if f['value']=='subsided')
    next(r for r in wrong['relations']if r['fact_id']==f['id'])['target_entity_ids']=['b']
    r=score.compare(c['record'],raw,baseline,out,wrong)
    assert r['metrics']['links']['candidate']['fp']==r['metrics']['links']['candidate']['fn']==1
    assert len(r['v37_lost_correct'])==1


def test_expression_regression_uses_exact_sets_not_equal_totals():
    c,raw,baseline,out=example();bad=deepcopy(out)
    e=next(e for e in bad['expressions']if e['label']=='DEPTH');e['start']+=1
    result=score.expression_regressions(c['record'],out,bad)
    assert len(result['DEPTH']['new_fp'])==len(result['DEPTH']['new_fn'])==1


@pytest.mark.parametrize('damage',['identity','hash','text','missing_reference'])
def test_invalid_reference_join_is_not_a_negative(damage):
    c,raw,b,out=example();reference=deepcopy(c['record'])
    if damage=='identity':raw['record_id']='other'
    if damage=='hash':reference['text_sha256']='0'*64
    if damage=='text':reference['text']+='x'
    if damage=='missing_reference':reference['annotation_status']='incomplete';reference['entities']=None
    with pytest.raises((ValueError,TypeError,KeyError)):score.compare(reference,raw,b,out,out)


def test_missing_case_or_duplicate_error_accounting_is_rejected():
    with pytest.raises(ValueError):score.summarize([],[],[],expected_ids=set(),mapped_retention_failures=0)
    with pytest.raises(ValueError):score.error_outcomes([], {})


@pytest.mark.parametrize('key',['record_id','url','title','text','annotations','predictions','ready','references'])
def test_unallowlisted_coordinator_fields_rejected(key):
    with pytest.raises(ValueError):score.public_aggregate({key:'forbidden'})


def test_worker_has_no_scoring_references_or_oracle_mount():
    assert not any(any(s in n for s in ('scoring','cases','review_v38','model'))for n in runner.WORKER_FILES)
    assert 'training/flood_ner/context_association_worker_v38.py' in runner.WORKER_FILES


def test_exact_nineteen_outcomes_preserve_missing_target_category():
    _,raw,_,out=example();keys=list(score.strict.output_keys(out)['links']);key=keys[0]
    inv=[{'error_id':str(i),'opaque_id':raw['record_id'],'strict_key':key,
          'polarity':'incorrect'if i<4 else'missed','missing_neural_targets':['missing']if i>=12 else[]}
         for i in range(19)]
    results=score.error_outcomes(inv,{raw['record_id']:out})
    assert len(results)==19 and sum(bool(r['missing_neural_targets'])for r in results)==7
    inv[1]['error_id']=inv[0]['error_id']
    with pytest.raises(ValueError):score.error_outcomes(inv,{raw['record_id']:out})


def constructed_summary():
    c,raw,base,out=example();reviews=[]
    for i in range(23):
        row=score.compare(c['record'],raw,base,out,out)
        row['record_id']='constructed-'+str(i);row['language']='english' if i<11 else 'taglish'
        reviews.append(row)
    fixtures=[{'case_id':'constructed-'+str(i),'passed':True,
               'language':('english','tagalog','taglish')[i%3]}for i in range(238)]
    outcomes=[{'error_id':str(i),'polarity':'incorrect'if i<4 else'missed',
               'missing_neural_targets':['absent']if i>=12 else[], 'resolved':i<12}for i in range(19)]
    return reviews,fixtures,outcomes


def test_contextual_pass_cannot_clear_reference_or_language_blockers():
    reviews,fixtures,outcomes=constructed_summary()
    result=score.summarize(reviews,fixtures,outcomes,expected_ids={r['record_id']for r in reviews},mapped_retention_failures=0)
    assert result['contextual_acceptance_passed'] and result['status']=='blocked'
    assert set(result['blockers'])=={'unresolved_reference_questions','pure_tagalog_real_performance_unmeasured'}
    score.public_aggregate(result)


@pytest.mark.parametrize('defect',['wrong_link','lost_correct','missed_context','missing_target','qualifier','expression','fixture','mapping'])
def test_remaining_gates_are_derived_from_actual_evidence(defect):
    reviews,fixtures,outcomes=constructed_summary();mapped=0
    if defect=='wrong_link':
        m=reviews[0]['metrics']['links']['candidate'];m['fp']+=1;m['predicted']+=1
    if defect=='lost_correct':reviews[0]['v37_lost_correct']=[('strict-key',)]
    if defect=='missed_context':outcomes[4]['resolved']=False
    if defect=='missing_target':reviews[0]['missing_required_targets']=[('strict-key',)]
    if defect=='qualifier':reviews[0]['qualifier_errors']=['upper bound lost']
    if defect=='expression':reviews[0]['expression_regressions']['TIME']['new_fp']=[(1,2,'TIME')]
    if defect=='fixture':fixtures[0]['passed']=False
    if defect=='mapping':mapped=1
    r=score.summarize(reviews,fixtures,outcomes,expected_ids={r['record_id']for r in reviews},mapped_retention_failures=mapped)
    assert r['status']=='blocked'
    if defect!='missing_target':assert not r['contextual_acceptance_passed']
    else:assert 'required_neural_targets_missing'in r['blockers']


@pytest.mark.parametrize('field',['metrics','fictional_by_language','eligible_languages','expression_regressions'])
def test_nested_candidate_details_cannot_escape_aggregate_allowlist(field):
    reviews,fixtures,outcomes=constructed_summary()
    r=score.summarize(reviews,fixtures,outcomes,expected_ids={r['record_id']for r in reviews},mapped_retention_failures=0)
    r[field]['url']='https://example.invalid/private'
    with pytest.raises(ValueError):score.public_aggregate(r)


def test_stale_qualification_implementation_rejected_before_reading_resources(monkeypatch):
    monkeypatch.setattr(qualification.previous,'qualify',lambda *a:pytest.fail('no source qualification dispatch'))
    with pytest.raises(ValueError,match='stale qualification'):
        qualification.qualify({'files':{},'predecessor_bundle':'missing','fixtures':'missing','implementation_sha256':'0'*64})


def test_stale_qualification_resources_rejected_before_processing(tmp_path,monkeypatch):
    import hashlib
    f=tmp_path/'bundle';f.write_text('{}',encoding='utf-8')
    monkeypatch.setattr(qualification.previous,'qualify',lambda *a:pytest.fail('must not process stale input'))
    with pytest.raises(ValueError,match='stale qualified'):
        qualification.qualify({'files':{str(f):'0'*64},'predecessor_bundle':str(f),'fixtures':str(f),
            'implementation_sha256':hashlib.sha256(Path(qualification.__file__).read_bytes()).hexdigest()})
