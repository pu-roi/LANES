# Phase 36: Open article fallback check

> **Checked:** October 02, 2026, 2:44 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Scope and result

### Additional pre-push verification — October 2

The developer requested a push to roi-branch conditional on certainty that existing features were preserved, then explicitly accepted the database schema addition/migration requirement and required the API, security, and merge skills. Actual AGENTS.md, DESIGN.md, and those skills were read. The remote roi-branch and local source branch share `4b5ea5d` with no divergent commits, so no newer branch work would be overwritten. The configured Cloud Build GitHub trigger targets `^main$` only; roi-branch push would not trigger that deployment. `cloudbuild.yaml` executes and waits for migrations before API/collector deployment. Main is not an authorized push target.

A second guarded disposable database, `lanes_p3_verify_push_20261002`, was created on the existing Cloud SQL instance. `alembic upgrade head` exited 0. Four real PostgreSQL queue checks and four existing flood-event lifecycle/metrics/rejection/analytics cases passed together (8/8). Separately isolated subprocesses passed OTP lifecycle (1), archive report/zone flows (2), saved-place limits (1), and login rate limits (1). The first profile/password case hit a harness error: explicit seeded user ID 1 had not advanced PostgreSQL's sequence. After correcting only disposable users/roles sequences, that unchanged profile/password test passed (1). No production source or test file was altered by these checks, and no message/email was sent outside mocked test behavior.

This adds fourteen distinct passing cases to the earlier 371, totaling **385 validated cases** from the 398 collected set; thirteen legacy/live-provider cases remain unexecuted. This is evidence of compatibility, not a 100% guarantee. Existing endpoint/schema fields are preserved; there are no removed definitions/files/frontend changes. Added code passed syntax/secret-marker checks; runtime imports use existing declared FastAPI/Pydantic/httpx/SQLAlchemy/Alembic packages and the standard library. Requirements/package files need no addition.

The second disposable database was deleted, the proxy stopped/removed, and only the original `postgres`/`lanes` databases remain. Production schema/data are unchanged. The reviewed bundle is ready for a local feature-branch commit; roi-branch publishing remains conditional on acceptance of the documented limits. Release/live collected-body/incident-grouping acceptance is separate. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

### Branch compatibility review — October 2

Reviewed `codex/news-extraction-persistence` including all uncommitted/new files against `roi-branch`, local `main`, and freshly fetched `origin/main`. No merge, reset, commit, push, deployment, or production database write ran. Local HEAD/roi-branch/origin/roi-branch remain `4b5ea5d`; local main remains `78bda26`; fetched remote main is `372dc60`. Fetch changed only the remote-tracking reference. The local main checkout is substantially older than remote main. A local branch shares its working folder and uncommitted edits; commits or separate worktrees are needed to isolate later branch switching.

**Static and runtime contract findings:** 25 tracked edits plus six new files are confined to backend/news tests/documentation. No frontend or deployment/dependency file changes, deleted tracked files, removed Python definitions, or removed API operations were found. Existing search helper signatures only gained optional parameters. App import/OpenAPI generation succeeded for current code and source snapshots of all three baselines, using an in-memory import loader rather than switching checkouts or executing startup/database work.

| Compared baseline | Existing API operations | Existing operations/fields removed or changed by this new work | Additions |
|---|---:|---|---|
| `roi-branch` | 149 | None; existing schema properties and database column definitions preserved | Three saved extraction/status/processing operations; two approved news tables |
| Latest `origin/main` | 148 | None; existing schema properties and database column definitions preserved | The same three operations/two tables plus the earlier staff open-leads operation |
| Older local `main` | 109 | No removed operations; twelve operation definitions/five schema properties/four existing tables differ because this checkout predates prior delivered work | Older accumulated feature additions; not evidence of new-feature damage |

**Broader regression result:** All 398 backend cases collect. A 35-module isolated run exercised 373 cases: 368 passed, four guarded PostgreSQL cases skipped because no disposable URL was configured, and one cleaner fixture had a denied temporary directory. The cleaner's four tests passed on the normal-permission retry, resolving that setup error; three overlap the broad pass, so 369 distinct cases were validated. Two additional existing geocoding normalization/representative-coordinate cases passed, giving **371 distinct passing cases** in this review. No new runtime regression was found. Existing multipart/naive-UTC deprecation warnings remain. Routing/Valhalla policy, carriageway validation, report media failure, feed/privacy schemas, authorization, retention, spatial prototypes, and the full news worker/extraction tests are covered. Previous four PostgreSQL/migration checks above remain the recorded evidence for the new tables; they were not rerun here.

