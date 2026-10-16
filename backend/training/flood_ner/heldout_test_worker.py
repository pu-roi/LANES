"""Isolated, frozen-roster GPU inference for the held-out test evaluation."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate_request(request: dict) -> dict:
    if request.get('operation') != 'heldout_test':
        raise ValueError('held-out test operation required')
    frozen = Path(request['freeze'])
    if digest(frozen) != request['freeze_sha256']:
        raise ValueError('freeze identity changed')
    state = json.loads(frozen.read_text(encoding='utf-8'))
    rows = request['rows']
    if (len(rows) != len({r['record_id'] for r in rows}) or len(rows) != 60
            or any(r['kind'] != 'location' or r['split'] != 'test' for r in rows)
            or Counter(r['language'] for r in rows) != {'english': 30, 'taglish': 30}):
        raise ValueError('60 test-only location passages required')
    for key in ('runs', 'native_model', 'native_model_files', 'candidate_tokenizer_sha256', 'native_tokenizer_sha256'):
        if request[key] != state[key]:
            raise ValueError('worker roster/model/tokenizer differs from freeze')
    members = [{k: v[k] for k in ('record_id', 'kind', 'split', 'language', 'text_sha256')} |
               {'entities_sha256': hashlib.sha256(json.dumps(v['entities'], sort_keys=True).encode('utf-8')).hexdigest()}
               for v in rows]
    if members != state['test_memberships']:
        raise ValueError('worker test memberships differ from freeze')
    root = Path(__file__).resolve().parents[3]
    for name, expected in state['evaluator_code'].items():
        if digest(root / name) != expected:
            raise ValueError('frozen evaluator bytes changed')
    if (Path(request['test_docbin']).name != 'test.spacy' or digest(Path(request['test_docbin'])) != request['test_docbin_sha256']
            or request['test_docbin_sha256'] != state['bindings']['test_docbin']['sha256']
            or digest(Path(request['registry'])) != request['registry_sha256']):
        raise ValueError('test DocBin or registry changed')
    return state


def main() -> None:
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    if sys.version_info[:2] != (3, 11):
        raise ValueError('qualified Python 3.11 required')
    state = validate_request(request)
    rows = request['rows']
    site = Path(sys.prefix) / 'Lib/site-packages'
    handles = [os.add_dll_directory(str(p)) for p in
               (site / 'torch/lib', site / 'nvidia/cuda_runtime/bin', site / 'nvidia/cuda_nvrtc/bin') if p.is_dir()]
    os.environ['CUDA_PATH'] = str(site / 'nvidia/cuda_runtime')
    import spacy
    import torch
    import cupy
    from spacy.vocab import Vocab
    from spacy.tokens import DocBin
    if spacy.__version__ != '3.7.5' or not torch.cuda.is_available() or not spacy.require_gpu(0):
        raise ValueError('qualified GPU required; no CPU fallback')
    torch.set_num_threads(2)
    registry = load_module('lanes_experiment_registry', Path(request['registry']))
    raw = load_module('lanes_test_raw_inference', Path(__file__).with_name('validation_worker.py'))
    vocab = Vocab().from_disk(Path(request['native_model']) / 'vocab')
    docs = list(DocBin().from_disk(request['test_docbin']).get_docs(vocab))
    refs = {d.user_data['record_id']: d for d in docs}
    if len(refs) != len(docs) or set(refs) != {r['record_id'] for r in rows}:
        raise ValueError('test DocBin memberships differ')
    for row in rows:
        doc = refs[row['record_id']]
        if (doc.text != row['text'] or hashlib.sha256(doc.text.encode('utf-8')).hexdigest() != row['text_sha256']
                or [(e.start_char, e.end_char, e.label_) for e in doc.ents] != [(e['start'], e['end'], e['label']) for e in row['entities']]):
            raise ValueError('test text/annotation identity differs')
    predictions, diagnostics = {}, Counter()
    for run in state['runs'] + [{'name': 'native', 'model': state['native_model'], 'model_files': state['native_model_files']}]:
        model = Path(run['model'])
        if {p.relative_to(model).as_posix(): digest(p) for p in model.rglob('*') if p.is_file()} != run['model_files']:
            raise ValueError('frozen model bytes changed')
        native = run['name'] == 'native'
        nlp = spacy.load(model, exclude=['tok2vec', 'tagger', 'morphologizer', 'parser'] if native else [])
        if set(nlp.get_pipe('ner').labels) != ({'LOC', 'ORG', 'PER'} if native else set(registry.LABELS)):
            raise ValueError('frozen label profile changed')
        expected = state['native_tokenizer_sha256'] if native else state['candidate_tokenizer_sha256']
        if hashlib.sha256(nlp.tokenizer.to_bytes(exclude=['vocab'])).hexdigest() != expected:
            raise ValueError('tokenizer bytes changed')
        guesses, other = raw.infer_raw(nlp, rows, native)
        predictions[run['name']] = guesses
        diagnostics.update(other)
        del nlp
        cupy.get_default_memory_pool().free_all_blocks()
    print(json.dumps({'state': 'passed', 'partition': 'test', 'predictions': predictions,
                      'native_non_loc_diagnostics': dict(diagnostics), 'training_performed': False,
                      'test_predictions_performed': True, 'inference_input': 'raw passage strings only'}))


if __name__ == '__main__':
    main()
