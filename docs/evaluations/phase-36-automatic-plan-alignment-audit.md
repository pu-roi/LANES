# Phase 36: Automatic Pipeline Plan Alignment Audit

> **Last Updated:** October 03, 2026, 2:15 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Scope:** Inspect recent committed reading changes and uncommitted monitoring/telemetry against the agreed automatic workflow, then isolate the unnecessary runtime native-PBF import. Static code/Git review, one backend import-boundary fix and focused offline regression checks; no production, database, dependency or security-policy changes.

## Conclusion

No evidence was found that the recent reading or monitoring work removed automatic ingestion or introduced mandatory per-claim staff approval. The automatic pipeline remains incomplete. The prior manual-first recommendation and serial frontend dependencies were inconsistent with the agreed goal; documentation was reconciled separately. Keep the implemented discovery, extraction, OSM evidence and inspection/monitoring work. The next implementation target remains their connection to operational NOAH/DRRMO placement and automatic publication/zone lifecycle.

## Reviewed work and findings

| Work | Evidence | Effect on original goal |
| --- | --- | --- |
| Saved RSS/manual input and durable extraction | `run_news_discovery.py` still invokes `process_saved_news`; the processor preserves immutable results, owned leases and retry outcomes. | Reusable automation foundation. Staff API access does not require a staff action for collector processing. |
| Committed reading UI (`d5df6a2`) | Added browsing, result/collection and presentation services read existing evidence. Presentation labels do not replace stored extraction or publish zones. | Inspection only; no new approval prerequisite. |
| Uncommitted F4b monitoring | Protected GET monitoring/history reads; optional discovery `actor_id` distinguishes staff from an unattended collector. Four additive telemetry tables record attempts. | Supports unattended operation; requires migration before deploying instrumented collection. |
| Fallback refactor | `FallbackInput` captures original inputs before telemetry commits; lookup still performs the existing search/feed/retrieval/assessment sequence. | No new manual approval rule. Live alternate-body recovery remains separately unverified. |
| Activation prototype | `news_auto_ingestion_service.py` retains gated automatic report/event/zone creation. `git grep` at `e9c81ae` shows no caller in application/collector code beyond definitions; current code likewise has no production caller. | Existing integration gap, not removal by reading/monitoring work. |
| Runtime spatial connection | Shared extraction uses `mode="rules_only"` and attaches `RoadPlacementEvidence` from the OSM provider. NOAH ranking imports appear in audit scripts; the operational provider does not invoke them. | OSM evidence is connected, operational NOAH/DRRMO section ranking is unfinished. Pasig history already supports the legacy location-ranking prototype. |
| Preview geometry | `NationwideGeometryService` returns `is_auto_approvable=False` and `requires_staff_edit=True`; activation requires `verified_segment`. Its flags and the activation/hybrid/NOAH services and collector script are unchanged from `e9c81ae`. | All legacy previews fail zone eligibility. A verified placement/lifecycle path must replace this temporary limitation for eligible claims; retaining it as permanent staff approval would contradict the goal. |
| Coverage | OSM provider returns unresolved when the claim includes a barangay but the catalog lacks a valid barangay boundary. | Known placement limitation. Preserve uncertainty and eligible broad alerts; implement supported spatial resolution before claiming automatic bounded zones. |

## Deployment dependency

`begin_discovery` now inserts and commits a telemetry run before feed collection. Missing telemetry tables or a telemetry-storage failure therefore stops that attempt. Apply approved revision `c5a7e9d2104f` before deploying this code to API and collector runtimes. A passing prior local migration round-trip is not evidence of production rollout. Do not report monitoring as purely independent of collection availability.

## Verification on October 3

Ran discovery, durable processing, telemetry, auto-ingestion and hybrid-extraction suites: **81 passed, 26 failed**. Every failure in the concise diagnostic run reports `ImportError: DLL load failed while importing _osmium: An Application Control policy has blocked this file.` The initial sandbox run also could not create a pytest temporary directory; normal-access reruns removed that temporary-directory error but retained the Windows native-module block. This run cannot establish a passing collection/OSM regression result. See [BUG-084](../others/bug-log.md#bug-084-windows-application-control-blocks-osmium-during-pipeline-verification).

Read-only Windows event inspection subsequently confirmed Code Integrity events 3033/3077 at 2:08:46 AM: Codex's bundled Python attempted to load `osmium/_osmium.cp312-win_amd64.pyd`, and Windows rejected its Enterprise signing level under policy `0283ac0f-fff1-49ae-ada1-8a933130cad6`. Why that trust decision differs from the earlier successful verification remains unknown.

No security policy was changed or bypassed. Prior 214-pass verification remains historical evidence, not today's result. No browser, fresh RSS-to-public-zone acceptance, production migration or deployment was exercised in this audit.

## Required next acceptance

### Verification recovery: runtime dependency isolation

The subsequent fix in `article_road_match_service.py` defers native PBF import/handler construction to `load_bounded_osm_roads`. Runtime catalog matching never reads PBF and retains the same pure road graph and Shapely geometry routines. The existing PBF parser behavior and import failures remain explicit when raw files are requested. No blocked binary is executed, and Windows security remains unchanged.

Post-fix result: **140 passed** across the original five suites plus runtime placement, road matching and NOAH ranking. Added a fresh-process regression that rejects native imports and verifies catalog-provider import succeeds while PBF reading still requires the native reader. All 26 formerly failing checks pass. This verifies the runtime fix, not raw-PBF tools, live automatic map publication or production deployment. No dependency or schema changes.

- Fresh RSS evidence reaches the automatic eligibility/publication path without a staff action.
- Operational ranking uses bounded OSM sections, exact NOAH vector context and place-matched Pasig DRRMO history, preserving ties and missing coverage.
- Eligible bounded claims create/link expiring zones; eligible unresolved claims show source-labeled alerts without routing effects.
- Conflicting/incomplete claims use the exception path; retry, syndication, correction/clearance and expiry preserve identity and existing report/routing behavior.
- Runtime OSM regressions now pass. Raw-PBF tooling still requires a policy-accepted native dependency; controlled end-to-end and desktop/mobile acceptance remain open.