**Coverage limits and required release ordering:** Twenty-three remaining cases in twelve legacy database/live-provider modules were not executed. They use shared configured sessions, live providers, import-time auth overrides, or a missing `db` fixture; those test files/conftest are unchanged from roi-branch. See [BUG-076](../others/bug-log.md#bug-076-full-backend-tests-lack-isolated-database-and-auth-fixtures). This is not a full production integration pass. The new RSS/manual save paths enqueue into the two added tables, so release must run migration `f29b6c8d104e` before the new API/collector revision; an unmigrated runtime would fail those news writes. Database/live integration acceptance remains open. Existing public report/event/zone models and routing/auth services were not modified by this new work. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

### Priority 3 durable extraction — October 2

The developer replied “okay proceed” after the next-task explanation identified the two-table schema approval requirement. This authorizes the reviewed additive extraction contract. Earlier deferral notes below are historical; Priority 2 live positive matching is still unverified.

Implemented migration `f29b6c8d104e`, immutable canonical input snapshots and version/pipeline-keyed typed rules-only artifacts; article transactions preserve prior successful bodies and enqueue valid current inputs. Manual repeats reuse the existing publication/input identity; revisions retain both versions. Blocked/empty/oversized/moderated inputs do not create new work. Completion is independent of moderation and never calls the auditor or public ingestion.

Workers use short PostgreSQL `FOR UPDATE SKIP LOCKED` transactions, fresh UUID ownership, five-minute leases, and conditional completion while the lease is valid. Transient extraction errors retry after 60/120/240/480 seconds, then fail at attempt five. Permanent invalid inputs fail visibly. Expired attempts recover within that bound. Storage failures propagate instead of reporting completion; stale workers cannot overwrite another lease. Due processing runs after 304 responses and independently through `--process-saved`. Default discovery enqueues but does not perform CPU extraction without `--process`.

**Verification:** The combined news/extraction regression run passed **223 tests** in 164.89 seconds. After adding the manual revision/storage-failure case and its safe error handling, the final focused worker/API/CLI rerun passed **17 tests**; sixteen overlap the combined run, giving 224 distinct controlled cases. The existing `python_multipart` deprecation warning remains. Coverage includes actual rules/PSGC output, preserved IDs/times, immutable revisions, eligibility, empty claims, retries/exhaustion, stale leases, restart/delivery idempotency, authentication/rate limits, manual revisions/storage failures, and 304 independence. External audit/ingestion methods are prohibited by these fixtures. Four additional real PostgreSQL cases passed in 10.33 seconds for migration-enforced immutable snapshots/checks, concurrent idempotent enqueue, SKIP LOCKED claims, stale ownership, and persisted output across new sessions. Whitespace checks passed.

Docker Desktop had no usable engine pipe. Migration verification instead used a disposable `lanes_p3_verify_20261002` database on the existing Cloud SQL instance through Google's temporary localhost Auth Proxy, without a new instance or paid source. The connection/database guard was checked before PostGIS creation. Full `alembic upgrade head`, downgrade to `a83c1d4e7b92`, and upgrade again each exited 0. The four PostgreSQL tests require an explicitly configured `LANES_NEWS_TEST_DATABASE_URL` and refuse databases outside `lanes_p3_verify_*`. The disposable database was deleted and proxy stopped after verification; production rows/schema were untouched.

Commands from `backend/`, with environment database credentials configured separately:

```powershell
.\venv\Scripts\python.exe -m alembic upgrade head
.\venv\Scripts\python.exe -m pytest tests/test_news_processing.py tests/test_news_processing_postgres.py -q -p no:cacheprovider
.\venv\Scripts\python.exe -m scripts.run_news_discovery --process-saved --limit 50
.\venv\Scripts\python.exe -m scripts.run_news_discovery --discover --process --limit 50
```

The production migration, image/job argument update, live automatically collected body-to-artifact check, and release restart delivery remain pending. Collector/staff processing is implemented, not deployed. This queue retries extraction of captured bodies; publisher retrieval retries and distributed GDELT pacing remain separate. Incident grouping, independent corroboration, public alerts, and zone updates are later contracts. No new runtime package, push, or deployment was added. Existing evaluation/plans were reused, so the documentation index needs no new entry.

### Continued Priority 2 acceptance — October 2

Read-only `--discover --dry-run --extract` runs around 12:56 AM and 1:19 AM Manila (the latter after the repair) returned HTTP 200 from all six feeds, parsed 95 entries each (GMA 15, Inquirer 20, Rappler 10, Philstar 10, BusinessWorld 30, Interaksyon 10), and returned no notices, candidates, or extractions: `outcome=no_candidates`, exit 0. The newest feed publications ranged from October 1 11:07:39 UTC to 16:42:31 UTC. This verifies current feed parsing, not the absence of floods or successful live incident matching.

Public publisher searches surfaced September 30 flood-control investigation stories and older actual flood reports. Neither closes current automatic-discovery acceptance. The first attempt to retrieve/extract the [September 30 Philstar investigation story](https://www.philstar.com/headlines/2026/09/30/2559999/dizon-denies-cover-taguig-flood-control-probe-well-go-where-evidence-leads-us) did not execute because automatic approval review reported a usage-limit error. The account status subsequently showed ordinary usage allowed, 7% five-hour usage and 1% weekly usage; the error could not be confirmed as exhaustion of this account. One retry through the same approval process was approved and succeeded. The exact cause of the review failure remains unknown; no approval setting was bypassed or changed.

**Live negative-body check passed:** The permitted retry retrieved 2,439 characters without a retrieval/extraction error. Shared rules extraction returned five location mentions, all `flood_mentioned=false`, condition `unknown`, no depth, and review-only actions. `body_has_metro_manila_flood_claim` returned false. This verifies the repair against one real, manually selected administrative article; it is not automatic discovery, alternate recovery, positive live flood matching, or general extraction-accuracy proof. No database session, auditor, ingestion, or public-state write ran.

A constructed local control nevertheless exposed a real defect: “flood control projects in Taguig City” became a body-grounded active flood claim. Six of the first seven regressions failed before the repair. Shared Taglish extraction now masks infrastructure/program phrases only for evidence-word checks and excludes policy-only sentences/clauses. Explicit depth-gauge wording remains eligible; ordinary project dimensions do not become flood depth. Original evidence text and character offsets are retained. A later boundary check caught overly broad suppression of “knee-deep water”; the final guard preserves this wording and gauge-only reports alongside flood-control mentions.

The **13 focused regressions pass**, covering spaced/hyphenated terms, anti-flood programs, rising funding, wall measurements, metadata-only input, mixed articles, separate road clauses, source offsets, and actual RSS/body shortlisting. These are constructed controls with mock HTTP, not live publisher-body validation. Metadata-local headlines can still be captured as review leads; the repair prevents policy text becoming flood observations. No dependency, model, migration, public-state write, push, or deployment was added.

Final combined regression verification: **207 passed**, with the existing `python_multipart` deprecation warning. Whitespace verification passes. Command from `backend/`:

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_taglish_extraction.py tests/test_news_saved_extraction.py tests/test_news_discovery.py tests/test_news_open_search.py tests/test_news_auto_ingestion.py tests/test_hybrid_extraction_service.py -q -p no:cacheprovider
```

Priority 2 remains active. Live automatically discovered flood/update matching and rollout remain open; prepared Priority 3 previews/storage design remain deferred.

### Priority 2 acceptance closeout — scope clarification

The developer clarified that the selected next action was to finish and assess Priority 2 before proceeding. Priority 3 preview/code/design was prepared prematurely and is deferred; its schema proposal is not part of this acceptance. No model/migration changes were made. This closeout reviews existing evidence; it does not claim another test run or live capture.

| Priority 2 acceptance item | Evidence | Assessment |
|---|---|---|
| Flood headlines with absent location can be checked against article bodies | Controlled body-only Metro Manila and non-local/incidental-weather fixtures | Pass locally, bounded at five extra probes/run |
| Retrieval bounds and failed/unknown/future inputs remain visible | Probe budget/error/future tests, API/CLI notices | Pass locally |
| Freshness and newer eligible coverage | Publication ordering, seven-day boundary, future timestamps, observation freshness tests | Pass locally; missing observation time does not become publication time |
| Same-city/road observations distinguish later changes from older evidence | Higher/lower depth, clearance, older republished observation, simultaneous conflict, segment/recurrence/multi-road tests | Pass locally as unverified update proposals |
| Copied articles retain source attribution and do not become independent evidence | Normalized-body duplicate and schema serialization tests | Pass locally for exact normalized copying; broader syndication remains later work |
| Updated URLs refresh without relabeling prior evidence after failure | SQLite refresh/duplicate/older-version tests and activation guard | Pass locally |
| Current live feed parsing | Latest recorded six-feed HTTP 200 snapshot, 95 parsed entries | Pass for feed parsing |
| Live automatically discovered current flood/update matching | Same snapshot returned `no_candidates`; historical references were manually supplied | Unverified; cannot be passed using empty feeds or historical fixtures |
| Production rollout of revised Priority 2 code | Changes remain local/unpushed/undeployed | Pending |

The earlier combined regression suite was **152 passed** (including Priority 3 previews), with the existing `python_multipart` warning. Priority 2's own earlier repairs passed the 141-test suite. The continued check above found and repaired an additional policy-text false positive; those earlier counts alone did not establish that case. Persistent incident storage/grouping, durable retry queues, and live-zone updates are later integration contracts. Live/rollout acceptance stays open. The prepared Priority 3 storage proposal is deferred and no approval is sought for it during this closeout.

### Priority 3 saved-extraction preparation and scope correction

Durable grouping, processing retry, and actual zone updates belong to later integration work. The earlier interpretation of “proceed” as Priority 3 preparation was premature and has been corrected: this section records already prepared local work, while Priority 2 acceptance remains active. No further Priority 3 work or schema change is authorized by this historical record.

The shared `_extract_article_inputs` now serves collected and saved article previews. Saved inputs retain real IDs, original publication time, URL/publisher provenance, and canonical-JSON SHA-256 identity. Fetch time/article ID do not change evidence identity; equivalent publication offsets hash identically; changed bodies hash differently. Missing/errored/oversized bodies do not enter extraction. Per-input exceptions expose the class while retaining later outputs.

Staff `GET /api/v1/admin/news/candidates/{article_id}/extraction` and bounded `--extract-saved --dry-run --limit 50` return actual rule/PSGC claims. SQLite SQL monitoring, real HTTP/API requests, and actual CRUD/CLI tests verify 401/403/404, source IDs/time/depth, stable hash, failed-body rejection, structured JSON, visible batch failures, empty-list outcomes, invalid-mode rejection, and zero SQL writes or evidence/review changes. Tests prohibit external audit and ingestion. Focused checks found and fixed a missing SlowAPI `Response` injection and nested Pydantic JSON stringification; the canonical-city expectation matches PSGC's `City of Pasig`.

Final regression command from `backend/`:

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_news_saved_extraction.py tests/test_news_discovery.py tests/test_news_open_search.py tests/test_news_auto_ingestion.py tests/test_hybrid_extraction_service.py -q -p no:cacheprovider
```

**152 passed**, with the existing `python_multipart` warning. These saved rows are controlled fixtures, not live automatic processing. No model, migration, dependency, deployed job, push, or deployment changed. The [two-table storage/worker contract](../plans/smart-auto-activation-and-hybrid-nlp-plan.md#priority-3-extraction-handoff--october-2-approved-implementation) is reviewable and awaits explicit approval before persistence implementation. Existing documents were reused; no new document/index entry was needed.

### October 2 follow-up: Observation ordering and refresh safety

The earlier blanket depth/status conflict rule is superseded. `event_review.road_updates` compares explicit observation times per city-qualified road, retaining prior/alternate depth and condition. Knee-deep at 10 AM followed by chest-deep at 11 AM becomes `possible_depth_status_update`; decreasing depth also follows the newer observation, and timed subsidence becomes `possible_clearance_update`. A newer publication describing an older observation returns `older_observation`. Same-time disagreement is a conflict; stale observations older than twelve hours, missing times, different segments, ambiguous latest states, continuity gaps over one day, and possible recurrence after clearance are separate outcomes. Publication/index timestamps never become observation timestamps. These are source-linked proposals, not verified incident matches or public writes; original-body and segment/continuity gaps remain explicit.

Discovery orders local then unknown-scope leads newest first within each feed. Feed fallback checks at most five alternate feeds and chooses the newest three eligible reports across that bounded set, requiring each publication inside seven days and within two days of the original. The probe cap is still global across discovery runs; there is no promise of global newest selection across every publisher when earlier feeds exhaust that cap.

A same-URL publication revision now refreshes the body even if metadata wording is unchanged. A failed refresh preserves the previous body with its original metadata/date, exposes the error, and remains retryable when feed entries are returned again. Duplicate provenance cannot relabel it. Older feed versions do not overwrite a newer stored snapshot. The dormant ingestion path treats retained errored bodies as unavailable and rejects activation despite a cached approval label. The staff fallback accepts retained bodies with a current fetch error, without altering original evidence. This does not add an article-version archive, durable retry, event persistence, or production ingestion integration.

The final combined discovery/open-search/ingestion/hybrid regression command below passes **141 tests**, with the existing `python_multipart` warning. New coverage uses actual rules/PSGC extraction for later higher/lower depth, clearance, older republished observations, simultaneous disagreement, stale evidence, missing clocks, different segments, recurrence, newer corroboration, and per-road ordering alongside unrelated warnings. HTTP/RSS/SQLite fixtures verify newest feed selection, seven-day boundary rejection, same-URL publication refresh, blocked refresh with duplicate provenance, preserved prior body/date, older-feed overwrite rejection, authenticated fallback for retained errored bodies, and zero activation despite a forged cached approval.

Read-only live rerun on October 2 with `--discover --dry-run --extract`: all six feeds returned HTTP 200 and parsed 95 entries (15/20/10/10/30/10), with no notices/candidates and outcome `no_candidates`. This proves parsing, not live update matching or the absence of floods. The initial broad Priority 3 hold was subsequently corrected: grouping, persistent retries, and actual zone updates are later contracts. The developer authorized saved-extraction preparation; live matching and rollout remain open. Changes are local, unpushed, and undeployed. No dependencies/models/migrations changed.

The staff-only `GET /api/v1/admin/news/candidates/{article_id}/open-leads?retrieve_articles=true` path searches GDELT and can retrieve up to three approved alternate publisher bodies. It does not replace the blocked original or persist alternate evidence. This is an on-demand backend feature; automatic same-event matching and scheduled integration remain unfinished.

## Offline verification

Commands from `backend/`:

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_news_open_search.py tests/test_news_discovery.py tests/test_news_auto_ingestion.py -q -p no:cacheprovider
```

Initial retrieval and malformed-URL repairs passed 55 tests; the final combined suite after the pacing repair passed **70 tests**, with one existing `python_multipart` deprecation warning. `git diff --check` found no whitespace errors.

Coverage includes:

- Staff lookup authentication and candidate provenance checks.
- API serialization of alternate text, publisher ID, fetch time, and review status.
- Original article text, fetch error, review state, and stored article count remain unchanged after retrieval.
- Unapproved or disabled publishers and the original publisher are not fetched as independent evidence.
- At most three alternate articles are requested; off-domain redirects are rejected.
- Malformed indexed URLs are skipped without losing valid results.
- Invalid JSON, invalid article-list shape, oversized responses, and HTTP 429 surface errors.
- A failed title search does not trigger an immediate RSS-phrase search.
- Existing ingestion safety checks continue to reject unsupported activation.

Offline fixtures do not prove that live articles will be accessible, complete, or about the same event.

## Live checks

Read-only network checks used the prior Inquirer title, “Quezon City LGU gives evacuees antibiotics for leptospirosis treatment.” The initial sandbox request returned `ConnectError`; an enabled-network retry returned `ConnectTimeout`. A longer-timeout request reached an HTTP error, and a diagnostic request confirmed **HTTP 429** from the GDELT URL as observed from this environment. No index hits or live alternate bodies were recovered. This does not establish the source of the throttling or prove GDELT is globally unavailable.

The configured GMA news feed succeeded with **HTTP 200**, parsed **15 entries**, and reported no error using the same enabled-network environment. A separate web-tool GDELT open was also unsuccessful. No Cloud Run verification was performed during these initial checks; the later diagnostic is recorded below.

## Repairs and remaining work

### Request pacing follow-up (October 1, 12:53 PM)

`news_open_search_service.py` now shares one gate across requests in each process. A successful query is cached for 600 seconds, with at most 32 entries. Uncached requests have a conservative 10-second gap after the previous request completes. Concurrent requests receive a deferred response instead of issuing parallel calls. The normal gap may wait at most 10 seconds in the synchronous endpoint; longer cooldowns return immediately.

Rate limits, including the provider's HTTP-200 plain-text throttle notice, and transient connection/server failures start a 60-second cooldown. Consecutive failures double the delay up to 900 seconds; success resets the failure count. A longer `Retry-After` (seconds or HTTP date) is honored. The lookup returns `retry_after_seconds`, and the API exposes `Retry-After` while retaining existing staff authentication and route limits. Provider bodies and private transport diagnostics are not included in API errors. Retry-After semantics follow [RFC 9110](https://datatracker.ietf.org/doc/html/rfc9110#section-10.2.3); 10 seconds is LANES's conservative policy, not a verified official GDELT quota.

A live request returned HTTP 429. An immediate repeated lookup was stopped locally with a 60-second cooldown; the instrumented HTTP client recorded **one outbound request total**. Thus repeat suppression works against a real failure, but live article retrieval success remains unverified.

A controlled single retry more than 60 seconds later returned `ConnectTimeout` without an HTTP response, and correctly entered a 60-second cooldown. Live index success remains unverified; no further requests were issued for this check.

Tests use a fake monotonic clock, so pacing/cooldown checks do not sleep or contact GDELT. Added coverage includes concurrent in-flight calls, cache expiry/eviction, safe copies of cached results, cached results during another query's cooldown, 60/120/240/480/900-second backoff, longer provider delays, HTTP-date headers, malformed headers, HTTP-200 throttling, server/connection failures, and API retry metadata.

The combined discovery, open-search, and ingestion safety suite after the pacing repair: **70 passed**, with the existing `python_multipart` deprecation warning. Whitespace verification passes.

This is **per-process coordination**. It resets on restart and cannot prevent combined traffic from multiple workers/Cloud Run instances or unrelated users sharing an egress IP. Before scheduled multi-instance operation, design shared coordination using the existing infrastructure; any schema changes require separate approval. No new schema, dependency, or paid service was added.

Malformed URL handling was repaired in `news_open_search_service.py`. HTTP errors now include their status code without exposing the response body; failed searches stop before the immediate phrase fallback. Regression coverage is in `test_news_open_search.py`, with retrieval-option integration coverage in `test_news_discovery.py`.

Before scheduled integration, confirm a successful GDELT lookup from the target runtime after throttling clears, coordinate pacing across replicas if deployed with multiple instances, broaden same-event discovery beyond exact title/excerpt phrases, and validate publication/observation date, location, and flood status from each fetched article. An index-seen time is not an event time. All fetched alternate bodies still require event review.

### Connection diagnosis and independent feeds (October 1, 11:02 PM)

One instrumented GDELT request was made locally and one through an execution-specific override of the existing `lanes-news-discovery` Cloud Run job in `asia-east1`. Execution `lanes-news-discovery-jlc6w` ran diagnostic Python only and completed successfully; it did not run discovery, open a database session, or change the job's saved configuration. A successful diagnostic execution means the tracing ran, not that GDELT supplied article evidence.

| Environment | TCP complete | TLS complete | Response received | Result |
|---|---:|---:|---:|---|
| Local | 0.41 s | 8.83 s | 10.39 s | HTTP 429 |
| Cloud Run | 0.19 s | 11.05 s | 12.19 s | HTTP 429 |

Elapsed times are measured from request start. Thus TLS took about 8.42 seconds locally and 10.86 seconds in Cloud Run. Both responses identified `GDELT Server`, asked callers to space requests by five seconds, and supplied no `Retry-After`. This proves slow TLS can exhaust the staff client's 3-second connect budget; it does not identify why GDELT's handshake is slow or which rate-limit bucket rejected the diagnostic. The Cloud Run diagnostic used a Quezon City flood query with August 16–20 bounds rather than the exact article-title query.

GDELT requests now override the client timeout with **15 seconds to connect / 20 seconds to read** and retain the existing 10-second pacing, bounded cache, and exponential cooldowns. The article-fetch timeout remains unchanged. A regression checks this per-request override even with a client configured for 3-second connect / 8-second read. Provider JSON must contain an actual `articles` list; an empty object or non-object payload is an explicit failure rather than a fabricated successful no-hit search.

Retrieval mode adds a Metro Manila place/flood query when prior title/excerpt searches succeed without an alternate, using publication ±2 days clamped to the last 90 days. It stops further index queries on provider errors. Separately, approved-publisher feeds can supply leads even after GDELT throttles: originals must have a known publication date within seven days and a Metro Manila place clue; feed entries must share that clue, contain flood wording, and have a known publication within two days of the original. At most five feeds and three alternate bodies are requested. Feed publication time is returned as `published_at`; `seen_at` remains null. Metadata similarity never verifies a shared event.

The current combined command above passes **87 tests**, with one existing `python_multipart` deprecation warning. New coverage includes realistic RSS parsing after simulated GDELT 429, alternate body parsing, retained provider errors/retry guidance, date/place filtering, probe/body bounds, failed-feed errors, no unnecessary feed polling when an approved index alternate exists, event query date bounds/cache separation/pacing, read-only CLI behavior, and authenticated API serialization with unchanged stored originals.

#### Live limitations

- The exact Inquirer AMP URL returned HTTP 403 with `server: cloudflare` and `cf-mitigated: challenge`, without article text.
- After the timeout fix, the latest exact-title diagnostic completed TCP/TLS, recorded HTTP 429 at 10.88 seconds, and returned `outcome=no_alternate_body`, exit code 1. Further index searches were correctly skipped. The August 18 original was outside the recent-feed window.
- A prior call produced an empty parsed result before strict article-list validation was added. It does not prove successful index retrieval or a valid no-hit response.
- Live configured feeds parsed GMA 15 entries, Rappler 10, Philstar 10, BusinessWorld 30, and Interaksyon 10; Inquirer's feed probe failed. These snapshots contained no matching recent Metro Manila flood leads. Working feeds prove feed access, not successful same-event recovery.
- A previously identified [Philstar August 17 flood report](https://www.philstar.com/nation/2026/08/17/2549888/list-flooded-metro-manila-areas-aug-17) supplied **8,933 characters** through the approved body parser, including Quezon City, Biak-na-Bato, and Sto. Domingo. This manually supplied reference was **not discovered by GDELT** and was not verified as the same event as the Inquirer article.
- Current source changes are local; the deployed collector was not updated. Scheduled integration, shared coordination, automatic same-event verification, and live automatically discovered evidence remain open. No dependencies, migrations, or SQLAlchemy models changed.

#### Repeatable read-only check

From `backend/`:

```powershell
.\venv\Scripts\python.exe -m scripts.run_news_discovery --open-leads --article-url "https://newsinfo.inquirer.net/2287229/quezon-city-lgu-gives-evacuees-antibiotics-for-leptospirosis-treatment/amp" --title "Quezon City LGU gives evacuees antibiotics for leptospirosis treatment" --published-at "2026-08-18T15:10:00+08:00" --retrieve-articles --trace-network
```

The diagnostic prints body character counts rather than article text, safe transport timings/status, and a read-only flag. Retrieval mode returns exit code 1 when no alternate body is available, even if index links exist; this is intentional failure reporting. No database session is opened by this mode.

### User-supplied browser automation research

The [Clawbrowser article](https://clawbrowser.ai/blog/browser-automation-without-getting-blocked/) describes browser identity, network signals, behavior, and sessions, and promotes its own managed browser. Its claims do not establish access to the exact Inquirer article or from LANES Cloud Run. The [Reddit discussion](https://www.reddit.com/r/automation/comments/1pi07om/whats_the_most_stable_way_you_have_found_to/) principally concerns layout changes and brittle automation selectors, rather than evidence of Cloudflare access. The supplied LinkedIn post could not be retrieved; its contents remain unverified.

[Cloudflare's official browser support documentation](https://developers.cloudflare.com/cloudflare-challenges/reference/supported-browsers/) says automated browsers and Selenium/Puppeteer/Playwright are unsupported for solving production challenges. Therefore a normal browser-rendering experiment could test whether JavaScript rendering supplies the complete story, but cannot be presented as a reliable challenge solution. A future pilot should compare the exact publisher URL locally and in the target runtime, preserve article completeness checks, and record challenge failures. No browser product was installed or integrated in this investigation.

### Live retrieval and collection-to-extraction follow-up (October 1, 11:30 PM)

The developer authorized proceeding with retrieval verification and a controlled collection-to-extraction run. Network-restricted checks first failed at TCP; enabled-network checks below distinguish sandbox failures from publisher/provider responses. No production database, scheduler, image, or job configuration was changed during this follow-up.

| Check | Measured result | What it establishes |
|---|---|---|
| Exact-title GDELT lookup | TCP complete 0.39 s; TLS complete 10.81 s; HTTP 429 at 12.73 s | The corrected connection budget reaches the provider; throttling still prevents index recovery. |
| Exact Inquirer AMP URL through existing Playwright and installed headless Chrome | HTTP 403, title `Just a moment...`, zero characters in an `article` element after an eight-second wait | Ordinary headless browser rendering did not recover this page. No challenge interaction or stealth changes were used. |
| Bundled Playwright Chromium | Executable missing | This browser was not tested; no binary was installed. |
| Cloud Run browser | Not attempted | Local Chrome results do not establish browser behavior in Cloud Run. No browser runtime was added to the production image. |
| Initial live feeds | Five feeds parsed; Inquirer HTTP 200 failed XML parsing | Some feed failures are data-format errors, separate from article-page blocking. |
| Repaired live feed run | All six returned HTTP 200 and parsed: GMA 15, Inquirer 20, Rappler 10, Philstar 10, BusinessWorld 30, Interaksyon 10 | The repaired parser restores Inquirer feed collection in this snapshot. |
| Live collection with rules extraction enabled | Zero shortlisted candidates; `outcome=no_candidates` | Feed polling worked, but no live flood candidate exercised automatic discovery-to-extraction. |
| Manually supplied historical Philstar September 9 article through the shared diagnostic extractor | 2,708 body characters; 29 claims; all `flagged_review`; no fetch/extraction error | Live body retrieval and rules extraction work for this reference. It was not discovered by a feed or GDELT and does not establish current flood truth or extraction accuracy. |

#### Repairs from the live investigation

Inquirer's HTTP-200 RSS contained undeclared HTML character references `hellip`, `nbsp`, and `rsquo`; ElementTree reported an undefined entity at line 92, column 54. The bounded parser now replaces only known HTML names outside CDATA with numeric XML references. XML's five predefined escapes and CDATA remain intact; unknown custom entities and DTD/external-entity declarations still fail. A second size check bounds normalized data. A separate unauthenticated-header probe returned HTTP 403, so live feed availability can vary with request conditions; the table records the normal LANES client result.

Feed parse failures now retain their received HTTP status. HTML/challenge responses have explicit failure messages, and a valid empty feed is a healthy collection outcome rather than a network failure.

The existing collector script supports:

```powershell
.\venv\Scripts\python.exe -m scripts.run_news_discovery --discover --dry-run --extract
```

`--extract` requires both `--discover` and `--dry-run`. The shared `extract_discovery_candidates` service uses the actual `HybridExtractionService` in `rules_only` mode, does not call the external auditor or ingestion service, and returns visible per-candidate errors. Missing bodies are not treated as extracted evidence. The JSON distinguishes `no_candidates`, `no_flood_claims`, `claims_extracted`, and `extraction_errors`, with claim actions, canonical places, observation time, and geometry provenance. Invalid non-dry-run extraction modes are rejected before any database session.

Controlled tests exercise real RSS parsing → article HTTP response → story parser → rules/PSGC extraction → review action through the CLI. They verify Maybunga knee-depth extraction, blocked-body failure, no database/auditor calls, safe per-candidate exception reporting with later candidates retained, valid empty feeds, and HTML-entity compatibility without enabling custom XML entities. This is a controlled fixture test, not a live automatically discovered flood article.

Automatic production extraction/publication, alternate-event matching, and verified-segment routing integration remain unfinished. The browser experiment yielded no reason to add Playwright to the backend production dependency list. All changes remain local.

Final validation after the RSS and diagnostic repairs:

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_news_discovery.py tests/test_news_open_search.py tests/test_news_auto_ingestion.py tests/test_hybrid_extraction_service.py -q -p no:cacheprovider
```

**107 passed**, with the existing `python_multipart` deprecation warning. `git diff --check` passes. No dependency, SQLAlchemy model, or migration was changed. The parser/security review retained approved-domain retrieval, body/feed size bounds, CDATA/XML escaping, custom-entity rejection, and fail-closed activation. The diagnostic does not call production ingestion or an external model.

### Priority 2: Body-only locations and alternate event review (October 1, 11:55 PM)

Priority 1 remains partially complete: controlled retrieval/parser checks pass, but live automatic recovery of the blocked original is unverified. The developer authorized continuing Priority 2 independently.

The collector now prioritizes metadata-local flood headlines. A flood headline with unknown scope can consume one of five extra body probes across the entire run. Accepted extra candidates require an extracted local flood claim; incidental Manila weather-office mentions in a Cebu flood story do not establish local scope. Explicitly non-local city/province feed clues are skipped, future publication times are not fetched, and failed/body-scope/budget results appear as run notices. Accepted URLs and seen requests are separate so rejected duplicate entries cannot become saved candidates; accepted cached bodies can be reused on repeat runs.

Alternate retrieval now includes `event_review`: shared specific Metro Manila places, shared city-qualified flood roads, context conflicts, missing evidence, and a duplicate-body source URL when applicable. Publication dates more than two days apart, observation times more than one day apart, differing road/city context, differing reported depth, and negated/forecast/subsided claims are visible review concerns. Depth/status changes may be updates within one event; these notes do not prove different events. Index-seen time never substitutes for publication time. A shared road name in another city does not establish overlap. Bodies copied across different publisher domains are flagged through normalized fingerprints rather than counted as independent confirmation. The strongest label is `possible_event_overlap`, with original body/observation-time gaps still exposed; there is no verified-event or auto-approval outcome.

Focused new tests passed for body-only local discovery, incidental-weather rejection, blocked-body notices, run-wide budgets across sources, future dates, accepted/rejected duplicate persistence and cached-body reuse, city-qualified event context, date/depth/status differences, missing publication time despite index-seen time, and copied-body serialization. The same combined discovery/open-search/ingestion/hybrid command above now passes **123 tests**, with the existing `python_multipart` warning. Whitespace checks pass. No dependency, model, or migration changed.

The revised live `--discover --dry-run --extract` run parsed all six feeds (95 entries total) with no notices or shortlisted candidates. It did not exercise a live body-only flood report or alternate event overlap. All new behavior is local and not deployed.

Remaining limits: discovery still needs flood wording in the feed title/summary; only five unknown-scope bodies are probed per run; notices are response data rather than a durable backlog. Conditional unchanged-feed responses and the probe bound can leave leads unprocessed until a later feed update; no automatic backlog retry is claimed. Partial copying/paraphrased syndication and source ownership are not established by exact normalized-body matching. Durable event grouping, complete same-event verification, broad live accuracy, independent corroboration, and automatic publication remain pending.
