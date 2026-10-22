"""Development-only correction preparation and a read-only future experiment protocol.

No network, inference, pipeline initialization or training entry point is provided.
Private identities and approved spans are inputs, never built into this module.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys

from .development_error_audit import bound, digest, read, require, safe_path, validate_join, write_new
from .successor_preparation import validate_partition_rows
from .successor_training import PAYLOAD_FILES, case_sensitive_parser, verify_package, verify_template

SCOPE = 'corrected_development_experiment_preparation_only'
VARIANTS = ('control', 'higher_dropout', 'lower_learning_rate')
PARAMETERS = {'control': ('0.1', '0.001'), 'higher_dropout': ('0.2', '0.001'),
              'lower_learning_rate': ('0.1', '0.0005')}
EPSILON = 1e-12
IMPLEMENTATION = tuple('backend/training/flood_ner/' + name for name in (
    'successor_experiment_preparation.py', 'successor_experiment_worker.py',
    'successor_preparation.py', 'successor_export_worker.py', 'successor_training.py',
    'experiment_registry.py', 'development_error_audit.py', 'annotation/schema.py', 'annotation/validation.py'))
BINDINGS = {'audit_manifest', 'proposals', 'proposed_records', 'proposal_validation',
            'validation_review', 'development_status', 'baseline_manifest', 'preservation_snapshot'}


def object_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def lines(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def verify_grant(root, grant):
    require(set(grant) == {'schema', 'scope', 'bindings', 'implementation', 'tests', 'development_directory',
        'baseline_directory', 'model_directory', 'permissions', 'expected'}, 'unexpected preparation grant fields')
    require(grant['schema'] == 'lanes-corrected-experiment-grant-v1' and grant['scope'] == SCOPE,
            'preparation-only grant required')
    require(grant['permissions'] == dict.fromkeys(('network', 'holdout', 'inference', 'training', 'upload', 'git'), False),
            'forbidden preparation permissions')
    require(all(type(v) is bool for v in grant['permissions'].values()), 'explicit Boolean capabilities required')
    require(grant['expected'] == {'counts': {'train': 345, 'dev': 60}, 'corrected_records': 9,
            'corrected_spans': 12, 'historical_anchors': 280}, 'approved finite revision required')
    require(set(grant['bindings']) == BINDINGS, 'missing preparation evidence')
    require(all(not any(word in value['path'].lower() for word in ('holdout', 'curator'))
                for value in grant['bindings'].values()), 'holdout evidence input forbidden')
    paths = {name: bound(root, value) for name, value in grant['bindings'].items()}
    require(len(grant['implementation']) == len(IMPLEMENTATION)
            and {v['path'] for v in grant['implementation']} == set(IMPLEMENTATION), 'missing implementation bindings')
    for value in [*grant['implementation'], grant['tests']]:
        bound(root, value)
    require(grant['tests']['path'] == 'backend/tests/test_flood_ner_successor_experiment.py', 'wrong test binding')
    for key in ('development_directory', 'baseline_directory', 'model_directory'):
        require('holdout' not in grant[key].lower() and 'curator' not in grant[key].lower(), 'holdout input forbidden')
    development = safe_path(root, grant['development_directory'])
    status = read(paths['development_status'])
    require(paths['development_status'] == development / 'aggregate-status.json'
            and status['capability'] == 'development' and status['counts'] == grant['expected']['counts'],
            'wrong development export')
    expected = {'admission-ledger.json', 'admitted-records.jsonl', 'coverage.json', 'dev.spacy',
                'partitions.json', 'source-only-join-metadata.json', 'tokenizer.bin', 'train.spacy'}
    require(set(status['files']) == expected, 'unexpected development export files')
    for name, sha in status['files'].items():
        require(digest(development / name) == sha, 'stale development export')
    baseline = safe_path(root, grant['baseline_directory'])
    manifest = read(paths['baseline_manifest'])
    require(paths['baseline_manifest'] == baseline / 'handoff-manifest.json'
            and set(manifest['files']) == PAYLOAD_FILES and manifest['counts'] == status['counts'],
            'wrong baseline package')
    for name, sha in manifest['files'].items():
        require(digest(baseline / name) == sha, 'stale baseline payload')
    for name in ('dev.spacy', 'train.spacy', 'tokenizer.bin'):
        require(manifest['files'][name] == status['files'][name], 'baseline export differs')
    # The audit binds both the reviewed proposal and the complete source-bound review.
    audit = read(paths['audit_manifest'])
    require(audit.get('frozen_inputs_unchanged') is True and audit.get('holdout_unopened') is True,
            'incomplete predecessor audit')
    private_hashes = paths['audit_manifest'].parent / 'private-output-hashes.json'
    require(digest(private_hashes) == audit['private_output_hashes_sha256'], 'stale audit inventory')
    hashes = {key.replace('\\', '/'): value for key, value in read(private_hashes).items()}
    # Inventory shape is checked against the exact bound files below, not inferred from counters.
    for key in ('proposals', 'proposed_records', 'proposal_validation', 'validation_review'):
        relative = paths[key].relative_to(Path(root).resolve()).as_posix()
        expected_hash = hashes.get(relative)
        if isinstance(expected_hash, dict):
            expected_hash = expected_hash.get('sha256')
        require(expected_hash == digest(paths[key]), 'proposal not bound by completed audit')
    validation = read(paths['proposal_validation'])
    require(validation.get('proposed_records') == 9 and validation.get('span_corrections') == 12
            and len(validation.get('records', [])) == 9
            and all(all(row.get(k) is True for k in ('schema_valid', 'source_exact', 'strict_token_alignment', 'nonoverlap'))
                    for row in validation['records']), 'incomplete proposal qualification')
    return paths, development, baseline


def apply_proposals(records, metadata, proposals, proposed_records, *, expected_records=9, expected_spans=12):
    """Apply an exact finite patch; all other fields and all validation rows stay equal."""
    indexed, rows = validate_join(records, metadata)
    validate_partition_rows(metadata, capability='development')
    patches = {p['record_id']: p for p in proposals}
    drafts = {r['record_id']: r for r in proposed_records}
    require(len(patches) == len(proposals) == len(drafts) == len(proposed_records) == expected_records
            and set(patches) == set(drafts), 'finite proposal identity mismatch')
    output, ledger, changes_count = [], [], 0
    for original in records:
        rid = original['record_id']
        result = deepcopy(original)
        if rid in patches:
            proposal, draft = patches[rid], drafts[rid]
            require(rows[rid]['partition'] == original['split'] == proposal['partition'] == 'train',
                    'validation correction forbidden')
            require(proposal['disposition'] == 'propose_boundary_correction'
                    and proposal['original_reference_sha256'] == object_hash(original['entities'])
                    and proposal['original_revision'] == original['annotation_revision'], 'stale proposal reference')
            require(proposal['source_id'] == original['source']['source_id']
                    and proposal['source_sha256'] == original['source']['text_sha256']
                    and proposal['source_raw_sha256'] == original['source']['raw_sha256']
                    and proposal['text_sha256'] == original['text_sha256'], 'stale source evidence')
            metadata_fields = {'annotation_revision', 'reviewer', 'review_status', 'notes', 'entities'}
            require({k: v for k, v in draft.items() if k not in metadata_fields}
                    == {k: v for k, v in original.items() if k not in metadata_fields}, 'unauthorized draft change')
            ids = {e['id']: e for e in result['entities']}
            require(len(ids) == len(result['entities']) and proposal['changes'], 'missing occurrence IDs')
            changed_ids = set()
            for change in proposal['changes']:
                eid = change['entity_id']
                require(eid in ids and eid not in changed_ids, 'duplicate or unknown correction occurrence')
                changed_ids.add(eid)
                before, after = change['before'], change['proposed']
                require(set(before) == set(after) == {'start', 'end', 'text', 'label'}
                        and {k: ids[eid][k] for k in before} == before and after['label'] == before['label'],
                        'unauthorized entity/type change')
                require(type(after['start']) is int and type(after['end']) is int
                        and 0 <= after['start'] <= before['start'] < before['end'] == after['end'] <= len(original['text'])
                        and after['start'] < before['start'] and original['text'][after['start']:after['end']] == after['text'],
                        'source-exact boundary expansion required')
                evidence = change['source_evidence']
                require(evidence == {'start': original['passage_start'] + after['start'],
                        'end': original['passage_start'] + after['end'], 'text': after['text']}
                        and original['source']['text'][evidence['start']:evidence['end']] == evidence['text'],
                        'unsupported source occurrence')
                ids[eid].update(after)
                changes_count += 1
            require(result['entities'] == draft['entities'], 'draft differs from approved finite patch')
            result['annotation_revision'] = original['annotation_revision'] + '-corrected-boundaries-v19'
            result['reviewer'] = 'Codex AI-assisted silver correction; not human verified'
            result['notes'] = original['notes'] + ['v19: adopted finite source-bound boundary corrections; membership unchanged.']
            ledger.append({'record_id': rid, 'original_annotation_sha256': object_hash(original['entities']),
                'revised_annotation_sha256': object_hash(result['entities']), 'proposal_sha256': object_hash(proposal),
                'source_sha256': original['source']['text_sha256'], 'changes': proposal['changes'],
                'convention': proposal['convention'], 'original_revision': original['annotation_revision'],
                'revised_revision': result['annotation_revision'], 'quality': 'AI-assisted silver', 'human_verified': False})
        output.append(result)
    require(len(ledger) == expected_records and changes_count == expected_spans, 'approved correction totals differ')
    validate_join(output, metadata)
    return output, ledger


def config_values(text):
    parser = case_sensitive_parser(text)
    return {(section, key): value for section in parser.sections() for key, value in parser[section].items()}


def variant_template(baseline, variant, seed):
    require(variant in PARAMETERS, 'unknown configuration')
    verify_template(baseline, seed)
    parser = case_sensitive_parser(baseline)
    dropout, rate = PARAMETERS[variant]
    require(parser['training']['dropout'] == '0.1' and parser['training.optimizer']['learn_rate'] == '0.001'
            and parser['training']['patience'] == '175' and parser['training.optimizer']['L2'] == '0.01'
            and parser['training.optimizer']['L2_is_weight_decay'] == 'true', 'baseline recipe changed')
    parser['training']['dropout'], parser['training.optimizer']['learn_rate'] = dropout, rate
    stream = io.StringIO()
    parser.write(stream)
    text = stream.getvalue()
    verify_variant(text, baseline, variant, seed)
    return text


def verify_variant(text, baseline, variant, seed):
    require(variant in PARAMETERS, 'unknown configuration')
    verify_template(text, seed)
    expected = config_values(baseline)
    expected[('training', 'dropout')], expected[('training.optimizer', 'learn_rate')] = PARAMETERS[variant]
    require(config_values(text) == expected, 'unexpected experiment configuration difference')


def protocol():
    return {'schema': 'lanes-corrected-experiment-protocol-v1', 'scope': SCOPE,
        'variants': {v: {'dropout': float(d), 'learning_rate': float(lr)} for v, (d, lr) in PARAMETERS.items()},
        'screening_order': list(VARIANTS), 'tie_tolerance': EPSILON,
        'metric': 'full_precision_strict_validation_micro_f1', 'seeds': [0, 1, 2], 'maximum_runs': 7,
        'control_winner_runs': 5, 'historical_models_replace_control': False,
        'retention': 'variant seed-0 F1 and three-seed mean must both strictly exceed corrected control',
        'failure_policy': 'stop; preserve outputs; no retry or alternative configuration',
        'concurrent_training': False, 'destination_reuse': False, 'training_authorized': False,
        'holdout_access_authorized': False, 'guaranteed_score': None}


def schedule(outcomes):
    """Pure prefix validator. Returns a plan only; never dispatches a process."""
    require(isinstance(outcomes, list), 'ordered constructed or authentic outcomes required')
    pending = [(v, 0) for v in VARIANTS]
    completed, winner = {}, None
    for index, row in enumerate(outcomes):
        require(index < len(pending) and set(row) == {'variant', 'seed', 'state', 'f1'}, 'unexpected run outcome')
        key = (row['variant'], row['seed'])
        require(type(row['seed']) is int and key == pending[index] and key not in completed, 'invalid sequential run order')
        require(row['state'] in ('completed', 'failed'), 'unknown run outcome')
        if row['state'] == 'failed':
            require(row['f1'] is None and index == len(outcomes) - 1, 'failure stops the sequence')
            return {'state': 'stopped_on_failure', 'next': None, 'completed_runs': len(completed),
                    'screening_winner': winner, 'retained': None, 'training_started': False}
        score = row['f1']
        require(type(score) in (float, int) and math.isfinite(score) and 0 <= score <= 1, 'finite F1 in [0,1] required')
        completed[key] = score
        if index == 2:
            best = max(completed[(v, 0)] for v in VARIANTS)
            winner = next(v for v in VARIANTS if best - completed[(v, 0)] <= EPSILON)
            pending += [('control', 1), ('control', 2)]
            if winner != 'control':
                pending += [(winner, 1), (winner, 2)]
    next_run = pending[len(outcomes)] if len(outcomes) < len(pending) else None
    retained = None
    if next_run is None:
        retained = 'control'
        if winner != 'control' and completed[(winner, 0)] > completed[('control', 0)] and (
                sum(completed[(winner, s)] for s in range(3)) > sum(completed[('control', s)] for s in range(3))):
            retained = winner
    return {'state': 'planned_next_run' if next_run else 'complete', 'next': list(next_run) if next_run else None,
            'completed_runs': len(completed), 'screening_winner': winner, 'retained': retained, 'training_started': False}


def verify_result(root, grant_path, output):
    grant = read(grant_path)
    _, development, baseline = verify_grant(root, grant)
    output = Path(output).resolve()
    receipt = read(output / 'preparation-result.json')
    require(receipt['grant_sha256'] == digest(grant_path) and receipt['training_authorized'] is False
            and receipt['training_performed'] is False, 'stale or unsafe preparation result')
    for name, sha in receipt['files'].items():
        require(digest(safe_path(output, name)) == sha, 'prepared file hash changed')
    for variant in VARIANTS:
        package = output / 'packages' / variant
        verify_package(root, package, safe_path(root, grant['model_directory']))
        for seed in range(3):
            verify_variant((package / f'train-seed-{seed}.cfg').read_text(encoding='utf-8'),
                (baseline / f'train-seed-{seed}.cfg').read_text(encoding='utf-8'), variant, seed)
    for name in ('dev.spacy', 'tokenizer.bin', 'partitions.json', 'source-only-join-metadata.json'):
        require(digest(output / 'development' / name) == digest(development / name), 'frozen development bytes changed')
    require(read(output / 'experiment-protocol.json') == protocol(), 'future protocol changed')
    return {'state': 'verified_read_only', 'counts': {'train': 345, 'dev': 60}, 'packages': len(VARIANTS),
            'training_authorized': False, 'training_started': False, 'gpu_verified': False}


def prepare(root, grant_path, interpreter, output):
    root, output = Path(root).resolve(), Path(output).absolute()
    grant = read(grant_path)
    verify_grant(root, grant)
    artifacts = root / 'backend/training/flood_ner/artifacts'
    require(output.resolve().is_relative_to(artifacts) and not output.exists(), 'new private output required')
    safe_path(root, output.relative_to(root).as_posix())
    require(Path(interpreter).is_file(), 'existing qualified CPU interpreter required')
    lock_path = artifacts / 'corrected-experiment-preparation-active.lock'
    with lock_path.open('x', encoding='utf-8') as lock:
        lock.write(str(output))
    try:
        # Single-use even after a failure: partial outputs and the claim remain evidence.
        claim = artifacts / ('corrected-experiment-claim-' + digest(grant_path) + '.json')
        write_new(claim, {'grant_sha256': digest(grant_path), 'output': str(output)})
        output.mkdir()
        request = output / 'worker-request.json'
        write_new(request, {'root': str(root), 'grant': str(Path(grant_path).resolve()),
                            'grant_sha256': digest(grant_path), 'output': str(output)})
        worker = root / 'backend/training/flood_ner/successor_experiment_worker.py'
        with (output / 'worker.stdout').open('xb') as stdout, (output / 'worker.stderr').open('xb') as stderr:
            process = subprocess.run([str(Path(interpreter).resolve()), '-I', '-B', str(worker), str(request)],
                                     cwd=root, stdout=stdout, stderr=stderr, check=False, timeout=240)
        require(process.returncode == 0, 'CPU qualification failed; preserve worker logs and partial output')
        return verify_result(root, grant_path, output)
    finally:
        lock_path.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('checkout', 'grant', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--python', type=Path)
    parser.add_argument('--prepare', action='store_true', help='Explicitly create exports; never trains')
    args = parser.parse_args()
    require(not args.prepare or args.python is not None, 'explicit interpreter required for preparation')
    result = prepare(args.checkout, args.grant, args.python, args.output) if args.prepare else verify_result(
        args.checkout, args.grant, args.output)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
