"""Frozen silver-reference evaluation protocol; no inference or training."""
from __future__ import annotations

from ..annotation.schema import PLACE_LABELS


def evaluation_contract(bindings: dict, tokenizer: dict, qualification: dict) -> dict:
    return {
        'schema_version': 'lanes-ner-evaluation-contract-v1',
        'state': 'frozen' if qualification['state'] == 'passed' else 'protocol_frozen_tokenizer_qualification_pending',
        'input_bindings': bindings, 'tokenizer': tokenizer, 'qualification': qualification,
        'labels': sorted(PLACE_LABELS),
        'partitions': {'train': {'english': 140, 'taglish': 140},
                       'dev': {'english': 30, 'taglish': 30}, 'test': {'english': 30, 'taglish': 30}},
        'sample_count': 400, 'contextual_pairs': 40,
        'matching': ['record_id', 'start', 'end', 'label'],
        'metrics': {
            'counts': ['TP', 'FP', 'FN', 'reference_spans', 'predicted_spans', 'passages'],
            'slices': ['overall', 'label', 'language', 'language_and_label'],
            'precision': 'TP/(TP+FP); null when denominator is zero',
            'recall': 'TP/(TP+FN); null when denominator is zero',
            'f1': '2*TP/(2*TP+FP+FN); null when denominator is zero',
            'aggregation': 'micro counts; no token-accuracy substitute',
            'negative_passage_false_positive_rate': 'negative passages with >=1 in-profile prediction / negative passages; null when none',
            'negative_support': 'Report negative passage count and false-positive passage count overall and by language',
        },
        'pretrained_comparison': {
            'reference': 'Collapse all six location classes to LOC, without merging adjacent entities',
            'prediction': 'Use pretrained LOC predictions only; ORG/PER remain separate diagnostics',
            'metric': 'Exact record/start/end matching in the separate coarse LOC task',
            'six_class_accuracy_claim': False, 'no_reference_driven_prediction_relabeling': True,
        },
        'rules_baseline': {
            'state': 'mapping_required_before_comparison',
            'requirements': ['Freeze extractor code/configuration hashes',
                'Document each emitted type to six-class label mapping and original character-offset convention',
                'Validate source-exact offsets; preserve unresolved/unsupported types separately',
                'Never infer a missing rule label or offset from reference annotations'],
        },
        'model_selection': {
            'partition': 'dev', 'metric': 'strict six-class micro F1', 'tie_break': 'earlier checkpoint step',
            'primary_seed': 0, 'robustness_seeds': [1, 2],
            'configuration_policy': 'Freeze configuration identities before training; select using development results only',
            'test_policy': 'No test predictions, metrics or errors for tuning; final selected experiment only after configurations/checkpoints are frozen',
            'test_boundary_audit': 'Deterministic token-boundary inspection is permitted here; it is not NER test evaluation',
        },
        'interpretation': 'Agreement with same-AI-reviewed silver references; not independently verified accuracy or human gold labels',
        'contextual_evaluation': 'All 40 pairs are training references, not a held-out contextual benchmark; depth/time diagnostics do not score contextual accuracy',
        'production_acceptance': 'Existing roadmap targets remain proposals pending baseline measurement; this protocol grants no production readiness',
        'source_use_scope': 'private_owner_only_academic_training_evaluation',
        'model_predictions_performed': False, 'exports': 0, 'training_performed': False,
    }


def score_exact_spans(references: dict, predictions: dict, languages: dict) -> dict:
    """Score already supplied spans, including empty records and undefined slices.

    Values are (start, end, label) triples. This helper runs no extractor and must
    not be called on held-out model results before the frozen contract allows it.
    """
    if set(references) != set(predictions) or set(references) != set(languages) or not references:
        raise ValueError('identical nonempty record identities required, including negative passages')
    if any(v not in {'english', 'taglish'} for v in languages.values()):
        raise ValueError('English/Taglish record language required')
    def checked(rows):
        result = {}
        for rid, values in rows.items():
            spans = []
            for value in values:
                if (not isinstance(value, (tuple, list)) or len(value) != 3
                    or type(value[0]) is not int or type(value[1]) is not int
                    or not 0 <= value[0] < value[1] or value[2] not in PLACE_LABELS):
                    raise ValueError('valid six-class character spans required')
                spans.append(tuple(value))
            if len(set(spans)) != len(spans):
                raise ValueError('duplicate prediction/reference spans forbidden')
            result[rid] = set(spans)
        return result
    ref, pred = checked(references), checked(predictions)
    def metrics(ids, label=None):
        truth = {(rid, *s) for rid in ids for s in ref[rid] if label is None or s[2] == label}
        guess = {(rid, *s) for rid in ids for s in pred[rid] if label is None or s[2] == label}
        tp, fp, fn = len(truth & guess), len(guess - truth), len(truth - guess)
        return {'TP': tp, 'FP': fp, 'FN': fn, 'reference_spans': len(truth), 'predicted_spans': len(guess),
            'passages': len(ids), 'precision': tp / (tp + fp) if tp + fp else None,
            'recall': tp / (tp + fn) if tp + fn else None,
            'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}
    def negative(ids):
        selected = [rid for rid in ids if not ref[rid]]
        false = sum(bool(pred[rid]) for rid in selected)
        return {'negative_passages': len(selected), 'false_positive_passages': false,
            'rate': false / len(selected) if selected else None}
    ids = sorted(ref)
    by_language = {language: [rid for rid in ids if languages[rid] == language] for language in ('english', 'taglish')}
    return {'overall': metrics(ids), 'labels': {label: metrics(ids, label) for label in sorted(PLACE_LABELS)},
        'languages': {lang: metrics(selected) for lang, selected in by_language.items()},
        'language_labels': {lang: {label: metrics(selected, label) for label in sorted(PLACE_LABELS)} for lang, selected in by_language.items()},
        'negative_passages': {'overall': negative(ids), **{lang: negative(selected) for lang, selected in by_language.items()}}}
