"""Scoped Linux CPU shadow worker. Outputs stay private; no references accepted."""
from __future__ import annotations

import time
COLD_STARTED = time.monotonic()
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import socket
import sys

if not __package__:
    sys.path[:0] = [str(Path(__file__).resolve().parents[2]), '/app']
from training.flood_ner import shadow_comparison as controller
from training.flood_ner import linux_runtime_v29 as q
from training.flood_ner.linux_runtime_worker_v29 import heartbeat, timeout_handler
from training.flood_ner.runtime_preflight import authenticate, bound_json, digest, require, verify_files
from training.flood_ner.runtime_probe_worker import blocked
from app.services import ner_shadow_service as service
from training.flood_ner.corrected_rules_worker import install_guards

REQUEST_KEYS = {'schema', 'implementation', 'model_sha256', 'resource_sha256', 'workload_sha256',
                'rules_files', 'provenance', 'requirements_sha256'}


def checked_request(path: Path, sha: str) -> dict:
    request = bound_json(path, sha)
    require(set(request) == REQUEST_KEYS and request['schema'] == 'lanes-shadow-worker-v30' and
            set(request['implementation']) == set(controller.CODE), 'exact worker authorization required')
    for name, expected in request['implementation'].items():
        source = Path('/app') / name[len('backend/'):] if name.startswith('backend/app/') else Path('/code') / name[len('backend/'):]
        require(digest(source) == expected, 'worker implementation binding mismatch')
    return request


def run(request: dict, inputs: Path, output: Path) -> dict:
    require(platform.system() == 'Linux' and sys.version_info[:2] == (3, 12), 'Linux Python 3.12 required')
    require(output.is_dir() and not any(output.iterdir()), 'new empty worker output required')
    signal.signal(signal.SIGALRM, timeout_handler); signal.setitimer(signal.ITIMER_REAL, 60)
    require(digest(Path('/app/requirements.txt')) == request['requirements_sha256'], 'wrong image requirements')
    for name, expected in request['rules_files'].items():
        source = Path('/data') / name[len('runtime_data/'):] if name.startswith('runtime_data/') else Path('/app') / name
        require(digest(source) == expected, 'rules code/asset binding mismatch')
    rows = controller.workload(bound_json(inputs / 'workload.json', request['workload_sha256']))
    authenticated = authenticate(Path('/assets/MANIFEST.json'), request['model_sha256'],
        Path('/assets/resource.json'), request['resource_sha256'], Path('/assets/base'))
    rules_sha = hashlib.sha256(json.dumps(request['rules_files'], sort_keys=True).encode()).hexdigest()
    require(request['provenance'] == {'model': request['model_sha256'],
            'tokenizer': authenticated['tokenizer_sha256'], 'rules': rules_sha}, 'false provenance')
    os.environ.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    socket.create_connection = socket.socket.connect = socket.socket.connect_ex = blocked
    import sqlalchemy
    sqlalchemy.create_engine = sqlalchemy.create_pool_from_url = blocked
    from sqlalchemy.ext import asyncio as sql_async
    sql_async.create_async_engine = blocked
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

    @registry.tokenizers('lanes.shadow_inference.v30')
    def factory():
        def create(nlp):
            nlp.vocab = Vocab().from_disk('/assets/base/vocab')
            tokenizer = Tokenizer(nlp.vocab).from_bytes(original, exclude=['vocab'])
            require(tokenizer.to_bytes(exclude=['vocab']) == original, 'factory tokenizer differs')
            return tokenizer
        return create

    config = load_config(model / 'config.cfg')
    config['nlp']['tokenizer'] = {'@tokenizers': 'lanes.shadow_inference.v30'}
    nlp = spacy.util.load_model_from_config(config, auto_fill=False); nlp.from_disk(model)
    require(nlp.pipe_names == ['ner'] and set(nlp.get_pipe('ner').labels) == service.LABELS, 'unexpected pipeline')
    require(nlp.tokenizer.to_bytes(exclude=['vocab']) == original, 'loaded tokenizer differs')
    rebuilt = Tokenizer(nlp.vocab).from_bytes(original, exclude=['vocab'])

    def predict(text: str) -> list[dict]:
        doc = nlp(text)
        require(doc.text == text and [(t.text, t.idx) for t in doc] ==
                [(t.text, t.idx) for t in rebuilt(text)], 'source/tokenizer reconstruction differs')
        return [{'start': e.start_char, 'end': e.end_char, 'text': e.text, 'label': e.label_} for e in doc.ents]

    # The rules module imports an enum through ORM package initializers. Reuse
    # the frozen rules worker's inert declaration facade; never create a driver,
    # connection, session or engine. The actual application files stay unchanged.
    install_guards()
    from app.services.taglish_extraction_service import split_sentences_with_offsets, find_place_mentions
    database = sys.modules.get('app.core.database')
    require(database is not None and type(database.engine).__name__ == 'OfflineEngine',
            'rules import must use the inert offline declaration facade')
    predict('Read-only shadow warmup.')
    q.write_new(output / 'ready.json', {'cold_worker_seconds': time.monotonic() - COLD_STARTED})
    signal.setitimer(signal.ITIMER_REAL, 0)
    timings = []
    with (output / 'comparisons.jsonl').open('x', encoding='utf-8', newline='\n') as stream:
        for index, row in enumerate(rows):
            heartbeat(output, 'article', index); signal.setitimer(signal.ITIMER_REAL, 30)
            started = time.monotonic()
            value = {k: row[k] for k in ('article_id', 'text', 'text_sha256')}
            result = service.compare_article(value, predict, provenance=request['provenance'],
                        splitter=split_sentences_with_offsets, finder=find_place_mentions)
            timings.append(time.monotonic() - started)
            stream.write(json.dumps(result, ensure_ascii=False) + '\n'); stream.flush()
            require(result['status'] == 'completed', 'extractor failure; partial independent results preserved')
            signal.setitimer(signal.ITIMER_REAL, 0)
    verify_files(model, authenticated['model_files']); verify_files(Path('/assets/base'), authenticated['resource_files'])
    require(nlp.tokenizer.to_bytes(exclude=['vocab']) == original, 'post-inference tokenizer differs')
    return {'status': 'completed', 'row_seconds': timings,
            'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            'tokenizer_verified': True, 'training_started': False, 'application_connected': False,
            'validation_evaluated': False, 'holdout_accessed': False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True); parser.add_argument('--request-sha256', required=True)
    args = parser.parse_args(); output = Path('/output')
    try:
        result = run(checked_request(args.request, args.request_sha256), args.request.parent, output)
        q.write_new(output / 'measurements.json', result)
    except BaseException as exc:
        import traceback
        with (output / 'private-failure-traceback.txt').open('x', encoding='utf-8') as stream:
            stream.write(traceback.format_exc())
        q.write_new(output / 'failure.json', {'status': 'failed', 'error_type': type(exc).__name__})
        raise SystemExit(2) from exc


if __name__ == '__main__':
    main()
