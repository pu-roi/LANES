"""Offline, hash-bound successor admission. Never starts training or collection.

The limited-provenance protocol is deliberately distinct from certified freshness.
The caller must keep research-holdout inputs inside the isolated curator context.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

SCOPE = 'limited_provenance_silver_research'
GATES = frozenset({'source_use', 'publication', 'language', 'history', 'exposure', 'grouping'})
PARTITIONS = {'development': ('train', 'dev'), 'research_holdout': ('research_holdout',)}
IMPLEMENTATIONS = ('successor_preparation.py', 'successor_export_worker.py', 'successor_training.py')
FROZEN_TOKENIZER = '3f666f61346b7196d931ab9781a3d83f41d688e24b298e8e494b3d92c384a588'
PLACE_LABELS = frozenset({'ROAD', 'LANDMARK', 'LOCAL_AREA', 'BARANGAY', 'CITY', 'PROVINCE'})
THEMES = frozenset({'facilities-institutions', 'misleading-names-time-common-words',
    'geographic-type-ambiguity', 'locality-designators', 'compound-crossing-roads',
    'project-asset-names', 'shared-identifiers', 'short-codes', 'unclassified_metadata'})
ROLES = frozenset({'observed_flooding', 'recovery', 'warning_forecast', 'prevention_project',
                   'adjacent_hazard', 'unrelated', 'unclassified_metadata'})


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write('\n')


def inside(root, relative):
    root = Path(root).resolve()
    relative = Path(relative)
    require(not relative.is_absolute() and '..' not in relative.parts, 'relative package path required')
    path = root / relative
    require(path.resolve().is_relative_to(root), 'path escapes checkout')
    # A checked-out file must not secretly redirect the binding through a link.
    for parent in (path, *path.parents):
        if parent == root:
            break
        require(not parent.is_symlink() and not getattr(parent, 'is_junction', lambda: False)(),
                'linked package path rejected')
    return path


def verify_binding(root, binding):
    require(isinstance(binding, dict) and set(binding) == {'path', 'sha256'}, 'invalid file binding')
    path = inside(root, binding['path'])
    require(path.is_file() and digest(path) == binding['sha256'], 'missing or stale file binding')
    return path


def binding(root, path):
    path = Path(path).resolve()
    return {'path': path.relative_to(Path(root).resolve()).as_posix(), 'sha256': digest(path)}


def verify_grant(root, grant):
    require(grant.get('schema') == 'lanes-successor-preparation-grant-v1'
            and grant.get('scope') == SCOPE, 'actual preparation grant required')
    capability = grant.get('capability')
    require(capability in PARTITIONS, 'invalid capability')
    auth = read(verify_binding(root, grant['task_authorization']))
    require(auth.get('schema') == 'lanes-successor-task-authorization-v1' and auth.get('scope') == SCOPE,
            'task authorization mismatch')
    require(all(auth.get(k) is False for k in ('network_allowed', 'training_allowed', 'inference_allowed',
                                              'upload_allowed', 'commit_allowed', 'push_allowed')),
            'scope exceeds offline preparation')
    require({'admit_in_new_package', 'freeze_grouped_partitions', 'serialize_and_reload'}
            <= set(auth.get('authorized_actions', [])), 'admission not authorized')
    require(grant['protocol'] == auth['original_protocol'], 'protocol binding mismatch')
    verify_binding(root, grant['protocol'])
    for item in grant['implementation']:
        require(item['path'] == 'backend/training/flood_ner/' + Path(item['path']).name,
                'implementation must bind actual public helper')
        verify_binding(root, item)
    require({Path(i['path']).name for i in grant['implementation']} >= set(IMPLEMENTATIONS),
            'implementation bindings incomplete')
    evidence = read(verify_binding(root, grant['test_evidence']))
    require(evidence.get('implementation') == grant['implementation'] and evidence.get('failures') == 0
            and evidence.get('passed', 0) > 0 and evidence.get('constructed_only') is True,
            'missing matching passing test evidence')
    require(bool(evidence.get('test_files')), 'test source bindings missing')
    for item in evidence['test_files']:
        require(item['path'].startswith('backend/tests/'), 'test binding outside research tests')
        verify_binding(root, item)
    require(grant.get('global_history_verified') is False and grant.get('accounting_verified') is False
            and grant.get('certified_fresh') is False, 'limitations must remain explicit')
    verify_binding(root, grant['bundle'])
    join = read(verify_binding(root, grant['cross_partition_evidence']))
    require(join.get('schema') == 'lanes-successor-cross-partition-preflight-v1'
            and join.get('records') == 465 and join.get('partitions') == auth['expected_counts']
            and join.get('group_separation_verified') is True,
            'combined partition verification missing')
    require(grant['bundle'] in join.get('input_bundles', []) and len(join['input_bundles']) == 2,
            'stale combined membership')
    for item in join['input_bundles']:
        verify_binding(root, item)
    verify_binding(root, grant['tokenizer'])
    require(grant['tokenizer']['sha256'] == FROZEN_TOKENIZER, 'wrong frozen tokenizer')
    verify_binding(root, grant['protected_input_manifest'])
    manifest = read(verify_binding(root, grant['model_manifest']))
    require(manifest.get('revision') == '51a40433059d8a2c25b98a48eca854f8789a491a', 'wrong model revision')
    model_dir = inside(root, grant['model_directory'])
    files = manifest.get('files', [])
    require(len(files) == 23 and len({f['path'] for f in files}) == 23, 'incomplete pinned model')
    for item in files:
        path = inside(model_dir, item['path'])
        require(path.is_file() and digest(path) == item['sha256'], 'model file changed')
    require(set(grant['expected_counts']) == set(PARTITIONS[capability]), 'wrong partition capability')
    require(grant['expected_counts'] == {p: auth['expected_counts'][p] for p in PARTITIONS[capability]},
            'expected membership differs from task authorization')
    require(grant['historical_anchor_count'] == 280, 'historical fitted anchors required')
    return model_dir


def safe_group_keys(keys):
    return sorted(k.split(':', 1)[0] + '_sha256:' + hashlib.sha256(k.split(':', 1)[1].encode('utf-8')).hexdigest()
                  if k.startswith('url:') or '://' in k else k for k in keys)


def publication_day_projection(printed_basis, captured_text):
    """Represent an exact captured calendar date; do not invent its timezone/time.

    SourceCapture requires a zoned datetime. UTC midnight here is explicitly a
    date-only projection for the eligibility window, never a publication instant.
    The unmodified printed basis and this distinction must remain in the ledger.
    """
    import re
    require(isinstance(printed_basis, str) and printed_basis in captured_text, 'uncaptured publication basis')
    match = re.fullmatch(r'([A-Z][a-z]+ \d{1,2}, \d{4}) \| \d{1,2}:\d{2}(?:am|pm)', printed_basis)
    require(match is not None, 'unsupported printed date format')
    return datetime.strptime(match.group(1), '%B %d, %Y').replace(tzinfo=timezone.utc).isoformat()


def validate_partition_rows(rows, *, capability, fitted_keys=frozenset(), excluded_ids=frozenset()):
    """Mechanical group guards; rows contain metadata only, never reference text."""
    require(capability in PARTITIONS and rows, 'nonempty scoped membership required')
    require(len(rows) == len({r['record_id'] for r in rows}), 'duplicate record identity')
    groups, articles, windows, hashes = {}, Counter(), defaultdict(list), set()
    ids = {r['record_id'] for r in rows}
    for row in rows:
        split = row['partition']
        require(split in PARTITIONS[capability], 'partition outside worker capability')
        require(row['record_id'] not in excluded_ids, 'historical nontraining, excluded or held reuse')
        require(row['passage_sha256'] not in hashes, 'duplicate passage')
        hashes.add(row['passage_sha256'])
        keys = frozenset(row['group_keys'])
        require(keys, 'group evidence missing')
        if row['fitted_component'] or keys & fitted_keys:
            require(split == 'train', 'fitted component leaked outside training')
        for key in keys:
            require(key not in groups or groups[key] == split, 'fragmented group')
            groups[key] = split
        require(not ids.intersection(row.get('alternatives', [])), 'mutually exclusive alternatives selected')
        article = row['article_group']
        articles[article] += 1
        if capability == 'research_holdout':
            require(articles[article] <= 3, 'article passage cap exceeded')
        for start, end in windows[row['source_sha256']]:
            require(not (row['passage_start'] < end and start < row['passage_end']), 'overlapping passages')
        windows[row['source_sha256']].append((row['passage_start'], row['passage_end']))


def normalize(root, bundle, tokenizer):
    from .annotation.schema import AnnotationRecord
    from .research_review import FileBinding, ReviewCandidate, group_keys, validate_candidate

    verified = {}

    class ScopedBinding(FileBinding):
        def verify(self):
            stat = self.path.stat()
            signature = (stat.st_size, stat.st_mtime_ns)
            key = (self.path, self.sha256)
            if key in verified:
                require(verified[key] == signature, 'evidence changed during validation')
            else:
                super().verify()
                verified[key] = signature

    def evidence_binding(value):
        require(set(value) == {'path', 'sha256'}, 'invalid evidence binding')
        result = ScopedBinding(inside(root, value['path']), value['sha256'])
        result.verify()
        return result

    require(bundle.get('schema') == 'lanes-successor-input-v1' and bundle.get('capability') in PARTITIONS,
            'invalid normalized input')
    require(set(bundle) == {'schema', 'capability', 'members', 'historical_anchor_count',
                           'historical_fitted_group_keys', 'historical_nontraining_record_ids', 'excluded_record_ids'},
            'unexpected input capability fields')
    require(all(m['partition'] in PARTITIONS[bundle['capability']] for m in bundle['members']),
            'worker received references outside capability')
    records, metadata = [], []
    counts, languages, polarities, labels = Counter(), defaultdict(Counter), defaultdict(Counter), defaultdict(Counter)
    for member in bundle['members']:
        raw = member['record']
        require('entities' in raw and raw.get('complete') is True, 'missing reference is not a negative')
        record = AnnotationRecord.model_validate_json(json.dumps(raw))
        require(record.source.origin == 'captured_original', 'constructed fixtures cannot be admitted')
        require(member['pool_kind'] in ({'reviewed_original_training', 'reviewed_additional', 'saved_development_window'}
                if bundle['capability'] == 'development' else {'research_holdout'}), 'historical nontraining reuse')
        raw_path = verify_binding(root, member['raw_binding'])
        require(digest(raw_path) == record.source.raw_sha256, 'captured raw source mismatch')
        evidence = {gate: tuple(evidence_binding(b) for b in bindings)
                    for gate, bindings in member['evidence'].items()}
        omissions = []
        for item in member.get('occurrence_exclusions', []):
            omissions.append({**item, 'evidence': tuple(evidence_binding(b)
                                                       for b in item['evidence'])})
        candidate = ReviewCandidate(record, member['eligibility'], evidence,
            alternatives=frozenset(member.get('alternatives', [])), occurrence_exclusions=tuple(omissions))
        validate_candidate(candidate, tokenizer, frozenset())
        split = member['partition']
        keys = sorted(group_keys(record) | frozenset(member.get('group_keys', [])))
        row = dict(record_id=record.record_id, partition=split, group_keys=keys,
                   article_group=record.source.article_group, source_sha256=record.source.text_sha256,
                   passage_sha256=record.text_sha256, passage_start=record.passage_start,
                   passage_end=record.passage_end, alternatives=member.get('alternatives', []),
                   fitted_component=member['fitted_component'], language=record.passage_language,
                   is_negative=not record.entities)
        metadata.append(row)
        # The original proposal is untouched. The new scoped package records admission.
        admitted = record.model_copy(update={'source': record.source.model_copy(update={
            'reuse_status': 'allowed', 'admission_status': 'training_admitted'}),
            'split': 'test' if split == 'research_holdout' else split, 'review_status': 'accepted'})
        records.append((admitted, split))
        counts[split] += 1
        languages[split][record.passage_language] += 1
        polarities[split][record.passage_language + ('_negative' if not record.entities else '_positive')] += 1
        labels[split].update(e.label for e in record.entities)
    excluded = set(bundle.get('excluded_record_ids', [])) | set(bundle['historical_nontraining_record_ids'])
    validate_partition_rows(metadata, capability=bundle['capability'],
        fitted_keys=frozenset(bundle['historical_fitted_group_keys']), excluded_ids=excluded)
    # Hash each distinct evidence file again before allowing any admission/export.
    # The per-record checks above share this invocation's cache, never a global cache.
    for path, sha256 in verified:
        FileBinding(path, sha256).verify()
    return records, metadata, dict(counts), {k: dict(v) for k, v in languages.items()}, \
        {k: dict(v) for k, v in polarities.items()}, {k: dict(v) for k, v in labels.items()}


def cross_partition_check(development, holdout):
    """Only hashed URL keys and source-only metadata cross the curator boundary."""
    rows = development + holdout
    require(not any(k.startswith('url:') for r in rows for k in r['group_keys']), 'unsafe literal URL group')
    require(len({r['record_id'] for r in rows}) == len(rows), 'cross-pool duplicate identity')
    groups, windows, hashes = {}, defaultdict(list), set()
    for row in rows:
        require(row['passage_sha256'] not in hashes, 'cross-pool duplicate text')
        hashes.add(row['passage_sha256'])
        for key in row['group_keys']:
            require(key not in groups or groups[key] == row['partition'], 'cross-partition related group')
            groups[key] = row['partition']
        require(not row['fitted_component'] or row['partition'] == 'train', 'historical anchor leakage')
        for start, end in windows[row['source_sha256']]:
            require(not (row['passage_start'] < end and start < row['passage_end']), 'cross-pool overlap')
        windows[row['source_sha256']].append((row['passage_start'], row['passage_end']))
    return {'records': len(rows), 'partitions': dict(Counter(r['partition'] for r in rows)),
            'group_separation_verified': True}


def safe_coverage(value):
    require(set(value) == {'schema', 'capability', 'partitions'} and
            value['schema'] == 'lanes-successor-coverage-v1' and value['capability'] in PARTITIONS,
            'unsafe coverage envelope')
    require(set(value['partitions']) == set(PARTITIONS[value['capability']]), 'unsafe coverage partitions')
    for table in value['partitions'].values():
        require(set(table) == {'languages', 'themes', 'flood_roles', 'independent_components', 'articles'},
                'unsafe coverage fields')
        require(set(table['languages']) == {'english', 'taglish'}, 'unsafe coverage languages')
        for row in table['languages'].values():
            require(set(row) == {'positive', 'negative', 'labels'} and set(row['labels']) == PLACE_LABELS,
                    'unsafe class coverage')
            require(all(type(n) is int and n >= 0 for n in [row['positive'], row['negative'], *row['labels'].values()]),
                    'unsafe class counts')
        for field, allowed in [('themes', THEMES), ('flood_roles', ROLES)]:
            require(set(table[field]) <= allowed and all(type(v) is int and v >= 0 for v in table[field].values()),
                    'unsafe category counts')
        require(all(type(table[k]) is int and table[k] >= 0 for k in ('independent_components', 'articles')),
                'unsafe grouping counts')
    return value


def coverage(bundle, records, metadata):
    result = {}
    by_id = {m['record']['record_id']: m for m in bundle['members']}
    for split in PARTITIONS[bundle['capability']]:
        subset = [(r, s) for r, s in records if s == split]
        rows = [r for r in metadata if r['partition'] == split]
        # Count connected conservative groups, not merely distinct event labels.
        parents = list(range(len(rows)))
        def find(i):
            while parents[i] != i:
                parents[i] = parents[parents[i]]
                i = parents[i]
            return i
        seen = {}
        for i, row in enumerate(rows):
            for key in row['group_keys']:
                if key in seen:
                    parents[find(i)] = find(seen[key])
                seen[key] = i
        table = {'languages': {}, 'themes': {}, 'flood_roles': {},
                 'articles': len({r['article_group'] for r in rows}),
                 'independent_components': len({find(i) for i in range(len(rows))})}
        for language in ('english', 'taglish'):
            refs = [r for r, _ in subset if r.passage_language == language]
            labels = Counter(e.label for r in refs for e in r.entities)
            table['languages'][language] = {'positive': sum(bool(r.entities) for r in refs),
                'negative': sum(not r.entities for r in refs), 'labels': {k: labels[k] for k in sorted(PLACE_LABELS)}}
        for field, singular, allowed in [('themes', 'theme', THEMES), ('flood_roles', 'flood_role', ROLES)]:
            counts = Counter()
            for record, _ in subset:
                category = by_id[record.record_id].get('metadata', {}).get(singular)
                counts[category if category in allowed else 'unclassified_metadata'] += 1
            table[field] = dict(counts)
        result[split] = table
    return safe_coverage({'schema': 'lanes-successor-coverage-v1', 'capability': bundle['capability'],
                          'partitions': result})


def safe_status(value):
    allowed = {'schema', 'scope', 'capability', 'counts', 'languages', 'polarities', 'labels',
               'serialization_reload_verified', 'python_version', 'spacy_version', 'files',
               'global_history_verified', 'accounting_verified', 'certified_fresh', 'training_performed',
               'model_predictions_performed', 'model_weights_loaded', 'pipeline_components_loaded'}
    require(isinstance(value, dict) and set(value) == allowed, 'unsafe coordinator status fields')
    require(value['schema'] == 'lanes-successor-qualified-export-v1'
            and value['serialization_reload_verified'] is True
            and isinstance(value['python_version'], str)
            and __import__('re').fullmatch(r'3\.11\.\d+', value['python_version'])
            and value['spacy_version'] == '3.7.5', 'unsafe qualification/runtime fields')
    require(value['scope'] == SCOPE and value['capability'] in PARTITIONS, 'status scope mismatch')
    require(value['global_history_verified'] is False and value['accounting_verified'] is False
            and value['certified_fresh'] is False and value['training_performed'] is False
            and value['model_predictions_performed'] is False and value['model_weights_loaded'] is False
            and value['pipeline_components_loaded'] == [], 'unsafe readiness claims')
    for table, keys in ((value['counts'], set(PARTITIONS[value['capability']])),
                        (value['languages'], set(PARTITIONS[value['capability']])),
                        (value['polarities'], set(PARTITIONS[value['capability']])),
                        (value['labels'], set(PARTITIONS[value['capability']]))):
        require(set(table) == keys, 'unexpected aggregate partition')
    for split in value['counts']:
        require(type(value['counts'][split]) is int and value['counts'][split] > 0, 'invalid aggregate count')
        for table, keys in ((value['languages'][split], {'english', 'taglish'}),
                            (value['polarities'][split], {'english_positive', 'english_negative',
                                                         'taglish_positive', 'taglish_negative'}),
                            (value['labels'][split], {'ROAD', 'LANDMARK', 'LOCAL_AREA', 'BARANGAY', 'CITY', 'PROVINCE'})):
            require(set(table) <= keys and all(type(v) is int and v >= 0 for v in table.values()),
                    'unsafe aggregate values')
        require(sum(value['languages'][split].values()) == value['counts'][split]
                and sum(value['polarities'][split].values()) == value['counts'][split],
                'aggregate counts do not reconcile')
        for language in ('english', 'taglish'):
            require(sum(value['polarities'][split].get(language + '_' + p, 0)
                        for p in ('positive', 'negative')) == value['languages'][split].get(language, 0),
                    'language/polarity counts do not reconcile')
    allowed_files = {'admitted-records.jsonl', 'admission-ledger.json', 'coverage.json', 'partitions.json', 'source-only-join-metadata.json',
                     'tokenizer.bin'} | {s.replace('_', '-') + '.spacy' for s in PARTITIONS[value['capability']]}
    require(set(value['files']) == allowed_files and all(len(v) == 64 and
            all(c in '0123456789abcdef' for c in v) for v in value['files'].values()), 'unsafe export bindings')
    return value


def prepare(root, grant_path, interpreter, output):
    root, grant_path, output = Path(root).resolve(), Path(grant_path).resolve(), Path(output).resolve()
    grant = read(grant_path)
    verify_grant(root, grant)
    require(output.is_relative_to(root / 'backend/training/flood_ner/artifacts') and not output.exists(),
            'new output inside private artifacts required')
    inside(root, output.relative_to(root))
    claims = root / 'backend/training/flood_ner/artifacts/successor-claims'
    inside(root, claims.relative_to(root))
    claims.mkdir(exist_ok=True)
    claim = claims / (digest(grant_path) + '.claim')
    with claim.open('x', encoding='utf-8') as stream:
        stream.write(str(output))
    output.mkdir()
    request = output / 'worker-request.json'
    write_new(request, {'root': str(root), 'grant': str(grant_path), 'output': str(output)})
    worker = root / 'backend/training/flood_ner/successor_export_worker.py'
    with (output / 'worker-stdout.log').open('xb') as stdout, (output / 'worker-stderr.log').open('xb') as stderr:
        result = subprocess.run([str(Path(interpreter).resolve()), '-I', '-B', str(worker), str(request)],
                                cwd=root, stdout=stdout, stderr=stderr, check=False)
    require(result.returncode == 0, 'qualification failed; private worker evidence retained')
    return safe_status(read(output / 'aggregate-status.json'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', required=True, type=Path)
    parser.add_argument('--grant', required=True, type=Path)
    parser.add_argument('--python', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.checkout, args.grant, args.python, args.output), sort_keys=True))


if __name__ == '__main__':
    main()
