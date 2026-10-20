"""One frozen validation-only shadow comparison, using saved spans and no model."""
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
    bound, checked_spans, diagnose, digest, read, require, safe_path, score_partition, write_new)
from training.flood_ner.regularization_comparison import (
    canonical_hash, compare_metrics, components, exclusive, install_guards, transitions)
from training.flood_ner.context_safeguards import raw_record
from training.flood_ner.context_safeguard_cases import core_cases
from training.flood_ner.context_safeguard_study import fixture_checks, jsonl, output_path, SOURCES as STUDY_SOURCES

SCOPE = 'frozen_context_safeguard_validation_only'
ENABLED = ['named_asset', 'shared_identifier']
POLICY = {'scope': SCOPE, 'subset': ENABLED, 'primary_seed': 0, 'records': 60,
    'languages': {'english': 38, 'taglish': 22}, 'tolerance': 1e-12,
    'overall_f1': 'strictly improve beyond tolerance', 'introduced_FP': 0, 'introduced_FN': 0,
    'supported_slice_f1': 'no decline beyond tolerance', 'negative_error_passages': 'no increase',
    'other_combinations': False, 'rule_tuning': False, 'automatic_retry': False,
    'model_selection_change': False, 'integration': False, 'holdout': False}
SOURCES = STUDY_SOURCES + ['backend/training/flood_ner/context_safeguard_validation.py']
TEST = 'backend/tests/test_flood_ner_context_safeguard_validation.py'
PERMISSIONS = dict.fromkeys(('network', 'model_loading', 'inference', 'training', 'holdout', 'upload', 'git'), False)
INPUTS = {'study_manifest', 'study_summary', 'development_status', 'control_predictions',
          'control_metrics', 'annotation_guide', 'scope_guide', 'test_evidence'}
FILES = {'raw-predictions.jsonl', 'references.jsonl', 'groups.json', 'baseline-metrics.json'}


def verify_sources(root, specification):
    require(len(specification['implementation']) == len(SOURCES) and
            {x['path'] for x in specification['implementation']} == set(SOURCES)
            and specification['tests']['path'] == TEST, 'complete validation source/test bindings required')
    for item in [*specification['implementation'], specification['tests']]: bound(root, item)


def stage_validation(records, metadata, predictions):
    """Coordinator projection only; no rule execution or scoring of parent containers."""
    dev_meta = [r for r in metadata if r['partition'] == 'dev']
    expected = {r['record_id']: r for r in dev_meta}
    require(len(expected) == len(dev_meta) == 60 and
            dict(Counter(r['language'] for r in dev_meta)) == POLICY['languages'], 'validation membership mismatch')
    train_groups = {key for row in metadata if row['partition'] == 'train' for key in row['group_keys']}
    require(all(row['group_keys'] and row['fitted_component'] is False and
                not train_groups.intersection(row['group_keys']) for row in dev_meta), 'fitted or split-group leakage')
    from training.flood_ner.annotation.schema import AnnotationRecord
    selected = {}
    for raw in records:
        if raw.get('split') != 'dev': continue
        rid = raw['record_id']; require(rid in expected and rid not in selected, 'duplicate/wrong validation record')
        require(isinstance(raw.get('entities'), list), 'explicit reference required')
        parsed = AnnotationRecord.model_validate_json(json.dumps(raw))
        meta = expected[rid]
        require(parsed.complete and parsed.review_status == 'accepted' and parsed.quality == 'silver'
                and parsed.annotation_profile == 'location-only-v1' and not parsed.facts and not parsed.relations
                and parsed.source.origin == 'captured_original', 'complete original silver reference required')
        require(parsed.text == parsed.source.text[parsed.passage_start:parsed.passage_end]
                and parsed.text_sha256 == meta['passage_sha256'] and parsed.source.text_sha256 == meta['source_sha256']
                and parsed.passage_start == meta['passage_start'] and parsed.passage_end == meta['passage_end']
                and parsed.passage_language == meta['language'] and meta['is_negative'] is (not parsed.entities),
                'source/text/language/polarity metadata mismatch')
        truth = [(e.start, e.end, e.label) for e in parsed.entities]
        checked_spans(truth, parsed.text)
        require(all(parsed.text[e.start:e.end] == e.text for e in parsed.entities), 'entity evidence mismatch')
        selected[rid] = (raw, truth)
    require(set(selected) == set(expected), 'missing validation record')
    guesses = {}
    for row in predictions:
        if row.get('partition') != 'dev' or row.get('seed') != 0: continue
        rid = row['record_id']
        require(type(row['seed']) is int and rid in selected and rid not in guesses, 'duplicate/wrong validation prediction')
        raw, truth = selected[rid]
        require(row['language'] == expected[rid]['language'] and row['text_sha256'] == raw['text_sha256']
                and checked_spans(row['reference'], raw['text']) == checked_spans(truth, raw['text']), 'prediction/reference join mismatch')
        checked_spans(row['prediction'], raw['text']); guesses[rid] = row['prediction']
    require(set(guesses) == set(selected), 'missing primary validation prediction')
    raw_view, refs, groups = [], [], []
    for rid in sorted(selected):
        raw, truth = selected[rid]; meta = expected[rid]
        opaque = 'validation-' + hashlib.sha256(rid.encode()).hexdigest()[:20]
        raw_view.append({'record_id': opaque, 'text': raw['text'], 'prediction': guesses[rid]})
        refs.append({'record_id': opaque, 'partition': 'dev', 'language': meta['language'],
                     'text_sha256': raw['text_sha256'], 'reference': truth})
        groups.append({'record_id': opaque, 'group_keys': [canonical_hash(key) for key in meta['group_keys']]})
    return raw_view, refs, groups


