# Scheduled historical news workflow investigation

> **Last Updated:** October 12, 2026, 3:57 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Subsequent approved audit implementation:** [Batch/quota verification](news-batch-audit-20261012/README.md) records the new eight-claim contract, durable quota handling, safe diagnostics, fresh scheduled-worker databases `lanes_workflow_20261012i/j` and separate preview. 492 offline, 226 native and 14 browser checks pass. Real quota 52/50/0 still blocks successful operational plotting. The earlier snapshots/results below remain historical; their discarded provider-status defect is repaired for new evaluations, and prior immutable results are not rewritten.

**Collection/extraction repairs verified locally; successful operational-zone refresh remains unverified.** The developer approved fixing article refresh and heading-context/locality extraction, then rerunning the same historical reports. This supersedes the original implementation-preservation restriction for those repairs only. Manual flood-row insertion, fabricated audit approvals, source retiming and gate bypasses remain excluded. Actual provider errors prevent successful plotting verification.

## Approved repairs and final automatic replay

- `news_discovery_service.py` now refreshes existing bodies after thirty minutes with at most twenty periodic captures per collection cycle. CRUD selects the oldest captures across reviewed publishers using existing timestamps and feed provenance. Parsed, empty and HTTP-304 feeds can revisit previously captured, still-recent article URLs. Registered source/host, age and future-publication checks remain enforced. Failed retrieval retains previous evidence and exposes its error; identical bodies do not create new immutable versions.
- `taglish_extraction_service.py` recognizes city headings with an observation clock and depth-group headings, preserving each road's own inline facts. Numbered address rows retain the existing address-candidate behavior when depth is supplied by a heading, and cannot end the surrounding list prematurely. City switches and narrative boundaries end local depth/time scope; list clocks cannot leak through the separate shared-narrative-clock pass. Evidence remains contiguous original text with original offsets. Forecast, negation, simulation, clearance and range behavior remain gated.
- Processing revision is `rules-spatial-preview-v17`, allowing normal queues to retain old results and evaluate the revised extractor. No packages, SQLAlchemy definitions, migrations, endpoints, frontend labels or cloud settings changed.

**Verification:** 271 focused extraction/discovery/queue/evaluation/publication/ingestion checks pass, with three existing warnings. Current migrations apply cleanly to fresh isolated PostGIS databases through `d7e4b9a21c60`. Source HTML and indexed-text hashes remain unchanged. All replay writes still use only `run_scheduled_news_tick`; no separate processing stage, synthetic audit response or flood insert is used by the harness.

| Post-repair replay | Database | Final evidence |
|---|---|---|
| September 24 checkpoint | `lanes_workflow_20261012e` | Five ticks; three articles; one version/run; five road locations; original twelve-hour admission rejections; zero zones/events |
| September 9 captured HTML | `lanes_workflow_20261012f` | Seven ticks; three articles/versions/runs; 33 locations; 46 completed evaluations; rate-limited audits age into expiry; zero zones/events |
| Intermediate indexed-text run | `lanes_workflow_20261012g` | Exposed the numbered-address list-boundary defect and captured the later GMA revision; retained separately rather than overwritten |
| Final indexed-text continuous replay | `lanes_workflow_20261012h` | 26 half-hour ticks; three articles, four versions/runs; 77 evaluations (73 completed, four failed); 33 final locations; zero zones/events/history locations |

At the final replay's first tick, the reader exposes 27 locations: one Manila road plus all 26 Quezon City sites. Every QC site retains its supported city, depth and 08:55 clock; the five incorrect parent-city mappings from the baseline are absent. GMA's changed 15:09 body is recaptured at 15:26 despite unchanged feed metadata, producing a second immutable GMA version. Further identical captures preserve four total article versions/runs. The actual saved pair is N.S. Amoranto/Banawe, Santo Domingo, Quezon City: 19 inches at 08:55 from early GMA and 10 inches at 16:30 from Philstar. The inconsistent source half-knee description is not rewritten.

