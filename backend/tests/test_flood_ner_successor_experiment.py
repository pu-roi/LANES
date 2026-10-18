"""Constructed corrections, protocol and CPU qualification checks; no private text."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner import successor_experiment_preparation as prep
from training.flood_ner import successor_experiment_worker as worker


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


@pytest.fixture
def corpus():
    records, metadata = [], []
    for split, languages in [('train', {'english': 170, 'taglish': 175}), ('dev', {'english': 38, 'taglish': 22})]:
        for language, count in languages.items():
            for i in range(count):
                rid = f'fixture-{split}-{language}-{i}'
                text = f'bayan ng Peña; bayan ng Peña. {rid}'
                entities = [{'id': 'first', 'start': 9, 'end': 13, 'text': 'Peña', 'label': 'CITY',
                             'comparison_key': None, 'identity': None},
                            {'id': 'second', 'start': 24, 'end': 28, 'text': 'Peña', 'label': 'CITY',
                             'comparison_key': None, 'identity': None}]
                record = {'schema_version': 'lanes-flood-ner-v1', 'record_id': rid, 'annotation_profile': 'location-only-v1',
                    'passage_language': language, 'source': {'schema_version': 'lanes-flood-ner-v1',
                        'source_id': rid, 'url': 'https://example.invalid/' + rid, 'publisher': 'Constructed test',
                        'title': '', 'language': language, 'origin': 'captured_original', 'text': text,
                        'text_sha256': sha(text), 'capture_version': 'fixture', 'published_at': None,
                        'captured_at': None, 'publication_basis': None, 'article_group': rid, 'event_group': None,
                        'syndication_group': None, 'reuse_status': 'allowed', 'reuse_terms': 'Constructed fixture only',
                        'admission_status': 'training_admitted', 'extraction_method': 'fixture', 'raw_sha256': sha('fixture')},
                    'passage_start': 0, 'passage_end': len(text), 'text': text, 'text_sha256': sha(text),
                    'entities': entities, 'facts': [], 'relations': [], 'annotation_revision': 'fixture-v1',
                    'quality': 'silver', 'teacher': 'constructed-test-teacher', 'reviewer': 'constructed-test-reviewer',
                    'review_status': 'accepted', 'complete': True, 'split': split, 'notes': []}
                records.append(record)
                metadata.append({'record_id': rid, 'partition': split, 'language': language, 'is_negative': False,
                    'passage_sha256': sha(text), 'source_sha256': sha(text), 'passage_start': 0, 'passage_end': len(text),
                    'group_keys': [rid], 'article_group': rid, 'fitted_component': split == 'train', 'alternatives': []})
    original = records[0]
    changes = []
    draft = deepcopy(original)
    for e in draft['entities']:
        before = {k: e[k] for k in ('start', 'end', 'text', 'label')}
        e['start'] -= 9
        e['text'] = original['text'][e['start']:e['end']]
        changes.append({'entity_id': e['id'], 'before': before,
            'proposed': {k: e[k] for k in before},
            'source_evidence': {k: e[k] for k in ('start', 'end', 'text')}})
    draft['review_status'] = 'draft'
    draft['annotation_revision'] += '-proposed'
    proposal = {'record_id': original['record_id'], 'partition': 'train', 'disposition': 'propose_boundary_correction',
        'original_reference_sha256': prep.object_hash(original['entities']), 'original_revision': 'fixture-v1',
        'source_id': original['source']['source_id'], 'source_sha256': original['source']['text_sha256'],
        'source_raw_sha256': original['source']['raw_sha256'], 'text_sha256': original['text_sha256'],
        'changes': changes, 'convention': {'path': 'fixture', 'sha256': sha('fixture')}}
    return records, metadata, [proposal], [draft]


def apply(corpus):
    return prep.apply_proposals(*corpus, expected_records=1, expected_spans=2)


def test_finite_corrections_preserve_every_record_and_repeated_occurrence(corpus):
    records, metadata, _, _ = deepcopy(corpus)
    corrected, ledger = apply(corpus)
    assert len(corrected) == 405 and len(ledger) == 1
    assert [(e['start'], e['end']) for e in corrected[0]['entities']] == [(0, 13), (15, 28)]
    assert corrected[1:] == records[1:]
    assert corpus[0] == records and corpus[1] == metadata
    assert corrected[0]['entities'][0]['id'] == records[0]['entities'][0]['id']
    assert not ledger[0]['human_verified']


@pytest.mark.parametrize('failure', ['old_hash', 'source_hash', 'type', 'text', 'identity', 'new_entity',
    'source_evidence', 'duplicate_occurrence', 'missing_occurrence', 'unauthorized_entity', 'incomplete',
    'duplicate_id', 'validation', 'fragmented_group', 'fitted_leakage', 'overlap', 'alternative', 'duplicate_text'])
def test_unsafe_correction_or_membership_rejected(corpus, failure):
    records, rows, proposals, drafts = corpus
    if failure == 'old_hash': proposals[0]['original_reference_sha256'] = '0' * 64
    if failure == 'source_hash': proposals[0]['source_sha256'] = '0' * 64
    if failure == 'type': proposals[0]['changes'][0]['proposed']['label'] = 'ROAD'
    if failure == 'text': drafts[0]['text'] += 'changed'
    if failure == 'identity': drafts[0]['entities'][0]['id'] = 'replacement'
    if failure == 'new_entity': drafts[0]['entities'].append(deepcopy(drafts[0]['entities'][0]))
    if failure == 'source_evidence': proposals[0]['changes'][0]['source_evidence']['start'] = 1
    if failure == 'duplicate_occurrence': proposals[0]['changes'].append(proposals[0]['changes'][0])
    if failure == 'missing_occurrence': proposals[0]['changes'].pop()
    if failure == 'unauthorized_entity': drafts[0]['entities'][1]['comparison_key'] = 'changed'
    if failure == 'incomplete': records[1]['complete'] = False
    if failure == 'duplicate_id': records[1]['record_id'] = records[0]['record_id']
    if failure == 'validation': proposals[0]['partition'] = 'dev'
    if failure == 'fragmented_group': rows[-1]['group_keys'] = rows[0]['group_keys']
    if failure == 'fitted_leakage': rows[-1]['fitted_component'] = True
    if failure == 'overlap': rows[1]['source_sha256'] = rows[0]['source_sha256']
    if failure == 'alternative': rows[1]['alternatives'] = [rows[0]['record_id']]
    if failure == 'duplicate_text': rows[1]['passage_sha256'] = rows[0]['passage_sha256']
    with pytest.raises(ValueError): apply(corpus)


def test_shared_schema_source_alignment_and_serialization(corpus, tmp_path):
    import spacy
    from training.flood_ner.successor_export_worker import serialize
    corrected, _ = apply(corpus)
    tokenizer = spacy.blank('xx').tokenizer
    parsed = worker.qualify_records(corrected, tokenizer)
    files = serialize(parsed, tokenizer, tokenizer.to_bytes(exclude=['vocab']), tmp_path, 'development')
    assert set(files) == {'train.spacy', 'dev.spacy', 'tokenizer.bin', 'admitted-records.jsonl'}
    for split in ('train', 'dev'):
        worker.verify_docbin(tmp_path / f'{split}.spacy', [r for r in parsed if r[1] == split], tokenizer.vocab)


@pytest.mark.parametrize('failure', ['missing_reference', 'null_reference', 'empty_incomplete', 'unapproved_use',
                                  'bad_offset', 'overlap', 'token_alignment', 'holdout', 'changed_tokenizer'])
def test_record_qualification_guards(corpus, failure):
    import spacy
    record = corpus[0][0]
    if failure == 'missing_reference': del record['entities']
    if failure == 'null_reference': record['entities'] = None
    if failure == 'empty_incomplete': record.update(entities=[], complete=False)
    if failure == 'unapproved_use': record['source']['reuse_status'] = 'unknown'
    if failure == 'bad_offset': record['entities'][0]['text'] = 'wrong'
    if failure == 'overlap': record['entities'][1] = dict(record['entities'][0], id='different')
    if failure == 'token_alignment': record['entities'][0].update(start=10, text='eña')
    if failure == 'holdout': record['split'] = 'test'
    tokenizer = spacy.blank('xx').tokenizer
    if failure == 'changed_tokenizer':
        tokenizer = lambda text: SimpleNamespace(char_span=lambda *a, **kw: None)
    with pytest.raises(ValueError): worker.qualify_records([record], tokenizer)


def test_reload_mismatch_rejected(corpus, tmp_path):
    import spacy
    from training.flood_ner.successor_export_worker import serialize
    tokenizer = spacy.blank('xx').tokenizer
    parsed = worker.qualify_records(corpus[0], tokenizer)
    serialize(parsed, tokenizer, tokenizer.to_bytes(exclude=['vocab']), tmp_path, 'development')
    selected = [r for r in parsed if r[1] == 'train']
    selected.reverse()
    with pytest.raises(ValueError, match='reload mismatch'):
        worker.verify_docbin(tmp_path / 'train.spacy', selected, tokenizer.vocab)


def recipe(seed=0):
    # Minimal constructed template accepted by the historical static validator.
    return f'''[paths]
train = "@@TRAIN@@"
dev = "@@DEV@@"
vectors = null
init_tok2vec = null
[system]
seed = {seed}
[nlp.tokenizer]
model_manifest = "@@MODEL_MANIFEST@@"
manifest_sha256 = "@@MODEL_MANIFEST_SHA256@@"
tokenizer_file = "@@TOKENIZER@@"
[components.ner.model]
nO = null
[corpora.train]
path = ${{paths.train}}
[corpora.dev]
path = ${{paths.dev}}
[training]
max_steps = 1000
max_epochs = 30
eval_frequency = 35
patience = 175
dropout = 0.1
[training.batcher]
size = 8
[training.optimizer]
L2 = 0.01
L2_is_weight_decay = true
learn_rate = 0.001
[training.before_to_disk]
output = "@@CHECKPOINT@@"
'''


@pytest.mark.parametrize('variant', prep.VARIANTS)
@pytest.mark.parametrize('seed', (0, 1, 2))
def test_only_two_declared_parameters_may_differ(variant, seed):
    text = prep.variant_template(recipe(seed), variant, seed)
    prep.verify_variant(text, recipe(seed), variant, seed)
    values = prep.config_values(text)
    assert (values['training', 'dropout'], values['training.optimizer', 'learn_rate']) == prep.PARAMETERS[variant]
    assert values['components.ner.model', 'nO'] == 'null'


@pytest.mark.parametrize('replacement', [('patience = 175', 'patience = 200'), ('L2 = 0.01', 'l2 = 0.01'),
    ('nO = null', 'no = null'), ('max_steps = 1000', 'max_steps = 2000'), ('size = 8', 'size = 16'),
    ('dropout = 0.1', 'dropout = 0.3'), ('learn_rate = 0.001', 'learn_rate = 0.002')])
def test_extra_recipe_changes_rejected(replacement):
    before, after = replacement
    with pytest.raises(ValueError): prep.verify_variant(recipe().replace(before, after), recipe(), 'control', 0)


def outcome(variant, seed, score=.7, state='completed'):
    return dict(variant=variant, seed=seed, state=state, f1=score)


def screening(scores):
    return [outcome(v, 0, s) for v, s in zip(prep.VARIANTS, scores)]


def test_control_tie_completes_in_five_runs():
    rows = screening([.7, .7 + 5e-13, .7])
    assert prep.schedule(rows)['next'] == ['control', 1]
    rows += [outcome('control', 1), outcome('control', 2)]
    result = prep.schedule(rows)
    assert result['retained'] == result['screening_winner'] == 'control'
    assert result['completed_runs'] == 5 and not result['training_started']
    with pytest.raises(ValueError): prep.schedule(rows + [outcome('higher_dropout', 1)])


@pytest.mark.parametrize('winner', ('higher_dropout', 'lower_learning_rate'))
@pytest.mark.parametrize('confirmation,retained_variant', [(.8, True), (.5, False)])
def test_variant_screening_and_confirmation_seven_run_cap(winner, confirmation, retained_variant):
    scores = [.7, .6, .6]
    scores[prep.VARIANTS.index(winner)] = .8
    rows = screening(scores) + [outcome('control', 1), outcome('control', 2)]
    assert prep.schedule(rows)['next'] == [winner, 1]
    rows += [outcome(winner, 1, confirmation), outcome(winner, 2, confirmation)]
    result = prep.schedule(rows)
    assert result['retained'] == (winner if retained_variant else 'control')
    assert result['completed_runs'] == 7
    with pytest.raises(ValueError): prep.schedule(rows + [outcome(winner, 2)])


def test_tolerance_is_relative_to_global_maximum_not_chained():
    rows = screening([.7, .7 + .8e-12, .7 + 1.6e-12])
    assert prep.schedule(rows)['screening_winner'] == 'higher_dropout'


@pytest.mark.parametrize('scores,winner', [([.7, .8, .8], 'higher_dropout'), ([.8, .7, .6], 'control')])
def test_deterministic_screening_preference(scores, winner):
    assert prep.schedule(screening(scores))['screening_winner'] == winner


def test_any_failure_stops_and_forbids_continuation():
    rows = [outcome('control', 0), outcome('higher_dropout', 0, None, 'failed')]
    assert prep.schedule(rows)['state'] == 'stopped_on_failure'
    with pytest.raises(ValueError): prep.schedule(rows + [outcome('lower_learning_rate', 0)])


@pytest.mark.parametrize('bad', [True, float('nan'), float('inf'), -.1, 1.1, None])
def test_invalid_or_rounded_percent_scores_rejected(bad):
    with pytest.raises(ValueError): prep.schedule([outcome('control', 0, bad)])


def test_out_of_order_historical_or_runner_up_outcomes_rejected():
    for rows in [[outcome('v16', 0)], [outcome('control', 1)], [outcome('control', True)],
                 [outcome('control', 0), outcome('control', 0)]]:
        with pytest.raises(ValueError): prep.schedule(rows)


def test_protocol_contains_no_execution_authorization():
    result = prep.protocol()
    assert not result['training_authorized'] and not result['holdout_access_authorized']
    assert result['maximum_runs'] == 7 and result['control_winner_runs'] == 5
    assert prep.schedule([])['next'] == ['control', 0]


def test_existing_output_and_concurrent_writer_stop_before_process(tmp_path, monkeypatch):
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'
    artifacts.mkdir(parents=True)
    grant = tmp_path / 'grant.json'
    prep.write_new(grant, {})
    monkeypatch.setattr(prep, 'verify_grant', lambda *args: None)
    monkeypatch.setattr(prep.subprocess, 'run', lambda *a, **kw: pytest.fail('process must not start'))
    output = artifacts / 'new'
    output.mkdir()
    with pytest.raises(ValueError): prep.prepare(tmp_path, grant, sys.executable, output)
    output.rmdir()
    (artifacts / 'corrected-experiment-preparation-active.lock').write_text('other')
    with pytest.raises(FileExistsError): prep.prepare(tmp_path, grant, sys.executable, output)


def test_failed_preparation_preserves_claim_and_output_no_retry(tmp_path, monkeypatch):
    artifacts = tmp_path / 'backend/training/flood_ner/artifacts'
    artifacts.mkdir(parents=True)
    grant = tmp_path / 'grant.json'
    prep.write_new(grant, {})
    monkeypatch.setattr(prep, 'verify_grant', lambda *args: None)
    monkeypatch.setattr(prep.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=1))
    with pytest.raises(ValueError): prep.prepare(tmp_path, grant, sys.executable, artifacts / 'first')
    assert (artifacts / 'first/worker.stderr').exists()
    assert not (artifacts / 'corrected-experiment-preparation-active.lock').exists()
    with pytest.raises(FileExistsError): prep.prepare(tmp_path, grant, sys.executable, artifacts / 'second')
    assert not (artifacts / 'second').exists()


def test_default_cli_verifies_without_starting_worker(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['prep', '--checkout', str(tmp_path), '--grant', 'grant', '--output', 'output'])
    monkeypatch.setattr(prep, 'prepare', lambda *args: pytest.fail('default must not prepare'))
    monkeypatch.setattr(prep, 'verify_result', lambda *args: {'state': 'verified_read_only'})
    prep.main()
    assert json.loads(capsys.readouterr().out)['state'] == 'verified_read_only'


def test_entry_points_offer_no_training_network_or_inference_command():
    import ast
    for module in (prep, worker):
        source = Path(module.__file__).read_text(encoding='utf-8')
        calls = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Call)]
        assert not any(isinstance(n.func, ast.Attribute) and n.func.attr in ('load', 'initialize', 'train', 'pipe')
                       for n in calls)
        assert not any(isinstance(n.func, ast.Attribute) and n.func.attr == 'update'
                       and isinstance(n.func.value, ast.Name) and n.func.value.id in ('nlp', 'optimizer') for n in calls)


@pytest.fixture
def grant_fixture(tmp_path):
    def put(relative, value):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        prep.write_new(path, value)
        return {'path': relative, 'sha256': prep.digest(path)}
    development, baseline = 'data/development', 'data/baseline'
    exports = {'admission-ledger.json', 'admitted-records.jsonl', 'coverage.json', 'dev.spacy',
               'partitions.json', 'source-only-join-metadata.json', 'tokenizer.bin', 'train.spacy'}
    files = {name: put(development + '/' + name, {})['sha256'] for name in exports}
    status = put(development + '/aggregate-status.json', {'capability': 'development',
                 'counts': {'train': 345, 'dev': 60}, 'files': files})
    baseline_files = {name: put(baseline + '/' + name, {})['sha256'] for name in prep.PAYLOAD_FILES}
    manifest = put(baseline + '/handoff-manifest.json', {'counts': {'train': 345, 'dev': 60}, 'files': baseline_files})
    qualified = {'proposed_records': 9, 'span_corrections': 12, 'records': [dict.fromkeys(
        ('schema_valid', 'source_exact', 'strict_token_alignment', 'nonoverlap'), True) for _ in range(9)]}
    inputs = {key: put('evidence/' + key + '.json', qualified if key == 'proposal_validation' else {})
              for key in ('proposals', 'proposed_records', 'proposal_validation', 'validation_review')}
    inventory = put('evidence/private-output-hashes.json', {v['path']: v['sha256'] for v in inputs.values()})
    audit = put('evidence/audit.json', {'frozen_inputs_unchanged': True, 'holdout_unopened': True,
                                      'private_output_hashes_sha256': inventory['sha256']})
    snapshot = put('evidence/preserved.json', {})
    implementation = [put(path, {}) for path in prep.IMPLEMENTATION]
    tests = put('backend/tests/test_flood_ner_successor_experiment.py', {})
    grant = {'schema': 'lanes-corrected-experiment-grant-v1', 'scope': prep.SCOPE,
        'bindings': {**inputs, 'audit_manifest': audit, 'preservation_snapshot': snapshot,
                     'development_status': status, 'baseline_manifest': manifest},
        'implementation': implementation, 'tests': tests, 'development_directory': development,
        'baseline_directory': baseline, 'model_directory': 'data/model',
        'permissions': dict.fromkeys(('network', 'holdout', 'inference', 'training', 'upload', 'git'), False),
        'expected': {'counts': {'train': 345, 'dev': 60}, 'corrected_records': 9,
                     'corrected_spans': 12, 'historical_anchors': 280}}
    return tmp_path, grant


def test_hash_bound_grant_accepted(grant_fixture):
    root, grant = grant_fixture
    assert prep.verify_grant(root, grant)[1] == root / 'data/development'


@pytest.mark.parametrize('failure', ['stale_proposal', 'stale_implementation', 'stale_test', 'stale_export',
    'missing_audit_binding', 'stale_baseline', 'holdout_binding', 'holdout_directory', 'training_permission',
    'wrong_counts', 'changed_anchor_count', 'unknown_field'])
def test_missing_stale_or_unsafe_grants_rejected(grant_fixture, failure):
    root, grant = grant_fixture
    if failure == 'stale_proposal': (root / grant['bindings']['proposals']['path']).write_text('{}changed')
    if failure == 'stale_implementation': (root / grant['implementation'][0]['path']).write_text('{}changed')
    if failure == 'stale_test': (root / grant['tests']['path']).write_text('{}changed')
    if failure == 'stale_export': (root / 'data/development/train.spacy').write_text('{}changed')
    if failure == 'missing_audit_binding': del grant['bindings']['audit_manifest']
    if failure == 'stale_baseline': (root / 'data/baseline/train-seed-0.cfg').write_text('{}changed')
    if failure == 'holdout_binding': grant['bindings']['proposals']['path'] = 'private-holdout/input.json'
    if failure == 'holdout_directory': grant['development_directory'] = 'private-holdout'
    if failure == 'training_permission': grant['permissions']['training'] = True
    if failure == 'wrong_counts': grant['expected']['counts']['dev'] = 59
    if failure == 'changed_anchor_count': grant['expected']['historical_anchors'] = 279
    if failure == 'unknown_field': grant['start_training'] = True
    with pytest.raises(ValueError): prep.verify_grant(root, grant)


def test_wrong_runtime_stops_before_opening_worker_request(monkeypatch):
    monkeypatch.setattr(sys, 'version_info', (3, 12))
    with pytest.raises(ValueError, match='qualified Python'): worker.main()


@pytest.mark.parametrize('updates,accepted', [({}, True), ({'fixture_parameter': 1}, False)])
def test_schema_resolution_accepts_empty_update_mapping_but_no_actual_updates(tmp_path, monkeypatch, updates, accepted):
    from confection import Config
    from spacy.util import registry
    from training.flood_ner import successor_training as trainer
    package, baseline = tmp_path / 'package', tmp_path / 'baseline'
    package.mkdir(); baseline.mkdir()
    for seed in range(3):
        for folder in (package, baseline): (folder / f'train-seed-{seed}.cfg').write_text(recipe(seed))
    (package / 'model-contract.json').write_text('{}')
    monkeypatch.setattr(Config, 'from_str', lambda *a, **kw: {})
    monkeypatch.setattr(registry, 'resolve', lambda *a, **kw: {'training': {'optimizer': SimpleNamespace(nr_update=updates)}})
    monkeypatch.setattr(trainer, 'render_config', lambda *a, **kw: '')
    if accepted:
        result = worker.schema_qualification(package, baseline, 'control', tmp_path)
        assert len(result['configs']) == 3 and not result['pipeline_created']
    else:
        with pytest.raises(ValueError, match='updates'): worker.schema_qualification(package, baseline, 'control', tmp_path)
