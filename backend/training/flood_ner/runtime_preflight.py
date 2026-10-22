"""Read-only retained-model preflight. Never qualifies inference or connects an app.

No corpus inputs, model initialization, predictions, installation or training. The
optional vocabulary probe reads only authenticated vector assets in a subprocess.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

LABELS = {'BARANGAY', 'CITY', 'LANDMARK', 'LOCAL_AREA', 'PROVINCE', 'ROAD'}
MODEL_FILES = {'config.cfg', 'meta.json', 'ner/cfg', 'ner/model', 'ner/moves',
               'tokenizer', 'vocab/key2row', 'vocab/lookups.bin',
               'vocab/strings.json', 'vocab/vectors', 'vocab/vectors.cfg'}
PACKAGES = ('spacy', 'thinc', 'numpy', 'blis', 'floret')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def checked_path(root: Path, relative: str) -> Path:
    require(isinstance(relative, str) and relative and '\\' not in relative,
            'portable relative path required')
    rel = Path(relative)
    require(not rel.is_absolute() and ':' not in relative
            and all(part not in ('', '.', '..') for part in relative.split('/')),
            'unsafe artifact path')
    path = root / rel
    require(not any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                    for p in (path, *path.parents)), 'linked paths forbidden')
    require(path.resolve().is_relative_to(root.resolve()), 'artifact escapes root')
    return path


def bound_json(path: Path, expected_sha256: str) -> dict:
    require(digest(path) == expected_sha256, 'stale manifest hash')
    value = json.loads(path.read_text(encoding='utf-8'))
    require(isinstance(value, dict), 'object manifest required')
    return value


def verify_files(root: Path, files: dict[str, str]) -> None:
    require(root.is_dir(), 'missing model directory')
    for relative, sha in files.items():
        path = checked_path(root, relative)
        require(path.is_file() and digest(path) == sha, 'model file binding differs')
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    require(actual == set(files), 'unexpected model directory membership')


def authenticate(manifest: Path, sha: str, resource_manifest: Path,
                 resource_sha: str, resource_dir: Path) -> dict:
    scoped = bound_json(manifest, sha)
    require(scoped.get('schema') == 'lanes-v19-scoped-models-v1'
            and scoped.get('retained') == 'control' and scoped.get('primary') == 'control-seed-0',
            'retained control seed 0 manifest required')
    runs = [r for r in scoped['runs'] if r['name'] == 'control-seed-0']
    require(len(runs) == 1 and runs[0]['model'] == 'models/control-seed-0/model',
            'unique primary checkpoint required')
    files = runs[0]['files']
    require(set(files) == MODEL_FILES, 'eleven selected-checkpoint files required')
    model = checked_path(manifest.parent, runs[0]['model'])
    verify_files(model, files)
    meta = json.loads((model / 'meta.json').read_text(encoding='utf-8'))
    require(meta.get('pipeline') == ['ner'] and set(meta['labels']['ner']) == LABELS
            and meta.get('vectors', {}).get('mode') == 'floret', 'unexpected model architecture')
    resource = bound_json(resource_manifest, resource_sha)
    require(resource.get('model') == 'tl_calamancy_md' and resource.get('version') == '0.1.0'
            and resource.get('revision') == '51a40433059d8a2c25b98a48eca854f8789a491a'
            and resource.get('download_complete') is True and len(resource['files']) == 23,
            'pinned complete resource manifest required')
    rf = {f['path']: f['sha256'] for f in resource['files']}
    require(len(rf) == 23, 'duplicate resource entries')
    verify_files(resource_dir, rf)
    for entry in resource['files']:
        require((resource_dir / entry['path']).stat().st_size == entry['bytes'], 'resource size differs')
    return {'model': model, 'model_files': files, 'resource_files': rf,
            'tokenizer_sha256': files['tokenizer'], 'labels': sorted(LABELS)}


def run_json(args: list[str], timeout: int = 30) -> dict:
    """Bounded child; never a shell, never a retry. Raw evidence stays private."""
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'ok': False, 'error_type': type(exc).__name__}
    if result.returncode:
        return {'ok': False, 'returncode': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr}
    try:
        value = json.loads(result.stdout)
        require(isinstance(value, dict), 'child object required')
    except (ValueError, TypeError):
        return {'ok': False, 'error_type': 'invalid_child_json',
                'stdout': result.stdout, 'stderr': result.stderr}
    return {'ok': True, 'value': value}


def environment_probe(interpreter: Path) -> dict:
    code = '''import importlib.metadata as m, json, platform, sys
packages = {}
for name in ('spacy', 'thinc', 'numpy', 'blis', 'floret'):
    try: packages[name] = m.version(name)
    except m.PackageNotFoundError: packages[name] = None
print(json.dumps({'system': platform.system(), 'machine': platform.machine(),
                  'python': list(sys.version_info[:3]), 'packages': packages}))
'''
    return run_json([str(interpreter), '-I', '-B', '-c', code])


def vocabulary_probe(interpreter: Path, resource_dir: Path) -> dict:
    # No application imports, neural pipeline, text, references or model weights.
    # Block outbound connections before importing spaCy. This is a research
    # guard, not an OS sandbox; future Linux qualification needs --network none.
    code = '''import json, socket, sys
def blocked(*args, **kwargs): raise RuntimeError('network forbidden')
socket.create_connection = blocked
socket.socket.connect = blocked
socket.socket.connect_ex = blocked
try:
    from spacy.vocab import Vocab
    vocab = Vocab().from_disk(sys.argv[1])
    vectors = vocab.vectors.get_batch(['Aster', 'Piña', 'baha'])
    assert vectors.shape == (3, 200)
    print(json.dumps({'loaded': True, 'lookup_verified': True, 'mode': vocab.vectors.mode, 'width': vocab.vectors.shape[1]}))
except Exception as exc:
    print(json.dumps({'loaded': False, 'error_type': type(exc).__name__, 'detail': str(exc)}))
'''
    return run_json([str(interpreter), '-I', '-B', '-c', code, str(resource_dir / 'vocab')])


def docker_probe(docker: Path) -> dict:
    # Query an existing engine only. Do not start, build, pull or install here.
    return run_json([str(docker), 'info', '--format',
                     '{"os":{{json .OSType}},"architecture":{{json .Architecture}},"version":{{json .ServerVersion}}}'], 15)


def assess(environment: dict, docker: dict, vocabulary: dict | None) -> dict:
    blockers = []
    if not environment.get('ok'):
        blockers.append('backend_interpreter_probe_failed')
    else:
        e = environment['value']
        if e.get('python', [])[:2] != [3, 12]: blockers.append('backend_python_3_12_not_verified')
        if e.get('packages', {}).get('spacy') != '3.7.5': blockers.append('spacy_3_7_5_not_verified')
    if not docker.get('ok') or docker.get('value', {}).get('os') != 'linux':
        blockers.append('linux_docker_engine_unavailable')
    if vocabulary is not None and (not vocabulary.get('ok') or not vocabulary['value'].get('lookup_verified')):
        blockers.append('backend_vocabulary_load_failed')
    # Discovery of prerequisites is not a measured Linux qualification.
    return {'schema': 'lanes-v19-runtime-preflight-v1',
            'status': 'preflight_blocked' if blockers else 'preflight_passed_qualification_pending',
            'blockers': blockers,
            'linux_inference_qualified': False, 'latency_measured': False, 'memory_measured': False,
            'neural_inference_performed': False, 'training_started': False,
            'application_connected': False, 'validation_accessed': False, 'holdout_accessed': False,
            'remaining': ['private inference-only tokenizer path binding',
                          'Linux CPU load and serialized-tokenizer parity',
                          'training-only prediction parity', 'cold/warm latency and peak RSS',
                          'bounded timeouts, malformed/oversized inputs and worker restart checks',
                          'deployment resource envelope and acceptance thresholds']}


def save_new(destination: Path, report: dict, evidence: dict) -> None:
    require(not destination.exists(), 'new output directory required')
    require(not any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                    for p in (destination, *destination.parents)), 'linked output forbidden')
    destination.mkdir(parents=True, exist_ok=False)
    for name, value in [('status.json', report), ('private-evidence.json', evidence)]:
        with (destination / name).open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(value, sort_keys=True, indent=2) + '\n')


def private_destination(destination: Path, artifacts: Path) -> None:
    require(destination.resolve().is_relative_to(artifacts.resolve())
            and destination.resolve() != artifacts.resolve(), 'output must be a private artifact subdirectory')
    require(not destination.exists(), 'new output directory required')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('model-manifest', 'model-manifest-sha256', 'resource-manifest',
                'resource-manifest-sha256', 'resource-dir', 'interpreter', 'docker'):
        parser.add_argument('--' + arg, required=True)
    parser.add_argument('--probe-vectors', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output:
        private_destination(args.output, Path(__file__).resolve().parent / 'artifacts')
    authenticated = authenticate(Path(args.model_manifest), args.model_manifest_sha256,
        Path(args.resource_manifest), args.resource_manifest_sha256, Path(args.resource_dir))
    environment = environment_probe(Path(args.interpreter))
    docker = docker_probe(Path(args.docker))
    vocabulary = vocabulary_probe(Path(args.interpreter), Path(args.resource_dir)) if args.probe_vectors else None
    # Recheck immutable assets after subprocesses, including optional vector read.
    verify_files(authenticated['model'], authenticated['model_files'])
    verify_files(Path(args.resource_dir), authenticated['resource_files'])
    report = assess(environment, docker, vocabulary)
    report.update(checkpoint_files_verified=len(authenticated['model_files']),
                  resource_files_verified=len(authenticated['resource_files']))
    evidence: dict[str, Any] = {'arguments': vars(args) | {'output': str(args.output) if args.output else None},
        'environment': environment, 'docker': docker, 'vocabulary': vocabulary,
        'model_files': authenticated['model_files'], 'resource_files': authenticated['resource_files'],
        'implementation_sha256': digest(Path(__file__))}
    if args.output:
        save_new(args.output, report, evidence)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
