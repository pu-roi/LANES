"""Pinned CPU tokenizer/schema qualification. No inference or training capability."""
from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
import shutil
import sys


def deny_execution():
    """Model graph resolution is allowed; pipelines/transport/updates are not."""
    from spacy.language import Language
    def forbidden(*args, **kwargs):
        raise RuntimeError('qualification forbids pipeline initialization, inference and updates')
    for name in ('initialize', 'begin_training', 'resume_training', 'update', '__call__', 'pipe'):
        setattr(Language, name, forbidden)
    def audit(event, args):
        if event in {'socket.connect', 'socket.bind', 'socket.getaddrinfo', 'socket.sendto',
                     'subprocess.Popen', 'os.system', 'os.posix_spawn'}:
            raise RuntimeError('offline qualification forbids network and child processes')
    sys.addaudithook(audit)


def qualification(package, control, output):
    from confection import Config
    from spacy.schemas import ConfigSchema
    from spacy.util import registry
    from training.flood_ner.regularization_experiment import digest, require, verify_candidate
    from training.flood_ner.successor_training import render_config
    from training.flood_ner import experiment_registry  # noqa: F401
    reports = []
    for seed in range(3):
        text = (package / f'train-seed-{seed}.cfg').read_text(encoding='utf-8')
        verify_candidate(text, (control / f'train-seed-{seed}.cfg').read_text(encoding='utf-8'), seed)
        checkpoint = output / f'uncreated-schema-checkpoint-{seed}'
        config = Config().from_str(render_config(text, {
            'TRAIN': package / 'train.spacy', 'DEV': package / 'dev.spacy',
            'TOKENIZER': package / 'tokenizer.bin', 'MODEL_MANIFEST': package / 'model-contract.json',
            'MODEL_MANIFEST_SHA256': digest(package / 'model-contract.json'), 'CHECKPOINT': checkpoint}), interpolate=True)
        resolved = registry.resolve(config, schema=ConfigSchema, validate=True)
        optimizer = resolved['training']['optimizer']
        require(optimizer.L2 == 0.05 and optimizer.L2_is_weight_decay is True and optimizer.learn_rate == 0.001
                and not optimizer.nr_update and not checkpoint.exists(), 'resolved optimizer or schema qualification differs')
        reports.append({'seed': seed, 'L2': optimizer.L2, 'L2_is_weight_decay': optimizer.L2_is_weight_decay,
                        'optimizer_updates': 0, 'config_sha256': digest(package / f'train-seed-{seed}.cfg')})
    return reports


def verify_serialization(path, parsed, tokenizer):
    from spacy.tokens import DocBin
    from training.flood_ner.successor_experiment_worker import verify_docbin
    from training.flood_ner.regularization_experiment import require
    verify_docbin(path, parsed, tokenizer.vocab)
    data = path.read_bytes()
    # from_bytes restores user_data but does not enable its reserialization.
    # Match the frozen serializer's explicit store_user_data=True contract.
    binary = DocBin(store_user_data=True).from_bytes(data)
    require(binary.to_bytes() == data, 'DocBin byte serialization/reload differs')
    docs = list(binary.get_docs(tokenizer.vocab))
    for doc, (record, _) in zip(docs, parsed):
        fresh = tokenizer(record.text)
        signature = lambda d: [(t.text, t.idx, t.whitespace_) for t in d]
        require(signature(doc) == signature(fresh), 'frozen tokenizer signature differs')
        require(all(fresh.char_span(e.start, e.end, alignment_mode='strict') is not None for e in record.entities),
                'strict entity alignment differs')
    return len(docs)


