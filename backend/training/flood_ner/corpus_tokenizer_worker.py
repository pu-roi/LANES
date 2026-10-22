"""Isolated tokenizer-only corpus worker. Never load a trained pipeline."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import sys


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    if sys.version_info[:2] != (3, 11) or request.get('operation') != 'tokenize_only':
        raise ValueError('isolated Python 3.11 tokenizer-only operation required')
    # Import can fail under Windows Application Control. The parent retains
    # stderr and marks the run blocked instead of changing policies/packages.
    import spacy
    from spacy.tokenizer import Tokenizer
    from spacy.vocab import Vocab
    if spacy.__version__ != '3.7.5':
        raise ValueError('spaCy 3.7.5 required')
    spacy.require_cpu()
    native_bytes = Path(request['native_tokenizer']).read_bytes()
    candidate_bytes = Path(request['candidate_tokenizer']).read_bytes()
    corpus_bytes = Path(request['corpus_tokenizer']).read_bytes()
    vocab = Vocab().from_disk(request['vocab_dir'])
    tokenizers = {
        'native': Tokenizer(vocab).from_bytes(native_bytes, exclude=['vocab']),
        'candidate': Tokenizer(vocab).from_bytes(candidate_bytes, exclude=['vocab']),
        'corpus-v3': Tokenizer(Vocab()).from_bytes(corpus_bytes),
    }
    results = {}
    for mode, tokenizer in tokenizers.items():
        saved = tokenizer.to_bytes(exclude=['vocab'])
        output = Path(request['output']) / (mode + '.tokenizer.bin')
        output.write_bytes(saved)
        restored = Tokenizer(tokenizer.vocab).from_bytes(saved, exclude=['vocab'])
        rows = []
        for case in request['cases']:
            def signature(doc): return [(t.idx, t.text, t.whitespace_) for t in doc]
            doc, roundtrip = tokenizer(case['text']), restored(case['text'])
            if doc.text != case['text'] or roundtrip.text != case['text'] or signature(doc) != signature(roundtrip):
                raise ValueError('tokenizer changed source characters or serialization/reload behavior')
            tokens = [{'start': t.idx, 'end': t.idx + len(t.text), 'text': t.text, 'whitespace': t.whitespace_} for t in doc]
            rows.append({'case_id': case['case_id'], 'text_sha256': case['text_sha256'], 'tokens': tokens,
                'reference_alignment': [{'start': e['start'], 'end': e['end'], 'label': e['label'],
                    'aligned': doc.char_span(e['start'], e['end'], alignment_mode='strict') is not None} for e in case['entities']]})
        results[mode] = {'tokenizer_sha256': hashlib.sha256(saved).hexdigest(), 'roundtrip_identical': True, 'cases': rows}
    print(json.dumps({'schema_version': 'lanes-corpus-tokenizer-worker-v1', 'operation': 'tokenize_only',
        'python_version': platform.python_version(), 'spacy_version': spacy.__version__,
        'pipeline_components_loaded': [], 'model_predictions_performed': False, 'model_weights_loaded': False,
        'runs': results}, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__': main()
