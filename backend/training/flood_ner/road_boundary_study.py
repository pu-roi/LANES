"""Frozen training-only road-boundary feasibility; saved spans, never a model."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner.development_error_audit import bound, checked_spans, digest, read, require, score_partition, write_new
from training.flood_ner.regularization_comparison import canonical_hash, compare_metrics, exclusive, install_guards, transitions
from training.flood_ner.context_safeguard_study import jsonl, output_path, qualify, validate_view
from training.flood_ner.road_boundary_rules import RULES, raw_record
from training.flood_ner.road_boundary_cases import core_cases

SCOPE = 'training_only_road_boundary_feasibility'
SOURCES = ['backend/training/flood_ner/' + name for name in ('road_boundary_rules.py', 'road_boundary_cases.py',
    'road_boundary_study.py', 'context_safeguards.py', 'context_safeguard_study.py',
    'development_error_audit.py', 'regularization_comparison.py', 'annotation/schema.py', 'evaluation/contract.py')]
TEST = 'backend/tests/test_flood_ner_road_boundary_study.py'
POLICY = {'scope': SCOPE, 'seed': 0, 'train': 345, 'languages': {'english': 170, 'taglish': 175},
    'actions': ['keep', 'trim', 'split'], 'labels_preserved': True, 'contained_children_only': True,
    'cascading': False, 'type_safeguard_composition': False, 'validation': False, 'holdout': False,
    'qualification': 'constructed checks pass, changed training spans > 0, introduced strict FP = FN = 0',
    'post_result_tuning': False}


def verify_sources(root, grant):
    require(len(grant['implementation']) == len(SOURCES) and {v['path'] for v in grant['implementation']} == set(SOURCES)
            and grant['tests']['path'] == TEST, 'complete boundary-study implementation/tests required')
    for binding in [*grant['implementation'], grant['tests']]: bound(root, binding)


def fixture_checks(cases):
    require(cases == core_cases() and len(cases) == 24, 'frozen fictional matrix differs')
    for case in cases:
        require(case['quality'] == 'constructed' and case['role'] == 'design_only_not_dataset_membership', 'fictional provenance required')
        result = raw_record({'record_id': case['case_id'], 'text': case['text'], 'prediction': case['prediction']})
        require(result['shadow'] == case['expected_shadow'] and all(d['action'] == case['expected_action']
                and d['abstained'] == case['expected_abstention'] for d in result['decisions']), 'fictional contract failed')
        require(raw_record({'record_id': case['case_id'], 'text': case['text'], 'prediction': result['shadow']})['shadow'] == result['shadow'],
                'non-idempotent fictional output')
        require(case['expected_entities'] == result['shadow'] if case['allow_definitive_scoring'] else
                case['expected_entities'] is None, 'ambiguous reference cannot be a negative')
    return {'passed': 24, 'definitive': 18, 'ambiguous_unscored': 6}


def road_roster(raw, refs):
    result = {}
    for row in raw:
        rid = row['record_id']; gold = checked_spans(refs[rid]['reference'], row['text'])
        prediction = checked_spans(row['prediction'], row['text'])
        fp = sorted(p for p in prediction - gold if p[2] == 'ROAD'); fn = sorted(p for p in gold - prediction if p[2] == 'ROAD')
        if fp or fn: result[rid] = {'ROAD_FP': fp, 'ROAD_FN': fn}
    return result


def verify_reviews(raw, refs, evidence):
    roster = road_roster(raw, refs); index = {r['record_id']: r for r in raw}
    require(set(evidence) == {'sources', 'reviews', 'grounding'} and set(evidence['reviews']) == set(roster)
            and set(evidence['grounding']) == set(RULES), 'every ROAD error and rule requires training evidence')
    for sha, source in evidence['sources'].items():
        require(hashlib.sha256(source.encode()).hexdigest() == sha, 'source review hash differs')
    for rid, review in evidence['reviews'].items():
        require(canonical_hash(review['errors']) == canonical_hash(roster[rid]) and review['full_article_reviewed'] is True
                and review['text_sha256'] == refs[rid]['text_sha256'] and review['reason']
                and review['disposition'] in ('boundary_ambiguity_hold', 'non_ROAD_prediction_preserved',
                    'typing_only_unchanged', 'source_supported_boundary_candidate'),
                'incomplete training ROAD disposition')
        source = evidence['sources'][review['source_sha256']]
        require(0 <= review['passage_start'] < review['passage_end'] <= len(source)
                and source[review['passage_start']:review['passage_end']] == index[rid]['text'], 'source-inexact passage review')
    for items in evidence['grounding'].values():
        require(items, 'empty rule grounding')
        for item in items:
            require(item['record_id'] in index and item['text_sha256'] == refs[item['record_id']]['text_sha256']
                    and 0 <= item['start'] < item['end'] <= len(index[item['record_id']]['text'])
                    and index[item['record_id']]['text'][item['start']:item['end']] == item['text'], 'nontraining or inexact grounding')
    return {'error_passages': len(roster), 'full_articles': len(evidence['sources']),
            'ROAD_FP': sum(len(x['ROAD_FP']) for x in roster.values()), 'ROAD_FN': sum(len(x['ROAD_FN']) for x in roster.values())}


def score_shadow(raw, refs, enabled):
    original = canonical_hash(raw); truth = {rid: r['reference'] for rid, r in refs.items()}
    languages = {rid: r['language'] for rid, r in refs.items()}
    proposals = [raw_record(row, enabled=enabled) for row in raw]
    counts = Counter(dict.fromkeys(('changed_spans', 'changed_passages', 'matched_spans', 'abstentions', 'trims', 'splits', 'net_entity_change'), 0))
    changes = []
    for row, proposal in zip(raw, proposals):
        delta = transitions(truth[row['record_id']], row['prediction'], proposal['shadow'], row['text'])
        delta['introduced_FN'] = delta['lost_TP']
        counts.update({key: len(value) for key, value in delta.items()})
        counts['changed_passages'] += any(d['action'] != 'keep' for d in proposal['decisions'])
        counts['net_entity_change'] += len(proposal['shadow']) - len(row['prediction'])
        for d in proposal['decisions']:
            counts['changed_spans'] += d['action'] != 'keep'; counts['matched_spans'] += bool(d['rule_ids'])
            counts['abstentions'] += d['abstained']; counts['trims'] += d['action'] == 'trim'; counts['splits'] += d['action'] == 'split'
        changes.append({'record_id': row['record_id'], **delta})
    require(canonical_hash(raw) == original, 'original saved predictions changed')
    return {'metrics': score_partition(truth, {r['record_id']: r['shadow'] for r in proposals}, languages),
            'counts': dict(counts)}, proposals, changes


def run(root, grant_path, expected_hash, output):
    root, output, artifacts = output_path(root, output)
    require(digest(grant_path) == expected_hash, 'stale boundary grant')
    grant = read(grant_path)
    require(set(grant) == {'schema', 'scope', 'protocol', 'inputs', 'implementation', 'tests'}
            and grant['schema'] == 'lanes-road-boundary-grant-v1' and grant['scope'] == SCOPE and grant['protocol'] == POLICY
            and set(grant['inputs']) == {'training_manifest', 'reviews', 'annotation_guide', 'scope_guide', 'test_evidence'},
            'training-only boundary grant required')
    verify_sources(root, grant); paths = {k: bound(root, b) for k, b in grant['inputs'].items()}
    manifest = read(paths['training_manifest']); view = paths['training_manifest'].parent
    require(manifest['schema'] == 'lanes-context-training-view-v1' and manifest['capability'] == 'training_only'
            and manifest['count'] == 345 and manifest['primary_seed'] == 0 and manifest['validation_emitted'] is False
            and manifest['holdout_accessed'] is False, 'original training-only view required')
    for item in [*manifest['implementation'], manifest['tests']]: bound(root, item)
    for name in ('raw-predictions.jsonl', 'references.jsonl', 'baseline-metrics.json'):
        require(digest(view / name) == manifest['files'][name], 'training input changed')
    tests = read(paths['test_evidence'])
    require(tests['scope'] == 'constructed_checks_only' and type(tests['passed']) is int and tests['passed'] > 0
            and tests['failed'] == 0 and tests['implementation'] == grant['implementation'] and tests['tests'] == grant['tests'],
            'matching constructed tests required')
    fixtures = fixture_checks(core_cases())
    raw = jsonl(view / 'raw-predictions.jsonl'); refs = validate_view(raw, jsonl(view / 'references.jsonl'))
    reviews = verify_reviews(raw, refs, read(paths['reviews']))
    baseline = score_partition({rid: r['reference'] for rid, r in refs.items()}, {r['record_id']: r['prediction'] for r in raw},
                               {rid: r['language'] for rid, r in refs.items()})
    compare_metrics(baseline, read(view / 'baseline-metrics.json'))
    with exclusive(artifacts / 'road-boundary-study-active.lock'):
        output.mkdir()
        try:
            write_new(output / 'rules.json', RULES); write_new(output / 'fixtures.json', core_cases())
            results = {}; eligible = []; metrics = {'baseline': baseline, 'individual_rules': {}}
            for key in RULES:
                result, decisions, changes = score_shadow(raw, refs, {key}); result.update(qualify(result['counts']))
                results[key] = {k: v for k, v in result.items() if k != 'metrics'}
                metrics['individual_rules'][key] = result['metrics']
                if result['qualifies_for_later_proposal']: eligible.append(key)
                write_new(output / (key + '-shadow.json'), {'decisions': decisions, 'strict_changes': changes})
            combined, decisions, changes = score_shadow(raw, refs, set(RULES))
            write_new(output / 'combined-shadow.json', {'decisions': decisions, 'strict_changes': changes})
            subset, decisions, changes = score_shadow(raw, refs, set(eligible))
            write_new(output / 'qualifying-subset-shadow.json', {'decisions': decisions, 'strict_changes': changes})
            safe = subset['counts']['introduced_FP'] == subset['counts']['introduced_FN'] == 0
            families = {}
            for family in ('trimming', 'splitting'):
                members = [k for k, value in RULES.items() if value['family'] == family]; qualified = [k for k in members if k in eligible]
                families[family] = {'rules': members, 'qualifying_rules': qualified if safe else [],
                    'disposition': 'feasible' if safe and len(qualified) == len(members) else 'partially_supported' if
                        qualified or any(results[k]['disposition'] == 'partially_supported' for k in members) else 'unsupported'}
            metrics.update(combined=combined['metrics'], qualifying_subset=subset['metrics']); write_new(output / 'metrics.json', metrics)
            for name in ('raw-predictions.jsonl', 'references.jsonl', 'baseline-metrics.json'):
                require(digest(view / name) == manifest['files'][name], 'training input changed during study')
            verify_sources(root, grant)
            summary = {'schema': 'lanes-road-boundary-study-v1', 'scope': SCOPE, 'counts': {'train': 345},
                'languages': POLICY['languages'], 'primary_seed': 0, 'fixtures': fixtures, 'ROAD_review': reviews,
                'per_rule': results, 'families': families, 'combined_counts': combined['counts'],
                'qualifying_subset_counts': subset['counts'], 'qualifying_subset_safe': safe,
                'qualifying_rules': eligible if safe else [], 'retained': 'v19_corrected_control_seed_0',
                'validation_evaluated': False, 'holdout_accessed': False, 'neural_inference': False, 'training': False,
                'production_integration': False, 'type_safeguard_composed': False,
                'limitations': ['Motivated by exposed validation findings; not blinded.', 'Training agreement is not generalization.',
                    'AI-assisted silver and incomplete-history/accounting limitations remain.',
                    'No prefix expansion, type changes, unmarked crossing inference or post-result tuning.']}
            write_new(output / 'summary.json', summary)
            write_new(output / 'manifest.json', {'grant_sha256': expected_hash, 'inputs': grant['inputs'],
                'implementation': grant['implementation'], 'tests': grant['tests'],
                'files': {p.name: digest(p) for p in output.iterdir() if p.is_file()}})
            return summary
        except BaseException as error:
            write_new(output / 'failure.json', {'type': type(error).__name__, 'reason': str(error),
                       'training': False, 'validation_evaluated': False, 'holdout_accessed': False})
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('checkout', 'grant', 'output'): parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--grant-sha256', required=True)
    args = parser.parse_args(); install_guards()
    import json
    print(json.dumps(run(args.checkout, args.grant, args.grant_sha256, args.output), sort_keys=True))


if __name__ == '__main__': main()
