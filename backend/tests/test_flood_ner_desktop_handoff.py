"""Standard-library handoff safety and exact relocation tests; no real GPU run."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import stat
from types import SimpleNamespace
import zipfile

import pytest

from training.flood_ner import desktop_handoff as h


def sha(data): return hashlib.sha256(data).hexdigest()


def record(n):
    text = 'Biñan\u2028Purok 31-A.'
    return {'record_id': f'r{n}', 'text': text, 'text_sha256': sha(text.encode()),
        'source': {'text': text, 'text_sha256': sha(text.encode()), 'admission_status': 'training_admitted', 'reuse_status': 'allowed'},
        'passage_start': 0, 'passage_end': len(text), 'passage_language': 'english' if n % 2 == 0 else 'taglish',
        'split': 'train' if n < 280 else 'dev' if n < 340 else 'test',
        'entities': [{'start': 0, 'end': 5, 'text': 'Biñan', 'label': 'CITY'}]}


def fixture_archive(tmp_path, alter=None, extra=None):
    locations = [record(n) for n in range(400)]
    contexts = deepcopy(locations[:40])
    if alter: alter(locations, contexts)
    names = [h.ARTIFACTS + 'cohort/records.jsonl', h.ARTIFACTS + 'context/records.jsonl']
    data = {names[0]: b''.join(h.json_bytes(r).replace(b'\n', b'') + b'\n' for r in locations),
            names[1]: b''.join(h.json_bytes(r).replace(b'\n', b'') + b'\n' for r in contexts)}
    manifest = {'schema_version': h.SCHEMA, 'files': {k: {'sha256': sha(v), 'bytes': len(v)} for k, v in data.items()},
        'inputs': {'location_records': names[0], 'context_records': names[1]}}
    archive = tmp_path / 'fixture.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr('handoff-manifest.json', h.json_bytes(manifest))
        for name, value in data.items(): zipped.writestr(name, value)
        if extra: extra(zipped)
    root = tmp_path / 'checkout'
    root.mkdir(); (root / '.git').mkdir(); (root / 'DESIGN.md').write_text('fixture')
    (root / 'backend/training/flood_ner').mkdir(parents=True)
    return archive, root, manifest


def test_verified_archive_restores_exact_unicode_and_skips_identical_files(tmp_path):
    archive, root, manifest = fixture_archive(tmp_path)
    _, check = h.verify_archive(archive, h.digest(archive), root)
    assert check['locations'] == 400 and check['contexts'] == 40 and len(check['missing_files']) == 2
    assert not (root / h.ARTIFACTS).exists()
    first = h.restore_archive(archive, h.digest(archive), root)
    assert len(first['restored_files']) == 2
    second = h.restore_archive(archive, h.digest(archive), root)
    assert not second['restored_files'] and len(second['identical_files']) == 2
    assert all(h.digest(root / name) == entry['sha256'] for name, entry in manifest['files'].items())


def test_conflict_is_found_before_any_missing_file_is_written(tmp_path):
    archive, root, manifest = fixture_archive(tmp_path)
    name = list(manifest['files'])[1]
    existing = root / name; existing.parent.mkdir(parents=True); existing.write_bytes(b'keep user file')
    with pytest.raises(ValueError, match='conflicting'): h.restore_archive(archive, h.digest(archive), root)
    assert existing.read_bytes() == b'keep user file'
    assert not (root / list(manifest['files'])[0]).exists()


@pytest.mark.parametrize('name', ['../escape', '/absolute', 'C:/secret', 'backend\\escape',
    'backend//escape', './escape', 'backend/../escape', 'backend/NUL.txt', 'backend/name.', 'backend/file:stream'])
def test_unsafe_archive_names_are_rejected(name):
    with pytest.raises(ValueError): h.safe_name(name)


@pytest.mark.parametrize('name', ['backend/.env', h.ARTIFACTS + 'research-env/installed.txt',
    h.ARTIFACTS + 'model/ner/model', h.ARTIFACTS + 'weights.safetensors', h.ARTIFACTS + 'wheel.whl',
    h.ARTIFACTS + 'old-backup.zip', h.ARTIFACTS + 'credentials.json', 'frontend/source.ts'])
def test_payload_excludes_environments_credentials_weights_and_nested_archives(name):
    with pytest.raises(ValueError): h.allowed_payload(name)


def test_zip_checksum_and_undeclared_members_are_rejected(tmp_path):
    archive, root, _ = fixture_archive(tmp_path)
    with pytest.raises(ValueError, match='ZIP checksum'): h.verify_archive(archive, '0' * 64, root)
    with zipfile.ZipFile(archive, 'a') as zipped: zipped.writestr(h.ARTIFACTS + 'extra.json', '{}')
    with pytest.raises(ValueError, match='undeclared'): h.verify_archive(archive, h.digest(archive), root)


@pytest.mark.parametrize('kind', ['duplicate', 'case_collision', 'symlink', 'traversal'])
def test_archive_rejects_duplicate_case_collisions_symlinks_and_traversal(tmp_path, kind):
    def extra(zipped):
        if kind == 'duplicate': zipped.writestr('handoff-manifest.json', '{}')
        elif kind == 'case_collision': zipped.writestr('HANDOFF-MANIFEST.JSON', '{}')
        elif kind == 'traversal': zipped.writestr('../escape', 'bad')
        else:
            info = zipfile.ZipInfo(h.ARTIFACTS + 'link'); info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            zipped.writestr(info, '../../escape')
    archive, root, _ = fixture_archive(tmp_path, extra=extra)
    with pytest.raises(ValueError): h.verify_archive(archive, h.digest(archive), root)


@pytest.mark.parametrize('mutation', ['count', 'duplicate', 'language', 'split', 'offset', 'hash', 'context', 'entity'])
def test_malformed_frozen_data_is_rejected_before_restoration(tmp_path, mutation):
    def alter(rows, contexts):
        if mutation == 'count': rows.pop()
        elif mutation == 'duplicate': rows[1] = deepcopy(rows[0])
        elif mutation == 'language': rows[0]['passage_language'] = 'taglish'
        elif mutation == 'split': rows[0]['split'] = 'test'
        elif mutation == 'offset': rows[0]['passage_start'] = 1
        elif mutation == 'hash': rows[0]['text_sha256'] = '0' * 64
        elif mutation == 'context': contexts[0]['source']['reuse_status'] = 'unknown'
        else: rows[0]['entities'][0]['end'] = 4
    archive, root, _ = fixture_archive(tmp_path, alter=alter)
    with pytest.raises(ValueError): h.restore_archive(archive, h.digest(archive), root)
    assert not (root / h.ARTIFACTS).exists()


def test_member_bytes_are_checked_even_with_a_matching_whole_archive_checksum(tmp_path):
    archive, root, manifest = fixture_archive(tmp_path)
    with zipfile.ZipFile(archive) as zipped: contents = {v.filename: zipped.read(v) for v in zipped.infolist()}
    contents[next(iter(manifest['files']))] += b'changed'
    with zipfile.ZipFile(archive, 'w') as zipped:
        for name, data in contents.items(): zipped.writestr(name, data)
    with pytest.raises(ValueError): h.verify_archive(archive, h.digest(archive), root)


def model_fixture(root):
    directory = root / 'backend/training/flood_ner/artifacts/gpu-qualification-fixture/model'
    directory.mkdir(parents=True)
    files = []
    for name, data in [('meta.json', b'{}'), ('vocab/strings.json', b'[]')]:
        path = directory / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        files.append({'path': name, 'sha256': sha(data), 'bytes': len(data)})
    return directory, {'model': 'tl_calamancy_md', 'version': '0.1.0',
        'revision': '51a40433059d8a2c25b98a48eca854f8789a491a', 'model_dir': 'D:/old/model', 'files': files}


def test_relocation_preserves_original_manifests_and_model_bytes(tmp_path):
    directory, original = model_fixture(tmp_path)
    old = tmp_path / h.ARTIFACTS / 'original'; old.mkdir()
    model = old / 'model.json'; model.write_bytes(h.json_bytes(original))
    candidate = old / 'candidate.tokenizer.bin'; candidate.write_bytes(b'constructed tokenizer bytes')
    tokenizer = old / 'tokenizer.json'
    value = {'model_manifest_sha256': h.digest(model), 'sha256': h.digest(candidate), 'tokenizer_file': candidate.name,
        'model_revision': original['revision'], 'qualification_state': 'passed', 'vocabulary_files': [original['files'][1]]}
    tokenizer.write_bytes(h.json_bytes(value))
    before = {p: h.digest(p) for p in [model, candidate, tokenizer]}
    manifest = {'inputs': {'model_manifest': model.relative_to(tmp_path).as_posix(), 'tokenizer_manifest': tokenizer.relative_to(tmp_path).as_posix(),
        'cohort': h.ARTIFACTS + 'cohort', 'context': h.ARTIFACTS + 'context', 'admission_manifest': h.ARTIFACTS + 'admission.json'}}
    inventory = {'model_dir': str(directory), 'runner_python': 'E:/existing/python.exe', 'research_python': 'E:/existing/research/python.exe'}
    output = tmp_path / h.ARTIFACTS / 'relocation'
    result = h.prepare_relocation(tmp_path, manifest, inventory, output)
    assert all(h.digest(p) == value for p, value in before.items())
    assert h.read(output / 'model-manifest.json')['files'] == original['files']
    assert h.read(output / 'tokenizer-manifest.json')['model_manifest_sha256'] == h.digest(output / 'model-manifest.json')
    assert h.digest(output / 'candidate.tokenizer.bin') == h.digest(candidate)
    assert h.read(output / 'tokenizer-manifest.json')['corpus_qualification_state'] == 'pending'
    assert result['qualification_run'] is False
    assert '--admission-manifest' in result['qualification_argv']
    with pytest.raises(ValueError): h.prepare_relocation(tmp_path, manifest, inventory, output)


def test_model_verification_rejects_changed_and_extra_files(tmp_path):
    directory, manifest = model_fixture(tmp_path)
    h.verify_model_files(directory, manifest)
    (directory / 'extra').write_bytes(b'x')
    with pytest.raises(ValueError): h.verify_model_files(directory, manifest)


def test_python_probe_reads_metadata_only_and_reports_missing_dependencies(tmp_path, monkeypatch):
    executable = tmp_path / 'python.exe'; executable.write_bytes(b'fixture')
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        assert '-I' in args and 'import spacy' not in args[-1] and 'import torch' not in args[-1]
        return SimpleNamespace(returncode=0, stderr=b'', stdout=h.json_bytes({'python': [3, 11, 17],
            'packages': {'spacy': '3.7.5', 'scipy': None, 'pydantic': '2.14.1', 'httpx': '0.27.0'}}))
    monkeypatch.setattr(h.subprocess, 'run', run)
    h.probe_python(executable, research=True)
    with pytest.raises(ValueError): h.probe_python(executable, research=False)
    assert len(calls) == 2


def test_missing_desktop_prerequisite_does_not_install_or_create_directories(tmp_path):
    archive, root, manifest = fixture_archive(tmp_path)
    with pytest.raises(ValueError, match='existing GPU research interpreter'): h.discover(root, manifest)
    assert not (root / h.ARTIFACTS).exists()


def test_root_detection_uses_existing_checkout_and_refuses_missing_checkout(tmp_path):
    archive, root, _ = fixture_archive(tmp_path)
    assert h.find_root(root / 'backend/training/flood_ner') == root
    with pytest.raises(ValueError): h.find_root(tmp_path)


def test_default_cli_verifies_only_without_restoring_or_running_qualification(tmp_path, monkeypatch, capsys):
    archive, root, _ = fixture_archive(tmp_path)
    monkeypatch.setattr(h, 'discover', lambda *args: {'fixture': 'metadata only'})
    assert h.main(['--repo', str(root), '--archive', str(archive), '--sha256', h.digest(archive)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['state'] == 'verified_only' and result['qualification_run'] is False and result['training_run'] is False
    assert not (root / h.ARTIFACTS).exists()
