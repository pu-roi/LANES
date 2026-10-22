"""Prepare/verify a single development-only weight-decay experiment; never train."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import io
import math
from pathlib import Path
import statistics
import subprocess
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner.development_error_audit import (
    COUNTS, LABELS, LANGUAGES, bound, digest, read, require, safe_path, write_new)
from training.flood_ner.successor_experiment_preparation import config_values
from training.flood_ner.successor_training import (
    PAYLOAD_FILES, case_sensitive_parser, launch, verify_package, verify_template)

SCOPE = 'development_regularization_preparation_only'
EPSILON = 1e-12
KEY_LABELS = ('ROAD', 'LOCAL_AREA')
IMPLEMENTATION = tuple('backend/training/flood_ner/' + n for n in (
    'regularization_experiment.py', 'regularization_worker.py', 'successor_training.py',
    'successor_preparation.py', 'successor_export_worker.py', 'successor_experiment_preparation.py',
    'successor_experiment_worker.py', 'experiment_registry.py', 'development_error_audit.py',
    'annotation/schema.py', 'annotation/validation.py', 'evaluation/contract.py', 'collection.py'))
TEST_PATH = 'backend/tests/test_flood_ner_regularization_experiment.py'
BINDINGS = frozenset({'preparation_result', 'baseline_manifest', 'development_status',
    'diagnosis_status', 'baseline_metrics', 'desktop_selection', 'preservation'})
SIDECARS = frozenset({'experiment-protocol.json', 'baseline-metrics.json',
                     'development-slices.json', 'cpu-qualification.json'})


def candidate_template(baseline, seed):
    verify_template(baseline, seed)
    parser = case_sensitive_parser(baseline)
    require(parser['training.optimizer']['L2'] == '0.01' and
            parser['training.optimizer']['L2_is_weight_decay'] == 'true', 'wrong control weight decay')
    parser['training.optimizer']['L2'] = '0.05'
    stream = io.StringIO(); parser.write(stream)
    result = stream.getvalue()
    verify_candidate(result, baseline, seed)
    return result


def verify_candidate(text, baseline, seed):
    require(type(seed) is int and seed in (0, 1, 2), 'seed must be 0/1/2')
    verify_template(text, seed); verify_template(baseline, seed)
    expected = config_values(baseline)
    require(expected['training.optimizer', 'L2'] == '0.01' and
            expected['training.optimizer', 'L2_is_weight_decay'] == 'true' and
            expected['training', 'dropout'] == '0.1' and
            expected['training.optimizer', 'learn_rate'] == '0.001' and
            expected['training', 'patience'] == '175', 'wrong corrected-control recipe')
    expected['training.optimizer', 'L2'] = '0.05'
    require(config_values(text) == expected, 'only L2=0.05 may differ from corrected control')


def beats(a, b):
    return a - b > EPSILON


def not_worse(a, b):
    return a - b >= -EPSILON


def checked_metric(row, *, supported_label=False):
    require(isinstance(row, dict), 'metric table required')
    for key in ('TP', 'FP', 'FN', 'reference_spans', 'predicted_spans', 'passages'):
        require(type(row.get(key)) is int and row[key] >= 0, 'nonnegative integer metric counts required')
    tp, fp, fn = (row[k] for k in ('TP', 'FP', 'FN'))
    require(tp + fn == row['reference_spans'] and tp + fp == row['predicted_spans'], 'inconsistent metric counts')
    expected = {'precision': tp / (tp + fp) if tp + fp else None,
                'recall': tp / (tp + fn) if tp + fn else None,
                'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}
    if supported_label and not row['reference_spans']:
        expected['f1'] = None
    for key, value in expected.items():
        actual = row.get(key)
        require(actual is None if value is None else type(actual) in (float, int)
                and math.isfinite(actual) and abs(actual - value) <= EPSILON, 'metric disagrees with strict counts')
    return row


def checked_score(score):
    require(isinstance(score, dict) and set(score) == {'overall', 'labels', 'languages', 'language_labels',
            'negative_passages', 'macro', 'language_macro'}, 'complete development metric tables required')
    checked_metric(score['overall'])
    require(set(score['labels']) == LABELS and set(score['languages']) == {'english', 'taglish'}
            and set(score['language_labels']) == {'english', 'taglish'}, 'six labels and both languages required')
    for row in score['labels'].values(): checked_metric(row, supported_label=True)
    for lang in ('english', 'taglish'):
        checked_metric(score['languages'][lang])
        require(set(score['language_labels'][lang]) == LABELS, 'missing language label')
        for row in score['language_labels'][lang].values(): checked_metric(row, supported_label=True)
        for key in ('TP', 'FP', 'FN', 'reference_spans', 'predicted_spans'):
            require(sum(r[key] for r in score['language_labels'][lang].values()) == score['languages'][lang][key],
                    'language/label totals differ')
    for table in (score['labels'], score['languages']):
        for key in ('TP', 'FP', 'FN', 'reference_spans', 'predicted_spans'):
            require(sum(r[key] for r in table.values()) == score['overall'][key], 'metric totals differ')
    require(sum(r['passages'] for r in score['languages'].values()) == score['overall']['passages'], 'passage totals differ')
    require(set(score['language_macro']) == {'english', 'taglish'}, 'macro languages missing')
    for labels, macro in [(score['labels'], score['macro']), *[(score['language_labels'][lang], score['language_macro'][lang])
                                                             for lang in ('english', 'taglish')]]:
        values = [r['f1'] for r in labels.values() if r['reference_spans'] > 0]
        require(set(macro) == {'supported_labels', 'f1'} and type(macro['supported_labels']) is int
                and macro['supported_labels'] == len(values), 'macro support differs')
        require(macro['f1'] is None if not values else type(macro['f1']) in (float, int)
                and math.isfinite(macro['f1']) and abs(macro['f1'] - statistics.mean(values)) <= EPSILON,
                'supported-label macro differs')
    negatives = score['negative_passages']
    require(set(negatives) == {'overall', 'english', 'taglish'}, 'negative support missing')
    for name, row in negatives.items():
        require(set(row) == {'negative_passages', 'false_positive_passages', 'rate'} and
                all(type(row[k]) is int and row[k] >= 0 for k in ('negative_passages', 'false_positive_passages'))
                and row['false_positive_passages'] <= row['negative_passages'], 'invalid negative counts')
        rate = row['false_positive_passages'] / row['negative_passages'] if row['negative_passages'] else None
        require(row['rate'] is None if rate is None else type(row['rate']) in (float, int)
                and math.isfinite(row['rate']) and row['rate'] == rate, 'negative rate differs')
    for key in ('negative_passages', 'false_positive_passages'):
        require(negatives['overall'][key] == sum(negatives[l][key] for l in ('english', 'taglish')), 'negative totals differ')
    return score


def checked_baseline(baseline):
    require(isinstance(baseline, dict) and set(baseline) == {'0', '1', '2'}, 'three corrected-control seeds required')
    for rows in baseline.values():
        require(set(rows) == {'train', 'dev'}, 'development partitions only')
        for split in ('train', 'dev'):
            score = checked_score(rows[split])
            require(score['overall']['passages'] == COUNTS[split] and
                    {l: row['passages'] for l, row in score['languages'].items()} == LANGUAGES[split], 'baseline slices differ')
        require(rows['dev']['overall']['reference_spans'] == 85 and
                all(rows['dev']['labels'][label]['reference_spans'] > 0 for label in KEY_LABELS), 'baseline support differs')
    return baseline


def protocol(baseline_sha):
    return {'schema': 'lanes-regularization-protocol-v1', 'scope': SCOPE,
            'baseline_metrics_sha256': baseline_sha, 'baseline_family': 'v19_corrected_control',
            'candidate': {'name': 'stronger_weight_decay', 'L2': 0.05, 'L2_is_weight_decay': True},
            'maximum_new_runs': 3, 'ordered_seeds': [0, 1, 2], 'screen_first': True,
            'metric': 'full_precision_strict_validation_micro_f1', 'tie_tolerance': EPSILON,
            'protected_labels': list(KEY_LABELS), 'screening': 'seed0 overall strictly improves; key labels do not regress',
            'retention': 'screen passes; three-seed overall mean strictly improves; key-label means do not regress',
            'ties': 'overall fails improvement; protected-label tie passes nonregression',
            'failure_policy': 'stop; preserve evidence; no retry, concurrency, destination reuse or substitute configuration',
            'training_authorized': False, 'inference_authorized_by_preparation': False,
            'holdout_access_authorized': False, 'repeat_holdout_evaluation_authorized': False,
            'future_run_requirements': ['explicit execution authorization', 'actual qualified desktop GPU',
                'fresh six-class head with pinned encoder initialization', 'new sequential output directories',
                'strict validation checkpoint reload and score reproduction',
                'all-label/language support, negative errors and train/validation gaps',
                'raw stdout/stderr, evaluation-step curves, resolved config, selected/last-step evidence'],
            'validation_is_reused': True, 'claim_unbiased_new_test_improvement': False, 'guaranteed_f1': None}


def schedule(outcomes, baseline):
    """Validate a finite outcome prefix; never dispatch training or inference."""
    checked_baseline(baseline)
    require(isinstance(outcomes, list) and len(outcomes) <= 3, 'at most three ordered outcomes')
    scores = []
    for index, row in enumerate(outcomes):
        require(set(row) == {'seed', 'state', 'validation'} and type(row['seed']) is int and row['seed'] == index,
                'sequential unique seeds 0/1/2 required')
        if index > 0:
            require(screen_passes(scores[0], baseline['0']['dev']), 'failed screening forbids confirmation')
        require(row['state'] in ('completed', 'failed'), 'unknown run state')
        if row['state'] == 'failed':
            require(row['validation'] is None and index == len(outcomes) - 1, 'failure stops sequence')
            return {'state': 'stopped_on_failure', 'next_seed': None, 'retained': 'control',
                    'completed_runs': len(scores), 'training_started': False}
        score = checked_score(row['validation'])
        old = baseline[str(index)]['dev']
        require(score['overall']['passages'] == old['overall']['passages'] and
                all(score['languages'][lang]['passages'] == old['languages'][lang]['passages'] and
                    score['negative_passages'][lang]['negative_passages'] == old['negative_passages'][lang]['negative_passages']
                    for lang in ('english', 'taglish')) and
                all(score['labels'][l]['reference_spans'] == old['labels'][l]['reference_spans'] for l in LABELS)
                and all(score['language_labels'][lang][l]['reference_spans'] == old['language_labels'][lang][l]['reference_spans']
                        for l in LABELS for lang in ('english', 'taglish')), 'candidate reference support changed')
        scores.append(score)
    if scores and not screen_passes(scores[0], baseline['0']['dev']):
        return {'state': 'screening_failed', 'next_seed': None, 'retained': 'control',
                'completed_runs': 1, 'training_started': False}
    if len(scores) < 3:
        return {'state': 'planned_next_run', 'next_seed': len(scores), 'retained': 'control',
                'completed_runs': len(scores), 'training_started': False}
    mean = lambda values: statistics.mean(values)
    gain = beats(mean(s['overall']['f1'] for s in scores),
                 mean(baseline[str(i)]['dev']['overall']['f1'] for i in range(3)))
    protected = all(not_worse(mean(s['labels'][l]['f1'] for s in scores),
                    mean(baseline[str(i)]['dev']['labels'][l]['f1'] for i in range(3))) for l in KEY_LABELS)
    return {'state': 'complete', 'next_seed': None, 'retained': 'stronger_weight_decay' if gain and protected else 'control',
            'completed_runs': 3, 'training_started': False}


def screen_passes(candidate, control):
    return beats(candidate['overall']['f1'], control['overall']['f1']) and all(
        not_worse(candidate['labels'][label]['f1'], control['labels'][label]['f1']) for label in KEY_LABELS)


def verify_grant(root, grant):
    require(set(grant) == {'schema', 'scope', 'permissions', 'bindings', 'implementation', 'tests',
            'development_directory', 'baseline_directory', 'model_directory', 'runtime'}, 'unexpected preparation fields')
    require(grant['schema'] == 'lanes-regularization-grant-v1' and grant['scope'] == SCOPE, 'preparation-only grant required')
    require(grant['permissions'] == dict.fromkeys(('network', 'holdout', 'inference', 'training', 'upload', 'git'), False)
            and all(type(v) is bool for v in grant['permissions'].values()), 'forbidden capabilities')
    require(set(grant['bindings']) == BINDINGS, 'missing predecessor bindings')
    require(all(not any(word in b['path'].lower() for word in ('holdout', 'curator')) for b in grant['bindings'].values()),
            'holdout inputs forbidden')
    paths = {key: bound(root, value) for key, value in grant['bindings'].items()}
    require(len(grant['implementation']) == len(IMPLEMENTATION) and
            {b['path'] for b in grant['implementation']} == set(IMPLEMENTATION), 'implementation bindings differ')
    for item in [*grant['implementation'], grant['tests']]: bound(root, item)
    require(grant['tests']['path'] == TEST_PATH, 'wrong constructed test binding')
    for key in ('development_directory', 'baseline_directory', 'model_directory'):
        require(not any(w in grant[key].lower() for w in ('holdout', 'curator')), 'forbidden directory capability')
    development = safe_path(root, grant['development_directory'])
    baseline = safe_path(root, grant['baseline_directory'])
    model = safe_path(root, grant['model_directory'])
    status = read(paths['development_status'])
    require(paths['development_status'] == development / 'aggregate-status.json' and
            status['capability'] == 'development' and status['counts'] == COUNTS and status['languages'] == LANGUAGES,
            'wrong development export')
    require(set(status['files']) == {'admitted-records.jsonl', 'train.spacy', 'dev.spacy', 'tokenizer.bin',
            'partitions.json', 'source-only-join-metadata.json'}, 'unexpected development capability')
    for name, sha in status['files'].items():
        require(digest(safe_path(development, name)) == sha, 'development input changed')
    parent = read(paths['preparation_result'])
    require(parent['schema'] == 'lanes-corrected-experiment-result-v1' and parent['counts'] == COUNTS
            and parent['training_performed'] is False, 'completed corrected preparation required')
    require(paths['baseline_manifest'] == baseline / 'handoff-manifest.json' and
            parent['files'].get('packages/control/handoff-manifest.json') == digest(paths['baseline_manifest']) and
            parent['files'].get('development/aggregate-status.json') == digest(paths['development_status']), 'wrong control lineage')
    manifest = verify_package(root, baseline, model)
    require(manifest['variant'] == 'control' and manifest['partition_manifest_sha256'] ==
            '4be5213e0b4106d358505027af936bedd7f80b8151345e62362127fcb2a5f20e', 'wrong control or partition lineage')
    for name in ('train.spacy', 'dev.spacy', 'tokenizer.bin'):
        require(digest(baseline / name) == digest(development / name), 'control exports differ')
    diagnosis = read(paths['diagnosis_status'])
    require(diagnosis['state'] == 'passed' and diagnosis['counts'] == COUNTS and diagnosis['prediction_records'] == 1215
            and diagnosis['desktop_metrics_reproduced'] is True and diagnosis['holdout_accessed'] is False
            and diagnosis['files']['metrics.json'] == digest(paths['baseline_metrics']), 'completed development diagnosis required')
    metrics = checked_baseline(read(paths['baseline_metrics']))
    selection = read(paths['desktop_selection'])
    require(selection['schedule']['state'] == 'complete' and selection['schedule']['retained'] == 'control', 'control selection differs')
    for seed in range(3):
        record = next(r for r in selection['outcomes'] if r['variant'] == 'control' and r['seed'] == seed)
        require(all(abs(metrics[str(seed)]['dev']['overall'][k] - record[k]) < 1e-8 for k in ('f1', 'precision', 'recall')),
                'baseline desktop metrics differ')
    runtime = grant['runtime']
    require(set(runtime) == {'python', 'sha256', 'version', 'spacy'} and runtime['version'] == '3.11.17'
            and runtime['spacy'] == '3.7.5' and digest(Path(runtime['python'])) == runtime['sha256'], 'qualified runtime binding differs')
    return paths, development, baseline, model


def verify_preservation(root, path):
    snapshot = read(path)
    for name, row in snapshot['files'].items():
        require('holdout' not in name.lower() or name.endswith(('.py', '.py.txt')), 'holdout content preservation read forbidden')
        p = safe_path(root, name)
        require(p.stat().st_size == row['bytes'] and digest(p) == row['sha256'], 'protected predecessor changed')
    # Only stat metadata: never open completed research-holdout contents here.
    for name, row in snapshot['holdout_metadata_only'].items():
        p = safe_path(root, name)
        require(p.stat().st_size == row['bytes'] and p.stat().st_mtime_ns == row['mtime_ns'], 'protected holdout metadata changed')
    return {'file_bindings': len(snapshot['files']), 'holdout_metadata_entries': len(snapshot['holdout_metadata_only'])}


@contextmanager
def exclusive_lock(path, owner):
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(str(owner))
    try:
        yield
    finally:
        Path(path).unlink()


def portable_files():
    return {'package/' + n for n in PAYLOAD_FILES | {'handoff-manifest.json'}} | {
        f'control-configs/train-seed-{s}.cfg' for s in range(3)} | set(SIDECARS)


def validate_slices(rows):
    from training.flood_ner.successor_preparation import cross_partition_check
    fields = {'record_id', 'partition', 'language', 'is_negative', 'group_keys', 'source_sha256',
              'passage_sha256', 'passage_start', 'passage_end', 'fitted_component', 'alternatives'}
    require(isinstance(rows, list) and len(rows) == 405 and len({r['record_id'] for r in rows}) == 405,
            '405 unique development slice identities required')
    from collections import Counter
    for row in rows:
        require(set(row) == fields and row['partition'] in COUNTS and row['language'] in ('english', 'taglish')
                and type(row['is_negative']) is bool and type(row['fitted_component']) is bool
                and row['group_keys'] and all(isinstance(k, str) and '://' not in k for k in row['group_keys']),
                'development-only source metadata required')
    require(dict(Counter(r['partition'] for r in rows)) == COUNTS and all(
        dict(Counter(r['language'] for r in rows if r['partition'] == s)) == LANGUAGES[s] for s in COUNTS),
        'slice membership/languages differ')
    cross_partition_check(rows, [])
    return rows


def verify_portable(root, experiment, model, expected_sha):
    require(digest(experiment / 'experiment-manifest.json') == expected_sha, 'stale experiment manifest')
    manifest = read(experiment / 'experiment-manifest.json')
    require(manifest['schema'] == 'lanes-regularization-handoff-v1' and manifest['scope'] == SCOPE
            and manifest['training_authorized'] is False, 'wrong experiment handoff')
    require(set(manifest['files']) == portable_files(), 'experiment payload capability differs')
    require({p.relative_to(experiment).as_posix() for p in experiment.rglob('*') if p.is_file()}
            == portable_files() | {'experiment-manifest.json'}, 'unexpected handoff member')
    for name, sha in manifest['files'].items():
        require(digest(safe_path(experiment, name)) == sha, 'portable handoff file changed')
    require(len(manifest['implementation']) == len(IMPLEMENTATION) and
            {b['path'] for b in manifest['implementation']} == set(IMPLEMENTATION), 'portable source bindings differ')
    for binding in manifest['implementation']: bound(root, binding)
    require(manifest['tests']['path'] == TEST_PATH, 'portable test binding differs')
    bound(root, manifest['tests'])
    package = experiment / 'package'; verify_package(root, package, model)
    for seed in range(3):
        verify_candidate((package / f'train-seed-{seed}.cfg').read_text(encoding='utf-8'),
                         (experiment / f'control-configs/train-seed-{seed}.cfg').read_text(encoding='utf-8'), seed)
    baseline = checked_baseline(read(experiment / 'baseline-metrics.json'))
    validate_slices(read(experiment / 'development-slices.json'))
    require(read(experiment / 'experiment-protocol.json') == protocol(digest(experiment / 'baseline-metrics.json')),
            'frozen protocol changed')
    contract = read(package / 'evaluation-contract.json')
    require(contract['holdout_access'] == 'none; completed comparison must not be repeated'
            and contract['repeat_holdout_evaluation_authorized'] is False, 'holdout is closed to this experiment')
    qualification = read(experiment / 'cpu-qualification.json')
    require(qualification['state'] == 'qualified' and qualification['records_qualified'] == 405 and
            qualification['configuration_schemas_verified'] == 3 and qualification['inference_performed'] is False
            and qualification['optimizer_updates'] == 0 and qualification['training_performed'] is False
            and qualification['serialization_reload_verified'] is True and qualification['counts'] == COUNTS
            and qualification['languages'] == LANGUAGES and qualification['python_version'] == '3.11.17'
            and qualification['spacy_version'] == '3.7.5'
            and all(qualification[k] is False for k in ('pipeline_created', 'pretrained_neural_weights_loaded',
                'holdout_accessed', 'gpu_verified', 'private_delivery_complete'))
            and all(qualification[k] is True for k in ('tokenizer_unchanged', 'annotations_unchanged', 'membership_grouping_unchanged')),
            'incomplete CPU qualification')
    require(qualification['export_hashes'] == {n: digest(package / n) for n in ('train.spacy', 'dev.spacy', 'tokenizer.bin')}
            and qualification['source_partition_sha256'] == read(package / 'qualification.json')['files']['partitions.json'],
            'CPU qualification export/group binding differs')
    return manifest, baseline


def verify_result(root, grant_path, expected_sha, output):
    require(digest(grant_path) == expected_sha, 'stale preparation grant')
    grant = read(grant_path)
    paths, development, baseline, model = verify_grant(root, grant)
    result = read(output / 'preparation-result.json')
    require(result['schema'] == 'lanes-regularization-result-v1' and result['scope'] == SCOPE
            and result['grant_sha256'] == expected_sha and result['counts'] == COUNTS
            and result['training_performed'] is False and result['holdout_accessed'] is False, 'wrong result binding')
    for name, sha in result['files'].items():
        require(digest(safe_path(output, name)) == sha, 'prepared output changed')
    verify_portable(root, output / 'experiment', model, result['files']['experiment/experiment-manifest.json'])
    for name in ('train.spacy', 'dev.spacy', 'tokenizer.bin'):
        require(digest(output / 'experiment/package' / name) == digest(development / name), 'frozen export changed')
    require(digest(output / 'experiment/development-slices.json') == digest(development / 'source-only-join-metadata.json'),
            'development metadata changed')
    preserved = verify_preservation(root, paths['preservation'])
    return {'state': 'verified_read_only', 'counts': COUNTS, 'packages': 1, 'configs': 3,
            'L2': 0.05, 'training_authorized': False, 'training_started': False,
            'gpu_verified': False, 'private_delivery_complete': False, 'preserved': preserved}


def prepare(root, grant_path, expected_sha, output):
    require(digest(grant_path) == expected_sha, 'stale preparation grant')
    grant = read(grant_path)
    verify_grant(root, grant)
    artifacts = root / 'backend/training/flood_ner/artifacts'
    require(output.resolve().is_relative_to(artifacts) and not output.exists(), 'new private output required')
    safe_path(root, output.relative_to(root).as_posix())
    with exclusive_lock(artifacts / 'regularization-preparation-active.lock', output):
        write_new(artifacts / ('regularization-preparation-claim-' + expected_sha + '.json'),
                  {'grant_sha256': expected_sha, 'output': str(output), 'training_authorized': False})
        output.mkdir()
        request = output / 'worker-request.json'
        write_new(request, {'root': str(root), 'grant': str(grant_path.resolve()), 'grant_sha256': expected_sha, 'output': str(output)})
        worker = root / 'backend/training/flood_ner/regularization_worker.py'
        try:
            with (output / 'worker.stdout').open('xb') as stdout, (output / 'worker.stderr').open('xb') as stderr:
                process = subprocess.run([grant['runtime']['python'], '-I', '-B', str(worker), str(request)],
                                         cwd=root, stdout=stdout, stderr=stderr, timeout=240, check=False)
            write_new(output / 'worker-outcome.json', {'returncode': process.returncode, 'training_performed': False})
            require(process.returncode == 0, 'CPU qualification failed; preserve private logs')
        except subprocess.TimeoutExpired:
            write_new(output / 'worker-outcome.json', {'state': 'timeout', 'training_performed': False})
            raise ValueError('CPU qualification timed out; preserve evidence; no automatic retry') from None
        return verify_result(root, grant_path, expected_sha, output)


def verify_desktop(root, experiment, expected_sha, interpreter, model, *, verify_gpu=False, start=False):
    require(start is False, 'preparation provides no training authorization')
    verify_portable(root, experiment, model, expected_sha)
    # Explicitly verification-only; existing GPU/schema checks are reused intact.
    result = launch(root, experiment / 'package', interpreter, model, start=False, verify_device=verify_gpu)
    require(result['training_started'] is False, 'verification started training')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', nargs='?', choices=('verify', 'prepare', 'schedule'), default='verify')
    for name in ('checkout', 'experiment', 'grant', 'python', 'model-dir', 'output', 'outcomes'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--grant-sha256'); parser.add_argument('--experiment-sha256')
    parser.add_argument('--verify-gpu', action='store_true')
    args = parser.parse_args()
    require(args.checkout is not None, 'explicit checkout required')
    root = args.checkout.resolve()
    if args.operation == 'prepare':
        require(args.grant and args.grant_sha256 and args.output, 'explicit preparation inputs required')
        result = prepare(root, args.grant.resolve(), args.grant_sha256, args.output.resolve())
    else:
        require(args.experiment and args.model_dir and args.experiment_sha256, 'explicit experiment hash and model paths required')
        if args.operation == 'schedule':
            _, baseline = verify_portable(root, args.experiment.resolve(), args.model_dir.resolve(), args.experiment_sha256)
            require(args.outcomes, 'outcomes file required')
            result = schedule(read(args.outcomes), baseline)
        else:
            require(args.python, 'explicit existing interpreter required')
            result = verify_desktop(root, args.experiment.resolve(), args.experiment_sha256,
                args.python.resolve(), args.model_dir.resolve(), verify_gpu=args.verify_gpu)
    import json
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