def prepare(root, grant_path, expected_hash, output):
    root, output, artifacts = output_path(root, output)
    require(digest(grant_path) == expected_hash, 'stale validation grant')
    grant = read(grant_path)
    require(set(grant) == {'schema', 'scope', 'protocol', 'permissions', 'inputs', 'implementation', 'tests', 'development_directory'}
            and grant['schema'] == 'lanes-context-validation-grant-v1' and grant['scope'] == SCOPE
            and grant['protocol'] == POLICY and grant['permissions'] == PERMISSIONS
            and all(type(x) is bool for x in grant['permissions'].values()) and set(grant['inputs']) == INPUTS,
            'frozen validation grant required')
    verify_sources(root, grant)
    paths = {key: bound(root, value) for key, value in grant['inputs'].items()}
    previous = read(paths['study_manifest']); summary = read(paths['study_summary'])
    require(digest(paths['study_summary']) == previous['files']['summary.json']
            and summary['qualifying_rule_ids'] == ENABLED and summary['eligible_subset_safe'] is True
            and summary['validation_evaluated'] is False, 'qualifying training study required')
    for item in [*previous['implementation'], previous['tests']]: bound(root, item)
    tests = read(paths['test_evidence'])
    require(tests['scope'] == 'constructed_checks_only' and type(tests['passed']) is int and tests['passed'] > 0
            and tests['failed'] == 0 and tests['implementation'] == grant['implementation']
            and tests['tests'] == grant['tests'], 'matching constructed verification required')
    development = safe_path(root, grant['development_directory']); status = read(paths['development_status'])
    require(status['capability'] == 'development' and status['counts'] == {'train': 345, 'dev': 60}, 'qualified parent required')
    for name in ('admitted-records.jsonl', 'partitions.json'):
        require(digest(development / name) == status['files'][name], 'stale qualified parent')
    raw, refs, groups = stage_validation(jsonl(development / 'admitted-records.jsonl'),
        read(development / 'partitions.json')['members'], jsonl(paths['control_predictions']))
    attempt_key = canonical_hash({'study': grant['inputs']['study_manifest']['sha256'],
        'predictions': grant['inputs']['control_predictions']['sha256'],
        'partitions': digest(development / 'partitions.json'), 'protocol': POLICY})
    with exclusive(artifacts / 'context-validation-preparation-active.lock'):
        output.mkdir()
        for name, rows in [('raw-predictions.jsonl', raw), ('references.jsonl', refs)]:
            with (output / name).open('x', encoding='utf-8', newline='\n') as stream:
                for row in rows: stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
        write_new(output / 'groups.json', groups)
        write_new(output / 'baseline-metrics.json', read(paths['control_metrics'])['0']['dev'])
        write_new(output / 'manifest.json', {'schema': 'lanes-context-validation-view-v1', 'scope': SCOPE,
            'protocol': POLICY, 'capability': 'validation_only', 'grant_sha256': expected_hash,
            'attempt_key': attempt_key, 'parent_bindings_metadata_only': grant['inputs'],
            'source_partition_sha256': digest(development / 'partitions.json'),
            'implementation': grant['implementation'], 'tests': grant['tests'],
            'files': {p.name: digest(p) for p in output.iterdir() if p.is_file()}})
    return {'state': 'validation_view_prepared', 'count': 60, 'comparison_run': False}


