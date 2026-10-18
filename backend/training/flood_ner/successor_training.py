"""Portable successor trainer handoff. Default operation only verifies files.

Only an explicit --start-training action may create a run and invoke spaCy.
Research-holdout artifacts are deliberately outside this module's capability.
"""
from __future__ import annotations

import argparse
import configparser
import json
from pathlib import Path
import re
import subprocess
import sys
import io
import uuid

if __package__:
    from .successor_preparation import digest, inside, read, require, write_new
else:
    # This script is also the explicit pinned-interpreter training subprocess.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from training.flood_ner.successor_preparation import digest, inside, read, require, write_new

PAYLOAD_FILES = frozenset({'train.spacy', 'dev.spacy', 'tokenizer.bin', 'model-contract.json',
    'qualification.json', 'evaluation-contract.json', 'train-seed-0.cfg', 'train-seed-1.cfg', 'train-seed-2.cfg',
    'gpu-qualification.json', 'gpu-runtime.json'})
TOKENS = {'TRAIN', 'DEV', 'TOKENIZER', 'MODEL_MANIFEST', 'MODEL_MANIFEST_SHA256', 'CHECKPOINT'}


def case_sensitive_parser(text):
    parser = configparser.RawConfigParser()
    parser.optionxform = str
    parser.read_string(text)
    return parser


def portable_template(recipe, seed):
    """Change only portable bindings/seed; preserve spaCy's case-sensitive keys."""
    require(type(seed) is int and seed in (0, 1, 2), 'supported seed required')
    parser = case_sensitive_parser(recipe)
    changes = {('paths', 'train'): '"@@TRAIN@@"', ('paths', 'dev'): '"@@DEV@@"',
        ('system', 'seed'): str(seed), ('nlp.tokenizer', 'model_manifest'): '"@@MODEL_MANIFEST@@"',
        ('nlp.tokenizer', 'manifest_sha256'): '"@@MODEL_MANIFEST_SHA256@@"',
        ('nlp.tokenizer', 'tokenizer_file'): '"@@TOKENIZER@@"',
        ('initialize.after_init', 'model_manifest'): '"@@MODEL_MANIFEST@@"',
        ('initialize.after_init', 'manifest_sha256'): '"@@MODEL_MANIFEST_SHA256@@"',
        ('training.before_to_disk', 'output'): '"@@CHECKPOINT@@"'}
    for (section, key), value in changes.items():
        require(parser.has_option(section, key), 'declared recipe field missing')
        parser[section][key] = value
    stream = io.StringIO()
    parser.write(stream)
    text = stream.getvalue()
    verify_template(text, seed)
    return text


def verify_template(text, seed):
    require(set(re.findall(r'@@([A-Z0-9_]+)@@', text)) == TOKENS, 'config relocation fields differ')
    require(not re.search(r'(?i)(holdout|test\.spacy|\[corpora\.test\])', text), 'holdout supplied to trainer')
    parser = case_sensitive_parser(text)
    require(set(parser['paths']) == {'train', 'dev', 'vectors', 'init_tok2vec'} and
            parser['system']['seed'] == str(seed), 'wrong training corpus or seed')
    require(parser['corpora.train']['path'] == '${paths.train}' and
            parser['corpora.dev']['path'] == '${paths.dev}', 'corpus path escape')
    require(parser['paths']['train'] == '"@@TRAIN@@"' and parser['paths']['dev'] == '"@@DEV@@"',
            'nonportable corpora')
    require(parser['training']['max_steps'] == '1000' and parser['training']['max_epochs'] == '30'
            and parser['training']['eval_frequency'] == '35' and parser['training.batcher']['size'] == '8',
            'declared recipe changed')
    require(parser.has_section('training.optimizer') and
            {'L2', 'L2_is_weight_decay'} <= set(parser['training.optimizer']) and
            not {'l2', 'l2_is_weight_decay'} & set(parser['training.optimizer']),
            'case-sensitive optimizer keys L2 and L2_is_weight_decay required')
    require(parser.has_option('components.ner.model', 'nO') and
            not parser.has_option('components.ner.model', 'no'),
            'case-sensitive architecture key nO required')


