"""Constructed v42 checks; never reads private article inputs or runs a model."""
from copy import deepcopy
import pytest

from app.services.news_ner.context_association_v42 import extract
from training.flood_ner.context_cases_v42 import core_cases,result
from training.flood_ner.context_cases_v41 import core_cases as v41_cases,result as v41_result
from training.flood_ner.location_repair_cases_v40 import temporal_cases
from training.flood_ner.location_repair_scoring_v40 import temporal_result
from training.flood_ner.context_acceptance_cases import core_cases as original
from training.flood_ner.context_association_cases_v35 import core_cases as v35
from training.flood_ner.context_cases_v36 import core_cases as v36
from training.flood_ner.context_cases_v37 import core_cases as v37
from training.flood_ner.context_cases_v38 import core_cases as v38
from training.flood_ner.context_review_v37 import fixture_result
from test_flood_ner_context_association_v37 import raw_case


@pytest.mark.parametrize('case',core_cases(),ids=lambda c:c['case_id'])
def test_v42_fictional(case):
    before=deepcopy(case['raw']);graph=extract(case['raw'])
    check=result(case,graph)
    assert check['passed'],check
    assert case['raw']==before


@pytest.mark.parametrize('case',v41_cases(),ids=lambda c:c['case_id'])
def test_v41_oracles_unchanged(case):
    check=v41_result(case,extract(case['raw']))
    assert check['passed'],check


@pytest.mark.parametrize('case',temporal_cases(),ids=lambda c:c['case_id'])
def test_v40_temporal_oracles_unchanged(case):
    check=temporal_result(case,extract(case['raw']))
    assert check['passed'],check


@pytest.mark.parametrize('case',original()+v35()+v36()+v37()+v38(),ids=lambda c:c['case_id'])
def test_238_oracles_unchanged(case):
    raw=raw_case(case)
    check=fixture_result(case,raw,extract(raw),exhaustive=case['case_id'].startswith(('fictional-v36_','fictional-v37_','fictional-v38_')))
    assert check['passed'],check


def test_fixture_matrix():
    cases=core_cases()
    assert len(cases)==len({(c['family'],c['language'],c['supported'])for c in cases})==36


@pytest.mark.parametrize('clock',['4:30 p.m','4:30 p.m.','4:30 PM','6:31 a.m','6:31 a.m.','6:31 AM'])
def test_clock_source_slices_and_roles(clock):
    import hashlib
    from training.flood_ner.location_repair_cases_v40 import mention
    text=f'At {clock}, flooding started on Daan Piña.'
    raw={'record_id':'fictional-clock-v42','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
         'publication':None,'mentions':[mention(text,'Daan Piña','ROAD')]}
    graph=extract(raw)
    assert [(f['value'],f['temporal_role'])for f in graph['facts']if f['kind']=='time']==[(clock,'onset')]
    assert all(text[e['start']:e['end']]==e['text']for e in graph['expressions'])


@pytest.mark.parametrize('depth',['8 to 12 inches','up to 20 cm','about 20 cm'])
def test_junction_ranges_and_qualifiers(depth):
    import hashlib
    from training.flood_ner.location_repair_cases_v40 import mention
    text=f'🌧 Daan Piña cor Daan Áster - {depth}'
    raw={'record_id':'fictional-range-v42','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
         'publication':None,'mentions':[mention(text,'Daan Piña','ROAD'),mention(text,'Daan Áster','ROAD',identity='n1')]}
    graph=extract(raw)
    fact=next(f for f in graph['facts']if f['kind']=='depth')
    assert fact['value']==depth
    relation=next(r for r in graph['relations']if r['fact_id']==fact['id'])
    assert relation['scope']=='collective'and relation['target_entity_ids']==['n0','n1']


def test_replacement_list_clock_and_report_clock_are_distinct():
    import hashlib
    from training.flood_ner.location_repair_cases_v40 import mention
    text=('As of 4:30 p.m, the following roads are flooded:\nDaan Piña - 8 inches, gutter deep\n'
          'As of 6 PM, the following roads are flooded:\nDaan Áster - 19 inches, knee-deep\n'
          'Report issued at 8 PM: the following roads are flooded:\nDaan Luntian - 10 inches, gutter deep')
    raw={'record_id':'fictional-update-v42','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
         'publication':None,'mentions':[mention(text,n,'ROAD',identity=f'n{i}')for i,n in enumerate(('Daan Piña','Daan Áster','Daan Luntian'))]}
    graph=extract(raw);facts={f['id']:f for f in graph['facts']}
    linked=[(facts[r['fact_id']]['value'],r['target_entity_ids'])for r in graph['relations']if facts[r['fact_id']]['kind']=='time']
    assert linked==[('4:30 p.m',['n0']),('6 PM',['n1'])]


def test_conflicting_junction_measurements_do_not_zip_to_roads():
    import hashlib
    from training.flood_ner.location_repair_cases_v40 import mention
    text='Daan Piña cor Daan Áster - 8 inches, 37 inches'
    raw={'record_id':'fictional-conflict-v42','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
         'publication':None,'mentions':[mention(text,'Daan Piña','ROAD'),mention(text,'Daan Áster','ROAD',identity='n1')]}
    graph=extract(raw)
    ids={f['id']for f in graph['facts']if f['kind']=='depth'}
    assert len(ids)==2 and not any(r['fact_id']in ids for r in graph['relations'])


def test_administrative_alias_and_unmeasured_junction_do_not_drop_list_scope():
    import hashlib
    from training.flood_ner.location_repair_cases_v40 import mention
    text=('As of 4:30 p.m, the following roads are flooded:\nPassable with caution\n'
          'Barangay Luntian (Maliwanag)\nDaan Piña cor Daan Áster (Southbound)\n'
          'Daan Bughaw - 8 inches, gutter deep')
    names=[('Barangay Luntian','BARANGAY'),('Daan Piña','ROAD'),('Daan Áster','ROAD'),('Daan Bughaw','ROAD')]
    raw={'record_id':'fictional-alias-v42','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
         'publication':None,'mentions':[mention(text,n,label,identity=f'n{i}')for i,(n,label)in enumerate(names)]}
    graph=extract(raw);facts={f['id']:f for f in graph['facts']}
    times=[(facts[r['fact_id']]['value'],r['target_entity_ids'])for r in graph['relations']if facts[r['fact_id']]['kind']=='time']
    assert times==[('4:30 p.m',['n1','n2']),('4:30 p.m',['n3'])]
    assert not any('n0'in r['target_entity_ids']for r in graph['relations'])
    assert len([f for f in graph['facts']if f['kind']=='depth'])==2


def test_light_vehicle_heading_uses_existing_contract_value():
    import hashlib
    from training.flood_ner.location_repair_cases_v40 import mention
    text='The following roads are flooded:\nImpassable to light vehicles\nDaan Piña - 8 inches, gutter deep'
    raw={'record_id':'fictional-light-v42','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
         'publication':None,'mentions':[mention(text,'Daan Piña','ROAD')]}
    graph=extract(raw);facts={f['id']:f for f in graph['facts']}
    access=[facts[r['fact_id']]for r in graph['relations']if facts[r['fact_id']]['kind']=='access']
    assert len(access)==1 and access[0]['value']=='light_vehicle_closed'
    assert access[0]['qualifiers']==['Impassable to light vehicles']
