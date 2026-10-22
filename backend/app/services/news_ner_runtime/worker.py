"""Persistent, sequential, inference-only child. Run with Python -I -B."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import sys
import time

BOOT = time.monotonic()
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent.parent))
from app.services.news_ner.bundle import verify_bundle
from app.services.news_ner.contract import LABELS, MAX_OUTPUT_BYTES, object_sha, require
from app.services.news_ner.location_pipeline import LOCATION_METHOD, LOCATION_RULES, from_neural_mentions
from app.services.news_ner_runtime.protocol import INPUT_BYTES, SESSION_SECONDS, VERSION, decode, encode, validate_request, verify_code
from app.services.news_ner_runtime.isolation import install


def receive() -> dict:
    return decode(sys.stdin.buffer.readline(INPUT_BYTES + 1), INPUT_BYTES)


def send(value: dict) -> None:
    sys.stdout.buffer.write(encode(value, MAX_OUTPUT_BYTES))
    sys.stdout.buffer.flush()


def load_model(assets: Path):
    """Same authenticated reconstruction as the frozen preview; no disk edits."""
    import spacy
    from spacy.language import Language
    from spacy.tokenizer import Tokenizer
    from spacy.util import load_config, registry
    from spacy.vocab import Vocab
    require(spacy.__version__ == '3.7.5', 'spacy_version')
    spacy.require_cpu()
    def blocked(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError('training_prohibited')
    Language.initialize = Language.update = Language.begin_training = Language.resume_training = blocked
    original = (assets / 'model/tokenizer').read_bytes()
    @registry.tokenizers('lanes.subprocess_inference.v1')
    def factory():
        def create(nlp):
            nlp.vocab = Vocab().from_disk(assets / 'base/vocab')
            tokenizer = Tokenizer(nlp.vocab).from_bytes(original, exclude=['vocab'])
            require(tokenizer.to_bytes(exclude=['vocab']) == original, 'tokenizer_factory')
            return tokenizer
        return create
    cfg = load_config(assets / 'model/config.cfg')
    cfg['nlp']['tokenizer'] = {'@tokenizers': 'lanes.subprocess_inference.v1'}
    nlp = spacy.util.load_model_from_config(cfg, auto_fill=False)
    nlp.from_disk(assets / 'model')
    require(nlp.pipe_names == ['ner'] and set(nlp.get_pipe('ner').labels) == LABELS, 'pipeline_labels')
    require(nlp.tokenizer.to_bytes(exclude=['vocab']) == original, 'tokenizer_loaded')
    rebuilt = Tokenizer(nlp.vocab).from_bytes(original, exclude=['vocab'])
    return nlp, rebuilt, original


def main() -> None:
    require(platform.system() == 'Linux' and sys.version_info[:2] == (3, 12), 'linux_python_required')
    isolation = install()  # Before imports/model loading. Unsupported isolation never becomes ready.
    startup = receive()
    require(set(startup) == {'state', 'bundle_sha256', 'code'} and startup['state'] == 'startup', 'startup_required')
    verify_code(ROOT, startup['code'])
    assets = Path('/assets')
    bundle = verify_bundle(assets, startup['bundle_sha256'])
    nlp, rebuilt, original = load_model(assets)
    provenance = {'runtime': VERSION, 'model': 'v19-control-seed-0', 'bundle_sha256': startup['bundle_sha256'],
                  'model_manifest_sha256': bundle['model_manifest_sha256'], 'resource_manifest_sha256': bundle['resource_manifest_sha256'],
                  'tokenizer_sha256': hashlib.sha256(original).hexdigest(), 'code_sha256': object_sha(startup['code']),
                  'location_rules': LOCATION_RULES, 'location_method': LOCATION_METHOD, 'context_rules': 'lanes-context-association-v42'}
    send({'state': 'ready', 'runtime': VERSION, 'isolation': isolation, 'cold_seconds': time.monotonic() - BOOT,
          'provenance': provenance})
    while True:
        message = receive()
        if message == {'state': 'shutdown'}:
            verify_bundle(assets, startup['bundle_sha256'])
            verify_code(ROOT, startup['code'])
            send({'state': 'shutdown'})
            return
        require(time.monotonic() - BOOT < SESSION_SECONDS, 'session_expired')
        require(set(message) == {'state', 'request'} and message['state'] == 'request', 'request_required')
        request = message['request']
        validate_request(request)
        started = time.monotonic()
        doc = nlp(request['text'])
        require(doc.text == request['text'] and [(t.text, t.idx) for t in doc] == [(t.text, t.idx) for t in rebuilt(request['text'])], 'source_reconstruction')
        binding = object_sha({'bundle': startup['bundle_sha256'], 'tokenizer': provenance['tokenizer_sha256'], 'text': request['text_sha256']})
        mentions = [{'id': f'n{i}', 'start': e.start_char, 'end': e.end_char, 'text': e.text, 'label': e.label_, 'provenance_sha256': binding}
                    for i, e in enumerate(doc.ents)]
        extracted = from_neural_mentions({**request, 'mentions': mentions})
        require(nlp.tokenizer.to_bytes(exclude=['vocab']) == original, 'tokenizer_changed')
        send({'state': 'response', 'record_id': request['record_id'], 'result': {**extracted, 'provenance': provenance,
              'measurements': {'extraction_seconds': time.monotonic() - started,
                               'peak_worker_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024}}})


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        # No traceback, paths, article text, exception messages or secrets cross IPC.
        try:
            send({'state': 'error', 'code': type(exc).__name__})
        finally:
            os._exit(2)
