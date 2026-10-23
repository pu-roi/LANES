# Authorized cloud flood-data reset

> **Last Updated:** October 22, 2026, 6:58 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). The user explicitly approved clearing all flood records, including citizen reports, while preserving source articles, accounts and community posts. This intentionally supersedes the earlier Part 2A requirement to preserve those flood records for this one maintenance operation. Earlier evaluation receipts remain historical evidence, not the current database state.

## Result

The reset committed on October 22, 2026 at approximately 6:49 PM Asia/Manila against the verified Cloud SQL `lanes` database at approved head `f1a9c7e2b604`. All 14 targeted flood/news-output tables are empty. Cleared 56 events, 56 zones, 43 reports, 43 surveys, 39 flood moderation outcomes, 125 event locations, 208 timeline entries and 244 extraction runs, plus 105 cases, 105 source bindings, 127 evaluations, 87 publication decisions and six decision/zone links. The report-location table was already empty. Removed 21 matching report-status notifications; six unrelated notifications remain.

All 37 community posts remain, including one previously archived post. Detached 34 `flood_report_id` links with a direct SQL update that leaves timestamps/content/media/location/moderation fields unchanged. Preserved eight comments, 14 post reactions, one edit-history entry and three community-post moderation records. The public community API still returns 36 visible posts; this does not imply that the archived post was removed.

Preserved all eight accounts, eight profiles, seven addresses, four roles, seven saved places and one OTP record, along with 174 article rows, 224 saved article versions, 77 feed-entry links and 13 feed checkpoints. Discovery telemetry (838 runs / 8,719 feed runs at the maintenance baseline), 642 audit logs, visitor records, configuration values except the intended pause flags, spatial reference data and all external model/training/OSM/NOAH assets remain. Source bodies and article review states are unchanged. Media objects/files were not deleted.

## Recovery and transaction checks

Two private custom-format PostgreSQL backups are retained in `data/flood-reset-20261022/`; Windows ACL inheritance is restricted to the current user and SYSTEM. The final archive is `final-242cb564f3d146acb6c9985790c3568b.dump`, SHA256 `3b96f2531b2391236b2ccb22476215a1c8dbb09ad464643d46a428837b643de5`. Both backups were restored to separate owned disposable PostGIS databases before their corresponding rehearsals. Every restored table's content fingerprint and sequence state matches the cloud snapshot.

Cloud SQL and local PostgreSQL 15 patch versions deparse array casts differently. Cross-environment qualification therefore compares exact row/sequence fingerprints, named constraint/trigger identities and FK definitions; it does not claim byte-identical deparsed CHECK text. Each cleanup separately proves its own complete constraint and trigger definitions unchanged before/after.

The reusable backend maintenance service uses a reviewed target identity and exact snapshot, locks the complete table set, detaches posts first and deletes in explicit FK order. Only the four named immutable/finalized news deletion triggers are temporarily disabled inside the transaction; they are restored before commit. Foreign keys and other triggers remain enabled. No sequence reset, blanket cascade, schema migration or new dependency. All pre-existing row fingerprints outside the selected deletion set match immediately after commit and again after hosted verification.

Rehearsals cover forced mid-delete rollback (including trigger/link/notification restoration), wrong target, changed snapshot, full successful clear, preserved-content fingerprints and an idempotent repeat. Twelve focused pytest checks pass for preservation, residual targets, schema/sequence changes and dangling links. The first cross-patch textual-comparison failure is retained; the correction did not bypass any row-preservation check.

## Hosted verification and operating state

The existing API revision/image/template and serving traffic are unchanged. A short maintenance window restricted public API ingress and paused both scheduled workers; public ingress was restored to `all` at 6:50 PM. Zone expiry is enabled again. The news scheduler is **PAUSED**, and `news_collection_enabled`, `news_processing_enabled` and `news_publication_enabled` remain **false**. The manual historical seed job retains its no-op command. Configured publishers and other settings were preserved.

Actual hosted APIs confirm empty results, events, reports, zones, flood moderation, history maps, analytics, exports and public news alerts. Collection/articles agree on 174 records with no extraction run; source versions remain in SQL. Existing protected endpoints still reject unauthenticated access. The SSE active-flood snapshot is `[]`.

Actual Chromium desktop (1440 px) and mobile (390 px) checks cover eight behaviors per viewport: empty Flooded Areas, 174 preserved articles in Collection status, empty history cards, zero analytics, downloaded empty JSON export, empty flood moderation, empty active zones and empty spatial history. No response mocking or UI edits. The initial spatial test used a tab locator where the existing control is a button; corrected targeted checks pass and both attempts are retained privately.

## Recovery and next work

Do not run the destructive reset service as part of API startup, migrations or scheduling. Its execution controller and sensitive backups/receipts stay private. Public APIs, response types and frontend source were not changed. The implementation is `backend/app/services/flood_data_reset.py`, with guard tests in `backend/tests/test_flood_data_reset.py`.

For recovery, stop writers, authenticate the final backup hash and restore it to a separate recovery database first. Restore the approved flood dependency set, matching community-report links and report notices without overwriting newer unrelated account/community data. Restore prior configuration only through a deliberate recovery operation. Keep the public serving revision and all backup evidence available; do not automatically resume old processing.

Existing raw NER/rules runs and their old live run IDs are now intentionally absent. Prior Part 2A processing authorities and live run references must not be reused. Future NER → Gemini qualification must create fresh runs from the retained full article inputs under new manifests, then verify and archive qualifying historical outputs. No real Gemini request or retraining occurred during this reset. Previously cached browser/offline flood data requires a successful refresh/sync; offline devices cannot be remotely guaranteed cleared.
