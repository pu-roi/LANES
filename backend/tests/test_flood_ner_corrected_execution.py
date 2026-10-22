from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from training.flood_ner.corrected_experiment_execution import (LABELS, check_selection, stopping_reason, summarize)
from training.flood_ner.successor_experiment_preparation import schedule


def outcome(variant, seed, f1):
    return {'variant': variant, 'seed': seed, 'state': 'completed', 'f1': f1}


def test_five_run_control_and_tie():
    rows = [outcome('control', 0, .7), outcome('higher_dropout', 0, .7 + 5e-13),
            outcome('lower_learning_rate', 0, .6), outcome('control', 1, .6), outcome('control', 2, .8)]
    result = summarize(rows)
    assert result['schedule']['retained'] == 'control'
    assert result['schedule']['completed_runs'] == 5
    assert result['families']['control']['mean'] == pytest.approx(.7)
    assert result['families']['control']['sample_stddev'] == pytest.approx(.1)


@pytest.mark.parametrize('confirmation,retained', [(.8, 'higher_dropout'), (.5, 'control'), (.64, 'control')])
def test_seven_runs_and_strict_retention(confirmation, retained):
    rows = [outcome('control', 0, .7), outcome('higher_dropout', 0, .8), outcome('lower_learning_rate', 0, .6),
            outcome('control', 1, .7), outcome('control', 2, .7),
            outcome('higher_dropout', 1, confirmation), outcome('higher_dropout', 2, confirmation)]
    assert schedule(rows)['retained'] == retained


def test_equal_mean_retains_control_with_exact_binary_scores():
    rows = [outcome('control', 0, .5), outcome('higher_dropout', 0, .75), outcome('lower_learning_rate', 0, .25),
            outcome('control', 1, .5), outcome('control', 2, .5),
            outcome('higher_dropout', 1, .375), outcome('higher_dropout', 2, .375)]
    assert schedule(rows)['retained'] == 'control'


def test_failure_stops_and_wrong_order_rejected():
    assert schedule([{'variant': 'control', 'seed': 0, 'state': 'failed', 'f1': None}])['next'] is None
    with pytest.raises(ValueError):
        schedule([outcome('higher_dropout', 0, .8)])


@pytest.mark.parametrize('bad', [float('nan'), float('inf'), -.1, 1.1, None])
def test_invalid_checkpoint_metrics(bad):
    selection = {'partition': 'dev', 'tie_break': 'earlier checkpoint step', 'step': 35, 'score': bad}
    meta = {'labels': {'ner': sorted(LABELS)}, 'pipeline': ['ner'], 'performance': {'ents_f': bad, 'ents_p': .7, 'ents_r': .7}}
    with pytest.raises(ValueError):
        check_selection(selection, meta)


def test_valid_selection_and_missing_label():
    selection = {'partition': 'dev', 'tie_break': 'earlier checkpoint step', 'step': 35, 'score': .7}
    meta = {'labels': {'ner': sorted(LABELS)}, 'pipeline': ['ner'], 'performance': {'ents_f': .7, 'ents_p': .7, 'ents_r': .7}}
    assert check_selection(selection, meta)['selected_step'] == 35
    meta['labels']['ner'].pop()
    with pytest.raises(ValueError):
        check_selection(selection, meta)


def test_stopping_reason_avoids_claim_from_missing_metadata():
    assert 'unavailable' in stopping_reason('', {})
    assert '1000' in stopping_reason('', {'lanes_training_step': 999})


def test_spacy_serialized_metadata_rounding_keeps_full_precision_selection():
    score = 0.7160493827160493
    selection = {'partition': 'dev', 'tie_break': 'earlier checkpoint step', 'step': 945, 'score': score}
    meta = {'labels': {'ner': sorted(LABELS)}, 'pipeline': ['ner'],
            'performance': {'ents_f': round(score, 10), 'ents_p': .75, 'ents_r': .68}}
    assert check_selection(selection, meta)['f1'] == score
    meta['performance']['ents_f'] += .00001
    with pytest.raises(ValueError):
        check_selection(selection, meta)


def test_continuation_cannot_turn_a_failed_training_run_into_a_retry(tmp_path):
    import json
    from training.flood_ner.corrected_experiment_execution import run
    prefix = tmp_path / 'prefix.json'
    prefix.write_text(json.dumps({'reason': 'training_failure', 'outcomes': []}))
    with pytest.raises(ValueError, match='independently validated'):
        run(tmp_path, tmp_path, prefix)
