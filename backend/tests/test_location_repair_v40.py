"""Fictional prototype checks; no private data, models or live services."""
import ast
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner.location_repair_v40 import propose, validate, METHODS, object_sha
from training.flood_ner.location_repair_cases_v40 import location_cases, temporal_cases, mention
from training.flood_ner.location_repair_scoring_v40 import location_result, temporal_result, aggregate


@pytest.mark.parametrize('case', location_cases(), ids=lambda c: c['case_id'])
@pytest.mark.parametrize('combined', [True, False])
def test_constructed_location_oracles(case, combined):
    original = deepcopy(case['raw'])
    result = propose(case['raw'], 'combined' if combined else case['family'])
    assert location_result(case, result)['passed']
    assert case['raw'] == original
    assert result['neural_mentions'] == original['mentions']
    for p in result['proposals']:
        assert p['origin'] == 'rule_proposal_not_neural'
        assert p['provenance_sha256'] == object_sha({k: v for k, v in p.items() if k != 'provenance_sha256'})
        assert original['text'][p['start']:p['end']] == p['text']


@pytest.mark.parametrize('field', ['references', 'expected', 'language', 'source_url', 'annotations', 'publication'])
def test_reference_or_identity_input_rejected(field):
    raw = deepcopy(location_cases()[0]['raw']); raw[field] = {}
    with pytest.raises(ValueError): propose(raw)


@pytest.mark.parametrize('damage', ['start', 'overlap', 'label', 'provenance', 'duplicate', 'bool_offset'])
def test_malformed_mentions_fail(damage):
    text = 'At Piña Road: flooding.'
    m = mention(text, 'Piña Road', 'LANDMARK')
    raw = {'record_id': 'fictional', 'text': text, 'mentions': [m]}
    if damage == 'start': m['start'] += 1
    if damage == 'overlap': raw['mentions'].append({**m, 'id': 'n2'})
    if damage == 'label': m['label'] = 'TIME'
    if damage == 'provenance': m['provenance_sha256'] = 'unknown'
    if damage == 'duplicate': raw['mentions'].append({**m})
    if damage == 'bool_offset': m['start'] = True
    with pytest.raises(ValueError): validate(raw)


def test_identity_does_not_control_proposals():
    raw = deepcopy(location_cases()[0]['raw']); a = propose(raw); raw['record_id'] = 'other'; b = propose(raw)
    a['record_id'] = b['record_id']; assert a == b


def test_no_cascade_or_boundary_resize():
    raw = next(c['raw'] for c in location_cases() if c['family'] == 'shared_locality' and c['supported'])
    out = propose(raw)
    assert [(m['start'], m['end']) for m in out['effective_mentions']] == [(m['start'], m['end']) for m in raw['mentions']]
    assert {m['id'] for m in out['effective_mentions']} == {m['id'] for m in raw['mentions']}


def test_empty_and_oversized_input():
    assert propose({'record_id': 'empty', 'text': '', 'mentions': []})['effective_mentions'] == []
    with pytest.raises(ValueError): propose({'record_id': 'long', 'text': 'x'*100001, 'mentions': []})


def test_exact_fixture_matrix_and_temporal_orders():
    locations = location_cases(); times = temporal_cases()
    assert len(locations) == len({c['case_id'] for c in locations}) == 36
    assert len(times) == len({c['case_id'] for c in times}) == 36
    assert {c['role'] for c in times} == {'onset', 'observation', 'report', 'recession', 'clearance', 'unspecified'}
    assert {c['language'] for c in locations} == {c['language'] for c in times} == {'english', 'tagalog', 'taglish'}
    assert sum(c['time_before'] for c in times) == 18
    assert all(c['publication']['value'] if 'publication' in c else c['raw']['publication']['value'] for c in times)


def test_time_oracle_exposes_wrong_roles_instead_of_accepting_them():
    case = next(c for c in temporal_cases() if c['role'] == 'observation')
    out = {'expressions': [{'id': 't', 'text': case['clock']}],
           'facts': [{'kind': 'time', 'entity_ids': ['t'], 'temporal_role': 'onset'}],
           'absolute_instants': [], 'numeric_depths': []}
    result = temporal_result(case, out)
    assert result['onset_invented'] and not result['passed']


def test_missing_outputs_cannot_qualify():
    with pytest.raises(ValueError): aggregate([], [], [], [], [])


def test_prototype_is_pure_and_does_not_import_rejected_safeguards():
    from training.flood_ner import location_repair_v40 as module
    tree = ast.parse(Path(module.__file__).read_text(encoding='utf-8'))
    names = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    names |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert names <= {'__future__', 'copy', 'hashlib', 'json', 're', 'typing'}


def test_conflicting_proposals_abstain(monkeypatch):
    from training.flood_ner import location_repair_v40 as module
    pattern = module.ASSET
    class Twice:
        def finditer(self, text):
            hits = list(pattern.finditer(text)); return iter(hits+hits)
    monkeypatch.setattr(module, 'ASSET', Twice())
    raw = next(c['raw'] for c in location_cases() if c['family'] == 'transport_asset' and c['supported'])
    result = propose(raw)
    assert not result['proposals'] and not result['effective_mentions']
    assert any('conflicting' in a['reason'] for a in result['abstentions'])


def test_proposed_id_collision_fails():
    raw = deepcopy(next(c['raw'] for c in location_cases() if c['family'] == 'transport_asset' and c['supported']))
    identity = propose(raw)['effective_mentions'][0]['id']
    raw['text'] += ' Near Zinnia Road: flooding.'
    raw['mentions'] = [mention(raw['text'], 'Zinnia Road', 'ROAD', identity=identity)]
    with pytest.raises(ValueError, match='collision'): propose(raw)


def test_occupied_destination_is_rejected(tmp_path, monkeypatch):
    from training.flood_ner import location_repair_study_v40 as study
    monkeypatch.setattr(study, 'ART', tmp_path)
    destination = tmp_path/'occupied'; destination.mkdir()
    with pytest.raises(ValueError): study.fresh(destination)
    with pytest.raises(ValueError): study.fresh(tmp_path/'nested'/'output')


def test_single_writer_lock_and_failure_preservation(tmp_path):
    from training.flood_ner import linux_runtime_v29 as runtime
    lock = tmp_path/'active.lock'; partial = tmp_path/'partial.json'
    with pytest.raises(RuntimeError, match='fictional failure'):
        with runtime.exclusive(lock, {'owner': 'fictional'}):
            partial.write_text('preserved', encoding='utf-8')
            with pytest.raises(FileExistsError):
                with runtime.exclusive(lock, {'owner': 'other'}): pass
            raise RuntimeError('fictional failure')
    assert partial.read_text(encoding='utf-8') == 'preserved'


def test_stale_freeze_rejected_before_any_execution(tmp_path):
    from training.flood_ner import location_repair_study_v40 as study
    freeze = tmp_path/'freeze.json'; freeze.write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError, match='stale freeze'): study.preflight(freeze, '0'*64)


def test_new_false_positive_blocks_even_when_counts_improve():
    from training.flood_ner.location_repair_scoring_v40 import recognition
    text = 'Aster Road Zinnia Road'
    a = mention(text, 'Aster Road', 'ROAD')
    z = mention(text, 'Zinnia Road', 'ROAD', identity='n1')
    row = recognition([(a['start'], a['end'], 'ROAD')], [], [a, z])
    assert row['gained_correct'] and row['introduced_fp']
