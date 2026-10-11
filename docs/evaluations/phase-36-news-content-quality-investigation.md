# Phase 36: News Intelligence Content Quality Investigation

> **Last Updated:** October 03, 2026, 11:23 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Correction deployed; versioned reprocessing and normal collector execution verified.

## Initial investigation evidence and scope (before correction)

Inspected local frontend/service/CRUD paths, the dotenvx-configured database in a PostgreSQL `READ ONLY` transaction, current local deterministic extraction, and live Google Cloud API/collector metadata. Browser inventory exposed no open user tab, so the actual currently viewed browser URL/session was not observed. The database trace reproduces the reported Bangkok/prevention content without assuming which frontend session the developer used.

The configured database contains **24 saved articles**. Current local `list_result_rows` returns **9 main-list claims**, from articles 5, 12 and 24. Original source bodies, timestamps and immutable extraction artifacts were preserved. The read-only utility is `backend/scripts/audit_news_display.py`; `--compare-local-rules` invokes only the local regex/CSV parser, not HTTP, the hybrid auditor or publication.

| Article / latest run | Main-list output | Confirmed problem |
| --- | --- | --- |
| #5 / #11: QC school gets detention basin under covered court to curb flooding | Five active cards: QC, covered court, basketball court, and two Quezon City mentions. | Purpose/prevention and habitual flooding were interpreted as active observations. Publisher boilerplate also remains in the captured supporting sentence. |
| #12 / #14: Thousands huddle in Bangkok shelters as Thai flood damages seen at $320 million | Three cards: Reuters Bangkok, interior, MARKET. | Foreign flooding appears in the Metro Manila results; generic `interior` is grounded to San Jacinto PSGC `0504119009`. |
| #24 / #20: DPWH to fast-track UP-PGH drainage/septic tank construction amid flooding | One active Manila card. | Its supporting sentence says construction is intended to help address flooding, rather than independently specifying a current observed flood at that location. |

Current pure local rules reproduce these problematic claims from the same saved bodies. The problem is not resolved by refresh or reprocessing alone. Other stored flood-control/corruption stories are already absent from the main results but remain inspectable in Collection status; collection history and qualified location results have different purposes. No claim is made that all 24 historical saved articles should be erased.

## Root causes

1. **Incomplete observation semantics:** `NON_OBSERVATION_FLOOD_TERMS` masks explicit `flood control`, `flood mitigation`, `flood prevention`, etc. It does not cover the observed `curb flooding`, `help mitigate localized flooding`, `help prevent flooding`, `help address flooding`, or habitual `regularly submerged` language. `ACTIVE_FLOOD_WORDS` then treats flood words as active evidence. Existing synthetic tests cover explicit flood-control terminology and mixed real observations, but omit these real prevention cases.
2. **Main-list scope missing:** `readable_claim` checks lengths/flags/condition/depth, but requires neither Metro Manila grounding nor body-linked geography. `claim_reading_reason` has the same limitation. This allows foreign and unresolved generic-place claims to be displayed as reported flood locations.
3. **Generic name grounding and source cleanup:** a common noun can match a Philippine gazetteer entry without a local context; captured GMA/Rappler text includes publisher/related-content fragments. Fix location grounding and parser cleanup while preserving legitimate mixed-topic evidence and original source offsets.
4. **Saved history is not collection eligibility:** metadata/body shortlisting affects new collection, not the already saved backlog or the results read gate. Existing successful immutable artifacts retain old results until a genuinely new pipeline version is processed. A versioned corrective run must preserve earlier evidence/history; filtering only new feeds is insufficient.
5. **Actual service path:** the saved runs identify `rules-psgc-osm-2026-10-02-v2` with OSM catalog digest `4695f141b5e5d79feb909a4da0c1fad55e9060b4e1eea7f8f4c20476505aaf7f` and extractor `taglish-rules-v1.0`. Scheduled processing invokes shared rules extraction plus OSM evidence; it does not invoke the optional LLM auditor. The services exist and are used, but their present semantics do not establish content correctness.

## Initial deployed runtime check (before correction)

At inspection, API `lanes-api-00047-59t` serves 100% traffic. API and `lanes-news-discovery` both reference `news-osm-20261002-v4-expat`. Collector arguments are `-m scripts.run_news_discovery --discover --process --limit 50`; its latest recorded execution succeeded at October 3, approximately 12:00 AM Philippine time. Success establishes job execution, not that qualifying current news was discovered or classified correctly.

Unauthenticated probes against the verified API origin return:

- `/health`: **200**, database connected.
- `/api/v1/admin/news/sources`: **401**, authentication enforced.
- `/api/v1/admin/news/results`: **404**, new main-list route absent from that deployment.

