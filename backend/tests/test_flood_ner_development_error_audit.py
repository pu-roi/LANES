"""Constructed development-only audit checks; no private articles or model weights."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import zipfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner import development_error_audit as audit


def test_strict_spans_repeated_mentions_and_unicode():
    text = 'Peña Road, Peña Road.'
    result = audit.diagnose([(0, 9, 'ROAD'), (11, 20, 'ROAD')], [(0, 9, 'ROAD')], text)
    assert (result['TP'], result['FP'], result['FN']) == (1, 0, 1)
    assert result['missed_without_overlap'] == [(11, 20, 'ROAD')]


@pytest.mark.parametrize('prediction,kind', [
    ([(0, 9, 'CITY')], 'wrong_type'), ([(5, 9, 'ROAD')], 'wrong_boundary'),
    ([(5, 9, 'CITY')], 'wrong_boundary_and_type')])
def test_overlap_diagnostics_never_become_true_positives(prediction, kind):
    row = audit.diagnose([(0, 9, 'ROAD')], prediction, 'Peña Road')
    assert (row['TP'], row['FP'], row['FN']) == (0, 1, 1)
    assert row['overlap_links'][0]['kind'] == kind


def test_one_to_many_overlap_links_do_not_double_count_strict_errors():
    row = audit.diagnose([(0, 4, 'CITY'), (5, 9, 'ROAD')], [(0, 9, 'ROAD')], 'Test Road')
    assert (row['TP'], row['FP'], row['FN']) == (0, 1, 2)
    assert len(row['overlap_links']) == 2


@pytest.mark.parametrize('spans', [None, [(0, 99, 'ROAD')], [(0, 3, 'DEPTH')],
                                 [(0, 3, 'ROAD'), (0, 3, 'ROAD')],
                                 [(0, 3, 'ROAD'), (1, 4, 'CITY')], [(True, 3, 'ROAD')]])
def test_invalid_reference_or_prediction_spans_rejected(spans):
    with pytest.raises(ValueError):
        audit.checked_spans(spans, 'Peña Road')


def test_exact_metrics_negative_errors_and_supported_macro():
    reference = {'positive': [(0, 4, 'CITY')], 'negative': []}
    prediction = {'positive': [(0, 4, 'CITY')], 'negative': [(0, 3, 'ROAD')]}
    result = audit.score_partition(reference, prediction, {'positive': 'english', 'negative': 'taglish'})
    assert result['overall']['TP'] == 1 and result['overall']['FP'] == 1
    assert result['overall']['f1'] == pytest.approx(2 / 3)
    assert result['labels']['ROAD']['FP'] == 1 and result['labels']['ROAD']['f1'] is None
    assert result['macro'] == {'supported_labels': 1, 'f1': 1.0}
    assert result['language_macro']['taglish'] == {'supported_labels': 0, 'f1': None}
    assert result['negative_passages']['taglish']['rate'] == 1.0


@pytest.mark.parametrize('change', ['missing_prediction', 'language'])
def test_metric_record_and_language_join_rejected(change):
    prediction = {} if change == 'missing_prediction' else {'a': []}
    with pytest.raises(ValueError):
        audit.score_partition({'a': []}, prediction, {'a': 'unknown' if change == 'language' else 'english'})


def constructed_join():
    records, rows = [], []
    for split, languages in audit.LANGUAGES.items():
        for language, count in languages.items():
            for i in range(count):
                rid = f'constructed-{split}-{language}-{i}'
                records.append({'record_id': rid, 'entities': [], 'complete': True, 'review_status': 'accepted',
                                'annotation_profile': 'location-only-v1', 'split': split, 'passage_language': language,
                                'text': 'fixture', 'text_sha256': hashlib.sha256(b'fixture').hexdigest(),
                                'passage_start': 0, 'passage_end': 7,
                                'source': {'text': 'fixture', 'text_sha256': hashlib.sha256(b'fixture').hexdigest()}})
                rows.append({'record_id': rid, 'partition': split, 'language': language,
                             'passage_sha256': records[-1]['text_sha256'], 'source_sha256': records[-1]['text_sha256'],
                             'passage_start': 0, 'passage_end': 7, 'is_negative': True, 'group_keys': [rid]})
    return records, rows


def test_all_405_constructed_records_accounted():
    records, rows = constructed_join()
    joined, metadata = audit.validate_join(records, rows)
    assert len(joined) == len(metadata) == 405


@pytest.mark.parametrize('failure', ['missing', 'duplicate', 'null_reference', 'missing_reference', 'incomplete',
                                    'language', 'text', 'negative', 'holdout', 'fragmented_group'])
def test_join_rejects_unsafe_inputs(failure):
    records, rows = constructed_join()
    if failure == 'missing': records.pop()
    if failure == 'duplicate': records[-1] = records[0]
    if failure == 'null_reference': records[0]['entities'] = None
    if failure == 'missing_reference': records[0].pop('entities')
    if failure == 'incomplete': records[0]['complete'] = False
    if failure == 'language': rows[0]['language'] = 'taglish'
    if failure == 'text': records[0]['text'] = 'modified'
    if failure == 'negative': rows[0]['is_negative'] = False
    if failure == 'holdout': rows[0]['partition'] = 'research_holdout'
    if failure == 'fragmented_group': rows[-1]['group_keys'] = rows[0]['group_keys']
    with pytest.raises(ValueError): audit.validate_join(records, rows)


@pytest.mark.parametrize('path', ['../escape', '/absolute', 'folder\\escape', 'C:/absolute'])
def test_path_escape_rejected(tmp_path, path):
    with pytest.raises(ValueError): audit.safe_path(tmp_path, path)


def test_binding_rejects_stale_hash(tmp_path):
    (tmp_path / 'fixture').write_bytes(b'original')
    binding = {'path': 'fixture', 'sha256': audit.digest(tmp_path / 'fixture')}
    assert audit.bound(tmp_path, binding).name == 'fixture'
    (tmp_path / 'fixture').write_bytes(b'modified')
    with pytest.raises(ValueError): audit.bound(tmp_path, binding)


def constructed_archive(tmp_path, extra=False):
    members = {}
    for seed in (0, 1, 2):
        for name in ['config.cfg', 'meta.json', 'tokenizer', 'ner/model', 'ner/cfg', 'ner/moves',
                     'vocab/strings.json', 'vocab/vectors', 'vocab/key2row', 'vocab/vectors.cfg', 'vocab/lookups.bin']:
            members[audit.checkpoint_prefix(seed) + name] = b'constructed'
    if extra: members['research-holdout.spacy'] = b'forbidden'
    manifest = {'files': {name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                          for name, data in members.items()}}
    path = tmp_path / 'fixture.zip'
    with zipfile.ZipFile(path, 'w') as z:
        for name, data in members.items(): z.writestr(name, data)
        z.writestr('checkpoint-backup-manifest.json', json.dumps(manifest))
    return path, manifest


def test_archive_authentication_and_exclusive_selected_extraction(tmp_path):
    path, manifest = constructed_archive(tmp_path)
    audit.verify_archive(path, manifest)
    output = tmp_path / 'new'; output.mkdir()
    audit.extract_models(path, output)
    assert len([p for p in output.rglob('*') if p.is_file()]) == 33
    with pytest.raises(FileExistsError): audit.extract_models(path, output)


def test_holdout_archive_rejected_even_with_matching_manifest(tmp_path):
    path, manifest = constructed_archive(tmp_path, extra=True)
    with pytest.raises(ValueError, match='forbidden'): audit.verify_archive(path, manifest)


def test_existing_destination_and_concurrent_audit_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, 'verify_request', lambda *a: None)
    request = tmp_path / 'request.json'; request.write_text('{}')
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'; artifacts.mkdir(parents=True)
    output = artifacts / 'new'; output.mkdir()
    with pytest.raises(ValueError): audit.run(tmp_path, request, sys.executable, output)
    lock = artifacts / 'development-error-audit-active.lock'; lock.write_text('other')
    with pytest.raises(FileExistsError): audit.run(tmp_path, request, sys.executable, artifacts / 'absent')
    assert lock.read_text() == 'other' and not (artifacts / 'absent').exists()


def test_launcher_dispatches_only_isolated_audit_worker(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, 'verify_request', lambda *a: None)
    monkeypatch.setattr(audit, 'safe_status', lambda value: value)
    request = tmp_path / 'request.json'; request.write_text('{}')
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'; artifacts.mkdir(parents=True)
    output = artifacts / 'new'; calls = []
    def run(args, **kwargs):
        calls.append(args)
        audit.write_new(output / 'aggregate-status.json', {'training_performed': False})
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(audit.subprocess, 'run', run)
    assert audit.run(tmp_path, request, sys.executable, output)['training_performed'] is False
    assert calls[0][1:3] == ['-I', '-B'] and calls[0][3].endswith('development_error_worker.py')
    assert not any('training.py' in arg or '--start-training' == arg for arg in calls[0])
    assert not (artifacts / 'development-error-audit-active.lock').exists()


def test_failed_worker_preserves_outcome_and_releases_lock(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, 'verify_request', lambda *a: None)
    request = tmp_path / 'request.json'; request.write_text('{}')
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'; artifacts.mkdir(parents=True)
    monkeypatch.setattr(audit.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=1))
    with pytest.raises(ValueError, match='preserved'): audit.run(tmp_path, request, sys.executable, artifacts / 'new')
    assert audit.read(artifacts / 'new/worker-outcome.json')['returncode'] == 1
    assert not (artifacts / 'development-error-audit-active.lock').exists()


def constructed_status():
    return dict(schema='lanes-development-error-audit-result-v1', counts=audit.COUNTS, languages=audit.LANGUAGES,
                seeds=[0, 1, 2], primary_seed=0, prediction_records=1215, python_version='3.11.17',
                spacy_version='3.7.5', device='cpu', tokenizer_sha256='a' * 64,
                desktop_metrics_reproduced=True, training_performed=False, holdout_accessed=False, optimizer_updates=0,
                files={name: 'b' * 64 for name in ['predictions.jsonl', 'errors.jsonl', 'metrics.json',
                                                 'desktop-comparison.json', 'checkpoint-hashes.json']})


@pytest.mark.parametrize('change', [{'candidate_ids': ['private']}, {'training_performed': True},
                                   {'holdout_accessed': True}, {'optimizer_updates': 1},
                                   {'python_version': {'text': 'private'}}, {'seeds': [False, True, 2]},
                                   {'counts': {'train': 'private', 'dev': 60}},
                                   {'files': {'private-passage': 'b' * 64}}])
def test_aggregate_rejects_content_and_premature_capabilities(change):
    value = constructed_status()
    assert audit.safe_status(value) == value
    with pytest.raises(ValueError): audit.safe_status({**value, **change})


@pytest.fixture
def request_fixture(tmp_path):
    def binding(name, content):
        path = tmp_path / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content) if not isinstance(content, str) else content, encoding='utf-8')
        return {'path': name, 'sha256': audit.digest(path)}
    development = 'artifacts/constructed-development'
    files = {name: binding(development + '/' + name, 'fixture')['sha256'] for name in
             ['admitted-records.jsonl', 'partitions.json', 'train.spacy', 'dev.spacy', 'tokenizer.bin',
              'admission-ledger.json', 'source-only-join-metadata.json', 'coverage.json']}
    model_files = []
    for i in range(23):
        name = f'file-{i}'
        b = binding('artifacts/model/' + name, 'constructed')
        model_files.append({'path': name, 'bytes': len(b'constructed'), 'sha256': b['sha256']})
    request = {'schema': 'lanes-development-error-audit-v1', 'scope': audit.SCOPE, 'capability': 'development',
               'bindings': {'archive': binding('archive', 'fixture'),
                            'backup_manifest': binding('backup', {'files': {}}),
                            'desktop_results': binding('desktop', {}),
                            'development_status': binding('status', {'capability': 'development', 'counts': audit.COUNTS,
                                                                    'languages': audit.LANGUAGES, 'files': files}),
                            'model_contract': binding('model-contract', {'model': 'tl_calamancy_md', 'version': '0.1.0',
                                'revision': '51a40433059d8a2c25b98a48eca854f8789a491a', 'files': model_files})},
               'development_directory': development, 'model_directory': 'artifacts/model',
               'implementation': [binding('backend/training/flood_ner/' + name, 'constructed') for name in
                    ['development_error_audit.py', 'development_error_worker.py', 'experiment_registry.py',
                     'annotation/schema.py', 'annotation/validation.py', 'evaluation/contract.py']]}
    return tmp_path, request


def test_complete_hash_bound_request(request_fixture):
    root, request = request_fixture
    paths, development, model = audit.verify_request(root, request)
    assert len(paths) == 5 and development.name == 'constructed-development' and model.name == 'model'


@pytest.mark.parametrize('failure', ['scope', 'capability', 'implementation', 'file', 'tokenizer', 'model', 'extra_model'])
def test_preflight_rejects_stale_or_forbidden_bindings(request_fixture, failure):
    root, request = request_fixture
    if failure == 'scope': request['scope'] = 'training'
    if failure == 'capability': request['capability'] = 'research_holdout'
    if failure == 'implementation': request['implementation'].pop()
    if failure == 'file': (root / request['bindings']['desktop_results']['path']).write_text('modified')
    if failure == 'tokenizer': (root / request['development_directory'] / 'tokenizer.bin').write_text('modified')
    if failure == 'model': (root / request['model_directory'] / 'file-0').write_text('modified')
    if failure == 'extra_model': (root / request['model_directory'] / 'extra').write_text('extra')
    with pytest.raises(ValueError): audit.verify_request(root, request)


def test_interrupted_worker_keeps_receipt(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, 'verify_request', lambda *a: None)
    request = tmp_path / 'request.json'; request.write_text('{}')
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'; artifacts.mkdir(parents=True)
    def timeout(*a, **k): raise audit.subprocess.TimeoutExpired('constructed', 1200)
    monkeypatch.setattr(audit.subprocess, 'run', timeout)
    with pytest.raises(ValueError, match='timed out'):
        audit.run(tmp_path, request, sys.executable, artifacts / 'new')
    assert audit.read(artifacts / 'new/worker-outcome.json')['state'] == 'timeout'
    assert not (artifacts / 'development-error-audit-active.lock').exists()


def test_hash_bound_audit_sources_keep_bytes_on_windows_checkout(tmp_path):
    import shutil
    import subprocess
    if not shutil.which('git'):
        pytest.skip('Git required for byte-preservation check')
    root = Path(__file__).resolve().parents[2]
    repo = tmp_path / 'repo'; repo.mkdir()
    def git(*args):
        return subprocess.run(['git', *args], cwd=repo, check=True, capture_output=True)
    git('init', '-q'); git('config', 'core.safecrlf', 'false')
    (repo / '.gitattributes').write_bytes((root / '.gitattributes').read_bytes())
    paths = ['backend/training/flood_ner/development_error_audit.py',
             'backend/training/flood_ner/development_error_worker.py',
             'backend/tests/test_flood_ner_development_error_audit.py']
    for name in paths:
        p = repo / name; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((root / name).read_bytes())
    git('config', 'core.autocrlf', 'true'); git('add', '.')
    for setting in ('true', 'false'):
        git('config', 'core.autocrlf', setting)
        destination = tmp_path / setting
        git('checkout-index', '--all', '--prefix=' + destination.as_posix() + '/')
        assert all((destination / name).read_bytes() == (root / name).read_bytes() for name in paths)
