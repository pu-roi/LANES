"""CPU-only diagnosis of already selected v19 checkpoints on development data.

No holdout capability, training entry point, initialization or optimizer updates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner import development_error_audit as audit
from training.flood_ner.corrected_experiment_execution import tree
from training.flood_ner.corrected_experiment_worker import cpu_runtime, load_model


def verify_request(root, request):
    audit.require(set(request) == {'schema', 'development', 'handoff', 'handoff_sha256', 'resources',
                                  'bindings', 'implementation'}, 'unexpected diagnosis fields')
    audit.require(request['schema'] == 'lanes-v19-development-diagnosis-v1', 'development-only request required')
    expected_sources = {'backend/training/flood_ner/' + n for n in (
        'v19_development_diagnosis.py', 'corrected_experiment_worker.py', 'corrected_experiment_execution.py',
        'development_error_audit.py', 'experiment_registry.py', 'annotation/schema.py',
        'annotation/validation.py', 'evaluation/contract.py')}
    audit.require({r['path'] for r in request['implementation']} == expected_sources
                  and len(request['implementation']) == len(expected_sources), 'incomplete implementation binding')
    for row in request['bindings'] + request['implementation']:
        audit.bound(root, row)
    development = audit.safe_path(root, request['development'])
    status = audit.read(development / 'aggregate-status.json')
    audit.require(status['capability'] == 'development' and status['counts'] == audit.COUNTS,
                  'holdout or altered membership forbidden')
    for name, sha in status['files'].items():
        audit.require(audit.digest(development / name) == sha, 'qualified development file changed')
    handoff = audit.safe_path(root, request['handoff'])
    audit.require(audit.digest(handoff / 'handoff-manifest.json') == request['handoff_sha256'], 'stale handoff')
    manifest = audit.read(handoff / 'handoff-manifest.json')
    audit.require({r['name'] for r in manifest['runs']} ==
                  {f'{f}-seed-{s}' for f in ('control', 'v16') for s in range(3)}, 'model roster differs')
    for run in manifest['runs']:
        audit.require(tree(audit.safe_path(handoff, run['model'])) == run['files'], 'checkpoint changed')
    package = handoff / 'package'
    for name in ('train.spacy', 'dev.spacy', 'tokenizer.bin'):
        audit.require(audit.digest(development / name) == audit.digest(package / name), 'trainer/data export differs')
    resources = audit.safe_path(root, request['resources'])
    contract = audit.read(package / 'model-contract.json')
    audit.require(tree(resources) == {r['path']: r['sha256'] for r in contract['files']}, 'pinned resources differ')
    return development, handoff, resources, manifest


def signature(doc):
    return [(t.text, t.idx, t.whitespace_) for t in doc]


def run(root, request_path, expected_sha, output):
    audit.require(audit.digest(request_path) == expected_sha, 'stale worker request')
    request = audit.read(request_path)
    development, handoff, resources, manifest = verify_request(root, request)
    audit.require(not output.exists() and output.resolve().is_relative_to(
        root / 'backend/training/flood_ner/artifacts'), 'new private destination required')
    output.mkdir()
    try:
        raw = [json.loads(line) for line in (development / 'admitted-records.jsonl').read_text(encoding='utf-8').splitlines()]
        records, metadata = audit.validate_join(raw, audit.read(development / 'partitions.json')['members'])
        metrics, comparisons, gaps = {}, [], {}
        dll_handles = cpu_runtime()
        from spacy.tokens import DocBin
        # Existing research workers use the backend's installed pure-Python
        # utilities (httpx via schema validation). No package is installed and
        # no backend/rules pipeline is imported into this neural runtime.
        backend_site = root / 'backend/.venv/Lib/site-packages'
        if backend_site.is_dir():
            sys.path.append(str(backend_site))
        from training.flood_ner.annotation.schema import AnnotationRecord
        from training.flood_ner.annotation.validation import validate_record
        saved = audit.read(handoff / 'development-selection.json')
        with (output / 'predictions.jsonl').open('x', encoding='utf-8') as ps, (output / 'errors.jsonl').open('x', encoding='utf-8') as es:
            for seed in range(3):
                run_info = next(r for r in manifest['runs'] if r['name'] == f'control-seed-{seed}')
                local = output / f'seed-{seed}'; local.mkdir()
                model = handoff / run_info['model']
                nlp, handles = load_model(root, model, handoff / 'package', resources, local)
                gold = {}
                for split in ('train', 'dev'):
                    for doc in DocBin().from_disk(development / f'{split}.spacy').get_docs(nlp.vocab):
                        rid = doc.user_data['record_id']
                        audit.require(rid not in gold and rid in records and metadata[rid]['partition'] == split,
                                      'DocBin identity mismatch')
                        row = records[rid]
                        audit.require(not validate_record(AnnotationRecord.model_validate_json(json.dumps(row)), nlp),
                                      'reference validation failed')
                        audit.require(doc.text == row['text'] and signature(doc) == signature(nlp.make_doc(row['text']))
                            and sorted((e.start_char, e.end_char, e.label_) for e in doc.ents) ==
                            sorted((e['start'], e['end'], e['label']) for e in row['entities']), 'reference/tokenization mismatch')
                        gold[rid] = doc
                audit.require(set(gold) == set(records), 'incomplete exports')
                ids = sorted(records); refs = {}; guesses = {}
                for rid, doc in zip(ids, nlp.pipe([records[r]['text'] for r in ids], batch_size=8)):
                    audit.require(doc.text == records[rid]['text'] and signature(doc) == signature(gold[rid]), 'inference tokens differ')
                    refs[rid] = [(e.start_char, e.end_char, e.label_) for e in gold[rid].ents]
                    guesses[rid] = [(e.start_char, e.end_char, e.label_) for e in doc.ents]
                    base = {'seed': seed, 'record_id': rid, 'partition': metadata[rid]['partition'],
                            'language': metadata[rid]['language'], 'text_sha256': records[rid]['text_sha256']}
                    ps.write(json.dumps({**base, 'reference': refs[rid], 'prediction': guesses[rid]}) + '\n')
                    es.write(json.dumps({**base, **audit.diagnose(refs[rid], guesses[rid], doc.text)}) + '\n')
                audit.require(len(guesses) == 405, 'inference omitted records')
                metrics[str(seed)] = {}
                for split in ('train', 'dev'):
                    selected = [r for r in ids if metadata[r]['partition'] == split]
                    metrics[str(seed)][split] = audit.score_partition({r: refs[r] for r in selected},
                        {r: guesses[r] for r in selected}, {r: metadata[r]['language'] for r in selected})
                observed = metrics[str(seed)]['dev']['overall']
                expected = next(r for r in saved['outcomes'] if r['variant'] == 'control' and r['seed'] == seed)
                delta = {k: observed[k] - expected[k] for k in ('f1', 'precision', 'recall')}
                comparisons.append({'seed': seed, 'differences': delta, 'matches_within_1e_8': all(abs(x) < 1e-8 for x in delta.values())})
                def gap(a, b):
                    return {k: a[k] - b[k] if a[k] is not None and b[k] is not None else None for k in ('f1', 'precision', 'recall')}
                train, dev = metrics[str(seed)]['train'], metrics[str(seed)]['dev']
                gaps[str(seed)] = {'overall': gap(train['overall'], dev['overall']),
                    'labels': {k: gap(train['labels'][k], dev['labels'][k]) for k in audit.LABELS},
                    'languages': {k: gap(train['languages'][k], dev['languages'][k]) for k in ('english', 'taglish')},
                    'language_labels': {lang: {label: gap(train['language_labels'][lang][label], dev['language_labels'][lang][label])
                        for label in audit.LABELS} for lang in ('english', 'taglish')}}
                print(json.dumps({'stage': 'development_seed_complete', 'seed': seed, 'records': len(guesses)}), flush=True)
                del nlp
        audit.write_new(output / 'metrics.json', metrics)
        audit.write_new(output / 'train-validation-gaps.json', gaps)
        audit.write_new(output / 'desktop-comparison.json', comparisons)
        # Raw training logs/curves were not delivered; summaries remain evidence of selected/last steps only.
        audit.write_new(output / 'training-evidence.json', {'outcomes': saved['outcomes'],
            'raw_curves_available': False, 'reason': 'authenticated handoff contains selected steps and stop summaries, no raw curves'})
        verify_request(root, request)
        status = {'schema': 'lanes-v19-development-diagnosis-result-v1', 'state': 'passed', 'records': 405,
                  'prediction_records': 1215, 'counts': audit.COUNTS, 'seeds': [0, 1, 2], 'device': 'cpu',
                  'python': sys.version.split()[0], 'spacy': __import__('spacy').__version__,
                  'desktop_metrics_reproduced': all(c['matches_within_1e_8'] for c in comparisons),
                  'holdout_accessed': False, 'training_performed': False,
                  'files': {p.name: audit.digest(p) for p in output.iterdir() if p.is_file()}}
        audit.write_new(output / 'aggregate-status.json', status)
        return status
    except BaseException as exc:
        audit.write_new(output / 'failure.json', {'state': 'failed', 'error': str(exc), 'training_performed': False})
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('checkout', 'request', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--request-sha256', required=True)
    args = p.parse_args()
    print(json.dumps(run(args.checkout.resolve(), args.request, args.request_sha256, args.output.resolve()), sort_keys=True))
