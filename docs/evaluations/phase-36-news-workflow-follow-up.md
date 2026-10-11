# News Intelligence workflow defect follow-up

> **Last Updated:** October 03, 2026, 7:39 PM
> Author: [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Scope and outcome

The developer authorized fixing existing News Intelligence features that do not perform their intended job after the [September 9 replay](phase-36-september9-production-day-replay.md). Three actual agents investigated extraction, discovery/processing and frontend contracts, implemented disjoint changes, and independently reviewed integration. This is a bounded news-workflow review, not an audit of every application feature.

Current local pipeline is **v8**, extractor **v1.6**. The developer explicitly approved `passable_with_caution` in the claim/API contract. Existing JSONB stores it; no SQLAlchemy model, migration or dependency changed. No production write, feed registration, schedule change, deployment or automatic map publication occurred.

## Reproduced defects and repairs

| Defect | Corrected behavior |
| --- | --- |
| Caution became unrestricted `passable_all` for 20 records | Explicit `passable_with_caution`, exact source provenance, unspecified vehicle types and an explicit hybrid guard preventing automatic closure |
| Independently stated Ortigas knee/Shaw waist or 2 PM/3 PM facts were mixed | Separate independent road predicates and retain each depth/city/clock; genuinely shared subjects retain shared facts and missing clocks remain unknown |
| A naive independent-`and` repair could detach caution/directions | Require the right road subject before its own first predicate; keep shared qualifiers together and cover three-road sequences |
| Bare “Shaw ... flooded” narrative inherited a prior list clock | Finite-verb narrative ends telegraphic list context |
| Successfully fetched publisher denial/forecast/nonlocal correction was discarded | Capture the known article's revised input, process its newest immutable version, hide unsupported claims and retain older source/run history |
| Corrected RSS removed flood wording or named another city and was skipped | Recognize previously verified article/history before metadata admission; retain age/future/older-publication checks and strict admission of new articles |
| Failed refresh with latest pending/failed extraction was excluded despite credible history | Use historical readable evidence only to retain Collection attention, never to revive older main-list claims |
| HTTP failure after a successful denial appeared only in feed telemetry | Record the known article's retrieval error while preserving its corrected body, including place-free revised metadata |
| Collection offered a permanently empty no-locations filter | Remove obsolete selectable option from the shared mobile/desktop dropdown; retain legacy API enums |
| Structured passability was absent from Flood Details | Backend supplies `summary.passability`; the existing responsive facts grid displays Road passability with explicit caution/unknown labels |

These repairs preserve source offsets and uncertainty. They do not claim general natural-language understanding or establish verified map geometry.

## Verification

- **452 related backend tests passed**, one existing `python_multipart` deprecation warning. New files cover passability, publisher corrections and Collection correction history; source attribution tests cover shared/independent clocks, qualifiers, negative/forecast context and exact offsets.
- Full frontend TypeScript `--noEmit --incremental false` and scoped ESLint passed. The first type check's cache-write permission failure was avoided with the equivalent no-cache check. Shared responsive layouts were reviewed in code; no browser implementation/debugging or browser test workaround occurred.
- Independent actual-body comparison matches all **33 September 9 sites and audited facts**, including 20 caution records.
- Private PostgreSQL replay adds three v8 runs to the September 9 subset, now three articles/four source versions/**eight runs**. Earlier history remains intact; repeats create no duplicates. Zero reports/zones remain unchanged. September 24 records are preserved.
- Authenticated frontend-proxy reads match all 33 record keys, source evidence and passability labels; unauthenticated reads return 401. The stable loopback backend is explicitly restarted to load final changes.
- Final visual acceptance remains incomplete because of the previously reported saved browser permission block. The user permits browser use only for the final display check.

Full bodies and private comparison outputs remain ignored artifacts. At completion of the replay and readiness review, changes were uncommitted on `roi-branch`; subsequent branch-publication preparation is recorded below.

## Branch readiness review — October 3

The developer requested senior-planner and merge-coordinator review before deciding to push. Fetching `origin` confirmed `roi-branch` had zero commits ahead/behind `origin/roi-branch`; no incoming branch changes required reconciliation. All application changes were uncommitted during this review. Existing skill edits/new skill folders were inspected as part of the prospective bundle and do not alter application runtime.

The broader regression run passes **555 backend tests**, including routing/provider fallback, flood-depth contracts, administrative authorization, timezone serialization, OSM matching, nationwide geometry and the 452 news-workflow cases. Full frontend TypeScript and scoped ESLint pass again. One existing multipart deprecation warning remains. This is targeted cross-system regression evidence, not an assertion that every application feature was tested. Legacy integration tests that write through the configured application database were not run against shared data.

Dependency manifests, SQLAlchemy models, Alembic source, routing implementation, authentication implementation and deployment configuration are unchanged. Private overrides/captured article bodies remain ignored; deterministic replay tests generate paraphrased inputs without relying on ignored captures. Existing private migration/head verification remains applicable because the migration chain is unchanged. Core feature, stack and database status notes now reflect local v8 while retaining prior verification history. A branch push does not establish production acceptance; final browser display acceptance and the separately documented freshness gap remain open. No commit, merge, push or deployment was performed for this readiness review.

An independent read-only agent reviewed every pending application diff, the launcher, replay script and six new test files and reported no blocking findings. The pending-file secret scan found only explicit dummy database credentials in guard tests. Configuration and bound-engine guards precede replay writes, unexpected replay URLs are rejected, and historical replay cannot invoke ingestion or public-zone writes. Exact real-source replay still requires ignored captures or fresh publisher retrieval, which may yield later revisions; generated regression fixtures are self-contained.

## Documentation preparation before branch publication

The developer subsequently requested senior-planner updates before pushing the reviewed bundle to `roi-branch`. All eight registered records were audited. Task/progress, feature, stack, system, database and bug records reflect tested local v8/v1.6 and its outstanding gates; architectural decisions remain unchanged because this follow-up changes no architecture. The evaluation/index retains the original v7 replay, its reconstructed-feed disclosure and the 555-test cross-system review. No source changed after that verification. A fresh remote fetch still shows no divergence before staging. Ignored credentials, full captures and private replay outputs are excluded from the commit bundle.

Branch publication is now authorized. Production API/collector release, final visual acceptance, retrieval/freshness policy, additional feed/fallback integration and automatic map publication remain pending. This preparation record does not assert a production deployment or mark those unfinished tasks complete.

## Freshness investigation: open, unchanged

The developer questioned an hourly refresh proposal because flood conditions can change rapidly. That proposal was **not approved or implemented**. Refreshing a successfully fetched article to detect a publisher edit differs from retrying an error.

| Mechanism | Verified current behavior |
| --- | --- |
| Production collection | Cloud Scheduler `lanes-news-discovery-every-3-hours`: enabled, `0 */3 * * *`, Asia/Manila; every three hours |
| Scheduler launch retry | One retry, minimum five-second backoff; retries launching the Cloud Run job, not individual publisher retrieval/extraction |
| Extraction retry | Five attempts; 60/120/240/480-second delays, five-minute leases; due work requires a later collector/worker invocation |
| Successful article, unchanged RSS metadata | Reuse current body; no body-refresh TTL |
| RSS HTTP 304 | No entries and no article fetches; cannot discover body-only edits or retry publisher failures through that response |
| New unreadable article | Rejected before candidate storage; no durable publisher-retrieval retry queue |
| Previously collected failed refresh | Preserve body/history and show error; retry on a later eligible parsed-feed visit |
| News Intelligence | Historical observations remain readable; display does not confirm flooding now |
| Activation prototype | Twelve-hour observation/publication maximum age; scheduled map publication remains disconnected |

The production schedule was read directly on October 3. **The three-hour cycle does not satisfy a near-real-time claim.** Shorter polling also cannot turn delayed/unrevised news into live confirmation. Source observation clocks, corrections/clearance and freshness must remain separate.

Next discussion should set discovery/update latency, publisher request limits, retry bounds and stale-observation behavior together. A short collector cycle with bounded revisits to recent known reports is a plausible direction, but exact intervals and production scheduling are not adopted here. The earlier hourly/24-hour suggestion is not a requirement. GDELT scheduled integration, feed expansion and automatic map placement/publication remain separate unfinished work.
