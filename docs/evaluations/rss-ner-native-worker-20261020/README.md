# Phase C3a — native capture, runtime and durable queue worker

> **Last Updated:** October 20, 2026, 10:23 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Status: C3a passed locally.** This is the approved local runtime-and-queue boundary. It does not activate automatic NER, RSS admission, placement, evaluation, publication or interface work. [Aggregate verification](summary.json) · [Roadmap](../../task_plan.md#phase-c--connect-automatic-article-processing) · [C2 evidence contract](../rss-ner-native-projection-20261020/README.md).

## Implementation

`news_ner_durable.processing.process_native_saved_news` is a separate internal worker. It authenticates assets before capture/claim, checks test configuration and the actual disposable database identity, honors processing/source selection, then uses one lazily started model subprocess sequentially. Existing scheduled/legacy entrypoints are unchanged. The thin `scripts.run_news_ner_processing` entrypoint rejects other environments/database names and unsupported platforms before writes. No public route, frontend type, dependency or migration is added.

Native enqueue now uses C2's complete capture schema/fingerprint. It accepts independently supplied publication evidence; automatic capture of existing articles defaults to unknown historical provenance. It never reconstructs raw publisher timezone evidence from normalized metadata. Legacy serialization remains unchanged. The native capture scan streams current article bodies and compares native versions for the intended pipeline, so a changed body or publication clock can produce its own immutable capture. Existing known provenance is retained when the remaining input is unchanged. Fetch/seen clocks do not create inference work. Queue-capture code participates in the trusted manifest; current source identities differ explicitly from C2's historical snapshot.

Native and legacy captures of the same body have different fingerprints and therefore different immutable versions. C1 fixture assertions now reflect that distinction; retained historical fixtures/receipts are unchanged. The SQLite identity test restores its original aware fixture clock because SQLite strips timezone information; actual persistence/timezone behavior is checked in PostGIS. Historical inspection-only native shapes are not silently upgraded into operational inputs.

The worker claims/commits before inference, holds no transaction during model loading or normalization, builds the complete C2 result, then finishes only its live owned lease. Native-only/no-observation results remain honest completed extractions. No geometry enrichment, audit, publication or rules fallback runs. Saved history remains readable through C1 serialization.

## Budgets and failures

The invocation has a 450-second budget; each article has 125 seconds starting before its claim. Work gets 115 seconds, reserving five seconds each for completion and cleanup. Startup/request retain their existing 60-second maxima and share remaining work time; cleanup remains at most five seconds. The unchanged extraction lease is 300 seconds. Fewer than 125 remaining seconds stops further claims without changing unclaimed rows.

Synchronous authentication/capture/normalization/storage work uses scoped Linux timers with restoration and nested-owner refusal. Inference retains its own supervisor timer; these timers are never armed simultaneously. PostgreSQL statement/lock waits and CLI connection establishment are bounded separately. Time budgets include normalization and JSONB completion rather than treating neural inference as the whole operation.

Runtime timeout/crash/cancellation records one bounded retryable attempt under the existing five-attempt/backoff policy, closes the session and stops. Invalid input, assets, configuration and result bindings are distinct. There is no in-session model restart or inference retry. Storage failure does not report durable success; existing lease recovery remains authoritative. Shutdown failure is visible without deleting a completed result. Source changes/processing pause stop before another claim.

## Verification preparation

**251 checks pass without skips:** 224 software checks and 27 owned PostgreSQL checks. The 244 core checks include C1/C2/source-validation regressions and 19 C3a scenarios: local-target guards, native capture/history/duplicates/changed input, independently supplied publication evidence, lazy startup, source-selection changes, operation/startup deadlines, cancellation, bounded failure/retry and shutdown behavior. Seven additional thin-CLI checks cover rejection before engine creation, malformed configuration, explicit asset errors, interruption and bounded fatal diagnostics. Inference is fictional in these tests.

The Linux acceptance image is built from the authenticated qualified image through a task-owned local tag verified against its immutable image ID. It overlays an explicit 120-file source allowlist and the required geographic/source references; normal build files are unchanged. Expected saved predictions remain outside worker mounts. A real Linux timer/restore/nested-timer check and a fictional-model queue-to-JSONB roundtrip pass before inference. Eight real fictional subprocess probes cover timeout, crash, malformed/oversized output, cancellation, concurrency, shutdown and parent-death containment.

The first preparation preserved a SQLite fixture expectation failure and a Docker build failure: Docker parsed a bare local image ID as a registry name. The next preparation uses the verified task-owned local tag. The initial internal-only database network did not expose a host port; its owned database was temporarily connected to the bridge for host tests, then detached before real inference. These were preparation failures; no neural attempt was consumed. Credentials, source bodies, predictions and raw receipts remain private.

## Controlled integration gate

One frozen local attempt uses one CPU / 3 GiB, equal swap cap and below-2,688-MiB total-container headroom. Its workload is the six existing complete articles, reviewed article and three existing fictional stress cases. It uses an internal network connecting only the worker and disposable PostGIS, read-only code/assets, and the unchanged model child's syscall network denial and credential-filtered environment.

The single attempt passes all ten native captures/claims/runtime outputs/durable results/fresh saved-history reads. **All 4,483 retained neural spans match**, including all **53 reviewed-article predictions**. Complete saved results match independent pure graph/projection recomputation from the authenticated saved predictions. The duplicate invocation captures/processes nothing and makes **zero additional neural requests**. Twenty immutable versions preserve both legacy fixture history and native captures. No publication source/case/decision, flood report or zone is created.

| Measured gate | Result | Limit |
|---|---:|---:|
| Actual worker-container memory peak | 2,339.29 MiB | Below 2,688 MiB |
| Native worker invocation | 70.074 s | 450 s |
| Longest complete article operation | 62.238 s | 125 s |
| Cold model startup | 2.552 s | 60 s |
| Longest inference request, including host validation | 16.425 s | 60 s |
| Model shutdown/reaping | 0.515 s | 5 s |
| Model starts / neural requests / model reaps | 1 / 10 / 1 | One sequential session |

Memory covers the actual Python supervisor, imported worker code, model, native normalization and SQL/JSONB persistence in the worker container; PostGIS is a separate owned container. Measurements include saved-history/duplicate verification checks against the same headroom gate. These are local integration measurements, not accuracy scores, new runtime-profile qualification, RSS processing or Cloud Run readiness.

## Independent preservation and final CLI review

Independent verification made **no additional inference requests**, authenticated 120 acceptance source bindings and verified all **six predecessor receipt packages / 1,511 files**. The old 1,040-binding runtime freeze still has exactly the same eight prior schema/C1 file paths differing from the current checkout, with the queue file's approved C3a delta recorded separately; 1,032 bindings match. Model/tokenizer/inference-worker/location/context rules and historical source snapshots remain unchanged.

Final error-path review found that the thin CLI could emit a traceback on interruption. Only that wrapper's error reporting changed afterward: explicit configuration/asset codes, bounded fatal output and exit 130 for cancellation. Its normal processing path and all qualified runtime/queue code remain unchanged. Seven isolated checks and a separate CLI source freeze verify this correction. **119 of 120 acceptance source bindings still match current files; the one CLI delta is explicitly recorded, not concealed by rewriting the inference freeze.** The successful image/source snapshot and its independent verification remain historical evidence. No second model run occurred.

Four owned containers are stopped with PID zero, the model was reaped and the owned internal network was removed. A private database snapshot preserves the actual JSONB/history. Raw receipts, inputs, predictions, credentials, model files and failed preparation logs stay ignored under the private `rss-ner-phase-c3a-20261020-v1` and `v2` packages. Only aggregates are published.

## Remaining work

Overall Phase C stays open: RSS admission/corrections, original feed-provenance capture, intended-method/native readers and nullable-confidence downstream consumers, placement/evaluation/publication compatibility and controlled end-to-end acceptance. Historical fixtures cannot become current alerts. The existing 60/15/30 scheduling policy and live cloud configuration are unchanged; this local result is not Cloud Run readiness or deployment approval.
