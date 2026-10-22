"""CPU score selected v21 checkpoints on frozen train/dev raw text only."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner import regularization_experiment as protocol
from training.flood_ner.corrected_experiment_execution import tree
from training.flood_ner.corrected_experiment_worker import load_model
from training.flood_ner.development_error_audit import checked_spans, read, require, score_partition, write_new
from training.flood_ner.regularization_experiment_execution import EXPERIMENT_SHA
from training.flood_ner.validation_comparison import checked_predictions
from training.flood_ner.validation_worker import infer_raw


def join_documents(documents, metadata, partition):
    require(partition in ('train', 'dev'), 'train/dev only')
    expected = {r['record_id']: r for r in metadata if r['partition'] == partition}
    require(len(documents) == len(expected) == protocol.COUNTS[partition], 'wrong development membership count')
    rows, references, languages = [], {}, {}
    for doc in documents:
        rid = doc.user_data.get('record_id')
        require(rid in expected and rid not in references, 'wrong/duplicate development identity')
        item = expected[rid]
        require(hashlib.sha256(doc.text.encode('utf-8')).hexdigest() == item['passage_sha256'],
                'development text hash differs')
        spans = [(e.start_char, e.end_char, e.label_) for e in doc.ents]
        checked_spans(spans, doc.text)
        require(item['is_negative'] == (len(spans) == 0), 'negative reference differs')
        rows.append({'record_id': rid, 'text': doc.text})
        references[rid], languages[rid] = spans, item['language']
    require(set(references) == set(expected), 'missing development identities')
    return rows, references, languages


def score_documents(nlp, documents, metadata, partition):
    rows, truth, languages = join_documents(documents, metadata, partition)
    guesses, _ = infer_raw(nlp, rows, False)
    checked_predictions(rows, guesses, protocol.LABELS)
    for row in rows:
        checked_spans(guesses[row['record_id']], row['text'])
    return protocol.checked_score(score_partition(truth, guesses, languages)), guesses


def gaps(train, dev):
    def difference(a, b):
        return {k: a[k] - b[k] if a[k] is not None and b[k] is not None else None
                for k in ('precision', 'recall', 'f1')}
    return {'overall': difference(train['overall'], dev['overall']),
            'labels': {label: difference(train['labels'][label], dev['labels'][label]) for label in protocol.LABELS},
            'languages': {lang: difference(train['languages'][lang], dev['languages'][lang]) for lang in ('english', 'taglish')},
            'language_labels': {lang: {label: difference(train['language_labels'][lang][label],
                dev['language_labels'][lang][label]) for label in protocol.LABELS} for lang in ('english', 'taglish')}}


def run(root, bundle, model, resources, output):
    protocol.verify_portable(root, bundle, resources, EXPERIMENT_SHA)
    require(model.is_dir() and not output.exists(), 'existing selected checkpoint and new scoring destination required')
    before = tree(model)
    require(bool(before), 'selected checkpoint is empty')
    output.mkdir()
    try:
        nlp, dll_handles = load_model(root, model, bundle / 'package', resources, output)
        from spacy.tokens import DocBin
        metadata = protocol.validate_slices(read(bundle / 'development-slices.json'))
        metrics, predictions = {}, {}
        for partition in ('dev', 'train'):
            documents = list(DocBin().from_disk(bundle / 'package' / f'{partition}.spacy').get_docs(nlp.vocab))
            metrics[partition], predictions[partition] = score_documents(nlp, documents, metadata, partition)
        require(before == tree(model), 'selected checkpoint changed during CPU loading/scoring')
        protocol.verify_portable(root, bundle, resources, EXPERIMENT_SHA)
        write_new(output / 'metrics.json', metrics)
        write_new(output / 'predictions.json', predictions)
        write_new(output / 'train-validation-gaps.json', gaps(metrics['train'], metrics['dev']))
        write_new(output / 'status.json', {'state': 'passed', 'device': 'cpu', 'counts': protocol.COUNTS,
                  'checkpoint_unchanged': True, 'raw_text_inference': True, 'holdout_accessed': False,
                  'training_started': False})
    except BaseException as exc:
        write_new(output / 'failure.json', {'error': str(exc), 'holdout_accessed': False})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('checkout', 'bundle', 'model', 'resources', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    run(args.checkout.resolve(), args.bundle.resolve(), args.model.resolve(), args.resources.resolve(), args.output.resolve())
