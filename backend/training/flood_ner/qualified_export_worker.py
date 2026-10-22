"""Isolated location DocBin serialization; never load a model pipeline."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import sys

LABELS = frozenset({'ROAD', 'LANDMARK', 'LOCAL_AREA', 'BARANGAY', 'CITY', 'PROVINCE'})
SPLITS = ('train', 'dev', 'test')


def require(value, message):
    if not value:
        raise ValueError(message)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def tokens(doc):
    return [{'start': t.idx, 'end': t.idx + len(t.text), 'text': t.text,
             'whitespace': t.whitespace_} for t in doc]


def signature(rows):
    return hashlib.sha256(json_bytes(sorted(rows, key=lambda r: r['record_id']))).hexdigest()


def write_docbins(rows, tokenizer, tokenizer_bytes, output):
    """Shared with constructed unit tests; production admission is parent-owned."""
    from spacy.tokens import DocBin

    output = Path(output)
    names = [s + '.spacy' for s in SPLITS] + ['tokenizer.bin']
    require(output.is_dir() and not any((output / n).exists() for n in names),
            'refuse existing serialization files')
    require(rows and len(rows) == len({r['record_id'] for r in rows}), 'unique nonempty records required')
    require(tokenizer.to_bytes(exclude=['vocab']) == tokenizer_bytes, 'candidate bytes changed on reload')
    docs = {s: [] for s in SPLITS}
    negatives = 0
    spans = 0
    for row in sorted(rows, key=lambda r: r['record_id']):
        require(row['split'] in SPLITS and row['language'] in {'english', 'taglish'},
                'invalid frozen partition/language')
        text = row['text']
        require(hashlib.sha256(text.encode('utf-8')).hexdigest() == row['text_sha256'], 'passage hash mismatch')
        doc = tokenizer(text)
        require(doc.text == text and tokens(doc) == row['tokens'], 'qualified token boundaries/text changed')
        entities = []
        previous = 0
        for e in sorted(row['entities'], key=lambda e: e['start']):
            require(type(e['start']) is int and type(e['end']) is int
                    and previous <= e['start'] < e['end'] <= len(text) and e['label'] in LABELS,
                    'invalid, overlapping or out-of-profile entity')
            span = doc.char_span(e['start'], e['end'], label=e['label'], alignment_mode='strict')
            require(span is not None, 'entity not strictly aligned to qualified tokenizer')
            entities.append(span)
            previous = e['end']
        doc.ents = entities
        doc.user_data['record_id'] = row['record_id']
        docs[row['split']].append(doc)
        spans += len(entities)
        negatives += not entities
    files = {'tokenizer.bin': tokenizer_bytes}
    for split in SPLITS:
        binary = DocBin(attrs=['ORTH', 'SPACY', 'ENT_IOB', 'ENT_TYPE'], store_user_data=True)
        for doc in docs[split]:
            binary.add(doc)
        data = binary.to_bytes()
        restored = list(DocBin().from_bytes(data).get_docs(tokenizer.vocab))
        require(len(restored) == len(docs[split]), 'DocBin record count changed')
        for original, replay in zip(docs[split], restored):
            require(original.text == replay.text and tokens(original) == tokens(replay)
                    and original.user_data == replay.user_data
                    and [(e.start_char, e.end_char, e.label_) for e in original.ents]
                    == [(e.start_char, e.end_char, e.label_) for e in replay.ents],
                    'DocBin reload changed identities, text, tokens or labels')
        files[split + '.spacy'] = data
    # Validate every in-memory DocBin before creating any training file.
    for name, data in files.items():
        with (output / name).open('xb') as stream:
            stream.write(data)
    return {'records': len(rows), 'counts': {s: len(docs[s]) for s in SPLITS},
            'languages': dict(Counter(r['language'] for r in rows)),
            'location_spans': spans, 'negative_passages': negatives,
            'request_records_sha256': signature(rows), 'serialization_reload_verified': True,
            'files': {n: hashlib.sha256(v).hexdigest() for n, v in files.items()}}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    require(sys.version_info[:2] == (3, 11)
            and request.get('operation') == 'export_qualified_location_corpus',
            'isolated Python 3.11 location export required')
    import spacy
    from spacy.tokenizer import Tokenizer
    from spacy.vocab import Vocab

    require(spacy.__version__ == '3.7.5', 'spaCy 3.7.5 required')
    spacy.require_cpu()
    vocab = Vocab().from_disk(request['vocab_dir'])
    data = Path(request['candidate_tokenizer']).read_bytes()
    require(hashlib.sha256(data).hexdigest() == request['candidate_sha256'], 'candidate hash changed')
    tokenizer = Tokenizer(vocab).from_bytes(data, exclude=['vocab'])
    report = write_docbins(request['records'], tokenizer, data, request['output'])
    report.update(schema_version='lanes-qualified-export-worker-v1', operation=request['operation'],
                  python_version=platform.python_version(), spacy_version=spacy.__version__,
                  pipeline_components_loaded=[], model_weights_loaded=False,
                  model_predictions_performed=False, training_performed=False)
    print(json_bytes(report).decode('utf-8'))


if __name__ == '__main__':
    main()
