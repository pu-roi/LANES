# Automatic news map: shared renderer correction

> **Last Updated:** October 10, 2026, 12:38 AM, Asia/Manila
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Local correction; developer visual acceptance and actual original-news activation remain open.

## October 10: Requested solid inner line and transparent outer area

The developer explicitly asks the automatic plot to have the same inner and outer layers as an Active Zone. The previous shared-hook correction still supplied `geometry: null` and `mode: review`, so it did not deliver that appearance. This follow-up supplies both geometries and selects the canonical Active paint for the public automatic simulation; it is an appearance change, not activation.

`news_placement_display_service.placement_display_zone` creates a claim-level core from the already-normalized display sections and a single dissolved decorative polygon using the staff default 25-m road margin. Separate cores and genuine gaps remain unchanged; overlapping halo pieces are drawn once. Like the manual buffer, the decoration can surround a small centerline gap; it is not an affected footprint, measured flood width, or routing input. Response-only `PlacementDisplayZone` adds `candidate_ids`, `core_geometry` and `aura_geometry`. The preview service and guarded saved-snapshot launcher populate it without changing evidence, publication decisions, databases or the saved capture.

The news adapter accepts explicit `activeAppearance`, used by `MapCanvas` for this public automatic simulation. It maps one claim to the existing hook's `report_geometry`/`geometry` inputs and uses the exact `ACTIVE_ZONE_ROAD_CORE_PAINT` and `ACTIVE_ZONE_POLYGON_FILL_PAINT`. The shared hook honors explicit `is_pending` separately from paint and refreshes existing line paint when modes change. Missing two-geometry data surfaces an actionable toast instead of silently drawing the previous single-layer result. Admin Needs Review retains its established review-only style; real persisted automatic/manual Active Zones retain their normal shared Active path. The snapshot still truthfully reports Needs Review and no routing effect. No new simulation banner is added.

Verification: 46 backend display/preview/estimated-road/launcher checks pass, TypeScript and scoped lint pass, and the actual public automatic-plot browser test passes on desktop/mobile including narrow/landscape details. It asserts solid cores, a separately translucent halo and a real centerline gap with halo-only pixels. Six additional shared Active rendering/zoom and admin mixed-review/Active-summary regressions pass on desktop/mobile: eight browser workflows total. Read-only live Boni verifies `MultiLineString` core and `Polygon` halo, canonical core opacity 0.95 and fill opacity 0.25/0.45, desktop click flies to zoom 16 without opening details, hover opens shared details inside the viewport, and zero page errors. Artifacts: `frontend/test-results/news-two-layers`, `news-two-layers-regression`, `news-two-layer-live-fly-only.png`, `news-two-layer-live-hover.png` and close-up `news-two-layer-boni.png`. Scoped diff whitespace checks pass. User visual acceptance is pending. Earlier one-layer observations below are historical and superseded for the public simulation.

## Why the previous checkpoint was inadequate

Sharing severity colors and the popup component did not share the renderer or its interaction lifecycle. The old news hook owned separate line paint, overview behavior, camera bounds and popup listeners. Its desktop test incorrectly expected click to open details. The developer rejected that implementation after seeing inconsistent layers, circles, overlapping road sections and popup behavior. The earlier Phase 1 verification is historical and superseded by this correction.

An Active Zone needs both its backend avoidance polygon (transparent aura) and original road geometry (solid core). The original Boni replay supplies ambiguous preview centerlines, not an activated polygon. Its response is still Needs Review, `routing_affected=false`, reason `top_section_has_arbitrary_bounds`; the operational publication service also excludes passable-all reports. Existing source/time/audit gates remain relevant. Changing colors or assigning Active in React cannot satisfy those conditions or add a real staff-list entry.

## Changes and exact responsibilities

