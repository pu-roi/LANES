# GMA incorrect-capture cleanup and active-only placement gate

> **Last Updated:** October 23, 2026, 8:15 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The exact incorrect cloud capture chain was removed; corrected News Intelligence remains available. Active plotting is blocked by spatial qualification.** API/manual worker v27 is deployed. No new active or historical GMA event/polygon was created, and no Gemini, token-count or NER inference request was made.

## Authorized cleanup and preservation

The user explicitly selected removal of the incorrect capture chain, superseding earlier append-only retention of that chain in the application database. This does not authorize general flood-data cleanup. Fresh private recovery evidence was captured before deletion and uploaded under a non-public Cloud Storage prefix. The bucket has no public IAM bindings.

| Deleted records | Exact selection | Count |
|---|---|---:|
| Incorrect historical events | 71–75 | 5 |
| Inactive zones | 71–75: Don Jose, Palali, Banawe, Tabayoc, Ubay | 5 |
| Event locations | Only locations owned by events 71–75 | 15 |
| Timeline entries | 209–218, including five supersession markers | 10 |
| News claim cases / sources | 106–110 in each table | 5 / 5 |
| Claim evaluations | 150–159 | 10 |
| Extraction runs | 375, 376, 378, 379, 380 | 5 |
| Incorrect original/native captures | 137 / 574 | 2 |

The transaction deleted **62 rows**. A complete custom-format backup, exact selected-row export, hash-bound preview and restored-backup rehearsal preceded the cloud write. Rehearsal proved rollback after an injected mid-delete failure, wrong-target/tampered-authority rejection and repeat execution without writes. Only the finalized-evaluation and immutable-source deletion guards were temporarily disabled and restored inside the transaction. All foreign keys remained enabled; trigger definitions/states, constraints and sequences are exact before/after matches. There was no reset, sequence reset, `TRUNCATE CASCADE`, or broad notification/account/community cleanup.

Every unselected public-table row matches its pre-cleanup fingerprint. Preserved records include **8 users, 37 community posts**, article 47 and its corrected versions **140/569**, all six corrected-capture runs **382/383/384/386/387/388**, and the two clean-source claim cases/sources/evaluations. The unrelated manually created/deactivated **event/zone 76** and its timeline remain exact. Citizen reports and moderation were not created or changed.

Collection Status retains article 47 and selected correction 388. Its processing history now has six clean-capture runs. The article reader returns native version 569 because that reader lists versions with retained runs; original capture 140 is independently verified present in SQL. It should not be mistaken for a missing source capture.

## Placement investigation and actual outcome

Corrected run 388 remains immutable: three source-supported observations on September 9, 2026 at **2:47 PM Asia/Manila**, gutter deep and passable to all vehicle types, with measured inches/metres unknown. No facts were borrowed from Tribune or Philstar.

User-provided coordinates are retained as hints with separate provenance, never as source-reported coordinates or polygon radii. The September 27 OSM snapshot places Rizal's hint about **1.3 m** from way **820063561**, and F. Sevilla's hint about **19.1 m** from way **22748072**, both in Malabon. These ways intersect retained NOAH vectors. For example, the nearby 233.6 m Rizal way has approximately 54.3 m of modeled overlap in the 5-year scenario, versus its full length in the 25/100-year scenarios. The nearby 149.2 m F. Sevilla way has approximately 78.0 / 117.8 / 149.2 m in the respective scenarios. These are modeled susceptibility intersections, not measured flood extent or article depth, and do not authorize an entire-road polygon.

| Group | Actual frozen-image and cloud preview | More precise investigation |
|---|---|---|
| resolved-n6: Rizal Ave Extn, San Agustin | `missing_valid_barangay_boundary` | The retained COD review explicitly excluded Malabon San Agustin (`PH1307502016`, PSGC `1380400016`) for `checked_osm_city_containment_mismatch`. A broader city fallback or clipping the conflicting polygon would bypass the boundary gate. |
| resolved-n8: Tañong F. Sevilla Blvd. (Bayan) | `named_road_sections_not_found` | Named F. Sevilla Boulevard ways exist near the hint; the full source section/locality relationship does not resolve to an accepted bounded section. Tañong's canonical administrative role remains unknown. |
| resolved-n10: Marcos Highway Underloop | `no_reported_road` | Raw LANDMARK prediction and `canonical_road: null` remain unchanged. Nearby named Marcos ways are elevated bridges; the raw PBF also contains unnamed vehicle link 4725482 about 1.4 m from the hint, connected near building-passage-tagged link 687797650. These unnamed links are omitted from the current named-road catalog. They are investigation candidates, not an approved underloop footprint. |

The Linux PBF inspection avoided a Windows application-control block on the installed osmium DLL. The original PBF and derived candidate findings remain private. No source facts, labels, boundaries, grade tags or existing spatial catalogs were changed to force acceptance.

