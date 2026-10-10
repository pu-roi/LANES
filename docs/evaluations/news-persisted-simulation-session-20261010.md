# Persisted News Simulation Session — October 10, 2026

Author: [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Root cause and correction

The earlier port-3000 simulation redirected only `/news/simulation`; public/Admin zones, auth and SSE remained connected to normal data. Active-style preview geometry never created a `FloodAvoidanceZone`.

The explicit **persisted** mode now runs at port 3001 and sends all API/auth/download/zone requests and both SSE streams to the guarded private backend on 8001. Both maps use the existing `/reports/active-zones` and shared renderer. No placement overlay is enabled in this mode. Separate browser origins preserve normal tokens/offline state; normal port-3000 and production routing remain unchanged. Legacy additive mode remains supported separately.

The private server now aligns zone reads, Admin paginated active/archived filters, linked news details, public news, Spatial Review, predictions and routing/SSE eligibility to one frozen clock. Normal database readers retain PostgreSQL time. It accepts port-3001 CORS and omits wall-time retention during historical replay. Startup runs no collector, auditor or activation. Both configured/bound engines must pass the loopback `lanes_news_test` guard. No dependency/model/migration changes.

Relevant files: frontend `src/lib/localNewsSimulation.ts`, `apiClient.ts`, `sse.ts`, `next.config.ts`, `tsconfig.json` (private generated types); both `start-persisted-news-simulation.ps1` launchers; backend `scripts/serve_local_news_replay.py`, `app/crud/report.py`; session/launcher/lifecycle tests; `.gitignore`.

## Real article evidence and policy distinctions

The live [Daily Tribune article](https://tribune.net.ph/2026/09/24/minor-flooding-hits-some-metro-areas) was rechecked. It attributes the report to MMDA. `unapproved_article_source` describes the app's publisher/feed registry, not article reliability; Daily Tribune is absent from that registry.

Visible publication is September 25, 2026, 4:41 AM PHT. Thursday's Boni observation is September 24 at 4:34 PM. At the preserved September 25 4:42 AM replay clock, this evidence is **12 hours 8 minutes old**, beyond the current 12-hour admission window and two-hour default observation lifetime. Age is relative to the replay clock, not today's date. The URL date does not replace visible publication metadata. These are application policies and were not relaxed.

The source also says all vehicle types could pass, a separate existing avoidance-activation restriction. The corner reference does not resolve competing affected road sections. No synthetic article was added to this operator replay.

## Verification

- **18 backend unit checks passed:** private-target guards, shared clocks, historical chronology and routing policy.
- **9 native PostGIS integration checks passed** on a fresh disposable lifecycle database: persisted activation/public/Admin identity and expiry; six evidence activation guards; two RSS → extraction → fixture audit → automatic activation → API cases. Test fixtures are separate from the real-article demonstration. Existing Alembic migrations applied successfully to `d7e4b9a21c60`; no migration changed.
- **14 frontend session-contract checks passed:** seven cases in each desktop/mobile project; actual resolver/client in isolated contexts, not browser rendering checks.
- **4 Chromium browser workflows passed on port 3001:** public Active core/halo/details and Admin mixed review inspection, desktop/mobile. HTTP/geometry fixtures; no successful Boni activation implied.
- TypeScript passed. Resolver/SSE/new-test lint passed. Legacy touched client/config full lint still reports existing `any`, `@ts-ignore`, unused-catch and `prefer-const` issues; no repository-wide lint pass claimed.
- Original captured-article pipeline replay completed in `lanes_news_test`: zero collected candidates, run 57 blocked by `unapproved_article_source`, zero provider calls, zero new zones. Total remains one archived earlier simulation zone. Original flood facts/dates/approvals unchanged.
- Live frontend proxy: public IDs `[]`, Admin active IDs `[]`, private login, five saved article locations, direct SSE initial event and CORS passed. No zone writes by HTTP checks.

## Docker recovery

Docker Desktop 4.91.0 failed on Ingest then Secrets Engine sockets. After verified shutdown, runtime directories were moved to sibling backups. First restart still failed at Secrets Engine; a second stopped-state backup/restart recovered it. Both `lanes_postgis_db` and `lanes_valhalla` were observed running. Backups end in `20261010-013619` and `20261010-013759` under the existing user-local runtime directories. No factory reset, volume deletion, WSL unregister, app update or diagnostic upload. This is an observed local workaround, not a universal repair.

## Review boundary

Use `http://127.0.0.1:3001/map` and `/admin/map` with the existing private account. Boni remains ineligible for Active under current policy. Publisher enrollment, freshness/passability policy and real-article geometry require separate review; cross-article reconciliation remains outside this phase. No normal/cloud data writes by this correction. See [launch guide](../guides/local-news-replay.md).
