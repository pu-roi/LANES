"""Regressions for observed access-negation and rainfall-role review errors."""
import pytest

from training.flood_ner.annotation.context_review import contextual_semantic_errors, reviewed_access_fact
from training.flood_ner.annotation.schema import Fact, Span


def span(text):
    return Span(start=10, end=10+len(text), text=text)


@pytest.mark.parametrize('text,value', [
    ('Not passable to light vehicles','light_vehicle_closed'),
    ('NOT PASSABLE TO LIGHT VEHICLES','light_vehicle_closed'),
    ('not passable to light vehicles','light_vehicle_closed'),
    ('Not\tpassable to light vehicles.','light_vehicle_closed'),
    ('NOT PASSABLE TO ALL TYPES OF VEHICLES (NPATV)','impassable_all'),
    ('passable to all type of vehicles','passable_all'),
    ('PASSABLE TO ALL TYPES OF VEHICLES (PATV).','passable_all'),
    ('Passable to motorcycles and cars (sedan)','passable_unspecified'),
    ('not passable','unknown'),
    ('not passable to cars','unknown'),
    ('passable to light vehicles','passable_unspecified'),
])
def test_case_and_vehicle_scope_preserve_source_meaning(text,value):
    evidence=span(text)
    fact=reviewed_access_fact('access',evidence)
    assert fact.value==value and fact.evidence==[evidence]
    assert not contextual_semantic_errors(fact)
    assert bool(fact.uncertainty)==(value=='unknown')


@pytest.mark.parametrize('text', [
    'Allison Road was passable',
    'Not passable to light vehicles; another road is passable',
    'Passable to all vehicles and not passable to cars',
    'possibly passable',
])
def test_unsupported_or_mixed_phrase_requires_review(text):
    with pytest.raises(ValueError):reviewed_access_fact('access',span(text))


def test_wrong_positive_label_is_rejected_by_semantic_guard():
    fact=reviewed_access_fact('access',span('Not passable to light vehicles'))
    fact.value='passable_unspecified'
    assert contextual_semantic_errors(fact)


def test_whole_passage_different_road_rules_are_not_a_global_negation():
    fact=Fact(id='access',kind='access',value='passable_all',evidence=[span('Main Road is not passable to light vehicles. Side Road is passable to all vehicles.')])
    assert not contextual_semantic_errors(fact)


def test_rainfall_onset_cannot_keep_a_flood_onset_role():
    fact=Fact(id='clock',kind='time',value='10 pm',entity_ids=['time'],temporal_role='onset',evidence=[span('10 pm')],qualifiers=['Rainfall onset, not flood onset.'])
    assert contextual_semantic_errors(fact)
    fact.temporal_role='unspecified'
    assert not contextual_semantic_errors(fact)