def validate_view(raw, references, groups):
    require(len(raw) == len(references) == len(groups) == 60, '60 validation records required')
    ids = {r['record_id'] for r in raw}
    require(len(ids) == 60 and len({r['record_id'] for r in references}) == 60
            and len({r['record_id'] for r in groups}) == 60
            and ids == {r['record_id'] for r in references} == {r['record_id'] for r in groups}, 'validation roster mismatch')
    refs = {r['record_id']: r for r in references}
    for row in raw:
        require(set(row) == {'record_id', 'text', 'prediction'} and isinstance(row['record_id'], str)
                and row['record_id'].startswith('validation-') and isinstance(row['text'], str) and row['text'], 'raw envelope mismatch')
        ref = refs[row['record_id']]
        require(set(ref) == {'record_id', 'partition', 'language', 'text_sha256', 'reference'}
                and ref['partition'] == 'dev' and ref['language'] in POLICY['languages']
                and ref['text_sha256'] == hashlib.sha256(row['text'].encode()).hexdigest(), 'nonvalidation reference mismatch')
        checked_spans(ref['reference'], row['text']); checked_spans(row['prediction'], row['text'])
    require(dict(Counter(r['language'] for r in references)) == POLICY['languages'], 'validation languages differ')
    require(all(set(r) == {'record_id', 'group_keys'} and isinstance(r['group_keys'], list)
                and r['group_keys'] and all(isinstance(k, str) and k for k in r['group_keys']) for r in groups), 'group metadata required')
    return refs


def outcome(metrics, counts):
    before, after = metrics['baseline'], metrics['shadow']; tolerance = POLICY['tolerance']
    pairs = [(before['labels'], after['labels']), (before['languages'], after['languages'])]
    pairs += [(before['language_labels'][lang], after['language_labels'][lang]) for lang in POLICY['languages']]
    no_decline = all(b[k]['f1'] is not None and b[k]['f1'] + tolerance >= value['f1']
        for a, b in pairs for k, value in a.items() if value['reference_spans'] > 0)
    checks = {'overall_f1_improved': after['overall']['f1'] - before['overall']['f1'] > tolerance,
        'no_introduced_FP': counts['introduced_FP'] == 0, 'no_introduced_FN': counts['introduced_FN'] == 0,
        'supported_slice_f1_preserved': no_decline,
        'negative_error_passages_preserved': all(after['negative_passages'][key]['false_positive_passages'] <=
            value['false_positive_passages'] for key, value in before['negative_passages'].items())}
    return {'checks': checks, 'qualifies_for_later_integration_proposal': all(checks.values()),
            'disposition': 'qualifies' if all(checks.values()) else 'does_not_qualify'}


