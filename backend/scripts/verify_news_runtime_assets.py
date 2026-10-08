"""Verify the deployed news spatial bundle without network or database access.

Used by the Docker build and available for read-only runtime inspection.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from app.services.barangay_boundary_service import DEFAULT_DIRECTORY as BARANGAY_DIRECTORY, BarangayBoundaryProvider
from app.services.news_placement_preview_service import NewsPlacementPreviewService
from app.services.news_road_placement_service import DEFAULT_CATALOG_DIR, NewsRoadPlacementProvider
from app.services.noah_vector_catalog_service import DEFAULT_DIRECTORY as NOAH_DIRECTORY, NoahVectorCatalog
from app.services.pasig_historical_service import DEFAULT_PASIG_CLEAN_CSV
from app.services.flood_location_service import FloodLocationProvider, DEFAULT_DIRECTORY as FLOOD_LOCATION_DIRECTORY
from app.services.cross_location_prediction_service import load_comparison


def verify_assets(noah_directory: Path, osm_directory: Path, barangay_directory: Path,
                  history_path: Path) -> dict:
    barangays = BarangayBoundaryProvider(barangay_directory)
    roads = NewsRoadPlacementProvider(osm_directory, barangays)
    noah = NoahVectorCatalog(noah_directory)
    osm_revision, noah_revision = roads.revision, noah.revision
    for error in (roads.error, barangays.error, noah.error):
        if error:
            raise ValueError(error)
    if not barangays.records:
        raise ValueError("qualified_barangay_catalog_empty")
    for (parent, _), (record, _) in barangays.records.items():
        city = roads.boundaries.get(parent)
        if city is None:
            raise ValueError("reported_city_not_covered")
        error = barangays.resolution_reason(record.city, record.barangay, city)
        if error:
            raise ValueError(error)
    preview = NewsPlacementPreviewService(roads, noah, history_path)
    if not preview.history_available:
        raise ValueError("pasig_history_source_unavailable")
    return dict(status="assets_ok", osm_revision=osm_revision, noah_catalog_sha256=noah_revision,
                barangay_catalog_sha256=barangays.digest,
                qualified_barangay_count=len(barangays.records),
                history_sha256=preview.history_digest,
                noah_tile_count=sum(len(s.tiles) for s in noah.manifest.scenarios.values()),
                proves_current_flood=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--noah-directory", type=Path,
        default=Path(os.environ.get("LANES_NEWS_NOAH_DIR", str(NOAH_DIRECTORY))))
    parser.add_argument("--osm-directory", type=Path,
        default=Path(os.environ.get("LANES_NEWS_OSM_CATALOG_DIR", str(DEFAULT_CATALOG_DIR))))
    parser.add_argument("--barangay-directory", type=Path,
        default=Path(os.environ.get("LANES_NEWS_BARANGAY_DIR", str(BARANGAY_DIRECTORY))))
    parser.add_argument("--history-path", type=Path, default=DEFAULT_PASIG_CLEAN_CSV)
    parser.add_argument("--flood-location-directory",type=Path,
        default=Path(os.environ.get("LANES_FLOOD_LOCATION_DIR",str(FLOOD_LOCATION_DIRECTORY))))
    args = parser.parse_args()
    try:
        result = verify_assets(args.noah_directory, args.osm_directory, args.barangay_directory, args.history_path)
        location = FloodLocationProvider(args.flood_location_directory)
        if location.error:
            raise ValueError(location.error)
        result.update(prediction_barangay_count=len(location.records),prediction_location_sha256=location.digest)
        candidate, evaluation, checksum = load_comparison()
        result.update(cross_location_model_sha256=checksum,
                      cross_location_shared_outcomes=evaluation["shared_outcomes"],
                      cross_location_selected_for_primary=False)
    except ValueError as error:
        print(json.dumps(dict(status="assets_invalid", reason=str(error))))
        raise SystemExit(1) from None
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
