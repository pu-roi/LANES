# Phase 36: Automatic source-alert publication and evidence lifecycle

> **Last Updated:** October 05, 2026, 7:08 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Implemented locally; final verification checkpoint recorded below. Operational zones and production release remain gated.

Automatic source-labeled **text-only news alerts**, atomic append-only decisions, supported observation refresh, matched clearance and two-hour evidence expiry are implemented locally. Read-time expiry becomes **Unconfirmed** even before maintenance; the default current feed retains it for 24 hours after expiry (configurable 1–72 hours), while safe historical detail remains available. Staff correction/defer/reject/reopen/clearance controls and desktop/mobile public-map News alerts are connected. Operational flood-zone activation/routing remains blocked by missing verified current affected polygons; OSM/NOAH/community boundaries remain placement evidence. No live deployment, paid provider request, new schema/dependency or normal/cloud database migration occurred.

## Delivered contract

`news_pipeline_service.py` explicitly processes saved article evidence, seeds eligible completed claims, independently evaluates bounded queued work, then calls atomic publication/expiry. Standalone seed/evaluate remains separate and creates no decisions. Discovery/collection is not silently coupled; no application pipeline command was run against normal/cloud data.

Publication rechecks immutable input/claim hashes, current pipeline/audit policy identity, approved publisher/URL, body-grounded place/status/time, twelve-hour publication admission and two-hour observation eligibility. Unknown depth/access remains unknown. No artificial citizen report, verified event, guessed polygon or routing zone is created. Each decision and existing AuditLog append shares its caller's transaction; failures roll back the case revision too.

Transaction-scoped advisory locks serialize UUID and exact qualified incident identity before case locks. Exact retries return the existing outcome without refreshing expiry; altered request identity or stale revision returns 409. Same-article, explicitly body-supported qualified sections with a genuinely newer observation can refresh a stable alert within a twelve-hour continuity bound. Immutable source bindings stay on their original cases. Ambiguous/mismatched/different-article clearance cannot withdraw another incident. Historical matched clearance and newer wet observations survive later reopen/reject/defer; older wet evidence cannot replace either newer observation history. Wet observations at or before matched clearance cannot become Active again. Staff preview and final correction share continuity/supersession checks; an evaluation already consumed by another case cannot create a duplicate alert.

Public reads choose the latest decision before filtering. Expired evidence immediately projects Unconfirmed even if maintenance is delayed; the default feed retains it for 24 hours after expiry (1–72 configurable). Supported Cleared is retained from its clearance observation for the same finite interval. Historical detail remains safely available. Withdrawal removes only the case's eligibility; existing citizen/manual or other fresh independently supported coverage is preserved. Finite zone expiry is never cleared to resurrect unsupported routing coverage.

## Interface and privacy

Public `/news/alerts` and detail expose only safe source information/excerpts, observation/expiry and server status. Internal reasons, credentials, raw provider payloads and private actor notes are not public. Staff routes require active session and reports view/full read or full write permission. UUID/revision-guarded preview/save/history is connected through shared desktop/mobile `NewsDecisionControls`; drafts survive failed or uncertain responses.

Public map `NewsAlertsPanel` offers a desktop control and mobile entry/sheet. It displays text-only reported places, source, supported excerpt/depth/access, corrections and Active/Unconfirmed/Cleared. Current status is unavailable for offline/error/stale cached snapshots. Polling, focus/reconnect and safe SSE invalidation refresh backend projections. Existing citizen report and zone operations remain separate.

## Verification

The broad regression run passes **452 backend checks across 25 suites**. Separate freshly migrated disposable PostGIS runs pass **21 lifecycle checks** and **7 native read/actual JWT API checks**. The focused lifecycle/pipeline/API checkpoint passes 40 checks (21 native plus 19 already represented in the broad regression); do not add those overlapping 19 or the earlier 449-check checkpoint to the current total. **16 desktop/mobile Playwright checks pass** with mocked API/session responses: eight public source-alert checks, four staff decision checks and four existing Select/location-filter/Active Zone regressions. Final TypeScript, scoped ESLint, Python compilation and `git diff --check` pass. The staff browser checks exposed an off-screen shared Select menu; flipping/capping it to the visual viewport fixes access on desktop/mobile. Primary visual review of preserved public/staff desktop/mobile screenshots passes, including the evidence dropdown. Two repeated staff screenshot captures add no distinct functional test count. Physical mobile/PWA, developer acceptance and deployed provider availability remain unverified. Native tests use newly created guarded local PostGIS with full existing migration upgrade to `d7e4b9a21c60`; providers and browser API/session responses are deterministic mocks. Production credentials/model availability, live fees, cloud migration, deployment and physical mobile/PWA acceptance are not claimed.

## Pre-push checkpoint

**Pre-push documentation checkpoint (October 05, 2026, 7:08 PM, Asia/Manila):** Senior-planner re-audit confirms **452 broad backend checks, 28 native PostGIS/actual JWT API checks and 16 distinct mocked desktop/mobile browser checks**, with final TypeScript/scoped lint, Python compilation, diff checks and primary screenshot review passed. Locally delivered source alerts, independent auditing, qualified refresh/clearance, two-hour Unconfirmed expiry, finite retention and F6/F7 interfaces are synchronized with current code. Operational flood-zone/routing activation, broader coverage, physical PWA/developer acceptance and deployment remain open. Existing approved migration head is `d7e4b9a21c60`; no new model/dependency/migration, paid provider call or normal/cloud DB write. User-authorized commit/push to `roi-branch` is the following Git step; this checkpoint does not claim push success. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Documentation audit

All eight authoritative records were audited; seven received current-state updates and `decisions.md` remains unchanged because the slice implements accepted lifecycle decisions without a new architectural pivot. Seventeen current/linked documents are synchronized and indexed, with Roi attribution and the October 05, 2026, 7:02 PM Asia/Manila timestamp. All 516 local targets and 157 heading anchors resolve. The pre-existing missing system-documentation API section heading was restored. Historical verification entries remain intact; source-alert delivery is separate from unfinished operational activation.

## Remaining work

Verified current operational affected polygons/width provenance, gated operational activation and linked-zone contributor/public interfaces remain open. Community administrative polygons and disconnected modeled NOAH road fragments are insufficient to establish currently flooded operational extent. Broader boundary/asset coverage, matching API/evaluator deployment, staging RSS-to-public acceptance, physical PWA/manual acceptance and optional duration training remain separate gates.

[Operator guide](../guides/news-publication-lifecycle.md), [backend contract](../plans/news-publication-readiness-plan.md), [frontend plan](../plans/news-publication-review-frontend-plan.md).