def validate_config_schemas(preparation):
    """Resolve actual spaCy schemas/factories without creating a pipeline or updates.

    Config parsing alone misses invalid registry arguments. Resolution constructs
    uninitialized model graphs and an unused optimizer; it never initializes a
    Language pipeline, invokes training callbacks, reads examples or calls train.
    """
    import importlib.util
    import platform
    import spacy
    from confection import Config
    from spacy.schemas import ConfigSchema
    from spacy.util import registry

    require(sys.version_info[:2] == (3, 11) and spacy.__version__ == '3.7.5',
            'qualified Python 3.11 / spaCy 3.7.5 required for schema validation')
    registry_path = Path(__file__).resolve().with_name('experiment_registry.py')
    spec = importlib.util.spec_from_file_location('lanes_successor_validation_registry', registry_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    package = Path(preparation).resolve()
    for seed in (0, 1, 2):
        template = (package / f'train-seed-{seed}.cfg').read_text(encoding='utf-8')
        verify_template(template, seed)
        checkpoint = Path(__file__).resolve().parent / 'artifacts' / ('schema-only-' + uuid.uuid4().hex)
        text = render_config(template, {'TRAIN': package / 'train.spacy', 'DEV': package / 'dev.spacy',
            'TOKENIZER': package / 'tokenizer.bin', 'MODEL_MANIFEST': package / 'model-contract.json',
            'MODEL_MANIFEST_SHA256': digest(package / 'model-contract.json'), 'CHECKPOINT': checkpoint})
        config = Config().from_str(text, interpolate=True)
        resolved = registry.resolve(config, schema=ConfigSchema, validate=True)
        require(not resolved['training']['optimizer'].nr_update, 'schema check must not update an optimizer')
        require(not checkpoint.exists(), 'schema check wrote a checkpoint')
    return {'state': 'configuration_schema_verified', 'seeds': [0, 1, 2],
            'python_version': platform.python_version(), 'spacy_version': spacy.__version__,
            'optimizer_updates': 0, 'pipeline_created': False, 'pretrained_weights_loaded': False,
            'training_started': False}


def validate_runtime_configs(interpreter, preparation):
    result = subprocess.run([str(Path(interpreter).resolve()), '-I', '-B', str(Path(__file__).resolve()),
                            '--internal-config-validation', str(Path(preparation).resolve())],
                            check=False, capture_output=True, text=True, timeout=120)
    require(result.returncode == 0, 'spaCy configuration schema validation failed before training:\n'
            + result.stderr[-6000:])
    report = json.loads(result.stdout)
    require(report.get('state') == 'configuration_schema_verified' and report.get('seeds') == [0, 1, 2]
            and report.get('spacy_version') == '3.7.5' and report.get('optimizer_updates') == 0
            and report.get('pipeline_created') is False and report.get('pretrained_weights_loaded') is False
            and report.get('training_started') is False, 'invalid schema qualification response')
    return report


def verify_package(checkout, preparation, model_dir):
    checkout, preparation, model_dir = map(lambda p: Path(p).resolve(), (checkout, preparation, model_dir))
    require(preparation.is_dir() and model_dir.is_dir(), 'private payload and pinned model required')
    manifest = read(preparation / 'handoff-manifest.json')
    require(manifest.get('schema') == 'lanes-successor-training-handoff-v1'
            and manifest.get('counts') == {'train': 345, 'dev': 60}
            and manifest.get('training_started') is False, 'not the qualified successor development handoff')
    require(set(manifest['files']) == PAYLOAD_FILES, 'unexpected trainer payload capability')
    require({p.relative_to(preparation).as_posix() for p in preparation.rglob('*') if p.is_file()}
            == PAYLOAD_FILES | {'handoff-manifest.json'}, 'unmanifested trainer payload file')
    require({item['path'] for item in manifest['implementation']} == {
        'backend/training/flood_ner/' + name for name in
        ('successor_preparation.py', 'successor_export_worker.py', 'successor_training.py', 'experiment_registry.py')},
        'missing trainer implementation bindings')
    for name, expected in manifest['files'].items():
        path = inside(preparation, name)
        require(path.is_file() and digest(path) == expected, 'trainer payload hash changed')
    for item in manifest['implementation']:
        path = inside(checkout, item['path'])
        require(path.is_file() and digest(path) == item['sha256'], 'trainer implementation hash changed')
    qualification = read(preparation / 'qualification.json')
    require(qualification.get('capability') == 'development' and qualification.get('counts') == manifest['counts']
            and qualification.get('serialization_reload_verified') is True, 'unqualified development exports')
    for name in ('train.spacy', 'dev.spacy', 'tokenizer.bin'):
        require(qualification['files'][name] == manifest['files'][name], 'export qualification mismatch')
    contract = read(preparation / 'evaluation-contract.json')
    require(contract.get('scope') == 'limited_provenance_silver_research'
            and contract.get('certified_fresh') is False and contract.get('human_gold') is False,
            'evaluation limitations missing')
    model = read(preparation / 'model-contract.json')
    require(model.get('revision') == '51a40433059d8a2c25b98a48eca854f8789a491a'
            and model.get('version') == '0.1.0' and len(model.get('files', [])) == 23, 'wrong model contract')
    require(len({r['path'] for r in model['files']}) == 23, 'duplicate model identity')
    for row in model['files']:
        path = inside(model_dir, row['path'])
        require(path.is_file() and path.stat().st_size == row['bytes'] and digest(path) == row['sha256'],
                'pinned model bytes differ')
    require({p.relative_to(model_dir).as_posix() for p in model_dir.rglob('*') if p.is_file()}
            == {r['path'] for r in model['files']}, 'unmanifested model files')
    for seed in range(3):
        verify_template((preparation / f'train-seed-{seed}.cfg').read_text(encoding='utf-8'), seed)
    return manifest


def probe(interpreter, *, gpu=False):
    """No pipelines, documents, optimizer or inference; read-only runtime/device check."""
    code = ('import json,platform,spacy; '
            'r={"python_version":platform.python_version(),"spacy_version":spacy.__version__}; ')
    if gpu:
        code += ('import torch,cupy; assert torch.cuda.is_available(), "qualified CUDA GPU required"; '
                 'spacy.require_gpu(0); '
                 'r.update(gpu_name=torch.cuda.get_device_name(0), '
                 'gpu_compute_capability=list(torch.cuda.get_device_capability(0)), '
                 'torch_version=torch.__version__,cupy_version=cupy.__version__); ')
    code += 'print(json.dumps(r,sort_keys=True))'
    result = subprocess.run([str(Path(interpreter).resolve()), '-I', '-B', '-c', code],
                            check=False, capture_output=True, text=True, timeout=60)
    require(result.returncode == 0, 'explicit interpreter/GPU verification failed; no CPU fallback')
    runtime = json.loads(result.stdout)
    require(runtime['python_version'].startswith('3.11.') and runtime['spacy_version'] == '3.7.5',
            'qualified Python 3.11 / spaCy 3.7.5 required')
    return runtime


def verify_gpu(preparation, runtime):
    report = read(Path(preparation) / 'gpu-qualification.json')
    previous = read(Path(preparation) / 'gpu-runtime.json')
    require(report.get('state') == 'passed' and report.get('gpu_environment_qualified') is True
            and report.get('model_revision') == '51a40433059d8a2c25b98a48eca854f8789a491a',
            'passed desktop GPU qualification required')
    for key in ('gpu_name', 'gpu_compute_capability', 'torch_version', 'cupy_version', 'spacy_version'):
        require(runtime.get(key) == previous.get(key), 'GPU/runtime differs from recorded qualification')


def render_config(template, paths):
    require(set(paths) == TOKENS, 'relocation fields missing')
    result = template
    for key, value in paths.items():
        # Replacements occur inside quoted spaCy config strings.
        escaped = json.dumps(str(value), ensure_ascii=False)[1:-1]
        result = result.replace('@@' + key + '@@', escaped)
    require('@@' not in result and 'research-holdout' not in result, 'unresolved or forbidden config path')
    return result


def launch(checkout, preparation, interpreter, model_dir, *, start=False, seed=None, output=None, verify_device=False):
    checkout, preparation, model_dir = map(lambda p: Path(p).resolve(), (checkout, preparation, model_dir))
    manifest = verify_package(checkout, preparation, model_dir)
    runtime = probe(interpreter, gpu=start or verify_device)
    validate_runtime_configs(interpreter, preparation)
    if start or verify_device:
        verify_gpu(preparation, runtime)
    if not start:
        require(output is None and seed is None, 'seed/output require explicit --start-training')
        return {'state': 'verified_read_only', 'counts': manifest['counts'], 'runtime': runtime,
                'gpu_verified': verify_device, 'configuration_schema_verified': True, 'training_started': False}
    require(type(seed) is int and seed in (0, 1, 2) and output is not None, 'explicit seed and new output required')
    output = Path(output).resolve()
    artifacts = checkout / 'backend/training/flood_ner/artifacts'
    require(output.is_relative_to(artifacts) and not output.exists(), 'new artifact output required')
    inside(checkout, output.relative_to(checkout))
    lock = artifacts / 'successor-training-active.lock'
    # Unlike failed admission grants, a finished training run releases its active lock.
    with lock.open('x', encoding='utf-8') as stream:
        stream.write(str(output))
    try:
        output.mkdir()
        relocated = read(preparation / 'model-contract.json')
        relocated['model_dir'] = str(model_dir)
        write_new(output / 'runtime-model-manifest.json', relocated)
        config = render_config((preparation / f'train-seed-{seed}.cfg').read_text(encoding='utf-8'), {
            'TRAIN': preparation / 'train.spacy', 'DEV': preparation / 'dev.spacy',
            'TOKENIZER': preparation / 'tokenizer.bin', 'MODEL_MANIFEST': output / 'runtime-model-manifest.json',
            'MODEL_MANIFEST_SHA256': digest(output / 'runtime-model-manifest.json'),
            'CHECKPOINT': output / 'selected-checkpoint'})
        (output / 'train.cfg').write_text(config, encoding='utf-8', newline='\n')
        write_new(output / 'run-request.json', {'checkout': str(checkout), 'preparation': str(preparation),
            'interpreter': str(Path(interpreter).resolve()), 'model_dir': str(model_dir), 'seed': seed,
            'output': str(output), 'handoff_sha256': digest(preparation / 'handoff-manifest.json'),
            'config_sha256': digest(output / 'train.cfg'), 'explicit_training_action': True})
        with (output / 'stdout.log').open('xb') as stdout, (output / 'stderr.log').open('xb') as stderr:
            result = subprocess.run([str(Path(interpreter).resolve()), '-I', '-B', str(Path(__file__).resolve()),
                                     '--internal-training', str(output / 'run-request.json')],
                                    check=False, stdout=stdout, stderr=stderr, cwd=checkout)
        write_new(output / 'run-outcome.json', {'returncode': result.returncode, 'seed': seed})
        require(result.returncode == 0, 'training failed; logs and outputs preserved')
        return {'state': 'training_completed', 'seed': seed, 'output': str(output)}
    finally:
        lock.unlink()


def internal_training(path):
    # Reachable only through an explicit later training command; never used by preparation.
    request = read(path)
    root, output = Path(request['checkout']), Path(request['output'])
    require(request.get('explicit_training_action') is True and
            (root / 'backend/training/flood_ner/artifacts/successor-training-active.lock').read_text(encoding='utf-8')
            == str(output), 'training request is not the active explicit run')
    require(digest(Path(request['preparation']) / 'handoff-manifest.json') == request['handoff_sha256']
            and digest(output / 'train.cfg') == request['config_sha256'], 'stale training request')
    verify_package(root, request['preparation'], request['model_dir'])
    verify_gpu(request['preparation'], probe(sys.executable, gpu=True))
    import importlib.util
    registry_path = root / 'backend/training/flood_ner/experiment_registry.py'
    spec = importlib.util.spec_from_file_location('lanes_successor_registry', registry_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from spacy.cli.train import train
    train(output / 'train.cfg', output_path=output / 'spacy', use_gpu=0)


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--internal-config-validation':
        print(json.dumps(validate_config_schemas(Path(sys.argv[2])), sort_keys=True))
        return
    if len(sys.argv) == 3 and sys.argv[1] == '--internal-training':
        internal_training(Path(sys.argv[2]))
        return
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('checkout', 'preparation', 'python', 'model-dir'):
        parser.add_argument('--' + flag, required=True, type=Path)
    parser.add_argument('--verify-gpu', action='store_true')
    parser.add_argument('--start-training', action='store_true')
    parser.add_argument('--seed', type=int, choices=(0, 1, 2))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    print(json.dumps(launch(args.checkout, args.preparation, args.python, args.model_dir,
        start=args.start_training, seed=args.seed, output=args.output, verify_device=args.verify_gpu), sort_keys=True))


if __name__ == '__main__':
    main()
