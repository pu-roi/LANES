"""Source-bound development context inventory; never a trainer or corpus editor."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any

PLACE_LABELS = frozenset({'ROAD','LANDMARK','LOCAL_AREA','BARANGAY','CITY','PROVINCE'})


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def checked_json(root: Path, binding: dict) -> dict | list:
    from .runtime_preflight import checked_path
    require(set(binding) == {'path', 'sha256'}, 'exact file binding required')
    path = checked_path(root, binding['path'])
    require(digest(path) == binding['sha256'], 'stale input hash')
    return json.loads(path.read_text(encoding='utf-8'))


def validate_development(records: list[dict], metadata: list[dict], tokenizer: Any) -> None:
    from .annotation.schema import AnnotationRecord
    from .annotation.validation import validate_record
    require(len(records) == len(metadata) == 405, '405 development records required')
    by_id = {m['record_id']: m for m in metadata}
    require(len(by_id) == 405 and len({r['record_id'] for r in records}) == 405, 'duplicate identity')
    counts = Counter(); languages = Counter()
    for raw in records:
        r = AnnotationRecord.model_validate_json(json.dumps(raw))
        require(r.split in ('train', 'dev') and r.annotation_profile == 'location-only-v1' and
                r.complete is True and r.review_status == 'accepted', 'qualified development only; holdout forbidden')
        require(not validate_record(r, tokenizer), 'invalid admitted source/reference')
        m = by_id.get(r.record_id)
        require(m is not None and m['partition'] == r.split and m['language'] == r.passage_language and
                m['passage_sha256'] == r.text_sha256 and m['source_sha256'] == r.source.text_sha256 and
                (m['passage_start'], m['passage_end']) == (r.passage_start, r.passage_end), 'metadata/text/partition join mismatch')
        counts[r.split] += 1; languages[(r.split, r.passage_language)] += 1
    require(dict(counts) == {'train': 345, 'dev': 60}, 'partition counts differ')
    require(languages == Counter({('train','english'):170, ('train','taglish'):175,
                                 ('dev','english'):38, ('dev','taglish'):22}), 'language counts differ')


def same_window(left: dict, right: dict) -> bool:
    return (all(left[k] == right[k] for k in ('record_id','text','text_sha256','passage_start','passage_end','passage_language','split'))
            and all(left['source'][k] == right['source'][k] for k in
                    ('source_id','url','capture_version','text_sha256')))


def contextual_state(reference: dict, current: dict, tokenizer: Any) -> dict:
    from .annotation.schema import AnnotationRecord
    from .annotation.validation import validate_record
    from .annotation.context_review import contextual_semantic_errors
    if not same_window(reference, current):
        return {'state': 'identity_or_source_window_mismatch', 'scorable': False}
    try:
        r = AnnotationRecord.model_validate_json(json.dumps(reference))
    except ValueError:
        return {'state':'schema_invalid', 'scorable':False}
    errors = validate_record(r, tokenizer)
    semantic = [e for fact in r.facts for e in contextual_semantic_errors(fact)]
    alignment = [e for e in errors if 'not token aligned' in e]
    structural = [e for e in errors if 'not token aligned' not in e]
    before = [e for e in reference['entities'] if e['label'] in PLACE_LABELS]
    boundary_drift = before != current['entities']
    accepted = r.annotation_profile == 'context-rich-v1' and r.complete and r.review_status == 'accepted'
    state = ('invalid_source_or_semantics' if structural or semantic else 'location_revision_mismatch' if boundary_drift
             else 'complete_existing_silver_reference' if accepted else 'incomplete_reference')
    return {'state':state, 'scorable':state == 'complete_existing_silver_reference',
            'structural_errors':structural, 'semantic_errors':semantic, 'alignment_issues':alignment,
            'location_revision_mismatch':boundary_drift,
            'context_entities':dict(Counter(e['label'] for e in reference['entities'] if e['label'] not in PLACE_LABELS)),
            'fact_kinds':dict(Counter(f['kind'] for f in reference['facts'])),
            'relations':len(reference['relations']), 'review_status':r.review_status,
            'complete_declared':r.complete, 'quality':r.quality}


def inventory(records: list[dict], contexts: list[dict], tokenizer: Any) -> tuple[list[dict], list[dict]]:
    require(len({r['record_id'] for r in contexts}) == len(contexts), 'ambiguous duplicate active context references')
    refs = {r['record_id']:r for r in contexts}; current_ids = {r['record_id'] for r in records}
    result = []
    for r in records:
        ref = refs.get(r['record_id'])
        state = contextual_state(ref, r, tokenizer) if ref is not None else {'state':'missing_context_reference', 'scorable':False}
        result.append({'record_id':r['record_id'],'partition':r['split'],'language':r['passage_language'],
                       'text_sha256':r['text_sha256'],'source_sha256':r['source']['text_sha256'],
                       'location_entities':len(r['entities']),'context':state,
                       'context_negative':bool(state['scorable'] and not ref['entities'] and not ref['facts'] and not ref['relations']),
                       'missing_is_negative':False})
    unmatched = [{'record_id':r['record_id'],'text_sha256':r['text_sha256'],'disposition':'outside_current_development_membership'}
                 for r in contexts if r['record_id'] not in current_ids]
    return result, unmatched


def source_use(record: dict, member: dict, evidence_verified: bool, exact_use_receipt: dict | None = None) -> dict:
    source = record['source']; original = member['record']
    receipt = exact_use_receipt or {}
    receipt_scope = (receipt.get('scope') == 'private_owner_only_academic_training_evaluation' and
                     receipt.get('record_id') == record['record_id'] and
                     receipt.get('source_sha256') == source['text_sha256'] and
                     receipt.get('text_sha256') == record['text_sha256'] and
                     receipt.get('start') == record['passage_start'] and receipt.get('end') == record['passage_end'] and
                     receipt.get('verified') is True)
    supported = (evidence_verified and member['eligibility'].get('source_use') is True and
                 source['reuse_status'] == 'allowed' and source['admission_status'] == 'training_admitted' and
                 original['record_id'] == record['record_id'] and original['text_sha256'] == record['text_sha256'] and
                 original['source']['text_sha256'] == source['text_sha256'] and
                 (original['passage_start'],original['passage_end']) == (record['passage_start'],record['passage_end']) and
                 ('private_owner_only_academic_training_evaluation' in source['reuse_terms'] or receipt_scope))
    return {'supported':bool(supported),'purpose':'private_existing_development_context_diagnosis',
            'scope':'same exact admitted passage; no publisher-policy expansion',
            'capture_terms_stale_but_exact_receipt_supported':bool(receipt_scope and source['reuse_terms']=='not verified'),
            'reason':'Bound admission, exact selected extent and existing private academic evaluation basis' if supported else
                     'Exact extent, source-use evidence or permitted purpose missing; hold unscored'}


def raw_projection(records: list[dict], use: dict[str,dict]) -> list[dict]:
    rows = []
    for r in records:
        if use[r['record_id']]['supported']:
            rows.append({'record_id':r['record_id'],'text':r['text'],'text_sha256':r['text_sha256'],
                         'published_at':r['source']['published_at'] if r['source'].get('publication_basis') else None})
    return rows


def validate_raw(rows: list[dict]) -> None:
    require(isinstance(rows,list) and bool(rows), 'nonempty raw rows required')
    seen = set()
    for row in rows:
        require(set(row) == {'record_id','text','text_sha256','published_at'}, 'references, partitions and predictions forbidden')
        require(isinstance(row['record_id'],str) and re.fullmatch(r'[A-Za-z0-9_-]{1,90}',row['record_id']) is not None and
                row['record_id'] not in seen, 'opaque unique identity required')
        require(isinstance(row['text'],str) and 0 < len(row['text']) <= 100000 and
                text_hash(row['text']) == row['text_sha256'], 'original text/hash required')
        if row['published_at'] is not None:
            d = datetime.fromisoformat(row['published_at'])
            require(d.utcoffset() is not None, 'timezone-qualified supported publication time required')
        seen.add(row['record_id'])


def phrase_candidates(text: str, raw: str | None, sentence_bounds: list[int]) -> list[list[int]]:
    """Only source occurrences within explicit claim evidence; never relocate a heading."""
    if not raw:
        return []
    start,end = sentence_bounds
    return [[i,i+len(raw)] for i in range(start,end) if text.startswith(raw,i) and i+len(raw)<=end]


def reference_phenomena(r: dict) -> list[str]:
    facts={f['id']:f for f in r['facts']}; result=set()
    depth_targets={}; time_targets={}
    for rel in r['relations']:
        fact=facts.get(rel['fact_id'])
        if not fact:continue
        if fact['kind']=='depth':depth_targets[rel['fact_id']]=set(rel['target_entity_ids'])
        if fact['kind']=='time':time_targets[rel['fact_id']]=set(rel['target_entity_ids'])
        if rel['scope']=='shared' and fact['kind']in('depth','time'):result.add('shared_'+fact['kind'])
        if len(rel['target_entity_ids'])>1 and fact['kind']in('depth','time'):
            result.add('multi_target_'+fact['kind'])
            if fact['kind']=='depth'and fact.get('value')is None:result.add('collective_depth_without_uniform_scalar')
    if len(depth_targets)>1 and any(len(t)>1 for t in time_targets.values()):result.add('separate_depths_under_shared_time')
    for f in r['facts']:
        if f['kind']=='depth' and f.get('depth_scope')in('range','collective','maximum'):result.add('depth_'+f['depth_scope'])
        if f['kind']=='time':result.add('time_'+str(f.get('temporal_role')))
        if f['kind']=='status':result.add('status_'+str(f.get('value')))
    return sorted(result)


def rule_features(claims: list[dict]) -> dict:
    return {'claims':len(claims),'depth_claims':sum(bool(c['depth_raw'])for c in claims),
            'time_claims':sum(bool(c['event_time_raw'])for c in claims),
            'resolved_time_claims':sum(bool(c['event_time_resolved'])for c in claims),
            'forecasts':sum(c['is_forecast']for c in claims),'negated':sum(c['is_negated']for c in claims),
            'historical':sum(c['is_historical']for c in claims),
            'conditions':dict(Counter(c['condition']for c in claims)),
            'unlocated_depth_evidence':sum(bool(c['depth_raw'])and not c['depth_span_candidates']for c in claims),
            'unlocated_time_evidence':sum(bool(c['event_time_raw'])and not c['time_span_candidates']for c in claims)}


def compare_context(reference: dict, output: dict, source_review: dict) -> dict:
    """Conservative exact evidence comparisons; missing offset provenance stays unmeasured."""
    require(source_review.get('supported') is True, 'source-reviewed complete reference required')
    result = {}
    for label, field in (('DEPTH','depth_span_candidates'),('TIME','time_span_candidates')):
        gold={(e['start'],e['end'])for e in reference['entities']if e['label']==label}
        predicted={tuple(pair)for c in output['claims']for pair in c[field]if len(c[field])==1}
        ambiguous=sum(len(c[field])>1 for c in output['claims'])
        result[label]={'reference_spans':len(gold),'located_single_occurrence_candidates':len(predicted),
                       'exact_intersections':len(gold&predicted),'reference_only':len(gold-predicted),
                       'candidate_only':len(predicted-gold),'ambiguous_occurrence_claims':ambiguous,
                       'metric_kind':'partial_evidence_overlap_not_full_entity_precision_recall'}
    result['relationships_scored']=False
    result['reason']='Runtime raw depth/time lacks complete explicit span/relationship provenance; report diagnostic overlaps only.'
    return result
