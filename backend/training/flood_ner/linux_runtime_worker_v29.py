"""Linux-only CPU measurements on a frozen raw-text workload, without references."""
from __future__ import annotations

import time
COLD_STARTED = time.monotonic()
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import signal
import socket
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner.runtime_preflight import LABELS, authenticate, bound_json, digest, require, verify_files
from training.flood_ner.runtime_probe_worker import blocked, spans
from training.flood_ner.linux_runtime_v29 import POLICY, SOURCES, text_hash, validate_workload, write_new

REQUEST_KEYS = {'schema', 'policy', 'model_manifest_sha256', 'resource_manifest_sha256',
                'workload_sha256', 'implementation', 'requirements_sha256'}


def checked_request(path: Path, sha: str) -> dict:
    value = bound_json(path, sha)
    require(set(value) == REQUEST_KEYS and value['schema'] == 'lanes-linux-runtime-worker-v29'
            and value['policy'] == POLICY and set(value['implementation']) == set(SOURCES), 'frozen worker request required')
    for name, expected in value['implementation'].items():
        require(digest(Path(__file__).parent / name) == expected, 'worker implementation differs')
    return value


def timeout_handler(*args: object) -> None:
    raise TimeoutError('frozen worker phase deadline exceeded')


def heartbeat(output: Path, phase: str, index: int) -> None:
    # Atomic replacement only within this attempt's private writable output.
    temp = output / 'heartbeat.tmp'
    with temp.open('x', encoding='utf-8') as stream:
        json.dump({'phase': phase, 'index': index}, stream)
    os.replace(temp, output / 'heartbeat.json')


def run(request: dict, input_dir: Path, output: Path) -> dict:
    require(platform.system() == 'Linux' and sys.version_info[:2] == (3, 12), 'Linux Python 3.12 required')
    require(output.is_dir() and not any(output.iterdir()), 'empty private worker output required')
    require(digest(Path('/app/requirements.txt')) == request['requirements_sha256'], 'image requirement binding differs')
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, POLICY['cold_seconds'])
    workload = bound_json(input_dir / 'workload.json', request['workload_sha256'])
    require(set(workload) == {'rows'}, 'raw workload object required')
    rows = workload['rows']; validate_workload(rows)
    authenticated = authenticate(Path('/assets/MANIFEST.json'), request['model_manifest_sha256'],
        Path('/assets/resource.json'), request['resource_manifest_sha256'], Path('/assets/base'))
    os.environ.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    socket.create_connection = blocked
    socket.socket.connect = blocked
    socket.socket.connect_ex = blocked
    import resource
    import spacy
    from spacy.language import Language
    from spacy.tokenizer import Tokenizer
    from spacy.util import registry, load_config
    from spacy.vocab import Vocab
    require(spacy.__version__ == '3.7.5', 'spaCy 3.7.5 required')
    spacy.require_cpu()
    Language.initialize = Language.update = Language.begin_training = Language.resume_training = blocked
    model = authenticated['model']; original = (model / 'tokenizer').read_bytes()

    @registry.tokenizers('lanes.linux_qualification_tokenizer.v1')
    def factory():
        def create(nlp):
            nlp.vocab = Vocab().from_disk('/assets/base/vocab')
            tokenizer = Tokenizer(nlp.vocab).from_bytes(original, exclude=['vocab'])
            require(tokenizer.to_bytes(exclude=['vocab']) == original, 'factory tokenizer bytes differ')
            return tokenizer
        return create

    config = load_config(model / 'config.cfg')
    config['nlp']['tokenizer'] = {'@tokenizers': 'lanes.linux_qualification_tokenizer.v1'}
    started = time.monotonic()
    nlp = spacy.util.load_model_from_config(config, auto_fill=False)
    nlp.from_disk(model)
    load_seconds = time.monotonic() - started
    require(nlp.pipe_names == ['ner'] and set(nlp.get_pipe('ner').labels) == LABELS, 'unexpected pipeline')
    require(nlp.tokenizer.to_bytes(exclude=['vocab']) == original, 'loaded tokenizer bytes differ')
    rebuilt = Tokenizer(nlp.vocab).from_bytes(original, exclude=['vocab'])
    # Prime fixed fictional text, never an additional corpus member.
    nlp('Read-only runtime warmup.')
    ready_seconds = time.monotonic() - COLD_STARTED
    write_new(output / 'ready.json', {'cold_worker_seconds': ready_seconds})
    signal.setitimer(signal.ITIMER_REAL, 0)
    timings = {kind + '_seconds': [] for kind in ('passage', 'article', 'stress')}
    with (output / 'predictions.jsonl').open('x', encoding='utf-8', newline='\n') as predictions:
        for index, row in enumerate(rows):
            kind = row['kind']; heartbeat(output, kind, index)
            deadline = POLICY['article_seconds'] if kind == 'article' else POLICY['stress_seconds']
            signal.setitimer(signal.ITIMER_REAL, deadline)
            text = row['text']; started = time.monotonic(); doc = nlp(text)
            entities = spans(doc, text)
            elapsed = time.monotonic() - started
            signal.setitimer(signal.ITIMER_REAL, 0)
            require(elapsed <= deadline, 'phase elapsed time exceeded')
            require([(t.text, t.idx) for t in doc] == [(t.text, t.idx) for t in rebuilt(text)], 'tokenizer reconstruction differs')
            timings[kind + '_seconds'].append(elapsed)
            if kind == 'passage':
                predictions.write(json.dumps({'record_id': row['record_id'], 'text_sha256': text_hash(text), 'prediction': entities}) + '\n')
                predictions.flush()
    verify_files(model, authenticated['model_files'])
    verify_files(Path('/assets/base'), authenticated['resource_files'])
    require(nlp.tokenizer.to_bytes(exclude=['vocab']) == original, 'post-inference tokenizer bytes differ')
    timings['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    packages = sorted({(d.metadata['Name'], d.version) for d in importlib.metadata.distributions()})
    return {'schema': 'lanes-linux-runtime-measurements-v1', 'status': 'worker_completed',
            'system': platform.system(), 'python': list(sys.version_info[:3]), 'spacy': spacy.__version__,
            'machine': platform.machine(), 'device': 'cpu', 'resolved_packages': packages,
            'cold_worker_seconds': ready_seconds, 'model_load_seconds': load_seconds,
            'metrics': timings, 'tokenizer_verified': True, 'training_started': False,
            'validation_accessed': False, 'holdout_accessed': False, 'gate_3_cleared': False}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request', type=Path, required=True)
    p.add_argument('--request-sha256', required=True)
    args = p.parse_args()
    output = Path('/output')
    try:
        request = checked_request(args.request, args.request_sha256)
        result = run(request, args.request.parent, output)
        write_new(output / 'measurements.json', result)
    except Exception as exc:
        if output.is_dir():
            write_new(output / 'failure.json', {'status': 'worker_failed', 'error_type': type(exc).__name__, 'detail': str(exc)})
        raise SystemExit(2) from exc


if __name__ == '__main__': main()
