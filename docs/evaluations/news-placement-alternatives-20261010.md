# News placement alternatives and visual overlap

> **Last Updated:** October 10, 2026, 1:14 AM, Asia/Manila
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Local implementation; developer visual acceptance pending.

## Confirmed cause

Read-only inspection of connected database `lanes` found article 25, one input version and completed run 61. Eleven raw claims include six location-context claims; the News Intelligence reader returns five road claims. Boni is claim index 1, with four ambiguous OSM candidates and no selected section. Claim sources, publication decisions and news-zone links are empty. Existing active zones 17/18 have no news links and their polygons do not intersect. The additive public simulation reads a captured result, not persisted news zones.

Opposite Boni candidates are approximately 7.9–8.3 m apart with no coincident centerline length. Two candidate pairs meet at endpoints; one modeled gap is approximately 3.86 m. Exact display normalization produces three parts from five input line parts. At zoom 16, 8 m is about 7 pixels on a flat map, narrower than the existing solid stroke. Drawing all candidates as one core therefore creates visual overlap, despite a dissolved halo and no duplicate database zone. NOAH scenario coverage is normalized along each original road before drawing.

## Correction

- `backend/app/services/news_placement_display_service.py::resolved_placement_display_zone` builds a two-layer presentation from only the uniquely selected, grounded candidate with available geometry. Ambiguous carriageways, incomplete candidate sets, unavailable fragments and uncertainty produce no display zone. All original candidate evidence remains inspectable.
- `backend/app/services/news_placement_preview_service.py` and `backend/scripts/serve_local_news_replay.py` use the same eligibility function. The saved capture is not rewritten.
- `frontend/src/features/admin/review/useNewsPlacementLayer.ts` passes only the server-resolved core/halo to the shared zone renderer on public simulation. It also rejects older responses combining alternatives. Admin inspection draws only the explicitly chosen candidate using existing review paint; clearing inspection removes it. Public camera bounds exclude unresolved alternatives.
- `frontend/src/features/admin/review/NewsReviewEvidence.tsx` explains one-at-a-time inspection and offers Clear suggestion on both responsive layouts. Inspecting a candidate does not resolve or approve its placement.
- Existing manual and persisted automatic zones retain their shared rendering, popup and camera behavior. Real gaps and opposing carriageways are not snapped together. Database schema, activation/routing policy and dependencies are unchanged.

The actual Boni overlay is consequently absent from public `/map`; all four alternatives remain in Admin inspection. This is intentional exclusion of unresolved geometry, not successful operational activation. Resolved preview fixtures keep the requested inner/outer appearance and Needs Review details. Cross-article incident/geometry reconciliation remains a separately reviewed backend phase.

## Verification

- 57 focused backend tests pass: display selection/topology, placement preview, estimated-road gates and replay guards.
- Eight distinct browser workflows pass across final focused runs: resolved public preview, unresolved alternative exclusion, single-candidate Admin inspection/switch/clear and persisted Active Zone core/aura/overview behavior, each on desktop and mobile. Resolved preview also checks narrow and landscape mobile details. Desktop click remains fly-only and mobile tap opens shared details.
- Initial verification exposed a mobile popup cleanup caused by rebuilding public records on selection. Keeping public display records stable fixes it. An existing mobile Active Zone check also failed during zoom/overview sampling; final scoped reruns pass. Its pixel sampling now hides HTML controls so palette/button colors cannot be counted as map auras. No assertion or test was removed.
- TypeScript, scoped ESLint and scoped diff whitespace checks pass.
- Read-only live desktop/mobile checks return zero news preview features, existing active IDs 17/18 and no page errors. Simulation response retains four Boni candidates, null selected candidate and null display zone. API Active Zones still returns IDs 17/18.
- Artifacts: `frontend/test-results/news-resolved-final`, `news-resolved-active-controls`, `news-resolved-live-1440.png` and `news-resolved-live-390.png`. Browser UI fixtures establish rendering contracts, not real-news activation or physical-device accuracy.

No collection, AI provider, publication or cloud database write was executed. The guarded loopback snapshot server was restarted to serve the changed presentation function; frontend changes are available on port 3000. Stop at this visual review checkpoint before changing activation or cross-article reconciliation.
