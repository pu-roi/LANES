"""Freeze baseline/config identities and verify initialization without training."""
from pathlib import Path
import json
import os
import subprocess

from . import corpus_tokenizer_qualification as q
from .qualified_export import new_output, passed_package, SCHEMA as EXPORT_SCHEMA
from .rules_baseline import specification, predict_mentions
from .sources import json_bytes


def validate_export(folder: Path, root: Path) -> dict:
    manifest = q.bound_manifest(folder / 'manifest.json')
    q.require(manifest.get('schema_version') == EXPORT_SCHEMA and manifest.get('state') == 'passed'
              and manifest.get('annotation_profile') == 'location-only-v1'
              and manifest.get('counts') == {'train': 280, 'dev': 60, 'test': 60}
              and manifest.get('records') == 400 and manifest.get('source_articles') == 138
              and manifest.get('location_spans') == 1465 and manifest.get('negative_passages') == 48
              and manifest.get('contextual_pairs_exported_as_samples') == 0
              and manifest.get('source_use_scope') == q.SCOPE
              and manifest.get('training_performed') is False, 'verified admitted export required')
    for ref in list(manifest['input_bindings'].values()) + [manifest['qualification'], manifest['evaluation_contract']]:
        q.verified_reference(ref, root)
    for name, sha in manifest['implementation_sha256'].items():
        q.require(name in {'qualified_export.py', 'qualified_export_worker.py'}
                  and q.digest(Path(__file__).with_name(name)) == sha, 'export implementation changed')
    q.require(q.digest(folder / 'tokenizer.bin') == manifest['tokenizer_sha256'], 'export tokenizer changed')
    return manifest


def rules_smoke() -> dict:
    # Importing the existing application's enum/model dependencies can create a
    # lazy SQLAlchemy engine. Block connections while testing this offline adapter.
    from unittest.mock import patch
    with patch('sqlalchemy.engine.Engine.connect', side_effect=RuntimeError('database access prohibited')):
        samples = ['Baha sa Main Road sa Pasig City.', 'Flooding at Barangay Bagong Ilog.',
                   'Sa Purok Singko ay may baha.', 'Biñan\nMain Road has flooding.']
        results = [predict_mentions(text) for text in samples]
    q.require(any(r['spans'] for r in results), 'constructed rules adapter produced no spans')
    return {'state': 'passed', 'constructed_passages': len(samples),
            'valid_spans': sum(len(r['spans']) for r in results),
            'diagnostics': sum(len(r['diagnostics']) for r in results),
            'database_connections_allowed': False, 'corpus_predictions_performed': False}


