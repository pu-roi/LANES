"""Sequential v19 execution bookkeeping; frozen trainers remain unchanged."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner.successor_experiment_preparation import schedule
from training.flood_ner.successor_training import verify_package

VARIANTS = ('control', 'higher_dropout', 'lower_learning_rate')
LABELS = {'BARANGAY', 'CITY', 'LANDMARK', 'LOCAL_AREA', 'PROVINCE', 'ROAD'}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def tree(path: Path) -> dict:
    return {p.relative_to(path).as_posix(): digest(p) for p in sorted(path.rglob('*')) if p.is_file()}


def write_new(path: Path, value: dict | list) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def check_selection(selection: dict, meta: dict) -> dict:
    if (selection.get('partition') != 'dev' or selection.get('tie_break') != 'earlier checkpoint step'
            or type(selection.get('step')) is not int or not 0 <= selection['step'] < 1000
            or set(meta.get('labels', {}).get('ner', [])) != LABELS or meta.get('pipeline') != ['ner']):
        raise ValueError('invalid six-label development checkpoint selection')
    performance = meta.get('performance', {})
    for name in ('ents_f', 'ents_p', 'ents_r'):
        value = performance.get(name)
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError('finite development precision/recall/F1 required')
    score = selection.get('score')
    if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError('finite full-precision selection F1 required')
    # spaCy serializes meta.json floats to ten decimal places. selection.json
    # retains Python precision and remains authoritative for scheduling.
    if abs(score - performance['ents_f']) > 5.1e-11:
        raise ValueError('selection and checkpoint F1 disagree')
    return {'f1': score, 'precision': performance['ents_p'],
            'recall': performance['ents_r'], 'selected_step': selection['step']}


def stopping_reason(stdout: str, last_meta: dict, selected_step: int | None = None) -> str:
    step = last_meta.get('lanes_training_step')
    if type(step) is not int:
        return 'successful exit; exact stopping cause unavailable'
    if step >= 999:
        return 'configured maximum 1000 steps reached'
    if selected_step is not None and step - selected_step >= 175 and '[+] Saved pipeline' in stdout:
        return 'early stopping after 175 optimizer steps without development improvement'
    if step >= 175 and '[+] Saved pipeline' in stdout:
        return 'completed before maximum budget; consistent with configured early stopping (patience 175)'
    return 'successful exit; exact stopping cause unavailable'


def summarize(outcomes: list[dict]) -> dict:
    decision = schedule([{k: row[k] for k in ('variant', 'seed', 'state', 'f1')} for row in outcomes])
    families = {}
    for variant in VARIANTS:
        rows = [r for r in outcomes if r['variant'] == variant and r['state'] == 'completed']
        scores = [r['f1'] for r in rows]
        families[variant] = {'runs': len(rows), 'seed_0': next((r['f1'] for r in rows if r['seed'] == 0), None),
                             'mean': statistics.mean(scores) if len(scores) == 3 else None,
                             'sample_stddev': statistics.stdev(scores) if len(scores) == 3 else None}
    return {'schedule': decision, 'families': families, 'primary_seed': 0}


def run(root: Path, experiment: Path, validated_prefix: Path | None = None) -> dict:
    artifacts = root / 'backend/training/flood_ner/artifacts'
    bundle = artifacts / 'corrected-experiment-desktop-20261018-v19'
    python = artifacts / 'gpu-qualification-20261015/research-env/Scripts/python.exe'
    model = artifacts / 'gpu-qualification-20261015/model'
    worker = Path(__file__).with_name('corrected_experiment_worker.py')
    outcomes = []
    if validated_prefix is None:
        write_new(experiment / 'execution-started.json', {'explicit_training_authorization': True,
                  'holdout_on_desktop': False, 'maximum_runs': 7})
        (experiment / 'runs').mkdir()
    else:
        # Narrow continuation after a proven post-run bookkeeping defect, never
        # a retry of training or reuse of a training destination.
        correction = json.loads(validated_prefix.read_text())
        if correction['reason'] != 'spacy_meta_rounding_validator_defect' or len(correction['outcomes']) != 1:
            raise ValueError('only the independently validated first run can be carried forward')
        outcomes = correction['outcomes']
        first = outcomes[0]
        if first['variant'] != 'control' or first['seed'] != 0 or first['state'] != 'completed':
            raise ValueError('unexpected validated prefix')
        previous = Path(first['output'])
        if (previous.resolve() != (experiment / 'runs/control-seed-0').resolve()
                or digest(previous / 'selected-checkpoint/selection.json') != first['selection_sha256']
                or check_selection(json.loads((previous / 'selected-checkpoint/selection.json').read_text()),
                                   json.loads((previous / 'selected-checkpoint/model/meta.json').read_text()))['f1'] != first['f1']
                or tree(previous / 'selected-checkpoint/model') != first['checkpoint_files']
                or json.loads((previous / 'run-outcome.json').read_text())['returncode'] != 0
                or json.loads((previous / 'development-check/status.json').read_text())['state'] != 'passed'):
            raise ValueError('validated original run changed')
        write_new(experiment / 'continuation-after-validator-correction.json', correction)
    while True:
        plan = summarize(outcomes)['schedule']
        if plan['state'] == 'complete':
            result = {**summarize(outcomes), 'outcomes': outcomes, 'training_completed': True,
                      'holdout_evaluated': False}
            write_new(experiment / 'development-selection.json', result)
            return result
        if plan['state'] == 'stopped_on_failure':
            raise ValueError('sequence already stopped')
        variant, seed = plan['next']
        package = bundle / 'packages' / variant
        output = experiment / 'runs' / f'{variant}-seed-{seed}'
        if output.exists() or (artifacts / 'successor-training-active.lock').exists():
            raise ValueError('existing destination or active training lock; no automatic recovery')
        verify_package(root, package, model)
        command = [str(python), '-I', '-B', str(Path(__file__).with_name('successor_training.py')),
                   '--checkout', str(root), '--preparation', str(package), '--python', str(python),
                   '--model-dir', str(model), '--start-training', '--seed', str(seed), '--output', str(output)]
        write_new(experiment / f'{variant}-seed-{seed}-command.json', {'command': command})
        print(json.dumps({'state': 'training_started', 'variant': variant, 'seed': seed}), flush=True)
        try:
            with (experiment / f'{variant}-seed-{seed}-launcher.stdout.log').open('xb') as out, \
                 (experiment / f'{variant}-seed-{seed}-launcher.stderr.log').open('xb') as err:
                completed = subprocess.run(command, cwd=root, stdout=out, stderr=err)
            if completed.returncode:
                raise ValueError(f'launcher exited {completed.returncode}; preserve logs')
            if json.loads((output / 'run-outcome.json').read_text())['returncode'] != 0:
                raise ValueError('training subprocess failed')
            selection = json.loads((output / 'selected-checkpoint/selection.json').read_text())
            meta = json.loads((output / 'selected-checkpoint/model/meta.json').read_text())
            metrics = check_selection(selection, meta)
            command = [str(python), '-I', '-B', str(worker), '--checkout', str(root),
                       '--model', str(output / 'selected-checkpoint/model'), '--package', str(package),
                       '--resources', str(model), '--output', str(output / 'development-check')]
            with (output / 'checkpoint-check.stdout.log').open('xb') as out, \
                 (output / 'checkpoint-check.stderr.log').open('xb') as err:
                checked = subprocess.run(command, cwd=root, stdout=out, stderr=err)
            if checked.returncode:
                raise ValueError('selected checkpoint failed load/development check')
            actual = json.loads((output / 'development-check/metrics.json').read_text())
            if abs(actual['overall']['f1'] - metrics['f1']) > 1e-8:
                raise ValueError('development F1 did not reproduce')
            metrics['precision'] = actual['overall']['precision']
            metrics['recall'] = actual['overall']['recall']
            last = json.loads((output / 'spacy/model-last/meta.json').read_text())
            row = {'variant': variant, 'seed': seed, 'state': 'completed', **metrics,
                   'stopping_reason': stopping_reason((output / 'stdout.log').read_text(), last, selection['step']),
                   'last_evaluated_step': last.get('lanes_training_step'), 'output': str(output),
                   'selection_sha256': digest(output / 'selected-checkpoint/selection.json'),
                   'checkpoint_files': tree(output / 'selected-checkpoint/model')}
            outcomes.append(row)
            write_new(experiment / f'outcomes-after-{len(outcomes)}.json', outcomes)
            print(json.dumps({k: v for k, v in row.items() if k != 'checkpoint_files'}), flush=True)
        except BaseException as exc:
            outcomes.append({'variant': variant, 'seed': seed, 'state': 'failed', 'f1': None,
                             'output': str(output), 'error': str(exc)})
            write_new(experiment / 'stopped-on-failure.json', {'outcomes': outcomes, 'error': str(exc)})
            raise


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', type=Path, required=True)
    parser.add_argument('--experiment', type=Path, required=True)
    parser.add_argument('--validated-prefix', type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.checkout.resolve(), args.experiment.resolve(), args.validated_prefix), sort_keys=True))
