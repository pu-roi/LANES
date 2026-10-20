"""Strict, source-bound accounting for saved contextual grouping errors; no extraction."""
from __future__ import annotations

from copy import deepcopy
from .context_acceptance import object_sha
from . import context_association_scoring as scoring

CATEGORIES=frozenset({'code_defect','reference_concern','missing_neural_location',
    'unsupported_context','unresolved_semantics'})


def representation_errors(original: dict, proposed: dict) -> list[str]:
    errors=[]
    if proposed['entities']!=original['entities']:errors.append('contextual entity spans changed')
    before={f['id']:f for f in original['facts']}
    for fact in proposed['facts']:
        if fact['id']in before and any(fact.get(k)!=before[fact['id']].get(k)for k in ('qualifiers','temporal_role')):
            errors.append('protected fact qualifier or time role changed')
    return errors


def time_regressions(reference: dict, previous: dict, candidate: dict) -> dict:
    gold=scoring.reference_keys(reference)['TIME'];old=scoring.output_keys(previous)['TIME'];new=scoring.output_keys(candidate)['TIME']
    return {'new_fp':sorted((new-gold)-(old-gold)),'new_fn':sorted((gold-new)-(gold-old))}


def connected_components(rows: list[dict]) -> list[list[str]]:
    """Join actual article/event/syndication identities, never dictionary names."""
    parent={r['record_id']:r['record_id']for r in rows};seen={}
    if len(parent)!=len(rows):raise ValueError('duplicate group member')
    def root(key: str) -> str:
        while parent[key]!=key:key=parent[key]
        return key
    for row in rows:
        for kind,value in row['groups'].items():
            if value is None:continue
            if not isinstance(value,str)or not value:raise ValueError('explicit group identity required')
            key=(kind,value)
            if key in seen:parent[root(row['record_id'])]=root(seen[key])
            else:seen[key]=row['record_id']
    groups={}
    for row in rows:groups.setdefault(root(row['record_id']),[]).append(row['record_id'])
    return sorted(sorted(members)for members in groups.values())


def error_inventory(reference: dict, output: dict) -> list[dict]:
    """Each strict FP/FN is independent, even when diagnostics pair two keys."""
    gold=scoring.reference_keys(reference)['links']
    predicted=scoring.output_keys(output)['links']
    entities={e['id']:e for e in reference['entities']}
    facts={f['id']:f for f in reference['facts']}
    result=[]
    for polarity, keys in [('incorrect',predicted-gold),('missed',gold-predicted)]:
        for key in sorted(keys):
            evidence=[]
            if polarity=='missed':
                for relation in reference['relations']:
                    if relation['scope']=='unresolved':continue
                    candidate=(scoring.fact_key(facts[relation['fact_id']],entities),
                        tuple(sorted(scoring.span_key(entities[i]) for i in relation['target_entity_ids'])),relation['scope'])
                    if candidate==key:evidence+=relation['evidence']+facts[relation['fact_id']]['evidence']
            else:
                by_id={e['id']:e for e in output['expressions']}
                mentions={e['id']:e for e in output['mentions']}
                fs={f['id']:f for f in output['facts']}
                for relation in output['relations']:
                    candidate=(scoring.fact_key(fs[relation['fact_id']],by_id),
                        tuple(sorted(scoring.span_key(mentions[i]) for i in relation['target_entity_ids'])),relation['scope'])
                    if candidate==key:evidence+=relation['evidence']+fs[relation['fact_id']]['evidence']
            unique={object_sha(e):e for e in evidence}
            for e in unique.values():
                if reference['text'][e['start']:e['end']]!=e['text']:raise ValueError('non-exact error evidence')
            if not unique:raise ValueError('missing source-bound error evidence')
            result.append({'error_id':object_sha([reference['record_id'],polarity,key]),
                'record_id':reference['record_id'],'polarity':polarity,'strict_key':key,
                'reference_sha256':object_sha(reference),'output_sha256':object_sha(output),
                'text_sha256':reference['text_sha256'],'source_sha256':reference['source']['text_sha256'],
                'evidence':list(unique.values()),'strict_count':1})
    return result


