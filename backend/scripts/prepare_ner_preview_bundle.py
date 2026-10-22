"""Copy a verified retained checkpoint into a new private inference-only bundle.

Explicit operator CLI; never invoked on API requests. Original files are read-only.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.news_ner.bundle import MODEL_FILES, VOCAB_FILES, digest, verify_bundle
from training.flood_ner.runtime_preflight import authenticate


def prepare(manifest: Path, manifest_sha: str, resource: Path, resource_sha: str,
            resource_dir: Path, destination: Path) -> str:
    if destination.exists():
        raise ValueError('new absent private destination required')
    verified = authenticate(manifest, manifest_sha, resource, resource_sha, resource_dir)
    destination.mkdir(parents=True, exist_ok=False)
    files = {}
    for prefix, source, names in [('model', verified['model'], MODEL_FILES),
                                   ('base/vocab', resource_dir / 'vocab', VOCAB_FILES)]:
        for name in sorted(names):
            target = destination / prefix / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, target)
            files[target.relative_to(destination).as_posix()] = {'bytes': target.stat().st_size, 'sha256': digest(target)}
    value = {'schema': 'lanes-ner-inference-bundle-v1', 'model_manifest_sha256': manifest_sha,
             'resource_manifest_sha256': resource_sha, 'files': files}
    (destination / 'manifest.json').write_text(json.dumps(value, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    sha = digest(destination / 'manifest.json')
    verify_bundle(destination, sha)
    return sha


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('manifest', 'resource', 'resource-dir', 'destination'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--manifest-sha', required=True)
    p.add_argument('--resource-sha', required=True)
    a = p.parse_args()
    print(json.dumps({'bundle_sha256': prepare(a.manifest, a.manifest_sha, a.resource, a.resource_sha, a.resource_dir, a.destination)}))
