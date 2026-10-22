"""Isolated GPU inference on raw validation passage strings, never test data."""
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def infer_raw(nlp: object, rows: list[dict], native: bool) -> tuple[dict, dict]:
    predictions = {}
    diagnostics = Counter()
    docs = list(nlp.pipe([r['text'] for r in rows], batch_size=8))
    if len(docs) != len(rows):
        raise ValueError('inference omitted validation records')
    for row, doc in zip(rows, docs):
        if doc.text != row['text']:
            raise ValueError('inference text changed')
        predictions[row['record_id']] = [(e.start_char, e.end_char, e.label_) for e in doc.ents if not native or e.label_ == 'LOC']
        if native:
            diagnostics.update(e.label_ for e in doc.ents if e.label_ != 'LOC')
    return predictions, dict(diagnostics)


def main() -> None:
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    if sys.version_info[:2] != (3, 11) or request.get('operation') != 'validation_only':
        raise ValueError('qualified Python 3.11 validation request required')
    rows = request['rows']
    if len(rows) != 60 or any(r['kind'] != 'location' or r['split'] != 'dev' for r in rows):
        raise ValueError('validation records only')
    if Path(request['dev_docbin']).name != 'dev.spacy' or digest(Path(request['dev_docbin'])) != request['dev_docbin_sha256']:
        raise ValueError('frozen validation DocBin required')
    if digest(Path(request['registry'])) != request['registry_sha256']:
        raise ValueError('frozen registry changed')
    site = Path(sys.prefix) / 'Lib/site-packages'
    handles = [os.add_dll_directory(str(p)) for p in
               (site/'torch/lib', site/'nvidia/cuda_runtime/bin', site/'nvidia/cuda_nvrtc/bin') if p.is_dir()]
    os.environ['CUDA_PATH'] = str(site/'nvidia/cuda_runtime')
    import spacy
    import torch
    import cupy
    from spacy.vocab import Vocab
    from spacy.tokens import DocBin
    if spacy.__version__ != '3.7.5' or not torch.cuda.is_available() or not spacy.require_gpu(0):
        raise ValueError('qualified GPU required')
    torch.set_num_threads(2)
    spec = importlib.util.spec_from_file_location('lanes_experiment_registry', request['registry'])
    module = importlib.util.module_from_spec(spec);sys.modules[spec.name] = module;spec.loader.exec_module(module)
    vocab = Vocab().from_disk(Path(request['native_model'])/'vocab')
    docs = list(DocBin().from_disk(request['dev_docbin']).get_docs(vocab))
    references = {d.user_data['record_id']: d for d in docs}
    if len(references) != len(docs) or set(references) != {r['record_id'] for r in rows}:
        raise ValueError('validation DocBin membership differs')
    for row in rows:
        ref = references[row['record_id']]
        if (ref.text != row['text'] or hashlib.sha256(row['text'].encode('utf-8')).hexdigest() != row['text_sha256']
                or [(e.start_char,e.end_char,e.label_) for e in ref.ents] != [(e['start'],e['end'],e['label']) for e in row['entities']]):
            raise ValueError('validation text/labels differ from qualified export')
    predictions = {};diagnostics = Counter()
    for run in request['runs'] + [{'name': 'native', 'model': request['native_model']}]:
        native = run['name'] == 'native'
        if not native:
            for name,h in run['model_files'].items():
                if digest(Path(run['model'])/name) != h:raise ValueError('selected model changed')
        nlp = spacy.load(run['model'], exclude=['tok2vec','tagger','morphologizer','parser'] if native else [])
        labels = set(nlp.get_pipe('ner').labels)
        if labels != ({'LOC','ORG','PER'} if native else set(module.LABELS)):
            raise ValueError('model label profile differs')
        expected = request['native_tokenizer_sha256'] if native else request['candidate_tokenizer_sha256']
        if hashlib.sha256(nlp.tokenizer.to_bytes(exclude=['vocab'])).hexdigest() != expected:
            raise ValueError('model tokenizer identity differs')
        # Never pass reference Docs/Examples to inference: only original strings.
        out, other = infer_raw(nlp, rows, native)
        diagnostics.update(other)
        predictions[run['name']] = out
        del nlp
        cupy.get_default_memory_pool().free_all_blocks()
    print(json.dumps({'state':'passed','partition':'dev','predictions':predictions,
                      'native_non_loc_diagnostics':dict(diagnostics), 'training_performed':False,
                      'test_predictions_performed':False,'inference_input':'raw validation passage strings only'}))


if __name__ == '__main__':
    main()
