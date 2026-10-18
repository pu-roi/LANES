"""Join saved desktop development predictions to qualified laptop languages.

No model loading, inference, training, holdout reading or selection occurs here.
This companion fills the language metadata deliberately absent from DocBins.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner.corrected_experiment_execution import LABELS, digest, write_new
from training.flood_ner.validation_comparison import checked_predictions, score_spans

ROSTER = {'control-seed-0', 'higher_dropout-seed-0', 'lower_learning_rate-seed-0', 'control-seed-1', 'control-seed-2'}


def score_saved(records: list[dict], bundle: dict) -> dict:
    rows = [r for r in records if r['split'] == 'dev']
    if (len(rows) != 60 or len({r['record_id'] for r in rows}) != 60
            or Counter(r['passage_language'] for r in rows) != {'english': 38, 'taglish': 22}
            or set(bundle['runs']) != ROSTER):
        raise ValueError('exact development membership, languages and five-run roster required')
    truth = {r['record_id']: [(e['start'], e['end'], e['label']) for e in r['entities']] for r in rows}
    languages = {r['record_id']: r['passage_language'] for r in rows}
    checked_predictions(rows, truth, frozenset(LABELS))
    scores = {}
    for name, run in bundle['runs'].items():
        guesses = run['predictions']
        checked_predictions(rows, guesses, frozenset(LABELS))
        result = score_spans(truth, guesses, languages)
        if abs(result['overall']['f1'] - run['selected_development_f1']) > 1e-8:
            raise ValueError('saved predictions do not reproduce selected development F1')
        for table in (result['labels'], *result['language_labels'].values()):
            for metric in table.values():
                if metric['reference_spans'] == 0:
                    metric.update(f1=None, recall=None, support_status='unmeasured')
        scores[name] = result
    return scores


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('predictions', 'package', 'development', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--predictions-sha256', required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('new development score destination required')
    if digest(args.predictions) != args.predictions_sha256:
        raise ValueError('authenticate desktop predictions before scoring')
    bundle = json.loads(args.predictions.read_text(encoding='utf-8'))
    qualification_path = args.package / 'qualification.json'
    if digest(qualification_path) != bundle['qualification_sha256']:
        raise ValueError('wrong corrected package qualification')
    qualification = json.loads(qualification_path.read_text(encoding='utf-8'))
    if (qualification['capability'] != 'development' or qualification['counts'] != {'train': 345, 'dev': 60}
            or digest(args.development / 'aggregate-status.json') != digest(qualification_path)):
        raise ValueError('qualified corrected development export required')
    for name in ('admitted-records.jsonl', 'partitions.json', 'dev.spacy'):
        if digest(args.development / name) != qualification['files'][name]:
            raise ValueError('development export bytes changed')
    records = [json.loads(line) for line in (args.development / 'admitted-records.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    result = {'state': 'passed', 'scope': 'development_only_saved_predictions', 'metrics': score_saved(records, bundle),
              'holdout_accessed': False, 'inference_performed': False, 'training_performed': False,
              'selection_changed': False, 'predictions_sha256': args.predictions_sha256}
    write_new(args.output, result)
    print(json.dumps({'state': 'passed', 'runs': 5, 'holdout_accessed': False, 'inference_performed': False}))


if __name__ == '__main__':
    main()
