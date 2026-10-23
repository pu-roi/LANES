# GMA connected-road placement and active-only cloud rollout

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). October 23, 2026, Asia/Manila.

## Verified cloud result

Three active presentation event/zone pairs **77–79** are saved and readable on navlanes.live. They directly reference unchanged **article 47, original 140/native 569, correction 388**. No historical counterparts were created; only unrelated ended event 76 appears in Flood History. Corrected News Intelligence still has three observations. Tribune 25 and Philstar 274 were not processed.

| Group / event / zone | Location | Source facts |
|---|---|---|
| resolved-n6 / 77 / 77 | Rizal Ave Extn, San Agustin, Malabon | Gutter deep; Sep 9, 2026, 2:47 PM Asia/Manila; all vehicles passable |
| resolved-n8 / 78 / 78 | Tañong F. Sevilla Blvd. (Bayan), Malabon | Same reported depth/time/access; administrative role remains unknown |
| resolved-n10 / 79 / 79 | Marcos Highway Underloop, Marikina | Same facts; original LANDMARK prediction retained |

Measured inches/metres remain unknown. The 25-metre margin is display policy; these are estimated road corridors within modeled susceptibility, not measured wet extents. User coordinates remain separately attributed hints and never supply polygon radii or article facts.

## Road and NOAH qualification

Opt-in `connected-road-noah-v1` follows connected node identities with exact names/aliases; cities disambiguate and barangays describe. Neither boundary clips geometry. Disconnected same-name roads, ambiguous pins, unsupported branches/name changes, incomplete coverage and explicit unsupported physical sections fail visibly. Earlier contracts retain their prior behavior.

| Group | OSM way IDs | Connected source metres | Modeled road metres |
|---|---|---:|---:|
| resolved-n6 | 22748071, 820063549, 820063561, 1302102343, 1302544817 | 431.27 | 431.27 |
| resolved-n8 | 22748072, 22748073, 54172611, 820063573, 820063574, 1059939676, 1059939677 | 446.06 | 411.37 |
| resolved-n10 | 4725482, 576549338, 687797650 | 115.31 | 115.31 |

F. Sevilla retains both authenticated one-way arms of the mapped boulevard loop. Its modeled dry intervals and holes survive the final geometry. One nearby NOAH polygon island without any intersecting road centerline is explicitly excluded; no modeled road core is lost. The ground-level underloop uses three connected vehicle links between checked junctions, original primary_link/access/destination tags and feature-specific building-passage evidence. Its crossing relationship with elevated Marcos Highway ways 4308741/1290005164/803340865 is authenticated; those elevated ways are excluded from the underloop output.

All retained 5-/25-/100-year scenario/class intersections contribute to the deduplicated modeled envelope. Exact source-aligned cores and final coverage are checked; existing 25-component/vertex/precision limits remain enforced. Rizal and F. Sevilla share node **686224593**; their overlap is admitted only within twice the existing corridor margin of that actual junction, for these same-time low-depth/passable observations. Existing unrelated active overlaps remain blocked under transaction/table locks.

## Releases and authority

- Placement/apply API v28: `lanes-api-gma-connected-20261023-v28`.
- Final serving API: `lanes-api-gma-connected-reader-20261023-v30`.
- Manual worker: `lanes-news-verified`, Linux amd64, 1 CPU / 3 GiB / 600 seconds / zero retries; default read-only preflight and general provider execution disabled; LANES key version 2 unchanged.
- v28 release SHA-256: `3e787e55193f7810d80a997c1503c20ad3e352703f147c5033574314f4584ac3`.
- v28 image digest: `sha256:684c6b6275103c4c6f19b60302db7756c91a39062e20e05b575b360af91ea198`.
- Final release SHA-256: `6f89a491f185be24691a7891153a93eb68f928095dfdeb49f51d3ebeb2b1ec56`.
- Final image digest: `sha256:f3b2f27647df0990aa7088ae2d097a9f129347c6c34280fb0f8c2b415f5c24da`.
- Complete reviewed preview SHA-256: `0da463100dbbaac8dc4cff16820a8d5b7c1d9a5cb6a3fead42f621168b4d70c2`.
- Original correction release remains pinned to v26 SHA-256 `ca6befd3719e1882a37d9183bb933848e8545faa6a65da05f7956613221a961b`; unchanged source/model/runtime/spatial identities verify the original saved result before new placement is derived.
- OSM compressed catalog: `b43240e75fb0eeeeb3e9a9d15724c162f24197c4bc0a05e834ae11776062b801`; original PBF: `0fa54508ad7fe5e9debd6f46b6cd5ca01eeb57b26e2ba5d5b751a5539b6b2b1d`.
- NOAH catalog: `cceb8c93d5441f14aad48808319a3d4cf3a87918ea8089dcb5efbf86c49940ce`.
- Reviewed feature asset: `7be8ed13dc23f4f5fcae83d7fbc8a3ccf1003be4724763635a83e03b0b0b0709`.

