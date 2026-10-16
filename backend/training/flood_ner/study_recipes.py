"""Preregistered bounded recipes; no training occurs without an explicit flag."""
import argparse
from copy import deepcopy
from datetime import datetime
import json
import math
from pathlib import Path
from typing import Any

from .manual_training import ROOT, PREPARATION, digest, validate_inputs, launch

RECIPES = {'recovery': {'patience': 175, 'learning_rate': 0.001},
           'A': {'patience': 350, 'learning_rate': 0.001},
           'B': {'patience': 350, 'learning_rate': 0.0005}}


def variant_config(base: Any, recipe: str, output: Path) -> Any:
    if recipe not in RECIPES:
        raise ValueError('unapproved recipe')
    result = deepcopy(base)
    result['training']['patience'] = RECIPES[recipe]['patience']
    result['training']['optimizer']['learn_rate'] = RECIPES[recipe]['learning_rate']
    result['training']['before_to_disk']['output'] = str(output / 'selected-checkpoint')
    return result


def choose_recipe(scores: dict[str, float]) -> str:
    if set(scores) != {'original', 'A', 'B'} or any(type(v) not in (float, int) or not math.isfinite(v) or not 0 <= v <= 1 for v in scores.values()):
        raise ValueError('three complete finite seed 0 development scores required')
    # Stable order gives original, then A, then B precedence on exact ties.
    return max(('original', 'A', 'B'), key=lambda name: scores[name])


def freeze_study(output: Path, session: Path) -> dict:
    from . import corpus_tokenizer_qualification as q
    from .qualified_export import new_output
    from spacy.util import load_config
    validate_inputs(require_new_output=False)
    output = new_output(ROOT, output)
    session_data = q.read(session)
    output.mkdir(parents=True)
    (output / 'configs').mkdir()
    entries = []
    for recipe in RECIPES:
        for seed in ((2,) if recipe == 'recovery' else (0, 1, 2)):
            destination = output / 'runs' / recipe / ('seed-' + str(seed))
            cfg = variant_config(load_config(PREPARATION / ('train-seed-' + str(seed) + '.cfg')), recipe, destination)
            path = output / 'configs' / (recipe + '-seed-' + str(seed) + '.cfg')
            path.write_text(cfg.to_str(), encoding='utf-8')
            entries.append({'recipe': recipe, 'seed': seed, 'config': path.relative_to(output).as_posix(),
                            'config_sha256': digest(path), 'output': destination.relative_to(output).as_posix()})
    state = {'schema_version': 'lanes-bounded-validation-recipes-v1', 'state': 'preregistered',
             'preparation': str(PREPARATION), 'preparation_sha256': digest(PREPARATION / 'manifest.json'),
             'no_new_training_after': session_data['no_new_training_after'], 'recipes': RECIPES,
             'selection': 'Seed 0 dev strict F1; original wins ties, then A, then B. Robustness only for a strict improvement.',
             'configs': entries, 'test_predictions_permitted': False, 'training_started': False,
             'implementation_sha256': digest(Path(__file__)),
             'files': {p.relative_to(output).as_posix(): digest(p) for p in sorted((output / 'configs').glob('*.cfg'))}}
    (output / 'manifest.json').write_text(json.dumps(state, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    return state


def validate_trial(study: Path, recipe: str, seed: int, require_new_output: bool = True) -> dict:
    from . import corpus_tokenizer_qualification as q
    from .qualified_export import new_output
    from spacy.util import load_config
    q.require(study.resolve().is_relative_to(ROOT / 'backend/training/flood_ner/artifacts'), 'private study required')
    value = q.bound_manifest(study / 'manifest.json')
    q.require(value['schema_version'] == 'lanes-bounded-validation-recipes-v1' and value['recipes'] == RECIPES
              and value['implementation_sha256'] == digest(Path(__file__)) and value['test_predictions_permitted'] is False,
              'preregistered recipe identity changed')
    q.require(type(seed) is int and recipe in RECIPES and seed in ((2,) if recipe == 'recovery' else (0,1,2)), 'invalid recipe/seed')
    q.require(value['preparation_sha256'] == digest(PREPARATION / 'manifest.json'), 'preparation changed')
    if require_new_output:
        q.require(datetime.now().astimezone() < datetime.fromisoformat(value['no_new_training_after']), '50-minute new-training cutoff reached')
    plan = validate_inputs(require_new_output=False, seed=seed)
    entry = next(v for v in value['configs'] if v['recipe'] == recipe and v['seed'] == seed)
    output = (study / entry['output']).resolve()
    q.require(output.is_relative_to(study.resolve()) and not any(p.is_symlink() or getattr(p,'is_junction',lambda:False)() for p in (output,*output.parents)), 'unsafe trial output')
    if require_new_output:
        new_output(ROOT, output)
        for status in study.glob('runs/*/seed-*/run-status.json'):
            q.require(q.read(status).get('state') != 'running', 'a study run is already marked running')
    config = study / entry['config']
    base = load_config(PREPARATION / ('train-seed-' + str(seed) + '.cfg'))
    q.require(load_config(config) == variant_config(base, recipe, output), 'trial changed unapproved settings')
    q.require(digest(config) == entry['config_sha256'], 'trial configuration hash changed')
    plan.update(config=str(config), config_sha256=digest(config), output=str(output), recipe=recipe,
                study_manifest=str(study / 'manifest.json'), study_manifest_sha256=digest(study / 'manifest.json'))
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--recipe', choices=tuple(RECIPES), required=True)
    parser.add_argument('--seed', type=int, choices=(0,1,2), required=True)
    parser.add_argument('--start-training', action='store_true')
    args = parser.parse_args()
    plan = validate_trial(args.study, args.recipe, args.seed)
    if not args.start_training:
        print(json.dumps({'state':'ready','recipe':args.recipe,'seed':args.seed,'training_started':False}))
        return
    raise SystemExit(launch(plan, validator=lambda: validate_trial(args.study,args.recipe,args.seed,require_new_output=False)))


if __name__ == '__main__':
    main()
