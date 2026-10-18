"""Single-attempt isolated frozen holdout comparison; aggregate-only public exit."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import random
import statistics
import subprocess
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from training.flood_ner.validation_comparison import LABELS, checked_predictions, score_spans

ORIGINAL_HANDOFF = 'b3dd00e73d59aa11fdcdbf4a1c97c7e58abd7b30540521f2215e9c7435887367'
HOLDOUT_QUALIFICATION = 'fe3cd0024cd9dcc67106068dba076286469baa0ae9a54a048c3c9f27bfc938a4'
PARTITION_SHA = '4be5213e0b4106d358505027af936bedd7f80b8151345e62362127fcb2a5f20e'
ROSTER = tuple(f'{f}-seed-{s}' for f in ('control', 'v16') for s in range(3)) + ('rules',)
PROTOCOL = {'schema': 'lanes-v19-frozen-holdout-protocol-v1', 'original_handoff': ORIGINAL_HANDOFF,
            'holdout_qualification': HOLDOUT_QUALIFICATION, 'roster': ROSTER, 'primary': 'control-seed-0',
            'labels': sorted(LABELS), 'records': 60, 'english': 30, 'taglish': 30,
            'positive_per_language': 27, 'negative_per_language': 3, 'article_cap': 3,
            'connected_groups': 30, 'bootstrap': {'replicates': 10000, 'seed': 0, 'method': 'paired connected-group percentile'},
            'neural': {'python': '3.11.17', 'spacy': '3.7.5', 'device': 'cpu'},
            'rules': {'python': '3.12.14', 'input': 'raw text and opaque IDs only'},
            'training': False, 'development_references': False, 'automatic_retries': False}
PROTOCOL_SHA256 = hashlib.sha256(json.dumps(PROTOCOL, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def child(root, name):
    relative = PurePosixPath(name)
    require(bool(relative.parts) and not relative.is_absolute() and '..' not in relative.parts
            and ':' not in name and '\\' not in name, 'unsafe binding path')
    result = Path(root).joinpath(*relative.parts)
    require(result.resolve().is_relative_to(Path(root).resolve()) and not any(p.is_symlink() or
            getattr(p, 'is_junction', lambda: False)() for p in (result, *result.parents)), 'linked path refused')
    return result


def tree(folder):
    return {p.relative_to(folder).as_posix(): digest(p) for p in sorted(Path(folder).rglob('*')) if p.is_file()}


def verify_qualification(root, path, expected_sha):
    from training.flood_ner.v19_evaluation_qualification import verify_receipt
    receipt = verify_receipt(root, path, expected_sha)
    require(receipt['original_handoff_sha256'] == ORIGINAL_HANDOFF and receipt['protocol_sha256'] == PROTOCOL_SHA256
            and receipt['verified'] is True, 'qualification protocol changed')
    runtime = receipt['neural_runtime']
    require(sys.version.split()[0] == runtime['version'] == '3.11.17'
            and Path(sys.executable).resolve() == Path(runtime['python']).resolve()
            and digest(sys.executable) == runtime['sha256'], 'qualified neural interpreter required')
    import spacy
    require(spacy.__version__ == runtime['spacy'] == '3.7.5', 'qualified spaCy required')
    return receipt


def verify_scoped(root, receipt):
    binding = receipt['scoped_manifest']
    path = child(root, binding['path'])
    require(digest(path) == binding['sha256'], 'scoped manifest changed')
    manifest, folder = read(path), path.parent
    require(manifest['schema'] == 'lanes-v19-scoped-models-v1' and manifest['original_handoff_sha256'] == ORIGINAL_HANDOFF
            and manifest['retained'] == 'control' and manifest['primary'] == 'control-seed-0', 'frozen scoped roster required')
    require(len(manifest['runs']) == 6 and {r['name'] for r in manifest['runs']} == set(ROSTER[:-1]), 'six frozen models required')
    # Scoped directory may contain qualification/exclusions outside payload; verify
    # exact membership beneath the six model roots and tokenizer-only package.
    expected = manifest['files']
    require({k: v for k, v in tree(folder).items() if k != path.name} == expected, 'scoped membership differs')
    for name, sha in expected.items():
        require(digest(child(folder, name)) == sha, 'scoped payload changed')
    require({p.name for p in (folder / 'package').iterdir()} == {'model-contract.json', 'tokenizer.bin'}, 'tokenizer-only package required')
    for run in manifest['runs']:
        model = child(folder, run['model'])
        require(tree(model) == run['files'], 'checkpoint membership changed')
        require(all(expected.get((PurePosixPath(run['model']) / k).as_posix()) == v for k, v in run['files'].items()), 'checkpoint not in scoped payload')
        meta = read(model / 'meta.json')
        require(set(meta['labels']['ner']) == LABELS and meta['pipeline'] == ['ner'], 'six-label NER required')
    allowed = {f'package/{n}' for n in ('model-contract.json', 'tokenizer.bin')} | {
        (PurePosixPath(r['model']) / n).as_posix() for r in manifest['runs'] for n in r['files']}
    require(set(expected) == allowed, 'unexpected scoped payload capability')
    return manifest, folder


def groups(rows):
    require(len(rows) == len({r['record_id'] for r in rows}), 'duplicate group identity')
    parent = {r['record_id']: r['record_id'] for r in rows}
    def find(rid):
        while parent[rid] != rid:
            parent[rid] = parent[parent[rid]]
            rid = parent[rid]
        return rid
    seen = {}
    for row in rows:
        require(bool(row['group_keys']), 'connected group evidence missing')
        for key in row['group_keys']:
            if key in seen:
                parent[find(row['record_id'])] = find(seen[key])
            seen[key] = row['record_id']
    result = {}
    for rid in sorted(parent):
        result.setdefault(find(rid), []).append(rid)
    return sorted(result.values())


def validate_rows(records, metadata, join, exclusions, tokenizer):
    """Full schema/source/token-boundary and independent source-only join checks."""
    # Neural compiled libraries are loaded before this optional pure-Python
    # application-validation dependency path; rules always run in their own process.
    backend_site = Path(__file__).resolve().parents[2] / '.venv/Lib/site-packages'
    if str(backend_site) not in sys.path:
        sys.path.append(str(backend_site))
    from training.flood_ner.annotation.schema import AnnotationRecord
    from training.flood_ner.annotation.validation import validate_record
    from training.flood_ner.research_review import group_keys
    from training.flood_ner.successor_preparation import safe_group_keys, validate_partition_rows, cross_partition_check
    require(len(records) == len({r['record_id'] for r in records}) == 60, 'sixty unique holdout passages required')
    require(Counter(r['passage_language'] for r in records) == {'english': 30, 'taglish': 30}, 'holdout languages differ')
    require(Counter((r['passage_language'], bool(r.get('entities'))) for r in records) ==
            {('english', True): 27, ('english', False): 3, ('taglish', True): 27, ('taglish', False): 3}, 'holdout polarity differs')
    require(len(metadata) == len(join) == 60 and {r['record_id'] for r in metadata} == {r['record_id'] for r in join}
            == {r['record_id'] for r in records}, 'holdout metadata join differs')
    by_id, joined = {r['record_id']: r for r in metadata}, {r['record_id']: r for r in join}
    require(len(exclusions) == 405 and Counter(r['partition'] for r in exclusions) == {'train': 345, 'dev': 60}, 'development exclusion scope differs')
    validate_partition_rows(metadata, capability='research_holdout')
    require(len({r['record_id'] for r in exclusions}) == 405 and all(r['group_keys'] for r in exclusions), 'incomplete development exclusion metadata')
    all_ids = {r['record_id'] for r in exclusions + join}
    require(not any(all_ids.intersection(r.get('alternatives', [])) for r in exclusions + join), 'selected mutually exclusive alternative')
    for raw in records:
        require('entities' in raw and raw.get('complete') is True, 'incomplete reference cannot be negative')
        record = AnnotationRecord.model_validate_json(json.dumps(raw, ensure_ascii=False))
        require(not validate_record(record, tokenizer), 'holdout schema/source/tokenizer validation failed')
        require(record.annotation_profile == 'location-only-v1' and record.split == 'test' and record.review_status == 'accepted'
                and record.source.origin == 'captured_original' and record.source.reuse_status == 'allowed'
                and record.source.admission_status == 'training_admitted', 'holdout admission differs')
        meta = by_id[record.record_id]
        derived = {'record_id': record.record_id, 'partition': 'research_holdout', 'article_group': record.source.article_group,
                   'source_sha256': record.source.text_sha256, 'passage_sha256': record.text_sha256,
                   'passage_start': record.passage_start, 'passage_end': record.passage_end,
                   'language': record.passage_language, 'is_negative': not record.entities}
        require(all(meta.get(k) == v for k, v in derived.items()) and meta['fitted_component'] is False,
                'source-derived metadata differs')
        require(group_keys(record) <= set(meta['group_keys']), 'source group omitted')
        projected = {**{k: v for k, v in meta.items() if k != 'article_group'}, 'group_keys': safe_group_keys(meta['group_keys'])}
        require(joined[record.record_id] == projected, 'independent source-only metadata differs')
    cross_partition_check(exclusions, join)
    require(len(groups(metadata)) == 30, 'locked thirty connected components required')


def qualified_export(folder):
    require(digest(folder / 'aggregate-status.json') == HOLDOUT_QUALIFICATION, 'qualified holdout identity differs')
    from training.flood_ner.successor_preparation import safe_status
    status = safe_status(read(folder / 'aggregate-status.json'))
    require(status['capability'] == 'research_holdout' and status['serialization_reload_verified'] is True, 'holdout capability required')
    for name, sha in status['files'].items():
        require(digest(child(folder, name)) == sha, 'qualified holdout changed')
    records = [json.loads(line) for line in (folder / 'admitted-records.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    return records, read(folder / 'partitions.json')['members'], read(folder / 'source-only-join-metadata.json')


def rules_request(root, receipt, rows):
    require(all(set(r) == {'record_id', 'text'} for r in rows), 'raw-only inference rows required')
    files = dict(receipt['rules_specification']['files'])
    from training.flood_ner.corrected_rules_worker import rules_code_files
    for name, sha256 in rules_code_files(root).items():
        require(receipt['implementation'].get(name, files.get(name)) == sha256, 'rules package closure must be qualified')
        files[name] = sha256
    worker = 'backend/training/flood_ner/corrected_rules_worker.py'
    require(worker in receipt['implementation'], 'rules worker must be qualified')
    files[worker] = receipt['implementation'][worker]
    return {'schema': 'lanes-corrected-rules-request-v1', 'root': str(root),
            'runtime': receipt['rules_runtime'], 'files': files, 'rows': rows}


def run_rules(root, receipt, rows, output):
    output.mkdir()
    request = output / 'raw-request.json'
    write_new(request, rules_request(root, receipt, rows))
    env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH'}}
    worker = root / 'backend/training/flood_ner/corrected_rules_worker.py'
    proc = subprocess.run([receipt['rules_runtime']['python'], '-I', '-B', '-X', 'utf8', str(worker), str(request)],
                          cwd=output, capture_output=True, env=env, timeout=600)
    (output / 'worker.stdout.log').write_bytes(proc.stdout)
    (output / 'worker.stderr.log').write_bytes(proc.stderr)
    require(proc.returncode == 0, 'rules worker failed; private diagnostics retained')
    result = json.loads(proc.stdout.decode('utf-8'))
    require(set(result) == {'schema', 'predictions', 'python_version', 'network_database_blocked'}
            and result['schema'] == 'lanes-corrected-rules-response-v1' and result['python_version'] == '3.12.14'
            and result['network_database_blocked'] is True, 'invalid rules worker response')
    return checked_predictions(rows, result['predictions'], LABELS)


def claim_attempt(root, freeze_sha, output):
    """Global immutable claim; new freeze/output/qualification cannot bypass it."""
    require(not output.exists(), 'new evaluation output required')
    attempts = root / 'backend/training/flood_ner/artifacts/v19-single-holdout-attempts'
    child(root, attempts.relative_to(root).as_posix())
    attempts.mkdir(exist_ok=True)
    key = hashlib.sha256((ORIGINAL_HANDOFF + HOLDOUT_QUALIFICATION + PROTOCOL_SHA256).encode()).hexdigest()
    claim = attempts / (key + '.json')
    write_new(claim, {'schema': 'lanes-v19-single-attempt-v1', 'original_handoff_sha256': ORIGINAL_HANDOFF,
                     'holdout_qualification_sha256': HOLDOUT_QUALIFICATION, 'protocol_sha256': PROTOCOL_SHA256,
                     'freeze_sha256': freeze_sha, 'output': str(output.resolve()),
                     'time': datetime.now(timezone.utc).isoformat(), 'exposure_possible_after_claim': True,
                     'automatic_retry_authorized': False})
    return claim


def scored(truth, predictions, languages):
    result = score_spans(truth, predictions, languages)
    for table in [result['labels'], *result['language_labels'].values()]:
        for metric in table.values():
            metric['support_status'] = 'measured' if metric['reference_spans'] else 'unmeasured'
            if not metric['reference_spans']:
                metric.update(f1=None, recall=None)
    return result


def paired_intervals(truth, predictions, components, retained='control', repetitions=10000):
    require(retained == 'control' and type(repetitions) is int and repetitions > 0, 'fixed control bootstrap required')
    require(components and len([r for c in components for r in c]) == len(truth)
            and {r for c in components for r in c} == set(truth), 'exact bootstrap grouping required')
    counts = {}
    for model, predicted in predictions.items():
        counts[model] = []
        for component in components:
            tp = fp = fn = 0
            for rid in component:
                ref, guess = set(map(tuple, truth[rid])), set(map(tuple, predicted[rid]))
                tp += len(ref & guess); fp += len(guess - ref); fn += len(ref - guess)
            counts[model].append((tp, fp, fn))
    comparisons = [('control-seed-0', 'v16-seed-0'), ('control-seed-0', 'rules')]
    samples = {a + '_minus_' + b: [] for a, b in comparisons}
    samples['control_mean_minus_v16_mean'] = []
    rng = random.Random(0)
    for _ in range(repetitions):
        indexes = [rng.randrange(len(components)) for _ in components]
        f1 = {}
        for model, rows in counts.items():
            tp, fp, fn = (sum(rows[i][j] for i in indexes) for j in range(3))
            f1[model] = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None
        for a, b in comparisons:
            if f1[a] is not None and f1[b] is not None:
                samples[a + '_minus_' + b].append(f1[a] - f1[b])
        if all(f1[f'{f}-seed-{s}'] is not None for f in ('control', 'v16') for s in range(3)):
            samples['control_mean_minus_v16_mean'].append(statistics.mean(f1[f'control-seed-{s}'] for s in range(3))
                                                       - statistics.mean(f1[f'v16-seed-{s}'] for s in range(3)))
    result = {}
    for name, values in samples.items():
        values.sort()
        result[name] = {'lower_95': values[int(.025 * (len(values) - 1))] if values else None,
                        'upper_95': values[int(.975 * (len(values) - 1))] if values else None,
                        'defined_replicates': len(values)}
    return {'method': 'paired connected-group percentile bootstrap', 'seed': 0,
            'replicates': repetitions, 'components': len(components), 'comparisons': result}


def private_path(root, path):
    require(path.resolve().is_relative_to(root / 'backend/training/flood_ner/artifacts'), 'private artifact path required')
    child(root, path.resolve().relative_to(root).as_posix())


def block_network():
    """Guard before neural imports; local model loading never needs transport."""
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                      OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
    def audit(event, args):
        if event in {'socket.connect', 'socket.bind', 'socket.getaddrinfo', 'socket.gethostbyname',
                     'socket.gethostbyaddr', 'socket.sendto'}:
            raise RuntimeError('offline evaluator: network forbidden')
    sys.addaudithook(audit)


def seal(root, qualification, qualification_sha, holdout, resources, freeze):
    block_network()
    private_path(root, freeze)
    require(not freeze.exists(), 'new freeze destination required')
    receipt = verify_qualification(root, qualification, qualification_sha)
    manifest, scoped = verify_scoped(root, receipt)
    require(digest(child(root, receipt['partition_manifest']['path'])) == PARTITION_SHA, 'locked partition lineage differs')
    package = scoped / 'package'
    contract = read(package / 'model-contract.json')
    require(tree(resources) == {r['path']: r['sha256'] for r in contract['files']}, 'pinned resources differ')
    exclusions = read(child(root, receipt['development_exclusions']['path']))
    if isinstance(exclusions, dict):
        exclusions = exclusions['members']
    # Every model is loaded and used on constructed text before holdout access.
    from training.flood_ner.corrected_experiment_worker import load_model
    preflight = freeze.with_name(freeze.name + '-constructed-preflight')
    require(not preflight.exists(), 'fresh constructed preflight required')
    preflight.mkdir()
    for run in manifest['runs']:
        destination = preflight / run['name']; destination.mkdir()
        nlp, handles = load_model(root, child(scoped, run['model']), package, resources, destination)
        require(nlp('Constructed probe at Pasig City.').text == 'Constructed probe at Pasig City.', 'constructed neural probe failed')
        if run['name'] == 'control-seed-0':
            tokenizer_nlp = nlp
    run_rules(root, receipt, [{'record_id': 'constructed-only', 'text': 'Baha sa Pasig City.'}], preflight / 'rules')
    records, members, join = qualified_export(holdout)
    require(digest(holdout / 'tokenizer.bin') == digest(package / 'tokenizer.bin'), 'qualified tokenizer differs')
    validate_rows(records, members, join, exclusions, tokenizer_nlp)
    verify_qualification(root, qualification, qualification_sha)
    state = {'schema': 'lanes-v19-holdout-freeze-v2', 'qualification': str(qualification), 'qualification_sha256': qualification_sha,
             'protocol_sha256': PROTOCOL_SHA256, 'holdout': str(holdout), 'holdout_files': tree(holdout),
             'resources': str(resources), 'resource_files': tree(resources), 'scoped_manifest_sha256': receipt['scoped_manifest']['sha256'],
             'constructed_preflight_files': tree(preflight), 'constructed_preflight': str(preflight),
             'original_handoff_sha256': ORIGINAL_HANDOFF, 'primary': 'control-seed-0', 'roster': ROSTER,
             'training_performed': False, 'holdout_predictions_performed': False}
    freeze.mkdir()
    write_new(freeze / 'manifest.json', state)
    return {'state': 'sealed_without_holdout_inference', 'freeze_sha256': digest(freeze / 'manifest.json'),
            'protocol_sha256': PROTOCOL_SHA256}


def verify_freeze(root, freeze, expected_sha):
    require(digest(freeze / 'manifest.json') == expected_sha, 'freeze changed')
    state = read(freeze / 'manifest.json')
    require(state['schema'] == 'lanes-v19-holdout-freeze-v2' and state['protocol_sha256'] == PROTOCOL_SHA256
            and state['original_handoff_sha256'] == ORIGINAL_HANDOFF and state['roster'] == list(ROSTER)
            and state['primary'] == 'control-seed-0', 'frozen protocol differs')
    receipt = verify_qualification(root, Path(state['qualification']), state['qualification_sha256'])
    manifest, scoped = verify_scoped(root, receipt)
    require(state['scoped_manifest_sha256'] == receipt['scoped_manifest']['sha256'], 'scoped receipt changed')
    for pathkey, filekey in [('holdout', 'holdout_files'), ('resources', 'resource_files'), ('constructed_preflight', 'constructed_preflight_files')]:
        require(tree(Path(state[pathkey])) == state[filekey], 'frozen files changed')
    return state, receipt, manifest, scoped


def safe_aggregate(result):
    """Deep typed allowlist: candidate-derived keys/strings never exit evaluator."""
    expected = {'schema', 'state', 'freeze_sha256', 'qualification_sha256', 'original_handoff_sha256',
                'holdout_qualification_sha256', 'protocol_sha256', 'primary', 'roster', 'device', 'records',
                'metrics', 'family_statistics', 'uncertainty', 'training_performed', 'selection_changed',
                'holdout_predictions_performed', 'global_history_verified', 'accounting_verified', 'certified_fresh',
                'python_version', 'spacy_version', 'rules_python_version', 'private_artifact_sha256'}
    require(isinstance(result, dict) and set(result) == expected, 'unsafe aggregate envelope')
    require(result['schema'] == 'lanes-v19-holdout-aggregate-v2' and result['state'] == 'passed'
            and result['primary'] == 'control-seed-0' and result['roster'] == list(ROSTER) and result['device'] == 'cpu'
            and result['records'] == 60 and result['python_version'] == '3.11.17' and result['spacy_version'] == '3.7.5'
            and result['rules_python_version'] == '3.12.14', 'unsafe aggregate constants')
    for field in ('training_performed', 'selection_changed', 'global_history_verified', 'accounting_verified', 'certified_fresh'):
        require(result[field] is False, 'unsafe aggregate claim')
    require(result['holdout_predictions_performed'] is True, 'unsafe prediction claim')
    for name in ('freeze_sha256', 'qualification_sha256', 'original_handoff_sha256', 'holdout_qualification_sha256', 'protocol_sha256'):
        sha(result[name])
    require(result['original_handoff_sha256'] == ORIGINAL_HANDOFF and result['holdout_qualification_sha256'] == HOLDOUT_QUALIFICATION
            and result['protocol_sha256'] == PROTOCOL_SHA256, 'unsafe aggregate identity')
    require(set(result['metrics']) == set(ROSTER), 'unsafe model keys')
    def integer(n):
        require(type(n) is int and n >= 0, 'unsafe aggregate count')
    def number(n, lower=0, upper=1):
        require(n is None or type(n) in (int, float) and math.isfinite(n) and lower <= n <= upper, 'unsafe numeric aggregate')
    def metric(m, support=False):
        require(set(m) == {'TP', 'FP', 'FN', 'reference_spans', 'predicted_spans', 'passages', 'precision', 'recall', 'f1'}
                | ({'support_status'} if support else set()), 'unsafe metric fields')
        for key in ('TP', 'FP', 'FN', 'reference_spans', 'predicted_spans', 'passages'):
            integer(m[key])
        require(m['TP'] + m['FN'] == m['reference_spans'] and m['TP'] + m['FP'] == m['predicted_spans'], 'inconsistent aggregate counts')
        for key in ('precision', 'recall', 'f1'):
            number(m[key])
        if support:
            require(m['support_status'] == ('measured' if m['reference_spans'] else 'unmeasured'), 'unsafe support claim')
            require(m['reference_spans'] > 0 or m['recall'] is None and m['f1'] is None, 'unmeasured slice has score')
    for table in result['metrics'].values():
        require(set(table) == {'overall', 'labels', 'languages', 'language_labels', 'negative_passages'}, 'unsafe score tables')
        metric(table['overall'])
        require(set(table['labels']) == LABELS and set(table['languages']) == set(table['language_labels']) == {'english', 'taglish'}, 'unsafe slice keys')
        for m in table['labels'].values(): metric(m, True)
        for lang in ('english', 'taglish'):
            metric(table['languages'][lang])
            require(set(table['language_labels'][lang]) == LABELS, 'unsafe language label keys')
            for m in table['language_labels'][lang].values(): metric(m, True)
        require(set(table['negative_passages']) == {'overall', 'english', 'taglish'}, 'unsafe negative keys')
        for m in table['negative_passages'].values():
            require(set(m) == {'negative_passages', 'false_positive_passages', 'rate'}, 'unsafe negative fields')
            integer(m['negative_passages']); integer(m['false_positive_passages']); number(m['rate'])
    require(set(result['family_statistics']) == {'control', 'v16'}, 'unsafe family keys')
    for family in result['family_statistics'].values():
        require(set(family) == {'primary_seed', 'primary_f1', 'mean_f1', 'sample_stddev'} and family['primary_seed'] == 0, 'unsafe family fields')
        for k in ('primary_f1', 'mean_f1', 'sample_stddev'): number(family[k])
    u = result['uncertainty']
    require(set(u) == {'method', 'seed', 'replicates', 'components', 'comparisons'} and u['seed'] == 0 and u['replicates'] == 10000
            and u['components'] == 30 and u['method'] == 'paired connected-group percentile bootstrap', 'unsafe bootstrap fields')
    require(set(u['comparisons']) == {'control-seed-0_minus_v16-seed-0', 'control-seed-0_minus_rules', 'control_mean_minus_v16_mean'}, 'unsafe comparison keys')
    for m in u['comparisons'].values():
        require(set(m) == {'lower_95', 'upper_95', 'defined_replicates'}, 'unsafe interval fields')
        number(m['lower_95'], -1, 1); number(m['upper_95'], -1, 1); integer(m['defined_replicates'])
        require(m['defined_replicates'] <= 10000, 'invalid replicate count')
    require(set(result['private_artifact_sha256']) == {'predictions.json', 'metrics.json', 'uncertainty.json'}, 'unsafe artifact names')
    for value in result['private_artifact_sha256'].values(): sha(value)
    return result


def sha(value):
    require(isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'unsafe digest')


def evaluate(root, freeze, expected_sha, output):
    block_network()
    private_path(root, output)
    state, receipt, manifest, scoped = verify_freeze(root, freeze, expected_sha)
    # No predictions or candidate rows reach a worker before the shared claim.
    claim_attempt(root, expected_sha, output)
    output.mkdir()
    try:
        records, members, join = qualified_export(Path(state['holdout']))
        rows = [{'record_id': r['record_id'], 'text': r['text']} for r in records]
        truth = {r['record_id']: [(e['start'], e['end'], e['label']) for e in r['entities']] for r in records}
        languages = {r['record_id']: r['passage_language'] for r in records}
        from training.flood_ner.corrected_experiment_worker import load_model
        from training.flood_ner.validation_worker import infer_raw
        predictions, metrics = {}, {}
        for run in manifest['runs']:
            destination = output / run['name']; destination.mkdir()
            nlp, handles = load_model(root, child(scoped, run['model']), scoped / 'package', Path(state['resources']), destination)
            predictions[run['name']], _ = infer_raw(nlp, rows, False)
            checked_predictions(rows, predictions[run['name']], LABELS)
            metrics[run['name']] = scored(truth, predictions[run['name']], languages)
            del nlp
        predictions['rules'] = run_rules(root, receipt, rows, output / 'rules')
        metrics['rules'] = scored(truth, predictions['rules'], languages)
        intervals = paired_intervals(truth, predictions, groups(members))
        families = {}
        for family in ('control', 'v16'):
            values = [metrics[f'{family}-seed-{s}']['overall']['f1'] for s in range(3)]
            families[family] = {'primary_seed': 0, 'primary_f1': values[0], 'mean_f1': statistics.mean(values), 'sample_stddev': statistics.stdev(values)}
        write_new(output / 'predictions.json', predictions)
        write_new(output / 'metrics.json', metrics)
        write_new(output / 'uncertainty.json', intervals)
        verify_freeze(root, freeze, expected_sha)
        result = {'schema': 'lanes-v19-holdout-aggregate-v2', 'state': 'passed', 'freeze_sha256': expected_sha,
                  'qualification_sha256': state['qualification_sha256'], 'original_handoff_sha256': ORIGINAL_HANDOFF,
                  'holdout_qualification_sha256': HOLDOUT_QUALIFICATION, 'protocol_sha256': PROTOCOL_SHA256,
                  'primary': 'control-seed-0', 'roster': list(ROSTER), 'device': 'cpu', 'records': 60,
                  'metrics': metrics, 'family_statistics': families, 'uncertainty': intervals,
                  'training_performed': False, 'selection_changed': False, 'holdout_predictions_performed': True,
                  'global_history_verified': False, 'accounting_verified': False, 'certified_fresh': False,
                  'python_version': '3.11.17', 'spacy_version': '3.7.5', 'rules_python_version': '3.12.14',
                  'private_artifact_sha256': {n: digest(output / n) for n in ('predictions.json', 'metrics.json', 'uncertainty.json')}}
        safe_aggregate(result)
        write_new(output / 'aggregate.json', result)
        return result
    except BaseException:
        import traceback
        with (output / 'private-failure-traceback.txt').open('x', encoding='utf-8') as stream:
            stream.write(traceback.format_exc())
        write_new(output / 'failure.json', {'state': 'failed', 'exposure_possible': True, 'automatic_retry_authorized': False,
                                          'training_performed': False, 'error': 'private evaluation failed'})
        raise ValueError('single holdout attempt failed; no retry authorized; private diagnostics retained') from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('seal', 'evaluate'))
    for name in ('checkout', 'freeze', 'qualification', 'holdout', 'resources', 'output'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--qualification-sha256')
    parser.add_argument('--freeze-sha256')
    args = parser.parse_args()
    require(args.checkout and args.freeze, 'checkout and freeze required')
    root, freeze = args.checkout.resolve(), args.freeze.resolve()
    try:
        if args.operation == 'seal':
            require(all((args.qualification, args.qualification_sha256, args.holdout, args.resources)), 'seal inputs required')
            result = seal(root, args.qualification.resolve(), args.qualification_sha256, args.holdout.resolve(), args.resources.resolve(), freeze)
        else:
            require(args.output and args.freeze_sha256, 'evaluation inputs required')
            result = evaluate(root, freeze, args.freeze_sha256, args.output.resolve())
    except BaseException:
        import traceback
        private_path(root, freeze)
        failure = freeze.with_name(freeze.name + '-private-failure-traceback.txt')
        if not failure.exists():
            with failure.open('x', encoding='utf-8') as stream:
                stream.write(traceback.format_exc())
        raise
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        if isinstance(exc, SystemExit):
            raise
        # Pydantic/source validation errors may embed private text. Never print
        # exception objects or tracebacks through the aggregate-only CLI.
        print(json.dumps({'state': 'failed', 'error': 'private evaluation operation failed', 'automatic_retry_authorized': False}))
        raise SystemExit(1)
