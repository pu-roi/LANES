# Automatic news map: Phase 1 investigation and UI plan

> **Last Updated:** October 10, 2026, 4:09 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Shared renderer retained; subsequent authorized backend correction now creates original Boni Zone #56. Actual public/Admin desktop/mobile checks pass; developer visual review remains pending.

## October 10 persisted original-source checkpoint

The real collector/extractor/live auditor/publication/footprint workflow now saves one Boni polygon with preserved source cores. Public/Admin return Zone #56 through their normal shared rendering/data paths. Same-observation continuity and consumer-aware review filtering remove the stale exception without extending expiry. Earlier preview-only and unfinished activation notes below are historical. [Root causes, files and verification](../evaluations/news-boni-corridor-reconstruction-20261010.md).

## October 10 overlap checkpoint

The approved investigation found no persisted duplicate Boni zones: one claim generates four ambiguous road alternatives whose strokes overlap in screen space. The local correction supplies a two-layer display only for resolved placement, keeps every alternative inspectable one at a time in Admin, and excludes unresolved alternatives from public painting/camera bounds. Existing zone rendering and source/publication gates remain shared. Await developer review before backend cross-article/incident spatial reconciliation. [Exact files and verification](../evaluations/news-placement-alternatives-20261010.md). This supersedes the earlier all-candidate public core/halo checkpoint.

## Revised Phase 1 checkpoint

