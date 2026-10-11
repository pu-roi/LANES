# Phase 36: Backend OSM/NOAH/Pasig placement preview

> **Last Updated:** October 03, 2026, 11:52 PM
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Local backend preview implemented and tested; map UI, durable public lifecycle and production release remain pending.

## Delivered

Shared captured-body processing now attaches typed `placement_preview` alongside `road_placement`. Bounded OSM candidates are compared with exact source-vector NOAH overlaps for 5-, 25- and 100-year scenarios. Article place specificity precedes matching history and modeled signals. Confirmed Pasig claims receive matching road/crossing DRRMO rows, year/record identifiers and separately retained unmatched rows. Other cities never inherit Pasig history. Current article depth, status, time and passability remain unchanged.

Alternatives remain visible. Truncated candidates, missing barangay boundaries, ungrounded qualifiers, competing carriageways, equal support and missing Pasig history cannot silently select a section. Forecast/negated/caption/context-only evidence does not select a flood placement. Historical locations remain previews. Every preview fixes `proves_current_flood=false`, `may_affect_routing=false` and `read_only=true`.

`GET /api/v1/admin/news/results/{run_id}/{claim_index}/placement` recomputes current placement from saved immutable evidence. The response separates the original claim/run identity from current OSM/NOAH/history revisions. It uses the existing admin-role dependency, validates identifiers, limits requests to three per minute, returns 404 for missing evidence and 503 for unavailable database storage. Analytical failures use typed status/reason. The GET invokes no publisher network, auditor, database writes or activation service. Ordinary result readers continue returning recorded artifacts.

## Analytical assets and storage

The offline builder reads the three permitted Metro Manila shapefiles, validates geographic WGS84 and numeric Var fields, preserves holes, repairs invalid rings with existing Shapely and clips without simplification into indexed 0.02-degree vector tiles. Tiles and source archives have SHA-256 identities; the manifest preserves attribution and ODbL identity. Runtime checksums/size limits and bounded caching protect reads. Unioning clipped intersections prevents duplicate lengths at shared tile edges. Intersections use source WGS84 vectors; metre lengths use a local affine approximation.

Local ignored `data/noah-placement/` contains **897 tiles plus one manifest**, **89,778,805 bytes** total. Manifest SHA-256: `cceb8c93d5441f14aad48808319a3d4cf3a87918ea8089dcb5efbf86c49940ce`. Production needs a versioned external asset directory configured with `LANES_NEWS_NOAH_DIR`; no source ZIP or tile was added to Git/the API image. The frontend NOAH raster is independent.

Code identity `rules-spatial-preview-v10` plus a hashed source revision tuple produces a **90-character** processing identity within existing `String(100)`. Optional preview data uses existing extraction JSONB; older artifacts deserialize without it. SQLAlchemy models, Alembic revisions and dependencies are unchanged. No actual local/cloud article was enqueued or reprocessed here, so prior four-article replay counts remain unchanged.

## Verification

- Broad news/extraction/spatial regressions: **512 passed, one skipped**.
- Final preview/builder plus hybrid/depth/routing checks after the source-provenance addition: **61 passed**. Twenty-three preview/builder cases overlap the broad run: **550 distinct passing checks**. Existing multipart deprecation warning remains.
- New cases cover holes, decimal Var fields, unsupported CRS, immutable build output, tile-edge deduplication, corrupt/missing/outside assets, repaired source identity, storage identity length, faithful claim facts, Pasig-only history, unmatched rows, missing/malformed history, forecast/negation/caption/context, truncation and missing barangay boundaries. Shared rules processing invokes no external auditor. Protected endpoint tests prove 401/403/staff access, immutable identity, 404/422 and no writes after fixture setup. Existing queue/idempotency and activation regressions pass.
- Actual OSM and built NOAH historical-location probes reproduce **one 86.2 m Santo Domingo span** between Atok/Calamba with full modeled overlap in all scenarios. **Caruncho retains six sections**, six matched historical-row associations and 22 unmatched rows. The ranking proposes one section while keeping alternatives; this does not verify actual flooded extent.
- Probe claims were constructed from already documented historical places. These are spatial checks, not a new complete-article, live RSS, current-flood or production acceptance test. Output is preserved in ignored `data/noah-placement-verification.json`. No reports, events or zones were created.

## Remaining checkpoint

October 4 checkpoint verification before Needs Review implementation: the targeted news/placement/feed selection produced 116 passes and two failures. The saved-place fixture now explicitly sets no profile address, preventing an unintended live geocoding request; all four feed-priority checks pass after that repair (117 distinct passing checks across the selection). Frontend TypeScript passes. The existing report-geocoding integration check could not pass because local PostgreSQL and Valhalla were unavailable; it remains a disclosed environment limitation. No model, migration, or dependency files changed. The checkpoint also preserves the current feed/profile-location work in the shared checkout.

Display previews in existing desktop/mobile Spatial Operations with source evidence, alternatives and uncertainty. Determine supported operational corridor geometry before applying the solid-core/translucent-area active-zone renderer. Complete independent audit/current-evidence eligibility and durable identity, publication links, duplicate prevention, correction/clearance and expiry before public writes/routing. Any exact SQLAlchemy/Alembic proposal still requires separate approval.

[Catalog guide](../guides/news-placement-preview.md) · [Rendering investigation](phase-36-flood-zone-rendering-investigation.md)
