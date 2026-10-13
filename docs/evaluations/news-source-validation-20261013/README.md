# Credit-free source validation and map acceptance — October 13

> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Local end-to-end acceptance and production backend release verified. Historical positive replay is separate from current live reporting.

## Implementation


### Final production release from main

PR #134 is merged into **main 420b38fcfcade930389cd58679f0b96a609da40f**. Cloud Build **1ec804a4-356b-494a-809a-0ae15d4d5932 SUCCESS**: all ten steps succeed, 275 regression checks pass, existing migration job lanes-migration-pssn2 succeeds, and news execution lanes-news-discovery-ghn6x succeeds at **4:33:42 PM PHT**. Image digest: sha256:702a131ae786da661eb59a94c8c6c1bf3b2c1eb624a025fabe09c683440dc1b3. API revision lanes-api-build-1ec804a4-356b-494a-809a-0ae15d4d5932 receives **100% traffic**, and API/news/expiry share that main image with source_rules/source-rules-v1/source-rules-production-v2. Minute expiry execution lanes-zone-expiry-55r74 succeeds at **4:35:24 PM PHT**. Quarter-hour OIDC controller remains enabled and a fresh Scheduler delivery returns HTTP 200 at **4:37:46 PM PHT**; collection need not dispatch a job when not due.

Automatic frontend build/rollout **build-2026-10-13-001** uses the same main commit, succeeds and serves **100% traffic** on navlanes.live. A redundant manual rollout was cancelled after discovering the automatic rollout; it is not serving. Live read-only Chromium checks pass **desktop and mobile**, using real health/public zone/public alert APIs, home/map/news-panel loading and protected-History HTTP 401; no API fixtures or page errors. The first mobile smoke assumed the desktop news-button location; corrected only that test to open the existing mobile action menu, then both cases pass. [Live desktop](desktop-production-map.png), [live mobile](mobile-production-map.png).

Live public APIs show one existing active citizen zone and zero current published news alerts, both HTTP 200. No historical flood data is inserted into production and no new current news activation is claimed. Complete captured-source timelines prove positive initial/later zone publication and expiry. No agent, replay helper, ChatGPT account or LLM news provider is needed by deployed operation. Source/network/spatial coverage and physical reporting accuracy remain bounded. Source code and deployment are reproducible from main; optional MCP/framework experiments are preserved on ROI.


Final autonomous delivery: the **4:45 PM PHT** quarter-hour tick reaches the new API and completes with **HTTP 200 at 4:45:26 PM**, without a manual trigger. A read-only production database check independently confirms **collection, processing and publication all enabled**, seven enabled publishers, 11 feeds checked/143 entries read/four articles saved or seen, **zero feed/body errors**, and no pending/processing/retry/failed claim queue. No eligible new current flood candidates are present. Last worker cycle is completed without an error and records zero inference requests. The first attempted local read used Cloud Run's Unix socket binding, which is unavailable on Windows; the successful follow-up uses this same Cloud SQL instance's existing public endpoint in an explicit read-only transaction without changing its schema/network/data.

### Complete historical timeline and reproducible release acceptance

Both scenarios now run through `scripts.replay_news_source_timelines` on fresh private PostGIS using **the normal scheduled worker and FastAPI public routes**. September 24 passes all five checkpoints with zero active zones: observed flooding is already outside the admission window when the captured article becomes available; forecast/clearance/context claims do not become new wet zones. September 9 passes all 26 checkpoints, four immutable article versions and four extraction runs. Initial seven zones include Santo Domingo at 19 inches/08:55. These expire before the later observation; a separate later seven-zone set includes Santo Domingo at 10 inches/16:30. Final public API returns zero active zones. Fourteen historical zones are retained, with 77 evaluations and 191 decisions. Both scenarios preserve counts/completed attempts on repeat and use **zero LLM requests**. [September 24 summary](september24-summary.json), [September 9 summary](september9-summary.json).

The first September 9 harness assertion expected `10-inch`, while the original later source/extractor preserves `10 inches`; the pipeline had correctly published the target. Corrected only that assertion to the source spelling plus 16:30 observation time, then reran all 26 ticks on a new database. The first receipt remains retained privately. Historical RSS membership is reconstructed; early publisher-index text uses a reconstructed HTML wrapper. No article fact, observation date, source approval, NLP output, audit result or polygon is substituted.

