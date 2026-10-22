"""Constructed evidence boundaries and refusal to turn reports into admission."""
from copy import deepcopy
import hashlib
from pathlib import Path

import pytest

from training.flood_ner.academic_use import clause_pointer, validate_academic_review, verify_pointer
from training.flood_ner.sources import json_bytes
from test_flood_ner_use_bundle import sample


def fixture(tmp_path):
    path=tmp_path/'evidence.txt';path.write_bytes('Policy Biñan—research\u2028evidence.'.encode('utf-8'))
    pointer=clause_pointer(path,tmp_path,7,21)
    records=[]
    for i in range(400):
        r=sample(i%139);r.record_id=f'record-{i}'
        records.append(r)
    publishers=sorted({r.source.publisher for r in records})
    prior={'assessments':[{'publisher':p,'scope':s,'proposed_outcome':'unresolved'} for p in publishers
        for s in ['academic_training_evaluation','paper_excerpts','dataset_distribution','production_use','model_distribution']]}
    prior.update(dataset_manifest_sha256=pointer['reference']['sha256'],context_manifest_sha256=pointer['reference']['sha256'])
    packet_path=tmp_path/'packet.json';packet_path.write_bytes(json_bytes(prior))
    unchanged=[r for r in prior['assessments'] if r['scope']!='academic_training_evaluation']
    report={'schema_version':'lanes-academic-use-review-v1','scope':'academic_training_evaluation',
        'training_admitted':0,'docbin_exported':0,'distribution_ready':False,'automatic_admission':False,
        'bindings':{k:pointer['reference'] for k in ['cohort_manifest','context_manifest','review_packet']},
        'unchanged_nonacademic_outcomes':unchanged,'nonacademic_outcomes_sha256':hashlib.sha256(json_bytes(unchanged)).hexdigest(),
        'article_reviews':[{'source_id':r.source.source_id,'publisher':r.source.publisher,'capture_version':r.source.capture_version,
            'text_sha256':r.source.text_sha256,'admission_decision':'unresolved','evidence_pointers':[pointer]} for r in records[:139]],
        'clauses':[{'clause_id':'constructed-policy','pointer':pointer}],
        'assessments':[{'publisher':p,'scope':'academic_training_evaluation','admission_decision':'unresolved','review_state':'complete',
            'source_ids':sorted({r.source.source_id for r in records if r.source.publisher==p}),
            'assessor':{'kind':'ai','name':'constructed AI fixture','reviewed_at':'2026-10-15T12:00:00+08:00'},
            'fair_use_factors':{k:'Explicit constructed factor assessment' for k in ['purpose','nature','amount','market_effect']},
            'clause_ids':['constructed-policy'],'next_actions':[{'owner_type':'researcher','action':'Document actual study facts'}]}
            for p in publishers]}
    report['bindings']['review_packet']={'path':'packet.json','sha256':hashlib.sha256(packet_path.read_bytes()).hexdigest()}
    return records,prior,report


def test_source_exact_unicode_clause_binding(tmp_path):
    records,prior,report=fixture(tmp_path)
    verify_pointer(report['clauses'][0]['pointer'],tmp_path)
    validate_academic_review(report,prior,records,tmp_path)


def test_immutable_publisher_display_alias_is_not_a_different_rights_scope(tmp_path):
    records,prior,report=fixture(tmp_path)
    for record in records:
        if 'abs-cbn.com' in record.source.url:record.source.publisher='ABS-CBN'
    validate_academic_review(report,prior,records,tmp_path)


def test_hash_valid_reference_to_a_different_packet_is_not_the_reviewed_packet(tmp_path):
    records,prior,report=fixture(tmp_path)
    other=tmp_path/'other.json';other.write_bytes(json_bytes({'unrelated':'packet'}))
    report['bindings']['review_packet']={'path':'other.json','sha256':hashlib.sha256(other.read_bytes()).hexdigest()}
    with pytest.raises(ValueError,match='corrected packet'):validate_academic_review(report,prior,records,tmp_path)


@pytest.mark.parametrize('mutation',['admit','export','distribution','automatic','scope','record_count','source_admission',
    'nonacademic','binding_hash','article_duplicate','article_hash','article_admit','missing_publisher','human_claim',
    'undated','factor_missing','factor_blank','clause_unknown','no_actions','owner_missing','evidence_changed','offset'])
def test_unqualified_reviews_cannot_fake_binding_scope_or_admission(tmp_path,mutation):
    records,prior,report=fixture(tmp_path);review=report['assessments'][0]
    if mutation=='admit':report['training_admitted']=400
    elif mutation=='export':report['docbin_exported']=400
    elif mutation=='distribution':report['distribution_ready']=True
    elif mutation=='automatic':report['automatic_admission']=True
    elif mutation=='scope':report['scope']='production_use'
    elif mutation=='record_count':records.pop()
    elif mutation=='source_admission':records[0].source.admission_status='training_admitted'
    elif mutation=='nonacademic':report['unchanged_nonacademic_outcomes'][0]['proposed_outcome']='allowed'
    elif mutation=='binding_hash':report['bindings']['cohort_manifest']['sha256']='0'*64
    elif mutation=='article_duplicate':report['article_reviews'][-1]=deepcopy(report['article_reviews'][0])
    elif mutation=='article_hash':report['article_reviews'][0]['text_sha256']='0'*64
    elif mutation=='article_admit':report['article_reviews'][0]['admission_decision']='allowed'
    elif mutation=='missing_publisher':report['assessments'].pop()
    elif mutation=='human_claim':review['assessor']['kind']='human'
    elif mutation=='undated':review['assessor']['reviewed_at']='2026-10-15'
    elif mutation=='factor_missing':review['fair_use_factors'].pop('market_effect')
    elif mutation=='factor_blank':review['fair_use_factors']['purpose']=' '
    elif mutation=='clause_unknown':review['clause_ids']=['missing']
    elif mutation=='no_actions':review['next_actions']=[]
    elif mutation=='owner_missing':review['next_actions'][0]['owner_type']='invented'
    elif mutation=='evidence_changed':(tmp_path/'evidence.txt').write_text('Changed text')
    else:report['clauses'][0]['pointer']['end']=99999
    with pytest.raises(ValueError):validate_academic_review(report,prior,records,tmp_path)


def test_pointer_cannot_escape_root_or_use_invalid_offsets(tmp_path):
    p=tmp_path/'evidence.txt';p.write_text('research')
    for start,end in [(0,100),(2,1),(True,3)]:
        with pytest.raises(ValueError):clause_pointer(p,tmp_path,start,end)
    with pytest.raises(ValueError):clause_pointer(p,tmp_path/'sub',0,3)