def compare(raw, refs, groups):
    truth = {rid: row['reference'] for rid, row in refs.items()}; langs = {rid: row['language'] for rid, row in refs.items()}
    original = canonical_hash(raw)
    proposals = [raw_record(row, enabled=set(ENABLED)) for row in raw]
    for row, proposal in zip(raw, proposals):
        old = checked_spans(row['prediction'], row['text']); new = checked_spans(proposal['shadow'], row['text'])
        require(proposal['record_id'] == row['record_id'] and {(x[0], x[1]) for x in new} <=
                {(x[0], x[1]) for x in old}, 'shadow additions/boundary or identity changes forbidden')
        require(len(proposal['decisions']) == len(old) and all(d['action'] in ('keep', 'drop', 'retag')
                for d in proposal['decisions']), 'invalid shadow decision roster')
    before = {r['record_id']: r['prediction'] for r in raw}; after = {r['record_id']: r['shadow'] for r in proposals}
    metrics = {'baseline': score_partition(truth, before, langs), 'shadow': score_partition(truth, after, langs)}
    counts = Counter(dict.fromkeys(('changed_passages', 'changed_spans', 'drops', 'retags'), 0))
    records = []; per_rule = {key: Counter(dict.fromkeys(('matched_spans', 'abstentions', 'changed_spans'), 0)) for key in ENABLED}
    for row, proposal in zip(raw, proposals):
        rid = row['record_id']; text = row['text']
        delta = transitions(truth[rid], before[rid], after[rid], text)
        gold = checked_spans(truth[rid], text); old = checked_spans(before[rid], text); new = checked_spans(after[rid], text)
        delta['introduced_FN'] = sorted((gold - new) - (gold - old))
        require(len(delta['introduced_FN']) == len(delta['lost_TP']), 'FN transitions differ')
        counts.update({key: len(spans) for key, spans in delta.items()})
        changed = old != new; counts['changed_passages'] += changed
        for decision in proposal['decisions']:
            require((decision['start'], decision['end']) in {(x[0], x[1]) for x in before[rid]}, 'prediction boundary changed')
            for proof in decision['evidence']:
                require(0 <= proof['start'] < proof['end'] <= len(text)
                        and text[proof['start']:proof['end']] == proof['text'], 'source-inexact decision evidence')
            counts['changed_spans'] += decision['action'] != 'keep'
            counts['drops'] += decision['action'] == 'drop'; counts['retags'] += decision['action'] == 'retag'
            for key in decision['rule_ids']:
                require(key in per_rule, 'unfrozen rule executed')
                per_rule[key]['matched_spans'] += 1; per_rule[key]['abstentions'] += decision['abstained']
                per_rule[key]['changed_spans'] += decision['action'] != 'keep'
        records.append({'record_id': rid, 'text_sha256': refs[rid]['text_sha256'], 'shadow': proposal,
            'transitions': delta, 'prediction_changed': changed,
            'baseline_errors': diagnose(truth[rid], before[rid], text), 'shadow_errors': diagnose(truth[rid], after[rid], text),
            'disposition': 'changed_introduced_strict_error' if delta['introduced_FP'] or delta['introduced_FN'] else
                           'changed_no_new_strict_error' if changed else 'original_prediction_preserved'})
    require(canonical_hash(raw) == original, 'input predictions mutated')
    old, new = metrics['baseline']['overall'], metrics['shadow']['overall']
    require(new['FP'] - old['FP'] == counts['introduced_FP'] - counts['resolved_FP']
            and new['TP'] - old['TP'] == counts['gained_TP'] - counts['lost_TP']
            and new['FN'] - old['FN'] == counts['introduced_FN'] - counts['gained_TP'], 'strict totals do not reconcile')
    index = {r['record_id']: r for r in records}; connected = components(groups)
    group_totals = [{'passages': len(ids), 'changed_passages': sum(index[r]['prediction_changed'] for r in ids),
        'introduced_FP': sum(len(index[r]['transitions']['introduced_FP']) for r in ids),
        'introduced_FN': sum(len(index[r]['transitions']['introduced_FN']) for r in ids),
        'resolved_FP': sum(len(index[r]['transitions']['resolved_FP']) for r in ids),
        'gained_TP': sum(len(index[r]['transitions']['gained_TP']) for r in ids)} for ids in connected]
    concentration = {'connected_groups': len(connected), 'changed_groups': sum(x['changed_passages'] > 0 for x in group_totals),
        'group_contributions_sorted': sorted(group_totals, key=lambda x: tuple(x[k] for k in sorted(x)), reverse=True)}
    return metrics, dict(counts), records, {k: dict(v) for k, v in per_rule.items()}, concentration