Responsive regression: 20 of 22 cases pass in the combined run; two desktop cases fail while loading the page (a retained trace contains Invalid or unexpected token). Both unchanged cases pass in a focused desktop follow-up, completing all 22 distinct cases across the runs. Initial traces remain retained. This does not claim an all-green first run. Actual map tests use persisted API data on both sizes. Main-based release worktree excludes MCP routes, auth helpers and framework/library upgrades; production dependencies and schema definitions remain unchanged. Cloud Build now tests its freshly built runtime and executes the actual source-mode worker before promoting the exact API revision.

### Measurement precedence and scheduled-worker follow-up

The developer clarified that explicit article measurements take precedence over verbal gauges, with verbal extraction only when a measurement is absent. The existing shared extractor already applies that rule. Removed the added source-validator rejection of paired descriptive/measurement differences; policy identity advances to `source-rules-v2-measurement-first` / `source-evidence-v2`, while provider/model remain `source_rules` / `source-rules-v1`. Original text, prior evaluations and hashes remain unchanged. Exact 19 inches maps to the existing knee gauge; arbitrary measurements and qualifiers are retained without rounding to an invented gauge.

The publisher capture contains decorative play-marker bullets. The first release also added a short display helper joining selected source fragments with ellipses. Removed that shortening: public descriptions use the extractor's saved evidence with decorative play markers removed for display only, under the existing 700-character projection bound. Original article and evidence spans keep their markers. Existing desktop/mobile See more controls expose longer descriptions.

The historical replay now enters through the same `run_scheduled_news_tick` worker used by production. Only publisher RSS/HTML and the historical clock are substituted; extraction, source checks, PostGIS writes, OSM/NOAH geometry, publication, advisory lock/cadence and runtime diagnostics run normally. This is a captured-source replay, not an authentic archived RSS or current flood activation.

Measured follow-up: **31 evaluations, 27 source alerts, seven estimated zones, zero LLM requests**. The Santo Domingo NS Amoranto/Banawe estimate uses **19 inches**. The native scheduled-worker scenario passes repeat/expiry checks; persisted snapshots independently confirm the measurement-based target and display cleanup. Current preserved dataset is `lanes_nlp_demo_20261013_v3`; scenario/report are in `data/news-nlp-demo-20261013-v3/`. Both actual map browser cases pass on desktop/mobile, including expanded source evidence. TypeScript and scoped ESLint pass.

Cloud Build `6acda5f8-1226-4596-a33a-943b9846799d` succeeds with **275 Linux checks passed**. API revision `lanes-api-source-nlp-v2-20261013` serves **100% traffic**; API/news/expiry share digest `sha256:b1fbabb2d6c30c7e26450eb2cc491a0c2ec71eddb1e1936ccce5a3683bafc318`. Scheduler is resumed on the existing quarter-hour controller. Deployed worker execution `lanes-news-discovery-xz4tf` succeeds at **3:36:34 PM PHT**; API health and navlanes.live return HTTP 200. No ChatGPT agent, local replay helper or LLM provider is required by normal deployed collection/processing/plotting. Optional MCP work remains separate. Main Git integration remains pending.

The six-zone results, first image and conflict handling below describe the **initial release**, superseded by this measurement-precedence follow-up.

[Updated desktop evidence](desktop-measurement-first.png) · [Updated mobile evidence](mobile-measurement-first.png).

`news_source_validation_service.py` reparses immutable text using existing local Taglish rules, matches exact occurrences/facts and retains bounded source spans. It checks publisher-derived parent locality, observation timing, status, depth, access and segment meaning; rejects altered/unsupported evidence and paired gauge/measurement conflicts. Stored provider is `source_rules`, version `source-rules-v1`. The legacy audit DTO is reused for compatibility, not to claim independent AI or physical verification.

Evaluation skips inference/quota requests and provider cooldown writes in this mode. Existing publication, source approval, freshness, idempotency, override and geometry/expiry guards remain. A nullable-evidence clearance lookup that previously crashed publication is fixed. Scoped list excerpts show the road's own depth/parent/row instead of a misleading earlier road's depth; original extraction, evidence spans and hashes are unchanged.

