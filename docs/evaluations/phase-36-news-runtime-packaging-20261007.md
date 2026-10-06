# Phase 36: News runtime packaging and release preparation

> **Last Updated:** October 07, 2026, 12:45 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Current follow-up

The subsequent [exact-source auditor repair](phase-36-auditor-evidence-options-20261007.md) supplies server-calculated evidence options and passes synthetic free-provider validation at both 60 seconds and the ordinary 20-second limit. The failed results below are historical. Matching deployment and real-article/map acceptance remain open.

## October 7 live timeout follow-up (earlier diagnosis)

The developer's first synthetic probe timed out with the existing 20-second
deadline. The CLI now accepts `--timeout-seconds` (1-120 seconds), propagated to
both the HTTP timeout and whole-response deadline. The regular worker retains
its existing 20-second default; no persistent/cloud setting changed. Invalid
limits make no provider request, and the exact `openrouter/free` guard remains.

**134 distinct focused checks pass** in this follow-up: 100 auditor/probe cases
and 34 evaluation-policy/pipeline-CLI cases. These overlap the earlier packaging
tests below; do not sum checkpoint totals. They verify custom timeout transport,
actual deadline cancellation, invalid limits, no paid fallback, historical
synthetic input and unchanged evidence rejection/current-publication gates.

