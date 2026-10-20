# Supervised news NER runtime — local qualification only

> **Last Updated:** October 21, 2026, 12:36 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)


## C3b — controlled full-pipeline entrypoint qualified locally

[C3b measured report/aggregate](../evaluations/rss-ner-rss-integration-20261021/README.md) · [Remaining ordered gates](../task_plan.md#phase-d--correct-monitoring-and-error-classification).

`python -m scripts.run_news_ner_pipeline --bundle <authenticated-path> --bundle-sha256 <independent-pin> --worker-code-sha256 <independent-pin> --limit 50` is a separate internal Linux entrypoint. Require explicit `ENVIRONMENT=test`, a disposable `DATABASE_URL` naming `lanes_p3_verify_*`, independently authenticated assets and existing geography/source references. The service verifies the actual database before writes. It is not a production switch and is not registered with Cloud Scheduler. Never point qualification tooling at shared/development/production storage or overwrite one-attempt claims.

The pipeline preserves raw feed publication wording/timezone proof and native body whitespace, captures corrections immutably, reuses one sequential model, prepares native read groups, evaluates source evidence and applies existing publication gates. Full invocation is 580 seconds with discovery capped at 120 including preparation, downstream reserve 100 and final reserve ten. Extraction retains its 450-second ceiling and also respects remaining reserves; articles/leases remain 125/300 seconds. No next operation starts with insufficient budget. The CLI returns bounded JSON; cancellation exits 130. Legacy entrypoints and default readers/scheduler remain unchanged.

754 distinct tests, retained replay, Linux preflight/eight subprocess probes and the one real controlled attempt pass. Eight mocked-RSS admissions plus two pre-existing short capture controls produce ten exact saved results, 4,483 matching spans/53 reviewed predictions and no duplicate inference. Peak total worker memory is 2,492.09 MiB at one CPU / 3 GiB; main pipeline is 75.772 seconds. Historical publication stays paused; positive publication is qualified with fictional supported evidence separately. Five owned containers are stopped, private database evidence retained and the internal network removed.

Current source differences have a separate 1,085-binding freeze; all 3,639 predecessor receipt files remain unchanged. No post-result application edit or second neural attempt occurred. This passes local Phase C acceptance only. Monitoring (D), frontend (E), 403 investigation (F), production method selection/assets, shared migration, approved cloud resources and actual Cloud Run verification remain gated. The last-inspected one-GiB cloud job is unchanged and unqualified by this three-GiB result.

**Earlier checkpoints below are historical.**

## C3a local native queue worker — qualified boundary

[Measured report/aggregate](../evaluations/rss-ner-native-worker-20261020/README.md) · [Remaining C3b work](../task_plan.md#phase-c--connect-automatic-article-processing).

The separate `scripts.run_news_ner_processing` entrypoint requires Linux, `ENVIRONMENT=test` and an explicitly supplied disposable `DATABASE_URL` naming `lanes_p3_verify_*`. It verifies the actual database name before writes and uses a five-second connection timeout. It accepts `--bundle`, `--bundle-sha256`, `--worker-code-sha256`, `--limit` (1–200) and optional `--article-id`. Supply pins from independently authenticated qualification assets, never from a saved result. The queue library also supports independently supplied publication evidence; existing metadata without raw feed timezone proof remains unknown. No RSS parser change is delivered here.

The worker authenticates before capture, commits one native lease before model loading and uses one lazy sequential model session. The job budget is 450 seconds; an article has 125 seconds including first-use startup, normalization and completion, with five-second completion/cleanup reserves. Startup/request retain 60-second ceilings and share available time. SQL/CPU deadlines are bounded without overlapping the inference supervisor's signal timer. No next claim is taken with fewer than 125 seconds left. Existing 300-second leases and five-attempt/backoff remain unchanged. Failure closes the session and stops; there is no in-session model restart or fallback. Storage failure never claims durable success.

Output contains bounded method/pipeline/count/status data. Exit 1 reports failed/retry/lost-lease/cleanup/configuration outcomes; exit 130 reports interruption. Paused, source-change, no-work and budget-stop outcomes leave unclaimed rows untouched. Native-only results remain completed with reasons. This entrypoint performs no placement, evaluation, publication or HTTP operation and is not added to the scheduler.

The single one-CPU / 3-GiB integration completes ten retained inputs in 70.074 seconds, with 2,339.29-MiB peak below 2,688 MiB, maximum complete operation 62.238 seconds and cleanup 0.515 seconds. All 4,483 spans/graphs/projections and 53 reviewed predictions match; duplicate delivery adds no inference. Expected predictions stay outside the worker. Four owned containers are stopped, the internal network removed and the database snapshot retained privately.

Historical inference/source freezes remain immutable. The successful acceptance image uses its frozen CLI snapshot; final CLI-only error/interrupt reporting has seven separate tests and its own source freeze. All runtime/queue/model/rule code remains identical to the successful run. Do not rerun the one-attempt controller, overwrite its claim or rewrite its freeze to hide that declared wrapper delta.

C3b must qualify original RSS publication provenance, admission/corrections, intended-method readers, nullable-confidence downstream consumers and placement/evaluation/publication with full-job budgets before automatic activation. Current cloud resources and the 60/15/30 cadence are unchanged. No shared migration or deployment is implied.

**Earlier checkpoints below are historical.**

## Current source checkpoint — Phase C2

The [C2 report](../evaluations/rss-ner-native-projection-20261020/README.md) records a separate evidence/projection package and retained-output replay, without starting the runtime. All historical runtime packages and the 1,040-binding freeze remain immutable: 1,032 bindings match; the same eight prior schema/C1 source deltas remain explicit. C2 additions have their own source freeze and receipts. No runtime requalification or performance/cloud-readiness claim follows. Runtime/session-budget and RSS integration remain C3.

**Earlier checkpoints below are historical.**

## Current application-source checkpoint — Phase C1

The [93-check C1 report](../evaluations/rss-ner-method-boundary-20261020/README.md) records queue methods and native-history compatibility without inference. Eight current-source differences from the old 1,040-binding freeze are explicit: the prior approved SQLAlchemy check plus seven C1 consumer/queue files. The remaining 1,032 bindings and all trained/tokenizer/rule/runtime assets match. Four prior receipt packages remain unchanged. The one-line schema-only exception below describes its earlier checkpoint, not today's entire application.

No runtime requalification or automatic connection occurred. Do not rewrite frozen hashes or rerun historical controllers against this changed checkout to conceal the differences. Native projection/source proof, runtime/queue budgets, RSS/current-reader integration and full-job/cloud release verification remain open.

**Earlier checkpoints below are historical.**

**Phase B passes locally at the explicitly approved one CPU / 3 GiB.** All 355 requests, 352 retained prediction comparisons, 53 reviewed-article predictions/saved graph, performance, total-memory headroom and loaded-model shutdown pass independent verification. This does not qualify the earlier one-GiB/two-GiB profiles or establish Cloud Run readiness. The implementation is not enabled in automatic processing or approved for deployment. Preserve every one-attempt claim and receipt; do not rerun a profile without separate authorization. [Passing result](../evaluations/rss-ner-runtime-phase-b-3g-20261020/README.md) · [Two-GiB failure](../evaluations/rss-ner-runtime-phase-b-2g-20261020/README.md) · [Original failure](../evaluations/rss-ner-runtime-phase-b-20261020/README.md) · [Current gates](../task_plan.md#phase-b--qualify-the-production-inference-runtime) · [Approved schema proposal](../plans/rss-ner-processing-mode-schema-proposal.md).

The current qualification tools are `qualify_news_ner_runtime_3g.py`, `news_ner_runtime_probe_3g.py`, `verify_news_ner_subprocess_3g.py` and `test_news_ner_runtime_3g.py`. They preserve the earlier one-GiB/two-GiB tooling and runtime, reuse the identical 355-request workload and keep expected predictions outside worker mounts. The three-GiB profile changes qualification memory/headroom controls only; model/tokenizer/rules and extraction behavior are unchanged. Its exclusive claim is `rss-ner-phase-b-3g-qualification.claim.json`; the earlier claims remain preserved too. Do not remove/bypass any claim. The original one-GiB tool sequence below is historical/reproducibility guidance, not permission to execute again. The minimal schema change is now separately approved and verified locally; next is Phase C controlled integration.

## Authorized later schema delta

The [schema verification report](../evaluations/rss-ner-mode-schema-20261020/README.md) records 66 passing checks with zero inference. The sole authorized current-source difference from the three-GiB frozen 1,040 bindings is the allowed-mode line in `backend/app/models/news.py`; all other 1,039 bindings and all historical snapshots/assets/manifests/receipts remain unchanged. Do not rewrite the frozen source hash or rerun inference to conceal that later approved delta. Automatic worker/API integration and shared/cloud migration remain pending.

## Runtime contract

The sibling `backend/app/services/news_ner_runtime` package is Linux amd64 / Python 3.12 only. No news scheduler, processing service or API imports it. Its child is invoked with an argument list using `python -I -B`, a fixed environment, closed inherited descriptors and no shell. It loads authenticated v19 seed-0 assets once and retains six neural location labels. Depth/time/status/access and grouping remain the frozen rules; nothing is trained or downloaded.

Protocol states are `startup → ready → request → response → ready`, followed by `shutdown`, or terminal failure. One request is active per session; concurrent requests are rejected. Messages are newline-delimited UTF-8 JSON with duplicate-key/nonfinite rejection, 1 MiB request envelopes, 100,000-character body limit and 8 MiB response limit. Text and offsets are unchanged Unicode codepoint coordinates. Request identity, source hash, aware publication metadata, model/tokenizer/code bindings, predictions, ordered proposals, abstentions and graph remain traceable. The supervisor recomputes the pure adapter and rejects inconsistent output.

Timeouts stop and reap the owned child; cancellation does the same. Abrupt parent death triggers the child kernel parent-death signal. The normal runtime returns bounded failure codes and does not include source text, secrets, exception messages, tracebacks or private paths in diagnostics. It does not retry or fall back. Actual loaded-model shutdown/reaping passes after the complete 355-request three-GiB session in 0.33864 s; fictional normal shutdown, earlier guard-stop shutdown and OOM-worker cleanup also pass.

Linux seccomp checks architecture, blocks network syscalls and io_uring, and proves real socket creation denial with IPv4/IPv6/Unix and a direct libc syscall. It is installed before model loading. Missing isolation support fails before readiness. This is credential reduction and network denial, not a general filesystem sandbox or a Cloud Run isolation certification. Child code/assets must be immutable and only the inference bundle should be supplied; expected predictions must never be mounted.

## Frozen resources and lease budget

The passed local profile is one CPU; **3 GiB RAM / total memory-swap**, one child / one request, with combined cgroup peak strictly **below 2,688 MiB**. Observed peak is 1,972.21 MiB. The original one-GiB / below-896-MiB and two-GiB / below-1,792-MiB profiles remain failed historical evidence, not deployment options qualified by this pass. No cloud memory setting changed.

Cold readiness ≤60 s; passage p95 ≤1 s; each retained article ≤30 s; maximum-length fictional input ≤60 s; cleanup ≤5 s. Frozen runtime deadlines imply the 125 s startup/request/cleanup envelope; measured cold + longest request + cleanup is 14.89679 s. The 450 s session budget refuses a request when insufficient time remains for its deadline/cleanup; the full measured session is 28.60577 s. Phase C must connect this to the real 300 s extraction lease, queue claiming and 600 s job timeout; these integrations do not exist yet.

The normal CLI import baseline uses fake storage and disables connections; it is included in the model container's memory. It does not simulate collection, real database pools, placement/evaluation work or overlapping stages. The measured local pass still requires later complete-job/cloud measurement, actual asset delivery/syscall verification and a separate deployment-resource decision.

## Qualification tools and protected execution

The host tools are `backend/scripts/qualify_news_ner_runtime.py` and `backend/scripts/verify_news_ner_subprocess_receipt.py`. The image-only probes are `news_ner_runtime_probe.py` and `news_ner_runtime_faults.py`. They are not scheduled application entry points. No external dependency or normal image/build change is needed. The private authenticated inference bundle must already exist; Git does not transfer it.

Controller operations are deliberately separate:

1. `prepare --output <new direct child of ignored artifacts>` authenticates predecessors/bundle/base image, checks the preserved pure adapter, runs constructed tests, stages an allowlisted build context and writes a frozen workload, limits and source hashes. It performs no inference. A local base tag is checked against the qualified image ID.
2. `build --output <prepared path> --freeze-sha256 <recorded hash>` builds the separate local image, runs real fictional fault checks, the current-code fake-storage import baseline and deliberate OOM in a separate disposable container. No model inference occurs in this operation.
3. `execute` requires the same frozen hash and passed fault receipt. It creates the exclusive `rss-ner-phase-b-qualification.claim.json`, makes one measured attempt and preserves partial results on failure. The current claim already exists; **do not delete, rename, overwrite or bypass it to retry**. A separately authorized follow-up needs a newly designed attempt controller/profile and absent destination.
4. `verify` authenticates receipts and completed outputs without inference. The independent verifier additionally checks saved resource/exit data against the actual stopped container. Both write new receipts exclusively; preserve existing verification files rather than overwriting them.

Constructed checks can be run without application/database fixtures:

```powershell
.\backend\.venv\Scripts\python.exe -B -m pytest --noconftest -p no:cacheprovider backend/tests/test_news_ner_subprocess.py -q
```

Keep model files, texts, expected spans, raw responses, package inventories, private source hashes and Docker receipts inside the ignored artifact directory. Publish aggregate results only. Do not prune unrelated containers/images, change cloud settings, alter model/rules/input bounds or run the old V46 live command as a substitute for this failed gate. [Historical preview guide](ner-backend-preview.md) and [earlier runtime history](ner-runtime-qualification.md) describe different, preserved scopes.
