"""Qualification measures coverage and compatibility without authorizing training."""
import hashlib
import json
from copy import deepcopy

import pytest

from training.flood_ner.annotation.schema import AnnotationRecord, text_hash
from training.flood_ner.cohort import build_cohort
from training.flood_ner.export import CANDIDATE_TOKENIZER_NAME, corpus_tokenizer
from training.flood_ner.qualification import load_frozen_cohort, model_compatibility, qualification_report
from training.flood_ner.sources import read_jsonl, write_jsonl


def sample(i, language='english', split='train'):
    text = f'Main Road {i} in Barangay Catmon.'
    domain = 'gmanetwork.com' if language == 'english' else 'rmn.ph'
    return AnnotationRecord.model_validate({
        'record_id': f'qualification-{i}', 'annotation_profile': 'location-only-v1',
        'passage_language': language, 'source': {
            'source_id': f's{i}', 'url': f'https://{domain}/article/{i}', 'publisher': domain,
            'text': text, 'text_sha256': text_hash(text), 'capture_version': f'v{i}',
            'article_group': f'a{i}', 'event_group': f'e{i}', 'syndication_group': f'y{i}',
            'reuse_terms': 'unknown', 'extraction_method': 'fixture',
        }, 'passage_start': 0, 'passage_end': len(text), 'text': text, 'text_sha256': text_hash(text),
        'entities': [{'id': 'road', 'label': 'ROAD', 'start': 0, 'end': len(f'Main Road {i}'), 'text': f'Main Road {i}'}],
        'annotation_revision': 'fixture-v1', 'teacher': 'test teacher', 'reviewer': 'test reviewer',
        'complete': True, 'review_status': 'accepted', 'split': split,
    })


def test_qualification_counts_and_confounds_are_not_accuracy_or_admission():
    rows = [sample(i, language, split) for i, (split, language) in enumerate(
        (s, l) for s in ('train', 'dev', 'test') for l in ('english', 'taglish'))]
    before = deepcopy([r.model_dump() for r in rows])
    report = qualification_report(rows, corpus_tokenizer())
    assert report['samples'] == report['accepted_annotations'] == 6
    assert report['source_articles'] == 6 and report['entity_spans'] == 6
    assert report['publisher_majority_language_fraction'] == 1
    assert report['publisher_majority_language_fraction_is_not_ner_accuracy']
    assert report['training_admitted'] == report['export_ready_records'] == 0
    assert not report['actual_model_inference_performed'] and not report['training_performed']
    assert report['candidate_tokenizer']['corpus_alignment_errors'] == []
    assert len(report['slices']) == 6
    assert [r.model_dump() for r in rows] == before


def test_empty_place_labels_and_unresolved_identity_do_not_become_clearance():
    row = sample(0); row.entities = []
    report = qualification_report([row], corpus_tokenizer())
    assert report['slices'][0]['empty_place_records'] == 1
    assert 'not absence of flooding' in report['notes'][0]
    assert report['declared_gold_records'] == 0
    assert not report['independent_review_verified_by_this_tool']


@pytest.mark.parametrize('change', ['profile', 'split', 'source'])
def test_qualification_refuses_unbound_or_wrong_profile_records(change):
    row = sample(0)
    if change == 'profile': row.annotation_profile = 'context-rich-v1'
    elif change == 'split': row.split = None
    else: row.text = 'fabricated text'
    with pytest.raises(ValueError): qualification_report([row], corpus_tokenizer())


