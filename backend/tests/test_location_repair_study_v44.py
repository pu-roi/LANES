import json
from pathlib import Path
import pytest

from training.flood_ner import location_repair_study_v44 as study
from training.flood_ner.location_repair_cases_v44 import location_cases
from training.flood_ner.location_repair_scoring_v44 import fact_key, freeze_key


def test_complete_balanced_fictional_workload():
    cases = location_cases()
    assert len(cases) == len({c['case_id'] for c in cases}) == 36
    for family in ('missing_junction', 'boundary_replacement', 'junction_type'):
        for language in ('english', 'tagalog', 'taglish'):
            subset = [c for c in cases if c['family'] == family and c['language'] == language]
            assert {(c['supported'], c['variant']) for c in subset} == {(True, 0), (True, 1), (False, 0), (False, 1)}


def test_stale_binding_rejected_before_preservation(tmp_path, monkeypatch):
    monkeypatch.setattr(study, 'ROOT', tmp_path)
    monkeypatch.setattr(study, 'preserved', lambda: pytest.fail('must reject stale binding first'))
    (tmp_path/'input.json').write_text('changed')
    study.write(tmp_path/'freeze.json', {'schema': 'lanes-location-freeze-v44', 'image': study.IMAGE, 'attempts': 1,
                'implementation': {}, 'inputs': [{'path': 'input.json', 'sha256': 'a'*64}], 'package_files': {}})
    with pytest.raises(AssertionError): study.check(tmp_path)


def test_first_failure_preserved_and_repeat_claim_rejected(tmp_path, monkeypatch):
    package = tmp_path/'package'; package.mkdir()
    study.write(package/'freeze.json', {'attempts': 1}); study.write(package/'request.json', {})
    monkeypatch.setattr(study, 'ART', tmp_path); monkeypatch.setattr(study, 'check', lambda _: {})
    calls = []
    def fail(args, receipt, timeout=30):
        calls.append(args); study.write(receipt, {'returncode': 1}); return {'returncode': 1}
    monkeypatch.setattr(study, 'command', fail)
    output = tmp_path/'attempt'
    with pytest.raises(AssertionError): study.execute(package, output, 'docker')
    assert json.loads((output/'failure.json').read_text())['retry_allowed'] is False
    assert len(calls) == 1 and (output/'image.json').exists()
    with pytest.raises(FileExistsError): study.execute(package, tmp_path/'second-attempt', 'docker')
    assert len(calls) == 1 and not (tmp_path/'second-attempt').exists()


def test_occupied_destination_is_never_modified(tmp_path, monkeypatch):
    monkeypatch.setattr(study, 'check', lambda _: {})
    output = tmp_path/'occupied'; output.mkdir(); marker = output/'keep'; marker.write_text('keep')
    with pytest.raises(AssertionError): study.execute(tmp_path, output, 'docker')
    assert marker.read_text() == 'keep'


def test_fact_identity_does_not_mix_repeated_row_evidence():
    graph = {'expressions': [{'id': 'x0', 'start': 1, 'end': 5, 'label': 'TIME'}]}
    f = {'kind': 'time', 'value': '6 PM', 'temporal_role': 'observation', 'depth_scope': None,
         'entity_ids': ['x0'], 'evidence': [{'start': 1, 'end': 30}]}
    g = {**f, 'evidence': [{'start': 1, 'end': 60}]}
    assert fact_key(f, graph) != fact_key(g, graph)
    assert freeze_key([['one'], ['two']]) == (('one',), ('two',))


def test_worker_mounts_exclude_references_expectations_and_models():
    assert all(not any(t in p.lower() for t in ('artifacts', 'fixtures', 'scoring', 'cases_', 'model-best', 'credentials'))
               for p in study.WORKER.values())
    assert len(study.CODE) == len(set(study.CODE))
