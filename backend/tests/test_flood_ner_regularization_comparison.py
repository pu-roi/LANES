"""Constructed saved predictions; no private passages or model execution."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import stat
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from training.flood_ner import regularization_comparison as c


def test_transitions_reconcile_repeated_unicode_mentions():
    text = 'Peña Road; Peña Road; Osa.'
    gold = [(0, 9, 'ROAD'), (11, 20, 'ROAD')]
    result = c.transitions(gold, [(0, 9, 'CITY')], gold + [(22, 25, 'CITY')], text)
    assert len(result['gained_TP']) == 2
    assert result['resolved_FP'] == [(0, 9, 'CITY')]
    assert result['introduced_FP'] == [(22, 25, 'CITY')]
    assert result['persistent_FN'] == []


def test_overlap_links_are_not_strict_error_totals():
    text = 'Osa Road'
    row = c.diagnose([(0, 3, 'CITY'), (4, 8, 'ROAD')], [(0, 8, 'ROAD')], text)
    assert (row['TP'], row['FP'], row['FN']) == (0, 1, 2)
    assert len(row['overlap_links']) == 2
    delta = c.transitions([(0, 3, 'CITY'), (4, 8, 'ROAD')], [], [(0, 8, 'ROAD')], text)
    assert len(delta['introduced_FP']) == 1 and len(delta['persistent_FN']) == 2


@pytest.mark.parametrize('spans', [None, [(0, 99, 'ROAD')], [(True, 3, 'CITY')],
    [(0, 3, 'DEPTH')], [(0, 3, 'CITY'), (0, 3, 'CITY')], [(0, 3, 'CITY'), (2, 4, 'ROAD')]])
def test_invalid_missing_overlapping_spans(spans):
    with pytest.raises(ValueError): c.transitions([], [], spans, 'Osa Road')


def tiny_records():
    records = {}; metadata = {}
    for split, language, text, spans in [('train', 'english', 'Osa Road', [(0, 8, 'ROAD')]),
                                        ('dev', 'taglish', 'Ulan lamang.', [])]:
        rid = 'constructed-' + split
        records[rid] = {'text': text, 'complete': True, 'entities': [{'start': s, 'end': e, 'label': label}
            for s, e, label in spans], 'text_sha256': c.canonical_hash(text),
            'source': {'text_sha256': c.canonical_hash(text)}}
        metadata[rid] = {'partition': split, 'language': language}
    return records, metadata


def test_full_scores_include_negative_and_unsupported_slices():
    records, metadata = tiny_records()
    old = {'constructed-train': [(0, 8, 'ROAD')], 'constructed-dev': []}
    new = {'train': {'constructed-train': [(0, 8, 'CITY')]}, 'dev': {'constructed-dev': [(0, 4, 'CITY')]}}
    metrics, rows, totals = c.analyze(records, metadata, old, new)
    assert len(rows) == 2 and totals['dev']['introduced_FP'] == 1
    assert metrics['candidate']['dev']['negative_passages']['taglish']['rate'] == 1.0
    assert metrics['candidate']['dev']['labels']['CITY']['f1'] is None
    assert metrics['control']['train']['macro']['f1'] == 1.0
    gaps = c.metric_gaps(metrics['candidate']['train'], metrics['candidate']['dev'])
    assert gaps['labels']['CITY']['f1'] is None


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'holdout', 'language'])
def test_join_mismatch(change):
    records, metadata = tiny_records()
    old = {'constructed-train': [(0, 8, 'ROAD')], 'constructed-dev': []}
    new = {'train': {'constructed-train': []}, 'dev': {'constructed-dev': []}}
    if change == 'missing': new['dev'] = {}
    if change == 'duplicate': new['dev']['extra'] = []
    if change == 'holdout': new['test'] = new.pop('dev')
    if change == 'language': metadata['constructed-dev']['language'] = 'unknown'
    with pytest.raises(ValueError): c.analyze(records, metadata, old, new)


@pytest.mark.parametrize('saved', [2, 2.0 + 1e-8, float('nan'), None])
def test_exact_counts_and_finite_float_check(saved):
    with pytest.raises(ValueError): c.compare_metrics({'count': 1}, {'count': saved})


def test_macro_only_rounding_tolerance():
    c.compare_metrics({'count': 1, 'score': .7}, {'count': 1, 'score': .7 + 1e-16})
    with pytest.raises(ValueError): c.compare_metrics({'score': .7}, {'score': .7 + 2e-12})
    with pytest.raises(ValueError): c.compare_metrics({'score': .7}, {'other': .7})


def test_groups_are_connected_not_raw_key_counts():
    rows = [{'record_id': 'a', 'group_keys': ['article-a', 'event-a']},
            {'record_id': 'b', 'group_keys': ['article-b', 'event-a']},
            {'record_id': 'c', 'group_keys': ['article-b', 'syndication-c']},
            {'record_id': 'd', 'group_keys': ['article-d']}]
    assert c.components(rows) == [['a', 'b', 'c'], ['d']]


def test_exclusive_lock_rejects_competing_writer_and_preserves_owner(tmp_path):
    path = tmp_path / 'active'
    with c.exclusive(path):
        with pytest.raises(FileExistsError):
            with c.exclusive(path): pass
        assert path.exists()
    assert not path.exists()


def test_existing_destination_rejected_without_reading_request(tmp_path):
    output = tmp_path / 'backend/training/flood_ner/artifacts/existing'
    output.mkdir(parents=True); (output / 'preserve').write_bytes(b'original')
    with pytest.raises(ValueError, match='new private destination'):
        c.run(tmp_path, tmp_path / 'missing-request', '0' * 64, output)
    assert (output / 'preserve').read_bytes() == b'original'


def test_stale_request_rejected(tmp_path):
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'; artifacts.mkdir(parents=True)
    request = tmp_path / 'request.json'; request.write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError, match='stale'):
        c.run(tmp_path, request, '0' * 64, artifacts / 'new')


@pytest.mark.parametrize('permission', ['network', 'model_loading', 'inference', 'training', 'holdout'])
def test_forbidden_permissions_cannot_be_granted(tmp_path, permission):
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'; artifacts.mkdir(parents=True)
    request = tmp_path / 'request.json'
    value = {'schema': 'lanes-regularization-comparison-v1', 'scope': c.SCOPE,
        'permissions': dict.fromkeys(('network', 'model_loading', 'inference', 'training', 'holdout', 'git', 'upload'), False),
        'inputs': {}, 'implementation': [], 'tests': {}, 'development_directory': 'fixture'}
    value['permissions'][permission] = True
    request.write_text(json.dumps(value), encoding='utf-8')
    with pytest.raises(ValueError, match='capability'):
        c.run(tmp_path, request, c.digest(request), artifacts / 'new')


def test_holdout_contents_cannot_enter_hash_preservation(tmp_path):
    with pytest.raises(ValueError, match='holdout content'):
        c.preserve(tmp_path, {'files': {'holdout/labels.json': {}}, 'holdout_metadata_only': {}})


@pytest.mark.parametrize('attempt', ['import spacy', 'import torch', 'import thinc',
                                   'import socket; socket.create_connection(("127.0.0.1", 9))',
                                   'import subprocess; subprocess.run(["never-run"])'])
def test_guard_prevents_models_transport_and_processes(attempt):
    script = ('import sys;sys.path.insert(0,' + repr(str(ROOT / 'backend')) + ');'
              'from training.flood_ner.regularization_comparison import install_guards;'
              'install_guards();' + attempt)
    result = subprocess.run([sys.executable, '-I', '-B', '-c', script], capture_output=True, text=True)
    assert result.returncode != 0 and 'comparison forbids' in result.stderr


def test_missing_reference_never_counts_as_negative():
    records, metadata = tiny_records()
    records['constructed-dev']['entities'] = None
    with pytest.raises(ValueError, match='complete development references'):
        c.analyze(records, metadata, {'constructed-train': [], 'constructed-dev': []},
                  {'train': {'constructed-train': []}, 'dev': {'constructed-dev': []}})


def test_incomplete_reference_rejected_even_when_empty():
    records, metadata = tiny_records(); records['constructed-dev']['complete'] = False
    with pytest.raises(ValueError, match='complete development references'):
        c.analyze(records, metadata, {'constructed-train': [], 'constructed-dev': []},
                  {'train': {'constructed-train': []}, 'dev': {'constructed-dev': []}})


def baseline_fixture():
    records, metadata = {}, {}
    for split, languages in [('train', {'english': 170, 'taglish': 175}),
                             ('dev', {'english': 38, 'taglish': 22})]:
        for language, count in languages.items():
            for i in range(count):
                rid = f'constructed-{split}-{language}-{i}'
                records[rid] = {'text': 'fixture', 'entities': [], 'text_sha256': c.canonical_hash('fixture')}
                metadata[rid] = {'partition': split, 'language': language}
    rows = [{'seed': seed, 'record_id': rid, 'partition': metadata[rid]['partition'],
             'language': metadata[rid]['language'], 'text_sha256': raw['text_sha256'],
             'reference': [], 'prediction': []} for seed in range(3) for rid, raw in records.items()]
    return records, metadata, rows


def test_three_seed_baseline_authenticated_primary_join():
    records, metadata, rows = baseline_fixture()
    assert len(c.validated_baseline(rows, records, metadata)) == 405


@pytest.mark.parametrize('failure', ['duplicate', 'identity', 'language', 'text', 'holdout', 'null_reference'])
def test_baseline_mismatches_rejected(failure):
    records, metadata, rows = baseline_fixture()
    if failure == 'duplicate': rows[1] = deepcopy(rows[0])
    if failure == 'identity': rows[0]['record_id'] = 'different'
    if failure == 'language': rows[0]['language'] = 'unknown'
    if failure == 'text': rows[0]['text_sha256'] = 'wrong'
    if failure == 'holdout': rows[0]['partition'] = 'test'
    if failure == 'null_reference': rows[0]['reference'] = None
    with pytest.raises(ValueError): c.validated_baseline(rows, records, metadata)


def test_archive_bytes_and_every_member_are_authenticated(tmp_path):
    payload = {name: b'{}' for name in [c.PREFIX + 'predictions.json', c.PREFIX + 'metrics.json',
                                      'experiment/development-selection.json']}
    manifest = {'files': {name: {'bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest()}
                         for name, value in payload.items()},
                **dict.fromkeys(('holdout_included', 'credentials_included', 'environment_included', 'base_model_included'), False)}
    archive = tmp_path / 'fixture.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        for name, value in {**payload, 'BACKUP-MANIFEST.json': json.dumps(manifest).encode()}.items():
            info = zipfile.ZipInfo(name); info.external_attr = (stat.S_IFREG | 0o600) << 16
            z.writestr(info, value)
    publication = {'archive': {'sha256': c.digest(archive), 'bytes': archive.stat().st_size}, 'archive_members': 4}
    assert len(c.authenticate_archive(archive, manifest, publication)) == 3
    archive.write_bytes(archive.read_bytes() + b'changed')
    with pytest.raises(ValueError, match='stale candidate archive'):
        c.authenticate_archive(archive, manifest, publication)


def review_fixture():
    records, metadata, comparisons, prior = {}, {}, {}, []
    for i in range(60):
        rid = f'constructed-{i}'
        raw = {'text_sha256': 'a' * 64, 'source': {'text': 'fixture', 'text_sha256': 'b' * 64}, 'entities': []}
        records[rid] = raw; metadata[rid] = {'partition': 'dev'}
        comparisons[rid] = {'control': {'FP': 0, 'FN': 0}, 'candidate': {'FP': int(i == 0), 'FN': 0}}
        prior.append({'record_id': rid, 'source_sha256': raw['source']['text_sha256'],
            'text_sha256': raw['text_sha256'], 'reference_sha256': c.canonical_hash([])})
    decisions = [{'record_id': 'constructed-0', 'source_sha256': 'b' * 64, 'text_sha256': 'a' * 64,
        'disposition': 'retain_reference', 'categories': ['nonplace'], 'reason': 'Constructed non-place.',
        'evidence': [{'start': 0, 'end': 7, 'text': 'fixture'}]}]
    return records, metadata, comparisons, decisions, prior


def test_every_validation_record_gets_a_disposition():
    result = c.review_entries(*review_fixture())
    assert len(result) == 60 and sum(r['review_scope'] == 'full_saved_article_and_passage' for r in result) == 1


@pytest.mark.parametrize('failure', ['missing_review', 'duplicate_review', 'stale_source', 'bad_evidence', 'oversized_evidence',
                                   'stale_reference', 'unsupported_correction'])
def test_source_review_is_complete_and_bound(failure):
    values = review_fixture(); decisions, prior = values[-2:]
    if failure == 'missing_review': decisions.clear()
    if failure == 'duplicate_review': decisions.append(deepcopy(decisions[0]))
    if failure == 'stale_source': decisions[0]['source_sha256'] = 'changed'
    if failure == 'bad_evidence': decisions[0]['evidence'][0]['text'] = 'invented'
    if failure == 'oversized_evidence': decisions[0]['evidence'][0]['end'] = 9999
    if failure == 'stale_reference': prior[1]['reference_sha256'] = 'changed'
    if failure == 'unsupported_correction': decisions[0]['disposition'] = 'apply_new_labels'
    with pytest.raises(ValueError): c.review_entries(*values)