def test_frozen_loader_uses_saved_tokenizer_and_rejects_hash_or_path_tampering(tmp_path):
    # Reuse the independently tested small cohort fixture, not the real corpus.
    from test_flood_ner_cohort import bundle, SMALL
    records, reviews, sources = bundle()
    folder = tmp_path / 'backend/training/flood_ner/artifacts/cohort'
    build_cohort(records, reviews, sources, tmp_path, folder, targets=SMALL, publisher_cap=2)
    restored, _, manifest = load_frozen_cohort(folder)
    assert len(restored) == manifest['total'] == 6
    original = (folder / 'grouped_annotations.jsonl').read_bytes()
    (folder / 'grouped_annotations.jsonl').write_bytes(original + b' ')
    with pytest.raises(ValueError, match='hash mismatch'): load_frozen_cohort(folder)
    (folder / 'grouped_annotations.jsonl').write_bytes(original)
    manifest['files']['../outside.json'] = '0' * 64
    (folder / 'partition_manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='outside its root'): load_frozen_cohort(folder)


def test_model_metadata_compatibility_is_not_model_or_tokenizer_qualification(tmp_path):
    meta = {'version': '0.2.0', 'spacy_version': '>=3.8.3', 'license': 'MIT', 'labels': {'ner': ['LOC', 'ORG', 'PER']}}
    path = tmp_path / 'meta.json'; path.write_text(json.dumps(meta))
    row = {'model': 'fixture model', 'version': '0.2.0', 'revision': 'pinned-fixture',
           'spacy_requirement': '>=3.8.3', 'ner_labels': ['LOC', 'ORG', 'PER'], 'license': 'MIT',
           'files': {'meta.json': {'raw_path': 'meta.json', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}}}
    result = model_compatibility([row], tmp_path)[0]
    assert not result['declared_spacy_compatibility']
    assert not result['fine_grained_lanes_labels_available']
    assert not result['weights_loaded'] and not result['runtime_tokenizer_qualified']
    meta.update(version='0.1.0', spacy_version='>=3.5.0,<4.0.0')
    path.write_text(json.dumps(meta))
    row.update(version='0.1.0', spacy_requirement=meta['spacy_version'])
    row['files']['meta.json']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert model_compatibility([row], tmp_path)[0]['state'] == 'metadata_compatible_only'
    row['license'] = 'invented license'
    with pytest.raises(ValueError, match='does not match'): model_compatibility([row], tmp_path)


@pytest.mark.parametrize('separator', ['\u0085', '\u2028', '\u2029'])
def test_jsonl_preserves_alternate_unicode_separators_without_splitting_records(tmp_path, separator):
    row = sample(0)
    text = row.text + separator + 'Purok 12 — bahay.'
    row.text = row.source.text = text
    row.text_sha256 = row.source.text_sha256 = text_hash(text)
    row.passage_end = len(text)
    path = tmp_path / 'records.jsonl'
    write_jsonl(path, [row])
    assert len(path.read_bytes().decode('utf8').splitlines()) == 1
    assert read_jsonl(path, AnnotationRecord)[0].model_dump() == row.model_dump()
    # Accept legacy externally produced JSONL with a literal Unicode separator.
    path.write_text(json.dumps(row.model_dump(mode='json'), ensure_ascii=False) + '\n', encoding='utf8')
    assert read_jsonl(path, AnnotationRecord)[0].text == text


@pytest.mark.parametrize('text,name', [
    ('CAUAYAN CITY– Floods', 'CAUAYAN CITY'), ('CAUAYAN CITY—Floods', 'CAUAYAN CITY'),
    ('along –Bonifacio Drive', 'Bonifacio Drive'), ('along —Bonifacio Drive', 'Bonifacio Drive'),
    ('“Barangay Catmon”', 'Barangay Catmon'), ('Quezon\u00a0City: baha', 'Quezon\u00a0City'),
    ('Sitio 006-A.', 'Sitio 006-A'), ('Blk. 12/Lot 04, Phase II', 'Lot 04'),
    ('Zone IV-A; baha', 'Zone IV-A'), ('Unit 3B:', 'Unit 3B'),
    ('Purok 1 to 2—baha', 'Purok 1 to 2'), ('Purok 2–baha', 'Purok 2'),
    ('Quezon City\u2028flooded', 'Quezon City'), ("Sitio Dela Peña's road", 'Sitio Dela Peña'),
])
def test_candidate_tokenizer_handles_address_boundaries_without_changing_text(text, name):
    nlp = corpus_tokenizer(CANDIDATE_TOKENIZER_NAME)
    doc = nlp.make_doc(text); start = text.index(name)
    assert doc.text == text and doc.char_span(start, start + len(name), alignment_mode='strict').text == name
    if '006-A' in text: assert any(t.text == '006-A' for t in doc)


def test_candidate_fix_keeps_frozen_v2_default_and_refuses_unknown_versions():
    text = 'Purok 1 to 2—baha'; end = len('Purok 1 to 2')
    assert corpus_tokenizer().make_doc(text).char_span(0, end, alignment_mode='strict') is None
    assert corpus_tokenizer(CANDIDATE_TOKENIZER_NAME).make_doc(text).char_span(0, end, alignment_mode='strict').text == text[:end]
    with pytest.raises(ValueError): corpus_tokenizer('unversioned-change')


def test_cli_surfaces_malformed_frozen_manifest_without_writing_output(tmp_path, capsys, monkeypatch):
    from training.flood_ner import cli
    monkeypatch.setattr(cli, 'REPO_ROOT', tmp_path)
    folder = tmp_path / 'corrupt'; folder.mkdir()
    (folder / 'partition_manifest.json').write_text('{"files": []}')
    output = tmp_path / 'backend/training/flood_ner/artifacts/should-not-exist'
    assert cli.main(['qualify-cohort', str(folder), '--news-register', str(tmp_path / 'unused.json'),
                 '--output', str(output)]) == 1
    assert not output.exists() and 'frozen manifest must bind' in capsys.readouterr().err


def test_qualification_destination_guard_preserves_previous_results(tmp_path):
    from training.flood_ner.qualification import write_qualification
    output = tmp_path / 'backend/training/flood_ner/artifacts/frozen'; output.mkdir(parents=True)
    (output / 'keep.json').write_text('original')
    with pytest.raises(ValueError, match='must be new'):
        write_qualification(tmp_path, tmp_path / 'unused.json', tmp_path, output)
    assert (output / 'keep.json').read_text() == 'original'
    with pytest.raises(ValueError, match='ignored training artifacts'):
        write_qualification(tmp_path, tmp_path / 'unused.json', tmp_path, tmp_path / 'outside')


@pytest.mark.parametrize('malformation', ['path', 'metadata', 'dependency'])
def test_malformed_model_evidence_returns_actionable_validation_error(tmp_path, malformation):
    meta = {'version': '0.1.0', 'spacy_version': '>=3.5.0,<4.0.0', 'license': 'MIT',
            'labels': {'ner': ['LOC']}, 'requirements': [123] if malformation == 'dependency' else []}
    path = tmp_path / 'meta.json'; path.write_text(json.dumps([] if malformation == 'metadata' else meta))
    row = {'model': 'fixture', 'revision': 'fixture', 'version': '0.1.0', 'spacy_requirement': meta['spacy_version'],
           'ner_labels': ['LOC'], 'license': 'MIT', 'files': {'meta.json': {
               'raw_path': 123 if malformation == 'path' else 'meta.json',
               'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}}}
    with pytest.raises(ValueError): model_compatibility([row], tmp_path)
