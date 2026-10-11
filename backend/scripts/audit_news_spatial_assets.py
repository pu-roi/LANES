"""Read-only audit of installed OSM and reviewed barangay placement assets.

Run from backend: python -m scripts.audit_news_spatial_assets --city Pasig --road C5
No network, database, activation, or inferred affected-width operations occur.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from shapely.geometry import LineString

from app.schemas.news_extraction import ExtractedClaim
from app.services.barangay_boundary_service import DEFAULT_DIRECTORY, BarangayBoundaryProvider
from app.services.news_road_placement_service import DEFAULT_CATALOG_DIR, NewsRoadPlacementProvider, city_key
from app.services.article_road_match_service import _way_matches, normalize_name


def audit_assets(roads: NewsRoadPlacementProvider, city: str, road: str, barangay: str | None = None) -> dict:
    evidence = "Asset coverage inspection; no flood observation."
    claim = ExtractedClaim(raw_place_name=road, canonical_road=road, canonical_city=city,
        canonical_barangay=barangay, place_type="street", place_char_start=0, place_char_end=len(road),
        evidence_sentence=evidence, evidence_sentence_offset=(0, len(evidence)))
    placement = roads.resolve(claim)
    boundary = roads.boundaries.get(city_key(city))
    matching = [way for way in roads.ways if _way_matches(way, road)]
    inside = [way.osm_id for way in matching if boundary is not None and
        LineString([(lon, lat) for _, lon, lat in way.nodes]).intersection(boundary).length > 0]
    boundary_checks = []
    for (parent, name), (record, _) in sorted(roads.barangays.records.items()):
        parent_boundary = roads.boundaries.get(parent)
        reason = "reported_city_not_covered" if parent_boundary is None else roads.barangays.resolution_reason(
            record.city, record.barangay, parent_boundary)
        boundary_checks.append(dict(city=record.city, barangay=name, psgc_code=record.psgc_code,
            status="available" if reason is None else "unavailable", reason=reason))
    return dict(osm_revision=roads.revision, osm_error=roads.error, barangay_error=roads.barangays.error,
        catalog_source_id=roads.catalog.source_id if roads.catalog else None,
        catalog_snapshot_at=roads.catalog.snapshot_at.isoformat() if roads.catalog else None,
        route_reference_relations=sorted({route.relation_id for way in (roads.catalog.ways if roads.catalog else [])
            if way.osm_id in inside for route in way.route_references
            if normalize_name(road).removesuffix(" road") == normalize_name(route.reference)}),
        road_name_matches=len(matching), ways_with_positive_length_in_city=len(inside), city_way_ids=inside,
        reviewed_boundary_checks=boundary_checks, placement=placement.model_dump(mode="json"),
        operational_flood_geometry_ready=False,
        operational_reason="mapped_centerlines_do_not_establish_observed_flooded_width_or_affected_footprint")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--osm-directory", type=Path,
        default=Path(os.environ.get("LANES_NEWS_OSM_CATALOG_DIR", str(DEFAULT_CATALOG_DIR))))
    parser.add_argument("--barangay-directory", type=Path,
        default=Path(os.environ.get("LANES_NEWS_BARANGAY_DIR", str(DEFAULT_DIRECTORY))))
    parser.add_argument("--city", required=True)
    parser.add_argument("--road", required=True)
    parser.add_argument("--barangay")
    args = parser.parse_args()
    roads = NewsRoadPlacementProvider(args.osm_directory, BarangayBoundaryProvider(args.barangay_directory))
    print(json.dumps(audit_assets(roads, args.city, args.road, args.barangay), indent=2))


if __name__ == "__main__":
    main()