Cloud execution **`lanes-news-verified-m8j9q`** completed a read-only preview with all three groups unresolved, matching the actual-data disposable preview. The new active-only command requires all three groups to qualify. **No cloud apply authority was issued and no activation was dispatched.** Tribune 25 and Philstar 274 remain untouched. Completing active plotting still requires authenticated locality coverage and a properly bounded F. Sevilla/underloop placement adapter or catalog support; this evaluation is not three-zone acceptance.

## Implemented release and tests

`news_gma_cleanup.py` provides the fixed selection, exact preservation checks, dependency rejection and transactional cleanup. `news_gma_active_outputs.py` provides separately bound preview/apply permissions, source/run/asset/database authentication, full three-location gating, geometry recomputation, overlap checks and atomic active-only persistence. It creates no ended counterpart; source lineage points directly to corrected 388. Internal presentation metadata excludes these instances from normal routing and statistics. History readers additionally exclude this exact active-only dataset, including after manual deactivation; older paired-dataset behavior is unchanged.

The manual worker exposes `gma-active-preview` and `gma-active-apply` through the existing supervised entrypoint. The actual issued authority permits preview only, zero provider requests and no application writes. It binds release, database, model/spatial manifest, run/result/source hashes, hints, private receipts and the unchanged stopped ledger. Default invocation remains read-only preflight; general processing is disabled.

| Release / verification | Result |
|---|---|
| Serving API | `lanes-api-gma-active-only-20261023-v27` |
| Image digest | `sha256:f0ad1ca60da8653efa00221e8363fe550d6ec9cc2caf0ca46cdd08475d1fe552` |
| Release hash | `5061dcff1d8cd2ad241e541b1283cd8d0004870935a5f73a3797c39e1608e915` |
| Worker settings | Linux amd64; 1 CPU, 3 GiB, 600 seconds, zero retries; LANES secret version 2 |
| Cloud read-only preflight | `lanes-news-verified-jxpcs`, passed; same native/resolved model pipelines |
| Regression checks | 126 passed; 26 database-dependent cases skipped in this invocation |
| Separate disposable-PostGIS checks | 61 passed, plus the added all-three failure-gate case passed separately; 62 distinct checks at existing migration head `f1a9c7e2b604` |
| Linux software contracts | Seven passed with networking disabled; zero external provider requests |
| Actual-data disposable preview | Source/asset authentication passed; three explicit spatial blockers; apply rejected without any row changes |
| Synthetic disposable persistence | Three active-only QA incidents saved once; no historical counterpart; hidden from history/routing; repeat zero writes; manual deactivation never reversed |
| Protected canary | Three run-388 cards, matching source/depth/time/passability, processing history, counts/pagination/search, history/map/analytics/export and auth protection passed before promotion |
| Hosted/local desktop/mobile | News summaries, source text, evidence and modal scrolling passed; existing frontend artifact unchanged |
| History and Spatial Operations UI | Hosted/local desktop/mobile show preserved event 76 and the active-list empty state; local desktop passed an isolated retry after a development-page loading timeout |

Synthetic geometry was confined to the owned restored QA database and is never cloud spatial acceptance evidence. Initial verification-script failures from local JWT environment selection, version-list expectations and article-wide search expectations were corrected in the private harness; they did not cause provider requests or application writes.

Final post-release SQL verification matches **every unselected row** against the locked cleanup baseline, including exact community-post links and account contents. Ledger contents and storage generation are unchanged. News/history/collection/public-active readers agree on navlanes.live and localhost. Three-location active-map focus remains untestable because no actual geometry qualifies; no UI acceptance is claimed for nonexistent active instances. Documentation audit updated the existing module status, task/progress, system/database notes and bug log; technology-stack and architecture-decision records need no change because no dependency or architecture replacement occurred.

No UI, public API shape, model/schema/migration, dependency, training or scheduled RSS change occurred. The spending ledger remains **stopped at 42 attempts / US$0.7524937 effective commitment**, with both object content and storage generation unchanged. News automation stays paused, expiry switches OFF, old seed disabled and personal key unused. Effective commitment remains an accounting bound, not a confirmed invoice.

## Evidence and recovery

Ignored private evidence is under `data/gma-active-cleanup-20261023/`: the fresh dump and hash, exact selected export/authority, successful recovery uploads, rehearsal database/proofs, cleanup and no-op repeat receipts, stopped ledger snapshots, release/image/rollback specifications, scoped IAM grants, protected reader results, raw OSM probe, actual cloud preview and UI screenshots. The cleanup authority SHA-256 is `ec66def0cf2acbe7734bc2f8e68127109e2385fb75459f07402512cf1ef05402`.

The restorable backup and receipts are also retained privately under `gs://lanes-storage/private/news-pilot/20261022-5512bbaa/gma-active-cleanup-20261023/`; placement receipts use the separate `diagnostics/gma-active-only-20261023-v1/` prefix with conditional create/read access. Credentials and authorization headers are excluded from operational logs and processing receipts.

Recovery restores selected records in dependency order from the fresh export/dump, with the same scoped safeguards, without overwriting unrelated later activity. Previous API/worker specifications are retained. No active GMA instances exist to withdraw. Do not reset the database, resume paid processing, recreate purged old outputs or issue activation permission from this unresolved preview.
