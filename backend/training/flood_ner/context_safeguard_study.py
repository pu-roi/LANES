"""Prepare training-only views, then study frozen text rules in a separate process."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner.development_error_audit import (
    bound, checked_spans, digest, read, require, safe_path, score_partition, write_new)
from training.flood_ner.regularization_comparison import compare_metrics, exclusive, install_guards
from training.flood_ner.context_safeguards import RULES, raw_record
from training.flood_ner.context_safeguard_cases import core_cases

SCOPE = 'training_only_context_safeguard_feasibility'
SOURCES = ['backend/training/flood_ner/' + name for name in (
    'context_safeguards.py', 'context_safeguard_cases.py', 'context_safeguard_study.py',
    'development_error_audit.py', 'regularization_comparison.py', 'evaluation/contract.py',
    'annotation/schema.py')]
TEST = 'backend/tests/test_flood_ner_context_safeguards.py'
VIEW_FILES = {'raw-predictions.jsonl', 'references.jsonl', 'grounding.json', 'rules.json',
              'fixtures.json', 'baseline-metrics.json'}


def sha_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def output_path(root, output):
    root, output = Path(root).resolve(), Path(output).absolute()
    artifacts = root / 'backend/training/flood_ner/artifacts'
    require(output.parent.resolve() == artifacts.resolve() and not output.exists(), 'absent private output required')
    safe_path(root, output.relative_to(root).as_posix())
    return root, output, artifacts


def verify_sources(root, specification):
    require(len(specification['implementation']) == len(SOURCES) and
            {x['path'] for x in specification['implementation']} == set(SOURCES)
            and specification['tests']['path'] == TEST, 'source/test bindings incomplete')
    for value in [*specification['implementation'], specification['tests']]:
        bound(root, value)


def stage_training(records, metadata, baseline_rows):
    """Coordinator-only projection. Nontraining rows are skipped, never scored or emitted."""
    train_meta = [row for row in metadata if row['partition'] == 'train']
    expected = {row['record_id']: row for row in train_meta}
    require(len(expected) == len(train_meta), 'duplicate training metadata')
    require(len(expected) == 345 and dict(Counter(row['language'] for row in expected.values())) ==
            {'english': 170, 'taglish': 175}, 'qualified training membership required')
    selected = {}
    from training.flood_ner.annotation.schema import AnnotationRecord
    for raw in records:
        if raw.get('split') != 'train':
            continue
        rid = raw['record_id']
        require(rid in expected and rid not in selected, 'duplicate or wrong training identity')
        require(isinstance(raw.get('entities'), list), 'explicit complete reference required')
        parsed = AnnotationRecord.model_validate_json(json.dumps(raw))
        require(parsed.annotation_profile == 'location-only-v1' and parsed.complete and
                parsed.review_status == 'accepted' and parsed.quality == 'silver' and
                parsed.source.origin == 'captured_original' and not parsed.facts and not parsed.relations,
                'complete captured training silver references required')
        require(parsed.text == parsed.source.text[parsed.passage_start:parsed.passage_end]
                and parsed.text_sha256 == expected[rid]['passage_sha256']
                and parsed.passage_language == expected[rid]['language'], 'training text/language mismatch')
        spans = [(e.start, e.end, e.label) for e in parsed.entities]
        checked_spans(spans, parsed.text)
        require(all(parsed.text[e.start:e.end] == e.text for e in parsed.entities), 'entity text mismatch')
        selected[rid] = raw
    require(set(selected) == set(expected), 'missing training record')
    guesses = {}
    for row in baseline_rows:
        if row.get('partition') != 'train' or row.get('seed') != 0:
            continue
        rid = row['record_id']
        require(type(row['seed']) is int and rid in selected and rid not in guesses, 'duplicate/wrong primary training prediction')
        raw = selected[rid]
        require(row['text_sha256'] == raw['text_sha256'] and row['language'] == raw['passage_language']
                and checked_spans(row['reference'], raw['text']) ==
                    checked_spans([(e['start'], e['end'], e['label']) for e in raw['entities']], raw['text']),
                'saved training prediction/reference mismatch')
        checked_spans(row['prediction'], raw['text']); guesses[rid] = row['prediction']
    require(set(guesses) == set(selected), 'missing primary training prediction')
    raw_view, references = [], []
    for rid, raw in selected.items():
        opaque = 'train-' + hashlib.sha256(rid.encode()).hexdigest()[:20]
        raw_view.append({'record_id': opaque, 'text': raw['text'], 'prediction': guesses[rid]})
        references.append({'record_id': opaque, 'partition': 'train', 'language': raw['passage_language'],
            'text_sha256': raw['text_sha256'],
            'reference': [(e['start'], e['end'], e['label']) for e in raw['entities']]})
    return raw_view, references, selected


def prepare(root, grant_path, expected_hash, output):
    root, output, artifacts = output_path(root, output)
    require(digest(grant_path) == expected_hash, 'stale preparation grant')
    grant = read(grant_path)
    require(set(grant) == {'schema', 'scope', 'inputs', 'development_directory', 'implementation', 'tests'}
            and grant['schema'] == 'lanes-context-safeguard-preparation-v1' and grant['scope'] == SCOPE
            and set(grant['inputs']) == {'development_status', 'control_predictions', 'control_metrics',
                'grounding', 'annotation_guide', 'scope_guide'}, 'training-only preparation grant required')
    verify_sources(root, grant)
    paths = {key: bound(root, binding) for key, binding in grant['inputs'].items()}
    status = read(paths['development_status']); development = safe_path(root, grant['development_directory'])
    require(status['capability'] == 'development' and status['counts'] == {'train': 345, 'dev': 60}, 'qualified parent required')
    for name in ('admitted-records.jsonl', 'partitions.json'):
        require(digest(development / name) == status['files'][name], 'stale parent input')
    raw_view, references, selected = stage_training(jsonl(development / 'admitted-records.jsonl'),
        read(development / 'partitions.json')['members'], jsonl(paths['control_predictions']))
    grounding = read(paths['grounding'])
    require(set(grounding) == set(RULES), 'grounding for every rule required')
    for items in grounding.values():
        require(items, 'empty training grounding')
        for item in items:
            require(item['record_id'] in selected, 'grounding outside training')
            raw = selected[item['record_id']]
            require(item['text_sha256'] == raw['text_sha256'] and item['source_sha256'] == raw['source']['text_sha256']
                    and 0 <= item['start'] < item['end'] <= len(raw['text'])
                    and raw['text'][item['start']:item['end']] == item['text'], 'stale/source-inexact grounding')
    with exclusive(artifacts / 'context-safeguard-preparation-active.lock'):
        output.mkdir()
        for name, rows in [('raw-predictions.jsonl', raw_view), ('references.jsonl', references)]:
            with (output / name).open('x', encoding='utf-8', newline='\n') as stream:
                for row in rows:
                    stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
        write_new(output / 'grounding.json', grounding)
        write_new(output / 'rules.json', RULES)
        write_new(output / 'fixtures.json', core_cases())
        write_new(output / 'baseline-metrics.json', read(paths['control_metrics'])['0']['train'])
        write_new(output / 'manifest.json', {'schema': 'lanes-context-training-view-v1', 'scope': SCOPE,
            'capability': 'training_only', 'count': 345, 'primary_seed': 0,
            'preparation_grant_sha256': expected_hash, 'parent_bindings_metadata_only': grant['inputs'],
            'implementation': grant['implementation'], 'tests': grant['tests'],
            'source_partition_sha256': digest(development / 'partitions.json'),
            'files': {p.name: digest(p) for p in output.iterdir() if p.is_file()},
            'validation_emitted': False, 'holdout_accessed': False,
            'role': 'audit views only; not new corpus membership or training-format exports'})
    return {'state': 'training_view_prepared', 'count': 345, 'validation_emitted': False, 'training': False}


def validate_view(raw_view, references):
    require(len(raw_view) == len(references) == 345, '345 training records only')
    require(len({x['record_id'] for x in raw_view}) == 345 and
            len({x['record_id'] for x in references}) == 345, 'duplicate view ID')
    refs = {x['record_id']: x for x in references}
    require(set(refs) == {x['record_id'] for x in raw_view}, 'view/reference IDs differ')
    for row in raw_view:
        require(set(row) == {'record_id', 'text', 'prediction'}, 'raw view contains forbidden fields')
        ref = refs[row['record_id']]
        require(set(ref) == {'record_id', 'partition', 'language', 'text_sha256', 'reference'}
                and ref['partition'] == 'train' and ref['language'] in ('english', 'taglish')
                and ref['text_sha256'] == hashlib.sha256(row['text'].encode()).hexdigest(), 'nontraining/mismatched reference')
        checked_spans(ref['reference'], row['text']); checked_spans(row['prediction'], row['text'])
    require(dict(Counter(r['language'] for r in references)) == {'english': 170, 'taglish': 175}, 'language counts differ')
    return refs


def fixture_checks(fixtures):
    require(fixtures == core_cases() and len(fixtures) == 48, 'frozen fictional fixture matrix differs')
    results = []
    for case in fixtures:
        require(case['quality'] == 'constructed' and case['role'] == 'design_fixture_only_not_dataset_membership', 'fixture provenance differs')
        actual = raw_record({'record_id': case['case_id'], 'text': case['text'], 'prediction': case['prediction']})
        decisions = [{'action': r['action'], 'label': r['proposed_label'], 'abstained': r['abstained']} for r in actual['decisions']]
        require(decisions == case['expected_decisions'], 'constructed contract failed: ' + case['case_id'])
        require(raw_record({'record_id': case['case_id'], 'text': case['text'], 'prediction': actual['shadow']})['shadow'] == actual['shadow'],
                'non-idempotent shadow')
        if case['allow_definitive_scoring']:
            require(actual['shadow'] == case['expected_entities'], 'definitive constructed shadow differs')
        else:
            require(case['expected_entities'] is None, 'ambiguous fixture cannot become a negative')
        results.append({'theme': case['theme'], 'language': case['language'], 'contrast': case['contrast'], 'passed': True})
    return results


def run_shadow(raw_view, refs, enabled):
    truth = {rid: r['reference'] for rid, r in refs.items()}
    languages = {rid: r['language'] for rid, r in refs.items()}
    outputs = [raw_record(row, enabled=enabled) for row in raw_view]
    predictions = {r['record_id']: r['prediction'] for r in raw_view}
    shadow = {r['record_id']: r['shadow'] for r in outputs}
    counts = Counter()
    per_record = []
    for row in raw_view:
        rid = row['record_id']; text = row['text']
        gold = checked_spans(truth[rid], text); before = checked_spans(predictions[rid], text); after = checked_spans(shadow[rid], text)
        delta = {'introduced_FP': sorted((after - gold) - (before - gold)),
            'introduced_FN': sorted((gold - after) - (gold - before)),
            'resolved_FP': sorted((before - gold) - (after - gold)),
            'gained_TP': sorted((after & gold) - (before & gold))}
        for key, spans in delta.items(): counts[key] += len(spans)
        per_record.append({'record_id': rid, **delta})
    decisions = [d for row in outputs for d in row['decisions']]
    for key, value in {'matched_spans': sum(bool(d['rule_ids']) for d in decisions),
        'changed_spans': sum(d['action'] != 'keep' for d in decisions),
        'abstentions': sum(d['abstained'] for d in decisions),
        'drops': sum(d['action'] == 'drop' for d in decisions), 'retags': sum(d['action'] == 'retag' for d in decisions)}.items(): counts[key] = value
    return {'metrics': score_partition(truth, shadow, languages), 'counts': dict(counts)}, outputs, per_record


def qualify(counts):
    """Frozen eligibility gate; no firing is evidence of no observed correction, not success."""
    harm = counts['introduced_FP'] + counts['introduced_FN']
    qualifies = counts['changed_spans'] > 0 and harm == 0
    return {'qualifies_for_later_proposal': qualifies,
        'disposition': 'feasible' if qualifies else 'unsupported' if harm else 'partially_supported',
        'reason': 'Constructed checks pass and observed training actions introduce no FP/FN.' if qualifies else
                  'Training harm; hold this rule unchanged.' if harm else
                  'Constructed checks pass, but no corrective training applicability was observed.'}


def study(root, view, expected_hash, output):
    root, output, artifacts = output_path(root, output)
    require(digest(view / 'manifest.json') == expected_hash, 'stale view manifest')
    manifest = read(view / 'manifest.json')
    require(manifest['schema'] == 'lanes-context-training-view-v1' and manifest['scope'] == SCOPE
            and manifest['capability'] == 'training_only' and manifest['count'] == 345
            and manifest['validation_emitted'] is False and manifest['holdout_accessed'] is False
            and set(manifest['files']) == VIEW_FILES, 'training-only view required')
    verify_sources(root, manifest)
    require({p.name for p in view.iterdir()} == VIEW_FILES | {'manifest.json'}, 'unexpected study input')
    for name, sha in manifest['files'].items(): require(digest(view / name) == sha, 'view member changed')
    require(read(view / 'rules.json') == RULES, 'rule definitions changed')
    raw_view = jsonl(view / 'raw-predictions.jsonl'); references = jsonl(view / 'references.jsonl')
    refs = validate_view(raw_view, references)
    fixtures = fixture_checks(read(view / 'fixtures.json'))
    before_hash = sha_json(raw_view)
    with exclusive(artifacts / 'context-safeguard-study-active.lock'):
        output.mkdir()
        baseline = score_partition({rid: r['reference'] for rid, r in refs.items()},
            {row['record_id']: row['prediction'] for row in raw_view}, {rid: r['language'] for rid, r in refs.items()})
        compare_metrics(baseline, read(view / 'baseline-metrics.json'))
        combined, combined_outputs, combined_delta = run_shadow(raw_view, refs, set(RULES))
        rule_results, eligible = {}, []
        for rule_id in RULES:
            result, decisions, deltas = run_shadow(raw_view, refs, {rule_id})
            counts = result['counts']
            result.update(qualify(counts))
            rule_results[rule_id] = result
            if result['qualifies_for_later_proposal']: eligible.append(rule_id)
            write_new(output / (rule_id + '-shadow.json'), {'decisions': decisions, 'strict_changes': deltas})
        subset, subset_outputs, subset_delta = run_shadow(raw_view, refs, set(eligible))
        subset_safe = subset['counts']['introduced_FP'] == subset['counts']['introduced_FN'] == 0
        families = {}
        for family in sorted({r['family'] for r in RULES.values()}):
            members = [key for key, value in RULES.items() if value['family'] == family]
            qualified = [key for key in members if key in eligible]
            families[family] = {'rules': members, 'qualifying_rules': qualified,
                'disposition': 'feasible' if len(qualified) == len(members) else
                               'partially_supported' if qualified or any(rule_results[k]['disposition'] == 'partially_supported' for k in members)
                               else 'unsupported'}
        write_new(output / 'combined-shadow.json', {'decisions': combined_outputs, 'strict_changes': combined_delta})
        write_new(output / 'eligible-subset-shadow.json', {'decisions': subset_outputs, 'strict_changes': subset_delta})
        metrics = {'baseline': baseline, 'combined': combined['metrics'],
            'individual_rules': {key: r['metrics'] for key, r in rule_results.items()}, 'eligible_subset': subset['metrics']}
        write_new(output / 'metrics.json', metrics)
        require(sha_json(raw_view) == before_hash, 'raw predictions mutated')
        for name, sha in manifest['files'].items(): require(digest(view / name) == sha, 'input changed during study')
        verify_sources(root, manifest)
        summary = {'schema': 'lanes-context-safeguard-study-v1', 'scope': SCOPE, 'counts': {'train': 345},
            'languages': dict(Counter(r['language'] for r in references)), 'primary_seed': 0,
            'retained': 'v19_corrected_control', 'fixtures': {'passed': len(fixtures), 'definitive': 36, 'ambiguous_unscored': 12},
            'per_rule': {key: {k: v for k, v in result.items() if k != 'metrics'} for key, result in rule_results.items()},
            'families': families, 'combined_counts': combined['counts'], 'eligible_subset_counts': subset['counts'],
            'eligible_subset_safe': subset_safe, 'qualifying_rule_ids': eligible if subset_safe else [],
            'limitations': ['Motivated by exposed validation findings; not blinded rule discovery.',
                'Training fit and constructed agreement do not establish generalization.',
                'Same-AI silver, reused validation, incomplete history/accounting limitations remain.',
                'No entity additions or boundary repairs; unsupported complex/multiword lists abstain.'],
            'validation_evaluated': False, 'holdout_accessed': False, 'neural_inference': False,
            'training': False, 'production_integration': False, 'model_selection_changed': False}
        write_new(output / 'summary.json', summary)
        write_new(output / 'manifest.json', {'input_manifest_sha256': expected_hash,
            'implementation': manifest['implementation'], 'tests': manifest['tests'],
            'files': {p.name: digest(p) for p in output.iterdir() if p.is_file()}})
        return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('prepare', 'study'))
    for name in ('checkout', 'input', 'output'): parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--input-sha256', required=True)
    args = parser.parse_args(); install_guards()
    result = prepare(args.checkout, args.input, args.input_sha256, args.output) if args.operation == 'prepare' else \
             study(args.checkout, args.input, args.input_sha256, args.output)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__': main()
