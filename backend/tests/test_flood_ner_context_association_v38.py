"""Constructed-only scope checks; no private evidence or corpus examples."""
from copy import deepcopy
import ast
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner import context_association_v38 as engine
from training.flood_ner import context_review_v37 as review
from training.flood_ner.context_acceptance_cases import core_cases as original
from training.flood_ner.context_association_cases_v35 import core_cases as v35
from training.flood_ner.context_cases_v36 import core_cases as v36
from training.flood_ner.context_cases_v37 import core_cases as v37
from training.flood_ner.context_cases_v38 import core_cases
from test_flood_ner_context_association_v37 import raw_case


@pytest.mark.parametrize('case', original()+v35()+v36()+v37()+core_cases(), ids=lambda c:c['case_id'])
def test_frozen_behavior(case):
    raw=raw_case(case);before=deepcopy(raw);out=engine.extract(raw)
    result=review.fixture_result(case,raw,out,exhaustive=case['case_id'].startswith(
        ('fictional-v36_', 'fictional-v37_', 'fictional-v38_')))
    assert result['passed'], result
    assert raw==before and out==engine.extract(raw) and out['mentions']==raw['mentions']


@pytest.mark.parametrize('field', ['reference','expected','annotations','predictions','language'])
def test_extraction_rejects_unauthorized_fields(field):
    raw=raw_case(core_cases()[0]);raw[field]={}
    with pytest.raises(ValueError):engine.extract(raw)


def test_opaque_identity_does_not_select_behavior():
    raw=raw_case(core_cases()[0]);a=engine.extract(raw);raw['record_id']='opaque-other'
    b=engine.extract(raw);a['record_id']=b['record_id'];assert a==b


def test_no_io_model_training_or_reference_imports():
    tree=ast.parse(Path(engine.__file__).read_text(encoding='utf-8'))
    imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
    assert not any(n.split('.')[0] in {'socket','httpx','requests','sqlalchemy','spacy','torch','thinc','subprocess'} for n in imports)
    assert not any('scoring' in n or 'cases' in n or 'review' in n for n in imports)


@pytest.mark.parametrize('damage', ['hash','offset','overlap','label'])
def test_malformed_source_or_mentions(damage):
    raw=raw_case(core_cases()[0])
    if damage=='hash':raw['text_sha256']='0'*64
    if damage=='offset':raw['mentions'][0]['start']+=1
    if damage=='overlap':raw['mentions'].append({**raw['mentions'][0],'id':'another'})
    if damage=='label':raw['mentions'][0]['label']='TIME'
    with pytest.raises(ValueError):engine.extract(raw)


def test_three_language_five_family_matrix_is_exact():
    cases=core_cases()
    assert len(cases)==len({c['case_id'] for c in cases})==30
    assert {c['language'] for c in cases}=={'english','tagalog','taglish'}
    assert len({c['family'] for c in cases})==5
