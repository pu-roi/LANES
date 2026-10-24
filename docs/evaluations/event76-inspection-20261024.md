# Event 76 detail inspection 503 — confirmed investigation

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). October 24, 2026, Asia/Manila. **Original investigation: confirmed. Repair now deployed; protected-branch/trigger integration pending below.** This investigation performed protected GETs, read-only SQL, cloud log/configuration reads and Git remote inspection. It changed no application code, deployment traffic, trigger settings or database records.

## Endpoint-specific root cause

`GET /api/v1/admin/flood-events/76/inspection` returns 503 on both serving `lanes-api-reader-recovery-20261024-v1` and retained v30. On both revisions, the history list returns 200 with one event and News Intelligence returns 200 with three results. The current serving revision/image is still the accepted reader-recovery release; no later automatic build replaced it.

Cloud logs on that revision report `psycopg.errors.InvalidParameterValue: cannot get array length of a scalar`. `history_overview` in `backend/app/services/spatial_browse_service.py` calls `jsonb_array_length` directly on both report and zone media, then wraps the aggregate with `coalesce`. Zone 76 has JSON `null` in `media_urls`, not SQL NULL or an array. PostgreSQL raises before the outer coalesce can supply zero; the staff read wrapper catches the SQLAlchemy error and returns the generic 503. Event 76 exists, has no attached report rows, and its zone's safe type-guarded photo count is zero. This represents the valid optional no-photo case, not missing flood data or a Gemini failure.

Prior hosted history acceptance verified the card/list/map and exclusion of presentation events, but did not open event 76's detail modal. The new reader canary covers news results/details/articles/collection, not this history-inspection route. Existing inspection tests do not establish coverage of this actual persisted JSON-null case. That coverage gap allowed the separate reader recovery to pass without detecting this older detail bug.

## Git / CI/CD findings

- Live backend: `lanes-api-reader-recovery-20261024-v1`, 100% traffic; packaged reader image SHA-256 `48c3dfc90a1fd1c8022699c28061666a7b69a039cc235f60a34f029bfcdfb1c4`.
- Cloud Build backend trigger is still deliberately disabled after the previous outage; its branch pattern remains `^main$`.
- Verified remote `main`: `326bc083bf603587a02c70d6195cfcddcf449905`; latest recorded automatic build `b49a73e8-be63-4166-b85b-fc74ae1dee56` came from that commit before reader recovery.
- Verified remote `roi-branch`: `689a6a4eb3cc970d0a5df0a724591bc767254b27`. Both remote branches lack the new checked-deployer file and retain the old deployment path. The reader recovery source changes remain in the local working tree; they are not yet committed/pushed/merged.
- No `.github/workflows` directory exists in this checkout. Backend automatic deployment is provided by the external Google Cloud Build trigger, not a GitHub Actions workflow in the repository.

A future merge will not trigger backend deployment while that trigger remains disabled. Restoring CI/CD requires integrating the reviewed repair into `main` before enabling the trigger. Enabling it against the old configuration would risk repeating the missing-reader outage; enabling it alone would not repair event 76's photo-count query.

## Required follow-up

1. Make the media-count query type-safe for supported arrays and both absent-media representations (SQL NULL and JSON null), without changing flood data/schema or inventing photos.
2. Add disposable-PostGIS coverage for both report and zone media, including absent media, empty arrays and real arrays; retain a visible diagnostic policy for malformed non-array values.
3. Extend protected release/hosted desktop/mobile checks to open event details and verify inspection collections, while retaining the existing news-reader gates.
4. Build a matching candidate, verify event 76 and preserved news/zones/history, then promote through protected checks.
5. Commit/push the reviewed repair on the feature branch, merge through the protected `main` workflow, verify the deployed build configuration and only then re-enable automatic backend deployment.

No reset, source reprocessing, NER, Gemini or token-count request is required. Private logs, protected endpoint comparisons, media-type results and build-state evidence are retained in ignored `data/event76-inspection-investigation-20261024/`.

## Repair and protected manual release — October 24, 2:05 AM

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). `media_array_length` now applies `nullif(column, 'null'::jsonb)` before `jsonb_array_length` for both report and zone aggregates. SQL NULL, JSON null and empty arrays produce zero; populated arrays count normally. Invalid strings, numbers, booleans and objects still raise visibly. Existing deleted-report exclusion, staff access and bounded response contracts remain unchanged. No database row was normalized or edited.

