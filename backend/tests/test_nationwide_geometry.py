"""Unit tests for NationwideGeometryService.

Verifies:
  1. Administrative hierarchy resolution across Luzon, Visayas, and Mindanao.
  2. Exact road corridor polygon (50m) and central LineString generation.
  3. Landmark 50m circular buffer polygon generation.
  4. Ambiguous city-only protection (prevents shutting down entire cities).
  5. Same-name place disambiguation using province/context clues.
  6. Closed ring GeoJSON geometric validity.
"""

from __future__ import annotations

import pytest
from app.schemas.news_extraction import ExtractedClaim
from app.services.nationwide_geometry_service import (
    NationwideGeometryService,
    buffer_osm_linestring_to_polygon,
    generate_point_buffer_polygon,
    generate_road_corridor_polygon,
    get_nationwide_geometry_service,
)


@pytest.fixture
def geometry_service() -> NationwideGeometryService:
    return get_nationwide_geometry_service()


def test_generate_point_buffer_polygon_is_valid_closed_ring():
    lat, lng = 14.5764, 121.0851
    poly = generate_point_buffer_polygon(lat, lng, radius_meters=50.0, num_points=16)

    assert poly["type"] == "Polygon"
    assert len(poly["coordinates"]) == 1
    ring = poly["coordinates"][0]
    assert len(ring) == 17  # 16 points + closed endpoint
    assert ring[0] == ring[-1]  # Closed polygon

    # Verify coordinates are in valid Philippine geographic ranges
    for pt in ring:
        assert 120.0 < pt[0] < 126.0  # Longitude
        assert 5.0 < pt[1] < 20.0     # Latitude


def test_generate_road_corridor_polygon_and_linestring():
    lat, lng = 14.5772, 121.0831
    poly, line = generate_road_corridor_polygon(lat, lng, length_meters=100.0, width_meters=40.0)

    assert poly["type"] == "Polygon"
    assert line["type"] == "LineString"
    assert len(line["coordinates"]) == 2

    ring = poly["coordinates"][0]
    assert len(ring) == 5
    assert ring[0] == ring[-1]


def test_exact_road_resolution_metro_manila(geometry_service: NationwideGeometryService):
    claim = ExtractedClaim(
        raw_place_name="C. Raymundo Ave",
        canonical_barangay="Maybunga",
        place_type="street",
        place_char_start=0,
        place_char_end=14,
        flood_mentioned=True,
        depth_canonical="knee",
        condition="active",
        evidence_sentence="Kasalukuyang lagpas-tuhod ang baha sa C. Raymundo Ave sa Pasig City.",
        evidence_sentence_offset=(0, 70),
    )

    ranked = geometry_service.rank_and_generate_geometry(claim, article_text="Baha sa Pasig")

    assert ranked.precision_level == "road"
    assert ranked.resolved_road == "C. Raymundo Ave"
    assert ranked.resolved_city == "City of Pasig"
    assert ranked.island_group == "Luzon"
    assert ranked.confidence_score >= 0.90
    assert ranked.geometry_geojson is not None
    assert ranked.geometry_geojson["type"] == "Polygon"
    assert ranked.source_geometry_geojson is not None
    assert ranked.is_auto_approvable is True
    assert ranked.requires_staff_edit is False


def test_regional_road_resolution_visayas(geometry_service: NationwideGeometryService):
    claim = ExtractedClaim(
        raw_place_name="Colon Street",
        place_type="street",
        place_char_start=0,
        place_char_end=12,
        flood_mentioned=True,
        depth_canonical="waist",
        condition="rising",
        evidence_sentence="Tumataas ang baha sa kahabaan ng Colon Street sa Cebu City.",
        evidence_sentence_offset=(0, 60),
    )

    ranked = geometry_service.rank_and_generate_geometry(claim, article_text="Floods hit Cebu City")

    assert ranked.precision_level == "road"
    assert ranked.resolved_road == "Colon Street"
    assert ranked.resolved_city == "City of Cebu"
    assert ranked.island_group == "Visayas"
    assert ranked.confidence_score >= 0.88
    assert ranked.geometry_geojson is not None
    assert ranked.is_auto_approvable is True


