"""Complete real source polygons and new-street detection, not synthetic coverage."""
import json
import shutil
from types import SimpleNamespace

import pytest
from geoalchemy2.shape import from_shape
from shapely.geometry import box

from app.services.flood_location_service import get_flood_location_provider, FloodLocationProvider, DEFAULT_DIRECTORY
from app.services.zone_prediction_service import resolve_location
from app.services.philippine_location_service import get_philippine_location_service
from app.services.barangay_boundary_service import get_barangay_boundary_provider


@pytest.mark.parametrize("name", sorted(get_philippine_location_service().get_pasig_barangays()))
def test_new_street_zone_is_located_in_each_of_thirty_source_barangays(name):
    provider = get_flood_location_provider()
    assert provider.error is None
    polygon = next(p for r,p in provider.records.values() if r.barangay == name)
    point = polygon.representative_point()
    extent = box(point.x-0.000001, point.y-0.000001, point.x+0.000001, point.y+0.000001)
    assert polygon.covers(extent)
    # No street/location/training-name field is supplied to the spatial resolver.
    result, reasons = resolve_location(SimpleNamespace(geometry=from_shape(extent,srid=4326)))
    assert reasons == [] and result["city"] == "Pasig" and result["barangays"] == [name]
    assert result["boundary_revision"] == provider.revision


def test_complete_location_assets_do_not_weaken_news_placement_catalog():
    provider = get_flood_location_provider()
    assert len(provider.records) == 30 and provider.city_boundary.is_valid
    assert len(get_barangay_boundary_provider().records) == 20
    manifest = json.loads((DEFAULT_DIRECTORY/"manifest.json").read_text())
    assert not manifest["geometry_modified"] and not manifest["may_affect_routing"] and not manifest["proves_current_flood"]


def test_outside_pasig_and_cross_barangay_extent_remain_explicit():
    result, reasons = resolve_location(SimpleNamespace(geometry=from_shape(box(120,13,120.01,13.01),srid=4326)))
    assert reasons and result["barangays"] == []
    provider = get_flood_location_provider()
    parts = [p for _,p in provider.records.values()]
    a = parts[0].representative_point(); b = parts[1].representative_point()
    extent = box(min(a.x,b.x)-.0001,min(a.y,b.y)-.0001,max(a.x,b.x)+.0001,max(a.y,b.y)+.0001)
    result, reasons = resolve_location(SimpleNamespace(geometry=from_shape(extent,srid=4326)))
    assert reasons and len(result["barangays"]) > 1


def test_wrong_parent_checksum_disables_catalog_instead_of_guessing(tmp_path):
    for name in ("boundaries.json","manifest.json","city.geojson"):
        shutil.copyfile(DEFAULT_DIRECTORY/name,tmp_path/name)
    (tmp_path/"city.geojson").write_text('{"geometry":null}')
    provider = FloodLocationProvider(tmp_path)
    assert provider.error and not provider.records