def evaluate(root, view, expected_hash, output):
    root, output, artifacts = output_path(root, output)
    view = safe_path(root, Path(view).absolute().relative_to(root).as_posix())
    require(digest(view / 'manifest.json') == expected_hash, 'stale validation view')
    manifest = read(view / 'manifest.json')
    require(manifest['schema'] == 'lanes-context-validation-view-v1' and manifest['scope'] == SCOPE
            and manifest['protocol'] == POLICY and manifest['capability'] == 'validation_only'
            and set(manifest['files']) == FILES and {p.name for p in view.iterdir()} == FILES | {'manifest.json'}, 'validation-only input required')
    verify_sources(root, manifest)
    for name, sha in manifest['files'].items(): require(digest(view / name) == sha, 'changed validation view member')
    parents = manifest['parent_bindings_metadata_only']
    key = canonical_hash({'study': parents['study_manifest']['sha256'], 'predictions': parents['control_predictions']['sha256'],
        'partitions': manifest['source_partition_sha256'], 'protocol': POLICY})
    require(manifest['attempt_key'] == key, 'stale attempt identity')
    fixture_checks(core_cases())
    claims = safe_path(root, 'backend/training/flood_ner/artifacts/context-validation-attempts'); claims.mkdir(exist_ok=True)
    with exclusive(artifacts / 'context-validation-active.lock'):
        write_new(claims / (key + '.json'), {'view_manifest_sha256': expected_hash,
            'grant_sha256': manifest['grant_sha256'], 'protocol': POLICY, 'state': 'consumed_no_automatic_retry'})
        output.mkdir()
        try:
            raw = jsonl(view / 'raw-predictions.jsonl'); refs = validate_view(raw, jsonl(view / 'references.jsonl'), read(view / 'groups.json'))
            baseline = score_partition({rid: r['reference'] for rid, r in refs.items()},
                {r['record_id']: r['prediction'] for r in raw}, {rid: r['language'] for rid, r in refs.items()})
            compare_metrics(baseline, read(view / 'baseline-metrics.json'))
            metrics, counts, decisions, per_rule, concentration = compare(raw, refs, read(view / 'groups.json'))
            verdict = outcome(metrics, counts)
            write_new(output / 'metrics.json', metrics); write_new(output / 'record-decisions.json', decisions)
            summary = {'schema': 'lanes-context-validation-result-v1', 'scope': SCOPE, 'counts': {'dev': 60},
                'languages': POLICY['languages'], 'subset': ENABLED, 'primary_seed': 0, 'transitions': counts,
                'rule_actions': per_rule, 'groups': concentration, 'decision': verdict,
                'record_dispositions': dict(Counter(r['disposition'] for r in decisions)),
                'retained': 'v19_corrected_control_seed_0', 'model_selection_changed': False,
                'holdout_accessed': False, 'neural_inference': False, 'training': False, 'production_integration': False,
                'limitations': ['Motivated by exposed validation findings; reused-validation research, not blinded evaluation.',
                    'AI-assisted silver references and incomplete-history/accounting limitations remain.',
                    'No holdout evaluation, new data, annotation changes or further rule tuning.']}
            verify_sources(root, manifest)
            for name, sha in manifest['files'].items(): require(digest(view / name) == sha, 'validation input changed during comparison')
            write_new(output / 'summary.json', summary)
            write_new(output / 'manifest.json', {'view_manifest_sha256': expected_hash, 'protocol': POLICY,
                'attempt_claim_sha256': digest(claims / (key + '.json')), 'implementation': manifest['implementation'],
                'tests': manifest['tests'], 'files': {p.name: digest(p) for p in output.iterdir() if p.is_file()}})
            return summary
        except BaseException as error:
            write_new(output / 'failure.json', {'type': type(error).__name__, 'reason': str(error),
                'attempt_consumed': True, 'automatic_retry': False, 'holdout_accessed': False, 'training': False})
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('prepare', 'evaluate'))
    for name in ('checkout', 'input', 'output'): parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--input-sha256', required=True)
    args = parser.parse_args(); install_guards()
    result = prepare(args.checkout, args.input, args.input_sha256, args.output) if args.operation == 'prepare' else \
             evaluate(args.checkout, args.input, args.input_sha256, args.output)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__': main()
