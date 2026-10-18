import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner.corrected_development_language_scores import ROSTER, score_saved


def data():
    rows = [{'record_id': str(i), 'text': 'Bañga', 'split': 'dev',
             'passage_language': 'english' if i < 38 else 'taglish',
             'entities': [{'start': 0, 'end': 5, 'label': 'CITY'}]} for i in range(60)]
    guesses = {str(i): [(0, 5, 'CITY')] for i in range(60)}
    return rows, {'runs': {name: {'predictions': copy.deepcopy(guesses), 'selected_development_f1': 1.0} for name in ROSTER}}


def test_saved_predictions_score_all_five_without_inference():
    rows, bundle = data()
    result = score_saved(rows, bundle)
    assert len(result) == 5
    assert result['control-seed-0']['languages']['taglish']['passages'] == 22
    assert result['control-seed-0']['language_labels']['taglish']['ROAD']['f1'] is None


@pytest.mark.parametrize('kind', ['missing_id', 'wrong_language', 'wrong_roster', 'wrong_score', 'invalid_offset'])
def test_inconsistent_development_join_refused(kind):
    rows, bundle = data()
    if kind == 'missing_id': rows[0]['record_id'] = 'absent'
    if kind == 'wrong_language': rows[0]['passage_language'] = 'taglish'
    if kind == 'wrong_roster': bundle['runs'].pop('control-seed-2')
    if kind == 'wrong_score': bundle['runs']['control-seed-0']['selected_development_f1'] = .5
    if kind == 'invalid_offset': bundle['runs']['control-seed-0']['predictions']['0'] = [(0, 6, 'CITY')]
    with pytest.raises(ValueError):
        score_saved(rows, bundle)
