# Active Zones selection colors and visibility — October 24, 2026

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). Updated October 24, 2026, 12:36 PM Asia/Manila. **Status: implemented and verified; source publication on `roi-branch`; frontend deployment pending.**

## Reproduced failure

The shared `syncGeoJSONSource` updater sent `removeAllProperties: true` and a replacement property list together. A real MapLibre worker reproduction changed the selected feature's properties to an empty object: the lime road's sampled RGBA changed from `[132,204,22,255]` to `[0,0,0,255]`. Losing color explains black roads; losing point/filter/identity properties also explains missing overview pins and interactions. Earlier map acceptance established presence and details, but did not assert property retention or rendered selection colors.

The admin map initially framed Pasig. Its tab transition restored only an existing selected zone, so unselected floods elsewhere in NCR could remain off-screen. Viewport query-key changes also discarded the current visible collection during reads. Review-only isolation could suppress zone drawing after a tab transition. A compact coordinate handoff could start on a hidden canvas, be marked handled and then have its camera flight interrupted by resize.

## Implemented behavior

- Send changed/added properties and explicit obsolete-property removals without clearing every property. Ignore absent optional values; preserve IDs, severity, colors, flags and evidence. Geometry-only diffs carry an empty property-update array so queued geometry/removal updates can coalesce safely. Reordered/replaced collections retain the full-set path.
- Request one overview fit to the existing server's global active bounds on entering Active Zones or returning from group inspection. Wait for map/style/canvas readiness and compact-map visibility. Group/zone inspection and coordinate/report handoffs keep their explicit focus. Ordinary polling, resizing and manual panning do not reframe an already handled overview request.
- Clear review-only isolation for the active overview and collapse visible workspace drawers without deleting their independent draft/session state. Keep inactive selected records outside the Active Only overlay and do not let a cached selection repopulate an authoritative globally empty active map.
- Retain the last successful map collection only for the same map/domain/filter scope while a viewport request loads or fails. Successful empty results replace it. Add persistent, accessible map loading/error/empty feedback with retry on desktop and the compact map; failed drawing retries redraw the layers and retain their warning until drawing succeeds.
- Restore active layers above the Pasig mask after style/terrain changes. Delay compact coordinate-only handoffs until the visible canvas has resized.

Key files: `frontend/src/features/map/syncGeoJSONSource.ts`, `hooks/useStaffMapData.ts`, `hooks/useFloodZonesLayer.ts`, `components/ActiveFloodMapStatus.tsx`, `frontend/src/features/admin/LiveMapPage.tsx`, and `components/ActiveZonesPanel.tsx`. Existing palettes, controls, layouts, flood evidence and HTTP response contracts are retained.

## Verification

- **72 functional Playwright cases passed** across desktop and mobile: new selection/worker/visibility regressions plus zone queue, public news-zone map, flood history map, moderation handoffs and shared heatmaps.
- Actual canvas pixel and worker-property checks cover selection/deselection, explicit property removal, queued geometry/property changes, additions, reorder and removal.
- Browser scenarios cover distributed NCR floods outside Pasig, group-to-overview return, delayed and failed viewport reads, authoritative empty data, review isolation, retryable drawing failure, style restoration, zero-elevation fixture terrain toggles, zoom 13.9/14/14.1/16 and explicit coordinate handoffs.
- Existing desktop **1,000- and 10,000-zone** bounded-history scale cases also passed during the broader run. That mixed run had a simultaneous functional timeout and was stopped; the 72 functional cases were then verified separately from the four desktop/mobile scale benchmarks. A later development-server run encountered source hot reloads, so functional verification used a frozen source snapshot and one worker. Three new-suite startup connection refusals passed after server readiness. The existing moderation fixture was updated to serve the current zone-detail and bounded-map contracts rather than unrelated empty arrays; its rendering assertions remain intact. The compact history focus comparison now waits for the detailed viewport geometry before capturing its baseline. All eight targeted reruns passed, including a transient wide-layout polling timeout. The strengthened overlapping-viewport check passed on desktop and mobile. No product assertion was removed or weakened to hide a failure.
- Frontend TypeScript `tsc --noEmit` passes. Scoped ESLint comparison against HEAD reports **zero added diagnostics**; **20 pre-existing errors** remain in `LiveMapPage.tsx` and `useFloodZonesLayer.ts`. This is not a claim that full-project lint is clean.
- All four original unrelated frontend file hashes match their pre-task records. Concurrent unrelated backend and other frontend changes were left untouched. API requests in the functional fixtures are intercepted; no Cloud SQL, flood, schema, dependency, extraction, Gemini, automation or deployed-service changes were made by this repair.

The regression fixtures are fictional browser data, not new flood evidence. QA uses a frozen source snapshot on local port 3005 and the existing Playwright setup; test logs/screenshots/traces are private build artifacts. This push publishes the source to `roi-branch`; frontend deployment remains a separate follow-up.

## Routine refresh label follow-up

> **Last Updated:** October 24, 2026, 06:41 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

At the developer's request, remove the visible routine “Updating flood map…” label when existing flood features remain on the map. `ActiveFloodMapStatus` retains a screen-reader-only refresh status with no padded visual row. Initial loading, empty results, stale-data alerts and retryable drawing/refresh failures remain visible. Shared use in `LiveMapPage` covers desktop and compact map layouts. No records, geometry, API, dependency or schema changes.

Verification: TypeScript and scoped lint pass. The existing desktop/mobile drawing-error/recovery cases passed initially; the refresh-retention/overlapping-request/authoritative-empty cases first timed out at `page.goto` waiting for the page `load` event, before application assertions. The helper now waits for `domcontentloaded` and retains explicit content/canvas/rendered-feature readiness checks. The two refresh cases pass on a one-worker rerun, including the assertion that the removed label is absent. Four distinct cases are accepted across these runs; this is not a clean first-run claim. Fictional API/geometry fixtures and lightweight basemaps are used. Source remains local and frontend deployment is pending.

The supplied Zone 85 screenshot separately exposes article-header/social boilerplate in its evidence/admin-notes excerpt. That presentation defect is logged as unresolved, alongside the seven accepted but unplotted Philstar observations and nineteen unresolved verification targets. It does not authorize editing original source text or creating guessed polygons.