The current local page calls `/admin/news/results`. The local frontend has no `NEXT_PUBLIC_API_URL` injected; its client defaults to `/api/v1` and Next.js proxies to configured `BACKEND_URL` or the local backend. This establishes a code/configuration distinction but does not prove the currently viewed browser's destination. Verify the actual deployed frontend build and proxy destination alongside the corrected API; deploying only the reader or only the collector is insufficient.

## Corrective priority before automatic map integration

- Add real positive/negative regression cases from these saved public-source passages: prevention infrastructure, habitual flooding, foreign flood, generic common nouns, boilerplate, and mixed policy plus genuine Metro Manila observation. Preserve an authentic local flood observation even when its article discusses infrastructure.
- Implement one backend evidence/scope policy shared by discovery/extraction and main-list presentation. Apply qualified-result predicates before SQL counts/pagination; retain excluded and unresolved evidence in the appropriate collection/history views with honest reasons. Do not label missing coverage as safe or silently invent a city.
- Version changed extraction behavior and reprocess eligible stored inputs without overwriting source versions or deleting backlog. Dry-run/compare the correction first; verify both positive retention and removal of the nine false main-list rows. An empty qualified-results list is acceptable when there is no supported local observation.
- Verify matching frontend/API/collector releases and approved migrations/configuration, then perform authenticated desktop/mobile checks against the actual demonstration URL. The deployed 404 is a release issue to close.
- Resume NOAH/DRRMO-assisted placement and automatic plotting once these content checks pass. Preserve the original automatic goal and its current-evidence/geometry/expiry gates.

During the initial investigation, no production writes, extraction enqueue, record deletion, deployment or external AI calls occurred. An initial hybrid-service audit was rejected by automatic approval review because network behavior was unverified; the database-only and explicitly local parser audits were subsequently approved and completed.

## Corrective implementation and verification — October 3

Implemented shared `news_evidence_policy.py` observation and Metro Manila predicates. Prevention-purpose and habitual references no longer establish active flooding; independent observations in mixed-topic articles remain eligible. Ordinary `interior ministry` and `MARKET` headings no longer become gazetteer sites. Discovery now checks every readable article body, including metadata-local and cached leads. Blocked metadata-local leads remain incomplete collection evidence.

Main-list SQL and Collection counts apply the same evidence/geography rules before pagination. Excluded saved claims retain their original detail/history and receive an honest reading reason. Extractor version is `taglish-rules-v1.1`; processing uses `rules-psgc-osm-2026-10-03-v3` plus the unchanged OSM digest, allowing corrective runs without overwriting earlier artifacts.

- **306 backend regressions pass**, covering extraction, discovery, processing, reading/history, fallback, ingestion and placement.
- **Eight read-only PostgreSQL predicate checks pass**, including genuine Pasig/Manila observations, mixed prevention/incident evidence, habitual flooding and foreign reports.
- The corrected SQL reader returns **zero qualifying cards** from the same 24 saved articles, excluding all nine false rows. This read-only comparison does not establish a genuine current local flood in the saved set.
- **13 distinct desktop/mobile UI cases pass; one desktop-only skip** across the initial run and focused recheck. The initial cold-route navigation timeout passed on recheck. Bounding-box assertions allow 0.01 CSS pixels of measurement error while document overflow remains strictly checked. TypeScript passes. Tests use mocked sessions/APIs and are not authenticated production acceptance.
- Upload rules exclude `.env*` and frontend build/test artifacts. Cloud Build `f35cb1d0-a565-4565-9494-e2a0a9c560ff` succeeded; backend image `news-evidence-20261003-v3` has digest `sha256:80c1b988feb4993d9838130bd680d93d321eba5f131075556f21a5cd1996e42d`.

Production was at migration `f29b6c8d104e`. Automatic approval review initially rejected migration execution because recovered prior chat approval was not accepted as trusted confirmation. The developer explicitly answered **“Approve migration and finish release”**. Migration execution `lanes-migration-j4dnk` succeeded; API/collector/frontend alignment and corrective processing are in progress. No completed production rollout or automatic zone activation is claimed here.

## Completed production release

- API `lanes-api-00048-xc7` serves **100%** traffic. API and scheduled collector use the exact backend digest above. `/health` returns 200; results, Collection and discovery-history routes return 401 without credentials instead of the former results 404.
- Firebase App Hosting build `702e8988-85c2-4f77-ba69-f0f6415325c2` succeeded. Frontend `lanes-frontend-build-2026-10-03-001` serves **100%** traffic at `https://lanes-frontend--lanes-project-508809.asia-east1.hosted.app`.
- Migration is verified at `c5a7e9d2104f`. Corrective execution `lanes-news-discovery-xjdjl` succeeded: **10 completed v3 runs**, **30 total runs**, **10 source versions**, **24 saved articles**, and **zero unsupported qualified cards**. All 20 earlier runs and all source versions/articles remain available.
- Normal discovery/processing execution `lanes-news-discovery-zrrkj` succeeded on the released image. The scheduled job retains its normal `--discover --process --limit 50` arguments. The initial corrective launch `lanes-news-discovery-n4f4g` failed before processing because PowerShell collapsed the unquoted comma arguments; quoting the complete flag resolved it.
- **13 deployed desktop/mobile checks pass, one desktop-only skip**, including navigation, narrow/landscape layout, collection, monitoring, history and error/retry. These exercise the deployed assets with mocked API/session responses; they do not represent an authenticated production administrator data review. Final PostgreSQL policy/count verification remains successful after the normal collector run.

