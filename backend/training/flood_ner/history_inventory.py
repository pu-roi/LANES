"""Standalone, read-only history inventory. Python 3.10+; standard library only.

Hashes files without exporting their contents. Source metadata extraction is
opt-in for explicitly named source-capture JSON/JSONL files. No archives are
opened, no helpers executed, and no claim of complete external history is made.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import urlsplit, urlunsplit


SKIP_DIRS = frozenset({'.git', '.venv', 'venv', 'env', 'node_modules', '__pycache__',
    '.next', '.cache', '.pytest_cache', '.mypy_cache', 'site-packages',
    'research-env', 'research_env', 'models', 'model', 'model-best', 'model-last',
    'selected-checkpoint', 'vocab', 'optimizer', 'checkpoints'})
WEIGHT_SUFFIXES = frozenset({'.bin', '.pt', '.pth', '.ckpt', '.safetensors', '.onnx',
    '.spacy', '.npy', '.npz', '.pkl', '.pickle', '.joblib', '.whl'})
SECRET_SUFFIXES = frozenset({'.pem', '.key', '.pfx', '.p12', '.kdbx'})
FRESH_MARKERS = ('heldout-', 'heldout_', 'fresh-test', 'fresh_test', 'fresh-heldout',
    'fresh_heldout', 'additional-heldout', 'additional_heldout', 'isolated-test', 'isolated_test')
MAX_METADATA_BYTES = 64 * 1024 * 1024
HEX = re.compile(r'[0-9a-f]{64}\Z')
IDENTIFIER = re.compile(r'[A-Za-z0-9_.:/-]{1,200}\Z')


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def excluded_reason(relative: Path) -> str | None:
    parts = [p.casefold() for p in relative.parts]
    if any(any(marker in part for marker in FRESH_MARKERS) for part in parts):
        return 'isolated_test'
    if any(p in SKIP_DIRS or p.startswith(('research-env-', 'research_env-', '.venv-')) for p in parts):
        return 'environment_dependency_or_model'
    name = parts[-1] if parts else ''
    if (name.startswith('.env') or name in ('.netrc', '.npmrc', '.pypirc') or any(token in name for token in
            ('credential', 'secret', 'private-key', 'private_key', 'id_rsa', 'id_ed25519', 'token-store'))
            or relative.suffix.casefold() in SECRET_SUFFIXES):
        return 'secret'
    if relative.suffix.casefold() in WEIGHT_SUFFIXES:
        return 'model_weight_or_binary_dependency'
    return None


def is_link(path: Path) -> bool:
    info = path.lstat()
    return path.is_symlink() or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def check_roots(checkout: Path, extras: list[Path], output: Path,
                exclusions: list[Path]) -> tuple[list[Path], Path, list[Path]]:
    roots = []
    for raw in [checkout, *extras]:
        if is_link(raw) or not raw.is_dir():
            raise ValueError('every input root must be an existing ordinary directory')
        root = raw.resolve(strict=True)
        if excluded_reason(Path(root.name)):
            raise ValueError('an input root itself falls under an exclusion')
        if any(root.is_relative_to(old) or old.is_relative_to(root) for old in roots):
            raise ValueError('input roots must be distinct and non-overlapping')
        roots.append(root)
    if is_link(checkout) or not (roots[0] / 'DESIGN.md').is_file():
        raise ValueError('checkout must be the explicit LANES checkout containing DESIGN.md')
    # Reject links anywhere on the destination chain, even when they resolve inside a root.
    for part in [output.absolute(), *output.absolute().parents]:
        if part.exists() or part.is_symlink():
            if is_link(part):
                raise ValueError('output cannot traverse links or reparse points')
    destination = output.resolve()
    if destination.exists() or any(root.is_relative_to(destination) for root in roots):
        raise ValueError('output must be a new directory and cannot contain an input root')
    excluded = []
    for raw in exclusions:
        path = raw.resolve(strict=True)
        if not any(path.is_relative_to(root) for root in roots) or path in roots:
            raise ValueError('explicit exclusions must be existing paths inside an input root')
        excluded.append(path)
    return roots, destination, excluded


def safe_source_metadata(record: object) -> dict | None:
    """Project scalar provenance only; never recurse into annotations or outputs."""
    if not isinstance(record, dict):
        return None
    source_id = record.get('source_id')
    url = record.get('url') or record.get('canonical_url')
    if not isinstance(source_id, str) or not IDENTIFIER.fullmatch(source_id) or not isinstance(url, str):
        return None
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
            return None
        # Query strings/fragments can contain access tokens; never export them.
        clean_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))
    except ValueError:
        return None
    value = {'source_id': source_id, 'url_without_query_fragment': clean_url}
    for key in ('text_sha256', 'raw_sha256', 'source_sha256'):
        item = record.get(key)
        if isinstance(item, str) and HEX.fullmatch(item):
            value[key] = item
    text = record.get('text')
    if isinstance(text, str):
        actual = hashlib.sha256(text.encode('utf-8')).hexdigest()
        value['computed_source_text_sha256'] = actual
        value['recorded_text_hash_matches'] = record.get('text_sha256') == actual
    for key in ('captured_at', 'published_at', 'publication_date'):
        item = record.get(key)
        if isinstance(item, str) and len(item) <= 40:
            try:
                datetime.fromisoformat(item.replace('Z', '+00:00'))
            except ValueError:
                continue
            value[key] = item
    for key in ('article_key', 'capture_version', 'article_group', 'event_group', 'syndication_group'):
        item = record.get(key)
        if isinstance(item, str) and IDENTIFIER.fullmatch(item):
            value[key] = item
    return value


def metadata_records(path: Path) -> list[dict]:
    if path.suffix.casefold() not in ('.json', '.jsonl') or path.stat().st_size > MAX_METADATA_BYTES:
        raise ValueError('metadata input must be JSON/JSONL no larger than 64 MiB')
    raw = path.read_text(encoding='utf-8-sig')
    if path.suffix.casefold() == '.jsonl':
        records = [json.loads(line) for line in raw.split('\n') if line.strip()]
    else:
        data = json.loads(raw)
        records = data if isinstance(data, list) else [data]
    return [item for record in records if (item := safe_source_metadata(record)) is not None]


def inventory(checkout: Path, extras: list[Path], output: Path,
              exclusions: list[Path] | None = None,
              metadata_files: list[Path] | None = None) -> dict:
    roots, destination, excluded = check_roots(checkout, extras, output, exclusions or [])
    wanted = [p.resolve(strict=True) for p in (metadata_files or [])]
    if len(set(wanted)) != len(wanted):
        raise ValueError('duplicate metadata inputs')
    for path in wanted:
        matches = [root for root in roots if path.is_relative_to(root)]
        if (not matches or excluded_reason(path.relative_to(matches[0]))
                or any(path.is_relative_to(p) for p in excluded)
                or any(is_link(p) for p in [path, *path.parents] if p.exists())
                or path.is_relative_to(destination)):
            raise ValueError('metadata inputs must be eligible ordinary files inside named roots')
    # All argument validation precedes output creation or source reads.
    destination.mkdir(parents=True, exist_ok=False)
    files, metadata, errors = [], [], []
    skipped: Counter = Counter()
    for index, root in enumerate(roots):
        def walk_error(exc: OSError) -> None:
            errors.append({'root_index': index, 'operation': 'directory_scan',
                           'error_type': type(exc).__name__})
        for base, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
            directory = Path(base)
            dirs.sort()
            names.sort()
            for name in list(dirs):
                path = directory / name
                try:
                    reason = ('output' if path.resolve() == destination else
                        'explicit_exclusion' if any(path.resolve().is_relative_to(p) for p in excluded) else
                        'link_or_reparse' if is_link(path) else excluded_reason(path.relative_to(root)))
                except OSError as exc:
                    reason = 'unreadable_directory'
                    errors.append({'root_index': index, 'operation': 'directory_stat', 'error_type': type(exc).__name__})
                if reason:
                    skipped[reason] += 1
                    dirs.remove(name)
            for name in names:
                path = directory / name
                relative = path.relative_to(root)
                try:
                    reason = ('explicit_exclusion' if any(path.resolve().is_relative_to(p) for p in excluded) else
                        'link_or_reparse' if is_link(path) else excluded_reason(relative))
                    if reason:
                        skipped[reason] += 1
                        continue
                    before = path.stat()
                    if not stat.S_ISREG(before.st_mode):
                        skipped['non_regular'] += 1
                        continue
                    sha = digest(path)
                    entry = {'root_index': index, 'path': relative.as_posix(), 'bytes': before.st_size,
                             'mtime_ns': before.st_mtime_ns, 'sha256': sha}
                    source_rows = metadata_records(path) if path.resolve() in wanted else []
                    after = path.stat()
                    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
                        raise ValueError('file changed during inventory')
                    files.append(entry)
                    metadata.extend({'root_index': index, 'file': relative.as_posix(),
                                     'file_sha256': sha, 'source': row} for row in source_rows)
                except (OSError, ValueError, UnicodeError) as exc:
                    errors.append({'root_index': index, 'path': relative.as_posix(),
                                   'operation': 'hash_or_metadata', 'error_type': type(exc).__name__})
    scanned = {(row['root_index'], row['path']) for row in files}
    for path in wanted:
        if not any((i, path.relative_to(root).as_posix()) in scanned for i, root in enumerate(roots) if path.is_relative_to(root)):
            errors.append({'operation': 'requested_metadata_not_inventoried', 'error_type': 'IncompleteInput'})
    result = {'schema_version': 'lanes-history-inventory-v1',
        'captured_at': datetime.now(timezone.utc).isoformat(),
        'collector_sha256': digest(Path(__file__)),
        'roots': [{'root_index': i, 'path': str(p), 'role': 'checkout' if i == 0 else 'explicit_extra'} for i, p in enumerate(roots)],
        'explicit_exclusions': [str(p) for p in excluded],
        'files': files, 'source_metadata': metadata, 'errors': errors,
        'excluded_entry_counts': dict(skipped), 'complete_for_named_readable_scope': not errors,
        'external_history_complete': False, 'fresh_test_sealed': False,
        'article_annotation_model_contents_exported': False, 'archives_opened': False,
        'scripts_executed': False, 'inputs_modified': False,
        'limitations': ['Only explicitly named roots were scanned; unspecified folders and computers remain unknown.',
            'Known fresh-test paths, secrets, environments, dependencies, links and model weights are excluded.',
            'Use explicit exclusions for private test folders with unrecognized names.',
            'Files are hashed without interpreting archives or annotation/model contents.',
            'Source metadata is opt-in and contains only projected provenance; no article text or labels.',
            'A successful inventory does not prove complete collection history or authorize sealing.']}
    data = (json.dumps(result, ensure_ascii=True, indent=2) + '\n').encode('utf-8')
    with (destination / 'inventory.json').open('xb') as stream:
        stream.write(data)
    manifest = {'schema_version': 'lanes-history-inventory-manifest-v1',
                'files': {'inventory.json': hashlib.sha256(data).hexdigest()},
                'collector_sha256': result['collector_sha256'], 'external_history_complete': False}
    with (destination / 'manifest.json').open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, indent=2)
        stream.write('\n')
    return {'files_hashed': len(files), 'source_metadata_records': len(metadata),
            'errors': len(errors), 'complete_for_named_readable_scope': not errors,
            'excluded_entry_counts': dict(skipped), 'external_history_complete': False,
            'fresh_test_sealed': False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', type=Path, required=True)
    parser.add_argument('--extra-root', type=Path, action='append', default=[])
    parser.add_argument('--exclude', type=Path, action='append', default=[])
    parser.add_argument('--source-metadata', type=Path, action='append', default=[])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        summary = inventory(args.checkout, args.extra_root, args.output, args.exclude, args.source_metadata)
    except (OSError, ValueError) as exc:
        # Do not echo input contents or exception strings, which could include secrets.
        print(json.dumps({'inventory_failed': True, 'error_type': type(exc).__name__}), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary['complete_for_named_readable_scope'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
