"""Freeze and evaluate a fixed held-out roster; never select models on test scores."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
from typing import Any
from unittest.mock import patch

from .validation_comparison import (LABELS, checked_predictions, coarse, digest,
                                    require, score_spans, selected_run)

SCHEMA = 'lanes-frozen-test-experiment-v1'
ROSTER = tuple((family, seed) for family in ('original', 'A') for seed in (0, 1, 2))
SOURCES = ('heldout_test.py', 'heldout_test_worker.py', 'validation_comparison.py',
           'validation_worker.py', 'manual_training.py', 'study_recipes.py', 'cli.py',
           'evaluation/contract.py')


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')


def reference(path: Path, root: Path) -> dict:
    return {'path': path.resolve().relative_to(root.resolve()).as_posix(), 'sha256': digest(path)}


def private_existing(path: Path, root: Path) -> Path:
    artifacts = (root / 'backend/training/flood_ner/artifacts').resolve()
    require(path.absolute().resolve().is_relative_to(artifacts), 'private artifact input required')
    for p in (path.absolute(), *path.absolute().parents):
        require(not p.is_symlink() and not getattr(p, 'is_junction', lambda: False)(), 'linked artifact input refused')
        if p == artifacts:
            break
    require(path.exists(), 'artifact input missing')
    return path.resolve()


def test_rows(cases: list[dict]) -> list[dict]:
    locations = [v for v in cases if v.get('kind') == 'location']
    require(len(locations) == len({v['record_id'] for v in locations}), 'duplicate location memberships')
    rows = sorted((v for v in locations if v['split'] == 'test'), key=lambda v: v['record_id'])
    validate_rows(rows)
    require(not ({v['record_id'] for v in rows} &
                 {v['record_id'] for v in cases if v.get('kind') in {'location', 'context'}
                  and (v['kind'] != 'location' or v['split'] != 'test')}),
            'test membership overlaps another partition/context')
    return rows


def validate_rows(rows: list[dict]) -> None:
    require(len(rows) == len({v['record_id'] for v in rows}) == 60
            and all(v['kind'] == 'location' and v['split'] == 'test' for v in rows)
            and Counter(v['language'] for v in rows) == {'english': 30, 'taglish': 30},
            '60 unique test locations, 30 English/30 Taglish required')
    require(all(hashlib.sha256(v['text'].encode('utf-8')).hexdigest() == v['text_sha256'] for v in rows),
            'test passage hash changed')
    truth = {v['record_id']: [(e['start'], e['end'], e['label']) for e in v['entities']] for v in rows}
    checked_predictions(rows, truth, LABELS)
    score_spans(truth, truth, {v['record_id']: v['language'] for v in rows})


def memberships(rows: list[dict]) -> list[dict]:
    return [{k: v[k] for k in ('record_id', 'kind', 'split', 'language', 'text_sha256')} |
            {'entities_sha256': hashlib.sha256(json.dumps(v['entities'], sort_keys=True).encode('utf-8')).hexdigest()}
            for v in rows]


def fixed_roster(records: list[dict]) -> list[dict]:
    chosen = [v for v in records if v['family'] in {'original', 'A'}]
    require(len(chosen) == 6 and all(type(v['seed']) is int for v in chosen)
            and Counter((v['family'], v['seed']) for v in chosen) == Counter(ROSTER),
            'exact original/A seeds 0/1/2 required')
    for v in chosen:
        require(v['recipe'] == ('recovery' if v['family'] == 'original' and v['seed'] == 2 else v['family']),
                'original seed 2 must resolve to recovery; fixed recipe identities required')
    return sorted(chosen, key=lambda v: ROSTER.index((v['family'], v['seed'])))


def load_inputs(preparation: Path, root: Path) -> dict:
    from . import corpus_tokenizer_qualification as q
    from .manual_training import validate_inputs
    from .qualified_export import passed_package
    plan = validate_inputs(root, preparation, require_new_output=False)
    prep = q.bound_manifest(preparation / 'manifest.json')
    qualification = q.verified_reference(prep['qualification'], root).parent
    _, paths = passed_package(qualification, root)
    cases, _, _ = q.inputs(paths['cohort'].parent, paths['context'].parent, paths['admission_package'], root)
    _, native = q.verify_model(paths['model_manifest'], root / 'backend/training/flood_ner/artifacts')
    export = q.verified_reference(prep['export'], root).parent
    return {'plan': plan, 'prep': prep, 'rows': test_rows(cases), 'native': native, 'export': export,
            'qualification': qualification, 'contract': q.verified_reference(prep['evaluation_contract'], root)}


def freeze_test_experiment(preparation: Path, study_report: Path, output: Path, root: Path) -> dict:
    from . import corpus_tokenizer_qualification as q
    from .qualified_export import new_output
    from .study_recipes import validate_trial
    output = new_output(root, output)
    inputs = load_inputs(preparation, root)
    q.bound_manifest(study_report / 'metadata-hashes.json')
    report = read(study_report / 'verification.json')
    require(report['state'] == 'passed' and report['scope_completed'] is True
            and report['test_predictions_performed'] is False and report['selection']['winner'] == 'A',
            'completed validation-only study with selected recipe A required')
    runs = []
    for record in fixed_roster(report['runs']):
        folder = private_existing(root / record['folder'], root)
        for key in ('status_binding', 'selection_binding', 'config'):
            q.verified_reference(record[key], root)
        run = selected_run(folder, record['seed'])
        require(run['selection'] == record['status']['selection'], 'development selection changed')
        launch = read(folder / 'launch-request.json')
        require(launch['preparation_sha256'] == digest(preparation / 'manifest.json'), 'run preparation differs')
        if record['recipe'] in {'A', 'recovery'}:
            study = Path(launch['study_manifest'])
            require(digest(study) == launch['study_manifest_sha256'] and launch['recipe'] == record['recipe'],
                    'trial/recovery study differs')
            expected = validate_trial(study.parent, record['recipe'], record['seed'], require_new_output=False)
            require(folder == Path(expected['output']) and launch['config_sha256'] == expected['config_sha256'],
                    'trial output/configuration differs')
        else:
            require(folder == (root / inputs['prep']['future_training_root'] / ('seed-' + str(record['seed']))).resolve()
                    and launch['config_sha256'] == inputs['prep']['files']['train-seed-' + str(record['seed']) + '.cfg'],
                    'original run output/configuration differs')
        require(launch['config_sha256'] == record['config']['sha256'] and Path(launch['config']).resolve() == (root / record['config']['path']).resolve(),
                'recorded configuration differs')
        run.update(name=record['family'] + '-seed-' + str(record['seed']), family=record['family'],
                   role=('primary' if record['family'] == 'original' and record['seed'] == 0 else
                         'exploratory' if record['family'] == 'A' else 'robustness'),
                   folder=str(folder), config=record['config'])
        runs.append(run)
    native_files = {p.relative_to(inputs['native']).as_posix(): digest(p)
                    for p in sorted(inputs['native'].rglob('*')) if p.is_file()}
    sources = {reference(Path(__file__).parent / n, root)['path']: digest(Path(__file__).parent / n) for n in SOURCES}
    bindings = {'preparation': reference(preparation / 'manifest.json', root),
                'study_report': reference(study_report / 'metadata-hashes.json', root),
                'evaluation_contract': reference(inputs['contract'], root),
                'export': reference(inputs['export'] / 'manifest.json', root),
                'test_docbin': reference(inputs['export'] / 'test.spacy', root),
                'rules': reference(preparation / 'rules-baseline.json', root)}
    state = {'schema_version': SCHEMA, 'state': 'frozen', 'frozen_at': datetime.now().astimezone().isoformat(),
             'recorded_by': 'Codex acting under researcher delegation; user approved both three-seed families',
             'primary': 'original-seed-0', 'exploratory_family': 'A', 'runs': runs, 'bindings': bindings,
             'test_memberships': memberships(inputs['rows']), 'native_model': str(inputs['native']),
             'native_model_files': native_files, 'python': inputs['plan']['python'],
             'python_sha256': digest(Path(inputs['plan']['python'])), 'evaluator_code': sources,
             'candidate_tokenizer_sha256': digest(inputs['export'] / 'tokenizer.bin'),
             'native_tokenizer_sha256': digest(inputs['qualification'] / 'native.tokenizer.bin'),
             'selection_policy': 'Roles fixed from validation; test scores never select a seed/recipe or change training.',
             'test_predictions_performed': False, 'training_performed': False}
    output.mkdir(parents=True)
    write(output / 'manifest.json', state)
    write(output / 'seal.json', {'manifest_sha256': digest(output / 'manifest.json')})
    return state


def verify_freeze(freeze: Path, root: Path) -> tuple[dict, dict]:
    from . import corpus_tokenizer_qualification as q
    freeze = private_existing(freeze, root)
    state = read(freeze / 'manifest.json')
    require(digest(freeze / 'manifest.json') == read(freeze / 'seal.json')['manifest_sha256'], 'frozen manifest changed')
    require(state['schema_version'] == SCHEMA and state['state'] == 'frozen'
            and state['primary'] == 'original-seed-0' and state['exploratory_family'] == 'A'
            and state['test_predictions_performed'] is False and state['training_performed'] is False,
            'fixed frozen experiment required')
    require([(v['family'], v['seed']) for v in state['runs']] == list(ROSTER)
            and [v['name'] for v in state['runs']] == [f'{f}-seed-{s}' for f, s in ROSTER]
            and [v['role'] for v in state['runs']] == ['primary', 'robustness', 'robustness'] + ['exploratory'] * 3,
            'model roster or roles changed')
    for name, sha in state['evaluator_code'].items():
        require(digest(root / name) == sha, 'frozen evaluator changed')
    require(set(state['evaluator_code']) == {reference(Path(__file__).parent / n, root)['path'] for n in SOURCES},
            'incomplete evaluator identity')
    for ref in state['bindings'].values():
        q.verified_reference(ref, root)
    q.bound_manifest(root / state['bindings']['study_report']['path'])
    inputs = load_inputs((root / state['bindings']['preparation']['path']).parent, root)
    require(memberships(inputs['rows']) == state['test_memberships'], 'test membership changed')
    require(Path(state['python']).resolve() == Path(inputs['plan']['python']).resolve()
            and digest(Path(state['python'])) == state['python_sha256'], 'qualified interpreter changed')
    require(Path(state['native_model']).resolve() == inputs['native'].resolve(), 'native model identity changed')
    check_model(inputs['native'], state['native_model_files'])
    for run in state['runs']:
        current = selected_run(private_existing(Path(run['folder']), root), run['seed'])
        require(all(current[k] == run[k] for k in ('model', 'model_files', 'selection', 'run_status_sha256', 'selection_sha256')),
                'frozen selected run changed')
        q.verified_reference(run['config'], root)
    return state, inputs


def check_model(model: Path, files: dict[str, str]) -> None:
    actual = {p.relative_to(model).as_posix(): digest(p) for p in model.rglob('*') if p.is_file()}
    require(actual == files, 'model file set or bytes changed')


def claim_attempt(freeze: Path, output: Path) -> None:
    # Exclusive durable marker intentionally survives any subsequent failure.
    with (freeze / 'attempt.json').open('x', encoding='utf-8') as f:
        json.dump({'attempted_at': datetime.now().astimezone().isoformat(), 'output': str(output),
                   'manifest_sha256': digest(freeze / 'manifest.json'), 'test_exposure': 'possible after this marker'}, f)


def family_statistics(metrics: dict) -> dict:
    result = {}
    for family in ('original', 'A'):
        result[family] = {}
        for profile in ('six_class', 'coarse_loc'):
            vals = [metrics[f'{family}-seed-{s}'][profile]['overall']['f1'] for s in (0, 1, 2)]
            defined = all(v is not None for v in vals)
            result[family][profile] = {'primary_seed': 0, 'primary': vals[0],
                                      'mean': statistics.mean(vals) if defined else None,
                                      'sample_stddev': statistics.stdev(vals) if defined else None,
                                      'min': min(vals) if defined else None, 'max': max(vals) if defined else None}
    return result


def scored_results(rows: list[dict], predictions: dict) -> tuple[dict, dict]:
    validate_rows(rows)
    expected = {f'{f}-seed-{s}' for f, s in ROSTER} | {'rules', 'native'}
    require(set(predictions) == expected, 'all eight fixed systems required')
    truth = {r['record_id']: [(e['start'], e['end'], e['label']) for e in r['entities']] for r in rows}
    languages = {r['record_id']: r['language'] for r in rows}
    metrics, errors = {}, {}
    for name, guesses in predictions.items():
        guesses = checked_predictions(rows, guesses, frozenset({'LOC'}) if name == 'native' else LABELS)
        require(all(len(spans) == len(set(map(tuple, spans))) for spans in guesses.values()), 'duplicate predictions refused')
        metrics[name] = {'coarse_loc': score_spans(coarse(truth), coarse(guesses), languages, frozenset({'LOC'}))}
        target = coarse(truth) if name == 'native' else truth
        # Native errors use coarse LOC; every other system uses strict six-class matching.
        errors[name] = {rid: {'false_positives': sorted(set(map(tuple, guesses[rid])) - set(map(tuple, target[rid]))),
                              'false_negatives': sorted(set(map(tuple, target[rid])) - set(map(tuple, guesses[rid])))} for rid in truth}
        if name != 'native':
            metrics[name]['six_class'] = score_spans(truth, guesses, languages)
    metrics['rules']['unavailable_labels'] = ['LOCAL_AREA']
    return metrics, errors


def evaluate_test(freeze: Path, python: Path, output: Path, root: Path) -> dict:
    from .qualified_export import new_output
    from .rules_baseline import predict_mentions, specification
    output = new_output(root, output)
    state, inputs = verify_freeze(freeze, root)
    require(python.resolve() == Path(state['python']).resolve(), 'same research interpreter required')
    rules = read(root / state['bindings']['rules']['path'])
    require(specification(root) == rules, 'frozen rules changed')
    claim_attempt(freeze, output)
    output.mkdir(parents=True)
    status = {'schema_version': 'lanes-heldout-test-results-v1', 'state': 'failed',
              'started_at': datetime.now().astimezone().isoformat(), 'training_performed': False,
              'partition': 'test', 'test_predictions_performed': False, 'test_exposure': 'possible',
              'freeze': reference(freeze / 'manifest.json', root)}
    try:
        write(output / 'status.json', status)
        rows = inputs['rows']
        request = {k: state[k] for k in ('runs', 'native_model', 'native_model_files', 'native_tokenizer_sha256', 'candidate_tokenizer_sha256')}
        request.update(operation='heldout_test', rows=rows, freeze=str(freeze / 'manifest.json'),
                       freeze_sha256=digest(freeze / 'manifest.json'), test_docbin=str(inputs['export'] / 'test.spacy'),
                       test_docbin_sha256=digest(inputs['export'] / 'test.spacy'),
                       registry=str(Path(__file__).with_name('experiment_registry.py')),
                       registry_sha256=inputs['prep']['implementation_sha256']['experiment_registry.py'])
        write(output / 'request.json', request)
        with patch('sqlalchemy.engine.Engine.connect', side_effect=RuntimeError('database access prohibited')):
            rule_rows = {r['record_id']: predict_mentions(r['text']) for r in rows}
        write(output / 'rules-predictions.json', rule_rows)
        env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH'}}
        env.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                   OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', CUPY_CACHE_DIR=str(output / '.cupy-cache'))
        proc = subprocess.run([str(python), '-B', '-I', '-X', 'utf8', str(Path(__file__).with_name('heldout_test_worker.py')),
                               str(output / 'request.json')], capture_output=True, env=env, cwd=output, timeout=600)
        (output / 'worker.stdout.log').write_bytes(proc.stdout)
        (output / 'worker.stderr.log').write_bytes(proc.stderr)
        require(proc.returncode == 0, 'held-out worker failed; inspect private stderr')
        result = json.loads(proc.stdout.decode('utf-8'))
        require(result['state'] == 'passed' and result['partition'] == 'test'
                and result['training_performed'] is False and result['test_predictions_performed'] is True,
                'test-only worker result required')
        predictions = result['predictions']
        require(set(predictions) == {v['name'] for v in state['runs']} | {'native'}, 'worker roster differs')
        predictions['rules'] = {rid: [(v['start'], v['end'], v['label']) for v in row['spans']] for rid, row in rule_rows.items()}
        write(output / 'predictions.json', {'predictions': predictions, 'native_non_loc_diagnostics': result['native_non_loc_diagnostics']})
        metrics, errors = scored_results(rows, predictions)
        write(output / 'errors.json', {'matching': 'strict six-class except native coarse LOC', 'systems': errors})
        stats = family_statistics(metrics)
        verify_freeze(freeze, root)
        status.update(state='passed', finished_at=datetime.now().astimezone().isoformat(), test_predictions_performed=True,
                      test_exposure='confirmed', samples=60, languages={'english': 30, 'taglish': 30},
                      primary='original-seed-0', metrics=metrics, family_statistics=stats,
                      native_non_loc_diagnostics=result['native_non_loc_diagnostics'],
                      rules_diagnostics=sum(len(v['diagnostics']) for v in rule_rows.values()),
                      interpretation='Same-AI silver-reference agreement; no test-driven model selection or training.')
        write(output / 'status.json', status)
        status['files'] = {p.name: digest(p) for p in output.iterdir() if p.is_file()}
        write(output / 'manifest.json', status)
    except Exception as exc:
        if isinstance(exc, subprocess.TimeoutExpired):
            (output / 'worker.stdout.log').write_bytes(exc.stdout or b'')
            (output / 'worker.stderr.log').write_bytes(exc.stderr or b'')
        status.update(error_type=type(exc).__name__, finished_at=datetime.now().astimezone().isoformat())
        write(output / 'failure.json', status)
        raise ValueError('held-out evaluation failed; preserve diagnostics and attempt marker; do not retry automatically') from None
    return status
