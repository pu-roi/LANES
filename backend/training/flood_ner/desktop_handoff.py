"""Standard-library-only private NER archive verification/restoration.

Default operation is read-only. --restore adds missing evidence and prepares
versioned relocation manifests; it never installs, tokenizes or trains.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile

SCHEMA = 'lanes-ner-desktop-handoff-v1'
ARTIFACTS = 'backend/training/flood_ner/artifacts/'
MAX_BYTES = 2 * 1024 ** 3


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    sha = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''): sha.update(chunk)
    return sha.hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))


def find_root(start=None):
    start = Path(start or Path.cwd()).resolve()
    for candidate in [start, *start.parents]:
        if ((candidate / '.git').exists() and (candidate / 'DESIGN.md').is_file()
                and (candidate / 'backend/training/flood_ner').is_dir()): return candidate
    raise ValueError('Run inside the existing LANES checkout, or supply --repo; no checkout was created')


def safe_name(name):
    require(isinstance(name, str) and name and '\\' not in name and ':' not in name, 'unsafe archive path')
    path = PurePosixPath(name)
    require(not path.is_absolute() and path.as_posix() == name and all(p not in {'.', '..', ''} for p in name.split('/')), 'unsafe archive path')
    for part in path.parts:
        require(part == part.rstrip(' .') and not re.fullmatch(r'(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part, re.I), 'unsafe Windows archive path')
    return path


def allowed_payload(name):
    path = safe_name(name)
    require(name.startswith((ARTIFACTS, 'docs/evaluations/')), 'payload must contain research evidence only')
    require(not any(p.casefold() in {'research-env', 'venv', '.venv', '__pycache__', 'node_modules', 'model', 'wheels'}
                    or p.casefold().startswith('.env') for p in path.parts), 'environment, credentials or model weights excluded')
    require(path.name.casefold() not in {'credentials.json', 'secrets.json', 'token.json'}, 'credentials excluded')
    require(path.suffix.casefold() not in {'.zip', '.whl', '.exe', '.dll', '.pyd', '.pt', '.pth', '.pkl', '.safetensors', '.onnx', '.7z', '.gz', '.tar'}, 'archives, executables and model weights excluded')
    require(path.suffix.casefold() != '.bin' or 'tokenizer' in path.name.casefold(), 'only tokenizer binary artifacts may be transferred')
    return path


def target_path(root, name):
    relative = safe_name(name)
    target = root.joinpath(*relative.parts)
    require(target.resolve().is_relative_to(root.resolve()), 'restoration path escapes checkout')
    current = root
    for part in relative.parts:
        current = current / part
        require(not current.is_symlink(), 'symlink restoration destination refused')
    return target


def verify_archive(archive, expected_sha256, root):
    """Check every member, every byte and all conflicts before writing anything."""
    archive, root = Path(archive).resolve(), Path(root).resolve()
    require(isinstance(expected_sha256, str) and re.fullmatch('[a-f0-9]{64}', expected_sha256), 'explicit ZIP SHA-256 required')
    require(digest(archive) == expected_sha256, 'ZIP checksum mismatch')
    with zipfile.ZipFile(archive) as zipped:
        entries = zipped.infolist()
        names = [v.filename for v in entries]
        require(len(entries) <= 20000 and len(names) == len(set(n.casefold() for n in names)), 'duplicate/colliding archive entries')
        require(sum(v.file_size for v in entries) <= MAX_BYTES, 'archive exceeds bounded research payload size')
        for entry in entries:
            safe_name(entry.filename)
            require(not entry.is_dir() and not stat.S_ISLNK(entry.external_attr >> 16) and not entry.flag_bits & 1, 'directories, symlinks or encrypted members refused')
        require('handoff-manifest.json' in names and zipped.getinfo('handoff-manifest.json').file_size <= 8 * 1024 ** 2, 'bounded handoff manifest required')
        manifest = json.loads(zipped.read('handoff-manifest.json').decode('utf-8'))
        require(manifest.get('schema_version') == SCHEMA and isinstance(manifest.get('files'), dict) and manifest['files'], 'versioned file manifest required')
        require(set(names) == set(manifest['files']) | {'handoff-manifest.json'}, 'archive has missing or undeclared files')
        require(isinstance(manifest.get('inputs'), dict), 'declared research input paths required')
        for key, name in manifest['inputs'].items():
            allowed_payload(name)
            if key not in {'cohort', 'context'}: require(name in manifest['files'], 'declared input missing from payload')
        conflicts, identical, missing = [], [], []
        for name, value in manifest['files'].items():
            allowed_payload(name)
            require(isinstance(value, dict) and type(value.get('bytes')) is int and value['bytes'] >= 0
                    and isinstance(value.get('sha256'), str) and re.fullmatch('[a-f0-9]{64}', value['sha256']), 'file size/hash identity required')
            require(zipped.getinfo(name).file_size == value['bytes'], 'archive member size mismatch')
            sha = hashlib.sha256()
            with zipped.open(name) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''): sha.update(chunk)
            require(sha.hexdigest() == value['sha256'], 'archive member checksum mismatch: ' + name)
            target = target_path(root, name)
            if target.exists():
                (identical if target.is_file() and digest(target) == value['sha256'] else conflicts).append(name)
            else: missing.append(name)
        # The reference data is verified inside the archive even before restore.
        def records(key):
            with zipped.open(manifest['inputs'][key]) as stream:
                return [json.loads(line.decode('utf-8')) for line in stream if line.strip()]
        locations, contexts = records('location_records'), records('context_records')
        require(len(locations) == len({v['record_id'] for v in locations}) == 400 and len(contexts) == len({v['record_id'] for v in contexts}) == 40, '400 unique locations/40 unique contexts required')
        require(sum(v['passage_language'] == 'english' for v in locations) == sum(v['passage_language'] == 'taglish' for v in locations) == 200, '200/200 language totals required')
        require(sum(v['passage_language'] == 'english' for v in contexts) == sum(v['passage_language'] == 'taglish' for v in contexts) == 20, '20/20 contextual language totals required')
        expected = {'train': {'english': 140, 'taglish': 140}, 'dev': {'english': 30, 'taglish': 30}, 'test': {'english': 30, 'taglish': 30}}
        require({s: {lang: sum(v['split'] == s and v['passage_language'] == lang for v in locations) for lang in expected[s]} for s in expected} == expected, 'frozen split identities required')
        by_id = {v['record_id']: v for v in locations}
        for record in locations + contexts:
            text, source = record['text'], record['source']
            require(hashlib.sha256(text.encode('utf-8')).hexdigest() == record['text_sha256']
                and hashlib.sha256(source['text'].encode('utf-8')).hexdigest() == source['text_sha256']
                and source['text'][record['passage_start']:record['passage_end']] == text, 'source/passage hash or Unicode offsets mismatch')
            require(source['admission_status'] == 'training_admitted' and source['reuse_status'] == 'allowed', 'scoped admitted derivative required')
            for entity in record['entities']:
                require(text[entity['start']:entity['end']] == entity['text'], 'entity Unicode offsets mismatch')
        for pair in contexts:
            location = by_id.get(pair['record_id'])
            require(location is not None and location['split'] == pair['split'] == 'train'
                and all(location[k] == pair[k] for k in ('source', 'text', 'text_sha256', 'passage_start', 'passage_end', 'passage_language')), 'context binding mismatch')
        return manifest, {'verified_files': len(manifest['files']), 'payload_bytes': sum(v['bytes'] for v in manifest['files'].values()),
            'missing_files': missing, 'identical_files': identical, 'conflicts': conflicts,
            'locations': 400, 'contexts': 40, 'language_totals': {'english': 200, 'taglish': 200}, 'partitions': {'train': 280, 'dev': 60, 'test': 60}}


def restore_archive(archive, expected_sha256, root):
    manifest, result = verify_archive(archive, expected_sha256, root)
    require(not result['conflicts'], 'conflicting existing files; nothing restored: ' + ', '.join(result['conflicts'][:8]))
    restored = []
    with zipfile.ZipFile(archive) as zipped:
        for name in result['missing_files']:
            path = target_path(root, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as output, zipped.open(name) as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b''): output.write(chunk)
            require(digest(path) == manifest['files'][name]['sha256'], 'restored bytes changed: ' + name)
            restored.append(name)
    return result | {'restored_files': restored, 'existing_files_modified': False}


def verify_model_files(directory, manifest):
    directory = Path(directory).resolve()
    require(directory.is_dir() and manifest.get('model') == 'tl_calamancy_md' and manifest.get('version') == '0.1.0'
        and manifest.get('revision') == '51a40433059d8a2c25b98a48eca854f8789a491a', 'pinned model identity required')
    files = manifest.get('files')
    require(isinstance(files, list) and files and len({v['path'] for v in files}) == len(files), 'model file inventory required')
    for entry in files:
        path = target_path(directory, entry['path'])
        require(path.is_file() and path.stat().st_size == entry['bytes'] and digest(path) == entry['sha256'], 'existing model hash/size mismatch: ' + entry['path'])
    require({p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()} == {v['path'] for v in files}, 'model contains unmanifested files')
    return directory


def probe_python(executable, research=False):
    require(Path(executable).is_file(), 'existing Python interpreter missing: ' + str(executable))
    script = "import sys,json;from importlib.metadata import version,PackageNotFoundError\nr={}\nfor p in ['spacy','scipy','pydantic','httpx']:\n try:r[p]=version(p)\n except PackageNotFoundError:r[p]=None\nprint(json.dumps({'python':list(sys.version_info[:3]),'packages':r}))"
    response = subprocess.run([str(executable), '-B', '-I', '-c', script], capture_output=True, timeout=30)
    require(response.returncode == 0, 'existing interpreter metadata query failed: ' + response.stderr.decode('utf-8', errors='replace'))
    value = json.loads(response.stdout.decode('utf-8'))
    require(value['packages']['spacy'] == '3.7.5', 'existing interpreter must have spaCy 3.7.5; nothing installed')
    if research: require(value['python'][:2] == [3, 11], 'existing research interpreter must be Python 3.11')
    else: require(all(value['packages'][p] for p in ('scipy', 'pydantic', 'httpx')), 'existing CLI interpreter lacks offline tooling dependencies; nothing installed')
    return value


def discover(root, manifest, research_python=None, runner_python=None, model_dir=None):
    artifacts = root / ARTIFACTS
    candidates = [Path(research_python)] if research_python else sorted(artifacts.glob('gpu-qualification*/research-env/Scripts/python.exe'))
    require(len(candidates) == 1, 'locate the existing GPU research interpreter explicitly with --research-python')
    research = candidates[0].resolve()
    require(research.is_relative_to(artifacts.resolve()), 'research interpreter must remain under existing ignored artifacts')
    research_metadata = probe_python(research, research=True)
    runners = [Path(runner_python)] if runner_python else [root / 'backend/venv/Scripts/python.exe', root / 'backend/.venv/Scripts/python.exe', research]
    runner, runner_metadata, failures = None, None, []
    for candidate in runners:
        if not candidate.is_file(): continue
        try:
            runner_metadata = probe_python(candidate)
            runner = candidate.resolve()
            break
        except (ValueError, OSError, subprocess.TimeoutExpired) as exc: failures.append(str(exc))
    require(runner is not None, 'existing CLI interpreter not ready; no dependencies changed: ' + '; '.join(failures))
    expected_model = manifest['model_identity']
    preferred = research.parents[2] / 'model'
    model_candidates = [Path(model_dir)] if model_dir else [preferred]
    verified = []
    for candidate in model_candidates:
        if candidate.is_dir():
            verify_model_files(candidate, expected_model)
            verified.append(candidate.resolve())
    require(len(verified) == 1 and verified[0].is_relative_to(artifacts.resolve()), 'existing pinned model not found; supply its actual --model-dir')
    return {'research_python': str(research), 'runner_python': str(runner), 'model_dir': str(verified[0]),
        'research_metadata': research_metadata, 'runner_metadata': runner_metadata,
        'torch_or_spacy_imported': False, 'gpu_setup_repeated': False}


def prepare_relocation(root, manifest, inventory, output):
    output = Path(output).resolve()
    require(output.is_relative_to((root / ARTIFACTS).resolve()) and not output.exists(), 'new ignored relocation output required')
    model_original_path = target_path(root, manifest['inputs']['model_manifest'])
    tokenizer_original_path = target_path(root, manifest['inputs']['tokenizer_manifest'])
    model_original, tokenizer_original = read(model_original_path), read(tokenizer_original_path)
    verify_model_files(inventory['model_dir'], model_original)
    require(tokenizer_original['model_manifest_sha256'] == digest(model_original_path), 'original model/tokenizer binding mismatch')
    candidate_path = tokenizer_original_path.parent / tokenizer_original['tokenizer_file']
    require(digest(candidate_path) == tokenizer_original['sha256'] and tokenizer_original['vocabulary_files'] == [v for v in model_original['files'] if v['path'].startswith('vocab/')], 'candidate/vocabulary identity mismatch')
    relocated = deepcopy(model_original)
    relocated['model_dir'] = inventory['model_dir']
    relocated['relocation'] = {'original_manifest': manifest['inputs']['model_manifest'], 'original_sha256': digest(model_original_path), 'file_bytes_changed': False}
    output.mkdir(parents=True)
    (output / 'model-manifest.json').write_bytes(json_bytes(relocated))
    candidate = deepcopy(tokenizer_original)
    candidate['model_manifest_sha256'] = digest(output / 'model-manifest.json')
    candidate['relocation'] = {'original_manifest': manifest['inputs']['tokenizer_manifest'], 'original_sha256': digest(tokenizer_original_path), 'tokenizer_bytes_changed': False}
    candidate['corpus_qualification_state'] = 'pending'
    (output / 'candidate.tokenizer.bin').write_bytes(candidate_path.read_bytes())
    candidate['tokenizer_file'] = 'candidate.tokenizer.bin'
    (output / 'tokenizer-manifest.json').write_bytes(json_bytes(candidate))
    command = [inventory['runner_python'], '-B', '-m', 'training.flood_ner', 'qualify-corpus-tokenizer',
        '--python', inventory['research_python'], '--model-manifest', str(output / 'model-manifest.json'),
        '--tokenizer-manifest', str(output / 'tokenizer-manifest.json'),
        '--cohort', str(root / manifest['inputs']['cohort']), '--context', str(root / manifest['inputs']['context']),
        '--admission-manifest', str(root / manifest['inputs']['admission_manifest']), '--output', str(output / 'qualification')]
    ps_quote = lambda value: "'" + str(value).replace("'", "''") + "'"
    (output / 'QUALIFY.ps1').write_text('Set-Location -LiteralPath ' + ps_quote(root / 'backend') + '\n& ' + ' '.join(ps_quote(v) for v in command) + '\n', encoding='utf-8')
    result = {'schema_version': 'lanes-ner-desktop-relocation-v1', 'repo': str(root), 'inventory': inventory,
        'qualification_argv': command, 'qualification_cwd': str(root / 'backend'),
        'original_model_manifest_sha256': digest(model_original_path), 'original_tokenizer_manifest_sha256': digest(tokenizer_original_path),
        'model_files_unchanged': len(model_original['files']), 'tokenizer_sha256': digest(output / 'candidate.tokenizer.bin'),
        'qualification_run': False, 'corpus_qualified': False, 'training_run': False}
    result['files'] = {p.name: digest(p) for p in output.iterdir() if p.is_file()}
    (output / 'relocation.json').write_bytes(json_bytes(result))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--repo', type=Path)
    parser.add_argument('--research-python', type=Path)
    parser.add_argument('--runner-python', type=Path)
    parser.add_argument('--model-dir', type=Path)
    parser.add_argument('--restore', action='store_true', help='Add missing evidence and prepare relocation; default verifies only')
    parser.add_argument('--output', type=Path, help='Required new ignored relocation destination for --restore')
    args = parser.parse_args(argv)
    try:
        root = find_root(args.repo)
        manifest, result = verify_archive(args.archive, args.sha256, root)
        require(not result['conflicts'], 'existing evidence conflicts; no files written: ' + ', '.join(result['conflicts'][:8]))
        for item in manifest.get('checkout_dependencies', []):
            require(item['path'].startswith('backend/training/flood_ner/') and not item['path'].startswith(ARTIFACTS), 'checkout dependency must be tracked NER tooling/configuration')
            require(digest(target_path(root, item['path'])) == item['sha256'], 'checkout dependency differs; pull the recorded roi-branch first: ' + item['path'])
        inventory = discover(root, manifest, args.research_python, args.runner_python, args.model_dir)
        if args.restore:
            require(args.output is not None and args.output.resolve().is_relative_to((root / ARTIFACTS).resolve()) and not args.output.exists(), '--restore requires a new ignored --output directory')
            result = restore_archive(args.archive, args.sha256, root)
            result['relocation'] = prepare_relocation(root, manifest, inventory, args.output)
        print(json.dumps({'state': 'restored_and_prepared' if args.restore else 'verified_only', 'repo': str(root),
            'files_verified': result['verified_files'], 'files_to_restore': len(result['missing_files']),
            'identical_files': len(result['identical_files']), 'inventory': inventory,
            'output': str(args.output) if args.restore else None, 'qualification_run': False, 'training_run': False}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, subprocess.TimeoutExpired) as exc:
        print('desktop handoff failed: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__': raise SystemExit(main())
