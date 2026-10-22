"""One stdin request, isolated CPU inference, one stdout response. No ORM imports."""
import hashlib
import json
from pathlib import Path
import platform
import signal
import sys
import time

BOOT = time.monotonic()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from news_ner.bundle import digest, safe_file, verify_bundle
from news_ner.contract import IMAGE, LABELS, MAX_CHARS, MAX_OUTPUT_BYTES, object_sha, require, validate_raw_input
from news_ner.location_pipeline import LOCATION_RULES, LOCATION_METHOD

CONTEXT_IMPLEMENTATION = 'lanes-context-association-v42'


def context_from_effective_mentions(raw: dict) -> dict:
    """Pure context boundary, also verifiable with cached effective mentions."""
    from news_ner.context_association_v42 import extract
    return extract(raw)


def extraction_from_neural_mentions(raw: dict) -> dict:
    """Shared explicit proposal chain and v42 graph; no model call here."""
    from news_ner.location_pipeline import from_neural_mentions
    return from_neural_mentions(raw)


def deadline(*_args: object) -> None:
    raise TimeoutError('preview deadline')


def run(request: dict) -> dict:
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, 60)
    require(set(request) == {'text', 'record_id', 'text_sha256', 'publication', 'bundle_sha256', 'code'}, 'exact worker request required')
    require(platform.system() == 'Linux' and sys.version_info[:2] == (3, 12), 'qualified Linux Python required')
    require(isinstance(request['text'], str) and len(request['text']) <= MAX_CHARS, 'bounded body required')
    package = Path(__file__).resolve().parent
    expected_code = {p.name for p in package.iterdir() if p.is_file() and p.suffix == '.py'} | {'promotion.json'}
    require(set(request['code']) == expected_code, 'complete code bindings required')
    for name, sha in request['code'].items():
        require(digest(safe_file(package, name)) == sha, 'worker code mismatch')
    assets = Path('/assets')
    bundle = verify_bundle(assets, request['bundle_sha256'])
    import spacy
    from spacy.language import Language
    from spacy.tokenizer import Tokenizer
    from spacy.util import load_config, registry
    from spacy.vocab import Vocab

    require(spacy.__version__ == '3.7.5', 'qualified spaCy required')
    spacy.require_cpu()

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError('training prohibited')

    Language.initialize = Language.update = Language.begin_training = Language.resume_training = blocked
    model = assets / 'model'
    original = (model / 'tokenizer').read_bytes()

    @registry.tokenizers('lanes.preview_inference.v1')
    def factory():
        def create(nlp):
            nlp.vocab = Vocab().from_disk(assets / 'base/vocab')
            tokenizer = Tokenizer(nlp.vocab).from_bytes(original, exclude=['vocab'])
            require(tokenizer.to_bytes(exclude=['vocab']) == original, 'tokenizer factory mismatch')
            return tokenizer
        return create

    cfg = load_config(model / 'config.cfg')
    cfg['nlp']['tokenizer'] = {'@tokenizers': 'lanes.preview_inference.v1'}
    nlp = spacy.util.load_model_from_config(cfg, auto_fill=False)
    nlp.from_disk(model)
    require(nlp.pipe_names == ['ner'] and set(nlp.get_pipe('ner').labels) == LABELS, 'unexpected pipeline')
    require(nlp.tokenizer.to_bytes(exclude=['vocab']) == original, 'loaded tokenizer mismatch')
    rebuilt = Tokenizer(nlp.vocab).from_bytes(original, exclude=['vocab'])
    cold_seconds = time.monotonic() - BOOT
    signal.setitimer(signal.ITIMER_REAL, 30)
    extraction_started = time.monotonic()
    doc = nlp(request['text'])
    require(doc.text == request['text'] and [(t.text, t.idx) for t in doc] == [(t.text, t.idx) for t in rebuilt(request['text'])], 'source reconstruction mismatch')
    neural_provenance = object_sha({'bundle': request['bundle_sha256'], 'tokenizer': hashlib.sha256(original).hexdigest(), 'text': request['text_sha256']})
    mentions = [{'id': f'n{i}', 'start': e.start_char, 'end': e.end_char, 'text': e.text,
                 'label': e.label_, 'provenance_sha256': neural_provenance} for i, e in enumerate(doc.ents)]
    raw = {k: request[k] for k in ('record_id', 'text', 'text_sha256', 'publication')}
    raw['mentions'] = mentions
    validate_raw_input(raw)
    extracted = extraction_from_neural_mentions(raw)
    proposal, graph = extracted['proposal'], extracted['graph']
    verify_bundle(assets, request['bundle_sha256'])
    require(nlp.tokenizer.to_bytes(exclude=['vocab']) == original, 'post-inference tokenizer mismatch')
    import resource
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    require(peak_rss <= 3 * 1024**3, 'qualified worker RSS limit exceeded')
    signal.setitimer(signal.ITIMER_REAL, 0)
    return {'proposal': proposal, 'graph': graph, 'measurements': {'cold_seconds': cold_seconds,
        'extraction_seconds': time.monotonic() - extraction_started, 'peak_worker_rss_bytes': peak_rss}, 'provenance': {
        'model': 'v19-control-seed-0', 'bundle_sha256': request['bundle_sha256'],
        'model_manifest_sha256': bundle['model_manifest_sha256'],
        'resource_manifest_sha256': bundle['resource_manifest_sha256'],
        'tokenizer_sha256': hashlib.sha256(original).hexdigest(), 'image': IMAGE,
        'code_sha256': object_sha(request['code']), 'location_rules': LOCATION_RULES,
        'location_method': LOCATION_METHOD,
        'context_rules': CONTEXT_IMPLEMENTATION}}


if __name__ == '__main__':
    try:
        payload = sys.stdin.buffer.read(1024 * 1024 + 1)
        require(len(payload) <= 1024 * 1024, 'worker input too large')
        result = json.dumps(run(json.loads(payload)), ensure_ascii=False).encode('utf-8')
        require(len(result) <= MAX_OUTPUT_BYTES, 'worker output too large')
        sys.stdout.buffer.write(result)
    except Exception as exc:
        # Raw tracebacks may contain private source or paths; expose only a type.
        sys.stderr.write(type(exc).__name__)
        raise SystemExit(2)