No new library, SQLAlchemy model, table or migration. Existing Alembic migrations apply to head `d7e4b9a21c60` on fresh loopback PostGIS in the existing LANES container. Earlier failed disposable runs remain separate; no shared/cloud data is reset.

## Measured local results

- Existing collector → captured article → normal extraction → source evaluation → publication → bundled real OSM/NOAH estimated zones: **one article, 31 evaluations, 26 source alerts, six active zones, zero LLM requests**.
- Repeated pipeline execution creates no duplicate extraction/decisions/zones. Advancing the replay clock expires the zones without claiming physical clearance.
- The native scenario uses fresh database `lanes_publication_lifecycle_test_nlp_20261013_v3`. Only publisher RSS/HTML and the clock are supplied from captured evidence; historical RSS membership is unverified. Source facts and geometry are not mocked.
- Preserved browser dataset: `lanes_nlp_demo_20261013_v2`; source clock is **September 9, 2026, 9:20:06 AM PHT**, following the source's original publication. Local API returns six zones and 26 alerts.
- Source checks accept supported Tribune observations/clearances, keep distinct repeated-road/parent identities, reject changed facts/offsets and ambiguous/negative fixtures, and retain Santo Domingo's half-knee/19-inch conflict.
- **270 Linux checks passed** in the focused image on the existing production dependency stack. Earlier Windows regression selection passed 269, then the added excerpt/security selection passed 26; these are overlapping selections, not additive totals.
- **One native PostGIS end-to-end scenario passed**, including repeat and expiry checks.
- **Four desktop/mobile Chromium cases passed**: source-mode diagnostics and real persisted polygons/source details with no API fixtures. TypeScript and scoped ESLint pass after correcting test types. The first map run failed only on an assumed link title; verified source URL replaced that locator. WebKit is not claimed.

[Desktop real map](desktop-real-map.png) · [Mobile real details](mobile-real-map.png).

## Production release

Cloud Build `0563c62f-829d-4267-bc4e-54c27ea9c9b2` succeeded; it runs the Linux checks before publishing the runtime stage. Image digest is `sha256:8212d32a8960732489f99c8e77da3a32f488708f0b0a403c8d3ba3a540118a66`, tag `source-rules-defense-20261013`. It overlays tested runtime changes on deployed main `cfd5aae` / prior digest `sha256:8f0cd8dc47f9277561b7002d3bacd97f86d03234b29577ee445609d9a35322d7`; candidate MCP/framework dependencies and credentials are excluded.

API revision `lanes-api-source-nlp-20261013` serves **100% normal traffic**. API, existing news job and existing expiry job select source_rules/source-rules-v1/config revision source-rules-defense-20261013 on the matching image. The news Scheduler was paused during rollout, then resumed with its existing quarter-hour OIDC controller target. Independent minute expiry is preserved; no extra container/service was created.

Production requires a configured private JWT key; development defaults generate a runtime secret. Automatic admin/admin bootstrap is development-only. API now binds Secret Manager `lanes-jwt-signing-key:1` with scoped runtime access. Private generation material was deleted after upload and never included in the build or Git. Previous exposed `ml-expiry`/`subsidence-v3` API tags are removed so they cannot serve the old public fallback key. Existing users need to sign in again; historical users/roles/data are preserved.

API health returns **HTTP 200**. A real controller delivery at **2:34:01 PM PHT** returns HTTP 200 and starts execution `lanes-news-discovery-5vwth`, which succeeds at **2:34:56 PM PHT**. Persisted cycle reads **135 feed entries**, finds **zero eligible new flood candidates**, records **zero inference requests** and ends with no runtime error. Source diagnostics report available/source_rules. This is live deployment/automation acceptance, not a claimed new current flood activation. The positive plotted event is proved by the local historical replay.

## Remaining boundaries

Rules share the local extractor and cannot independently establish news truth or catch every semantic error. Unknown or ambiguous spatial cases remain unresolved. NOAH susceptibility and the existing road margin support estimates, not measured wet width. Captured September 9 data must not be presented as current October flooding.

This initial-release integration warning is superseded by the final main-based backend/frontend deployment above. The matching release is integrated into main; retain source-mode configuration and the private signing-key binding on subsequent builds. Ignored pre/post release snapshots are in `data/news-nlp-release-20261013/`; [runbook and rollback](../../guides/news-source-validation-defense.md), [implementation plan](../../plans/news-source-validation-defense.md).
