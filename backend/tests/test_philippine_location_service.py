"""Unit tests for PhilippineLocationService and nationwide administrative resolution."""

from __future__ import annotations

import pytest
from app.services.philippine_location_service import (
    PhilippineLocationService,
    get_philippine_location_service,
)


@pytest.fixture
def location_service() -> PhilippineLocationService:
    return get_philippine_location_service()


def test_location_service_loads_pasig_barangays(location_service: PhilippineLocationService):
    pasig_bgys = location_service.get_pasig_barangays()
    assert len(pasig_bgys) == 30
    assert "Maybunga" in pasig_bgys
    assert "Pinagbuhatan" in pasig_bgys
    assert "Kapitolyo" in pasig_bgys
    assert "Rosario" in pasig_bgys
    assert "Santa Cruz" in pasig_bgys


def test_barangay_normalization_with_aliases(location_service: PhilippineLocationService):
    assert location_service.normalize_barangay_name("Maybunga") == "Maybunga"
    assert location_service.normalize_barangay_name("Barangay Maybunga") == "Maybunga"
    assert location_service.normalize_barangay_name("Brgy. Sta. Lucia") == "Santa Lucia"
    assert location_service.normalize_barangay_name("Sta. Rosa") == "Santa Rosa"
    assert location_service.normalize_barangay_name("Sto. Tomas") == "Santo Tomas"
    assert location_service.normalize_barangay_name("Maybunnga") == "Maybunga"
    assert location_service.normalize_barangay_name("Brgy. Palatiw") == "Palatiw"
    assert location_service.normalize_barangay_name("pala") is None
    assert location_service.normalize_barangay_name("ImaginaryBarangayXYZ") is None


def test_province_resolution(location_service: PhilippineLocationService):
    res_bulacan = location_service.resolve_location_hierarchy("Bulacan")
    assert res_bulacan is not None
    assert res_bulacan["matched_name"] == "Bulacan"
    assert res_bulacan["level"] == "Prov"
    assert res_bulacan["province"] == "Bulacan"

    res_pampanga = location_service.resolve_location_hierarchy("Pampanga")
    assert res_pampanga is not None
    assert res_pampanga["matched_name"] == "Pampanga"
    assert res_pampanga["level"] == "Prov"

    res_cebu = location_service.resolve_location_hierarchy("Cebu")
    assert res_cebu is not None
    assert res_cebu["province"] == "Cebu"


def test_city_resolution_and_aliases(location_service: PhilippineLocationService):
    res_malolos = location_service.resolve_location_hierarchy("Malolos", "Flooding in Malolos, Bulacan")
    assert res_malolos is not None
    assert res_malolos["matched_name"] == "City of Malolos"
    assert res_malolos["province"] == "Bulacan"
    assert res_malolos["level"] == "City"

    res_cebu_city = location_service.resolve_location_hierarchy("Cebu City", "Floodwaters in Cebu City")
    assert res_cebu_city is not None
    assert res_cebu_city["matched_name"] == "City of Cebu"
    assert res_cebu_city["province"] == "Cebu"

    res_davao = location_service.resolve_location_hierarchy("Davao City", "Rescue ops in Davao City")
    assert res_davao is not None
    assert res_davao["matched_name"] == "City of Davao"


def test_disambiguation_with_context(location_service: PhilippineLocationService):
    # San Fernando exists in Pampanga and La Union
    res_pampanga = location_service.resolve_location_hierarchy(
        "San Fernando", "Baha sa City of San Fernando sa probinsya ng Pampanga"
    )
    assert res_pampanga is not None
    assert res_pampanga["province"] == "Pampanga"

    res_la_union = location_service.resolve_location_hierarchy(
        "San Fernando", "Baha sa San Fernando, La Union kaninang umaga"
    )
    assert res_la_union is not None
    assert res_la_union["province"] == "La Union"


def test_nonexistent_location_returns_none(location_service: PhilippineLocationService):
    assert location_service.resolve_location_hierarchy("Gotham City") is None
    assert location_service.resolve_location_hierarchy("Atlantis") is None