Preview and apply use separately frozen operation authorities bound to the database, current release, saved-result/source hashes, original assets, coordinate hints, new road policy/code/assets and exact complete output. Conditional create/read IAM is scoped to the private receipt prefix. Earlier releases/authorities/requests remain retained. No secret is present in the image, source, frontend or sanitized evidence.

## Persistence, preservation and reuse

A fresh 823,644-byte private restorable backup includes the two citizen reports created during work. It was restored before the actual-geometry rehearsal; this phase did not repeat the earlier cleanup. The cloud transaction inserts **3 flood_events, 3 flood_avoidance_zones, 7 flood_event_locations, 6 flood_event_timeline_entries**. No claim/evaluation/decision/extraction/report records are created or modified. Every pre-existing row in the affected tables is exact. Accounts, 37 community posts, source versions/history, pending reports **44/45**, surveys, notifications, moderation and event/zone **76** are preserved. Migration head `f1a9c7e2b604`, trigger states and foreign keys remain unchanged; insertion sequences advance normally.

All-three qualification and preview checks are repeated under the output locks. A restored-copy late flush failure rolls back the complete set, concurrent callers produce one saved set plus reuse, stale previews fail, and subsequent commands cannot reactivate manually deactivated instances. Cloud repeats on v28 and v30 return `reused`, event IDs 77–79, zero application writes/provider requests. Presentation lineage remains absent from history analytics/exports and ordinary routing exclusions.

## Source-depth response repair

Actual HTTP checking found that the existing gauge conversion would fill unknown gutter measurements as 8 inches/0.20 m, including during FastAPI response revalidation after a service returned nulls. The final backend reads the authenticated correction's exact raw depth/measurements and preserves them through the existing response validator and queue/card projection for this versioned dataset. The ordinary gauge conversion is unchanged. No source fact, correction, stored geometry or public response field was altered. Tests cover revalidation as well as the service object.

## Verification and receipts

- **157** targeted regressions pass; **3** optional fresh-database fixture cases skipped without their environment. Actual restored-PostGIS checks independently pass source authentication, all-three persistence, preservation, concurrency, rollback, stale preview rejection, repeat and manual deactivation. A separate broader Windows fresh-fixture attempt hit its 180-second local timeout under resource pressure; it made no cloud writes and is not counted as passed. The final frozen Linux image subsequently passes fresh and repeated `alembic upgrade head` on a new disposable database, preserving head `f1a9c7e2b604` (private `migration-acceptance.json`).
- Seven frozen Linux worker contracts pass with networking disabled and zero provider calls. Final-image reader checks revalidate actual saved correction 388 using its original assets and verify source-based depth after response revalidation on restored PostGIS.
- Protected canary checks prove three News Intelligence observations, exact source times/body, retained LANDMARK, pagination/filter/count agreement, three active-zone public/detail/queue responses, unknown numeric depth, history/analytics/export exclusion and unauthenticated-admin rejection.
- Hosted desktop/mobile News Intelligence summaries/source evidence/scrolling pass. Hosted desktop/mobile Active Zones grouping/details/map focus, guest public-map popups for all three roads, and history exclusion pass. Local desktop/mobile News Intelligence and maps also pass, including all three guest public-map popups, map focus, card details and history exclusion.
- Browser harness corrections reflect existing behavior: inspection opens the mobile map and needs its return control; public-map checks use a separate guest context because admin sessions redirect to the admin dashboard. No UI edits were made for these checks. Local server reload interruption and a screenshot/font timeout were retained as failed harness attempts; the final stable-server desktop rerun and mobile run pass.

Private immutable receipts and recovery assets are under `gs://lanes-storage/private/news-pilot/20261022-5512bbaa/diagnostics/gma-connected-20261023-v1/`. Sanitized/local verification manifests, complete source/road evidence, preview/apply authorities, source fingerprints and browser screenshots are retained in ignored `data/gma-connected-road-20261023/`.

Cloud executions: preflight **lanes-news-verified-74nrw**, preview **lanes-news-verified-6fgmn**, apply **lanes-news-verified-ftb4d**, repeat v28 **lanes-news-verified-bvlkh**, repeat v30 **lanes-news-verified-876ng**. The original earlier cleanup, processing and spending receipts remain retained.

Ledger content and GCS generation remain unchanged: **stopped / 42 attempts / US$0.7524937 effective conservative commitment**. No NER, Gemini generation, countTokens, fallback or retries occurred. Reservations are not invoice charges. News automation remains paused, old seed disabled, both expiry switches OFF, and the personal key unused.

## Recovery and review stop

Restore a previously accepted serving revision and disable further manual execution if release rollback is necessary. Withdraw these three instances through normal deactivation, preserving source/placement receipts and unrelated records. The fresh backup/private row exports support scoped recovery; do not reset the database or overwrite later unrelated user activity. Repeated commands must never reactivate deactivated instances. Stop after this GMA rollout for user review; no Tribune, Philstar or scheduled processing follows automatically.

## Final review stop

All hosted/local desktop/mobile checks are accepted. Private `completion.json` records the completed GMA rollout and exact release. Three corrected active zones remain available until normal manual deactivation. Tribune, Philstar and scheduled news remain pending/paused. No further processing is authorized by this completion.
