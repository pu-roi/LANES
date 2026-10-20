"""Constructed-only successor checks; private study inputs are never loaded."""
from copy import deepcopy
from pathlib import Path
import sys
import ast
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner import context_association_v41 as engine
from training.flood_ner.context_cases_v41 import core_cases, result
from training.flood_ner.location_repair_cases_v40 import temporal_cases
from training.flood_ner.location_repair_scoring_v40 import temporal_result
from training.flood_ner.context_acceptance_cases import core_cases as original
from training.flood_ner.context_association_cases_v35 import core_cases as v35
from training.flood_ner.context_cases_v36 import core_cases as v36
from training.flood_ner.context_cases_v37 import core_cases as v37
from training.flood_ner.context_cases_v38 import core_cases as v38
from training.flood_ner.context_review_v37 import fixture_result
from test_flood_ner_context_association_v37 import raw_case


@pytest.mark.parametrize('case', core_cases(), ids=lambda c:c['case_id'])
def test_new_frozen_oracles(case):
    before=deepcopy(case['raw']);out=engine.extract(case['raw'])
    assert result(case,out)['passed'],result(case,out)
    assert case['raw']==before


@pytest.mark.parametrize('case', temporal_cases(), ids=lambda c:c['case_id'])
def test_all_v40_temporal_oracles(case):
    output=engine.extract(case['raw'])
    assert temporal_result(case,output)['passed'],temporal_result(case,output)


@pytest.mark.parametrize('case', original()+v35()+v36()+v37()+v38(), ids=lambda c:c['case_id'])
def test_all_238_original_oracles(case):
    raw=raw_case(case);output=engine.extract(raw)
    check=fixture_result(case,raw,output,exhaustive=case['case_id'].startswith(('fictional-v36_','fictional-v37_','fictional-v38_')))
    assert check['passed'],check


def test_no_imports_with_io_models_or_mutable_module_patching():
    tree=ast.parse(Path(engine.__file__).read_text(encoding='utf-8'))
    modules=[n.module or '' for n in ast.walk(tree)if isinstance(n,ast.ImportFrom)]
    modules += [a.name for n in ast.walk(tree)if isinstance(n,ast.Import)for a in n.names]
    assert not any(m.split('.')[0]in{'torch','spacy','socket','sqlalchemy','subprocess','httpx'}for m in modules)
    assert not any(isinstance(n,ast.Assign)and any(isinstance(t,ast.Attribute)for t in n.targets)for n in ast.walk(tree))


@pytest.mark.parametrize('field',['expected','reference','source','language','predictions'])
def test_reference_inputs_rejected(field):
    raw=deepcopy(core_cases()[0]['raw']);raw[field]={}
    with pytest.raises(ValueError):engine.extract(raw)


def test_case_matrix_and_frozen_predecessor_global_identity():
    from training.flood_ner import context_association_v38 as previous
    identity=previous.time_role
    assert len(core_cases())==len({c['case_id']for c in core_cases()})==36
    assert len({(c['family'],c['language'],c['supported'],c['variant'])for c in core_cases()})==36
    engine.extract(core_cases()[0]['raw'])
    assert previous.time_role is identity


@pytest.mark.parametrize('text',[
    'At 6 PM, flooding on Daan Piña either started or was reported.',
    'Flooding on Daan Piña either started or was reported at 6 PM.',
])
def test_conflicting_predicates_in_both_orders_remain_unspecified(text):
    from training.flood_ner.location_repair_cases_v40 import mention
    import hashlib
    raw={'record_id':'fictional-conflict','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
         'publication':None,'mentions':[mention(text,'Daan Piña','ROAD')]}
    output=engine.extract(raw)
    assert [f['temporal_role']for f in output['facts']if f['kind']=='time']==['unspecified']


def test_publication_clock_is_preserved_but_not_attached_as_an_event():
    from training.flood_ner.location_repair_cases_v40 import mention
    import hashlib
    text='The article about Daan Piña was published at 9 PM. Flooding on Daan Piña started at 6 PM.'
    raw={'record_id':'fictional-published','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
         'publication':None,'mentions':[mention(text,'Daan Piña','ROAD',i,f'n{i}')for i in(0,1)]}
    out=engine.extract(raw)
    time_facts=[f for f in out['facts']if f['kind']=='time']
    assert [f['temporal_role']for f in time_facts]==['publication','onset']
    assert time_facts[0]['id']in{x['fact_id']for x in out['unassigned']}
    assert not out['absolute_instants']


def test_joint_list_requires_complete_correctly_typed_mentions():
    raw=deepcopy(next(c['raw']for c in core_cases()if c['family']=='collective_locality'and c['supported']))
    a,b=0,len(raw['text'])
    assert engine.joint_locality(raw['text'],a,b,raw['mentions'])
    raw['mentions'][1]['label']='ROAD'
    assert not engine.joint_locality(raw['text'],a,b,raw['mentions'])
    assert not engine.joint_locality(raw['text'],a,b,raw['mentions'][:1])


def test_stale_successor_freeze_rejected_before_execution(tmp_path):
    from training.flood_ner import context_study_v41 as study
    f=tmp_path/'freeze.json';f.write_text('{}',encoding='utf-8')
    with pytest.raises(ValueError,match='stale freeze'):study.preflight(f,'0'*64)