def validate_dispositions(inventory: list[dict], dispositions: list[dict]) -> None:
    expected={e['error_id']:e for e in inventory};actual={e['error_id']:e for e in dispositions}
    if len(expected)!=len(inventory) or len(actual)!=len(dispositions) or expected.keys()!=actual.keys():
        raise ValueError('exactly one disposition for every strict error required')
    for identity,row in actual.items():
        if row['category']not in CATEGORIES or not row.get('reason')or not row.get('evidence'):
            raise ValueError('supported category, reason and evidence required')
        if row.get('inventory_sha256')!=object_sha(expected[identity]):raise ValueError('stale strict error binding')


def map_previous(reference: dict, revised: dict|None, outputs: dict, change_evidence: list) -> list[dict]:
    """Preserve an explicit disposition for every previously correct association."""
    gold=scoring.reference_keys(reference)['links']
    sets={name:scoring.output_keys(out)['links'] for name,out in outputs.items()}
    newgold=scoring.reference_keys(revised)['links']if revised is not None else set()
    result=[]
    for key in sorted(gold.intersection(set().union(*sets.values()))):
        disposition='unresolved'if revised is None else'retained'if key in newgold else'corrected'
        if disposition=='corrected'and not change_evidence:raise ValueError('source review required for changed correct link')
        result.append({'key':key,'disposition':disposition,'previous_methods':sorted(n for n,s in sets.items()if key in s),
            'change_evidence':deepcopy(change_evidence)if disposition=='corrected'else[]})
    return result


def fixture_result(case: dict, row: dict, output: dict, *, exhaustive: bool) -> dict:
    from .context_association_v37 import validate_output
    validate_output(row,output)
    gold=scoring.reference_keys(case['record']);predicted=scoring.output_keys(output)
    kinds={f['kind']for f in case['record']['facts']}
    expected={k for k in gold['links']if k[0][0]in kinds};actual={k for k in predicted['links']if k[0][0]in kinds}
    expression_equality=all(gold[label]==predicted[label]for label,kind in [('DEPTH','depth'),('TIME','time')]if kind in kinds)
    invented=bool(output['absolute_instants']or output['numeric_depths'])
    result={'case_id':case['case_id'],'family':case['family'],'language':case['language'],'contrast':case['contrast'],
        'passed':expected==actual and expression_equality and not invented,'association_counts':scoring.strict_counts(expected,actual),
        'expression_equality':expression_equality,'unmeasured_additional_fact_kinds':sorted({f['kind']for f in output['facts']}-kinds),
        'expected_links':sorted(expected),'actual_links':sorted(actual),'unassigned_reference_facts':len(gold['unassigned_facts']),
        'numeric_or_absolute_invention':invented}
    if exhaustive:
        gold=scoring.reference_keys(case['record']);predicted=scoring.output_keys(output)
        result['association_counts']=scoring.strict_counts(gold['links'],predicted['links'])
        result['expression_equality']=all(gold[k]==predicted[k] for k in ('DEPTH','TIME'))
        result['passed']=gold['links']==predicted['links']and result['expression_equality']and not result['numeric_or_absolute_invention']
        result['expected_links']=sorted(gold['links']);result['actual_links']=sorted(predicted['links'])
        result['unmeasured_additional_fact_kinds']=[]
    result['exhaustive_context_oracle']=exhaustive
    return result


def readiness(*, fixture_results: list[dict], metrics: dict, retained_lost: int,
              gained: int, unresolved_references: int, missing_required_targets: int,
              qualifier_failures: int, new_time_fp: int=0,new_time_fn: int=0) -> dict:
    if len(fixture_results)!=208 or len({r['case_id']for r in fixture_results})!=208:
        raise ValueError('all 208 unique fictional checks required')
    blockers=[]
    if not all(r['passed']for r in fixture_results):blockers.append('fictional_behavior_failures')
    if metrics['fp']:blockers.append('known_incorrect_resolved_associations')
    if retained_lost:blockers.append('supported_correct_associations_lost')
    if not gained:blockers.append('no_targeted_correction')
    if unresolved_references:blockers.append('unresolved_reference_questions')
    if missing_required_targets:blockers.append('required_neural_targets_missing')
    if qualifier_failures:blockers.append('qualifier_preservation_failures')
    if new_time_fp or new_time_fn:blockers.append('time_span_regression')
    return {'status':'blocked'if blockers else'eligible_for_separate_read_only_demo_plan',
        'blockers':blockers,'pure_tagalog_real_performance':'unmeasured',
        'application_connected':False,'training_started':False}


