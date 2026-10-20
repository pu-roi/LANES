"""Constructed tests only: no publisher text, predictions or live services."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner import context_acceptance as a
from training.flood_ner.context_acceptance_cases import core_cases


@pytest.fixture(scope='module')
def tokenizer():
    from spacy.lang.en import English
    return SimpleNamespace(make_doc=English().tokenizer)


@pytest.mark.parametrize('case', core_cases(), ids=lambda c: c['case_id'])
def test_forty_explicit_constructed_references(case, tokenizer):
    assert a.validate_case(case, tokenizer) == []


def test_matrix_is_exact_and_does_not_hide_missing_cases(tokenizer):
    cases = core_cases()
    assert not a.validate_matrix(cases, tokenizer)
    assert a.validate_matrix(cases[:-1], tokenizer)
    cases[-1] = deepcopy(cases[0])
    assert a.validate_matrix(cases, tokenizer)


def test_explicit_occurrences_and_unicode():
    text = '🌧 Piña Road, Piña Road.'
    assert a.exact_occurrence(text, 'Piña Road', 1) == {'start':13,'end':22,'text':'Piña Road'}
    for occurrence in (-1, 2, None, True):
        with pytest.raises(ValueError): a.exact_occurrence(text, 'Piña Road', occurrence)


def training_reference():
    r = deepcopy(core_cases()[0]['record'])
    r['source']['origin'] = 'captured_original'
    r.update(quality='silver', split='train', teacher='AI-assisted source review')
    current = deepcopy(r); current.update(annotation_profile='location-only-v1', facts=[], relations=[])
    current['entities'] = [e for e in current['entities'] if e['label'] in a.PLACE_LABELS]
    return r, deepcopy(r), current


def review_for(r):
    unlinked = {f['id'] for f in r['facts']} - {x['fact_id'] for x in r['relations']}
    return {'record_id':r['record_id'],'proposal_sha256':a.object_sha(r),'disposition':'retain_proposed',
        'completeness':dict.fromkeys(('locations','depth','time','status','access','associations'), True),
        'unassigned_facts':dict.fromkeys(unlinked,'No supported named target; preserve unresolved.'),
        'repeat_exceptions':[],'issues':[],'evidence':[{'source_sha256':r['source']['text_sha256'],
            'passage_sha256':r['text_sha256'],'source_window':[r['passage_start'],r['passage_end']],
            'reviewed_extent':[0,len(r['source']['text'])]}],
        'drafting_basis':'source_and_historical_reference_only_not_blinded'}


def test_reference_revision_preserves_location_and_source(tokenizer):
    old, proposed, current = training_reference()
    assert not a.validate_revision(old, proposed, current, tokenizer)
    assert not a.validate_review(proposed, review_for(proposed))


@pytest.mark.parametrize('damage', ['text','hash','source','identity','language','window','validation','holdout','location','null','overlap','token'])
def test_reference_rejects_substantive_changes_and_excluded_partitions(damage, tokenizer):
    old, p, current = training_reference()
    if damage == 'text':p['text'] += ' changed'
    elif damage == 'hash':p['text_sha256'] = '0'*64
    elif damage == 'source':p['source']['capture_version'] = 'other'
    elif damage == 'identity':p['record_id'] = 'other'
    elif damage == 'language':p['passage_language'] = 'taglish'
    elif damage == 'window':p['passage_start'] += 1
    elif damage in {'validation','holdout'}:p['split'] = current['split'] = 'dev' if damage == 'validation' else 'test'
    elif damage == 'location':p['entities'][0]['label'] = 'CITY'
    elif damage == 'null':p['facts'] = None
    elif damage == 'overlap':p['entities'].append(deepcopy(p['entities'][0]))
    elif damage == 'token':
        e=next(e for e in p['entities'] if e['label']=='DEPTH');e['start']+=1;e['text']=p['text'][e['start']:e['end']]
    assert a.validate_revision(old,p,current,tokenizer)


@pytest.mark.parametrize('damage',['stale','incomplete','null_completeness','negative_missing','no_evidence','no_basis','hold_complete','unassigned'])
def test_review_cannot_invent_completeness_or_clear_a_hold(damage):
    _,p,_=training_reference();r=review_for(p)
    if damage=='stale':r['proposal_sha256']='0'*64
    elif damage=='incomplete':r['completeness']['time']=False
    elif damage=='null_completeness':r['completeness']['time']=None
    elif damage=='negative_missing':p['complete']=False;r['proposal_sha256']=a.object_sha(p)
    elif damage=='no_evidence':r['evidence']=[]
    elif damage=='no_basis':r['drafting_basis']='predictions'
    elif damage=='hold_complete':r['disposition']='hold'
    elif damage=='unassigned':r['unassigned_facts']={'invented':'unknown'}
    assert a.validate_review(p,r)


def test_unresolved_references_stay_held_and_empty_is_not_automatic_negative():
    _,p,_=training_reference();p.update(complete=False,review_status='unresolved')
    r=review_for(p);r.update(disposition='hold',issues=['Missing source scope']);r['completeness']['associations']=False
    assert not a.validate_review(p,r)
    p.update(entities=[],facts=[],relations=[]);r['proposal_sha256']=a.object_sha(p)
    assert not a.validate_review(p,r)  # Valid hold, never an eligible negative.
    r['disposition']='retain_proposed'
    assert a.validate_review(p,r)


def test_repeats_require_source_bound_exclusion_not_first_match():
    r={'text':'🌧 2 PM, 2 PM','entities':[{'start':2,'end':6,'text':'2 PM','label':'TIME'}]}
    assert a.literal_coverage(r,[])
    exception={'start':8,'end':12,'label':'TIME','reason':'This fictional second occurrence is a quoted identifier, not a time.'}
    assert not a.literal_coverage(r,[exception])
    assert a.literal_coverage(r,[exception,exception])
    exception['end']=11
    assert a.literal_coverage(r,[exception])


def test_contained_qualifier_span_covers_literal_without_overlapping_entities():
    text='gutter deep; Above gutter deep'
    r={'text':text,'entities':[{'start':0,'end':11,'text':'gutter deep','label':'DEPTH'},
            {'start':13,'end':len(text),'text':'Above gutter deep','label':'DEPTH'}]}
    assert not a.literal_coverage(r,[])


def test_conflicting_update_cycles_and_changed_temporal_role_rejected(tokenizer):
    old,p,current=training_reference()
    first=deepcopy(p['relations'][0]);second=deepcopy(p['relations'][0]);second['id']='second-link'
    first['overrides_relation_id']='second-link';second['overrides_relation_id']=first['id']
    p['relations']=[first,second]
    assert a.validate_revision(old,p,current,tokenizer)


def test_missing_references_are_not_qualified_by_unchanged_expected_output(tokenizer):
    c=deepcopy(core_cases()[0]);c['record']['facts']=None
    assert a.validate_case(c,tokenizer)


def test_source_review_cannot_reuse_another_article_hash():
    _,p,_=training_reference();r=review_for(p);r['evidence'][0]['source_sha256']='0'*64
    assert a.validate_review(p,r)


def test_fixture_construction_is_deterministic_and_source_exact():
    cases=core_cases();assert a.object_sha(cases)==a.object_sha(core_cases())
    labels={e['label']for c in cases for e in c['record']['entities']}
    assert a.PLACE_LABELS<=labels
    for c in cases:
        for e in c['record']['entities']:assert c['record']['text'][e['start']:e['end']]==e['text']


@pytest.mark.parametrize('damage',[None,'scope','source','window','missing','duplicate'])
def test_exact_source_use_or_explicit_hold(damage):
    _,_,r=training_reference()
    proof={'record_id':r['record_id'],'verified':True,'scope':'private_owner_only_academic_training_evaluation',
        'text_sha256':r['text_sha256'],'source_sha256':r['source']['text_sha256'],
        'start':r['passage_start'],'end':r['passage_end']}
    receipts=[proof]
    if damage=='scope':proof['scope']='all_public_uses'
    elif damage=='source':proof['source_sha256']='0'*64
    elif damage=='window':proof['end']-=1
    elif damage=='missing':receipts=[]
    elif damage=='duplicate':receipts.append(deepcopy(proof))
    if damage is None:a.validate_source_use([r],receipts)
    else:
        with pytest.raises(ValueError):a.validate_source_use([r],receipts)


def raw_input():
    text='🌧 Piña Court'
    return {'record_id':'fictional-input','text':text,'text_sha256':__import__('hashlib').sha256(text.encode()).hexdigest(),
        'publication':None,'mentions':[{'id':'p','start':2,'end':12,'text':'Piña Court','label':'LOCAL_AREA','provenance_sha256':'a'*64}]}


def test_raw_contract_preserves_local_area_without_public_claim_schema():
    a.validate_raw_input(raw_input())


@pytest.mark.parametrize('damage',['reference','prediction','bad_hash','naive_time','unsupported_time','wrong_label','offset','duplicate','no_provenance','oversize'])
def test_raw_contract_rejects_reference_leakage_and_invalid_mentions(damage):
    x=raw_input()
    if damage in {'reference','prediction'}:x[damage]=[]
    elif damage=='bad_hash':x['text_sha256']='0'*64
    elif damage=='naive_time':x['publication']={'value':'2026-10-19T12:00:00','basis':'source timestamp'}
    elif damage=='unsupported_time':x['publication']={'value':'2026-10-19T12:00:00+08:00','basis':''}
    elif damage=='wrong_label':x['mentions'][0]['label']='DEPTH'
    elif damage=='offset':x['mentions'][0]['start']=0
    elif damage=='duplicate':x['mentions'].append(deepcopy(x['mentions'][0]))
    elif damage=='no_provenance':x['mentions'][0]['provenance_sha256']=''
    elif damage=='oversize':x['text']='x'*100001
    with pytest.raises(ValueError):a.validate_raw_input(x)


@pytest.mark.parametrize('damage',['time_role','missing_fact','overlap','invented_instant','wrong_expected','missing_reference'])
def test_semantic_and_expectation_errors_remain_failures(damage,tokenizer):
    case=deepcopy(next(c for c in core_cases()if c['family']=='observation_onset'))
    if damage=='time_role':case['record']['facts'][0]['qualifiers']=['not a flood onset']
    elif damage=='missing_fact':case['record']['relations'][0]['fact_id']='absent'
    elif damage=='overlap':case['record']['entities'].append(deepcopy(case['record']['entities'][0]))
    elif damage=='invented_instant':case['expected']['absolute_instants']=['2026-10-19T01:00:00+08:00']
    elif damage=='wrong_expected':case['expected']['relations']=[]
    elif damage=='missing_reference':case['record']['complete']=False
    assert a.validate_case(case,tokenizer)


def test_guarded_reference_process_blocks_network_database_models_and_predictions(tmp_path):
    backend=Path(__file__).resolve().parents[1]
    code='''import sys,socket
sys.path.insert(0,sys.argv[1])
from training.flood_ner.context_acceptance import install_reference_guards
install_reference_guards()
import spacy
from spacy.language import Language
for operation in [lambda:socket.getaddrinfo('example.invalid',443),lambda:open('raw-predictions.jsonl'),lambda:open('model-best/ner/model'),lambda:__import__('psycopg'),lambda:spacy.load('absent-model'),lambda:Language.initialize(None),lambda:Language.update(None,[]),lambda:Language.__call__(None,'fictional')]:
 try:operation()
 except RuntimeError:pass
 else:raise AssertionError('forbidden action permitted')
print('guards passed')
'''
    result=subprocess.run([sys.executable,'-I','-B','-c',code,str(backend)],cwd=tmp_path,capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stderr
