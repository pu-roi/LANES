"""Offline validation-only comparisons; original experiment inputs are immutable."""
from collections import Counter
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

LABELS = frozenset({'ROAD', 'LANDMARK', 'LOCAL_AREA', 'BARANGAY', 'CITY', 'PROVINCE'})


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value: Any, message: str) -> None:
    if not value:
        raise ValueError(message)


def score_spans(truth: dict, guesses: dict, languages: dict, labels: frozenset = LABELS) -> dict:
    require(bool(truth) and set(truth) == set(guesses) == set(languages), 'identical nonempty record identities required')
    require(all(v in {'english', 'taglish'} for v in languages.values()), 'frozen languages required')
    def checked(rows: dict) -> dict:
        out = {}
        for rid, values in rows.items():
            spans = []
            for v in values:
                require(isinstance(v, (list, tuple)) and len(v) == 3 and type(v[0]) is int
                        and type(v[1]) is int and 0 <= v[0] < v[1] and v[2] in labels,
                        'valid in-profile character spans required')
                spans.append(tuple(v))
            require(len(spans) == len(set(spans)), 'duplicate spans refused')
            out[rid] = set(spans)
        return out
    references, predictions = checked(truth), checked(guesses)
    def metrics(ids: list, label: str | None = None) -> dict:
        ref = {(rid, *v) for rid in ids for v in references[rid] if label is None or v[2] == label}
        pred = {(rid, *v) for rid in ids for v in predictions[rid] if label is None or v[2] == label}
        tp, fp, fn = len(ref & pred), len(pred-ref), len(ref-pred)
        return {'TP': tp, 'FP': fp, 'FN': fn, 'reference_spans': len(ref), 'predicted_spans': len(pred),
                'passages': len(ids), 'precision': tp/(tp+fp) if tp+fp else None,
                'recall': tp/(tp+fn) if tp+fn else None, 'f1': 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}
    def negatives(ids: list) -> dict:
        ids = [rid for rid in ids if not references[rid]]
        fp = sum(bool(predictions[rid]) for rid in ids)
        return {'negative_passages': len(ids), 'false_positive_passages': fp, 'rate': fp/len(ids) if ids else None}
    ids = sorted(truth)
    by_lang = {lang: [rid for rid in ids if languages[rid] == lang] for lang in ('english', 'taglish')}
    return {'overall': metrics(ids), 'labels': {label: metrics(ids, label) for label in sorted(labels)},
            'languages': {lang: metrics(rows) for lang, rows in by_lang.items()},
            'language_labels': {lang: {label: metrics(rows, label) for label in sorted(labels)} for lang, rows in by_lang.items()},
            'negative_passages': {'overall': negatives(ids), **{lang: negatives(rows) for lang, rows in by_lang.items()}}}


def coarse(rows: dict) -> dict:
    # Collapse labels without merging adjacent entities. Duplicate boundaries from
    # conflicting rule types describe one coarse prediction, not extra entities.
    return {rid: sorted({(a, z, 'LOC') for a, z, label in spans}) for rid, spans in rows.items()}


def checked_predictions(rows: list, guesses: dict, labels: frozenset) -> dict:
    expected = {r['record_id']: r for r in rows}
    require(len(expected) == len(rows) and set(guesses) == set(expected), 'omitted/duplicate/moved prediction identities')
    for rid, spans in guesses.items():
        text = expected[rid]['text']
        for v in spans:
            require(len(v) == 3 and type(v[0]) is int and type(v[1]) is int
                    and 0 <= v[0] < v[1] <= len(text) and v[2] in labels, 'prediction offset or label invalid')
    return guesses


