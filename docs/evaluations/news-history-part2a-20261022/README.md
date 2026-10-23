# Part 2A — Retained news history and general source inventory

**Status: implementation verified locally; shared batch application remains blocked. Overall Part 2A remains open.**

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Measured data

Database-enforced read-only checks resolve events 23, 59, 60, 61, 62 and 63 through retained publication links to original article versions/runs. Tribune events retain version 66; GMA events retain morning version 137, independently of corrected version 140. Occurrence days are September 24 and September 9; administrative October lifecycles remain unchanged. No shared row changed.

The inventory identifies 12 saved full-body articles, including article 47/version 140 for future processing, and 132 canonical training source articles/full-body hashes. Complete source captures resolve all training references; annotated passages and labels are not extraction output. Current selected publishers admit 99 for capture registration and retain 33 unresolved publisher outcomes. These are source-admission counts, not NER, NCR or geometry acceptance counts.

## Implementation

- Retained legacy decision/source links and native import run/group references supply separate article evidence in authenticated, paginated event inspection. Full article/extraction inspection follows the exact saved run/version.
- News-only, user-only, mixed and unknown origins remain distinguishable. Citizen submissions retain Reports and their own metrics; no fake citizen reports are created.
- Shared SQL/Python occurrence, filter and duration rules separate news source dates from administrative actions. Existing lifecycle timestamps are not rewritten.
- General packages accept bounded non-September selections; frozen E0 evidence remains unchanged. Compatible completed native runs are reusable. Training capture registration is pinned, conflict-safe and transactional; new articles use the existing local_update scheduled exclusion. Existing articles remain unchanged.
- New archives prefer source clearance, otherwise the agreed two-hour exact-time assumption or next-day 00:00 Philippine endpoint for date-only observations. Assumptions never enter observed-duration statistics. Unknown/contradictory dates and geometry/identity disagreements stay unresolved.
- Cross-article reuse requires supported observation identity and equal qualified geometry. Immutable extraction remains intact. Native-only groups remain inspectable without invented scalar claims.

## Verification

The final combined backend run passed **374 tests**, including disposable PostGIS fresh migrations, the 1,000/10,000-record seven-query card budget, retained legacy/native evidence, source suppression, source/version tampering, read-only preflight, archive reuse across concurrent article sessions, rollback, date-only/exact assumptions, general dataset inspection, SQL/Python/export parity, authorization and ordinary routing. Mixed-source incidents preserve their original timing when evidence is attached or a citizen report is soft-deleted. An observation match lock serializes cross-article lookup before competing archive inserts.

The previously reproduced September 9 failures are resolved: a list observation retains its explicit scoped-evidence marker; the narrative continuation helper cannot copy a neighbour road's clock into an independent clause. **150 extraction/replay tests** passed before the combined run; those cases are included in the 374 total. No saved extraction or trained weights were modified.

Production Playwright: **19 passed, one intentional skip** (desktop copy of the mobile-only switcher). Suites: `news-history-evidence`, `flood-history`, `historical-news-phase1` and `historical-offline-routing`, both configured Chromium projects. Coverage includes 320 px, keyboard/Enter/Escape navigation, exact original article inspection, separate citizen Reports, Retry recovery, map/list controls, both active maps, authenticated deactivation, retained history and offline eligibility/cache failures. [Desktop](desktop-event-details.png) and [320 px mobile](mobile320-event-details.png) screenshots use fictional transport fixtures, not shared seeded outputs.

TypeScript, focused ESLint and the normal dotenvx production build pass. Build/browser serving used `.next-news-simulation` and port 3002. An initial browser attempt caught a Windows text-encoding error (repaired); another direct build omitted the project's environment loader and was replaced by the normal build command. Earlier failing test fixtures were corrected to retain activation and expiry as separate immutable decisions. Final verification uses the actual constraints, not disabled triggers.

The six-event read-only audit passes on the shared predecessor without a schema change. Frozen original E0 reconstruction passes unchanged. Private final package: `saved-package-v3`; shared processing status is **blocked**, not approved for apply. See [structured verification](summary.json).

Private input packages, source bodies, database pins and per-source receipts remain in ignored `data/news-history-part2a-20261022/`. Public documentation records aggregate evidence only.

## Remaining execution boundary

The shared processing preflight reports `historical_cloud_processing_not_qualified`, `historical_linux_amd64_required`, `historical_native_migration_required` and `historical_native_storage_incompatible`. The database remains at its audited predecessor; this Windows operator is not the qualified Linux worker. No shared registration, NER processing, output apply, migration, deployment, commit or push occurred. Part 2A adds no table/model/migration. Shared output authority remains a separately qualified, exactly reviewed step; E1 processing-only authority does not authorize archive writes.
