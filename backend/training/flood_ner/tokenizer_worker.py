"""Isolated CPU comparison worker; constructed text only, no article loading."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import statistics
import sys
import time
from typing import Any


def sibling(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8'); sys.stderr.reconfigure(encoding='utf-8')
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    cases = request['cases']; mode = request['mode']
    if sys.version_info[:2] != (3, 11) or platform.system() != 'Windows':
        raise ValueError('isolated Windows CPython 3.11 required')
    if (mode not in {'native', 'candidate'} or len(cases) != 48
            or any(c.get('origin') != 'constructed_fixture' or c.get('quality') != 'constructed' for c in cases)):
        raise ValueError('48 constructed cases and explicit tokenizer mode required')
    import spacy
    import torch
    from spacy.tokenizer import Tokenizer
    if spacy.__version__ != '3.7.5' or torch.version.cuda is not None:
        raise ValueError('spaCy 3.7.5 / CPU torch required')
    torch.set_num_threads(2); torch.manual_seed(0); spacy.require_cpu()
    start = time.perf_counter()
    nlp = spacy.load(request['model_dir'], exclude=['tagger', 'morphologizer', 'parser'])
    load_ms = (time.perf_counter() - start) * 1000
    if nlp.meta.get('version') != '0.1.0' or set(nlp.get_pipe('ner').labels) != {'LOC', 'ORG', 'PER'}:
        raise ValueError('model identity/labels differ')
    candidate = sibling('model_tokenizer')
    if mode == 'candidate': candidate.apply_candidate(nlp.tokenizer)
    # Vocabulary identity comes from the bound model, not tokenizer serialization.
    tokenizer_bytes = nlp.tokenizer.to_bytes(exclude=['vocab'])
    Path(request['tokenizer_file']).write_bytes(tokenizer_bytes)
    restored = Tokenizer(nlp.vocab).from_bytes(tokenizer_bytes, exclude=['vocab'])
    def signature(doc: Any) -> list[tuple]:
        return [(t.idx, t.text, t.whitespace_) for t in doc]
    roundtrip = all(signature(nlp.make_doc(c['text'])) == signature(restored(c['text'])) for c in cases)
    if not roundtrip: raise ValueError('saved tokenizer roundtrip differs')
    nlp.tokenizer = restored
    for case in cases: nlp(case['text'])
    latencies = []; rows = []; signatures = {}; identical = True
    for repeat in range(10):
        for case in cases:
            start = time.perf_counter(); doc = nlp(case['text']); latencies.append((time.perf_counter() - start) * 1000)
            if doc.text != case['text']: raise ValueError('model changed source text')
            tokens = [{'start': t.idx, 'end': t.idx + len(t.text), 'text': t.text} for t in doc]
            entities = [{'start': e.start_char, 'end': e.end_char, 'label': e.label_, 'text': e.text} for e in doc.ents]
            current = json.dumps({'tokens': tokens, 'entities': entities}, sort_keys=True)
            if repeat and signatures[case['case_id']] != current: identical = False
            if not repeat:
                signatures[case['case_id']] = current
                rows.append({'case_id': case['case_id'], 'text_sha256': hashlib.sha256(doc.text.encode('utf-8')).hexdigest(),
                             'tokens': tokens, 'entities': entities,
                             'reference_alignment': [{'start': p['start'], 'end': p['end'], 'label': p['label'],
                                                      'aligned': doc.char_span(p['start'], p['end'], alignment_mode='strict') is not None}
                                                     for p in case['expected_places']]})
    ordered = sorted(latencies)
    result = {'schema_version': 'lanes-model-preflight-result-v1', 'python_version': platform.python_version(),
              'spacy_version': spacy.__version__, 'model_revision': request['model_revision'], 'model_version': nlp.meta['version'],
              'cpu_only': True, 'pipeline': nlp.pipe_names, 'repeated_predictions_identical': identical,
              'tokenizer_mode': mode, 'tokenizer_name': 'calamancy-native' if mode == 'native' else candidate.TOKENIZER_NAME,
              'tokenizer_sha256': hashlib.sha256(tokenizer_bytes).hexdigest(), 'roundtrip_identical': roundtrip,
              'cases': rows, 'resources': {'load_ms': load_ms, 'p50_ms': statistics.median(latencies),
                                          'p95_ms': ordered[int(.95 * (len(ordered) - 1))],
                                          'peak_working_set_bytes': sibling('preflight_worker').peak_working_set(),
                                          'warmup_passes': 1, 'measured_passes': 10, 'measured_calls': len(latencies),
                                          'batch_size': 1, 'threads': 2}}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__': main()
