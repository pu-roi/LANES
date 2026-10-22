"""Constructed proposals distinguish recommendations from actual admission."""
from copy import deepcopy
import hashlib
import json

import pytest

from test_flood_ner_academic_use import fixture as review_fixture
from training.flood_ner.academic_proposal import HOLD, RECOMMEND, validate_decision_proposal
from training.flood_ner.sources import json_bytes, write_jsonl


def fixture(tmp_path):
    records, packet, review = review_fixture(tmp_path)
    slots = [(split, lang) for split, n in [('train', 140), ('dev', 30), ('test', 30)]
             for lang in ['english', 'taglish'] for _ in range(n)]
    for record, (split, lang) in zip(records, slots):
        record.split = split
        record.passage_language = lang
    contexts = [r.model_copy(deep=True) for r in records[:20] + records[140:160]]
    for context in contexts:
        context.annotation_profile = 'context-rich-v1'

    def save(name, data):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(json_bytes(data))
        return {'path': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    for name, rows, filename in [('cohort', records, 'grouped_annotations.jsonl'),
                                  ('context', contexts, 'context_annotations.jsonl')]:
        folder = tmp_path / name
        folder.mkdir()
        write_jsonl(folder / filename, rows)
    cohort = save('cohort/partition_manifest.json', {'files': {
        'grouped_annotations.jsonl': hashlib.sha256((tmp_path/'cohort/grouped_annotations.jsonl').read_bytes()).hexdigest()}})
    context = save('context/manifest.json', {'location_manifest_sha256': cohort['sha256'], 'files': {
        'context_annotations.jsonl': hashlib.sha256((tmp_path/'context/context_annotations.jsonl').read_bytes()).hexdigest()}})
    packet.update(dataset_manifest_sha256=cohort['sha256'], context_manifest_sha256=context['sha256'])
    packet_ref = save('packet.json', packet)
    review['bindings'] = {'cohort_manifest': cohort, 'context_manifest': context, 'review_packet': packet_ref}
    for row in review['article_reviews']:
        row['exception_flags'] = ['byline_not_captured'] if row['source_id']=='s0' else []
    prior_ref = save('prior-review.json', review)
    account = 'researcher@example.org'
    guidance = save('guidance.json', {'access': {'authorized_account': account, 'conforms_to_named_account_privacy': True},
        'use_scope': {'private_research_and_training': True, 'permission_from_publishers_established_by_this_report': False}})
    evidence = save('evidence-register.json', [{'evidence_id': 'constructed-policy', 'outcome': 'captured',
        'substantive': True, 'pointer': review['clauses'][0]['pointer']}])
    bindings = {**review['bindings'], 'prior_review': prior_ref, 'adviser_access': guidance,
        'researcher_facts': save('facts.json', {'bindings': review['bindings']}),
        'access_verification': save('access.json', {'checked_at': '2026-10-15T12:00:00+08:00', 'items': [
            {'id': 'constructed-folder', 'permissions': [{'type': 'user', 'role': 'owner', 'emailAddress': account}]}]}),
        'copy_inventory': save('copies.json', {'distinct_selected_articles': 139,
            'scope_limitations': ['Constructed, bounded inventory; not a global copy total'],
            'containers': [{'kind': 'directory', 'complete_body_string_occurrences': 400}]}),
        'evidence_register': evidence}
    common = {'recommendation': RECOMMEND, 'basis_type': 'policy_and_research_rationale',
        'fair_use_factors': {k: 'Explicit constructed assessment' for k in ['purpose', 'nature', 'amount', 'market_effect']},
        'rationale': 'Constructed research recommendation, not clearance', 'limitations': ['Private study only'],
        'remaining_actions': [], 'evidence_ids': ['constructed-policy'],
        'assessor': {'kind': 'ai', 'name': 'Constructed AI fixture', 'reviewed_at': '2026-10-15T12:00:00+08:00'}}
    rows = []
    for r in records[:139]:
        flags = ['byline_not_captured'] if r.source.source_id == 's0' else []
        rows.append({**deepcopy(common), 'source_id': r.source.source_id, 'publisher': r.source.publisher,
            'capture_version': r.source.capture_version, 'text_sha256': r.source.text_sha256,
            'sample_ids': sorted(v.record_id for v in records if v.source.source_id==r.source.source_id),
            'exception_flags': flags, 'exception_dispositions': {f: 'Do not invent a missing byline' for f in flags}})
    pubs = sorted({r.source.publisher for r in records})
    publisher_rows = []
    for p in pubs:
        ids = sorted(r['source_id'] for r in rows if r['publisher']==p)
        publisher_rows.append({**deepcopy(common), 'publisher': p, 'source_ids': list(ids),
            'recommended_source_ids': list(ids), 'held_source_ids': [], 'covers_all_publisher_articles': True})
    proposal = {'schema_version': 'lanes-private-academic-proposal-v1',
        'scope': 'private_owner_only_academic_ner_training_evaluation', 'authorized_account': account,
        'training_admitted': 0, 'docbin_exported': 0, 'automatic_admission': False, 'source_admission_changed': False,
        'publisher_permission_claimed': False, 'distribution_ready': False, 'bindings': bindings,
        'article_recommendations': rows, 'publisher_recommendations': publisher_rows,
        'actual_project_decisions': [{'publisher': p, 'actual_decision': 'unresolved', 'decision_maker': None,
            'decision_date': None, 'is_publisher_permission': False,
            'evidence_references': {k: bindings[k] for k in ['researcher_facts', 'adviser_access', 'prior_review']}} for p in pubs],
        'unchanged_nonacademic_outcomes': review['unchanged_nonacademic_outcomes'],
        'nonacademic_outcomes_sha256': review['nonacademic_outcomes_sha256']}
    return proposal, records, contexts


def test_complete_constructed_proposal_does_not_mutate_source_admission(tmp_path):
    proposal, records, contexts = fixture(tmp_path)
    before = [r.model_dump() for r in records + contexts]
    result = validate_decision_proposal(proposal, records, contexts, tmp_path)
    assert result['recommendations'] == {RECOMMEND: 139}
    assert result['actual_project_decisions'] == result['training_admitted'] == 0
    assert before == [r.model_dump() for r in records + contexts]


@pytest.mark.parametrize('mutation', [
    'hash', 'broken_reference', 'bare_fact_reference', 'missing_binding', 'missing_evidence', 'failed_evidence',
    'duplicate_article', 'missing_article', 'unsupported_value', 'source_hash', 'sample_ids',
    'missing_factor', 'empty_factor', 'missing_disposition', 'missing_publisher', 'overridden_hold',
    'hold_without_action', 'human_claim', 'undated', 'manufactured_decision', 'publisher_permission',
    'admit', 'export', 'automatic', 'distribution', 'nonacademic', 'context_count', 'context_changed',
    'frozen_record_changed', 'public_access', 'different_owner', 'unbound_guidance', 'copy_count', 'row_admitted',
    'boolean_count', 'malformed_row',
])
def test_proposals_reject_bad_evidence_scope_or_admission(tmp_path, mutation):
    p, records, contexts = fixture(tmp_path)
    row = p['article_recommendations'][0]
    if mutation == 'hash': p['bindings']['prior_review']['sha256'] = '0'*64
    elif mutation == 'broken_reference': p['bindings']['researcher_facts']['path'] = 'missing.json'
    elif mutation == 'bare_fact_reference': p['actual_project_decisions'][0]['evidence_references']['researcher_facts'] = 'facts.json'
    elif mutation == 'missing_binding': p['bindings'].pop('researcher_facts')
    elif mutation == 'missing_evidence': row['evidence_ids'] = []
    elif mutation == 'failed_evidence':
        file = tmp_path/'evidence-register.json'
        data = json.loads(file.read_text(encoding='utf-8'));data[0]['outcome']='failed'
        file.write_bytes(json_bytes(data));p['bindings']['evidence_register']['sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
    elif mutation == 'duplicate_article': p['article_recommendations'][-1] = deepcopy(row)
    elif mutation == 'missing_article': p['article_recommendations'].pop()
    elif mutation == 'unsupported_value': row['recommendation'] = 'licensed'
    elif mutation == 'source_hash': row['text_sha256'] = '0'*64
    elif mutation == 'sample_ids': row['sample_ids'] = []
    elif mutation == 'missing_factor': row['fair_use_factors'].pop('amount')
    elif mutation == 'empty_factor': row['fair_use_factors']['amount'] = ' '
    elif mutation == 'missing_disposition': row['exception_dispositions'] = {}
    elif mutation == 'missing_publisher': p['publisher_recommendations'].pop()
    elif mutation in {'overridden_hold', 'hold_without_action'}:
        row['recommendation'] = HOLD
        row['remaining_actions'] = [] if mutation == 'hold_without_action' else ['Resolve this source-specific gap']
    elif mutation == 'human_claim': row['assessor']['kind'] = 'human'
    elif mutation == 'undated': row['assessor']['reviewed_at'] = '2026-10-15'
    elif mutation == 'manufactured_decision': p['actual_project_decisions'][0]['decision_maker'] = 'Invented adviser signature'
    elif mutation == 'publisher_permission': p['publisher_permission_claimed'] = True
    elif mutation == 'admit': p['training_admitted'] = 400
    elif mutation == 'export': p['docbin_exported'] = 400
    elif mutation == 'automatic': p['automatic_admission'] = True
    elif mutation == 'distribution': p['distribution_ready'] = True
    elif mutation == 'nonacademic': p['unchanged_nonacademic_outcomes'][0]['proposed_outcome'] = 'allowed'
    elif mutation == 'context_count': contexts.pop()
    elif mutation == 'context_changed': contexts[0].entities[0].text = 'Invented location'
    elif mutation == 'frozen_record_changed': records[0].annotation_revision = 'silently changed'
    elif mutation in {'public_access', 'different_owner'}:
        file=tmp_path/'access.json';data=json.loads(file.read_text(encoding='utf-8'))
        if mutation=='public_access':data['items'][0]['permissions'].append({'type':'anyone','role':'reader'})
        else:data['items'][0]['permissions'][0]['emailAddress']='other@example.org'
        file.write_bytes(json_bytes(data));p['bindings']['access_verification']['sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
    elif mutation == 'unbound_guidance': p['authorized_account'] = 'other@example.org'
    elif mutation == 'row_admitted': row['admission_status'] = 'training_admitted'
    elif mutation == 'boolean_count': p['training_admitted'] = False
    elif mutation == 'malformed_row': p['article_recommendations'][0] = None
    elif mutation == 'copy_count':
        file=tmp_path/'copies.json';data=json.loads(file.read_text(encoding='utf-8'));data['containers'][0]['complete_body_string_occurrences']=-1
        file.write_bytes(json_bytes(data));p['bindings']['copy_inventory']['sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
    with pytest.raises(ValueError): validate_decision_proposal(p, records, contexts, tmp_path)


def test_partial_publisher_recommendation_keeps_article_hold_explicit(tmp_path):
    p, records, contexts = fixture(tmp_path)
    row = p['article_recommendations'][0];row['recommendation']=HOLD;row['remaining_actions']=['Clarify credited rights']
    pub = next(v for v in p['publisher_recommendations'] if v['publisher']==row['publisher'])
    pub['recommended_source_ids'].remove(row['source_id']);pub['held_source_ids']=[row['source_id']]
    pub['covers_all_publisher_articles']=False
    result = validate_decision_proposal(p, records, contexts, tmp_path)
    assert result['recommendations'] == {HOLD: 1, RECOMMEND: 138}
