"""Manual frozen-seed launcher. Default is read-only; --start-training opts in."""
import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[3]
PREPARATION = ROOT / 'backend/training/flood_ner/artifacts/experiment-preparation-20261016-v2'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')


def validate_inputs(root: Path = ROOT, preparation: Path = PREPARATION,
                    require_new_output: bool = True, seed: int = 0) -> dict[str, Any]:
    if type(seed) is not int or seed not in (0, 1, 2):
        raise ValueError('frozen seed must be 0, 1 or 2')
    # Only the repaired CLI interpreter imports the validation module (SciPy).
    sys.path.insert(0, str(root / 'backend'))
    from training.flood_ner import corpus_tokenizer_qualification as q
    from training.flood_ner.qualified_export import new_output, passed_package
    from training.flood_ner.experiment_preparation import validate_export
    from spacy.util import load_config

    recorded = q.read(root / 'docs/evaluations/flood-ner-experiment-preparation-20261016/verification.json')
    q.require(digest(preparation / 'manifest.json') == recorded['manifest_sha256'],
              'preparation identity changed')
    manifest = q.bound_manifest(preparation / 'manifest.json')
    q.require(manifest['schema_version'] == 'lanes-experiment-preparation-v1'
              and manifest['state'] == 'passed' and manifest['initialization_only'] is True
              and manifest['primary_seed'] == 0 and manifest['robustness_seeds'] == [1, 2],
              'passing frozen preparation required')
    for name, sha in manifest['implementation_sha256'].items():
        q.require(digest(Path(__file__).with_name(name)) == sha, 'prepared implementation changed')
    for name, sha in q.read(preparation / 'rules-baseline.json')['files'].items():
        q.require(digest(root / name) == sha, 'frozen rules code/assets changed')
    export = q.verified_reference(manifest['export'], root).parent
    exported = validate_export(export, root)
    report, paths = passed_package(q.verified_reference(manifest['qualification'], root).parent, root)
    q.require(manifest['input_bindings'] == exported['input_bindings'] == report['input_bindings'],
              'prepared/export/qualification bindings differ')
    q.inputs(paths['cohort'].parent, paths['context'].parent, paths['admission_package'], root)
    q.verify_model(paths['model_manifest'], root / 'backend/training/flood_ner/artifacts')
    q.verified_reference(manifest['evaluation_contract'], root)
    request = q.read(preparation / 'request.json')
    training_root = root / manifest['future_training_root']
    output = training_root / ('seed-' + str(seed))
    if require_new_output:
        new_output(root, output)
        for status_path in training_root.glob('seed-*/run-status.json'):
            q.require(q.read(status_path).get('state') != 'running',
                      'another seed is marked running; inspect it before starting a new run')
    config = preparation / ('train-seed-' + str(seed) + '.cfg')
    cfg = load_config(config)
    q.require(cfg['system']['seed'] == seed and 'test.spacy' not in config.read_text(encoding='utf-8')
              and Path(cfg['training']['before_to_disk']['output']).resolve() == output / 'selected-checkpoint',
              'seed/output or held-out policy differs')
    interpreter = root / 'backend/training/flood_ner/artifacts/gpu-qualification-20261015/research-env/Scripts/python.exe'
    q.require(digest(interpreter) == exported['research_interpreter_sha256'], 'research interpreter changed')
    return {'operation': 'train_seed_' + str(seed), 'seed': seed, 'config': str(config),
            'config_sha256': digest(config), 'output': str(output), 'python': str(interpreter),
            'preparation_manifest': str(preparation / 'manifest.json'),
            'preparation_sha256': digest(preparation / 'manifest.json'),
            'registry': str(Path(__file__).with_name('experiment_registry.py')),
            'registry_sha256': manifest['implementation_sha256']['experiment_registry.py'],
            'model_manifest': request['model_manifest'], 'test_predictions_performed': False}


