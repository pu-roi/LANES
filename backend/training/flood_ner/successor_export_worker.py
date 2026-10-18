"""Pinned-runtime successor export worker: vocabulary + tokenizer only, no pipelines."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import sys
from types import SimpleNamespace


def serialize(records, tokenizer, tokenizer_bytes, output, capability):
    from spacy.tokens import DocBin
    from training.flood_ner.successor_preparation import PARTITIONS, require, write_new, digest

    partitions = PARTITIONS[capability]
    docs = {s: [] for s in partitions}
    require(tokenizer.to_bytes(exclude=['vocab']) == tokenizer_bytes, 'tokenizer reload mismatch')
    for record, partition in records:
        require(partition in docs, 'worker received forbidden partition')
        doc = tokenizer(record.text)
        spans = [doc.char_span(e.start, e.end, label=e.label, alignment_mode='strict') for e in record.entities]
        require(all(span is not None for span in spans) and doc.text == record.text, 'strict token alignment failed')
        doc.ents = spans
        doc.user_data['record_id'] = record.record_id
        docs[partition].append(doc)
    files = {'tokenizer.bin': tokenizer_bytes}
    signature = lambda doc: (doc.text, [(t.text, t.idx, t.whitespace_) for t in doc],
                             [(e.start_char, e.end_char, e.label_) for e in doc.ents], dict(doc.user_data))
    for partition, values in docs.items():
        require(values, 'empty export partition')
        binary = DocBin(attrs=['ORTH', 'SPACY', 'ENT_IOB', 'ENT_TYPE'], store_user_data=True)
        for doc in values:
            binary.add(doc)
        data = binary.to_bytes()
        replay = list(DocBin().from_bytes(data).get_docs(tokenizer.vocab))
        require([signature(d) for d in values] == [signature(d) for d in replay], 'serialization reload mismatch')
        files[partition.replace('_', '-') + '.spacy'] = data
    for name, data in files.items():
        with (output / name).open('xb') as stream:
            stream.write(data)
    with (output / 'admitted-records.jsonl').open('x', encoding='utf-8', newline='\n') as stream:
        for record, _ in records:
            stream.write(record.model_dump_json() + '\n')
    return {name: digest(output / name) for name in [*files, 'admitted-records.jsonl']}


def main():
    # Load pinned spaCy before exposing any optional shared-helper dependencies.
    import spacy
    from spacy.tokenizer import Tokenizer
    from spacy.vocab import Vocab

    if sys.version_info[:2] != (3, 11) or spacy.__version__ != '3.7.5':
        raise ValueError('Python 3.11 / spaCy 3.7.5 required')
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    root = Path(request['root']).resolve()
    sys.path.append(str(root / 'backend/.venv/Lib/site-packages'))
    sys.path.insert(0, str(root / 'backend'))
    from training.flood_ner.successor_preparation import (
        SCOPE, read, write_new, verify_grant, verify_binding, normalize, safe_status, safe_group_keys, digest, require, coverage)

    grant = read(request['grant'])
    model_dir = verify_grant(root, grant)
    output = Path(request['output'])
    require(output.is_dir() and not (output / 'aggregate-status.json').exists(), 'new worker destination required')
    spacy.require_cpu()  # Tokenization/serialization only, not CPU training.
    vocab = Vocab().from_disk(model_dir / 'vocab')
    tokenizer_bytes = verify_binding(root, grant['tokenizer']).read_bytes()
    tokenizer = Tokenizer(vocab).from_bytes(tokenizer_bytes, exclude=['vocab'])
    bundle = read(verify_binding(root, grant['bundle']))
    require(bundle['capability'] == grant['capability'], 'worker capability mismatch')
    require(bundle.get('historical_anchor_count') == grant['historical_anchor_count'], 'lost historical anchors')
    records, metadata, counts, languages, polarities, labels = normalize(root, bundle, SimpleNamespace(make_doc=tokenizer))
    require(counts == grant['expected_counts'] and languages == grant['expected_languages'], 'membership changed')
    if grant['capability'] == 'research_holdout':
        require(polarities == {'research_holdout': {'english_positive': 27, 'english_negative': 3,
                'taglish_positive': 27, 'taglish_negative': 3}}, 'holdout polarity quotas not met')
    write_new(output / 'admission-ledger.json', {'schema': 'lanes-scoped-admission-ledger-v1',
        'scope': SCOPE, 'grant_sha256': digest(request['grant']), 'records': [
            {'record_id': m['record']['record_id'], 'partition': m['partition'],
             'reviewed_annotation_revision': m['record']['annotation_revision'],
             'evidence': m['evidence'], 'raw_binding': m['raw_binding'],
             'occurrence_exclusions': m.get('occurrence_exclusions', []),
             'pool_kind': m['pool_kind'], 'decision': 'admitted_under_documented_limitations'}
            for m in bundle['members']]})
    write_new(output / 'partitions.json', {'schema': 'lanes-locked-partitions-v1', 'scope': SCOPE,
        'grant_sha256': digest(request['grant']), 'bundle_sha256': grant['bundle']['sha256'], 'members': metadata})
    write_new(output / 'source-only-join-metadata.json', [
        {**{k: v for k, v in r.items() if k != 'article_group'},
         'group_keys': safe_group_keys(r['group_keys'])} for r in metadata])
    write_new(output / 'coverage.json', coverage(bundle, records, metadata))
    files = serialize(records, tokenizer, tokenizer_bytes, output, grant['capability'])
    files.update({name: digest(output / name) for name in ('admission-ledger.json', 'coverage.json', 'partitions.json', 'source-only-join-metadata.json')})
    status = safe_status(dict(schema='lanes-successor-qualified-export-v1', scope=SCOPE,
        capability=grant['capability'], counts=counts, languages=languages, polarities=polarities, labels=labels,
        files=files, serialization_reload_verified=True, python_version=platform.python_version(),
        spacy_version=spacy.__version__, global_history_verified=False, accounting_verified=False,
        certified_fresh=False, training_performed=False, model_predictions_performed=False,
        model_weights_loaded=False, pipeline_components_loaded=[]))
    write_new(output / 'aggregate-status.json', status)
    print(json.dumps(status, sort_keys=True))


if __name__ == '__main__':
    main()
