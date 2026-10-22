"""Authenticate a regularization transfer before optional exclusive extraction.

Standard library only. No archived code, model or dataset is executed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def relative_path(name):
    require(isinstance(name, str) and name, 'empty path')
    path = PurePosixPath(name)
    require(not path.is_absolute() and path.as_posix() == name and
            '..' not in path.parts and ':' not in name and '\\' not in name,
            'unsafe path')
    return path


def authenticate(checkout, archive, manifest_path, manifest_sha256):
    """Read and hash bytes only; verify all inputs before creating output."""
    checkout = Path(checkout).resolve()
    manifest_bytes = Path(manifest_path).read_bytes()
    require(sha(manifest_bytes) == manifest_sha256, 'transfer manifest checksum mismatch')
    manifest = json.loads(manifest_bytes)
    require(manifest['schema'] == 'lanes-regularization-transfer-v1' and
            manifest['training_authorized'] is False and manifest['holdout_included'] is False,
            'unsafe transfer scope')
    raw = Path(archive).read_bytes()
    require(len(raw) == manifest['archive']['bytes'] and
            sha(raw) == manifest['archive']['sha256'], 'ZIP checksum/size mismatch')
    expected = manifest['files']
    require(len(expected) == 20 and all(relative_path(n) for n in expected), 'expected twenty files')
    data = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
        infos = zipped.infolist()
        require(len(infos) == 20 and len({i.filename for i in infos}) == 20,
                'unexpected/duplicate ZIP members')
        require({i.filename for i in infos} == set(expected), 'unexpected/missing ZIP members')
        for info in infos:
            relative_path(info.filename)
            require(not info.is_dir() and stat.S_ISREG(info.external_attr >> 16) and
                    0 <= info.file_size <= 5_000_000, 'unsafe member type/size')
            payload = zipped.read(info)
            binding = expected[info.filename]
            require(len(payload) == binding['bytes'] and sha(payload) == binding['sha256'],
                    'member binding mismatch')
            data[info.filename] = payload
    experiment = json.loads(data['experiment-manifest.json'])
    require(sha(data['experiment-manifest.json']) == manifest['experiment_manifest_sha256'] and
            set(experiment['files']) == set(data) - {'experiment-manifest.json'} and
            experiment['training_authorized'] is False, 'experiment manifest mismatch')
    for name, expected_sha in experiment['files'].items():
        require(sha(data[name]) == expected_sha, 'experiment member mismatch')
    require(manifest['implementation'] == experiment['implementation'] and
            manifest['tests'] == experiment['tests'], 'source bindings differ')
    for binding in [*manifest['implementation'], manifest['tests']]:
        source = checkout.joinpath(*relative_path(binding['path']).parts).resolve()
        require(source.is_relative_to(checkout) and source.is_file() and
                sha(source.read_bytes()) == binding['sha256'],
                'pull matching source bytes before extraction')
    package_files = {n.removeprefix('package/') for n in data if n.startswith('package/')}
    package = json.loads(data['package/handoff-manifest.json'])
    require(len(package_files) == 12 and set(package['files']) == package_files - {'handoff-manifest.json'}
            and package['training_authorized'] is False and package['training_started'] is False,
            'trainer membership/capability mismatch')
    for name, expected_sha in package['files'].items():
        require(sha(data['package/' + name]) == expected_sha, 'trainer member mismatch')
    require(package['experiment_protocol_sha256'] == sha(data['experiment-protocol.json']),
            'trainer protocol mismatch')
    return data


def verify_or_extract(checkout, archive, manifest, manifest_sha256, destination=None):
    data = authenticate(checkout, archive, manifest, manifest_sha256)
    if destination is not None:
        root = Path(checkout).resolve()
        allowed = root / 'backend/training/flood_ner/artifacts'
        output = Path(destination).absolute()
        require(allowed.is_dir() and allowed.resolve().is_relative_to(root) and
                output.parent.resolve() == allowed.resolve() and
                output.name == 'regularization-desktop-20261018-v21' and
                not output.exists() and not output.is_symlink(),
                'absent checkout artifact destination required')
        output.mkdir()  # Exclusive claim: concurrent/repeated extraction fails.
        for name, payload in data.items():
            target = output.joinpath(*relative_path(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(payload)
        require(all((output / n).read_bytes() == p for n, p in data.items()), 'extraction readback differs')
    return {'state': 'extracted_verified' if destination is not None else 'verified_read_only',
            'files': len(data), 'trainer_files': 12, 'training_started': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('verify', 'extract'), nargs='?', default='verify')
    for name in ('checkout', 'archive', 'manifest'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--destination', type=Path)
    args = parser.parse_args()
    require((args.operation == 'extract') == (args.destination is not None),
            'only explicit extract accepts/requires a new destination')
    print(json.dumps(verify_or_extract(args.checkout, args.archive, args.manifest,
        args.manifest_sha256, args.destination), sort_keys=True))


if __name__ == '__main__':
    main()
