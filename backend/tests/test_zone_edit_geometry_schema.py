"""Regression coverage for admin active-zone geometry updates."""

from app.schemas.report import FloodAvoidanceZoneUpdate


def test_zone_edit_update_accepts_a_road_centreline() -> None:
    update = FloodAvoidanceZoneUpdate.model_validate({
        "geometry": {
            "type": "LineString",
            "coordinates": [[121.08, 14.55], [121.081, 14.551]],
        },
    })

    assert update.geometry is not None
    assert update.geometry.type == "LineString"


def test_zone_edit_update_accepts_exact_polygon_vertices() -> None:
    update = FloodAvoidanceZoneUpdate.model_validate({
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[121.08, 14.55], [121.081, 14.55], [121.081, 14.551], [121.08, 14.55]]],
        },
    })

    assert update.geometry is not None
    assert update.geometry.type == "Polygon"
