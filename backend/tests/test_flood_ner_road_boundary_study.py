"""Fictional boundary contracts and mocked training views; no private text."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from training.flood_ner import road_boundary_rules as r
from training.flood_ner import road_boundary_study as s
from training.flood_ner.road_boundary_cases import core_cases


@pytest.mark.parametrize('case', core_cases(), ids=lambda x: x['case_id'])
def test_fictional_matrix(case):
    before = deepcopy(case['prediction']); result = r.propose('opaque', case['text'], before)
    assert result['shadow'] == case['expected_shadow']
    assert all(d['action'] == case['expected_action'] and d['abstained'] == case['expected_abstention'] for d in result['decisions'])
    assert r.propose('opaque', case['text'], result['shadow'])['shadow'] == result['shadow']
    assert before == case['prediction']
    assert r.propose('another-id', case['text'], before)['decisions'] == result['decisions']
    for d in result['decisions']:
        for proof in d['evidence']: assert case['text'][proof['start']:proof['end']] == proof['text']


def test_full_fixture_contract_and_unscored_ambiguity():
    assert s.fixture_checks(core_cases()) == {'passed': 24, 'definitive': 18, 'ambiguous_unscored': 6}
    broken = deepcopy(core_cases()); broken[0]['text'] += '!'
    with pytest.raises(ValueError): s.fixture_checks(broken)


@pytest.mark.parametrize('text', ['Aster-Hilaga Road', 'Aster/Hilaga Road', 'Aster Road Hilaga',
    'Aster Avenue Hilaga', 'Intersection Road', 'Northbound Road', 'Aster Corner Road'])
def test_no_unmarked_split_or_integral_name_trimming(text):
    original = [[0, len(text), 'ROAD']]
    assert r.propose('opaque', text, original)['shadow'] == original


def test_named_road_and_incomplete_crossing_abstain():
    text = 'It is named Aster Road Junction'; start = len('It is named ')
    result = r.propose('opaque', text, [[start, len(text), 'ROAD']])
    assert result['decisions'][0]['abstained'] and result['decisions'][0]['action'] == 'keep'
    for text in ['Aster Road corner Hilaga', 'Aster Road corner Hilaga Street northbound',
                 'Aster Road corner Hilaga Street corner Piña Road']:
        d = r.propose('opaque', text, [[0, len(text), 'ROAD']])['decisions'][0]
        assert d['action'] == 'keep' and d['abstained']


@pytest.mark.parametrize('label', ['CITY', 'LANDMARK', 'BARANGAY', 'LOCAL_AREA', 'PROVINCE'])
def test_nonroad_entities_never_retyped_or_trimmed(label):
    text = 'Peña Road Intersection'; old = [[0, len(text), label]]
    assert r.propose('opaque', text, old)['shadow'] == old


def test_prefix_expansion_is_not_attempted():
    text = 'Aster-Peña Road'; start = len('Aster-'); old = [[start, len(text), 'ROAD']]
    assert r.propose('opaque', text, old)['shadow'] == old


def test_conflicting_candidates_abstain():
    original = [[0, 20, 'ROAD']]
    candidates = [{'children': [[0, 10, 'ROAD']]}, {'children': [[0, 9, 'ROAD']]}]
    children, action, abstained = r.resolve(original, candidates, [])
    assert children == original and action == 'keep' and abstained


@pytest.mark.parametrize('children', [[], [[0, 50, 'ROAD']], [[0, 3, 'CITY']],
    [[0, 5, 'ROAD'], [4, 9, 'ROAD']]])
def test_bad_child_geometry_and_type_rejected(children):
    old = [[0, 9, 'ROAD']]; decisions = [{'original': old[0], 'children': children, 'action': 'split'}]
    with pytest.raises(ValueError): r.check_output('Peña Road', old, decisions, children)


@pytest.mark.parametrize('bad', [None, [[True, 3, 'ROAD']], [[0, 99, 'ROAD']], [[0, 3, 'ROAD'], [0, 3, 'ROAD']],
    [[0, 4, 'ROAD'], [3, 7, 'ROAD']], [[0, 3, 'ORG']]])
def test_invalid_original_spans(bad):
    with pytest.raises(ValueError): r.propose('opaque', 'Peña Road', bad)


@pytest.mark.parametrize('field', ['reference', 'expected_label', 'source_id', 'language'])
def test_reference_and_identity_separation(field):
    with pytest.raises(ValueError): r.raw_record({'record_id': 'opaque', 'text': 'Peña Road', 'prediction': [], field: []})


def test_unknown_rule_rejected():
    with pytest.raises(ValueError): r.propose('opaque', 'Peña Road', [], enabled={'expand_prefix'})


def synthetic_views():
    raw, refs = [], []
    cases = [c for c in core_cases() if c['contrast'] == 'supported' and c['language'] == 'english']
    for i in range(345):
        c = cases[i % 3]; rid = 'train-fictional-' + str(i)
        raw.append({'record_id': rid, 'text': c['text'], 'prediction': c['prediction']})
        refs.append({'record_id': rid, 'partition': 'train', 'language': 'english' if i < 170 else 'taglish',
            'text_sha256': c['text_sha256'], 'reference': c['expected_entities']})
    return raw, refs


def synthetic_evidence(raw, refs):
    refs = {x['record_id']: x for x in refs}; reviews = {}; sources = {}
    for row in raw:
        sha = hashlib.sha256(row['text'].encode()).hexdigest(); sources[sha] = row['text']
    for rid, errors in s.road_roster(raw, refs).items():
        row = next(x for x in raw if x['record_id'] == rid)
        reviews[rid] = {'errors': errors, 'full_article_reviewed': True, 'text_sha256': refs[rid]['text_sha256'],
            'source_sha256': refs[rid]['text_sha256'], 'passage_start': 0, 'passage_end': len(row['text']),
            'disposition': 'source_supported_boundary_candidate', 'reason': 'Fictional explicit contrast.'}
    grounding = {key: [{'record_id': raw[i]['record_id'], 'text_sha256': refs[raw[i]['record_id']]['text_sha256'],
        'start': 0, 'end': len(raw[i]['text']), 'text': raw[i]['text']}] for i, key in enumerate(r.RULES)}
    return {'sources': sources, 'reviews': reviews, 'grounding': grounding}


def test_scoring_split_counts_and_unsupported_slices():
    raw, references = synthetic_views(); refs = s.validate_view(raw, references)
    result, decisions, changes = s.score_shadow(raw, refs, set(r.RULES))
    assert result['counts']['gained_TP'] == 460 and result['counts']['resolved_FP'] == 345
    assert result['counts']['introduced_FP'] == result['counts']['introduced_FN'] == 0
    assert result['counts']['net_entity_change'] == 115
    assert result['metrics']['overall']['f1'] == 1 and result['metrics']['labels']['CITY']['f1'] is None
    assert len(decisions) == len(changes) == 345


@pytest.mark.parametrize('damage', ['missing', 'wrong_source', 'wrong_text', 'null_reference', 'nontraining'])
def test_incomplete_reviews_or_references_rejected(damage):
    raw, references = synthetic_views(); refs = s.validate_view(raw, references); evidence = synthetic_evidence(raw, references)
    rid = raw[0]['record_id']
    if damage == 'missing': del evidence['reviews'][rid]
    if damage == 'wrong_source': evidence['sources'][references[0]['text_sha256']] += '!'
    if damage == 'wrong_text': evidence['reviews'][rid]['text_sha256'] = '0' * 64
    if damage == 'nontraining': evidence['grounding']['terminal_descriptor'][0]['record_id'] = 'validation-hidden'
    if damage == 'null_reference': refs[rid]['reference'] = None
    with pytest.raises(ValueError): s.verify_reviews(raw, refs, evidence)


def make_package(root):
    artifacts = root / 'backend/training/flood_ner/artifacts'; artifacts.mkdir(parents=True)
    def dump(p, value): p.write_text(json.dumps(value), encoding='utf-8')
    def binding(p): return {'path': p.relative_to(root).as_posix(), 'sha256': s.digest(p)}
    for name in [*s.SOURCES, s.TEST, 'old-test.py']:
        p = root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('fictional source binding')
    implementation = [binding(root / n) for n in s.SOURCES]; tests = binding(root / s.TEST)
    view = artifacts / 'view'; view.mkdir(); raw, refs = synthetic_views()
    for name, rows in [('raw-predictions.jsonl', raw), ('references.jsonl', refs)]:
        (view / name).write_text('\n'.join(json.dumps(x) for x in rows), encoding='utf-8')
    baseline, _, _ = s.score_shadow(raw, {x['record_id']: x for x in refs}, set())
    dump(view / 'baseline-metrics.json', baseline['metrics'])
    dump(view / 'manifest.json', {'schema': 'lanes-context-training-view-v1', 'capability': 'training_only', 'count': 345,
        'primary_seed': 0, 'validation_emitted': False, 'holdout_accessed': False,
        'implementation': implementation[3:], 'tests': binding(root / 'old-test.py'),
        'files': {p.name: s.digest(p) for p in view.iterdir()}})
    dump(root / 'reviews.json', synthetic_evidence(raw, refs))
    dump(root / 'evidence.json', {'scope': 'constructed_checks_only', 'passed': 1, 'failed': 0,
        'implementation': implementation, 'tests': tests})
    (root / 'guide.md').write_text('Fictional conventions')
    grant = {'schema': 'lanes-road-boundary-grant-v1', 'scope': s.SCOPE, 'protocol': s.POLICY,
        'inputs': {k: binding(root / name) for k, name in {'training_manifest': str((view / 'manifest.json').relative_to(root)),
            'reviews': 'reviews.json', 'annotation_guide': 'guide.md', 'scope_guide': 'guide.md', 'test_evidence': 'evidence.json'}.items()},
        'implementation': implementation, 'tests': tests}
    path = root / 'grant.json'; dump(path, grant)
    return artifacts, path, grant, view


def test_frozen_study_end_to_end(tmp_path):
    artifacts, grant, _, _ = make_package(tmp_path)
    summary = s.run(tmp_path, grant, s.digest(grant), artifacts / 'result')
    assert set(summary['qualifying_rules']) == set(r.RULES)
    assert summary['families']['splitting']['disposition'] == 'feasible'
    assert summary['validation_evaluated'] is summary['holdout_accessed'] is summary['type_safeguard_composed'] is False


@pytest.mark.parametrize('damage', ['grant', 'source', 'view', 'test_evidence', 'holdout', 'occupied', 'concurrent'])
def test_stale_forbidden_and_occupied_inputs_rejected(tmp_path, damage):
    artifacts, grant_path, grant, view = make_package(tmp_path); expected = s.digest(grant_path); output = artifacts / 'result'
    if damage == 'grant': expected = '0' * 64
    if damage == 'source': (tmp_path / s.SOURCES[0]).write_text('changed')
    if damage == 'view': (view / 'references.jsonl').write_text('changed')
    if damage == 'test_evidence':
        p = tmp_path / 'evidence.json'; data = s.read(p); data['failed'] = 1; p.write_text(json.dumps(data))
        grant['inputs']['test_evidence']['sha256'] = s.digest(p); grant_path.write_text(json.dumps(grant)); expected = s.digest(grant_path)
    if damage == 'holdout':
        p = view / 'manifest.json'; data = s.read(p); data['capability'] = 'holdout'; p.write_text(json.dumps(data))
        grant['inputs']['training_manifest']['sha256'] = s.digest(p); grant_path.write_text(json.dumps(grant)); expected = s.digest(grant_path)
    if damage == 'occupied': output.mkdir()
    if damage == 'concurrent': (artifacts / 'road-boundary-study-active.lock').write_text('owner')
    with pytest.raises((ValueError, FileExistsError)): s.run(tmp_path, grant_path, expected, output)


def test_failure_preserves_evidence_without_changing_inputs(tmp_path, monkeypatch):
    artifacts, grant, _, view = make_package(tmp_path); before = s.digest(view / 'raw-predictions.jsonl')
    monkeypatch.setattr(s, 'score_shadow', lambda *args: (_ for _ in ()).throw(RuntimeError('constructed failure')))
    with pytest.raises(RuntimeError): s.run(tmp_path, grant, s.digest(grant), artifacts / 'failed')
    assert s.read(artifacts / 'failed/failure.json')['type'] == 'RuntimeError'
    assert s.digest(view / 'raw-predictions.jsonl') == before


def test_guarded_cli_blocks_models_transport_and_processes():
    program = """
import sys,socket,subprocess
sys.path.insert(0,'backend')
from training.flood_ner.road_boundary_study import install_guards
install_guards()
for f in (lambda:__import__('spacy'), lambda:socket.getaddrinfo('example.org',443),
          lambda:subprocess.run([sys.executable,'-c','print(1)'])):
    try:f()
    except RuntimeError:pass
    else:raise AssertionError('forbidden operation')
print('blocked')
"""
    p = subprocess.run([sys.executable, '-B', '-c', program], cwd=ROOT, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    assert p.stdout.strip() == 'blocked'
