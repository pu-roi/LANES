"""Validate and copy an already reviewed catalog into a NEW immutable directory.

Requires an archived original source and explicit licensing review. Does not
download, synthesize, repair, simplify, clip or approve administrative geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from app.services.barangay_boundary_service import BarangayBoundaryProvider
from app.services.news_road_placement_service import DEFAULT_CATALOG_DIR, NewsRoadPlacementProvider, city_key


def provision_catalog(catalog_directory: Path, source_archive: Path, output: Path, osm_directory: Path,
                      license_url: str, license_reviewed_by: str, *, copy_source_archive: bool = True) -> dict:
    if output.exists():
        raise ValueError("Output must be a new version directory; never replace an in-use snapshot")
    parsed = urlparse(license_url)
    if parsed.scheme != "https" or not parsed.netloc or not license_reviewed_by.strip():
        raise ValueError("Explicit HTTPS licensing source and actual reviewer are required")
    boundaries = BarangayBoundaryProvider(catalog_directory)
    if boundaries.error or boundaries.catalog is None:
        raise ValueError(boundaries.error or "invalid_barangay_boundary_catalog")
    if source_archive.stat().st_size > 128 * 1024 * 1024:
        raise ValueError("Source archive exceeds bounded provisioning limit")
    digest = hashlib.sha256(source_archive.read_bytes()).hexdigest()
    if digest != boundaries.catalog.source_sha256:
        raise ValueError("Archived polygon source checksum mismatch")
    roads = NewsRoadPlacementProvider(osm_directory, boundaries)
    roads._load()
    if roads.error or roads.catalog is None:
        raise ValueError(roads.error or "osm_catalog_unavailable")
    for _, (record, _) in boundaries.records.items():
        city = roads.boundaries.get(city_key(record.city))
        if city is None:
            raise ValueError("reported_city_not_covered")
        reason = boundaries.resolution_reason(record.city, record.barangay, city)
        if reason:
            raise ValueError(reason)
    receipt = dict(catalog_sha256=boundaries.digest, source_sha256=digest,
        source_id=boundaries.catalog.source_id, source_url=boundaries.catalog.source_url,
        license_url=license_url, license_reviewed_by=license_reviewed_by,
        osm_catalog_sha256=roads.digest, osm_source_id=roads.catalog.source_id,
        source_archive_mode="copied" if copy_source_archive else "already_archived_separately",
        source_archive_filename=source_archive.name,
        verified_record_count=len(boundaries.records), provisioned_at=datetime.now(timezone.utc).isoformat(),
        proves_current_flood=False, may_affect_routing=False)
    output.mkdir(parents=True, exist_ok=False)
    for filename in ("boundaries.json", "manifest.json"):
        shutil.copyfile(catalog_directory / filename, output / filename)
    if copy_source_archive:
        shutil.copyfile(source_archive, output / "polygon_source.archive")
    review_receipt = catalog_directory / "review_receipt.json"
    if review_receipt.exists():
        shutil.copyfile(review_receipt, output / "review_receipt.json")
    (output / "provisioning_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog_directory", type=Path)
    parser.add_argument("source_archive", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--osm-directory", type=Path, default=DEFAULT_CATALOG_DIR)
    parser.add_argument("--license-url", required=True)
    parser.add_argument("--license-reviewed-by", required=True)
    parser.add_argument("--source-already-archived", action="store_true",
        help="Validate the original local archive but retain it separately from runtime/container assets")
    args = parser.parse_args()
    print(json.dumps(provision_catalog(args.catalog_directory, args.source_archive, args.output,
        args.osm_directory, args.license_url, args.license_reviewed_by,
        copy_source_archive=not args.source_already_archived), indent=2))


if __name__ == "__main__":
    main()
