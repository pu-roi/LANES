# Automatic expiry control and fixed-deadline investigation

> **Last Updated:** October 10, 2026, 6:36 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Result and scope

Delivered locally on normal frontend **3000** / backend **8000**. Admin **System Settings → Evidence expiry → Enable automatic expiry** uses the existing shared Checkbox, configuration API, permission checks, revision conflict handling and settings audit. No SQLAlchemy model, migration or dependency changed. The shared cloud configuration was not changed; the scheduled cloud worker still requires a matching backend rollout. Developer acceptance and deployment remain pending.

- **Enabled (legacy default):** existing deadlines govern public/Admin visibility, routing and scheduled zone/news expiry. Per-depth durations remain 30–120 minutes, currently defaulting to 120.
- **Disabled:** existing active zones and published active news remain operational past their recorded deadlines. Public/Admin readers, routing, event metrics, related-zone candidates and existing contribution support follow the same policy. The news feed retains these active decisions past its ordinary expired-evidence retention window.
- Stored observation dates, original deadlines, excerpts, article title/link/publisher and geometry remain unchanged. Changing duration settings does not rewrite old deadlines.
- Manual deactivation, withdrawal and qualified clearance remain authoritative. Disabling expiry never restores already inactive zones or explicitly expired/withdrawn news decisions. New publication/approval/footprint admissions and research evidence freshness still require qualified evidence.
- Re-enabling applies the original deadlines immediately to readers; the next maintenance run ends overdue active records. Expiry means current conditions are unconfirmed, not observed dry.

Policy reads and expiry writes use the shared configuration lock. The zone batch reacquires it after each lifecycle commit so a newly saved pause cannot be bypassed by the remaining batch.

The flag is stored in the existing configuration JSON envelope, outside its legacy nested `settings` object. The new API still exposes it in typed settings and audits before/after values normally. Older strict-schema workers can read their known fields without an unknown-field failure, but **do not honor the toggle**. Matching API/worker versions are required; an old settings writer can also replace the envelope. No cloud deployment or shared policy save was performed during verification.

## What removed Boni

Read-only timeline investigation found cloud **Zone #23** automatically deactivated at **October 10, 6:00:29 PM Manila**: `evidence_expired` followed by `event_ended`. Its original source observation is September 24, **4:34 PM**, with a **6:34 PM** deadline that same day. Geometry and source evidence remain stored. The local, database-bound scenario clock did not control the other scheduled worker using the shared database and real clock. Its later runtime records also reported a worker failure; the completed zone deactivation is nevertheless recorded.

This supersedes the earlier 5:49 PM snapshot in the [Boni reconstruction evaluation](news-boni-corridor-reconstruction-20261010.md). Current normal public/Admin active IDs are **17–21**, not 23. This task does not recreate or reactivate Boni.

## Fixed timer versus machine learning

`configuration_service.evidence_deadline` calculates observation time plus configured per-depth minutes. `flood_event_service.expire_due_zones` checks active records with an elapsed `expires_at` deadline, without a Pasig city filter. News decision expiry runs independently through `news_publication_service.expire_case`; read-time queries also apply deadlines before maintenance.

`zone_prediction_service.predict_zone` resolves Pasig model coverage and calls `flood_subsidence_prediction_service.preview_subsidence`. This is a separate research duration estimate. It does not write zone deadlines or deactivate operational zones. Pausing the operational timer does not make historical evidence fresh for that research service.

## Files and connections

| Files | Responsibility |
|---|---|
| `backend/app/schemas/configuration.py`, `services/configuration_service.py` | Typed flag, legacy default, atomic audited persistence and shared SQL deadline predicates. |
| `backend/app/services/flood_event_service.py`, `news_publication_service.py` | Scheduled expiry pause; unchanged manual/clearance lifecycle; event/support consistency. |
| `backend/app/crud/report.py`, `services/flood_routing_policy.py`, `services/ors_service.py`, `services/merge_service.py`, `services/citizen_approval_service.py` | Consistent active-zone eligibility in maps, Admin, routing, zone matching and existing contribution support. |
| `backend/app/crud/news_publication_read.py`, `services/news_publication_read_service.py`, `services/news_zone_projection_service.py` | Current news feed, source-preserving popup details and retained Active projections while paused. |
| `frontend/src/features/admin/SystemSettingsPage.tsx`, `adminApi.ts` | Shared responsive setting control and typed API contract; Save/Revert and errors remain in the existing flow. |

## Verification

- **51** targeted configuration/projection/scenario tests pass.
- **186** native settings and publication lifecycle tests pass in fresh, disposable local PostGIS databases migrated to head. Tests use the actual configuration HTTP API, audit, publication/footprint services, public endpoint, Admin reader, routing, scheduled expiry and manual deactivation. Evidence fields, source geometry and original deadlines are preserved; paused active feed retention and no resurrection are checked. Qualified clearance is checked with expiry both enabled and disabled.
- **18 unique desktop/mobile settings scenarios** pass. Initial full run had 17 passes and a desktop navigation hydration timeout; that scenario passed on its focused rerun. Toggle save/reload/re-enable, permission denial, revision conflict, surfaced errors and narrow-screen overflow checks pass.
- Actual authenticated desktop/mobile browser reads on **localhost:3000** show the enabled toggle and 120-minute defaults. Screenshots were inspected. Active IDs remain 17–21; no shared configuration was saved. Ignored evidence: `data/news-replay/expiry-settings-live-check.json` and `expiry-settings-live-{desktop,mobile}.png`.
- TypeScript and settings-page ESLint pass. `adminApi.ts` retains five existing `no-explicit-any` violations; its scoped check with that rule disabled passes. Whitespace check passes.
- An additional legacy integration run produced **33 passes / 23 skips / one merge failure**: duplicate city location entries violate the event-location unique constraint during reviewed merge creation. That failure occurs after the candidate read, outside the changed expiry predicate. Its two newly created local fixture reports/posts were removed by exact IDs/time/ownership checks. Cloud data was not involved. This is not release-wide acceptance.

No deploy, push, global setting save or flood reactivation is claimed.
