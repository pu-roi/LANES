# News placement preview and NOAH catalog

> **Last Updated:** October 07, 2026, 12:25 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

Staff can inspect a completed immutable result without writes:

```text
GET /api/v1/admin/news/results/{run_id}/{claim_index}/placement
Authorization: Bearer <staff JWT>
```

Review the ranked candidate, reported/predicted kind, alternatives, OSM/NOAH/history checksums, modeled overlap and status/reason. Original saved claim/run identity is separate from current placement revision. A proposed centerline does not prove flooded width. The local Spatial Operations Needs Review interface now opens current news exceptions with separate modeled road pieces using the existing transparent severity aura; it starts with no candidate selected. Newly processed artifacts also expose the optional preview through existing extraction/details contracts. This does not deliver automatic publication. [Inspection verification](../evaluations/phase-36-needs-review-inspection.md).

## Current OSM and administrative coverage

The local OSM catalog rebuild uses the same September 27 snapshot, adding source-stated C5 route relations rather than renaming roads. C5/Pasig now resolves 45 road ways and 14 ambiguous sections; these do not establish a flooded span. Run the read-only `python -m scripts.audit_news_spatial_assets --city Pasig --road C5` from `backend/` to inspect OSM/NOAH/history/boundary source identity and coverage. No network/database/public write occurs.

Twenty Pasig OSM community polygons are bundled locally, including Ugong. The actual reviewer is the geometry agent performing automated source/PSGC/parent checks; no official/legal/human/field verification is implied. The placement response preserves `barangay_osm_relation_id`, `barangay_source_url` and `barangay_source_classification` beside source/catalog hashes. Ten Pasig barangays and broader regions remain unsupported. Missing polygons and parent-city containment mismatch remain explicit failures. Follow the [boundary asset guide](news-barangay-boundary-assets.md); no point fallback, synthetic polygon, hazard envelope or arbitrary road buffer supplies operational width. [Current verification](../evaluations/phase-36-independent-evaluation-and-spatial-coverage.md).

## Build exact analytical assets

From the repository root in PowerShell, using the existing Python environment and verified Metro Manila ZIPs:

```powershell
backend/venv/Scripts/python.exe backend/scripts/build_noah_placement_catalog.py `
  --noah-5yr data/noah_metro_5yr_inspect.zip `
  --noah-25yr data/noah_metro_25yr_inspect.zip `
  --noah-100yr data/noah_metro_100yr_inspect.zip `
  --output data/noah-placement
```

Default extent: longitude 120.90–121.14, latitude 14.35–14.79. `--bounds west south east north` permits an explicitly smaller development catalog. The builder refuses to replace an existing manifest: choose a new versioned directory for changed sources. Partial builds have no manifest and remain unavailable. Preserve attribution and ODbL terms when distributing these derived assets.

Local default is now versioned `backend/runtime_data/noah-placement`; the original builder output can remain in ignored `data/noah-placement`. Override with:

```powershell
$env:LANES_NEWS_NOAH_DIR = 'D:/path/to/immutable/noah-catalog'
```

Restart API/collector after changing the directory/catalog. Providers cache immutable versions; do not modify live tiles in place. New source digests change processing identity while preserving old inputs/results. OSM uses the existing `LANES_NEWS_OSM_CATALOG_DIR`; history uses the existing bundled Pasig clean CSV.

## Runtime and limits

The reviewed approximately 90 MB derived bundle is now included in `backend/runtime_data/noah-placement` and copied by Docker to `/data/noah-placement`, with complete build-time asset verification and preserved manifest hashes. Raw ZIPs remain outside Git/the API image. Explicit immutable external catalogs remain supported. Matching cloud deployment is pending; the frontend PNG overlay cannot replace analytical vectors. [Packaging evidence](../evaluations/phase-36-news-runtime-packaging-20261007.md), [exact release steps](news-zone-release-checklist.md).

Missing/corrupt/oversized assets and out-of-extent queries remain unavailable evidence. Missing history/barangay boundaries stay explicit. Zero modeled overlap does not prove current safety. NOAH return periods are distinct from DRRMO historical years; neither supplies current observation time or depth.

The protected preview GET does not enqueue processing. Historical persistence/replay must follow the [private isolation guide](local-news-replay.md). Existing replay rows were not changed by this slice.

[Verification and remaining work](../evaluations/phase-36-backend-placement-preview.md).