def selected_run(folder: Path, seed: int) -> dict:
    status = json.loads((folder / 'run-status.json').read_text(encoding='utf-8'))
    require(status.get('state') == 'completed' and status.get('training_completed') is True
            and status.get('exit_code') == 0 and status.get('seed') == seed
            and status.get('test_predictions_performed') is False, 'completed scoped training run required')
    selection = json.loads((folder / 'selected-checkpoint/selection.json').read_text(encoding='utf-8'))
    require(selection == status['selection'] and selection.get('partition') == 'dev'
            and selection.get('tie_break') == 'earlier checkpoint step', 'selection/status mismatch')
    model = folder / 'selected-checkpoint/model'
    require((model / 'meta.json').is_file(), 'selected model missing')
    return {'name': 'seed-' + str(seed), 'seed': seed, 'model': str(model), 'selection': selection,
            'model_files': {p.relative_to(model).as_posix(): digest(p) for p in sorted(model.rglob('*')) if p.is_file()},
            'run_status_sha256': digest(folder / 'run-status.json'),
            'selection_sha256': digest(folder / 'selected-checkpoint/selection.json')}


def compare_validation(python: Path, preparation: Path, training_root: Path, output: Path,
                       root: Path, seeds: list[int] | None = None, allow_incomplete: bool = False) -> dict:
    from . import corpus_tokenizer_qualification as q
    from .manual_training import validate_inputs
    from .qualified_export import new_output, passed_package
    from .rules_baseline import predict_mentions, specification
    from unittest.mock import patch

    seeds = [0, 1, 2] if seeds is None else seeds
    require(bool(seeds) and len(set(seeds)) == len(seeds) and all(type(s) is int and s in (0, 1, 2) for s in seeds), 'frozen seed identities required')
    output = new_output(root, output)
    plan = validate_inputs(root, preparation, require_new_output=False)
    require(python.resolve() == Path(plan['python']).resolve(), 'same qualified interpreter required')
    manifest = q.bound_manifest(preparation / 'manifest.json')
    export = q.verified_reference(manifest['export'], root).parent
    qualification = q.verified_reference(manifest['qualification'], root).parent
    _, paths = passed_package(qualification, root)
    cases, _, _ = q.inputs(paths['cohort'].parent, paths['context'].parent, paths['admission_package'], root)
    rows = [c for c in cases if c.get('kind') == 'location' and c['split'] == 'dev']
    require(len(rows) == 60 and Counter(r['language'] for r in rows) == {'english': 30, 'taglish': 30}, '60 frozen validation passages required')
    runs, missing = [], []
    for seed in seeds:
        folder = training_root / ('seed-' + str(seed))
        try:
            run = selected_run(folder, seed)
            launch = q.read(folder / 'launch-request.json')
            if 'recipe' in launch:
                from .study_recipes import validate_trial
                study_manifest = Path(launch['study_manifest'])
                require(digest(study_manifest) == launch['study_manifest_sha256'], 'trial study identity changed')
                expected = validate_trial(study_manifest.parent, launch['recipe'], seed, require_new_output=False)
                require(launch['config_sha256'] == expected['config_sha256']
                        and folder.resolve() == Path(expected['output']), 'trial configuration/output differs')
            else:
                require(launch['config_sha256'] == manifest['files']['train-seed-' + str(seed) + '.cfg'],
                        'frozen training configuration differs')
            require(launch['preparation_sha256'] == digest(preparation / 'manifest.json'), 'training preparation binding differs')
            runs.append(run)
        except (OSError, ValueError, KeyError) as exc:
            if not allow_incomplete:
                raise
            missing.append({'seed': seed, 'reason': str(exc)})
    require(bool(runs), 'at least one completed model required')
    _, native_model = q.verify_model(paths['model_manifest'], root / 'backend/training/flood_ner/artifacts')
    rules = specification(root)
    require(rules == q.read(preparation / 'rules-baseline.json'), 'rules baseline changed')
    request = {'operation': 'validation_only', 'rows': rows, 'runs': runs,
               'native_model': str(native_model), 'native_tokenizer_sha256': digest(qualification / 'native.tokenizer.bin'),
               'candidate_tokenizer_sha256': digest(export / 'tokenizer.bin'),
               'dev_docbin': str(export / 'dev.spacy'), 'dev_docbin_sha256': digest(export / 'dev.spacy'),
               'registry': str(Path(__file__).with_name('experiment_registry.py')),
               'registry_sha256': manifest['implementation_sha256']['experiment_registry.py']}
    output.mkdir(parents=True)
    state = {'schema_version': 'lanes-validation-comparison-v1', 'state': 'failed',
             'partition': 'dev', 'test_predictions_performed': False, 'training_performed': False}
    try:
        (output / 'request.json').write_text(json.dumps(request, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        with patch('sqlalchemy.engine.Engine.connect', side_effect=RuntimeError('database connection prohibited')):
            rule_rows = {r['record_id']: predict_mentions(r['text']) for r in rows}
        rule_predictions = {rid: [(s['start'], s['end'], s['label']) for s in value['spans']] for rid, value in rule_rows.items()}
        checked_predictions(rows, rule_predictions, LABELS)
        (output / 'rules-predictions.json').write_text(json.dumps(rule_rows, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH'}}
        env.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', CUPY_CACHE_DIR=str(output / '.cupy-cache'))
        proc = subprocess.run([str(python), '-B', '-I', '-X', 'utf8', str(Path(__file__).with_name('validation_worker.py')), str(output / 'request.json')],
                              capture_output=True, env=env, cwd=output, timeout=600)
        (output / 'worker.stdout.log').write_bytes(proc.stdout)
        (output / 'worker.stderr.log').write_bytes(proc.stderr)
        require(proc.returncode == 0, 'validation worker failed; preserve worker.stderr.log')
        result = json.loads(proc.stdout.decode('utf-8'))
        require(result['state'] == 'passed' and result['partition'] == 'dev'
                and result['test_predictions_performed'] is False and result['training_performed'] is False,
                'validation-only worker required')
        truth = {r['record_id']: [(e['start'], e['end'], e['label']) for e in r['entities']] for r in rows}
        languages = {r['record_id']: r['language'] for r in rows}
        metrics = {'rules': {'six_class': score_spans(truth, rule_predictions, languages),
                             'coarse_loc': score_spans(coarse(truth), coarse(rule_predictions), languages, frozenset({'LOC'})),
                             'unavailable_labels': ['LOCAL_AREA'], 'diagnostics': sum(len(v['diagnostics']) for v in rule_rows.values())}}
        require(set(result['predictions']) == {v['name'] for v in runs} | {'native'}, 'worker model identities differ')
        for name, predictions in result['predictions'].items():
            predictions = checked_predictions(rows, predictions, frozenset({'LOC'}) if name == 'native' else LABELS)
            metrics[name] = {'coarse_loc': score_spans(coarse(truth), coarse(predictions), languages, frozenset({'LOC'}))}
            if name != 'native':
                exact = score_spans(truth, predictions, languages)
                selected = next(v['selection'] for v in runs if v['name'] == name)
                require(abs(exact['overall']['f1'] - selected['score']) < 1e-12, 'reloaded model does not reproduce selected F1')
                metrics[name]['six_class'] = exact
        (output / 'predictions.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        for run in runs:
            for name, h in run['model_files'].items():
                require(digest(Path(run['model']) / name) == h, 'selected model changed during evaluation')
        validate_inputs(root, preparation, require_new_output=False)
        state.update(state='partial' if missing else 'passed', recorded_at=datetime.now().astimezone().isoformat(),
                     samples=60, languages=dict(Counter(languages.values())), metrics=metrics, missing_runs=missing,
                     primary_seed=0, selected_runs=runs, native_non_loc_diagnostics=result['native_non_loc_diagnostics'],
                     interpretation='Same-AI silver-reference validation agreement; not independent gold accuracy.',
                     preparation={'path': str(preparation), 'sha256': digest(preparation / 'manifest.json')},
                     implementation_sha256={p.name: digest(p) for p in [Path(__file__), Path(__file__).with_name('validation_worker.py')]})
        state['files'] = {p.name: digest(p) for p in output.iterdir() if p.is_file()}
        (output / 'manifest.json').write_text(json.dumps(state, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    except Exception as exc:
        if isinstance(exc, subprocess.TimeoutExpired):
            (output / 'worker.stdout.log').write_bytes(exc.stdout or b'')
            (output / 'worker.stderr.log').write_bytes(exc.stderr or b'')
        state['error_type'] = type(exc).__name__
        (output / 'failure.json').write_text(json.dumps(state, indent=2)+'\n', encoding='utf-8')
        raise ValueError('comparison failed; private diagnostics retained in '+str(output)) from None
    return state
