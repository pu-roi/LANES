# Automatic news map UI: Phase 1 verification

> **Last Updated:** October 09, 2026, 10:45 PM, Asia/Manila
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Historical checkpoint, rejected by developer for incomplete rendering/interaction parity; superseded by [shared-renderer correction](news-shared-map-renderer-20261009.md). Its test counts describe the earlier implementation, not current acceptance.

## Result and scope

News placement suggestions now use the shared FloodZonePopup, with desktop hover/click and mobile tap. Review suggestions show Needs Review, source evidence/link, road/locality/section, reported depth/passability and observation time. Missing severity stays neutral; missing observation time stays unspecified. They do not claim operational activation or confirmed safe vehicle passage. Admin review obtains article metadata from its existing detail response; the additive public snapshot supplies its existing title/link. No additional backend endpoint is required.

The preview layer retains each backend preview_geometry once per candidate, with stable feature identity and layer lifetime. Shared pending-aura tokens supply its visual language; zoom-scaled news widths reduce the oversized 24/32 px strokes. Selection updates data without removing/recreating the layer. Style reload is supported without a repeated idle setData loop. Separate carriageways and real MultiLineString gaps remain unchanged. Endpoint and alternative-carriageway geometry canonicalization is deferred to the backend phase; narrower strokes do not prove that all overlap has been eliminated.

Initial public overview can include existing active zones; selecting a suggestion frames only its supplied preview geometry. The camera respects reduced motion and navigation padding. Desktop click retains its popup during camera movement. Popup positioning uses the shared anchor helper, measures its rendered height, and repositions after rendering/moveend so longer source excerpts remain within the screen. Hover has a 400 ms dwell and a 250 ms bridge into the popup. Mobile details have a close control and bounded scroll area.

Actual operational news zones continue through the same active polygon/core hook and Active Zones panels as manual zones. The current original September 24 snapshot still returns Needs Review, four ambiguous Boni candidates and no routing effect. This frontend phase does not create a persisted simulated zone or populate Admin Active Zones with that snapshot.

## Changed application files

| File under frontend/ | Responsibility |
| --- | --- |
| src/features/admin/review/useNewsPlacementLayer.ts | Stable candidate rendering, hover/click/tap popup lifecycle, selected-only camera bounds and measured popup positioning |
| src/features/admin/review/reviewApi.ts | Optional presentation-only article metadata on PlacementEnvelope |
| src/features/admin/review/NewsReviewEvidence.tsx | Reuses loaded original article title/publisher/link/publication time in the map preview |
| src/features/admin/LiveMapPage.tsx | Passes desktop/mobile interaction mode to the existing review hook |
| src/features/map/MapCanvas.tsx | Supplies existing snapshot title/link and touch mode to the shared review hook |
| src/features/map/mapStyles.ts | Shared pending-aura-based, zoom-scaled news preview paint |
| src/features/map/mapPopupUtils.ts | Shared flood popup anchor calculation |
| src/features/map/hooks/useFloodZonesLayer.ts | Reuses that anchor helper; active-zone paint and detail content remain established |
| src/features/map/components/FloodZonePopup.tsx | Shared preview-aware detail layout and centralized severity colors |
| tests/news-placement-map.spec.ts | Public preview interactions, camera isolation, true gaps, separate carriageways, long excerpts and responsive popup checks |

## Verification

- TypeScript: `node node_modules/typescript/bin/tsc --noEmit` passes.
- Scoped ESLint passes for useNewsPlacementLayer, NewsReviewEvidence, reviewApi, mapPopupUtils and the new test. Broader lint still reports existing any/unescaped-quote/unused-variable violations in FloodZonePopup and existing any paint declarations in mapStyles; this is not a repository-wide lint pass. The new paint uses MapLibre's LineLayerSpecification paint type.
- Application diff whitespace check passes.
- Playwright: **17 passed, one desktop-only skip** across the two viewport projects. The new preview test passes on desktop and mobile; it also exercises 320×740 and 844×390 mobile layouts. Its screenshot pixel checks retain a real unpainted gap and a separate painted carriageway. A long excerpt checks full desktop popup bounds. Fifteen existing checks cover active news core/aura/source details, Admin Active Zones news summaries, mixed review inspection, style switching and cleanup, unresolved/unavailable/truncated/failed queue states, and mobile narrow/landscape evidence switching. Fixtures are intercepted HTTP responses and do not demonstrate actual pipeline activation.
- Read-only live desktop check on localhost:3000: the original saved **Minor flooding hits some metro areas** snapshot returns four candidates and Needs Review. Hover shows the source details; click focuses the selected Boni section at zoom 17, approximately [121.02823, 14.58323]. The final full-excerpt popup bounding-box check confirms it stays within the 900 px screen. Normal API traffic remains connected; non-GET API traffic was blocked in this browser check. Screenshots capture overview, hover and selected focus. The source still lacks a publisher field in this snapshot, so its popup correctly uses News report rather than inventing a publisher label.
- Earlier attempts encountered a shared Playwright output-directory collision, an incorrectly inherited WebKit mobile browser setting in the new test, and a stopped local development server. The test now explicitly selects Chromium, uses distinct output directories, and passed after the normal repository development command restored port 3000. The live longer excerpt exposed a real bottom cutoff, fixed and covered by the final long-excerpt checks. One live initial-hover retry timed out; the final live script repeats pointer movement until the rendered road responds and passes hover, camera and full-popup bounds checks.

Local, ignored screenshots are under frontend/test-results/news-map-phase1-final, news-map-phase1-regression and frontend/test-results/boni-live-*.png. The local development server is available on port 3000 for developer review. These screenshots and the read-only browser helper are verification artifacts, not committed source articles.

No backend source, migration, dependency, database state, provider request, publication/activation gate, push or deployment was changed by this phase. Existing unrelated working-tree changes were preserved. Schema/dependency/architectural decision documents require no updates for this frontend change.

## Developer checkpoint

Review public /map hover, click focus and mobile tap, plus Admin /admin/map → Needs Review inspection. Remaining actual activation, public/admin persisted-zone parity, source/clock/audit gates and semantic road grouping belong to the next reviewed phase. No next-phase work starts until the developer accepts this UI checkpoint.
