"""Compare authenticated saved development predictions. Never load a model."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner.development_error_audit import (
    COUNTS, LABELS, bound, checked_spans, diagnose, digest, read, require,
    safe_path, score_partition, validate_join, write_new)
from training.flood_ner.regularization_experiment import checked_score

SCOPE = 'saved_development_comparison_only'
PREFIX = 'experiment/runs/stronger-weight-decay-seed-0/development-check/'
IMPLEMENTATION = tuple('backend/training/flood_ner/' + name for name in (
    'regularization_comparison.py', 'development_error_audit.py', 'regularization_experiment.py',
    'annotation/schema.py', 'evaluation/contract.py'))
TEST = 'backend/tests/test_flood_ner_regularization_comparison.py'
INPUTS = {'archive', 'backup_manifest', 'publication', 'control_predictions', 'control_metrics',
          'development_status', 'prior_reviews', 'reviews', 'training_reviews', 'preservation',
          'annotation_guide', 'scope_guide'}


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def compare_metrics(actual, saved, path=''):
    """Counts/structure exact; floating arithmetic permits only 1e-12."""
    if isinstance(actual, dict):
        require(isinstance(saved, dict) and set(actual) == set(saved), 'metric fields differ: ' + path)
        for key in actual:
            compare_metrics(actual[key], saved[key], path + '/' + key)
    elif type(actual) is float:
        import math
        require(type(saved) is float and math.isfinite(actual) and math.isfinite(saved)
                and abs(actual - saved) <= 1e-12, 'metric float differs: ' + path)
    else:
        require(type(actual) is type(saved) and actual == saved, 'metric count/value differs: ' + path)


def transitions(reference, control, candidate, text):
    truth = checked_spans(reference, text)
    old = checked_spans(control, text); new = checked_spans(candidate, text)
    ofp, nfp = old - truth, new - truth
    otp, ntp = old & truth, new & truth
    result = {key: sorted(value) for key, value in {
        'introduced_FP': nfp - ofp, 'resolved_FP': ofp - nfp, 'persistent_FP': ofp & nfp,
        'gained_TP': ntp - otp, 'lost_TP': otp - ntp, 'persistent_TP': otp & ntp,
        'persistent_FN': truth - (otp | ntp)}.items()}
    require(len(nfp) - len(ofp) == len(result['introduced_FP']) - len(result['resolved_FP'])
            and len(ntp) - len(otp) == len(result['gained_TP']) - len(result['lost_TP']),
            'transition totals do not reconcile')
    return result


def components(metadata):
    """Actual connected components; overlapping group keys are not independent."""
    parent = {row['record_id']: row['record_id'] for row in metadata}
    def find(key):
        while parent[key] != key:
            parent[key] = parent[parent[key]]; key = parent[key]
        return key
    owners = {}
    for row in metadata:
        require(row['group_keys'], 'group evidence missing')
        for key in row['group_keys']:
            rid = row['record_id']
            if key in owners:
                parent[find(rid)] = find(owners[key])
            owners[key] = rid
    groups = {}
    for rid in parent:
        groups.setdefault(find(rid), []).append(rid)
    return sorted((sorted(ids) for ids in groups.values()), key=lambda ids: ids[0])


def authenticate_archive(archive, manifest, publication):
    require(digest(archive) == publication['archive']['sha256'] and
            archive.stat().st_size == publication['archive']['bytes'], 'stale candidate archive')
    require(all(manifest[key] is False for key in ('holdout_included', 'credentials_included',
                'environment_included', 'base_model_included')), 'forbidden archive capability')
    with zipfile.ZipFile(archive) as zipped:
        infos = zipped.infolist(); names = {i.filename for i in infos}
        require(len(infos) == len(names) == publication['archive_members'] and
                names == set(manifest['files']) | {'BACKUP-MANIFEST.json'}, 'archive membership differs')
        require(json.loads(zipped.read('BACKUP-MANIFEST.json')) == manifest, 'embedded manifest differs')
        for info in infos:
            path = PurePosixPath(info.filename)
            require(not any(token in info.filename.lower() for token in ('heldout', 'holdout', 'curator'))
                    or info.filename.endswith(('.py', '.py.txt')), 'holdout archive content forbidden')
            require(not path.is_absolute() and path.as_posix() == info.filename and
                    '..' not in path.parts and ':' not in info.filename and '\\' not in info.filename
                    and not info.is_dir() and stat.S_ISREG(info.external_attr >> 16), 'unsafe archive entry')
            if info.filename == 'BACKUP-MANIFEST.json':
                continue
            binding = manifest['files'][info.filename]
            value = zipped.read(info)
            require(len(value) == binding['bytes'] and hashlib.sha256(value).hexdigest() == binding['sha256'],
                    'archive member hash differs')
        # Only JSON predictions/metrics/decision are interpreted. Archived code is never imported.
        return {name: json.loads(zipped.read(name)) for name in (
            PREFIX + 'predictions.json', PREFIX + 'metrics.json', 'experiment/development-selection.json')}


def validated_baseline(rows, records, metadata):
    require(isinstance(rows, list) and len(rows) == 1215, 'all authenticated baseline rows required')
    index = {}
    for row in rows:
        require(set(row) == {'seed', 'record_id', 'partition', 'language', 'text_sha256', 'reference', 'prediction'}
                and type(row['seed']) is int and row['seed'] in (0, 1, 2), 'invalid baseline envelope')
        key = row['seed'], row['record_id']
        require(key not in index and row['record_id'] in records, 'duplicate or missing baseline identity')
        raw = records[row['record_id']]; meta = metadata[row['record_id']]
        truth = [(e['start'], e['end'], e['label']) for e in raw['entities']]
        require(row['partition'] == meta['partition'] and row['partition'] in COUNTS
                and row['language'] == meta['language'] and row['text_sha256'] == raw['text_sha256']
                and checked_spans(row['reference'], raw['text']) == checked_spans(truth, raw['text']),
                'baseline text/reference/language/partition differs')
        checked_spans(row['prediction'], raw['text'])
        index[key] = row
    require(set(index) == {(seed, rid) for seed in range(3) for rid in records}, 'baseline roster incomplete')
    return {rid: index[0, rid]['prediction'] for rid in records}


def review_entries(records, metadata, comparisons, decisions, prior):
    require(isinstance(decisions, list) and len({r['record_id'] for r in decisions}) == len(decisions),
            'duplicate review decisions')
    focused = {rid for rid, row in comparisons.items() if metadata[rid]['partition'] == 'dev'
               and (row['control']['FP'] or row['control']['FN'] or row['candidate']['FP'] or row['candidate']['FN'])}
    decisions = {row['record_id']: row for row in decisions}
    require(set(decisions) == focused, 'every affected validation passage requires one source review')
    require(len(prior) == 60 and {row['record_id'] for row in prior} ==
            {rid for rid in records if metadata[rid]['partition'] == 'dev'}, 'prior review roster differs')
    previous = {row['record_id']: row for row in prior}
    result = []
    for rid in sorted(previous):
        raw = records[rid]; old = previous[rid]
        require(old['source_sha256'] == raw['source']['text_sha256'] and old['text_sha256'] == raw['text_sha256']
                and old['reference_sha256'] == canonical_hash(raw['entities']), 'stale prior reference review')
        row = {'record_id': rid, 'source_sha256': raw['source']['text_sha256'],
            'text_sha256': raw['text_sha256'], 'reference_sha256': canonical_hash(raw['entities']),
            'annotation_changed': False, 'reviewer': 'AI-assisted silver; not human verification',
            'prior_review_sha256': canonical_hash(old)}
        if rid in decisions:
            decision = decisions[rid]
            require(set(decision) == {'record_id', 'source_sha256', 'text_sha256', 'disposition',
                    'categories', 'reason', 'evidence'} and decision['source_sha256'] == row['source_sha256']
                    and decision['text_sha256'] == row['text_sha256'] and decision['reason']
                    and decision['categories'] and decision['disposition'] in
                    ('retain_reference', 'retain_unresolved_boundary'), 'incomplete source review')
            require(decision['evidence'], 'source review requires exact evidence')
            for evidence in decision['evidence']:
                require(set(evidence) == {'start', 'end', 'text'} and type(evidence['start']) is int
                        and type(evidence['end']) is int and 0 <= evidence['start'] < evidence['end']
                        and evidence['end'] <= len(raw['source']['text'])
                        and raw['source']['text'][evidence['start']:evidence['end']] == evidence['text'],
                        'review evidence is not source exact')
            row.update(decision, review_scope='full_saved_article_and_passage')
        else:
            require(not any(comparisons[rid][family][key] for family in ('control', 'candidate')
                        for key in ('FP', 'FN')), 'unreviewed error passage')
            row.update(disposition='carry_prior_supported_reference', categories=[],
                reason='Both primary models match the unchanged reference; prior source review carried forward.',
                review_scope='unchanged_prior_review_and_prediction_check')
        result.append(row)
    return result


def analyze(records, metadata, control, candidate):
    require(set(control) == set(records) and set(candidate) == {'train', 'dev'}, 'wrong prediction roster')
    require(set(metadata) == set(records) and all(isinstance(raw.get('entities'), list)
            and raw.get('complete') is True and metadata[rid]['partition'] in COUNTS
            and metadata[rid]['language'] in ('english', 'taglish') for rid, raw in records.items()),
            'complete development references and language joins required')
    metrics = {'control': {}, 'candidate': {}}; comparisons = {}; totals = {}
    for split in COUNTS:
        chosen = {rid: raw for rid, raw in records.items() if metadata[rid]['partition'] == split}
        require(isinstance(candidate[split], dict) and set(candidate[split]) == set(chosen), 'candidate identity mismatch')
        truth = {rid: [(e['start'], e['end'], e['label']) for e in raw['entities']] for rid, raw in chosen.items()}
        languages = {rid: metadata[rid]['language'] for rid in chosen}
        old = {rid: control[rid] for rid in chosen}
        for family, guesses in (('control', old), ('candidate', candidate[split])):
            for rid, spans in guesses.items():
                checked_spans(spans, chosen[rid]['text'])
            metrics[family][split] = checked_score(score_partition(truth, guesses, languages))
        summary = Counter()
        for rid, raw in chosen.items():
            transition = transitions(truth[rid], old[rid], candidate[split][rid], raw['text'])
            row = {'record_id': rid, 'partition': split, 'language': languages[rid],
                'source_sha256': raw['source']['text_sha256'], 'text_sha256': raw['text_sha256'],
                'reference_sha256': canonical_hash(raw['entities']), 'transitions': transition,
                'prediction_changed': set(map(tuple, old[rid])) != set(map(tuple, candidate[split][rid])),
                'control': diagnose(truth[rid], old[rid], raw['text']),
                'candidate': diagnose(truth[rid], candidate[split][rid], raw['text'])}
            comparisons[rid] = row
            summary.update({key: len(value) for key, value in transition.items()})
            summary['prediction_changed_passages'] += int(row['prediction_changed'])
            summary['error_either_passages'] += int(any(row[f][k] for f in ('control', 'candidate') for k in ('FP', 'FN')))
        totals[split] = dict(summary)
    return metrics, comparisons, totals


def preserve(root, ledger):
    for name, item in ledger['files'].items():
        require(not any(token in name.lower() for token in ('holdout', 'heldout', 'curator'))
                or name.endswith(('.py', '.py.txt')), 'holdout content cannot enter preservation hashes')
        path = safe_path(root, name)
        require(digest(path) == item['sha256'] and path.stat().st_size == item['bytes'], 'protected file changed')
    for name, item in ledger['holdout_metadata_only'].items():
        # No contents, directory scanning or model loading for completed holdout artifacts.
        current = safe_path(root, name).stat()
        require(current.st_size == item['bytes'] and current.st_mtime_ns == item['mtime_ns'],
                'holdout metadata changed')
    return {'hashed_files': len(ledger['files']), 'holdout_stat_only': len(ledger['holdout_metadata_only'])}


@contextmanager
def exclusive(path):
    with path.open('x', encoding='utf-8') as stream:
        stream.write('development comparison; no execution capabilities')
    try:
        yield
    finally:
        path.unlink()


def run(root, request_path, expected_sha, output):
    root = Path(root).resolve(); output = Path(output).absolute()
    artifacts = root / 'backend/training/flood_ner/artifacts'
    require(artifacts.is_dir() and output.parent.resolve() == artifacts.resolve() and not output.exists(),
            'new private destination required')
    safe_path(root, output.relative_to(root).as_posix())
    require(digest(request_path) == expected_sha, 'stale comparison request')
    request = read(request_path)
    require(set(request) == {'schema', 'scope', 'permissions', 'inputs', 'implementation', 'tests',
                'development_directory'} and request['schema'] == 'lanes-regularization-comparison-v1'
            and request['scope'] == SCOPE and request['permissions'] ==
                dict.fromkeys(('network', 'model_loading', 'inference', 'training', 'holdout', 'git', 'upload'), False)
            and all(type(v) is bool for v in request['permissions'].values()), 'comparison-only capability required')
    require(set(request['inputs']) == INPUTS and len(request['implementation']) == len(IMPLEMENTATION)
            and {x['path'] for x in request['implementation']} == set(IMPLEMENTATION)
            and request['tests']['path'] == TEST, 'input/source/test bindings incomplete')
    for binding in [*request['inputs'].values(), *request['implementation'], request['tests']]:
        require(not any(token in binding['path'].lower() for token in ('heldout', 'holdout', 'curator')),
                'holdout input forbidden')
        bound(root, binding)
    paths = {key: safe_path(root, b['path']) for key, b in request['inputs'].items()}
    status = read(paths['development_status'])
    require(status['capability'] == 'development' and status['counts'] == COUNTS, 'development inputs only')
    development = safe_path(root, request['development_directory'])
    for name, sha in status['files'].items():
        bound(root, {'path': (development / name).relative_to(root).as_posix(), 'sha256': sha})
    raw = [json.loads(line) for line in (development / 'admitted-records.jsonl').read_text(encoding='utf-8').splitlines()]
    metadata = read(development / 'partitions.json')['members']
    records, index = validate_join(raw, metadata)
    from training.flood_ner.annotation.schema import AnnotationRecord
    for row in raw:
        parsed = AnnotationRecord.model_validate_json(json.dumps(row))
        require(parsed.annotation_profile == 'location-only-v1' and parsed.source.origin == 'captured_original'
                and not parsed.facts and not parsed.relations and parsed.split in COUNTS, 'non-development reference')
        checked_spans([(e.start, e.end, e.label) for e in parsed.entities], parsed.text)
        require(all(parsed.text[e.start:e.end] == e.text for e in parsed.entities), 'entity text differs')
    publication = read(paths['publication']); manifest = read(paths['backup_manifest'])
    require(digest(paths['backup_manifest']) == publication['backup_manifest_sha256'], 'stale backup manifest')
    ledger = read(paths['preservation']); preserve(root, ledger)
    with exclusive(artifacts / 'regularization-comparison-active.lock'):
        output.mkdir()
        try:
            values = authenticate_archive(paths['archive'], manifest, publication)
            baseline_rows = [json.loads(line) for line in paths['control_predictions'].read_text(encoding='utf-8').splitlines()]
            control = validated_baseline(baseline_rows, records, index)
            metrics, rows, totals = analyze(records, index, control, values[PREFIX + 'predictions.json'])
            for split in COUNTS:
                compare_metrics(metrics['candidate'][split], values[PREFIX + 'metrics.json'][split])
                compare_metrics(metrics['control'][split], read(paths['control_metrics'])['0'][split])
            reviews = review_entries(records, index, rows, read(paths['reviews']),
                [json.loads(line) for line in paths['prior_reviews'].read_text(encoding='utf-8').splitlines()])
            training_reviews = read(paths['training_reviews'])
            require(len({x['record_id'] for x in training_reviews}) == len(training_reviews), 'duplicate training review')
            for review in training_reviews:
                row = records[review['record_id']]
                require(index[review['record_id']]['partition'] == 'train' and review['text_sha256'] == row['text_sha256']
                        and review['source_sha256'] == row['source']['text_sha256'] and review['reason']
                        and review['annotation_changed'] is False, 'invalid training review')
            gap_tables = {family: metric_gaps(m['train'], m['dev']) for family, m in metrics.items()}
            private_groups = {split: components([row for row in metadata if row['partition'] == split]) for split in COUNTS}
            concentration = {}
            for split, groups in private_groups.items():
                error_counts = [sum(any(rows[rid][f][k] for f in ('control', 'candidate') for k in ('FP', 'FN'))
                                    for rid in group) for group in groups]
                concentration[split] = {'connected_groups': len(groups),
                    'passages_per_group': sorted(map(len, groups), reverse=True),
                    'error_groups': sum(n > 0 for n in error_counts), 'error_passages_per_group': sorted(error_counts, reverse=True)}
            write_new(output / 'metrics.json', metrics)
            write_new(output / 'gaps.json', gap_tables)
            write_new(output / 'groups.json', private_groups)
            write_new(output / 'training-review.json', training_reviews)
            with (output / 'comparisons.jsonl').open('x', encoding='utf-8', newline='\n') as stream:
                for row in rows.values():
                    stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
            with (output / 'validation-review.jsonl').open('x', encoding='utf-8', newline='\n') as stream:
                for row in reviews:
                    stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
            aggregate = {'schema': 'lanes-regularization-comparison-status-v1', 'scope': SCOPE,
                'counts': COUNTS, 'primary_seed': 0, 'retained': 'v19_corrected_control',
                'transitions': totals, 'group_concentration': concentration,
                'validation_dispositions': dict(Counter(row['disposition'] for row in reviews)),
                'focused_validation_passages': sum(r['review_scope'] == 'full_saved_article_and_passage' for r in reviews),
                'focused_source_articles': len({r['source_sha256'] for r in reviews if r['review_scope'] == 'full_saved_article_and_passage'}),
                'training_passages_reviewed': len(training_reviews), 'model_loading': False, 'inference': False,
                'training': False, 'holdout_accessed': False, 'annotations_changed': False,
                'preserved': preserve(root, ledger)}
            write_new(output / 'aggregate.json', aggregate)
            write_new(output / 'manifest.json', {'request_sha256': expected_sha,
                'inputs': request['inputs'], 'implementation': request['implementation'], 'tests': request['tests'],
                'files': {p.name: digest(p) for p in output.iterdir() if p.is_file()}})
            return aggregate
        except BaseException as error:
            write_new(output / 'failure.json', {'type': type(error).__name__, 'reason': str(error),
                       'model_loading': False, 'inference': False, 'training': False, 'holdout_accessed': False})
            raise


def metric_gaps(train, dev):
    def difference(a, b):
        return {key: a[key] - b[key] if a[key] is not None and b[key] is not None else None
                for key in ('precision', 'recall', 'f1')}
    return {'overall': difference(train['overall'], dev['overall']),
        'labels': {label: difference(train['labels'][label], dev['labels'][label]) for label in sorted(LABELS)},
        'languages': {language: difference(train['languages'][language], dev['languages'][language])
                      for language in ('english', 'taglish')},
        'language_labels': {language: {label: difference(train['language_labels'][language][label],
                dev['language_labels'][language][label]) for label in sorted(LABELS)}
                for language in ('english', 'taglish')}}


def install_guards():
    def audit(event, args):
        if event in {'socket.connect', 'socket.bind', 'socket.sendto', 'socket.getaddrinfo',
                     'subprocess.Popen', 'os.system', 'os.posix_spawn'} or event == 'import' and \
                args[0].split('.')[0] in {'spacy', 'torch', 'thinc', 'cupy'}:
            raise RuntimeError('saved comparison forbids models, inference, network and processes')
    sys.addaudithook(audit)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('checkout', 'request', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--request-sha256', required=True)
    args = parser.parse_args()
    install_guards()
    print(json.dumps(run(args.checkout, args.request, args.request_sha256, args.output), sort_keys=True))


if __name__ == '__main__':
    main()
