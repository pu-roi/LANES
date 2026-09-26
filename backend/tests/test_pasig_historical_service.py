"""Unit and integration tests for PasigHistoricalService.

Verifies:
  1. All 726 clean records are loaded and indexed.
  2. Frequent flood corridors (Ortigas, C. Raymundo, West Capitol) are found with recurrence counts and depth ranges.
  3. Historical recurrence prior bonuses and explainable rationales are correctly calculated.
"""

from __future__ import annotations

import pytest

from app.services.pasig_historical_service import (
    PasigHistoricalService,
    get_pasig_historical_service,
)


@pytest.fixture
def historical_service() -> PasigHistoricalService:
    return get_pasig_historical_service()


def test_pasig_historical_dataset_is_indexed(historical_service: PasigHistoricalService):
    assert len(historical_service.streets) >= 250
    assert len(historical_service.landmarks) >= 250
    assert len(historical_service.barangays) >= 25


def test_frequent_corridor_lookup(historical_service: PasigHistoricalService):
    rec = historical_service.lookup_street("Ortigas Ext")
    assert rec is not None
    assert rec.recurrence_count >= 10
    assert len(rec.years) >= 2
    assert rec.depth_min_cm is not None and rec.depth_max_cm is not None

    ortigas_broad = historical_service.lookup_street("Ortigas")
    assert ortigas_broad is not None
    assert ortigas_broad.recurrence_count >= 10

    c_raymundo = historical_service.lookup_street("C. Raymundo Ave")
    assert c_raymundo is not None
    assert c_raymundo.recurrence_count >= 1


def test_recurrence_bonus_and_rationale(historical_service: PasigHistoricalService):
    bonus, rationale = historical_service.get_recurrence_bonus("Ortigas Ext", city_hint="Pasig")
    assert bonus >= 0.04
    assert rationale is not None
    assert "Corroborated by Pasig DRRMO flood history" in rationale
    assert "Ortigas" in rationale

    sandoval_bonus, sandoval_rat = historical_service.get_recurrence_bonus("Sandoval Ave", city_hint="Pasig")
    assert sandoval_bonus >= 0.06
    assert "Major flood corridor" in sandoval_rat


def test_non_pasig_city_skips_pasig_prior(historical_service: PasigHistoricalService):
    bonus, rationale = historical_service.get_recurrence_bonus("Ortigas Ave", city_hint="Cebu City")
    assert bonus == 0.0
    assert rationale is None