def test_regional_road_resolution_mindanao(geometry_service: NationwideGeometryService):
    claim = ExtractedClaim(
        raw_place_name="Roxas Avenue",
        place_type="street",
        place_char_start=0,
        place_char_end=12,
        flood_mentioned=True,
        depth_canonical="half-knee",
        condition="active",
        evidence_sentence="Abot kalahating tuhod ang baha sa kahabaan ng Roxas Avenue sa Davao City.",
        evidence_sentence_offset=(0, 75),
    )

    ranked = geometry_service.rank_and_generate_geometry(claim, article_text="Flash flood in Davao City")

    assert ranked.precision_level == "road"
    assert ranked.resolved_road == "Roxas Avenue"
    assert ranked.resolved_city == "City of Davao"
    assert ranked.island_group == "Mindanao"
    assert ranked.geometry_geojson is not None
    assert ranked.is_auto_approvable is True


def test_city_only_mention_prevents_auto_approval(geometry_service: NationwideGeometryService):
    """Broad municipal mention without a specific street must NEVER be auto-approved."""
    claim = ExtractedClaim(
        raw_place_name="Iloilo City",
        place_type="city",
        place_char_start=0,
        place_char_end=11,
        flood_mentioned=True,
        depth_canonical="knee",
        condition="active",
        evidence_sentence="Binaha ang ilang bahagi sa Iloilo City dahil sa malakas na ulan.",
        evidence_sentence_offset=(0, 65),
    )

    ranked = geometry_service.rank_and_generate_geometry(claim, article_text="Iloilo weather update")

    assert ranked.precision_level == "city"
    assert ranked.is_auto_approvable is False
    assert ranked.requires_staff_edit is True
    assert "Broad municipal mention" in ranked.score_rationale


def test_same_name_city_disambiguation_pampanga_vs_la_union(geometry_service: NationwideGeometryService):
    """San Fernando in Pampanga vs San Fernando in La Union disambiguated using context."""
    claim = ExtractedClaim(
        raw_place_name="San Fernando",
        place_type="city",
        place_char_start=0,
        place_char_end=12,
        flood_mentioned=True,
        depth_canonical=None,
        condition="active",
        evidence_sentence="Binaha ang MacArthur Highway sa San Fernando sa lalawigan ng Pampanga.",
        evidence_sentence_offset=(0, 70),
    )

    ranked = geometry_service.rank_and_generate_geometry(claim, article_text="Pampanga weather alert")

    assert ranked.resolved_city == "City of San Fernando"
    assert ranked.resolved_province == "Pampanga"


def test_buffer_osm_linestring_to_corridor_polygon():
    """Verify buffering a multi-point OpenStreetMap LineString into a closed polygon ring."""
    # Simulated OSM road way coordinates for Colon Street, Cebu City
    osm_coordinates = [
        [123.8990, 10.2970],
        [123.8998, 10.2975],
        [123.9005, 10.2980],
    ]

    buffered_poly = buffer_osm_linestring_to_polygon(osm_coordinates, radius_meters=25.0)

    assert buffered_poly["type"] == "Polygon"
    assert len(buffered_poly["coordinates"]) == 1
    ring = buffered_poly["coordinates"][0]

    # For 3 points, left side (3 pts) + right side (3 pts) + closed connection = 7 pts
    assert len(ring) == 7
    assert ring[0] == ring[-1]  # Closed polygon

    # Verify all coordinates stay within reasonable geographic limits in Cebu
    for lon, lat in ring:
        assert 123.89 < lon < 123.91
        assert 10.29 < lat < 10.30


@pytest.mark.asyncio
async def test_geocode_osm_feature_offline_anchor(geometry_service: NationwideGeometryService):
    """Verify OSM feature retrieval from cached offline anchors with corridor polygon."""
    res = await geometry_service.geocode_osm_feature("Colon Street, Cebu City")

    assert res is not None
    assert res["source"] == "offline_anchor"
    assert abs(res["lat"] - 10.2975) < 0.01
    assert abs(res["lng"] - 123.8998) < 0.01
    assert res["geometry_geojson"]["type"] == "Polygon"
    assert res["source_geometry_geojson"]["type"] == "LineString"