**October 10 explicit appearance authorization:** The developer asks the actual public automatic plot for Active-style inner/outer layers. Supply a backend-generated claim-level core and dissolved decorative halo and map them through the existing Active paint; keep evidence/status/publication semantics separate. The earlier shared-hook correction was still one-layer and did not satisfy the requested appearance. This correction is implemented and awaits visual acceptance; original-source operational activation stays in the separately reviewed next phase. [Exact implementation and evidence](../evaluations/news-shared-map-renderer-20261009.md#october-10-requested-solid-inner-line-and-transparent-outer-area).

The developer rejected color-only parity, separate paint/camera/popup implementations and click-to-open on desktop. The authorized correction replaces the news hook with an adapter into `useFloodZonesLayer`, uses canonical active/review paint and actual zoom visibility, shares measured popup anchoring and mobile close/reopen, and combines only exact adjoining/coincident preview coverage on the backend. Four original Boni candidates yield three drawable parts with evidence preserved. Active news fixtures retain both core and polygon aura; Boni itself remains review-only under the existing original-source activation gates. [Correction, exact files, evidence and remaining limits](../evaluations/news-shared-map-renderer-20261009.md). Earlier implementation counts/behavior below are historical. Stop for visual review before changing activation or routing policy.

## Intended result and review gates

The developer wants automatic news zones to follow the existing Active Zone design, with clean road coverage, desktop hover/mobile tap information and reliable camera selection. A successful end-to-end activation simulation must create the same persisted zone visible on public /map and Admin Spatial Operations → Active Zones, including its primary list.

This checkpoint investigates and plans only. On "next" or "proceed", implement the agreed Phase 1 UI slice, present desktop/mobile evidence, then stop for review. Proceed to backend geometry/publication work only after that UI checkpoint is accepted. No frontend status assignment can substitute for backend activation.

## Documentation reviewed

Read AGENTS.md, DESIGN.md and frontend/AGENTS.md; apply News Intelligence, UI, API, senior-planner and test skills. Relevant docs include the README/current replay guide, task/progress/system records, activation safety gates, LiPAD/NOAH placement plan, October 6 estimated-road integration, October 9 runtime/backend acceptance and September replay evaluations.

The October 6 integration and latest additive replay guide supersede older claims that the collector has no publication path. Distinguish implemented backend fixture acceptance, historical replay previews and actual current-news activation. Existing documents also record the developer's rejection of fabricated article/auditor demonstrations and removal of the added simulation status box; do not reintroduce either as a shortcut.

## Evidence collected during this investigation

- The developer confirms images 1/4 were captured on public /map and the simulated Boni lines are absent from Admin → Active Zones.
- Read-only HTTP GET http://localhost:3000/api/v1/reports/active-zones returns zone IDs 17 and 18, both with Polygon geometry, LineString report_geometry and zero news contributors.
- GET http://localhost:3000/simulation/api/v1/news/simulation returns status Needs Review, routing_affected=false, preview status ambiguous, reason top_section_has_arbitrary_bounds and four candidates.
- frontend/public/news-simulation.local.json selects september24. apiClient redirects only /news/simulation to the private snapshot route; normal zone/auth/SSE traffic remains on its normal API.
- The saved connected capture at ignored data/news-replay/september24-cloud-addition.json identifies run 61, claim index 1. These are placement candidates, not newly persisted FloodAvoidanceZone rows.
- No database writes, provider/auditor calls, collection jobs, application edits, tests, server restarts or deployment occurred during investigation.

## Pipeline traced

| Stage | Current files / functions |
| --- | --- |
| Publisher/feed configuration and collection | backend/app/services/news_sources.py, news_feed_service.py, news_discovery_service.py; backend/scripts/run_news_discovery.py calls discovery and, when configured, run_news_pipeline |
| Captured body and durable extraction | backend/app/crud/news_processing.py; backend/app/services/news_processing_service.py::process_saved_news and news_discovery_service.py::_extract_article_inputs |
| Parsing and place grounding | hybrid_extraction_service.py::extract_hybrid(mode="rules_only"), taglish_extraction_service.py::extract_taglish_flood_facts, Philippine location/geometry services |
| Road/model evidence | news_road_placement_service.py, article_road_context_service.py, news_placement_preview_service.py; checked OSM, NOAH and applicable Pasig history |
| Independent audit | news_evaluation_service.py, news_claim_auditor.py; separate from committed rules extraction |
| Source publication and operational activation | news_pipeline_service.py → news_publication_service.py and news_footprint_worker_service.py; exact-footprint or news_estimated_road_service.py corridor path |
| Zone persistence | news_publication_service.py::activate_operational_footprint stores each accepted polygon component plus matching source_geometry and news-zone links; current evidence/expiry remains required |
| Public/staff zone projection | endpoints/reports.py active-zones → crud/report.py active/expiry filter → news_zone_projection_service.py |
| News Intelligence reader/handoff | NewsIntelligencePage.tsx → NewsResults.tsx/newsApi.ts → admin_news.py/news_results_service.py; NewsResultDialog.tsx navigates to /admin/map?review_news=run:claim |
| Activated map zones | MapCanvas.tsx and LiveMapPage.tsx → useFloodZonesLayer.ts → mapStyles.ts/FloodZonePopup.tsx |
| Review candidates | NeedsReviewPanel.tsx/NewsReviewEvidence.tsx → reviewApi.ts placement API → useNewsPlacementLayer.ts |
| Additive public simulation preview | useNewsSimulation.ts → scripts/serve_local_news_replay.py saved snapshot → MapCanvas.tsx → useNewsPlacementLayer.ts |

Service filenames in the table without a full directory are under backend/app/services; frontend components are under frontend/src/features/news, admin/review or map as applicable.

## Confirmed causes and remaining checks

### Rendering and absent admin zone

useNewsPlacementLayer emits one feature per candidate into news-placement-suggestions/news-placement-centerlines. It uses PENDING_REPORT_ROAD_AURA_PAINT, not the active polygon/core hook. Public simulation sets overviewVisible=true, bypassing the normal detailed-opacity zoom threshold. An active-looking road core is not generated.

LiveMapPage Active Zones reads the actual active-zones endpoint. The September replay overlay is a public-map-only presentation branch, so it cannot appear in that active list. This is a status/activation mismatch, not simply a missing admin paint layer.

### Overlapping linework

The four saved candidates have distinct IDs and disjoint OSM way sets:

| Candidate ID | Section | Approximate displayed length |
| --- | --- | --- |
| osm:242925489-242925667 | Ballesteros–F. Ortigas carriageway | 183.8 m |
| osm:1141753366-1141753373 | Opposite Ballesteros–F. Ortigas carriageway, two fragments | 180.0 m |
| osm:1141753343-1141753373 | Martinez–F. Ortigas carriageway | 123.7 m |
| osm:242925667-454028267 | Opposite F. Ortigas–Martinez carriageway | 124.6 m |

Two same-carriageway pairs share endpoints. Opposite-carriageway section endpoints are about 8 m apart. One modeled MultiLineString preserves a roughly 3.9 m gap. Distances are approximate local-coordinate measurements, not a spatial acceptance decision.

All four candidates are marked ambiguous_carriageway=true. The hook displays all of them together with 24/32 px round-capped translucent strokes. Stroke overlap and adjoining caps can explain darker patches and apparent duplicate/continuous coverage. This does not establish four identical backend geometries.

news_placement_preview_service already dissolves scenario overlaps within each candidate using placement_geometry_service.source_aligned_line_union. It preserves real gaps and original bends. Do not union separate carriageways, alternatives or dry gaps just to improve a screenshot. Any necessary semantic section grouping/canonicalization belongs on the backend in a later phase.

### Missing popup

useNewsPlacementLayer mouseenter only changes the cursor. It has no hover dwell, popup root, FloodZonePopup render or mobile-tap information path. Its feature properties contain candidate_id, selection and color only. Source/condition/depth/time and preview basis are available in the PlacementEnvelope but not passed to a popup.

Existing active/pending hooks implement hover/tap separately. An active popup says Active by default unless is_pending is provided; directly feeding candidates into that component without an explicit preview state would misrepresent status.

### Camera behavior

Candidate clicks change selectedId, then an effect calls fitBounds. Public MapCanvas always supplies all current zone polygon coordinates as contextCoordinates. These are included even when a single Boni candidate is selected, so the camera still frames unrelated Pasig zones.

The effect uses padding=48, maxZoom=17 and duration=650; its focus key does not express an overview-versus-selection distinction. Inspect interactions with URL focus, polling, map resize and desktop/mobile panel visibility during implementation.

Images 1/4 are dimmed. GlobalMap has a menu backdrop which can intercept input; screenshots alone do not establish whether that menu or another overlay was open. Reproduce this before attributing dimming/interception to geometry.

## Proposed Phase 1: frontend rendering and interactions

1. Keep activated news zones on the shared active polygon/core renderer and existing Active Zones lists. Give review/simulation candidates the existing transparent review visual language and an explicit status/basis in their information content. Do not add a permanent simulation box.
2. Give the candidate layer stable rendering/lifecycle behavior; check exact duplicate draw submissions, coincident endpoint artifacts, zoom sizing and selection emphasis. Use supplied preview_geometry once per candidate, preserving road topology and genuine gaps. Record any backend grouping requirement for the next phase.
3. Reuse shared popup content/lifecycle patterns for desktop hover and mobile tap. Supply original article/publisher/link, road/locality, reported depth/passability, observation time, preview reason and modeled-placement basis from the existing envelope. Do not show unprovided facts as confirmed.
4. Separate initial overview camera bounds from selected-candidate focus. A selected candidate focuses its own geometry with layout-aware padding; refresh/style reload should not repeatedly reset manual camera position. Verify click/tap and menu/backdrop behavior.
5. Verify actual activated-news fixtures across public map and Admin Active Zones list/map using the existing endpoint contracts. Treat this as UI acceptance, not proof that the original Boni claim activated.

Likely application files: frontend/src/features/admin/review/useNewsPlacementLayer.ts; frontend/src/features/map/MapCanvas.tsx, mapStyles.ts, mapGeoUtils.ts and components/FloodZonePopup.tsx; frontend/src/features/admin/LiveMapPage.tsx; supporting existing news presentation/types only where needed. Review GlobalMap.tsx if overlay interception reproduces.

The current request does not authorize silently promoting ambiguous preview data into public Active Zones. A true persisted activation simulation remains an explicit backend acceptance item after UI review. First audit the actual original-source gates and supported geometry; do not invent article observations, widen flood coverage or assign Active locally.

## Validation and developer checkpoint

Use existing frontend/playwright.config.ts desktop-chromium/mobile-chromium projects and extend news-zone-map.spec.ts/spatial-review.spec.ts as needed; do not introduce a new framework. Existing mocked active-zone tests do not exercise this public simulation preview branch.

- Compare ordinary active core/aura with a persisted-news-shaped API fixture.
- Confirm previews have no active core/status and active zones remain in the staff list.
- Hover detail opens after dwell, remains usable while entering the popup and closes correctly.
- Mobile tap opens readable source details, closes predictably and fits above navigation/safe-area constraints.
- Verify adjoining same-road sections, parallel carriageways, a genuine modeled gap, selection and multiple candidates at overview/street zooms.
- Selected Boni focus excludes unrelated zones 17/18; background refresh/style reload does not pull the camera away.
- No doubled layer registration, trapped pointer events, stale popup or overflow after navigation.
- Run TypeScript, relevant scoped lint and selected Playwright checks; disclose mocks and save desktop/mobile screenshots.

Present the changed files, evidence and any unresolved backend geometry issue, then wait for the developer's review. Phase 2 addresses source/clock/audit/geometry activation and genuine public/admin persistence parity; Phase 3 covers full RSS-to-zone lifecycle, routing, refresh/clearance/expiry and release acceptance. Each requires its own review checkpoint.

## Phase 1 implementation checkpoint

The developer authorized proceeding. Shared preview-aware popup content, stable candidate rendering, zoom-scaled review auras, selected-only camera bounds and measured popup placement are implemented. Seventeen responsive browser checks and TypeScript pass; a read-only live desktop check confirms the original Boni source popup and selected zoom-17 focus. Existing lint limitations, exact files and verification artifacts are recorded in [Phase 1 verification](../evaluations/news-map-ui-phase1-20261009.md). The current snapshot remains review-only; operational activation and geometry canonicalization are deferred. Await developer visual review.
