import json
from types import SimpleNamespace

from geoalchemy2.shape import from_shape
import pytest
from shapely.geometry import MultiPolygon, Point, Polygon, box, mapping

from app.models.report import ReportSeverity
from app.services.flood_heatmap_service import historical_heatmap_features, severity_weight
from app.schemas.flood_event import HistoricalFloodZoneResponse


@pytest.mark.parametrize("severity, expected", [("low", 1), ("medium", 2), ("high", 3), ("extreme", 5), (ReportSeverity.HIGH, 3), (None, 2)])
def test_public_and_history_weights_match(severity, expected):
    assert severity_weight(severity) == expected


@pytest.mark.parametrize("geometry", [
    box(121, 14, 121.02, 14.02),
    Polygon([(121,14),(121.1,14),(121.1,14.1),(121,14.1)], holes=[[(121.02,14.02),(121.08,14.02),(121.08,14.08),(121.02,14.08)]]),
    MultiPolygon([box(121,14,121.01,14.01), box(121.03,14,121.05,14.02)]),
])
def test_one_point_per_zone_stays_on_saved_footprint_without_writes(geometry):
    zones = [SimpleNamespace(id=3, geometry=from_shape(geometry, srid=4326)),
             SimpleNamespace(id=4, geometry=json.dumps(mapping(geometry)))]
    original = repr(zones)
    features = historical_heatmap_features(7, "extreme", zones)
    assert len(features) == 2
    for feature, zone in zip(features, zones):
        assert geometry.covers(Point(feature.geometry.coordinates))
        assert feature.model_dump(mode="json")["properties"] == {"event_id": 7, "zone_id": zone.id, "weight": 5}
    assert repr(zones) == original


@pytest.mark.parametrize("raw", [None, "bad-json", {}, mapping(Point(121,14)),
    mapping(Polygon()), mapping(Polygon([(121,14),(121.1,14.1),(121.1,14),(121,14.1),(121,14)])),
    mapping(box(200,14,201,15))])
def test_missing_invalid_or_nonpolygon_footprints_are_not_invented(raw):
    assert historical_heatmap_features(7, "low", [SimpleNamespace(id=3, geometry=raw)]) == []


@pytest.mark.parametrize("geometry, expected", [(box(121,14,121.01,14.01), "Polygon"),
    (MultiPolygon([box(121,14,121.01,14.01),box(121.02,14,121.03,14.01)]), "MultiPolygon"),
    (Polygon([(121,14),(121.1,14.1),(121.1,14),(121,14.1),(121,14)]), None), (None,None)])
def test_history_zone_contract_retains_unmapped_and_multipart_records(geometry, expected):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    result = HistoricalFloodZoneResponse.model_validate({"id": 3, "geometry": from_shape(geometry,srid=4326) if geometry else None,
        "severity": "high", "is_active": False, "created_at": now, "updated_at": now})
    assert (result.geometry.type if result.geometry else None) == expected
    assert result.id == 3 and result.is_active is False
