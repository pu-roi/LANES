"""Explicit, bounded v21 execution; frozen package and trainers remain unchanged."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import statistics
import subprocess
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner import regularization_experiment as protocol
from training.flood_ner.corrected_experiment_execution import check_selection, stopping_reason, tree
from training.flood_ner.development_error_audit import digest, read, require, safe_path, write_new

EXPERIMENT_SHA = '35050682217749d945a3c5fecbe5d3771212b1df1276f9f5f95bad4c7d6a0e78'
BUNDLE_NAME = 'regularization-desktop-20261018-v21'
OUTPUT_NAME = 'regularization-v21-experiment-20261019-v1'
NEW_BINDINGS = {
    'backend/training/flood_ner/regularization_experiment_execution.py',
    'backend/training/flood_ner/regularization_development_worker.py',
    'backend/tests/test_flood_ner_regularization_execution.py',
}


def verify_authorization(root, path, expected):
    require(digest(path) == expected, 'execution authorization hash changed')
    grant = read(path)
    require(set(grant) == {'schema', 'explicit_training_authorization', 'maximum_runs',
            'experiment_sha256', 'source_bindings', 'preservation', 'preflight', 'checkout_commit'},
            'unexpected execution authorization fields')
    require(grant['schema'] == 'lanes-v21-execution-authorization-v1'
            and grant['explicit_training_authorization'] is True
            and type(grant['maximum_runs']) is int and grant['maximum_runs'] == 3
            and grant['experiment_sha256'] == EXPERIMENT_SHA, 'bounded explicit training authorization required')
    require(NEW_BINDINGS <= set(grant['source_bindings']), 'execution source/test identities missing')
    for name, expected_sha in grant['source_bindings'].items():
        require(digest(safe_path(root, name)) == expected_sha, 'execution source/test binding changed: ' + name)
    for key in ('preservation', 'preflight'):
        item = grant[key]
        require(set(item) == {'path', 'sha256'} and digest(safe_path(root, item['path'])) == item['sha256'],
                'execution evidence binding changed')
    preflight = read(safe_path(root, grant['preflight']['path']))
    require(preflight.get('state') == 'verified_read_only'
            and preflight.get('gpu_verified') is True
            and preflight.get('configuration_schema_verified') is True
            and preflight.get('training_started') is False, 'actual qualified GPU/schema preflight required')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root).decode().strip()
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=root).decode().strip()
    require(head == grant['checkout_commit'] and branch == 'roi-branch', 'checkout changed after authorization')
    return grant


def verify_preserved(root, grant):
    ledger = read(safe_path(root, grant['preservation']['path']))
    for name, expected in ledger.items():
        require(digest(safe_path(root, name)) == expected, 'protected predecessor changed: ' + name)
    return len(ledger)


def family_summary(scores):
    if len(scores) != 3:
        return {'runs': len(scores), 'mean': None, 'sample_stddev': None, 'labels': None}
    values = [s['overall']['f1'] for s in scores]
    labels = {}
    for label in sorted(protocol.LABELS):
        vals = [s['labels'][label]['f1'] for s in scores]
        labels[label] = {'mean': statistics.mean(vals) if all(v is not None for v in vals) else None,
                         'sample_stddev': statistics.stdev(vals) if all(v is not None for v in vals) else None}
    return {'runs': 3, 'mean': statistics.mean(values), 'sample_stddev': statistics.stdev(values), 'labels': labels}


def run_sequence(experiment, baseline, dispatch, verify_inputs):
    """Exclusive new experiment; persist dispatch before side effects; never resume."""
    protocol.checked_baseline(baseline)
    (experiment / 'runs').mkdir()
    write_new(experiment / 'execution-started.json', {'maximum_runs': 3, 'primary_seed': 0,
              'started_at': datetime.now(timezone.utc).isoformat(), 'holdout_accessed': False})
    outcomes, evidence = [], []
    while True:
        decision = protocol.schedule(outcomes, baseline)
        if decision['next_seed'] is None:
            result = {'schedule': decision, 'outcomes': outcomes, 'runs': evidence, 'primary_seed': 0,
                      'candidate': family_summary([r['validation'] for r in outcomes]),
                      'control': family_summary([baseline[str(s)]['dev'] for s in range(3)]),
                      'holdout_accessed': False}
            write_new(experiment / 'development-selection.json', result)
            return result
        seed = decision['next_seed']
        output = experiment / 'runs' / f'stronger-weight-decay-seed-{seed}'
        require(not output.exists(), 'existing run destination; preserve it without retry')
        try:
            verify_inputs()
            write_new(experiment / f'seed-{seed}-dispatch.json', {'seed': seed, 'output': str(output),
                      'time': datetime.now(timezone.utc).isoformat(), 'automatic_retry_allowed': False})
            row = dispatch(seed, output)
            require(type(row['seed']) is int and row['seed'] == seed, 'dispatched seed mismatch')
            score = protocol.checked_score(row['validation'])
            next_outcomes = outcomes + [{'seed': seed, 'state': 'completed', 'validation': score}]
            next_decision = protocol.schedule(next_outcomes, baseline)
            verify_inputs()
            outcomes, evidence = next_outcomes, evidence + [row]
            write_new(experiment / f'outcomes-after-{seed + 1}.json', {'outcomes': outcomes, 'runs': evidence,
                      'next_decision': next_decision})
            print(__import__('json').dumps({'state': 'seed_validated', 'seed': seed,
                  'f1': score['overall']['f1'], 'road_f1': score['labels']['ROAD']['f1'],
                  'local_area_f1': score['labels']['LOCAL_AREA']['f1'], 'decision': next_decision}), flush=True)
        except BaseException as exc:
            write_new(experiment / 'stopped-on-failure.json', {'outcomes': outcomes, 'runs': evidence,
                      'failed_seed': seed, 'error': str(exc), 'retained': 'control',
                      'automatic_retry_allowed': False, 'holdout_accessed': False})
            raise


def dispatch_one(root, bundle, interpreter, resources, experiment, seed, output):
    artifacts = root / 'backend/training/flood_ner/artifacts'
    require(not output.exists() and not (artifacts / 'successor-training-active.lock').exists(),
            'occupied destination or active training lock; no automatic recovery')
    command = [str(interpreter), '-I', '-B', str(Path(__file__).with_name('successor_training.py')),
               '--checkout', str(root), '--preparation', str(bundle / 'package'), '--python', str(interpreter),
               '--model-dir', str(resources), '--start-training', '--seed', str(seed), '--output', str(output)]
    write_new(experiment / f'seed-{seed}-command.json', {'command': command})
    print(__import__('json').dumps({'state': 'training_started', 'seed': seed, 'output': str(output)}), flush=True)
    with (experiment / f'seed-{seed}-launcher.stdout.log').open('xb') as out, \
            (experiment / f'seed-{seed}-launcher.stderr.log').open('xb') as err:
        completed = subprocess.run(command, cwd=root, stdout=out, stderr=err, check=False)
    require(completed.returncode == 0, 'training launcher failed; preserve logs and partial output')
    require(read(output / 'run-outcome.json')['returncode'] == 0, 'training subprocess failed')
    selection = read(output / 'selected-checkpoint/selection.json')
    meta = read(output / 'selected-checkpoint/model/meta.json')
    selected = check_selection(selection, meta)
    initialization = meta.get('lanes_initialization', {})
    require(initialization.get('optimizer_updates') == 0
            and initialization.get('method', '').startswith('fresh six-class NER head; copied pinned pretrained'),
            'fresh six-class head with pinned encoder evidence required')
    worker = Path(__file__).with_name('regularization_development_worker.py')
    check = [str(interpreter), '-I', '-B', str(worker), '--checkout', str(root), '--bundle', str(bundle),
             '--model', str(output / 'selected-checkpoint/model'), '--resources', str(resources),
             '--output', str(output / 'development-check')]
    write_new(output / 'development-command.json', {'command': check})
    with (output / 'checkpoint-check.stdout.log').open('xb') as out, \
            (output / 'checkpoint-check.stderr.log').open('xb') as err:
        checked = subprocess.run(check, cwd=root, stdout=out, stderr=err, timeout=1200, check=False)
    require(checked.returncode == 0, 'selected checkpoint failed CPU loading/development scoring')
    status = read(output / 'development-check/status.json')
    require(status['state'] == 'passed' and status['holdout_accessed'] is False
            and status['checkpoint_unchanged'] is True, 'invalid checkpoint verification receipt')
    metrics = read(output / 'development-check/metrics.json')
    for partition in ('train', 'dev'):
        protocol.checked_score(metrics[partition])
    require(abs(metrics['dev']['overall']['f1'] - selected['f1']) <= 1e-8,
            'independent development F1 did not reproduce selected checkpoint')
    return {'seed': seed, 'validation': metrics['dev'], 'train': metrics['train'],
            'selected_step': selected['selected_step'], 'selection_score': selected['f1'],
            'stopping_reason': stopping_reason((output / 'stdout.log').read_text(encoding='utf-8'),
                read(output / 'spacy/model-last/meta.json'), selected['selected_step']),
            'output': str(output), 'checkpoint_files': tree(output / 'selected-checkpoint/model'),
            'selection_sha256': digest(output / 'selected-checkpoint/selection.json')}


def execute(root, output, authorization, expected):
    root, output = Path(root).resolve(), Path(output).resolve()
    artifacts = root / 'backend/training/flood_ner/artifacts'
    require(output == artifacts / OUTPUT_NAME and not output.exists(), 'new canonical experiment destination required')
    safe_path(root, output.relative_to(root).as_posix())
    bundle = artifacts / BUNDLE_NAME
    interpreter = artifacts / 'gpu-qualification-20261015/research-env/Scripts/python.exe'
    resources = artifacts / 'gpu-qualification-20261015/model'
    grant = verify_authorization(root, authorization, expected)

    def verify_inputs():
        verify_authorization(root, authorization, expected)
        protocol.verify_portable(root, bundle, resources, EXPERIMENT_SHA)
        verify_preserved(root, grant)

    verify_inputs()
    baseline = read(bundle / 'baseline-metrics.json')
    with protocol.exclusive_lock(artifacts / 'regularization-execution-active.lock', output):
        require(not (artifacts / 'successor-training-active.lock').exists(), 'active training lock; stop')
        # One permanent claim per frozen experiment, including failed attempts.
        write_new(artifacts / ('regularization-execution-claim-' + EXPERIMENT_SHA + '.json'),
                  {'output': str(output), 'authorization_sha256': expected, 'maximum_runs': 3})
        output.mkdir()
        identity = subprocess.check_output(['whoami']).decode().strip()
        subprocess.run(['icacls', str(output), '/inheritance:r', '/grant:r', identity + ':(OI)(CI)F'],
                       check=True, capture_output=True)
        write_new(output / 'execution-authorization.json', grant)
        result = run_sequence(output, baseline,
            lambda seed, destination: dispatch_one(root, bundle, interpreter, resources, output, seed, destination),
            verify_inputs)
        retained = result['schedule']['retained']
        primary = (output / 'runs/stronger-weight-decay-seed-0/selected-checkpoint/model' if retained != 'control'
                   else artifacts / 'corrected-v19-experiment-20261018-v1/runs/control-seed-0/selected-checkpoint/model')
        write_new(output / 'frozen-primary.json', {'retained': retained, 'primary_seed': 0,
                  'model': str(primary), 'checkpoint_files': tree(primary),
                  'tokenizer_sha256': digest(bundle / 'package/tokenizer.bin'),
                  'configuration_sha256': digest(bundle / ('package/train-seed-0.cfg' if retained != 'control'
                                                         else 'control-configs/train-seed-0.cfg')),
                  'holdout_accessed': False})
        write_new(output / 'preservation-final.json', {'unchanged_files': verify_preserved(root, grant),
                  'env_unchanged': True, 'holdout_accessed': False})
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('checkout', 'experiment', 'authorization'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--authorization-sha256', required=True)
    args = parser.parse_args()
    result = execute(args.checkout, args.experiment, args.authorization, args.authorization_sha256)
    print(__import__('json').dumps({'state': 'experiment_completed', 'decision': result['schedule']}))
