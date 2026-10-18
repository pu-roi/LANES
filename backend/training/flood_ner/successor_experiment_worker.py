"""Pinned CPU tokenizer/serialization/schema qualification; no pipeline or inference."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import platform
import sys
from types import SimpleNamespace


def schema_qualification(package, baseline, variant, output):
    from confection import Config
    from spacy.schemas import ConfigSchema
    from spacy.util import registry
    from training.flood_ner.successor_training import render_config
    from training.flood_ner.successor_experiment_preparation import digest, require, verify_variant
    # Import registry factories only. Do not call their pipeline callbacks.
    from training.flood_ner import experiment_registry  # noqa: F401

    verified = []
    for seed in range(3):
        template = (package / f'train-seed-{seed}.cfg').read_text(encoding='utf-8')
        verify_variant(template, (baseline / f'train-seed-{seed}.cfg').read_text(encoding='utf-8'), variant, seed)
        checkpoint = output / f'schema-only-{variant}-{seed}'
        require(not checkpoint.exists(), 'schema destination already exists')
        config = Config().from_str(render_config(template, {'TRAIN': package / 'train.spacy',
            'DEV': package / 'dev.spacy', 'TOKENIZER': package / 'tokenizer.bin',
            'MODEL_MANIFEST': package / 'model-contract.json',
            'MODEL_MANIFEST_SHA256': digest(package / 'model-contract.json'), 'CHECKPOINT': checkpoint}), interpolate=True)
        resolved = registry.resolve(config, schema=ConfigSchema, validate=True)
        require(not resolved['training']['optimizer'].nr_update and not checkpoint.exists(),
                'schema resolution performed updates or wrote a checkpoint')
        verified.append({'seed': seed, 'config_sha256': digest(package / f'train-seed-{seed}.cfg'),
                         'optimizer_updates': 0})
    return {'state': 'configuration_schema_verified', 'variant': variant, 'configs': verified,
            'python_version': platform.python_version(), 'spacy_version': '3.7.5',
            'pipeline_created': False, 'pretrained_weights_loaded': False, 'training_started': False}


def qualify_records(records, tokenizer):
    from training.flood_ner.annotation.schema import AnnotationRecord
    from training.flood_ner.annotation.validation import validate_record
    from training.flood_ner.successor_experiment_preparation import require
    parsed = []
    for raw in records:
        require(raw.get('split') in ('train', 'dev') and raw.get('complete') is True
                and raw.get('review_status') == 'accepted' and isinstance(raw.get('entities'), list)
                and raw.get('annotation_profile') == 'location-only-v1', 'incomplete or forbidden reference')
        record = AnnotationRecord.model_validate_json(json.dumps(raw, ensure_ascii=False))
        require(record.source.admission_status == 'training_admitted' and record.source.reuse_status == 'allowed'
                and record.quality == 'silver', 'unsupported source use or reference quality')
        require(not validate_record(record, SimpleNamespace(make_doc=tokenizer)), 'schema/source/alignment validation failed')
        parsed.append((record, raw['split']))
    return parsed


def verify_docbin(path, records, vocab):
    from spacy.tokens import DocBin
    from training.flood_ner.successor_experiment_preparation import require
    docs = list(DocBin().from_bytes(path.read_bytes()).get_docs(vocab))
    require(len(docs) == len(records), 'DocBin record count mismatch')
    for doc, (record, _) in zip(docs, records):
        require(doc.user_data.get('record_id') == record.record_id and doc.text == record.text
                and [(e.start_char, e.end_char, e.label_) for e in doc.ents]
                == [(e.start, e.end, e.label) for e in record.entities], 'DocBin identity/reference reload mismatch')


def main():
    import spacy
    from spacy.tokenizer import Tokenizer
    from spacy.vocab import Vocab
    if sys.version_info[:2] != (3, 11) or spacy.__version__ != '3.7.5':
        raise ValueError('qualified Python 3.11 / spaCy 3.7.5 required')
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    if set(request) != {'root', 'grant', 'grant_sha256', 'output'}:
        raise ValueError('preparation-only worker request required')
    root, output = Path(request['root']).resolve(), Path(request['output']).resolve()
    sys.path.append(str(root / 'backend/.venv/Lib/site-packages'))
    sys.path.insert(0, str(root / 'backend'))
    from training.flood_ner.successor_experiment_preparation import (
        SCOPE, VARIANTS, IMPLEMENTATION, apply_proposals, digest, lines, object_hash, protocol,
        read, require, safe_path, variant_template, verify_grant, write_new)
    from training.flood_ner.successor_export_worker import serialize
    from training.flood_ner.successor_training import PAYLOAD_FILES, verify_package
    from training.flood_ner.experiment_registry import verified_model

    require(digest(request['grant']) == request['grant_sha256'], 'stale worker grant')
    grant = read(request['grant'])
    paths, development, baseline = verify_grant(root, grant)
    artifacts = root / 'backend/training/flood_ner/artifacts'
    require(output.is_relative_to(artifacts) and output.is_dir()
            and (artifacts / 'corrected-experiment-preparation-active.lock').read_text(encoding='utf-8') == str(output)
            and not (output / 'preparation-result.json').exists(), 'inactive or reused worker destination')
    safe_path(root, output.relative_to(root).as_posix())
    spacy.require_cpu()
    original = lines(development / 'admitted-records.jsonl')
    metadata = read(development / 'partitions.json')['members']
    proposals = lines(paths['proposals'])
    for proposal in proposals:
        from training.flood_ner.development_error_audit import bound
        bound(root, proposal['convention'])
    revised, ledger = apply_proposals(original, metadata, proposals, lines(paths['proposed_records']))
    validation_reviews = lines(paths['validation_review'])
    require(len(validation_reviews) == 60 and len({r['record_id'] for r in validation_reviews}) == 60
            and {r['record_id'] for r in validation_reviews} == {r['record_id'] for r in original if r['split'] == 'dev'}
            and all(r['annotation_changed'] is False for r in validation_reviews), 'validation review mismatch')
    contract = read(baseline / 'model-contract.json')
    contract['model_dir'] = str(safe_path(root, grant['model_directory']))
    write_new(output / 'runtime-model-contract.json', contract)
    model = verified_model(str(output / 'runtime-model-contract.json'), digest(output / 'runtime-model-contract.json'))
    tokenizer_bytes = (development / 'tokenizer.bin').read_bytes()
    require(digest(development / 'tokenizer.bin') == '3f666f61346b7196d931ab9781a3d83f41d688e24b298e8e494b3d92c384a588',
            'frozen tokenizer mismatch')
    tokenizer = Tokenizer(Vocab().from_disk(model / 'vocab')).from_bytes(tokenizer_bytes, exclude=['vocab'])
    old_parsed = qualify_records(original, tokenizer)
    parsed = qualify_records(revised, tokenizer)
    for partition in ('train', 'dev'):
        verify_docbin(development / f'{partition}.spacy', [r for r in old_parsed if r[1] == partition], tokenizer.vocab)
    export = output / 'development'
    export.mkdir()
    files = serialize(parsed, tokenizer, tokenizer_bytes, export, 'development')
    for partition in ('train', 'dev'):
        verify_docbin(export / f'{partition}.spacy', [r for r in parsed if r[1] == partition], tokenizer.vocab)
    require(files['train.spacy'] != digest(development / 'train.spacy'), 'corrected training export did not change')
    require(files['dev.spacy'] == digest(development / 'dev.spacy')
            and files['tokenizer.bin'] == digest(development / 'tokenizer.bin'), 'validation/tokenizer bytes changed')
    for name in ('partitions.json', 'source-only-join-metadata.json'):
        with (export / name).open('xb') as stream:
            stream.write((development / name).read_bytes())
        files[name] = digest(export / name)
    write_new(output / 'correction-adoption-ledger.json', {'scope': SCOPE, 'records': ledger,
        'span_corrections': sum(len(r['changes']) for r in ledger), 'human_verified': False,
        'parent_status_sha256': digest(paths['development_status']), 'historical_anchors_preserved': 280})
    status = read(paths['development_status'])
    status['files'] = files
    status['revision_scope'] = 'development annotation derivative; original global partitions preserved'
    status['preparation_grant_sha256'] = digest(request['grant'])
    status['parent_export_sha256'] = digest(paths['development_status'])
    # Actual counts and support are derived from the validated revised records.
    status['counts'] = dict(Counter(split for _, split in parsed))
    status['labels'] = {split: dict(sorted(Counter(e.label for r, s in parsed if s == split for e in r.entities).items()))
                        for split in ('train', 'dev')}
    status['languages'] = {split: dict(Counter(r.passage_language for r, s in parsed if s == split))
                           for split in ('train', 'dev')}
    status['serialization_reload_verified'] = True
    write_new(export / 'aggregate-status.json', status)
    write_new(output / 'development-revision-manifest.json', {
        'schema': 'lanes-corrected-development-revision-v1', 'scope': SCOPE,
        'parent_admission_manifest_sha256': read(baseline / 'handoff-manifest.json')['dataset_manifest_sha256'],
        'parent_export_sha256': digest(paths['development_status']), 'counts': status['counts'],
        'revised_records_sha256': digest(export / 'admitted-records.jsonl'),
        'qualified_export_sha256': digest(export / 'aggregate-status.json'),
        'correction_ledger_sha256': digest(output / 'correction-adoption-ledger.json'),
        'partition_metadata_sha256': digest(export / 'partitions.json'),
        'historical_anchors_preserved': 280, 'holdout_revision': 'unchanged; unopened', 'human_verified': False})
    write_new(output / 'experiment-protocol.json', protocol())
    write_new(output / 'validation-policy.json', {'reference_changed': False,
        'question': 'Unresolved generic gymnasium versus named school LANDMARK boundary; retain frozen reference.',
        'review_sha256': digest(paths['validation_review']), 'independent_human_adjudication': False})
    packages = output / 'packages'
    packages.mkdir()
    implementation = [{'path': p, 'sha256': digest(root / p)} for p in IMPLEMENTATION if p.rsplit('/', 1)[1] in (
        'successor_preparation.py', 'successor_export_worker.py', 'successor_training.py', 'experiment_registry.py')]
    schema_reports = []
    for variant in VARIANTS:
        package = packages / variant
        package.mkdir()
        for name in ('train.spacy', 'dev.spacy', 'tokenizer.bin'):
            with (package / name).open('xb') as stream:
                stream.write((export / name).read_bytes())
        for name in ('model-contract.json', 'evaluation-contract.json', 'gpu-qualification.json', 'gpu-runtime.json'):
            with (package / name).open('xb') as stream:
                stream.write((baseline / name).read_bytes())
        write_new(package / 'qualification.json', status)
        for seed in range(3):
            text = variant_template((baseline / f'train-seed-{seed}.cfg').read_text(encoding='utf-8'), variant, seed)
            with (package / f'train-seed-{seed}.cfg').open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
        parent = read(baseline / 'handoff-manifest.json')
        manifest = {'schema': 'lanes-successor-training-handoff-v1', 'scope': 'limited_provenance_silver_research',
            'counts': status['counts'], 'files': {name: digest(package / name) for name in sorted(PAYLOAD_FILES)},
            'implementation': implementation, 'dataset_manifest_sha256': digest(output / 'development-revision-manifest.json'),
            'partition_manifest_sha256': parent['partition_manifest_sha256'],
            'parent_annotation_manifest_sha256': parent['dataset_manifest_sha256'],
            'development_revision_sha256': digest(output / 'correction-adoption-ledger.json'),
            'preparation_grant_sha256': digest(request['grant']), 'experiment_protocol_sha256': digest(output / 'experiment-protocol.json'),
            'variant': variant, 'training_authorized': False, 'training_started': False,
            'desktop_gpu_verified_for_this_handoff': False, 'private_delivery_complete': False}
        write_new(package / 'handoff-manifest.json', manifest)
        verify_package(root, package, model)
        schema_reports.append(schema_qualification(package, baseline, variant, output))
    write_new(output / 'cpu-qualification.json', {'configs': schema_reports, 'records_qualified': len(parsed),
        'corrected_records': len(ledger), 'corrected_spans': sum(len(r['changes']) for r in ledger),
        'validation_unchanged': True, 'tokenizer_unchanged': True, 'historical_anchors_preserved': 280,
        'serialization_reload_verified': True, 'inference_performed': False, 'training_performed': False,
        'holdout_opened': False, 'gpu_verified': False})
    inventory = {p.relative_to(output).as_posix(): digest(p) for p in output.rglob('*') if p.is_file()
                 and p.name not in ('worker.stdout', 'worker.stderr')}
    write_new(output / 'preparation-result.json', {'schema': 'lanes-corrected-experiment-result-v1',
        'scope': SCOPE, 'grant_sha256': digest(request['grant']), 'files': inventory,
        'counts': status['counts'], 'qualified_configs': len(schema_reports) * 3,
        'training_authorized': False, 'training_performed': False, 'holdout_accessed': False,
        'private_delivery_complete': False, 'desktop_gpu_verified': False})
    print(json.dumps({'state': 'qualified', 'counts': status['counts'], 'configs': 9, 'training_started': False}))


if __name__ == '__main__':
    main()
