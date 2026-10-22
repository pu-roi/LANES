"""CPU inference smoke test on fixed fictional text; not Linux qualification.

No corpus input is accepted. No pipeline initialization, optimizer, export or
application import is used. Original configs and checkpoints are never edited.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import socket
import statistics
import sys
import time

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner.runtime_preflight import LABELS, authenticate, digest, require, verify_files

PROBES = (
    '  Floodwater was reported along Aster Road in Sample City.\n',
    'May baha sa Piña Street at closed ang road sa Barangay Halimbawa.',
    'A flood-control project was announced for Sample City next year.',
    'Walang baha at open ang Sample Road. Sample Road remains passable.',
)
REQUEST_KEYS = {'scope', 'model_manifest', 'model_manifest_sha256', 'resource_manifest',
                'resource_manifest_sha256', 'resource_dir', 'worker_sha256'}


def checked_request(path: Path, sha: str) -> dict:
    require(digest(path) == sha, 'stale probe request')
    value = json.loads(path.read_text(encoding='utf-8'))
    require(set(value) == REQUEST_KEYS and value['scope'] == 'fictional_cpu_runtime_smoke',
            'only the fixed fictional smoke scope is supported; no corpus input')
    require(value['worker_sha256'] == digest(Path(__file__)), 'stale worker binding')
    return value


def blocked(*args: object, **kwargs: object) -> None:
    raise RuntimeError('runtime probe forbids training and outbound connections')


def spans(doc: object, text: str) -> list:
    require(doc.text == text, 'source text changed')
    rows = []
    end = 0
    for entity in doc.ents:
        require(entity.label_ in LABELS and type(entity.start_char) is int and type(entity.end_char) is int
                and end <= entity.start_char < entity.end_char <= len(text)
                and text[entity.start_char:entity.end_char] == entity.text,
                'invalid predicted location span')
        end = entity.end_char
        rows.append([entity.start_char, entity.end_char, entity.label_])
    return rows


def probe(request: dict) -> dict:
    authenticated = authenticate(Path(request['model_manifest']), request['model_manifest_sha256'],
        Path(request['resource_manifest']), request['resource_manifest_sha256'], Path(request['resource_dir']))
    # No automatic fallback to GPU or a training runtime.
    require(sys.version_info[:2] == (3, 12), 'backend Python 3.12 required')
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    socket.create_connection = blocked
    socket.socket.connect = blocked
    socket.socket.connect_ex = blocked
    import spacy
    from spacy.language import Language
    from spacy.tokenizer import Tokenizer
    from spacy.util import registry
    from spacy.vocab import Vocab
    require(spacy.__version__ == '3.7.5', 'spaCy 3.7.5 required')
    spacy.require_cpu()
    Language.initialize = blocked
    Language.update = blocked
    Language.begin_training = blocked
    Language.resume_training = blocked
    model = authenticated['model']
    original = (model / 'tokenizer').read_bytes()

    # Inference-only factory. Never import historical training callbacks.
    @registry.tokenizers('lanes.runtime_tokenizer_probe.v1')
    def factory():
        def create(nlp):
            nlp.vocab = Vocab().from_disk(Path(request['resource_dir']) / 'vocab')
            tokenizer = Tokenizer(nlp.vocab).from_bytes(original, exclude=['vocab'])
            require(tokenizer.to_bytes(exclude=['vocab']) == original, 'tokenizer factory mismatch')
            return tokenizer
        return create

    started = time.perf_counter()
    # Replace the whole tokenizer registry config in memory, retaining all model
    # architectures and weights. Original desktop paths stay untouched on disk.
    from spacy.util import load_config
    config = load_config(model / 'config.cfg')
    config['nlp']['tokenizer'] = {'@tokenizers': 'lanes.runtime_tokenizer_probe.v1'}
    nlp = spacy.util.load_model_from_config(config, auto_fill=False)
    nlp.from_disk(model)
    load_seconds = time.perf_counter() - started
    require(nlp.pipe_names == ['ner'] and set(nlp.get_pipe('ner').labels) == LABELS,
            'unexpected loaded pipeline')
    require(nlp.tokenizer.to_bytes(exclude=['vocab']) == original, 'loaded tokenizer mismatch')
    rebuilt = Tokenizer(nlp.vocab).from_bytes(original, exclude=['vocab'])
    baseline = []
    first = time.perf_counter()
    for text in PROBES:
        doc = nlp(text)
        require([(t.text, t.idx) for t in doc] == [(t.text, t.idx) for t in rebuilt(text)],
                'tokenizer reconstruction mismatch')
        baseline.append(spans(doc, text))
    first_seconds = time.perf_counter() - first
    elapsed = []
    for _ in range(10):
        for text, expected in zip(PROBES, baseline):
            start = time.perf_counter(); actual = spans(nlp(text), text)
            elapsed.append(time.perf_counter() - start)
            require(actual == expected, 'non-deterministic CPU predictions')
    verify_files(model, authenticated['model_files'])
    verify_files(Path(request['resource_dir']), authenticated['resource_files'])
    return {'schema': 'lanes-v19-fictional-runtime-smoke-v1', 'status': 'smoke_passed',
        'system': platform.system(), 'python': list(sys.version_info[:3]), 'spacy': spacy.__version__,
        'device': 'cpu', 'fictional_probes': len(PROBES), 'warm_calls': len(elapsed),
        'load_seconds': load_seconds, 'first_four_probes_seconds': first_seconds,
        'warm_median_seconds': statistics.median(elapsed), 'warm_max_seconds': max(elapsed),
        'tokenizer_parity': True, 'deterministic_predictions': True,
        'linux_inference_qualified': False, 'production_latency_qualified': False,
        'memory_measured': False, 'training_started': False, 'application_connected': False,
        'validation_accessed': False, 'holdout_accessed': False}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request', type=Path, required=True)
    p.add_argument('--request-sha256', required=True)
    args = p.parse_args()
    request = checked_request(args.request, args.request_sha256)
    try:
        result = probe(request)
    except Exception as exc:
        result = {'status': 'smoke_blocked', 'error_type': type(exc).__name__,
                  'detail': str(exc), 'linux_inference_qualified': False, 'training_started': False}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
