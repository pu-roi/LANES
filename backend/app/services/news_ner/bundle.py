"""Strict, inference-only artifact verification; no model initialization."""
import hashlib
import json
from pathlib import Path

from .contract import require

MODEL_FILES = {'config.cfg', 'meta.json', 'ner/cfg', 'ner/model', 'ner/moves',
               'tokenizer', 'vocab/key2row', 'vocab/lookups.bin',
               'vocab/strings.json', 'vocab/vectors', 'vocab/vectors.cfg'}
VOCAB_FILES = {'key2row', 'lookups.bin', 'strings.json', 'vectors', 'vectors.cfg'}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_file(root: Path, relative: str) -> Path:
    require(isinstance(relative, str) and bool(relative) and '\\' not in relative and ':' not in relative
            and all(p not in {'', '.', '..'} for p in relative.split('/')), 'unsafe bundle member')
    path = root / relative
    require(not Path(relative).is_absolute() and path.resolve().is_relative_to(root.resolve()), 'bundle escape')
    require(not any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)() for p in (path, *path.parents)), 'linked artifacts forbidden')
    return path


def verify_bundle(root: Path, expected_sha256: str) -> dict:
    manifest = safe_file(root, 'manifest.json')
    require(digest(manifest) == expected_sha256, 'bundle manifest mismatch')
    value = json.loads(manifest.read_text(encoding='utf-8'))
    require(set(value) == {'schema', 'model_manifest_sha256', 'resource_manifest_sha256', 'files'}
            and value['schema'] == 'lanes-ner-inference-bundle-v1', 'unexpected bundle schema')
    expected = {'model/' + n for n in MODEL_FILES} | {'base/vocab/' + n for n in VOCAB_FILES}
    require(set(value['files']) == expected, 'inference-only membership required')
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    require(actual == expected | {'manifest.json'}, 'unexpected bundle files')
    for name, entry in value['files'].items():
        path = safe_file(root, name)
        require(set(entry) == {'sha256', 'bytes'} and path.stat().st_size == entry['bytes']
                and digest(path) == entry['sha256'], 'bundle asset mismatch')
    return value