Required disposable PostGIS testing owns a fresh isolated container/database, runs fresh and repeated upgrades to the existing migration head, and fails if test configuration is absent. Cloud Build runs this gate before publishing/migrating/deploying. The protected canary checks up to three genuine history events and all five paginated evidence collections against read-only database expectations, independent of the broken baseline inspection. Existing news checks remain required. A candidate or concurrent-traffic failure prevents promotion.

- Frozen Linux runtime: **323 passed, one repository-only skip**; source-only check passed locally within **36 local passes**.
- Mandatory disposable PostGIS: **18 passed**, including authenticated no-report/JSON-null-zone HTTP 200/media_count 0 and unauthorized/commuter rejection; fresh/repeated migration head passed.
- Responsive fixture interaction: **two passed**; actual hosted desktop/mobile opened event 76, loaded collections, scrolled and focused its zone on the map, all HTTP 200.
- Zero-traffic preview passed, then `lanes-api-history-details-20261024-v1` passed the release-specific protected job and received serving traffic. Repeated serving UI and protected checks passed; all 13 protected table fingerprints and the manual-worker specification are unchanged.
- Immutable API image: `asia-east1-docker.pkg.dev/lanes-project-508809/lanes/lanes-api@sha256:e105f666a0d164d7d31f769c90c65e0af18466d9b16a23e1449fbb5290e44bf5`.
- Packaged reader retains canonical SHA-256 `d6676e09e364d79b509c5dce0bcabc112ce359a41f247314bcfadbca417b1270`; correction 388 still supplies exactly three observations. No inference/provider/count calls, UI/schema/dependency changes or seeding.

Initial test runs exposed fixture setup/QA locator errors and an incorrectly encoded JSON-null comparison; these were corrected before the passing frozen image. The final implementation uses a static typed SQL literal, not a JSON-encoded string or user SQL. Malformed media remains an error.

**Integration pending:** scoped release checkout excludes four unrelated frontend edits. Backend trigger remains disabled until the reviewed repair is merged into `main`; publication and one exact merged-commit build are required before CI/CD completion. Preserve recovery reader revision/v30, private pre/post configurations, fingerprints and tests under ignored `data/history-details-repair-20261024/`. No reset or article replay is needed for rollback.

## Completed publication and restored CI/CD

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). October 24, 2026, 02:21 AM Asia/Manila.

PR [#142](https://github.com/pu-roi/LANES/pull/142) merged reviewed head `b88dcd6e4a015163ae6e5c5a7a8859c42e965d63` into `main` as `8c33ae04b071bdf587b4b72e98289de5f77db583`. The existing `^main$` trigger was restored only after that exact tree was verified. Controlled build `d52b144e-2809-4f3c-b941-5d378c21bc33` passed all seven stages and serves `lanes-api-build-d52b144e-2809-4f3c-b941-5d378c21bc33` at 100% traffic. Its protected canary confirms correction 388 (three observations) and event 76 with all five evidence collections. Cloud tests: 323 passed/one repository-only skip, required PostGIS 18 passed plus repeated migration; no new schema migration.

Final hosted desktop/mobile News Intelligence evidence/scrolling, real history detail/collections/map focus, active-zone details and public-map popups all pass. Direct history, analytics and JSON exports contain only genuine event 76; active zones remain 77–79. All 13 protected fingerprints, manual-worker specification, stopped 42-attempt ledger (US$0.7524937), expiry OFF, paused news, inert old seed and four unrelated frontend edits are unchanged. No NER, Gemini, token counts, seeding or database cleanup occurred.

Immutable safe receipt bundle: `gs://lanes-storage/private/history-detail-repair/20261024/8c33ae04b071bdf587b4b72e98289de5f77db583/`. Recovery configuration and original worker/data snapshots remain private locally; the accepted manual revision and v30 are retained. Final records are published on roi-branch after the verified main deployment; the preceding pending integration text records its earlier checkpoint.

Final main-build image digest: `sha256:50f3d77568eff16e02f23d60cb8c5636b40bfc9c61ff4e5d5c7de8119ca34ea0`. Private receipt bundle generation `1792779653726778`, SHA-256 `4ce1a83ab1f20ed7bd38c3fddf427b02eadcf9d9f381c2b40ea45bbb39b50346`; conditional creation and stored MD5 verification passed. Full private build descriptor is retained locally.
