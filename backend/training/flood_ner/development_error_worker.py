"""Qualified CPU inference on development references only. No training entry point."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import platform
import sys


def token_signature(doc):
    return [(t.text, t.idx, t.whitespace_) for t in doc]


def main():
    import spacy
    import torch
    from spacy.scorer import Scorer
    from spacy.tokens import DocBin
    from spacy.training import Example

    if sys.version_info[:2] != (3, 11) or spacy.__version__ != '3.7.5':
        raise ValueError('qualified Python 3.11 / spaCy 3.7.5 required')
    root, output, request_hash = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3]
    sys.path.append(str(root / 'backend/.venv/Lib/site-packages'))
    sys.path.insert(0, str(root / 'backend'))
    from training.flood_ner import development_error_audit as audit
    from training.flood_ner.annotation.schema import AnnotationRecord
    from training.flood_ner.annotation.validation import validate_record
    audit.require(audit.digest(output / 'request.json') == request_hash, 'stale worker request')
    request = audit.read(output / 'request.json')
    paths, development, model = audit.verify_request(root, request)
    audit.require((root / 'backend/training/flood_ner/artifacts/development-error-audit-active.lock')
                  .read_text(encoding='utf-8') == str(output), 'worker not the active audit')
    backup = audit.read(paths['backup_manifest'])
    audit.verify_archive(paths['archive'], backup)
    audit.extract_models(paths['archive'], output)
    raw_records = [json.loads(line) for line in (development / 'admitted-records.jsonl').read_text(encoding='utf-8').splitlines()]
    records, rows = audit.validate_join(raw_records, audit.read(development / 'partitions.json')['members'])
    spacy.require_cpu()
    torch.set_num_threads(2)
    registry = root / 'backend/training/flood_ner/experiment_registry.py'
    spec = importlib.util.spec_from_file_location('lanes_development_audit_registry', registry)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    contract = audit.read(paths['model_contract'])
    contract['model_dir'] = str(model)
    audit.write_new(output / 'runtime-model-contract.json', contract)
    contract_path = output / 'runtime-model-contract.json'
    tokenizer_bytes = (development / 'tokenizer.bin').read_bytes()
    expected_tokenizer = audit.digest(development / 'tokenizer.bin')
    desktop = audit.read(paths['desktop_results'])
    metrics, comparison, model_hashes = {}, [], {}
    with (output / 'predictions.jsonl').open('x', encoding='utf-8', newline='\n') as predictions_stream, \
         (output / 'errors.jsonl').open('x', encoding='utf-8', newline='\n') as errors_stream:
        for seed in (0, 1, 2):
            checkpoint = output / f'models/seed-{seed}'
            before = {p.relative_to(checkpoint).as_posix(): audit.digest(p) for p in checkpoint.rglob('*') if p.is_file()}
            nlp = spacy.load(checkpoint, config={'nlp': {'tokenizer': {
                'model_manifest': str(contract_path), 'manifest_sha256': audit.digest(contract_path),
                'tokenizer_file': str(development / 'tokenizer.bin')}}})
            audit.require(nlp.pipe_names == ['ner'] and set(nlp.get_pipe('ner').labels) == audit.LABELS,
                          'selected six-class NER pipeline required')
            audit.require(nlp.tokenizer.to_bytes(exclude=['vocab']) == tokenizer_bytes, 'loaded tokenizer bytes differ')
            audit.require(nlp.meta['lanes_initialization']['optimizer_updates'] == 0, 'unexpected initialization metadata')
            gold = {}
            for split in ('train', 'dev'):
                for doc in DocBin().from_bytes((development / f'{split}.spacy').read_bytes()).get_docs(nlp.vocab):
                    rid = doc.user_data['record_id']
                    audit.require(rid not in gold and rid in records and rows[rid]['partition'] == split,
                                  'DocBin identity/partition mismatch')
                    raw = records[rid]
                    record = AnnotationRecord.model_validate_json(json.dumps(raw))
                    errors = validate_record(record, nlp)
                    audit.require(not errors, 'shared source/schema/span validation failed')
                    expected = sorted((e['start'], e['end'], e['label']) for e in raw['entities'])
                    audit.require(doc.text == raw['text'] and expected == sorted(
                        (e.start_char, e.end_char, e.label_) for e in doc.ents), 'DocBin reference mismatch')
                    audit.require(token_signature(doc) == token_signature(nlp.make_doc(raw['text'])), 'tokenization differs')
                    gold[rid] = doc
            audit.require(set(gold) == set(records), 'DocBin membership incomplete')
            ids = sorted(records)
            refs, guesses, examples = {}, {}, {'train': [], 'dev': []}
            for rid, predicted in zip(ids, nlp.pipe((records[rid]['text'] for rid in ids), batch_size=8)):
                audit.require(predicted.text == records[rid]['text'] and
                              token_signature(predicted) == token_signature(gold[rid]), 'inference changed text/tokens')
                refs[rid] = [(e.start_char, e.end_char, e.label_) for e in gold[rid].ents]
                guesses[rid] = [(e.start_char, e.end_char, e.label_) for e in predicted.ents]
                errors = audit.diagnose(refs[rid], guesses[rid], predicted.text)
                row = {'seed': seed, 'record_id': rid, 'partition': rows[rid]['partition'],
                       'language': rows[rid]['language'], 'text_sha256': records[rid]['text_sha256']}
                predictions_stream.write(json.dumps({**row, 'reference': refs[rid], 'prediction': guesses[rid]}, ensure_ascii=False) + '\n')
                errors_stream.write(json.dumps({**row, **errors}, ensure_ascii=False) + '\n')
                examples[rows[rid]['partition']].append(Example(predicted, gold[rid]))
            audit.require(len(guesses) == 405, 'inference membership incomplete')
            metrics[str(seed)] = {}
            for split in ('train', 'dev'):
                selected = [rid for rid in ids if rows[rid]['partition'] == split]
                report = audit.score_partition({r: refs[r] for r in selected}, {r: guesses[r] for r in selected},
                                               {r: rows[r]['language'] for r in selected})
                official = Scorer.score_spans(examples[split], 'ents')
                audit.require(abs(report['overall']['f1'] - official['ents_f']) < 1e-12, 'strict scoring disagreement')
                metrics[str(seed)][split] = report
            observed = metrics[str(seed)]['dev']['overall']
            recorded = next(row for row in desktop['seeds'] if row['seed'] == seed)
            differences = {name: observed[key] - recorded[name] for key, name in
                           [('f1', 'dev_f1'), ('precision', 'dev_precision'), ('recall', 'dev_recall')]}
            comparison.append({'seed': seed, 'recorded': {k: recorded[k] for k in differences},
                               'cpu': {name: observed[key] for key, name in
                                       [('f1', 'dev_f1'), ('precision', 'dev_precision'), ('recall', 'dev_recall')]},
                               'differences': differences, 'matches_within_1e_8': all(abs(v) < 1e-8 for v in differences.values())})
            audit.require(before == {p.relative_to(checkpoint).as_posix(): audit.digest(p)
                                      for p in checkpoint.rglob('*') if p.is_file()}, 'checkpoint bytes changed')
            model_hashes[str(seed)] = before
            print(json.dumps({'stage': 'seed_audit_complete', 'seed': seed, 'records': 405}), flush=True)
            del nlp
    audit.write_new(output / 'metrics.json', metrics)
    audit.write_new(output / 'desktop-comparison.json', comparison)
    audit.write_new(output / 'checkpoint-hashes.json', model_hashes)
    audit.verify_request(root, request)
    status = {'schema': 'lanes-development-error-audit-result-v1', 'counts': audit.COUNTS,
              'languages': audit.LANGUAGES, 'seeds': [0, 1, 2], 'primary_seed': 0, 'prediction_records': 1215,
              'python_version': platform.python_version(), 'spacy_version': spacy.__version__,
              'device': 'cpu', 'tokenizer_sha256': expected_tokenizer,
              'desktop_metrics_reproduced': all(r['matches_within_1e_8'] for r in comparison),
              'training_performed': False, 'holdout_accessed': False, 'optimizer_updates': 0,
              'files': {name: audit.digest(output / name) for name in
                        ('predictions.jsonl', 'errors.jsonl', 'metrics.json', 'desktop-comparison.json', 'checkpoint-hashes.json')}}
    audit.safe_status(status)
    audit.write_new(output / 'aggregate-status.json', status)
    print(json.dumps(status, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
