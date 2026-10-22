"""Constructed transfers only; no real text, annotations or weights."""
import importlib.util
import json
from pathlib import Path
import stat
import zipfile

import pytest

SPEC = importlib.util.spec_from_file_location('delivery', Path(__file__).parents[1] /
    'training/flood_ner/regularization_delivery.py')
delivery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(delivery)


def encoded(value):
    return json.dumps(value, sort_keys=True).encode()


@pytest.fixture
def transfer(tmp_path):
    root = tmp_path / 'checkout'; root.mkdir()
    (root / 'backend/training/flood_ner/artifacts').mkdir(parents=True)
    source = root / 'source.py'; source.write_bytes(b'# constructed source\n')
    binding = {'path': 'source.py', 'sha256': delivery.sha(source.read_bytes())}
    data = {f'package/payload-{n}.bin': b'constructed' for n in range(11)}
    data.update({f'control-configs/seed-{n}.cfg': b'constructed' for n in range(3)})
    data.update({n: b'{}' for n in ('experiment-protocol.json', 'baseline-metrics.json',
                                  'development-slices.json', 'cpu-qualification.json')})
    data['package/handoff-manifest.json'] = encoded({'files': {
        n.removeprefix('package/'): delivery.sha(v) for n, v in data.items() if n.startswith('package/')},
        'training_authorized': False, 'training_started': False,
        'experiment_protocol_sha256': delivery.sha(data['experiment-protocol.json'])})
    data['experiment-manifest.json'] = encoded({'files': {n: delivery.sha(v) for n, v in data.items()},
        'implementation': [binding], 'tests': binding, 'training_authorized': False})
    archive = tmp_path / 'transfer.zip'; manifest = tmp_path / 'manifest.json'
    def rebuild(entries=None, symlink=False, unsafe_scope=False):
        with zipfile.ZipFile(archive, 'w') as z:
            for index, (name, payload) in enumerate(entries if entries is not None else data.items()):
                info = zipfile.ZipInfo(name); info.create_system = 3
                info.external_attr = ((stat.S_IFLNK if symlink and index == 0 else stat.S_IFREG) | 0o600) << 16
                z.writestr(info, payload)
        document = {'schema': 'lanes-regularization-transfer-v1',
            'training_authorized': unsafe_scope, 'holdout_included': False,
            'archive': {'bytes': archive.stat().st_size, 'sha256': delivery.sha(archive.read_bytes())},
            'files': {n: {'bytes': len(v), 'sha256': delivery.sha(v)} for n, v in data.items()},
            'experiment_manifest_sha256': delivery.sha(data['experiment-manifest.json']),
            'implementation': [binding], 'tests': binding}
        manifest.write_bytes(encoded(document))
        return delivery.sha(manifest.read_bytes())
    expected = rebuild()
    destination = root / 'backend/training/flood_ner/artifacts/regularization-desktop-20261018-v21'
    return root, archive, manifest, destination, data, rebuild, expected


def run(t, expected=None, extract=True):
    root, archive, manifest, destination, _, _, original = t
    return delivery.verify_or_extract(root, archive, manifest, expected or original,
                                     destination if extract else None)


def test_read_only_then_extraction_and_bytes(transfer):
    assert run(transfer, extract=False)['state'] == 'verified_read_only'
    assert not transfer[3].exists()
    assert run(transfer)['state'] == 'extracted_verified'
    assert all((transfer[3] / n).read_bytes() == v for n, v in transfer[4].items())


@pytest.mark.parametrize('case', ['checksum', 'manifest', 'missing', 'duplicate', 'unexpected',
                                 'unsafe', 'symlink', 'source', 'scope', 'member'])
def test_preflight_rejects_without_destination(transfer, case):
    root, archive, manifest, destination, data, rebuild, expected = transfer
    entries = list(data.items())
    if case == 'checksum': archive.write_bytes(archive.read_bytes() + b'changed')
    if case == 'manifest': expected = '0' * 64
    if case == 'missing': expected = rebuild(entries[:-1])
    if case == 'duplicate': expected = rebuild(entries[:-1] + [entries[0]])
    if case == 'unexpected': expected = rebuild(entries[:-1] + [('other.bin', b'bad')])
    if case == 'unsafe': expected = rebuild(entries[:-1] + [('../escape', b'bad')])
    if case == 'symlink': expected = rebuild(symlink=True)
    if case == 'source': (root / 'source.py').write_bytes(b'changed')
    if case == 'scope': expected = rebuild(unsafe_scope=True)
    if case == 'member': expected = rebuild([(entries[0][0], b'changed'), *entries[1:]])
    with pytest.raises(ValueError): run(transfer, expected)
    assert not destination.exists()


def test_existing_destination_is_preserved(transfer):
    transfer[3].mkdir(); marker = transfer[3] / 'preserve'; marker.write_bytes(b'original')
    with pytest.raises(ValueError, match='absent'): run(transfer)
    assert marker.read_bytes() == b'original'


@pytest.mark.parametrize('name', ['../bad', '/absolute', 'a\\b', 'a:b', 'a//b', ''])
def test_path_rejection(name):
    with pytest.raises(ValueError): delivery.relative_path(name)