def qualify(bundle: dict) -> dict:
    """Source-only tokenizer qualification; no extraction or model components."""
    import hashlib
    import json
    from pathlib import Path
    from types import SimpleNamespace
    from .context_acceptance import install_reference_guards
    from .context_revision_v35 import proposal_errors,source_summary,PRESERVED
    from .annotation.schema import AnnotationRecord
    from .annotation.validation import validate_record
    if set(bundle)!={'files','prior','revised','fixtures','tokenizer','vocab','source_use'}:
        raise ValueError('exact reference/fictional qualification bundle required')
    for key in ('prior','revised','fixtures','tokenizer','source_use'):
        if bundle[key]not in bundle['files']:raise ValueError('unbound qualification input')
    for name,h in bundle['files'].items():
        lower='/'+str(name).replace('\\','/').lower()
        if any(w in lower for w in ('/predictions','/results.jsonl','/holdout','/model-best/','/model-last/')):
            raise ValueError('reference-only qualification scope')
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=h:raise ValueError('stale qualification binding')
    install_reference_guards()
    from spacy.tokenizer import Tokenizer
    from spacy.vocab import Vocab
    raw=Path(bundle['tokenizer']).read_bytes()
    tokenizer=Tokenizer(Vocab().from_disk(bundle['vocab'])).from_bytes(raw,exclude=['vocab'])
    if tokenizer.to_bytes(exclude=['vocab'])!=raw:raise ValueError('tokenizer reconstruction differs')
    prior=json.loads(Path(bundle['prior']).read_text(encoding='utf-8'))
    revised=json.loads(Path(bundle['revised']).read_text(encoding='utf-8'))
    previous={p['proposed']['record_id']:p for p in prior}
    current={r['proposed']['record_id']:r for r in revised}
    if len(previous)!=23 or len(current)!=23 or len(prior)!=23 or len(revised)!=23 or previous.keys()!=current.keys():
        raise ValueError('exact 23 unique source-only counterparts required')
    uses={u['record_id']:u for u in json.loads(Path(bundle['source_use']).read_text(encoding='utf-8'))}
    errors=[]
    for rid,before in previous.items():
        after=current[rid];proposal=after['proposed'];source_summary(proposal)
        if after['original']!=before['proposed']or any(proposal[k]!=before['proposed'][k] for k in PRESERVED):
            raise ValueError('source review changed protected identity')
        errors+=representation_errors(before['proposed'],proposal)
        use=uses.get(rid,{})
        if not(use.get('verified')is True and use.get('scope')=='private_owner_only_academic_training_evaluation'
                and use.get('text_sha256')==proposal['text_sha256']
                and use.get('source_sha256')==proposal['source']['text_sha256']
                and [use.get('start'),use.get('end')]==[proposal['passage_start'],proposal['passage_end']]):
            raise ValueError('unsupported source use')
        errors+=proposal_errors(before['proposed'],proposal,before['current'],after['review'],SimpleNamespace(make_doc=tokenizer))
    fixtures=json.loads(Path(bundle['fixtures']).read_text(encoding='utf-8'))
    if len(fixtures)!=208 or len({c['case_id']for c in fixtures})!=208:raise ValueError('exact 208 fictional cases required')
    for case in fixtures:
        r=AnnotationRecord.model_validate_json(json.dumps(case['record']))
        if r.quality!='constructed'or r.split is not None:raise ValueError('fictional cases cannot be corpus members')
        errors+=validate_record(r,SimpleNamespace(make_doc=tokenizer))
    if errors:raise ValueError('source/tokenizer qualification failed: '+'; '.join(errors))
    return {'status':'qualified_references_and_fictional_cases','references':23,'fixtures':208,
        'tokenizer_reconstruction_verified':True,'neural_inference':False,'training_started':False}


if __name__=='__main__':
    import argparse,json,hashlib
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True);parser.add_argument('--sha256',required=True)
    args=parser.parse_args()
    if hashlib.sha256(args.bundle.read_bytes()).hexdigest()!=args.sha256:raise ValueError('stale bundle')
    print(json.dumps(qualify(json.loads(args.bundle.read_text(encoding='utf-8')))))
