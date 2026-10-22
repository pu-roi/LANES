"""CPU loading and development scoring of already selected checkpoints only."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner.corrected_experiment_execution import LABELS, digest, tree, write_new


def cpu_runtime() -> list:
    """Keep existing interpreter-local DLL handles alive; CPU needs no CUDA install."""
    handles = []
    if sys.platform == 'win32':
        site = Path(sys.prefix) / 'Lib/site-packages'
        for relative in ('torch/lib', 'nvidia/cuda_runtime/bin', 'nvidia/cuda_nvrtc/bin'):
            path = site / relative
            if path.is_dir():
                handles.append(os.add_dll_directory(str(path)))
    return handles


def load_model(root: Path, checkpoint: Path, package: Path, resources: Path, output: Path):
    handles = cpu_runtime()
    import torch
    import spacy
    if sys.version_info[:2] != (3, 11) or spacy.__version__ != '3.7.5':
        raise ValueError('existing qualified Python 3.11/spaCy 3.7.5 required')
    spacy.require_cpu()
    torch.set_num_threads(2)
    registry = root / 'backend/training/flood_ner/experiment_registry.py'
    spec = importlib.util.spec_from_file_location('lanes_corrected_registry', registry)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    contract = json.loads((package / 'model-contract.json').read_text())
    contract['model_dir'] = str(resources)
    write_new(output / 'runtime-model-contract.json', contract)
    contract_path = output / 'runtime-model-contract.json'
    nlp = spacy.load(checkpoint, config={'nlp': {'tokenizer': {
        'model_manifest': str(contract_path), 'manifest_sha256': digest(contract_path),
        'tokenizer_file': str(package / 'tokenizer.bin')}}})
    if nlp.pipe_names != ['ner'] or set(nlp.get_pipe('ner').labels) != LABELS:
        raise ValueError('loadable six-label NER pipeline required')
    if nlp.tokenizer.to_bytes(exclude=['vocab']) != (package / 'tokenizer.bin').read_bytes():
        raise ValueError('loaded tokenizer differs from frozen bytes')
    return nlp, handles


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('checkout', 'model', 'package', 'resources', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir()
    before = tree(args.model)
    nlp, handles = load_model(args.checkout, args.model, args.package, args.resources, args.output)
    from spacy.tokens import DocBin
    from training.flood_ner.validation_comparison import score_spans, checked_predictions
    from training.flood_ner.validation_worker import infer_raw
    docs = list(DocBin().from_disk(args.package / 'dev.spacy').get_docs(nlp.vocab))
    rows = [{'record_id': d.user_data['record_id'], 'text': d.text} for d in docs]
    if len(rows) != 60 or len({r['record_id'] for r in rows}) != 60:
        raise ValueError('exact sixty development records required')
    truth = {d.user_data['record_id']: [(e.start_char, e.end_char, e.label_) for e in d.ents] for d in docs}
    predictions, _ = infer_raw(nlp, rows, False)
    checked_predictions(rows, predictions, frozenset(LABELS))
    scored = score_spans(truth, predictions, {r['record_id']: 'english' for r in rows})
    # DocBins deliberately carry IDs only. Never invent operational languages.
    metrics = {k: scored[k] for k in ('overall', 'labels')}
    metrics['language_metrics'] = 'pending laptop development-only partition metadata; not present in trainer delivery'
    write_new(args.output / 'metrics.json', metrics)
    write_new(args.output / 'predictions.json', predictions)
    if before != tree(args.model):
        raise ValueError('checkpoint files changed during loading')
    write_new(args.output / 'status.json', {'state': 'passed', 'device': 'cpu', 'records': 60,
              'labels': sorted(LABELS), 'holdout_accessed': False, 'training_started': False})
    print(json.dumps({'state': 'passed', 'overall': metrics['overall']}))


if __name__ == '__main__':
    main()
