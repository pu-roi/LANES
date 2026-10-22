"""Offline development-only inference audit; never trains or opens a holdout."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import zipfile

LABELS = frozenset({'BARANGAY', 'CITY', 'LANDMARK', 'LOCAL_AREA', 'PROVINCE', 'ROAD'})
SCOPE = 'existing_development_error_audit_only'
COUNTS = {'train': 345, 'dev': 60}
LANGUAGES = {'train': {'english': 170, 'taglish': 175}, 'dev': {'english': 38, 'taglish': 22}}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def safe_path(root, relative):
    relative = PurePosixPath(relative)
    require(not relative.is_absolute() and '..' not in relative.parts and ':' not in str(relative)
            and '\\' not in str(relative), 'unsafe relative path')
    root = Path(root).resolve()
    path = root.joinpath(*relative.parts)
    require(path.resolve().is_relative_to(root), 'path escapes root')
    require(not any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                    for p in (path, *path.parents) if p != root.parent), 'linked path forbidden')
    return path


def bound(root, binding):
    require(set(binding) == {'path', 'sha256'}, 'exact hash binding required')
    path = safe_path(root, binding['path'])
    require(path.is_file() and digest(path) == binding['sha256'], 'stale or missing input hash')
    return path


def verify_request(root, request):
    require(set(request) == {'schema', 'scope', 'capability', 'bindings', 'development_directory',
                            'model_directory', 'implementation'}, 'unexpected audit request fields')
    require(request['schema'] == 'lanes-development-error-audit-v1' and request['scope'] == SCOPE
            and request['capability'] == 'development', 'development-only audit scope required')
    names = {'archive', 'backup_manifest', 'development_status', 'model_contract', 'desktop_results'}
    require(set(request['bindings']) == names, 'audit bindings incomplete')
    paths = {name: bound(root, item) for name, item in request['bindings'].items()}
    expected = {'backend/training/flood_ner/' + name for name in
                ('development_error_audit.py', 'development_error_worker.py', 'experiment_registry.py',
                 'annotation/schema.py', 'annotation/validation.py', 'evaluation/contract.py')}
    require({b['path'] for b in request['implementation']} == expected
            and len(request['implementation']) == len(expected), 'audit implementation bindings incomplete')
    for item in request['implementation']:
        bound(root, item)
    status = read(paths['development_status'])
    require(status.get('capability') == 'development' and status.get('counts') == COUNTS
            and status.get('languages') == LANGUAGES, 'wrong development export')
    development = safe_path(root, request['development_directory'])
    required = {'admitted-records.jsonl', 'partitions.json', 'train.spacy', 'dev.spacy', 'tokenizer.bin',
                'admission-ledger.json', 'source-only-join-metadata.json', 'coverage.json'}
    require(set(status['files']) == required, 'unexpected development export capability')
    for name, sha in status['files'].items():
        bound(root, {'path': str((development / name).relative_to(Path(root).resolve())).replace('\\', '/'),
                     'sha256': sha})
    model = safe_path(root, request['model_directory'])
    contract = read(paths['model_contract'])
    require(contract.get('model') == 'tl_calamancy_md' and contract.get('version') == '0.1.0'
            and contract.get('revision') == '51a40433059d8a2c25b98a48eca854f8789a491a'
            and len(contract.get('files', [])) == 23, 'pinned base model contract required')
    require(len({r['path'] for r in contract['files']}) == 23, 'duplicate base model paths')
    for row in contract['files']:
        path = safe_path(model, row['path'])
        require(path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], 'base model hash mismatch')
    require({p.relative_to(model).as_posix() for p in model.rglob('*') if p.is_file()}
            == {r['path'] for r in contract['files']}, 'unmanifested base model files')
    return paths, development, model


def verify_archive(archive, manifest):
    """Authenticate every member, but extract selected models only in a new output."""
    files = manifest['files']
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        require(len(names) == len(set(names)) and set(names) == set(files) | {'checkpoint-backup-manifest.json'},
                'archive manifest membership mismatch')
        require(json.loads(zipped.read('checkpoint-backup-manifest.json')) == manifest, 'archive manifest differs')
        for name, row in files.items():
            parts = PurePosixPath(name)
            require(not parts.is_absolute() and '..' not in parts.parts and '\\' not in name and ':' not in name
                    and 'holdout' not in name.lower() and not name.endswith(('.py', '.exe')),
                    'unsafe or forbidden archive member')
            sha, size = hashlib.sha256(), 0
            with zipped.open(name) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    sha.update(chunk)
                    size += len(chunk)
            require(sha.hexdigest() == row['sha256'] and size == row['bytes'], 'archive member hash mismatch')
        for seed in (0, 1, 2):
            prefix = checkpoint_prefix(seed)
            require(sum(n.startswith(prefix) for n in names) == 11
                    and {prefix + n for n in ('config.cfg', 'meta.json', 'tokenizer', 'ner/model')} <= set(names),
                    'incomplete selected checkpoint')


def checkpoint_prefix(seed):
    return f'backend/training/flood_ner/artifacts/successor-training-seed-{seed}-v16-retry1/selected-checkpoint/model/'


def extract_models(archive, output):
    with zipfile.ZipFile(archive) as zipped:
        for seed in (0, 1, 2):
            prefix = checkpoint_prefix(seed)
            for name in zipped.namelist():
                if name.startswith(prefix):
                    path = safe_path(output, f'models/seed-{seed}/' + name[len(prefix):])
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with path.open('xb') as target, zipped.open(name) as stream:
                        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                            target.write(chunk)


def validate_join(raw_records, metadata):
    require(len(raw_records) == 405 and len(metadata) == 405, '405 development references required')
    records = {r['record_id']: r for r in raw_records}
    rows = {r['record_id']: r for r in metadata}
    require(len(records) == len(raw_records) and len(rows) == len(metadata) and set(rows) == set(records),
            'missing or duplicate record identities')
    groups, counts = {}, {split: {language: 0 for language in ('english', 'taglish')} for split in COUNTS}
    for rid, raw in records.items():
        row = rows[rid]
        require('entities' in raw and isinstance(raw['entities'], list) and raw.get('complete') is True
                and raw.get('review_status') == 'accepted' and raw.get('annotation_profile') == 'location-only-v1',
                'incomplete reference is not a negative')
        require(row['partition'] in COUNTS and raw.get('split') != 'test', 'holdout reference forbidden')
        require(row['language'] in ('english', 'taglish') and row['language'] == raw['passage_language'],
                'language join mismatch')
        require(row['passage_sha256'] == raw['text_sha256'] == hashlib.sha256(raw['text'].encode()).hexdigest()
                and row['source_sha256'] == raw['source']['text_sha256']
                and row['passage_start'] == raw['passage_start'] and row['passage_end'] == raw['passage_end']
                and row['is_negative'] == (len(raw['entities']) == 0), 'reference metadata mismatch')
        require(raw['source']['text'][raw['passage_start']:raw['passage_end']] == raw['text'], 'source text mismatch')
        counts[row['partition']][row['language']] += 1
        for key in row['group_keys']:
            require(key not in groups or groups[key] == row['partition'], 'fragmented development group')
            groups[key] = row['partition']
    require(counts == LANGUAGES, 'development membership/language counts changed')
    return records, rows


def checked_spans(spans, text):
    require(isinstance(spans, list), 'explicit span list required')
    result = []
    for span in spans:
        require(isinstance(span, (tuple, list)) and len(span) == 3 and type(span[0]) is int
                and type(span[1]) is int and 0 <= span[0] < span[1] <= len(text) and span[2] in LABELS,
                'invalid Unicode character span')
        result.append(tuple(span))
    require(len(set(result)) == len(result), 'duplicate span')
    ordered = sorted(result)
    require(all(a[1] <= b[0] for a, b in zip(ordered, ordered[1:])), 'overlapping spans')
    return set(result)


def diagnose(reference, predicted, text):
    truth, guess = checked_spans(reference, text), checked_spans(predicted, text)
    fp, fn = sorted(guess - truth), sorted(truth - guess)
    # Overlap links are diagnostic, not mutually exclusive or a change to strict scoring.
    links = []
    for gold in fn:
        for prediction in fp:
            if max(gold[0], prediction[0]) < min(gold[1], prediction[1]):
                kind = ('wrong_type' if gold[:2] == prediction[:2] else
                        'wrong_boundary' if gold[2] == prediction[2] else 'wrong_boundary_and_type')
                links.append({'reference': gold, 'prediction': prediction, 'kind': kind})
    return {'TP': len(truth & guess), 'FP': len(fp), 'FN': len(fn), 'false_positives': fp,
            'false_negatives': fn, 'overlap_links': links,
            'missed_without_overlap': [s for s in fn if not any(tuple(r['reference']) == s for r in links)],
            'spurious_without_overlap': [s for s in fp if not any(tuple(r['prediction']) == s for r in links)]}


def score_partition(references, predictions, languages):
    from training.flood_ner.evaluation.contract import score_exact_spans
    result = score_exact_spans(references, predictions, languages)
    slices = [result['labels'], *result['language_labels'].values()]
    for labels in slices:
        for row in labels.values():
            row['supported'] = row['reference_spans'] > 0
            if not row['supported']:
                row['f1'] = None
        valid = [v['f1'] for v in labels.values() if v['supported']]
        # Macro denominator is explicitly the number of labels with reference support.
        macro = {'supported_labels': len(valid), 'f1': sum(valid) / len(valid) if valid else None}
        if labels is result['labels']:
            result['macro'] = macro
        else:
            lang = next(lang for lang, value in result['language_labels'].items() if value is labels)
            result.setdefault('language_macro', {})[lang] = macro
    return result


def safe_status(value):
    fields = {'schema', 'counts', 'languages', 'seeds', 'primary_seed', 'prediction_records', 'python_version',
              'spacy_version', 'device', 'tokenizer_sha256', 'desktop_metrics_reproduced', 'training_performed',
              'holdout_accessed', 'optimizer_updates', 'files'}
    require(set(value) == fields and value['schema'] == 'lanes-development-error-audit-result-v1',
            'aggregate allowlist mismatch')
    require(value['counts'] == COUNTS and value['languages'] == LANGUAGES and value['seeds'] == [0, 1, 2]
            and all(type(seed) is int for seed in value['seeds'])
            and type(value['primary_seed']) is int and value['primary_seed'] == 0
            and type(value['prediction_records']) is int and value['prediction_records'] == 1215,
            'aggregate counts mismatch')
    require(value['training_performed'] is False and value['holdout_accessed'] is False
            and type(value['optimizer_updates']) is int and value['optimizer_updates'] == 0
            and value['device'] == 'cpu' and type(value['desktop_metrics_reproduced']) is bool,
            'forbidden audit capability')
    require(isinstance(value['python_version'], str) and isinstance(value['tokenizer_sha256'], str)
            and re.fullmatch(r'3\.11\.\d+', value['python_version']) and value['spacy_version'] == '3.7.5'
            and re.fullmatch(r'[a-f0-9]{64}', value['tokenizer_sha256']), 'invalid aggregate runtime/hash')
    require(set(value['files']) == {'predictions.jsonl', 'errors.jsonl', 'metrics.json',
                                   'desktop-comparison.json', 'checkpoint-hashes.json'}
            and all(isinstance(v, str) and re.fullmatch(r'[a-f0-9]{64}', v) for v in value['files'].values()),
            'unsafe aggregate file fields')
    return value


def run(root, request_path, interpreter, output):
    root, output = Path(root).resolve(), Path(output).absolute()
    request = read(request_path)
    verify_request(root, request)
    artifacts = root / 'backend/training/flood_ner/artifacts'
    require(output.resolve().is_relative_to(artifacts) and not output.exists(), 'new private artifact output required')
    safe_path(root, output.relative_to(root).as_posix())
    require(Path(interpreter).is_file(), 'explicit existing qualified interpreter required')
    with (artifacts / 'development-error-audit-active.lock').open('x', encoding='utf-8') as lock:
        lock.write(str(output))
    try:
        output.mkdir()
        write_new(output / 'request.json', request)
        binding = digest(output / 'request.json')
        worker = root / 'backend/training/flood_ner/development_error_worker.py'
        # No historical launcher, training subprocess, network or installation path.
        with (output / 'worker.stdout').open('xb') as stdout, (output / 'worker.stderr').open('xb') as stderr:
            try:
                result = subprocess.run([str(Path(interpreter).resolve()), '-I', '-B', str(worker), str(root),
                                         str(output), binding], cwd=root, stdout=stdout, stderr=stderr,
                                        check=False, timeout=1200)
            except subprocess.TimeoutExpired as exc:
                write_new(output / 'worker-outcome.json', {'state': 'timeout', 'training_performed': False})
                raise ValueError('CPU audit timed out; preserved worker logs contain partial progress') from exc
        write_new(output / 'worker-outcome.json', {'returncode': result.returncode, 'training_performed': False})
        require(result.returncode == 0, 'CPU audit failed; preserved worker logs contain the blocker')
        return safe_status(read(output / 'aggregate-status.json'))
    finally:
        (artifacts / 'development-error-audit-active.lock').unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('checkout', 'request', 'python', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.checkout, args.request, args.python, args.output), sort_keys=True))


if __name__ == '__main__':
    main()