No saved article was deleted and no external LLM audit was invoked. The content correction is released. Automatic NOAH/DRRMO-assisted publication/zone plotting remains the next integration bundle in the original plan.

## Strict actual-flood collection follow-up — October 3

The Collection screenshot exposed a remaining admission loophole and misleading legacy statuses. The two displayed stories were first saved on September 30. Both fail the released v3 body's local-flood test; the October 3 collector inspected 95 feed entries and saved zero candidates. However, v3 still admitted unreadable metadata-local leads, and previously saved place mentions without flood facts were labeled “Needs checking.”

The v4 follow-up requires affirmative flooding evidence in the reporting body, grounded in Metro Manila. New blocked/unreadable articles generate visible discovery notices and body-error telemetry without being saved as candidates. Failed refresh diagnostics remain available for previously qualifying flood evidence without relabeling its old body. Cached and duplicate rejected leads cannot bypass admission. Forecasts, simulations, rescue drills, habitual references, projects, foreign floods and caption-only mentions are excluded by shared server-owned reading/discovery rules. Floodwater headlines are included in the broad retrieval vocabulary; retrieval remains separate from admission.

Completed extractions with zero qualifying locations and unverified legacy bodies are labeled `excluded`, have no actionable mention count, and stay out of default attention. They remain accessible via **Excluded from flood reports** / **All saved articles**, along with immutable extraction history. Classification occurs on the backend before counting and pagination. Version `rules-psgc-osm-2026-10-03-v4` and extractor `taglish-rules-v1.2` preserve older runs. No SQLAlchemy model, migration or dependency changes are needed.

Cases use paraphrases of [GMA's measured flooded-road report](https://www.gmanetwork.com/news/topstories/metro/956643/flooded-roads-metro-manila/story/), the previously cited UP-PGH construction and Taguig investigation reports, and adversarial English/Taglish variants. Historical publisher examples are tests, not inserted live observations.

- **341 backend tests pass**, including admission, cached/duplicate handling, failed refreshes, immutable processing, Collection/main/detail agreement and caption-only legacy artifacts.
- **15 read-only PostgreSQL checks pass**. The unchanged 24-article / 30-run saved set produces zero qualifying locations; all **24 legacy articles are excluded**, with **zero default attention articles**.
- TypeScript passes. **15 distinct desktop/mobile UI cases pass, one desktop-only skip** across the full suite plus focused recheck. The first new test assumed a native select; the recheck operates the existing custom dropdown. Coverage includes excluded-history access, 320px layout, keyboard/navigation and errors. API/session responses are mocked.
- Final v4 production rollout and saved-version processing are complete. Finite tests do not establish universal 100% classification accuracy; strict screening can defer legitimate articles with missing or ambiguous evidence.

Author / resolver: [@roicambe](https://github.com/roicambe) (Roi Cambe).

### v4 backend release verification

- Backend Cloud Build `3f934121-0d73-4f30-b65e-24b740f74116` succeeded. API `lanes-api-00049-q25` serves 100% traffic. The API and scheduled collector share digest `sha256:ab3fbf2295ae09b930d836b93f2159bfd1bc6d3a17779a3671d678d58985b318` (`news-screening-20261003-v4`). Health is 200; results/Collection return 401 without credentials.
- Saved-only execution `lanes-news-discovery-mrlzb` succeeded: ten v4 completions, **40 total extraction runs**, ten source versions and 24 saved articles. All previous 30 runs remain intact. Migration remains `c5a7e9d2104f` with no additional schema change.
- Normal execution `lanes-news-discovery-rx52c` succeeded; its telemetry records **55 feed entries**, **zero saved candidates**, and zero body errors. The normal `--discover --process --limit 50` job arguments remain unchanged. Both audited project bodies are rejected and all 24 legacy articles remain excluded, with zero qualifying locations or default attention items.
- Firebase build `b447a884-9de1-4c03-b1e7-e1c6459800b8` succeeded. Frontend `lanes-frontend-build-2026-10-03-002` serves 100% traffic; Firebase confirms rollout complete. All **15 deployed desktop/mobile cases pass, one desktop-only skip** (API/session mocked). The real unauthenticated website API proxy returns 401 for results and excluded Collection, confirming the protected route boundary. The temporary UI test server on port 3002 was stopped; the user's port 3000 was not modified. A later read found the pre-existing local API port 8000 not running; no local/deployed equivalence is inferred from that stopped endpoint.