Actual auditing continues to return HTTP 429; four final evaluations terminate as `auditor_http_error`, whose HTTP status is not persisted by the existing diagnostic record. Other wet evaluations age into normal expiry. No verified alert/first operational zone exists in the final replay, so no footprint activation or Flood History event can follow. The changed-depth zone refresh-versus-duplicate branch remains unverified. The repaired discovery/extraction behavior is demonstrated; overall map activation is not claimed successful. Historical RSS, missing original early HTML, weather dispatch and browser acceptance limitations below still apply.

Private result files are `september24-after-fix-scheduled-workflow-20261012.json`, `september9-after-fix-scheduled-workflow-20261012.json`, the intermediate indexed output and `september9-indexed-continuous-after-fix-final-scheduled-workflow-20261012.json` under ignored `data/news-replay/`. Existing local display and cloud databases remain untouched. No push or deployment was performed.

### Follow-up: current provider quota and diagnostic loss

At October 12, 02:34 PHT, a read-only OpenRouter key-information request returns HTTP 200 with `is_free_tier=true` and `free_model_daily_requests={used:52, limit:50, remaining:0}`. These explicit request counters confirm that the current daily free-model allowance is exhausted; the earlier monetary/deprecated fields did not establish that fact. The existing `check_news_auditor.py --probe`, with the configured `openrouter/free` model and unchanged twenty-second timeout, independently returns HTTP 429 / `auditor_rate_limited`. It performs no database access or public-data writes. These checks establish the current barrier, not the HTTP status of every earlier replay failure. [Official quota/error documentation](https://openrouter.ai/docs/api_reference/limits) describes the daily request counters and provider/platform sources of 429 responses.

Code tracing confirms a separate diagnostic limitation: `NewsClaimAuditor.audit` returns `provider_http_status`, but `evaluate_news_claims` retains only `reason_code`/`retryable` for unavailable or invalid results. `finish_owned_evaluation` saves `result=None` for failed/retry evaluations; the existing model has no separate provider-status column. Consequently the four terminal `auditor_http_error` rows cannot establish whether their original responses were 400, 401, 404 or another status. No provider body/status logging, schema, audit scheduling or model configuration was changed under the narrower collection/extraction repair approval. Successful first-zone and changed-depth verification still needs a functioning real auditor.

## Initial investigation: execution boundaries

The unchanged `run_scheduled_news_tick` performs maintenance, discovery, durable extraction, evaluation, publication and footprint activation. Its existing publication and freshness checks remain enabled. Two registered source selections are used per scenario, with all their registered feed URLs: GMA/Tribune for September 24 and GMA/Philstar for September 9. Current registry approvals are retained. This is sample-source integration coverage, not proof of historical coverage of every configured publisher.

Only external publisher HTTP responses and the simulation clock are supplied by an ignored harness. Actual independent auditing uses the configured `openrouter/free` provider, the normal 20-second timeout and normal durable retries. No auditor response is substituted. Feed titles, URLs and publication dates are reconstructed from source metadata without invented descriptions; authentic historical RSS membership is unverified. Archive CDX requests for Tribune RSS and GMA Metro RSS over September 23Ã¢â‚¬â€œ26 returned empty lists. Search absence does not prove that no other report existed.

Existing Alembic migrations were applied to four new, empty loopback databases: `lanes_workflow_20261012a` for September 24, `lanes_workflow_20261012b` for captured September 9 HTML, `lanes_workflow_20261012c` for indexed-text checkpoints and `lanes_workflow_20261012d` for the continuous indexed-text replay. No models or migration definitions changed. Existing local display database `lanes_plotting_20261011`, its server/frontend, and cloud storage are preserved. All flood/event/case/evaluation rows are created solely by the normal worker. Observer SQL uses read-only transactions. A first September 24 worker completed before the observer failed on incorrect diagnostic column names; the observer was repaired and preflighted, and the worker continued against its durable state without deleting, backfilling or resetting records.

Private infrastructure/results live under ignored `data/news-replay/`: `setup-scheduled-workflow-20261012.py`, `run-scheduled-workflow-20261012.py` and `*-scheduled-workflow-20261012.json`. Application source and product labels are unchanged. The weather-controller/cloud dispatch path is not exercised; without a historical weather snapshot, the worker uses its normal unavailable-weather collection interval. This checkpoint does not establish full deployment acceptance or browser rendering acceptance.

## September 24Ã¢â‚¬â€œ25: completed worker scenario

| Historical input | Earliest supplied availability | Observed result |
|---|---|---|
| GMA afternoon [rain advisory](https://www.gmanetwork.com/news/weather/content/1003547/thunderstorm-advisory-heavy-to-intense-rains-over-parts-of-metro-manila-6-areas-thursday-2-24-p-m/story/) | September 24, 15:41 PHT | Captured as local news, not an observed-flood extraction candidate |
| GMA [16:12 advisory](https://www.gmanetwork.com/news/weather/content/1003561/thunderstorm-advisory-metro-manila-laguna-tarlac-9-areas-thursday-4-12-p-m/story/) | September 24, 16:58 PHT | Captured as local news, not an observed-flood extraction candidate |
| Tribune [minor flooding report](https://tribune.net.ph/2026/09/24/minor-flooding-hits-some-metro-areas) | September 25, 04:41 PHT | Normal extraction; five visible road locations; no active zones or Flood History events |

Five observed ticks finish at September 24 15:42, 16:59, 17:29 and September 25 04:42, 05:12. The final database contains three articles, one completed flood extraction, eleven evaluations/cases and eleven unpublished decisions. Six decisions reject context-only claims; the five road decisions reject `observation_outside_admission_window`. Public-map response generation returns no active zones; event/history-location tables are empty. The second post-publication tick creates no duplicate extraction/evaluation/zone.

The Tribune road observation is September 24 16:34, over twelve hours before the first realistic publication checkpoint. Clearances are earlier still. `preliminary_reason` checks the twelve-hour observation admission window before the active-evidence expiry check. This is evidence of normal delayed-report rejection, not a collector failure or proof of successful automatic plotting. The original road depths, conditions, source dates and captured HTML remain unchanged. Disabling maintenance expiry does not, by itself, bypass initial observation admission.

## September 9: captured HTML checkpoint scenario completed

Primary captures: GMA [flooded-road list](https://www.gmanetwork.com/news/topstories/metro/1001693/list-flooded-roads-in-metro-manila-wednesday-sept-9-2026/story/), Philstar [16:30 road observations](https://www.philstar.com/nation/2026/09/09/2555106/list-flooded-metro-manila-areas-september-9/amp/), and GMA [evening coverage](https://www.gmanetwork.com/news/weather/content/1001808/several-metro-manila-areas-flood-due-to-habagat/story/).

The captured GMA list is its 15:09 updated body, not its original 09:19 body. It is first exposed at 15:10. Exposing that updated body at 09:19 would introduce future evidence. Current canonical and AMP publisher fetches both confirm the 15:09 update and lack the earlier Quezon City list.

Seven checkpoint ticks finish at 15:10, 15:40, 17:04, 17:34, 18:04, 21:25 and 21:55. Three articles/versions and three completed extraction runs produce **33 visible locations**, 46 evaluations (38 completed, eight failed), zero zones and zero Flood Events/history locations. Repeated unchanged publisher content produces no duplicate version or extraction. These are checkpoint runs, not a continuous replay of every due collection/controller tick between article arrivals.

The first GMA cycle publishes a verified Marcos Highway text alert, but the estimated-footprint worker records `local_place_not_grounded`; it cannot activate an operational zone. Publication expires that alert on the later 17:04 tick. The Philstar report's 16:30 observations are captured/extracted at 17:04; auditing records 19 timeouts in that cycle plus invalid/evidence-binding responses. Ordinary 17:34 and 18:04 retries receive HTTP 429 (`auditor_rate_limited`). On the later 21:25 tick, twenty evaluations finish as `observation_evidence_expired`, rather than source verification. The evening GMA article has three road observations rejected for `missing_supported_observation_time`. Final failed audits include four `auditor_response_invalid`, one `audit_place_evidence_missing`, one `audit_fact_place_binding_missing`, and two `audit_parent_locality_evidence_missing`.

The worker reports `requires_attention` during failed/retry cycles, but the final cycle reports `completed` even though eight terminal failed evaluations remain in storage and no zones were activated. This is a completed current-cycle outcome, not proof that all captured reports succeeded; backlog/history diagnostics matter. The final source counts and map/history absence are verified through read-only database observation and the existing zone-response generator, not rendered browser checks.

A read-only OpenRouter key-information request confirms the configured account is on the free tier. Its deprecated rate-limit field and monetary `usage_daily=0` do **not** establish remaining request quota or the reset time. Actual auditor responses prove HTTP 429; daily-quota exhaustion is not independently confirmed. [Official provider limits](https://openrouter.ai/docs/api-reference/limits) describe free-model throttling. No provider/model/timeout change was made to force the test through.

## Earlier GMA version and depth comparison: checkpoint run completed

The primary GMA page returned through the search index includes a 09:55 update, an 08:55 Quezon City observation and a 19-inch depth at N.S. Amoranto/Banawe in Barangay Sto. Domingo. The later Philstar report names that road/barangay with 10 inches at its 16:30 update. The source's inconsistent half-knee label is retained; no corrected measurement is invented.

The earlier GMA body is saved privately as indexed rendered text with provenance. Original publisher HTML for 09:55 has not been recovered. The separate `september9-indexed` scenario exposed this unchanged text through reconstructed HTML, then offered the original captured 15:09 HTML and later Philstar article. This tests semantic processing and durable article-version handling, but cannot prove fidelity of the missing original markup or RSS membership. The ten-tick indexed-text checkpoint scenario completed in `lanes_workflow_20261012c`: three articles/versions, three completed extraction runs, 65 completed evaluations, 31 final displayed locations and no zones/events. Its final evaluations include 24 `unsupported_locality`, 28 `observation_evidence_expired`, five `not_observed_flood_evidence`, five `unsupported_claim_context` and three missing supported observation times.

**Conditional article-refresh failure:** The publisher HTTP fixture offers the actual captured 15:09 GMA HTML from 15:10 onward, but the collector requests that article URL only once, at 09:56. It preserves only one GMA version and never extracts the new body. `news_discovery_service.py` reuses the saved body indefinitely when title/excerpt fingerprint, publication date and source identity match. This reproduces a stale-body condition under unchanged feed metadata. Authentic historical RSS is unavailable, so it does not establish that GMA's real September 9 feed metadata stayed unchanged.

**Indexed road-list context failure:** The earlier rendered body supplies city/time/depth in headings above road bullets. Extracted N.S. Amoranto road claims retain individual road/barangay names, but lose supported city, observation time and depth; they cannot enter eligible evaluation or appear as the expected road results. This is a semantic failure for the preserved indexed-text sample; the missing original HTML limits claims about the publisher's original markup. Philstar's later inline measurements resolve 26 inches in Sienna versus 10 inches in Santo Domingo separately. No cross-barangay measurements were merged manually.

**Continuous worker replay completed:** A new empty `lanes_workflow_20261012d` completed all 26 half-hour ticks from 09:56 through 22:26, using the existing unavailable-weather interval. It retains the same indexed-text/markup and archive caveats. All adjacent worker ticks are 1,800 seconds apart. The final database has three articles, three versions, three completed extraction runs, 65 completed evaluations, 31 visible locations and zero zones/events/history locations. GMA was still fetched only at 09:56, confirming the conditional stale-body result across every intervening worker cycle. Publisher HTML hashes remain unchanged. Controller/cloud dispatch and successful operational-zone refresh remain separate unproven scopes. No index snapshot has been inserted into a news table manually.

## Initial remaining verification (before repair authorization)

**Additional locality evidence:** Read-only inspection of the continuous replay's immutable first extraction finds five street mentions resolved to unsupported parent cities despite the primary indexed source's Quezon City heading. The later Philstar extraction resolves the corresponding entries under Quezon City. These samples were not corrected or resubmitted; they reinforce the heading-context failure and identify a street-versus-city ambiguity to cover in a future fix.

| Road mention in the early Quezon City list | Saved early canonical city | Later Philstar canonical city |
|---|---|---|
| N.S. Amoranto corner Ubay Street | Ubay | Quezon City |
| N.S. Amoranto corner Biak na Bato Street | Bato | Quezon City |
| Calamba corner Don Jose | City of Calamba | Quezon City |
| Samat corner Don Jose | Bugallon | Quezon City |
| Sto. Domingo corner Calamba | San Manuel | Quezon City |

The preserved early sample and reconstructed-markup limitations still apply. Rechecking available sources did not recover a new eligible same-place sequence. Radyo Pilipinas has a primary September 9 measured-road report, but it is outside the current reviewed source registry; no source approval or registration was invented to admit it. The staff Sources endpoints list/probe configured feeds, rather than providing an existing registration action. At that checkpoint repair permission was pending. The developer subsequently approved those repairs; final verification is recorded at the top of this document.

- Captured September 9 checkpoint and continuous indexed-text worker runs finished; historical RSS, original early HTML, weather-controller dispatch and rendered browser acceptance remain outside verified coverage.
- Continuous half-hour worker replay finished; successful operational-zone refresh remains unverified because capture/context/auditing/placement barriers prevent an eligible first zone.
- Observe whether later same-place reports update a zone, create another case/event, expire prior support, or fail earlier gates. Code inspection alone is insufficient: publication refresh targets currently require matching article identity as well as incident identity.
- Source-version/idempotency counts and captured HTML hashes were checked against run outputs. Explain missing stages as failures or unreached stages, not successes.
- Preserve these archive/dispatch/browser limitations in the completion audit. At the initial checkpoint implementation fixes were not authorized. The later approval covers the two repairs recorded above; shared-cloud historical activation remains outside scope.

## Initial completion audit (before approved repairs)

| Requirement | Evidence | Status |
|---|---|---|
| Investigate additional September 24 sources | Two primary GMA advisory captures, source searches and collector rows | Verified for available sample; no second same-road measured update verified |
| Let collection/extraction/auditing/publication/footprint services write their own records | Existing scheduled-worker entry point; loopback safeguards; no harness flood inserts or stage calls | Verified |
| Preserve original evidence, times and depths | Original HTML hashes unchanged; article/version/extraction snapshots | Verified for captures; early GMA body is indexed text with reconstructed markup |
| Process September 9 later reports | Three captured articles, 33 locations, durable failures/retries and final state | Verified |
| Observe article edits and different-time/depth reports | Indexed primary early report plus later captured HTML/Philstar; continuous 26-tick replay | Conditional stale-body failure and heading-context failure verified; successful changed-depth zone transition not reached |
| Inspect map/database/history outcome | Existing public-zone response generator and read-only tables after every tick | Verified zero zones/events; news evidence retained |
| Distinguish updating an existing operational zone from duplicate zone creation | No eligible operational zone in these unmodified runs | Unverified; zero created zones cannot prove the behavior once a first zone exists |
| Full historical discoverability/controller/browser acceptance | Missing authentic historical RSS/early publisher HTML/weather dispatch; no new browser session for these databases | Unverified |

The original investigation was blocked pending repair authorization after three consecutive goal turns. Authorization has now arrived, the two repairs are implemented and final replays are terminal. The original goal is still **not complete**: successful operational-zone update verification needs a first eligible audited zone. Provider reliability remains the current barrier; this repair scope does not authorize changing providers or bypassing evidence checks. Local source fixes and runtime evidence are recorded above. No cloud data movement occurred.
