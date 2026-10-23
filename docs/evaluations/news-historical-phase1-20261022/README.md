# Phase 1 — connected local historical workflow

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). Branch `roi-branch`. Verification date: October 22, 2026, Asia/Manila.

**Phase 1 complete locally:** 434 distinct backend checks, 45 distinct desktop/mobile project checks (three intentional skips), TypeScript, focused lint and the final production build pass. The final changed-workflow/offline rerun passes all 12 checks. [Machine-readable aggregate](summary.json). This is isolated fixture verification, not actual September or hosted acceptance.

The fictional local workflow exercises saved authenticated extraction → source interpretation → existing bounded OSM/NOAH geometry → separate demo/archive saving → both active maps → authenticated deactivation → retained history. No real September inference or shared/cloud writes occurred. Frozen E0 documents authenticate unchanged; E1 processing-only authority is retained.

The later user correction supersedes the original visible-label requirement: the existing badge/modal layout and controls are preserved, with no historical-demonstration label. Source dates remain truthful. Internal versioned metadata retains dataset/session/observation lineage, original history references, geometry provenance and actual administrative action timestamps. Demo geometry remains excluded from online/offline routing and real-occurrence statistics.

**Latest interface amendment:** the user removed the Historical dataset selector. Flood Events/Analytics now use the unified history and original filters; dataset/session identifiers remain internal. See the [current verification and screenshots](#unified-history-amendment). Earlier dataset-selection acceptance below describes the original Phase 1 checkpoint.

## Backend verification

- 365 checks pass across historical E0/E1/output integration, native schema migration, source/road/NOAH placement, readers, routing, history/analytics, queue and authorization.
- 68 additional checks pass for publication API/lifecycle, routing, ordinary event lifecycle and historical heatmaps. These require the disposable fixture administrator; an initial empty-fixture run was corrected without changing the production code or tests.
- The approved `f1a9c7e2b604` migration adds no table/column/model. Deferred event/timeline constraints retain ordinary ended-event requirements and allow unknown archive endpoints only with the retained historical lineage. Missing start precision and unknown clearance stay distinct; an exact start never proves a missing endpoint. Upgrade/repeat/round-trip and transactional unsafe downgrade are tested on owned PostGIS.
- Existing history summary reads retain the seven-query budget. SQL/Python source-date/duration/export rules agree. Assumed two-hour intervals are limited to exact supported instants without sourced closure and excluded from observed durations; demonstrations add no real occurrences.
- Final focused repeats pass 19 endpoint/history checks and 52 output/E1 checks, including the new preflight/apply geometry-disagreement case and removal of presentation-specific reporter roles. These overlap earlier batches; the distinct total is 434.
- Concurrent/repeated output commands reuse identities, cannot reactivate deactivated demos, preserve completed immutable extraction, and roll back partial lifecycle/evaluation writes on conflicts.

## Frontend verification

The broad production-browser run passes 43 checks with three intentional skips; its two lifecycle failures came from a test using an administrator session on the commuter map. Correcting the fixture to inspect each screen with its intended role passes all eight changed-workflow checks. The final rerun after history Retry/source-date fixes passes all 12 changed-workflow/offline checks: 45 distinct project checks pass in total. Existing article evidence, filters/paging/focus, queue membership, keyboard/touch, 320 px layouts, map inspection, errors/recovery, dataset/export selection and deactivation-to-history are covered. Browser APIs use fictional fixture transport; backend lifecycle/geometry is independently exercised on disposable PostGIS. No hosted acceptance is implied.

TypeScript and focused changed-module lint pass. Existing unrelated diagnostics remain in `adminApi.ts` (5), `useFloodZonesLayer.ts` (13), and `routingApi.ts` (4, previously 5); the existing popup has none. Comparison against HEAD finds no new diagnostic signatures in these legacy files. No new dependency is introduced.

The first broad dev-server browser attempt encountered page-loading timeouts and was interrupted after the user changed the presentation requirement. Its screenshots with the removed notice are superseded. Final acceptance uses the production build, and the latest tests explicitly assert the label is absent.

## Operation and release boundaries

See the [operator guide](../../guides/historical-news-preparation.md#phase-1--saved-output-materialization-and-reading). `materialize_news_historical_outputs.py` has separately authenticated read-only preflight and apply modes and never invokes inference. Phase 1 apply is disposable/local-only; no shared output release is authorized or qualified. Saved native-reader context independently selects saved evidence, leaving scheduled RSS processing unchanged.

Phase 2 still must qualify/package the actual Linux/one-CPU/3-GiB worker and assets, exact cloud target/output policy and approved migrations, execute the real frozen September inputs, inspect positive/unresolved real outputs and complete hosted desktop/mobile/deactivation/history rehearsal. Quirino/Guazon is the primary candidate; Gov. Pascual needs independent qualification. No deployment, commit or push is included here.


## Reviewed screenshots

All images contain fictional fixtures and preserve the existing badge/modal presentation. The demonstration label is absent. Mobile evidence/history checks include 320 px; public popup uses the configured mobile device viewport.

| View | Desktop | Mobile |
|---|---|---|
| Saved native evidence | [Desktop](native-evidence-desktop.png) | [Mobile](native-evidence-mobile.png) |
| Unified history (latest) | [Desktop](history-unified-desktop.png) | [Mobile](history-unified-mobile.png) |
| Public map popup | [Desktop](public-map-desktop.png) | [Mobile](public-map-mobile.png) |
| Spatial Operations details | [Desktop](spatial-details-desktop.png) | [Mobile](spatial-details-mobile.png) |

The final screenshots supersede earlier notice-bearing images. Only owned test databases were created and removed. The frozen manifest and its four bound documents verify unchanged. No new package, SQLAlchemy model, shared migration, cloud output, real inference, commit or push occurred. Earlier E0/E1 reports remain preserved as evidence of their original checkpoints.


## Unified history amendment

The user clarified that Flood Events already serves as the history view. The added Historical dataset selector is removed from both tabs and both device layouts. The existing status/date/location filters, records, maps/heatmaps, analytics and exports use unified history. Obsolete `dataset_id` URL parameters are removed while retaining `event_id`; native-evidence links address the event directly. Internal provenance, dataset-aware backend operations and routing/count semantics are unchanged. The preference is recorded in repository `AGENTS.md`.

TypeScript and focused lint pass. Focused desktop/mobile fixture checks verify absence of the selector, no hidden dataset filtering on record/map/export requests, event inspection and Retry, reload/deep-link preservation and 320 px overflow. Existing history analytics/filters/mobile map controls are included. The final focused desktop/mobile rerun passes seven checks, with one intentional desktop skip for the mobile-only view switcher. An initial existing desktop analytics check timed out during cold development-page loading; it passes on the compiled-page rerun. The aggregate retains both the original Phase 1 checkpoint and this subsequent amendment. No production build, backend test run or database mutation was needed for this control removal; the original Phase 1 checks above remain their own historical checkpoint.

Reviewed latest screenshots: [Desktop unified history](history-unified-desktop.png) · [320 px mobile unified history](history-unified-mobile.png). Earlier `dataset-history-*.png` files are preserved as the superseded acceptance snapshot.
