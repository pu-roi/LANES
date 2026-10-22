"""Constructed source-only revision checks; no private annotations or models."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner import context_revision_v35 as review
from training.flood_ner.context_acceptance import object_sha
from training.flood_ner.context_acceptance_cases import make_case, entity, depth


class Tokenizer:
    """Span shape probe only; real frozen-tokenizer qualification is separate."""
    def make_doc(self, text):
        return SimpleNamespace(char_span=lambda a,b,**kw: (a,b) if 0<=a<b<=len(text) else None)


def fixture():
    case = make_case('row_measurements','english','supported','Élan Road: about 12 cm.',
        [entity('p','Élan Road'),entity('d','about 12 cm','DEPTH')],
        [depth('f','d',qualifiers=['approximate'])],[('f',['p'],'local')],
        ['No exact scalar.'],'Constructed reference only.')
    original=case['record'];original.update(quality='silver',split='train',teacher='constructed-unit-test')
    # Simulate an original-capture contract using fictional bytes only.
    original['source']['origin']='captured_original'
    current=deepcopy(original);current['entities']=[e for e in original['entities']if e['label']=='ROAD']
    current.update(facts=[],relations=[],annotation_profile='location-only-v1')
    proposed=deepcopy(original)
    disposition={'record_id':proposed['record_id'],'disposition':'retain_proposed',
        'completeness':{k:True for k in ('locations','depth','time','status','access','associations')},
        'unassigned_facts':{},'proposal_sha256':object_sha(proposed)}
    return original,proposed,current,disposition


def test_valid_revision_has_no_side_effects():
    args=fixture();before=deepcopy(args)
    assert review.proposal_errors(*args,Tokenizer())==[]
    assert args==before and review.source_summary(args[1])['complete']


@pytest.mark.parametrize('damage', ['text','source','split','location','hash','missing','incomplete','unassigned'])
def test_unauthorized_or_incomplete_reference_changes_are_rejected(damage):
    original,proposed,current,r=fixture()
    if damage=='text': proposed['text']='other text'
    if damage=='source':proposed['source']['publisher']='changed publisher'
    if damage=='split':proposed['split']='dev'
    if damage=='location':proposed['entities'][0]['label']='LANDMARK'
    if damage=='hash':r['proposal_sha256']='f'*64
    if damage=='missing':proposed['complete']=False
    if damage=='incomplete':r['completeness']['associations']=False
    if damage=='unassigned':proposed['relations']=[]
    if damage!='hash':r['proposal_sha256']=object_sha(proposed)
    assert review.proposal_errors(original,proposed,current,r,Tokenizer())


def test_held_references_are_explicit_and_not_complete_negatives():
    original,proposed,current,r=fixture()
    proposed.update(complete=False,review_status='unresolved');r['disposition']='hold'
    r['completeness']['associations']=False;r['proposal_sha256']=object_sha(proposed)
    assert review.proposal_errors(original,proposed,current,r,Tokenizer())==[]
    proposed['complete']=True;r['proposal_sha256']=object_sha(proposed)
    assert any('held' in e for e in review.proposal_errors(original,proposed,current,r,Tokenizer()))


def test_structural_ledger_cannot_hide_removed_entities_or_qualifiers():
    original,proposed,_,_=fixture();proposed['facts'][0]['qualifiers']=[]
    proposed['entities']=proposed['entities'][:-1]
    changes=review.field_changes(original,proposed)
    assert {c['path']for c in changes}=={'/entities','/facts'}
    assert all(c['original']!=c['proposed']for c in changes)


@pytest.mark.parametrize('damage',['duplicate','missing','historical','original'])
def test_review_identity_join_is_exact(damage):
    old=[];new=[]
    for i in range(24):
        original,proposed,current,r=fixture()
        original['record_id']=proposed['record_id']=f'fictional-{i}'
        old.append({'proposed':original});new.append({'original':deepcopy(original),'proposed':proposed,'review':r})
    if damage=='duplicate':new[1]=deepcopy(new[0])
    if damage=='missing':new.pop()
    if damage=='historical':new[0]['proposed']['passage_language']='taglish'
    if damage=='original':new[0]['original']['text']='forged'
    with pytest.raises(ValueError):review.join_reviews(old,new)


def test_file_bindings_reject_stale_payload_and_traversal(tmp_path):
    p=tmp_path/'source.json';p.write_text('{}',encoding='utf-8')
    binding={'source.json':{'bytes':2,'sha256':review.digest(p)}}
    review.verify_frozen_files(tmp_path,binding)
    p.write_text('[]',encoding='utf-8')
    with pytest.raises(ValueError,match='stale'):review.verify_frozen_files(tmp_path,binding)
    with pytest.raises(ValueError,match='unsafe'):review.verify_frozen_files(tmp_path,{'../escape':binding['source.json']})