The agent made one free synthetic retry at 60 seconds. It completed the provider
exchange but returned `probe_failed`, `outcome=invalid`,
`reason=audit_evidence_offset_mismatch`. The model's evidence positions failed
the exact source-substring check. No evidence gate was relaxed and no database
access/publication occurred. The next task is free-auditor evidence formatting
reliability, followed by successful grounded provider acceptance. Original timeout
cause is not proven by this retry. See the [official free-router limitations](https://openrouter.ai/docs/guides/routing/routers/free-router).

The image was rebuilt successfully after this code change, including the existing
asset-verification step. Follow-up manifest-list digest:
`sha256:eb1dd3348be86a88db59709ef7ca8733f7ac9f44de6067516e10712117480158`.
No dependency/model/migration, cloud write, deployment, commit or push changed.

## Initial packaging result and remaining acceptance

The local API/job image now includes the same bounded Metro Manila analytical
NOAH catalog as local placement. Docker verifies the OSM, qualified barangay,
NOAH and Pasig history assets before accepting a build. The final Linux image
build and network-disabled runtime verification succeed. **188 distinct focused
tests pass**, including native existing-migration/storage checks in a disposable
loopback PostGIS database, which was removed afterward.

Normal encrypted backend configuration selects `openrouter` / `openrouter/free`
and passes the new read-only configuration check. No live provider probe, cloud
migration, current-article publication, deployment, commit or push was performed
in this packaging checkpoint. Follow the [exact release checklist](../guides/news-zone-release-checklist.md)
for the single free synthetic probe, reviewed Git release, backend/frontend
rollouts and controlled current-article acceptance.

## Runtime bundle and code changes

- `backend/runtime_data/noah-placement` contains 897 unchanged gzip tiles:
  299 each for 5-, 25- and 100-year scenarios. Total compressed tile bytes:
  **89,708,051**. Bounds are `[120.9, 14.35, 121.14, 14.79]`; tile size is 0.02 degrees.
- Manifest SHA-256 is
  `cceb8c93d5441f14aad48808319a3d4cf3a87918ea8089dcb5efbf86c49940ce`.
  The manifest retains the original three source archive hashes, tile hashes,
  ODbL-1.0 license and Project NOAH/contributor attribution. The bundle README
  links the source/license. Original archives and the national dataset are not
  packaged. NOAH remains modeled susceptibility, never proof of current flooding.
- `.gitattributes` preserves raw manifest/gzip bytes across Windows and Linux.
  `NoahVectorCatalog` defaults to the versioned backend bundle locally; explicit
  `LANES_NEWS_NOAH_DIR` still overrides it. Docker sets that variable to
  `/data/noah-placement` and copies the existing runtime directory to `/data`.
- `scripts.package_news_noah_assets` verifies every source tile, copies only
  manifest-declared files into a new directory and verifies the resulting
  identity. Existing output directories are refused.
- `scripts.verify_news_runtime_assets` checks catalog identities, tile checksums,
  nonempty qualified boundaries and each boundary's parent containment, plus
  Pasig history availability. Invalid assets exit nonzero with a reason code.
  The Dockerfile runs it during build; operators can run it without a network.
- `scripts.check_news_auditor` checks settings without database/provider access.
  Explicit `--probe` makes one synthetic historical request using only the
  exact free router `openrouter/free`; other model/provider selections are
  refused. It cannot collect news or create publication/zone records.

No package, model, migration definition, UI component, endpoint or architectural
decision was added by this slice. The existing UI integration remains as recorded
in the [October 6 integration verification](phase-36-estimated-road-zone-integration-20261006.md).

## Verification

| Check | Result |
|---|---|
| Runtime bundle, NOAH builder, placement preview, estimated roads, spatial assets | 58 passed |
| Free-auditor check and independent claim-auditor regressions | 93 passed |
| Existing publication storage/migration checks in fresh local PostGIS | 37 passed |
| Final `backend/Dockerfile` Linux build | Passed, including build-time assets verification |
| Final image verifier using `--network none` | `assets_ok`, 897 tiles, 20 qualified barangays |
| Final image free-auditor module import / `.env*` exclusion | Passed; no environment files bundled |
| Normal dotenvx configuration check | `configuration_ok`, `provider_request_made=false` |

The 37 native checks cover existing full/repeated upgrades, publication
downgrade/re-upgrade and evidence preservation at head `d7e4b9a21c60`. The fresh
database was `lanes_publication_test_release_f9828090f6` on loopback, removed in
the harness's final cleanup. The normal/cloud database was not used.

Final local image tag: `lanes-news-release-check:20261007`.
OCI manifest-list digest:
`sha256:7dd31b9439d495901ec334c63a13e01da757ab4552a77ea248f8644e149dd283`.
This is a local build receipt, not a deployed Artifact Registry identity.

The runtime verifier reports OSM revision
`5edd1284a00003ed2d97ff7d500f02b58d7f53521864e149311628df3d338386:barangay-4b596be585945502fffd1ca9e14f282fb5a10e3b844c3ca2b21eda1a157894c2`,
barangay digest `4b596be585945502fffd1ca9e14f282fb5a10e3b844c3ca2b21eda1a157894c2`,
and history digest `e3fd9c5a1fc966ea017de89f061eb8e80a199a026c93f58fcab5d96379623e13`.
Twenty of thirty Pasig community boundaries remain qualified; packaging does
not expand that coverage or prove real-event placement accuracy.

## Cloud checkpoint and ordered next actions

The developer's manual Cloud Run settings were inspected read-only: both
`lanes-api` and `lanes-news-discovery` select `openrouter/free` through `openrouter`
and contain an OpenRouter key. No key value is recorded here. The deployed news
job still uses `--process`; local `cloudbuild.yaml` prepares `--pipeline` for
the future release. The last cloud schema read was `c5a7e9d2104f`.

1. Test one free synthetic AI response with the new probe. Treat rate limits,
   incompatible output and provider errors as unresolved acceptance.
2. Review/push `roi-branch`, then merge through the approved GitHub workflow.
   Cloud Build must successfully execute the existing migration before matching
   API/job images are accepted. Verify schema/image/asset/config identities.
3. Verify the separate Firebase App Hosting frontend rollout. Root Cloud Build
   deploys the backend; it does not establish frontend rollout success.
4. Run one controlled current-article pipeline execution, inspect per-claim
   outcomes and existing desktop/mobile map/routing/lifecycle behavior.
   No qualifying current article can validly mean no new zone.
5. Review the three-hour scheduler versus two-hour observation freshness and
   free-provider capacity; complete physical PWA acceptance separately.

## Docker startup interruption and recovery

During verification Docker Desktop failed to rename the Windows AF_UNIX
`sailor-ingest.sock`. The engine was unavailable and its Linux distro stopped.
The normal stop command failed. After stopping identified crashed Docker
processes, the two inspected zero-byte socket directories were preserved as
sibling backups and fresh runtime directories created. Docker then started;
engine 29.8.0, the original `lanes_postgis_db` and `lanes_valhalla` containers and
`lanes_lanes_db_data` volume were observed. No factory reset, WSL unregister or
persistent database removal occurred. Exact backup paths and the matching
[Docker issue report](https://github.com/docker/desktop-feedback/issues/554)
are linked in the release guide. A future recurrence remains possible.