def main():
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    if set(request) != {'root', 'grant', 'grant_sha256', 'output'}:
        raise ValueError('preparation-only worker request required')
    root, output = Path(request['root']).resolve(), Path(request['output']).resolve()
    handles = []
    if sys.platform == 'win32':
        for relative in ('torch/lib', 'nvidia/cuda_runtime/bin', 'nvidia/cuda_nvrtc/bin'):
            directory = Path(sys.prefix) / 'Lib/site-packages' / relative
            if directory.is_dir(): handles.append(os.add_dll_directory(str(directory)))
    import torch
    import spacy
    from spacy.tokenizer import Tokenizer
    from spacy.vocab import Vocab
    if sys.version_info[:2] != (3, 11) or spacy.__version__ != '3.7.5':
        raise ValueError('existing Python 3.11/spaCy 3.7.5 required')
    spacy.require_cpu(); torch.set_num_threads(2)
    sys.path.insert(0, str(root / 'backend'))
    # Reuse installed pure-Python schema utilities; never install dependencies.
    sys.path.append(str(root / 'backend/.venv/Lib/site-packages'))
    from training.flood_ner.regularization_experiment import (
        SCOPE, PAYLOAD_FILES, SIDECARS, candidate_template, checked_baseline, digest,
        protocol, read, require, verify_grant, verify_preservation, verify_portable, write_new)
    from training.flood_ner.development_error_audit import validate_join
    from training.flood_ner.successor_preparation import validate_partition_rows
    from training.flood_ner.successor_experiment_worker import qualify_records
    from training.flood_ner.experiment_registry import verified_model
    require(digest(request['grant']) == request['grant_sha256'], 'stale worker grant')
    grant = read(request['grant'])
    paths, development, baseline, resources = verify_grant(root, grant)
    require(sys.version.split()[0] == grant['runtime']['version'] and
            Path(sys.executable).resolve() == Path(grant['runtime']['python']).resolve()
            and digest(Path(sys.executable)) == grant['runtime']['sha256'], 'worker runtime mismatch')
    require((root / 'backend/training/flood_ner/artifacts/regularization-preparation-active.lock').read_text(encoding='utf-8')
            == str(output) and output.is_dir() and not (output / 'preparation-result.json').exists(), 'inactive or reused worker')
    deny_execution()
    preserved = verify_preservation(root, paths['preservation'])
    records = [json.loads(line) for line in (development / 'admitted-records.jsonl').read_text(encoding='utf-8').splitlines()]
    metadata = read(development / 'partitions.json')['members']
    validate_join(records, metadata); validate_partition_rows(metadata, capability='development')
    # Resource relocation is private, for tokenizer/vocabulary reads only.
    contract = read(baseline / 'model-contract.json'); contract['model_dir'] = str(resources)
    write_new(output / 'runtime-model-contract.json', contract)
    model = verified_model(str(output / 'runtime-model-contract.json'), digest(output / 'runtime-model-contract.json'))
    tokenizer_bytes = (development / 'tokenizer.bin').read_bytes()
    tokenizer = Tokenizer(Vocab().from_disk(model / 'vocab')).from_bytes(tokenizer_bytes, exclude=['vocab'])
    require(tokenizer.to_bytes(exclude=['vocab']) == tokenizer_bytes, 'tokenizer reload changed')
    parsed = qualify_records(records, tokenizer)
    sizes = {s: verify_serialization(development / f'{s}.spacy', [r for r in parsed if r[1] == s], tokenizer)
             for s in ('train', 'dev')}
    experiment = output / 'experiment'; experiment.mkdir()
    package = experiment / 'package'; package.mkdir()
    controls = experiment / 'control-configs'; controls.mkdir()
    for name in PAYLOAD_FILES - {'evaluation-contract.json', *(f'train-seed-{s}.cfg' for s in range(3))}:
        shutil.copyfile(baseline / name, package / name)
    for seed in range(3):
        name = f'train-seed-{seed}.cfg'
        shutil.copyfile(baseline / name, controls / name)
        with (package / name).open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(candidate_template((baseline / name).read_text(encoding='utf-8'), seed))
    evaluation = read(baseline / 'evaluation-contract.json')
    evaluation.update(holdout_access='none; completed comparison must not be repeated',
        evaluation='Development-only experimental selection; no additional research-holdout predictions.',
        repeat_holdout_evaluation_authorized=False, completed_holdout_comparison=True,
        validation_is_reused=True, claim_unbiased_new_test_improvement=False)
    write_new(package / 'evaluation-contract.json', evaluation)
    shutil.copyfile(paths['baseline_metrics'], experiment / 'baseline-metrics.json')
    checked_baseline(read(experiment / 'baseline-metrics.json'))
    shutil.copyfile(development / 'source-only-join-metadata.json', experiment / 'development-slices.json')
    write_new(experiment / 'experiment-protocol.json', protocol(digest(experiment / 'baseline-metrics.json')))
    parent = read(baseline / 'handoff-manifest.json')
    manifest = dict(parent)
    manifest.update(files={name: digest(package / name) for name in sorted(PAYLOAD_FILES)},
        variant='stronger_weight_decay', experiment_protocol_sha256=digest(experiment / 'experiment-protocol.json'),
        preparation_grant_sha256=request['grant_sha256'], training_authorized=False, training_started=False,
        desktop_gpu_verified_for_this_handoff=False, private_delivery_complete=False,
        parent_control_handoff_sha256=digest(baseline / 'handoff-manifest.json'))
    write_new(package / 'handoff-manifest.json', manifest)
    schemas = qualification(package, controls, output)
    qualification_receipt = {'schema': 'lanes-regularization-cpu-qualification-v1', 'state': 'qualified',
        'counts': sizes, 'records_qualified': len(parsed), 'configuration_schemas_verified': len(schemas), 'configs': schemas,
        'languages': {s: dict(Counter(r.passage_language for r, split in parsed if split == s)) for s in sizes},
        'labels': {s: dict(Counter(e.label for r, split in parsed if split == s for e in r.entities)) for s in sizes},
        'python_version': sys.version.split()[0], 'spacy_version': spacy.__version__,
        'serialization_reload_verified': True, 'tokenizer_unchanged': True, 'annotations_unchanged': True,
        'membership_grouping_unchanged': True, 'historical_anchors_preserved_by_identical_partitions': 280,
        'export_hashes': {n: digest(package / n) for n in ('train.spacy', 'dev.spacy', 'tokenizer.bin')},
        'source_partition_sha256': digest(development / 'partitions.json'),
        'optimizer_updates': 0, 'pipeline_created': False, 'pretrained_neural_weights_loaded': False,
        'inference_performed': False, 'training_performed': False, 'holdout_accessed': False,
        'gpu_verified': False, 'private_delivery_complete': False, 'preserved': preserved}
    write_new(experiment / 'cpu-qualification.json', qualification_receipt)
    experiment_manifest = {'schema': 'lanes-regularization-handoff-v1', 'scope': SCOPE,
        'grant_sha256': request['grant_sha256'], 'training_authorized': False,
        'implementation': grant['implementation'], 'tests': grant['tests'],
        'baseline_control_sha256': digest(baseline / 'handoff-manifest.json'),
        'files': {p.relative_to(experiment).as_posix(): digest(p) for p in experiment.rglob('*') if p.is_file()}}
    write_new(experiment / 'experiment-manifest.json', experiment_manifest)
    verify_portable(root, experiment, resources, digest(experiment / 'experiment-manifest.json'))
    verify_preservation(root, paths['preservation'])
    write_new(output / 'preparation-result.json', {'schema': 'lanes-regularization-result-v1', 'scope': SCOPE,
        'grant_sha256': request['grant_sha256'], 'counts': sizes, 'training_performed': False, 'holdout_accessed': False,
        'files': {p.relative_to(output).as_posix(): digest(p) for p in output.rglob('*') if p.is_file()
                  and p.name not in ('worker.stdout', 'worker.stderr')}})
    print(json.dumps({'state': 'qualified', 'counts': sizes, 'configs': len(schemas),
                      'training_started': False, 'holdout_accessed': False}), flush=True)


if __name__ == '__main__':
    main()
