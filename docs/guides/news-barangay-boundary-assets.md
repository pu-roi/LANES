# Reviewed barangay boundaries for news placement

> **Last Updated:** October 05, 2026, 6:04 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

The loader now has a bundled **OSM community** preview catalog for twenty of Pasig's thirty barangays, including Ugong. Automated asset checks establish exact PSGC identity, complete valid source rings and same-snapshot city containment; they do not establish official/legal/human/field verification or observed flood extent. A PSGC name CSV alone is not polygon coverage. Synthetic test polygons must never be installed as runtime boundaries. See the [catalog source/review record](../../backend/runtime_data/barangay/README.md).

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
| `source_classification`, `review_method` | Source class is `reviewed_source` (backward-compatible default) or `osm_community`. Community sources require an explicit actual review method; this records automated asset validation separately from official/legal/field review. |
| `records` | Up to 2,000 objects with `city`, `barangay`, `psgc_code` and `geometry`. Geometry is an unsimplified WGS84 GeoJSON Polygon or MultiPolygon. Parent/name/code must match the bundled PSGC reference. Community records require `osm_relation_id` and its exact HTTPS OSM relation `source_url`. |

`manifest.json` contains `{"catalog_sha256":"<lowercase SHA-256 of boundaries.json bytes>"}`. Maximum file sizes are 4,096 bytes for the manifest and 32,000,000 bytes for the catalog. All polygons must be valid, nonempty and within the NCR regional coordinate envelope. Duplicate city/barangay identities and unsupported fields are rejected. During placement, the polygon must fit the corresponding checked OSM city boundary; mismatches stay unresolved rather than being silently clipped or repaired.

## Provisioning and verification

1. Obtain permitted authoritative/reviewed administrative polygons. Retain the original archive, provenance, attribution and source date; confirm that the coordinates are EPSG:4326 and identify the correct PSGC parent for each record. This task does not select or fabricate a polygon source.
2. Export the reviewed records into the above catalog, preserving holes and disconnected polygon parts. Calculate the catalog hash only after writing its final bytes. Keep the original source hash separate.
3. Configure the same catalog version for API and extraction/evaluator processes. A missing catalog, missing barangay, corrupt checksum, identity mismatch or parent containment failure blocks barangay placement with a safe reason.
4. Check current protected placement reads against representative article locations. Confirm returned barangay source/code/hash and that every candidate remains inside the reported boundary. Check mismatches separately; successful loading is not ground-truth geometry verification.

Boundary assets require no database migration. Their checksum enters the extraction policy identity; refreshing assets produces a new result on subsequent processing rather than rewriting previous evidence. Coverage availability does not authorize automatic public zones or routing closures.

## Current partial community coverage

The installed catalog comes from the separately archived Metro Manila PBF, snapshot `2026-09-27T00:56:56Z`, with original relation IDs and ODbL attribution. Catalog SHA-256 is `4b596be585945502fffd1ca9e14f282fb5a10e3b844c3ca2b21eda1a157894c2`; Ugong relation `108731` matches current PSGC `1381200029`. Reviewer metadata explicitly records **Codex geometry agent (automated asset validation)**. The original PBF is retained in ignored `data/` and is not duplicated into the small runtime assets. Review/provisioning receipts retain source, PSGC and road-catalog hashes and every exclusion.

Omitted coverage: Bambang, Kalawaan, Malinao, Palatiw, Pinagbuhatan, San Joaquin, San Miguel, San Nicolas, Santa Cruz and Santo Tomas. Three candidates have unclosed source linework; San Miguel lacks an explicit PSGC reference; other names lack accepted matching relations. Missing areas retain named coverage failures. No source rings are repaired, simplified, snapped or substituted.

The constructed C5/Ugong/Pasig probe produces thirteen clipped candidates and 250 modeled NOAH fragments, eleven disconnected preview geometries and zero linework outside Ugong. It remains a predicted candidate without current-flood/operational-width/routing confirmation.

To build a new reviewed community version from the archived same-snapshot PBF, run `python -m scripts.build_news_barangay_catalog <source-pbf> <new-review-directory>` from `backend/`; the builder refuses replacement. Review its exclusions, source/license metadata and identity before provisioning.

## October 5 rejected alternatives and provisioning follow-up

The [GeoRisk PSA barangay service](https://ulap-nga.georisk.gov.ph/arcgis/rest/services/PSA/Barangay_2020/MapServer/0) returned token-required access (499). The public [Pasig barangay atlas](https://services1.arcgis.com/GMAJGrCZkLEPNMcz/ArcGIS/rest/services/PasigBarangay/FeatureServer/1) references old 1986/2000 coverage: 24 of 30 polygons, no Ugong, 13 of 24 incompatible with strict checked OSM parent containment and unclear redistribution terms. Neither source was installed. Do not silently clip/repair an incompatible parent or represent missing polygons as coverage.

`BarangayBoundaryProvider.resolution_reason` distinguishes missing/invalid coverage from `barangay_boundary_parent_mismatch`. Offline `scripts.provision_news_barangay_catalog` validates an already reviewed catalog, archived source SHA, explicit HTTPS license/reviewer and every parent boundary before copying into a **new** immutable output directory. It refuses an existing output and performs no download, synthesis, simplification or geometry approval. Its receipt records source/catalog/OSM hashes and no current-flood/routing assertion.

From `backend/`, after independently reviewing permitted real polygons:

```powershell
.\venv\Scripts\python.exe -m scripts.provision_news_barangay_catalog `
  <reviewed-catalog-directory> <archived-source-file> <new-version-directory> `
  --license-url <https-license-source> --license-reviewed-by <actual-reviewer>
```

Configure the same immutable catalog version for API and extraction/evaluator processes and restart. Run read-only `scripts.audit_news_spatial_assets --city Pasig --road C5` to inspect coverage. C5 route coverage and partial Pasig community preview provisioning are delivered locally; omitted barangays/regions, official/legal extent and supported operational flood footprints remain unverified. [Verification](../evaluations/phase-36-independent-evaluation-and-spatial-coverage.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)