| File | Responsibility |
| --- | --- |
| `frontend/src/features/admin/review/useNewsPlacementLayer.ts` | Data adapter from news evidence/display sections to the shared zone hook. No independent painting or popup controller. Original candidate selection and initial overview retain their existing panel/context roles. |
| `frontend/src/features/map/hooks/useFloodZonesLayer.ts` | Shared feature construction, active core/polygon versus review aura, overview pins, hover dwell, mobile tap and desktop fly-only click. Namespaced sources permit active and review data to coexist. Selection updates do not tear down the interaction effect. Explicit mobile close clears selection for reopening; camera motion respects reduced motion. |
| `frontend/src/features/map/mapStyles.ts` | Canonical active and review paint. Preview-only news paint removed. Below zoom 14 use overview pins; at/above 14 use detail. Actual layer min/max zoom excludes invisible features from hit detection. |
| `frontend/src/features/map/components/FloodZonePopup.tsx` | Same compact desktop and modal mobile component, common header/height/hazard/reporter layout and close control. Source-specific facts and Needs Review status remain truthful. |
| `frontend/src/features/map/mapPopupUtils.ts` | Shared anchor selection. The zone hook measures and repositions actual content after rendering/movement to fit the viewport. |
| `frontend/src/features/map/MapCanvas.tsx`, `frontend/src/features/admin/LiveMapPage.tsx` | Pass existing public simulation/admin review data and touch mode into the adapter. Normal Active Zones API/list path remains the persisted-zone path. |
| `frontend/src/features/admin/review/reviewApi.ts` | Add optional presentation `display_sections` response typing. |
| `backend/app/services/news_placement_display_service.py` | Union coincident coverage and merge exact touching endpoints for one preview claim. Preserve real gaps, distinct carriageways, original candidates and candidate membership; no snapping, buffering or activation decision. |
| `backend/app/schemas/news_placement.py`, `backend/app/services/news_placement_preview_service.py` | Response-only display-section contract and service integration. No database schema or migration. |
| `backend/scripts/serve_local_news_replay.py` | Apply the same presentation service when reading the saved original-source capture on guarded loopback 8001. Does not rewrite the capture or publish zones. |

The four original Boni candidates now produce three continuous drawable parts: two adjoining carriageway sections plus the genuine disconnected part. All four candidate identities/evidence remain available. Parallel carriageways can still visually overlap when screen-space aura widths exceed their separation; this is different from duplicate centerline coverage. No gap or carriageway is silently filled or collapsed.

## Verification

- 48 backend tests pass: display union/membership, exact endpoints, reversed duplicates, partial overlap, tiny real gaps, parallel roads, placement preview, estimated-road gates and local replay guards.
- TypeScript and scoped adapter/API/test lint pass. Existing wider lint debt is not represented as clean.
- Nine distinct responsive workflows pass across scoped reruns: public news review on desktop/mobile (including 320px and landscape), active-news-shaped core/aura with zoom-out/back-in on desktop/mobile, mixed admin review on both surfaces, mobile narrow/landscape evidence switching and active-news staff summaries on both surfaces. The inapplicable desktop mobile-layout case is skipped. Artifacts: `frontend/test-results/news-shared-acceptance`, `news-active-measured-parity`, `news-active-pixel-debug`, `news-shared-final`. UI fixtures test contracts; they do not prove the original article activated. Earlier broad runs failed on color sampling/anti-aliasing or resource contention; final targeted reruns verify the corrected assertions and rendering. The last mobile repaint records 1,440 solid-core and 3,682 aura pixels.
- Read-only live public map uses the original saved Boni source: four candidates, three display sections, desktop click flies to zoom 16 without popup, subsequent hover opens shared source details entirely inside the viewport; no browser page errors. Private screenshot artifacts: `frontend/test-results/news-shared-live-overview.png`, `news-shared-live-fly-only.png`, `news-shared-live-hover.png`.

Audit of the core registry finds no new runtime dependency, SQL model/migration, flagship module or major architecture decision. Tech stack, database design, feature reference and decisions therefore need no new entry. Task plan, progress, system documentation, bug log, master index and replay guidance are synchronized. Changes remain on `roi-branch`, preserving the pre-existing working tree.

## Developer review and remaining issues

Reload `http://localhost:3000/map`. Review desktop hover/click and mobile tap/close/reopen, zoom 13 overview pins versus zoom 14+ detail, and joined Boni endpoints at street zoom. Existing persisted Active Zones still show solid core plus polygon aura. The Boni overlay remains review-only and therefore has no solid core or Admin Active Zones list entry. This limitation is not resolved by this UI phase. Real original-source activation, bounded road/carriageway evidence, publication admission and subsidence integration require the next separately reviewed backend phase. No cloud mutation, fabricated article, gate override, new dependency, SQL migration, commit, push or deployment in this correction.
