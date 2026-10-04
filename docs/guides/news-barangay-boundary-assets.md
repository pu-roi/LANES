# Reviewed barangay boundaries for news placement

> **Last Updated:** October 05, 2026, 2:56 AM
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

The loader is implemented; no real reviewed barangay polygons are installed by this change. A PSGC name CSV is an identity reference, not polygon coverage. Synthetic test polygons must never be installed as operational boundaries.

## Asset directory contract

Set `LANES_NEWS_BARANGAY_DIR` to a versioned directory containing `boundaries.json` and `manifest.json`. The default is `backend/runtime_data/barangay/`. Files are loaded without network requests. Restart processes after changing asset versions; do not modify an in-use immutable snapshot.

`boundaries.json` is a JSON object with these fields:

| Field | Meaning |
| --- | --- |
| `format_version` | Integer `1`. |
| `source_id`, `source_url` | Bounded source identity and original HTTPS source link. Use the reviewed polygon source, not a name-only CSV. |
| `source_sha256` | Lowercase SHA-256 of the archived source used to produce the polygons. |
| `snapshot_at`, `verified_at` | Timezone-aware source snapshot and review timestamps; review cannot predate the snapshot. |
| `verified_by`, `attribution` | Actual asset reviewer and required source attribution. These record review; they do not authenticate arbitrary uploaded polygons or confirm flooding. |
| `records` | Up to 2,000 objects with `city`, `barangay`, `psgc_code` and `geometry`. Geometry is an unsimplified WGS84 GeoJSON Polygon or MultiPolygon. Parent/name/code must match the bundled PSGC reference. |

`manifest.json` contains `{"catalog_sha256":"<lowercase SHA-256 of boundaries.json bytes>"}`. Maximum file sizes are 4,096 bytes for the manifest and 32,000,000 bytes for the catalog. All polygons must be valid, nonempty and within the NCR regional coordinate envelope. Duplicate city/barangay identities and unsupported fields are rejected. During placement, the polygon must fit the corresponding checked OSM city boundary; mismatches stay unresolved rather than being silently clipped or repaired.

## Provisioning and verification

1. Obtain permitted authoritative/reviewed administrative polygons. Retain the original archive, provenance, attribution and source date; confirm that the coordinates are EPSG:4326 and identify the correct PSGC parent for each record. This task does not select or fabricate a polygon source.
2. Export the reviewed records into the above catalog, preserving holes and disconnected polygon parts. Calculate the catalog hash only after writing its final bytes. Keep the original source hash separate.
3. Configure the same catalog version for API and extraction/evaluator processes. A missing catalog, missing barangay, corrupt checksum, identity mismatch or parent containment failure blocks barangay placement with a safe reason.
4. Check current protected placement reads against representative article locations. Confirm returned barangay source/code/hash and that every candidate remains inside the reported boundary. Check mismatches separately; successful loading is not ground-truth geometry verification.

Boundary assets require no database migration. Their checksum enters the extraction policy identity; refreshing assets produces a new result on subsequent processing rather than rewriting previous evidence. Coverage availability does not authorize automatic public zones or routing closures.
