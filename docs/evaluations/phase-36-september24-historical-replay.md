# September 24 flood report: historical pipeline replay

> **Last Updated:** October 03, 2026, 1:38 PM
> Author / resolver: [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Scope and source

The developer requested testing LANES's own services and logic using the [Daily Tribune report](https://tribune.net.ph/2026/09/24/minor-flooding-hits-some-metro-areas). Its event is Thursday, September 24, 2026; publication is September 25 at 4:41 AM Philippine time. The test preserves both dates. Actual publisher HTTP retrieval and the production extraction entry point run locally; durable storage and the main reader run in an isolated in-memory database. Real PostgreSQL predicates are checked with read-only literals. This is not a deployed, authenticated UI or automatic map-publication test.

Daily Tribune is not among the six configured live collector publishers. The article is outside the seven-day collection window on October 3. The historical replay's temporary source and clock do not change production source configuration, age policy or saved data.

## Reproduction and defects

The original regular-page parser returned only 182 characters of heading/author/photo controls and zero claims, even though the HTTP response contained the article paragraphs. The publisher streams `story-text` containers after the enclosing article closes. The AMP page supplied 1,333 characters and exposed extraction defects:

- Manila inside **Metropolitan Manila Development Authority** became a separate flooded city and inherited Mandaluyong's depth.
- Narrative intersections/proximity such as “at the corner of,” “near,” and “at” lost their qualifier or created an extra claim for a crossing road.
- Hyphenated **8-inch** and **10-inch** measurements were missed.
- **Cleared** and **receded** were not correctly classified; the East Avenue cleared update appeared active.
- An earlier “In Manila” context incorrectly attached the Quezon City road updates to Manila.
- Separate **by 3:20 PM / by 3:29 PM** clearance clocks were missed. The 4:34 PM observation could not resolve across the overnight publication delay, although Thursday was explicitly reported.
- An adjacent “the road remained passable to all types of vehicles” sentence was not attached to Boni Avenue.
- City/Sitio qualifiers duplicated reported sites. They are now retained as `location_context_only` provenance without qualifying as independent floods.
- Removing those duplicate qualifiers exposed an existing geography bug: **Roxas Boulevard in Manila** retained a PSGC code from an unrelated homonymous barangay. Explicit road parent cities now supply the road claim's administrative PSGC identity.

All seven initial replay tests failed before the corrections. Later failing checks were addressed, including a too-short retrieval test fixture, UTC serialization comparison, the Roxas PSGC mismatch, and PostgreSQL diagnostic literals initially using boolean values instead of production JSON `->>` text types. No failing test was removed.

## Corrected real-article results

The regular page now yields **1,136 characters of reporting body**, excluding headings, photo credits, controls and related stories. Body SHA-256: `dc4773d602277a22fb0660705e21eb45f64125f4bd8167cd55ad21ec3350bc0f`.

| Road site | City | Depth | Condition in the historical report | Observation / clearance time (PH) |
|---|---|---|---|---|
| Boni Avenue at F. Ortigas Street | Mandaluyong | 10 inches / half-knee | Flooded; passable to all vehicle types | Sept 24, 4:34 PM |
| Quirino Avenue near Guazon Street | Manila | Approximately 8 inches / gutter | Flooded; vehicle-specific passability unknown | Not explicitly stated |
| Gov. Pascual Avenue, Sitio 6 | Malabon | 8 inches / gutter | Flooded; vehicle-specific passability unknown | Not explicitly stated |
| East Avenue corner EDSA, westbound | Quezon City | Not stated | Subsided / cleared | Sept 24, 3:20 PM |
| Aurora Boulevard at Araneta Avenue, southbound/westbound | Quezon City | Not stated | Subsided | Sept 24, 3:29 PM |

The source says traffic remained passable through the Manila/Malabon corridors but does not specify all vehicle types; the parser does not invent that classification or an observation clock. The extracted 11 mentions comprise **five road sites, two standalone city summaries, and four context qualifiers**. SQL and detail readers agree on seven readable observations. All ten live replay assertions pass; offline replay of the captured body passes with the same digest/results.

The date resolver only uses a sole explicit recent weekday attached to actual flooding and the aware publication date. Ambiguous weekdays, explicit unresolved dates, future/old dates, and naive publication timestamps stay unresolved. Anaphoric passability requires exactly one preceding road in the same paragraph. Report clocks are not promoted to observation times. Evidence/place offsets remain exact.

## Validation

- **373 related backend tests pass; one skipped.** The skipped telemetry migration test requires a dedicated disposable PostgreSQL URL; no schema changed in this replay task. Seventeen replay cases cover publisher containers, independent road facts, city context, clocks, negative/ambiguous variants, provenance offsets, local discovery, durable extraction and SQL reading. Qualifiers do not inflate Collection attention counts; the isolated replay article is `ready` with seven readable observations and zero questionable mentions.
- **19 PostgreSQL positive/negative policy checks pass** using read-only literals.
- **11 real replay claim comparisons pass on PostgreSQL**, yielding seven readable claims / five road sites, matching detail explanations.
- The production database remains **24 articles, 10 source versions, 40 extraction runs**, with zero qualifying live cards, 24 excluded articles, zero default attention and migration `c5a7e9d2104f`. No historical article/run/report/zone was inserted there, and no external LLM auditor was called.
- Source and pipeline fixes are **local, uncommitted and not deployed**: extractor `taglish-rules-v1.3`, processing `rules-psgc-osm-2026-10-03-v5`. The deployed v4 release is unchanged. No dependency, model, migration, frontend or API route changes.

## Placement findings and remaining work

The real local OSM catalog is exercised. Four sites identify a single intersection/proximity, which does not define two endpoints of an affected road span; they remain `missing_explicit_bounded_span`. Gov. Pascual remains `named_road_sections_not_found`: the catalog contains **Governor Wenceslao Pascual Avenue**, but an unverified abbreviation/name mapping is not added. These are explicit placement gaps, not verified flood polygons. Every result has `may_affect_routing=false`; cleared or stale observations cannot become current closures.

Release the tested v5 API/collector correction together, then verify deployed behavior. If Daily Tribune is added to discovery, first verify its RSS/feed configuration and retain the reporting-body checks. Continue the original OSM/NOAH/matching Pasig DRRMO placement and automatic alert/zone integration; this replay does not substitute routine staff approval for automatic eligible news publication.

## Reproduce

From `backend`, using the repository virtual environment:

```powershell
.\venv\Scripts\python.exe -m scripts.replay_september24_news --output "$env:TEMP\lanes-sept24-replay-v5.json"
.\venv\Scripts\python.exe -m scripts.replay_september24_news --body-file "$env:TEMP\lanes-sept24-replay-body.txt"
.\venv\Scripts\python.exe -m pytest tests/test_news_september24_replay.py -q -p no:cacheprovider
dotenvx run -f .env -- .\venv\Scripts\python.exe -m scripts.audit_news_display --summary-only --validate-policy --replay-result "$env:TEMP\lanes-sept24-replay-v5.json"
```

Network access is needed for the first command; the second replays the captured public body offline. The last command uses the configured PostgreSQL connection inside a read-only transaction. Never use production replay insertion or change article dates to make historical flooding appear current.

## Private Docker database and actual page follow-up

At the developer's request, Docker Desktop was recovered by preserving both failed runtime socket directories before a fresh start. The original PostgreSQL/PostGIS and Valhalla containers resumed. A separate `lanes_news_test` database was created, PostGIS enabled, and the entire existing migration chain applied successfully to `c5a7e9d2104f`; no schema source was modified. Ignored `.env.test.local` overrides the database and local JWT key while preserving the encrypted cloud `.env`.

`scripts.seed_local_news_replay` passes actual captured publisher text through the existing evidence gate, saver, durable processor and result reader. It refuses cloud/other databases and connection-target query overrides. Three identical invocations leave **one article and one extraction run**, with **seven readable locations/five roads**, no auto-approved claims and unchanged zero zone totals. The preserved body is under ignored `data/news-replay/september24-body.txt`.

The actual authenticated frontend proxy returns HTTP 200 and all five road names. Browser verification on the real local page (no API mocks) confirms the seven-card list, original observation/publication dates, subsided East/Aurora labels, Boni detail with contiguous evidence/passability wording, captured source body, and Collection **Locations available / seven locations / zero questionable mentions**. Default Needs attention correctly has zero items. The browser was signed in using the separate local bootstrap admin, and the visible page remains open for the developer.

All **29 focused historical replay/connection-isolation tests pass**. Both dedicated launchers bind frontend/backend to loopback. No frontend component/API contract/dependency change was needed. This follow-up adds a persisted local UI demonstration; it does not establish deployed v5 or automatic map/zone integration. See [restart, replay and restore instructions](../guides/local-news-replay.md).

## Explicit location fields in the details modal

The subsequent developer request adds an explicit Reported location section before the flood metrics. `NewsResultDialog` renders the existing extracted street, barangay, section/intersection and local landmark, using a shared summary slot. This is frontend presentation only; it changes no extraction, API, model or dependencies. Missing road data says **Not specified for this mention**, because the Mandaluyong summary claim cannot inherit Boni Avenue from a separate sentence/claim.

Live authenticated local browser checks confirm Boni Avenue with F. Ortigas Street, Gov. Pascual Avenue with Sitio 6, and the Aurora Boulevard direction/intersection string. The city-only fallback is verified separately. At mobile widths 390 and 320, document width equals the viewport; modal bounds are 366×820 within 390×844 and 296×616 within 320×640. Desktop layout is checked at 1440×900. TypeScript and scoped ESLint pass; both existing responsive Info regression tests pass with API fixtures using installed Chrome. The initial automated launch failed because Playwright's bundled browser was absent; the same tests passed using their existing executable-path override. No failing test was removed. The location display is visible locally and has not been deployed.

## Street-recording reliability audit — October 3, 2026

At the developer's request, checked the existing extraction fields and location tests after confirming that separate cards belong to the same article. Each stored claim preserves its raw place, canonical road, reported section/intersection, local area, city, source sentence and source offsets. The September 24 regressions check the five road sites, crossing roads as qualifiers, Sitio 6, separate city/depth attribution, distinct observation times, and missing values without borrowing from another report. Broader tests cover multiple cities, road lists, ambiguous facts and same-road section updates. Placement tests reject unbounded extents, competing road paths and incomplete map coverage instead of selecting arbitrary geometry.

Validation: **29** historical replay/local isolation tests, **64** Taglish extraction tests and **17** road placement tests pass (**110 total**). The first placement attempt encountered sandbox permissions on pytest's temporary fixture directory; rerunning those 17 tests with permitted temporary-file access passed. No extraction, UI, database schema or deployed release was changed during this audit. These tests establish the checked cases, not universal accuracy for unseen publisher wording. Recording a street mentioned in the source remains distinct from proving its exact affected map extent.

## Article-level city context — October 3, 2026, 5:24 PM

The developer identified redundant city summary cards in the actual records, rather than missing street extraction. Added post-extraction reconciliation within one article and resolved city. Credible specific flood observations make broad city summaries context only; original sentences/offsets and road facts are retained. City-only observations, other cities, unreliable specific evidence and explicit different times remain independent. Tests cover both positive reconciliation and these exclusions, including unchanged durable reader/Collection counts.

Pipeline v6/extractor v1.4 creates a new immutable result rather than rewriting the prior run. Guarded local replay completed run 6: one article, two saved extraction runs, five readable road locations, no automatic approvals and unchanged zone totals. The real frontend proxy returns the five expected run-6 ordinals (`1`, `4`, `5`, `9`, `10`); authenticated browser verification confirms five cards, preserved Boni street/intersection/depth/4:34 PM evidence and zero Collection attention items. A stalled local auto-reload worker was restarted through the private loopback launcher before verification. Production v4 remains unchanged.

Validation: **165** replay, extraction, result/history, placement, isolation and processing checks plus **59** discovery checks pass (**224 total**). Initial new fixture expectations assumed the raw city name included "City" and used wording outside the existing affirmative-evidence pattern; corrected the fixture identity/wording and retained every test. No schema, migration, dependency, response contract or frontend code change. The existing v5 corrections are included in v6; release verification and original automatic placement/publication remain pending.

## Branch pre-push verification — October 3

At the developer's request, audited the registered documentation and prepared all pending changes on `roi-branch`. Corrected stale F4b rollout and schema/replay-count notes while retaining v6 deployment and automatic OSM/NOAH/DRRMO integration as unfinished. The dependency manifests already cover all added runtime imports; no new library is introduced. The approved telemetry migration is included in this branch bundle and was previously deployed with explicit approval.

The complete news/extraction/road-match suite passes **355** cases, with five PostgreSQL-only cases skipped in that first invocation. A separate guarded local run passes those **five** cases on newly created disposable databases: four extraction queue checks and one full telemetry migration round-trip. Existing private `alembic upgrade head` also succeeds. Both disposable databases were removed afterward; the saved replay and cloud database were preserved. Total: **360 distinct backend/database checks**.

TypeScript and changed-file ESLint pass. The desktop/mobile article and intelligence run passes 23 cases, skips three optional/project cases, and identifies two copies of an existing publisher-selection test whose selector searched inside the drawer although shared Select options are portalled to the document. Updated only that locator, preserving every assertion; focused rerun passes both desktop/mobile cases. Thus **25 distinct responsive UI cases are validated**. The real-publisher optional fixture cases are not substituted for the earlier authenticated local replay verification.

`git fetch origin` reports no `roi-branch` divergence before staging. `git diff --check` is clean. Private `.env.test.local`, captured source body, credentials and generated test outputs remain outside the commit. This is source publication preparation, not a new production release or proof of automatic plotting.