def prepare_experiment(python: Path, export: Path, output: Path, root: Path) -> dict:
    root = root.resolve()
    output = new_output(root, output)
    export = export.resolve()
    artifacts = root / 'backend/training/flood_ner/artifacts'
    q.require(export.is_relative_to(artifacts), 'existing private export required')
    manifest = validate_export(export, root)
    interpreter = python.resolve()
    q.require(interpreter.is_file() and interpreter.is_relative_to(artifacts)
              and q.digest(interpreter) == manifest['research_interpreter_sha256'],
              'same qualified research interpreter required')
    qualification = q.verified_reference(manifest['qualification'], root).parent
    report, paths = passed_package(qualification, root)
    q.require(manifest['input_bindings'] == report['input_bindings'], 'qualification/export identities differ')
    q.inputs(paths['cohort'].parent, paths['context'].parent, paths['admission_package'], root)
    model, model_dir = q.verify_model(paths['model_manifest'], artifacts)
    contract = q.read(q.verified_reference(manifest['evaluation_contract'], root))
    q.require(contract['model_selection']['primary_seed'] == 0
              and contract['model_selection']['robustness_seeds'] == [1, 2]
              and contract['model_selection']['tie_break'] == 'earlier checkpoint step',
              'unsupported frozen experiment protocol')
    rules = specification(root)
    # Explicitly chosen once before any corpus baseline results or training.
    future_root = artifacts / 'academic-training-20261016-v1'
    q.require(not future_root.exists(), 'planned training root already exists; preserve it and choose a new version')
    output.mkdir(parents=True)
    status = {'schema_version': 'lanes-experiment-preparation-v1', 'state': 'failed',
              'training_performed': False, 'model_predictions_performed': False,
              'optimizer_updates': 0, 'test_corpus_read_by_initializer': False}
    try:
        smoke = rules_smoke()
        (output / 'rules-baseline.json').write_bytes(json_bytes(rules))
        (output / 'rules-smoke.json').write_bytes(json_bytes(smoke))
        request = {'operation': 'initialize_only', 'model_dir': str(model_dir),
                   'model_manifest': str(paths['model_manifest']),
                   'model_manifest_sha256': report['input_bindings']['model_manifest']['sha256'],
                   'export': str(export), 'tokenizer_sha256': manifest['tokenizer_sha256'],
                   'output': str(output), 'future_training_root': str(future_root)}
        request_path = output / 'request.json'
        request_path.write_bytes(json_bytes(request))
        env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH'}}
        env.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                   OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
        worker = Path(__file__).with_name('experiment_worker.py')
        proc = subprocess.run([str(interpreter), '-B', '-I', '-X', 'utf8', str(worker), str(request_path)],
                              cwd=output, env=env, capture_output=True, timeout=600)
        (output / 'worker.stdout.log').write_bytes(proc.stdout)
        (output / 'worker.stderr.log').write_bytes(proc.stderr)
        q.require(proc.returncode == 0, 'initialization worker failed; see retained worker.stderr.log')
        result = json.loads(proc.stdout.decode('utf-8'))
        q.require(result.get('state') == 'passed' and result.get('operation') == 'initialize_only'
                  and result.get('optimizer_updates') == 0 and result.get('training_performed') is False
                  and result.get('model_predictions_performed') is False and result.get('test_corpus_read') is False
                  and [v['seed'] for v in result.get('seeds', [])] == [0, 1, 2], 'invalid initialization readiness result')
        for seed in result['seeds']:
            q.require(seed['configuration_loaded'] is True and seed['optimizer_updates'] == 0
                      and seed['pipeline'] == ['ner'] and set(seed['labels']) == q.PLACE_LABELS
                      and seed['gpu_parameter_arrays'] > 0
                      and seed['tokenizer_sha256'] == manifest['tokenizer_sha256']
                      and q.digest(output / ('train-seed-' + str(seed['seed']) + '.cfg')) == seed['config_sha256'],
                      'seed configuration readiness differs')
        (output / 'initialization.json').write_bytes(json_bytes(result))
        q.require(not future_root.exists(), 'unexpected training/checkpoint execution')
        validate_export(export, root)
        passed_package(qualification, root)
        q.verify_model(paths['model_manifest'], artifacts)
        for name, sha in rules['files'].items():
            q.require(q.digest(root / name) == sha, 'rules baseline code/asset changed')
        status.update(state='passed', primary_seed=0, robustness_seeds=[1, 2],
                      export={'path': (export / 'manifest.json').relative_to(root).as_posix(),
                              'sha256': q.digest(export / 'manifest.json')},
                      evaluation_contract=manifest['evaluation_contract'], input_bindings=manifest['input_bindings'],
                      qualification=manifest['qualification'], baseline_mapping='rules-baseline.json',
                      pretrained_baseline={'scope': 'coarse LOC only, original native tokenizer and pinned NER weights',
                                           'six_class_claim': False, 'reference_driven_relabeling': False},
                      model_selection=contract['model_selection'], training_policy=result['training_policy'],
                      rule_mapping_scope='existing mention rules; not full flood claim/context/placement pipeline',
                      unavailable_rule_output_labels=['LOCAL_AREA'],
                      authoritative_checkpoint='future seed directory/selected-checkpoint/model; built-in model-best is diagnostic only because spaCy overwrites equal scores',
                      future_training_root=future_root.relative_to(root).as_posix(),
                      source_use_scope=q.SCOPE, initialization_only=True,
                      implementation_sha256={p.name: q.digest(p) for p in
                          [Path(__file__), worker, Path(__file__).with_name('experiment_registry.py'),
                           Path(__file__).with_name('rules_baseline.py')]})
        status['files'] = {p.name: q.digest(p) for p in sorted(output.iterdir()) if p.is_file()}
        (output / 'manifest.json').write_bytes(json_bytes(status))
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as exc:
        if isinstance(exc, subprocess.TimeoutExpired):
            (output / 'worker.stdout.log').write_bytes(exc.stdout or b'')
            (output / 'worker.stderr.log').write_bytes(exc.stderr or b'')
        # Do not print settings-validation error details, which can contain env values.
        status.update(state='failed', error_type=type(exc).__name__)
        (output / 'failure.json').write_bytes(json_bytes(status))
        raise ValueError('experiment preparation failed; private diagnostics retained in ' + str(output)) from None
    return status
