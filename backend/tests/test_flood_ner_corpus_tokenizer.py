"""Corpus boundary/admission isolation and frozen silver-scoring regressions."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
import spacy
from spacy.tokenizer import Tokenizer

from training.flood_ner import corpus_tokenizer_qualification as q
from training.flood_ner.evaluation.contract import evaluation_contract, score_exact_spans
from training.flood_ner.sources import json_bytes


def fixture_payload(tmp_path):
    case = {'case_id': 'location:unicode', 'kind': 'location', 'text': 'Biñan\u202831-A CITY—-Purok',
        'text_sha256': hashlib.sha256('Biñan\u202831-A CITY—-Purok'.encode()).hexdigest(),
        'entities': [{'start': 0, 'end': 5, 'label': 'CITY'}]}
    nlp = spacy.blank('xx')
    data = nlp.tokenizer.to_bytes(exclude=['vocab'])
    rows = []
    doc = nlp.make_doc(case['text'])
    rows.append({'case_id': case['case_id'], 'text_sha256': case['text_sha256'],
        'tokens': [{'start': t.idx, 'end': t.idx + len(t.text), 'text': t.text, 'whitespace': t.whitespace_} for t in doc],
        'reference_alignment': [{'start': 0, 'end': 5, 'label': 'CITY', 'aligned': True}]})
    runs = {}
    for name in ('native', 'candidate', 'corpus-v3'):
        (tmp_path / (name + '.tokenizer.bin')).write_bytes(data)
        runs[name] = {'cases': deepcopy(rows), 'tokenizer_sha256': hashlib.sha256(data).hexdigest(), 'roundtrip_identical': True}
    payload = {'schema_version': 'lanes-corpus-tokenizer-worker-v1', 'operation': 'tokenize_only',
        'python_version': '3.11.17', 'spacy_version': '3.7.5', 'pipeline_components_loaded': [],
        'model_predictions_performed': False, 'model_weights_loaded': False, 'runs': runs}
    return case, payload, {'sha256': hashlib.sha256(data).hexdigest()}


def test_unicode_tokens_and_saved_bytes_are_validated_without_predictions(tmp_path):
    case, payload, manifest = fixture_payload(tmp_path)
    q.validate_payload(payload, [case], tmp_path, manifest)
    restored = Tokenizer(spacy.blank('xx').vocab).from_bytes((tmp_path / 'candidate.tokenizer.bin').read_bytes(), exclude=['vocab'])
    assert restored(case['text']).text == case['text']
    assert json.loads(json_bytes(payload)) == payload


@pytest.mark.parametrize('mutation', ['false_alignment', 'numeric_alignment', 'missing_case', 'duplicate_case',
    'omitted_token', 'changed_unicode', 'changed_whitespace', 'bool_offset', 'wrong_hash', 'roundtrip',
    'pipeline', 'predictions', 'weights', 'extra_entities', 'wrong_python', 'wrong_spacy', 'tokenizer_hash'])
def test_payload_rejects_false_claims_and_malformed_results(tmp_path, mutation):
    case, value, manifest = fixture_payload(tmp_path)
    row = value['runs']['candidate']['cases'][0]
    if mutation == 'false_alignment': row['reference_alignment'][0]['aligned'] = False
    elif mutation == 'numeric_alignment': row['reference_alignment'][0]['aligned'] = 1
    elif mutation == 'missing_case': value['runs']['candidate']['cases'] = []
    elif mutation == 'duplicate_case': value['runs']['candidate']['cases'].append(deepcopy(row))
    elif mutation == 'omitted_token': row['tokens'].pop(0)
    elif mutation == 'changed_unicode': row['tokens'][0]['text'] = 'Binan'
    elif mutation == 'changed_whitespace': row['tokens'][0]['whitespace'] = '\n'
    elif mutation == 'bool_offset': row['tokens'][0]['start'] = False
    elif mutation == 'wrong_hash': row['text_sha256'] = '0' * 64
    elif mutation == 'roundtrip': value['runs']['candidate']['roundtrip_identical'] = 1
    elif mutation == 'pipeline': value['pipeline_components_loaded'] = ['ner']
    elif mutation == 'predictions': value['model_predictions_performed'] = True
    elif mutation == 'weights': value['model_weights_loaded'] = True
    elif mutation == 'extra_entities': row['entities'] = []
    elif mutation == 'wrong_python': value['python_version'] = '3.12.0'
    elif mutation == 'wrong_spacy': value['spacy_version'] = '3.8.0'
    else: manifest['sha256'] = '0' * 64
    with pytest.raises(ValueError): q.validate_payload(value, [case], tmp_path, manifest)


@pytest.mark.parametrize('text', ['Biñan\u2028España', '\t31-A\r\n', 'CITY—-Purok 003-B', '\u0085Zone IV\u2029', ''])
def test_exact_whitespace_reconstruction_and_offsets(text):
    doc = spacy.blank('xx').make_doc(text)
    tokens = [{'start': t.idx, 'end': t.idx + len(t.text), 'text': t.text, 'whitespace': t.whitespace_} for t in doc]
    q.validate_tokens(tokens, text)
    if text:
        with pytest.raises(ValueError): q.validate_tokens(tokens[:-1], text)


def test_metrics_include_record_identity_label_language_negatives_and_undefined_slices():
    truth = {'a': [(0, 5, 'CITY')], 'b': [(0, 5, 'CITY')], 'negative': []}
    pred = {'a': [(0, 5, 'CITY')], 'b': [(0, 5, 'ROAD')], 'negative': [(0, 2, 'LOCAL_AREA')]}
    result = score_exact_spans(truth, pred, {'a': 'english', 'b': 'taglish', 'negative': 'english'})
    assert result['overall']['TP'] == 1 and result['overall']['FP'] == 2 and result['overall']['FN'] == 1
    assert result['overall']['f1'] == pytest.approx(0.4)
    assert result['negative_passages']['overall'] == {'negative_passages': 1, 'false_positive_passages': 1, 'rate': 1.0}
    assert result['negative_passages']['taglish']['rate'] is None
    assert result['labels']['PROVINCE']['precision'] is None and result['labels']['PROVINCE']['f1'] is None
    assert result['languages']['taglish']['recall'] == 0


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'invalid_label', 'bool_offset', 'invalid_language', 'empty'])
def test_metric_inputs_do_not_silently_drop_negative_records_or_invalid_predictions(mutation):
    truth, pred, langs = {'a': []}, {'a': []}, {'a': 'english'}
    if mutation == 'missing': pred = {}
    elif mutation == 'duplicate': pred['a'] = [(0, 2, 'CITY'), (0, 2, 'CITY')]
    elif mutation == 'invalid_label': pred['a'] = [(0, 2, 'LOC')]
    elif mutation == 'bool_offset': pred['a'] = [(False, 2, 'CITY')]
    elif mutation == 'invalid_language': langs['a'] = 'unknown'
    else: truth, pred, langs = {}, {}, {}
    with pytest.raises(ValueError): score_exact_spans(truth, pred, langs)


def test_contract_cannot_claim_qualification_after_a_failed_or_blocked_run():
    for state in ('blocked', 'failed', 'passed'):
        contract = evaluation_contract({}, {'name': q.TOKENIZER_NAME, 'qualified': state == 'passed'}, {'state': state})
        assert (contract['state'] == 'frozen') == (state == 'passed')
        assert contract['model_selection']['primary_seed'] == 0
        assert contract['model_selection']['robustness_seeds'] == [1, 2]
        assert contract['pretrained_comparison']['six_class_accuracy_claim'] is False
        assert contract['rules_baseline']['state'] == 'mapping_required_before_comparison'


def test_manifest_rejects_modified_bytes_and_path_escape(tmp_path):
    (tmp_path / 'evidence').write_bytes(b'original')
    manifest = tmp_path / 'manifest.json'
    manifest.write_bytes(json_bytes({'files': {'evidence': q.digest(tmp_path / 'evidence')}}))
    q.bound_manifest(manifest)
    (tmp_path / 'evidence').write_bytes(b'changed')
    with pytest.raises(ValueError): q.bound_manifest(manifest)
    manifest.write_bytes(json_bytes({'files': {'../escape': '0' * 64}}))
    with pytest.raises(ValueError): q.bound_manifest(manifest)


@pytest.fixture
def admitted_fixture(tmp_path):
    from test_flood_ner_cohort import sample
    evidence = tmp_path / 'evidence.json'
    evidence.write_text('{}')
    reference = {'path': 'evidence.json', 'sha256': q.digest(evidence)}
    rows, entries, old_entries = [], [], []
    for i in range(138):
        source_records = []
        for _ in range(3 if i < 124 else 2):
            n = len(rows)
            row = sample(i)[0]
            row.record_id = f'record-{n:04}'
            row.passage_language = 'english' if n % 2 == 0 else 'taglish'
            row.split = 'train' if n < 280 else 'dev' if n < 340 else 'test'
            row.source.reuse_status = 'allowed'
            row.source.admission_status = 'training_admitted'
            row.source.reuse_terms = q.SCOPE
            rows.append(row)
            source_records.append(row)
        members = q.membership(source_records)
        entry = {'source_id': row.source.source_id, 'capture_version': row.source.capture_version,
            'source_sha256': row.source.text_sha256, 'url': row.source.url,
            'decision': 'adopt_private_academic_basis' if i < 69 else 'prior_desktop_reported_adoption' if i < 137 else 'prior_local_adoption',
            'evidence': reference, 'provenance_reference': reference, 'scope': q.SCOPE,
            'permission_claimed': False, 'admission_applied': True,
            'assessor': {'kind': 'ai', 'capacity': 'acting_under_explicit_researcher_delegation'},
            'applied_at': '2026-10-16T12:00:00+08:00', 'memberships': members,
            'selection_sha256': hashlib.sha256(json_bytes(members)).hexdigest(), 'samples': len(source_records),
            'admission_status': 'training_admitted', 'reuse_status': 'allowed', 'reuse_terms': q.SCOPE}
        entries.append(entry)
        old_entries.append(deepcopy(entry))
    ledger = {'schema_version': 'lanes-private-academic-admission-v1', 'scope': q.SCOPE,
        'admission_applied': True, 'training_admitted': 400, 'source_articles': 138, 'sample_memberships': 400,
        'publisher_permission_claimed': False, 'legal_approval_claimed': False, 'dataset_license_granted': False,
        'canonical_desktop_v2': False, 'desktop_predecessor_unreconciled': True, 'articles': entries,
        'unchanged_nonacademic_outcomes': [{} for _ in range(12)],
        'provenance': {'applied_at': '2026-10-16T12:00:00+08:00'}}
    index = {'articles': old_entries, 'unchanged_nonacademic_outcomes': [{} for _ in range(12)]}
    return ledger, rows, deepcopy(rows[:40]), index


def test_admission_scope_and_all_distinct_memberships_bind_to_actual_records(tmp_path, admitted_fixture):
    q.validate_admission(*admitted_fixture, tmp_path)


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'source_hash', 'unknown_reuse', 'context_policy',
    'scope', 'split', 'memberships', 'evidence', 'decision', 'permission', 'nonacademic', 'desktop_claim', 'bool_count'])
def test_unqualified_or_mismatched_admission_is_rejected(tmp_path, admitted_fixture, mutation):
    ledger, rows, contexts, index = admitted_fixture
    if mutation == 'missing': ledger['articles'].pop()
    elif mutation == 'duplicate': ledger['articles'][-1] = deepcopy(ledger['articles'][0])
    elif mutation == 'source_hash': rows[0].source.text_sha256 = '0' * 64
    elif mutation == 'unknown_reuse': rows[0].source.reuse_status = 'unknown'
    elif mutation == 'context_policy': contexts[0].source.reuse_terms = 'unrestricted'
    elif mutation == 'scope': ledger['scope'] = 'production_use'
    elif mutation == 'split': rows[0].split = 'test'
    elif mutation == 'memberships': ledger['articles'][0]['memberships'].pop()
    elif mutation == 'evidence': ledger['articles'][0]['evidence']['sha256'] = '0' * 64
    elif mutation == 'decision': ledger['articles'][0]['decision'] = 'permission'
    elif mutation == 'permission': ledger['publisher_permission_claimed'] = True
    elif mutation == 'nonacademic': ledger['unchanged_nonacademic_outcomes'].pop()
    elif mutation == 'desktop_claim': ledger['desktop_predecessor_unreconciled'] = False
    else: ledger['sample_memberships'] = True
    with pytest.raises(ValueError): q.validate_admission(ledger, rows, contexts, index, tmp_path)


@pytest.mark.parametrize('mutation', ['bytes', 'vocab', 'model', 'cases', 'filename', 'state'])
def test_candidate_manifest_rejects_wrong_model_vocabulary_or_saved_bytes(tmp_path, mutation):
    model = tmp_path / 'model.json'; model.write_text('{}')
    tokenizer = tmp_path / 'candidate.tokenizer.bin'; tokenizer.write_bytes(b'fixture tokenizer')
    value = {'schema_version': 'lanes-calamancy-tokenizer-v1', 'name': q.TOKENIZER_NAME,
        'qualification_state': 'passed', 'model_revision': q.MODEL_REVISION,
        'model_manifest_sha256': q.digest(model), 'serialization_excludes': ['vocab'],
        'tokenizer_file': tokenizer.name, 'sha256': q.digest(tokenizer), 'vocabulary_files': [],
        'cases_sha256': q.digest(q.CONSTRUCTED_CASES)}
    manifest = tmp_path / 'tokenizer_manifest.json'
    manifest.write_bytes(json_bytes(value))
    q.verify_tokenizer(manifest, model, {'files': []})
    if mutation == 'bytes': tokenizer.write_bytes(b'changed')
    elif mutation == 'vocab': value['vocabulary_files'] = [{'path': 'vocab/vectors'}]
    elif mutation == 'model': value['model_manifest_sha256'] = '0' * 64
    elif mutation == 'cases': value['cases_sha256'] = '0' * 64
    elif mutation == 'filename': value['tokenizer_file'] = '../candidate.tokenizer.bin'
    else: value['qualification_state'] = 'failed'
    manifest.write_bytes(json_bytes(value))
    with pytest.raises(ValueError): q.verify_tokenizer(manifest, model, {'files': []})


def run_fixture(tmp_path, monkeypatch):
    root = tmp_path
    artifacts = root / 'backend/training/flood_ner/artifacts'
    artifacts.mkdir(parents=True)
    interpreter = artifacts / 'research/python.exe'
    interpreter.parent.mkdir()
    interpreter.write_bytes(b'isolated executable fixture')
    model_manifest, tokenizer_manifest = artifacts / 'model.json', artifacts / 'tokenizer.json'
    model_manifest.write_text('{}'); tokenizer_manifest.write_text('{}')
    cohort = artifacts / 'cohort'; cohort.mkdir(); (cohort / 'tokenizer.bin').write_bytes(b'corpus')
    context = artifacts / 'context'; context.mkdir()
    admission = artifacts / 'admission.json'; admission.write_text('{}')
    monkeypatch.setattr(q, 'inputs', lambda *a: ([], [], {}))
    monkeypatch.setattr(q, 'verify_model', lambda *a: ({'files': []}, artifacts))
    monkeypatch.setattr(q, 'verify_tokenizer', lambda *a: ({'name': q.TOKENIZER_NAME, 'sha256': '0' * 64}, tokenizer_manifest))
    monkeypatch.setattr(q, 'bound_manifest', lambda *a: {})
    return dict(python=interpreter, model_manifest=model_manifest, tokenizer_manifest=tokenizer_manifest,
        cohort=cohort, context=context, admission_manifest=admission, output=artifacts / 'output', root=root)


@pytest.mark.parametrize('outcome', ['application_control', 'timeout', 'malformed_json', 'wrong_payload', 'list_payload', 'string_payload'])
def test_failed_subprocess_is_preserved_and_never_retried_or_qualified(tmp_path, monkeypatch, outcome):
    arguments = run_fixture(tmp_path, monkeypatch)
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        assert '-I' in command and kwargs['timeout'] == 300
        assert kwargs['env']['HF_HUB_OFFLINE'] == '1'
        if outcome == 'timeout': raise subprocess.TimeoutExpired(command, 300, stderr=b'partial stderr')
        if outcome == 'application_control': return SimpleNamespace(returncode=1, stdout=b'', stderr=b'OSError: [WinError 4551] blocked DLL')
        stdout = {'malformed_json': b'not JSON', 'wrong_payload': b'{}', 'list_payload': b'[]', 'string_payload': b'"invalid"'}[outcome]
        return SimpleNamespace(returncode=0, stdout=stdout, stderr=b'')
    monkeypatch.setattr(q.subprocess, 'run', run)
    result = q.qualify_corpus_tokenizer(**arguments)
    assert len(calls) == 1 and result['state'] != 'passed'
    assert result['model_predictions_performed'] is False
    contract = q.read(arguments['output'] / 'evaluation-contract.json')
    assert contract['state'] == 'protocol_frozen_tokenizer_qualification_pending'
    assert q.read(arguments['output'] / 'manifest.json')['tokenizer_qualified'] is False
    if outcome == 'application_control':
        assert result['application_control_4551'] is True
        assert b'4551' in (arguments['output'] / 'worker.stderr.log').read_bytes()
    with pytest.raises(ValueError): q.qualify_corpus_tokenizer(**arguments)
    assert len(calls) == 1


def test_cli_requires_all_explicit_inputs_and_existing_constructed_guards_remain():
    from training.flood_ner.cli import main
    with pytest.raises(SystemExit): main(['qualify-corpus-tokenizer'])
    from training.flood_ner.tokenizer_qualification import load_cases
    assert len(load_cases(q.CONSTRUCTED_CASES)) == 48


@pytest.mark.parametrize('state,exit_code', [('passed', 0), ('failed', 2), ('blocked', 2)])
def test_corpus_cli_reports_qualification_state_without_claiming_inference(tmp_path, monkeypatch, capsys, state, exit_code):
    from training.flood_ner.cli import main
    monkeypatch.setattr(q, 'qualify_corpus_tokenizer', lambda *a: {'state': state, 'error': 'blocked evidence' if state == 'blocked' else None})
    args = ['qualify-corpus-tokenizer']
    for name in ('python', 'model-manifest', 'tokenizer-manifest', 'cohort', 'context', 'admission-manifest', 'output'):
        args.extend(['--' + name, str(tmp_path / name)])
    assert main(args) == exit_code
    captured = capsys.readouterr()
    assert json.loads(captured.out)['state'] == state
    if state == 'blocked': assert 'blocked evidence' in captured.err


def test_corpus_worker_refuses_main_interpreter_and_overwriting_before_launch(tmp_path, monkeypatch):
    arguments = run_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(q.subprocess, 'run', lambda *a, **kw: pytest.fail('invalid inputs launched worker'))
    with pytest.raises(ValueError): q.qualify_corpus_tokenizer(**(arguments | {'python': Path(sys.executable)}))
    arguments['output'].mkdir()
    with pytest.raises(ValueError): q.qualify_corpus_tokenizer(**arguments)


@pytest.mark.parametrize('bad', [{'runs': None}, {'runs': {'native': []}}, {'runs': {'native': {'cases': [None]}}}])
def test_structurally_malformed_worker_results_are_explicit_validation_errors(tmp_path, bad):
    case, payload, manifest = fixture_payload(tmp_path)
    payload.update(bad)
    with pytest.raises(ValueError): q.validate_payload(payload, [case], tmp_path, manifest)


def test_worker_does_not_import_a_pipeline_or_call_model_loading():
    import ast
    tree = ast.parse(Path(q.__file__).with_name('corpus_tokenizer_worker.py').read_text(encoding='utf-8'))
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr in {'load', 'pipe', 'predict', 'update', 'initialize', 'add_pipe'} for node in ast.walk(tree))