def worker(request_path: Path) -> None:
    request = json.loads(request_path.read_text(encoding='utf-8'))
    seed = request.get('seed')
    if (sys.version_info[:2] != (3, 11) or type(seed) is not int or seed not in (0, 1, 2)
            or request.get('operation') != 'train_seed_' + str(seed)):
        raise ValueError('isolated qualified Python 3.11 frozen-seed request required')
    for key, binding in [('config', 'config_sha256'), ('registry', 'registry_sha256'),
                         ('preparation_manifest', 'preparation_sha256')]:
        if digest(Path(request[key])) != request[binding]:
            raise ValueError('training request binding changed')
    site = Path(sys.prefix) / 'Lib/site-packages'
    handles = [os.add_dll_directory(str(p)) for p in
               (site / 'torch/lib', site / 'nvidia/cuda_runtime/bin', site / 'nvidia/cuda_nvrtc/bin') if p.is_dir()]
    os.environ['CUDA_PATH'] = str(site / 'nvidia/cuda_runtime')
    import spacy
    import torch
    from spacy.cli.train import train
    if spacy.__version__ != '3.7.5' or not torch.cuda.is_available() or not spacy.require_gpu(0):
        raise ValueError('qualified GPU runtime unavailable; no CPU fallback')
    torch.set_num_threads(2)
    spec = importlib.util.spec_from_file_location('lanes_experiment_registry', request['registry'])
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    print('GPU:', torch.cuda.get_device_name(0), flush=True)
    print(('Primary' if seed == 0 else 'Robustness') + ' seed ' + str(seed)
          + '; train=280, dev=60. Test predictions are excluded.', flush=True)
    train(Path(request['config']), Path(request['output']), use_gpu=0)


def launch(plan: dict[str, Any], validator: Callable[[], Any] | None = None) -> int:
    configure_output()
    output = Path(plan['output'])
    output.mkdir(parents=True, exist_ok=False)
    request_path = output / 'launch-request.json'
    env_before = digest(ROOT / 'backend/.env')
    plan['launcher_sha256'] = digest(Path(__file__))
    request_path.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
    status: dict[str, Any] = {'state': 'running', 'seed': plan['seed'],
                              'started_at': datetime.now().astimezone().isoformat(),
                              'training_completed': False, 'test_predictions_performed': False}
    status_path = output / 'run-status.json'
    status_path.write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
    env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH'}}
    env.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
               OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', PYTHONUNBUFFERED='1',
               CUPY_CACHE_DIR=str(output / '.cupy-cache'))
    print('Output:', output, '\nLive log:', output / 'training.log', flush=True)
    proc = None
    code = 1
    try:
        with (output / 'training.log').open('w', encoding='utf-8', buffering=1) as log:
            proc = subprocess.Popen([plan['python'], '-B', '-I', '-u', '-X', 'utf8', str(Path(__file__)),
                                     '--worker', str(request_path)], cwd=output, env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding='utf-8', errors='replace')
            for line in proc.stdout:
                print(line, end='', flush=True)
                log.write(line)
            code = proc.wait()
        if code != 0:
            raise RuntimeError('training worker failed; preserve training.log')
        if validator is None:
            validate_inputs(require_new_output=False, seed=plan['seed'])
        else:
            validator()
        if digest(ROOT / 'backend/.env') != env_before:
            raise RuntimeError('.env changed during run; completion requires review')
        selected = output / 'selected-checkpoint'
        if not (selected / 'model/meta.json').is_file() or not (selected / 'selection.json').is_file():
            raise RuntimeError('authoritative selected checkpoint missing')
        status.update(state='completed', training_completed=True, exit_code=0,
                      selection=json.loads((selected / 'selection.json').read_text(encoding='utf-8')))
        print('Training completed. Preserve this folder for result review.', flush=True)
        return 0
    except KeyboardInterrupt:
        status.update(state='interrupted')
        print('\nInterrupted. Preserve partial outputs; do not rerun into this folder.', flush=True)
        return 130
    except Exception as exc:
        status.update(state='failed', error_type=type(exc).__name__)
        print(str(exc), file=sys.stderr, flush=True)
        return code if code else 1
    finally:
        if proc is not None and proc.poll() is None:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.terminate()
                proc.wait()
        status['ended_at'] = datetime.now().astimezone().isoformat()
        status_path.write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    # A redirected Windows stdout can default to cp1252. Training logs include
    # Unicode symbols, so forwarding a worker line must not terminate training.
    configure_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start-training', action='store_true')
    parser.add_argument('--seed', type=int, choices=(0, 1, 2), default=0)
    parser.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        worker(args.worker)
        return 0
    try:
        print('Verifying frozen preparation, corpus, tokenizer and model hashes...', flush=True)
        plan = validate_inputs() if args.seed == 0 else validate_inputs(seed=args.seed)
        if not args.start_training:
            print('CHECK PASSED. Training has not started. Run the PowerShell launcher with -StartTraining to begin.')
            return 0
        return launch(plan)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('Launcher refused: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
