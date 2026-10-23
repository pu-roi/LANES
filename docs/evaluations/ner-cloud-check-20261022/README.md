# NER-first deployment check — full Cloud Run qualification passed

**Status: the trained NER passed one explicitly approved full frozen workload on the separate unscheduled Cloud Run job, under the approved `cloud-run-v1` resource profile. Automatic processing, application data and history seeding remain unchanged.** Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

The user selected a separate unscheduled `lanes-ner-check` job before continuing Part 2A. Local files/checks, cloud upload/account/job creation and one execution/documentation update received separate approvals. The ordinary backend pipeline, frontend, Valhalla, Cloud SQL and schedules were not changed. The unchanged original model/runtime were deployed only inside the separate unscheduled test image.

## Cloud acceptance — full frozen workload passed

After explicit approval, uploaded the verified profile image, updated **only** the existing unscheduled `lanes-ner-check` job, cleared `--diagnostic-only` arguments, verified actual configuration, and dispatched exactly one full execution: **`lanes-ner-check-nbpmz`**. It ran October 22, 2026, **12:03:18.678–12:04:01.937 PM Philippine time**, one task/attempt zero, task exit zero and no automatic retries. Four cloud executions now exist: the initial strict preflight failure, two approved diagnostic-only runs, and this single actual model session. Earlier failures/claims remain preserved.

The independent verifier matches **355 full proposal/graph/provenance hashes**, **352 separately retained prediction records**, and the reviewed article's **53 mentions**, with exact source/run/package/model bindings. Every one of **358 resource snapshots** passes the approved profile. Registry index bytes and Linux amd64 manifest, actual saved job and execution settings, task status and logs are independently verified. A success exit alone did not establish acceptance. All 418 predecessor files and original model/runtime/isolation authenticate unchanged. The image contains exact frozen input/model/application files and no expected answers or application settings.

| Actual cloud measurement | Result | Requirement |
|---|---:|---:|
| Cold model start | 4.9637 s | ≤60 s |
| Passage p95 | 0.04006 s | ≤1 s |
| Longest request | 15.4551 s | All article ≤30 s / stress ≤60 s checks pass |
| Loaded session | 30.7342 s | <450 s |
| Cleanup | 0.1835 s, child exit 0 | ≤5 s, clean exit |
| Combined cgroup peak | 2,067.3 MiB | <2,688 MiB, actual hard memory limit 3 GiB |
| CPU configuration / measurement | Configured 1; measured quota 1.043 throughout | Independent actual setting check plus finite positive recorded quota |
| Swap | Host-no-swap basis in all 358 snapshots | Approved host-zero-capacity/devices evidence, not an enforced-zero-limit claim |

The unchanged model child passes seccomp and IPv4/IPv6/Unix/raw-socket denial and parent-death protection. Full results retain the original known-input oracle and model identity; this is a deployment regression/containment check, not a new accuracy benchmark. No source collection, retraining, historical processing, seeding, publication or activation occurred.

The dedicated service account has no project roles, user-managed keys or application credentials, and the job has no volumes/Cloud SQL binding or matching regional scheduler. Actual settings remain one CPU/three GiB, one task/parallelism one, timeout 600 seconds, max retries zero. The ordinary rules-only news worker image/arguments remain unchanged; no application records, API/Valhalla deployment or schedule changed. Temporary cloud resources remain retained, unscheduled, and require separate cleanup approval. **Automatic NER processing is not enabled by this test.** Production worker integration requires a separate concrete review/approval before Part 2A seeding resumes.

Private immutable evidence: `data/ner-cloud-check-20261022-cloud-full-v1`, with claim `data/ner-cloud-check-20261022-cloud-full-v1.claim.json`. It contains the exact user authorization, upload/registry authentication, before/after job configuration, execution/task metadata, full structured logs, all result events, independent prediction/resource verifier output, saved control-plane verifier output, role/key/schedule checks and final `cloud-acceptance.json` / `final-receipt-manifest.json`. Image/package/freeze remain the local profile identities in the next section; actual platform resolution is included in the structured summary. No commit/push occurred.

## Approved cloud resource profile — verified locally

The user explicitly approved the qualification-criteria change and local edits in `backend/scripts/news_ner_cloud_probe.py`, `qualify_news_ner_cloud.py`, `backend/tests/test_news_ner_cloud.py` and the same seven documentation records. No NER inference, cloud operation or database access was included or performed in this revision. The launcher, Dockerfile, inference runtime and model remain unchanged.

| Contract | `local-strict-v1` | Approved `cloud-run-v1` |
|---|---|---|
| Selection | Default local preparation | Explicit prepare flag, frozen in image check/identity; cannot switch after preparation |
| CPU | Exact measured quota/period equals one | Independently verify actual saved job and execution configured 1 CPU; every measured quota/period is finite, positive and recorded unchanged |
| Memory | Exact 3 GiB limit, peak below 2,688 MiB | Same |
| Swap | Enforced zero container allowance | Either enforced zero allowance, or readable zero host capacity/free and zero devices, explicitly labeled as host evidence |
| Timing, output and isolation | Original qualified requirements | Same deadlines, 355 graph/provenance hashes, 352 retained predictions, reviewed 53 mentions and unchanged seccomp/parent-death isolation |

The cloud swap/CPU criteria are an explicitly approved new profile; the earlier strict cloud attempts remain failed and their evidence is never relabeled. Host absence does not claim an enforced per-container zero limit. The probe checks resource evidence at preflight, loaded readiness, each request and after loaded-model cleanup. The independent result verifier validates all **358 snapshots**, monotonic peaks, record/peak binding and labels; its result expressly requires a separate control-plane verifier. That verifier rejects wrong job/project/region, image, service account, configured CPU/memory, retries/tasks/timeout, diagnostic-only args, overridden command, credentials, volumes/Cloud SQL or incomplete/retried execution. Registry index/platform authentication and actual permissions/schedules are separate required checks.

**150 tests pass**, zero skips/failures/errors across the affected four suites. Twelve actual Linux container cases pass without a model: 0.806 quota diagnostic/preflight, 1.043 quota diagnostic/preflight, nonzero swap-capacity diagnostic and rejected preflight, active-device rejection, malformed-swap rejection, enforced-zero-swap diagnostic/preflight with host swap present, unbounded-CPU rejection and wrong-memory rejection. The actual image also passes ordinary preflight, diagnostic schema v3, supervision and unchanged isolation without Docker external init. A non-neural fake-session test proves a mid-workload swap check stops further requests and closes the session. The initial stale diagnostic-plan fixture failed once and was corrected; its receipt remains retained. Earlier test counts are overlapping historical checkpoints, not additive totals.

| Final local identity | Value |
|---|---|
| Image / OCI index | `sha256:e9fb8f878b3e84283cfd46da4e154db24357bd107bf15f8753f4b96510eb8e42` |
| Package | `ca02f710217295ca019c7162470fd4471bb20bcf6ad61e0f335478f2b690f79d` |
| Freeze | `6e89a749a81439187fa1dd60a9058843bb3e9af03af9be7e288ab11cd7f6a49b` |
| Proposed registry tag, not uploaded | `asia-east1-docker.pkg.dev/lanes-project-508809/lanes/lanes-ner-check:cloud-profile-ca02f710217295ca019c` |
| Private package | `data/ner-cloud-check-20261022-cloud-profile-v1` |

The application/input/assets exactly match the frozen context and contain no application settings or expected answers. All 418 predecessor files authenticate unchanged. Fourteen stopped owned containers were inspected and removed; image, source context, oracles, receipts and historical claims remain retained. Authorization, pre-edit source snapshots and all test attempts are under `data/ner-cloud-check-20261022-cloud-profile-approval`. No new dependencies, migrations, UI, ordinary deployment pipeline or scheduled-processing changes.

At the local preparation checkpoint, `cloud-qualification-plan` printed the concrete proposal only, with inference authorization false; its later full cloud approval and acceptance are recorded above. It requires matching profile/preflight/supervision receipts. Full cloud testing requires separate approval: upload this exact image, update only the existing unscheduled job, **clear `--diagnostic-only` args**, verify actual digest/configuration and execute once with zero retries. Keep 1 CPU/3 GiB, one task, 600 seconds, no application credentials/roles. Verify original neural results, every resource snapshot, actual configuration, clean shutdown and retained task/log evidence before declaring the cloud test passed. No new local neural attempt or full cloud execution is authorized by profile preparation.

## Corrected cloud diagnostic — supervision passes, resource review open

The user separately approved upload/update/configuration verification and one diagnostic execution of the corrected image. **`lanes-ner-check-b4b8m`** completed on October 22 at **11:48:10 AM Philippine time**, one task/attempt zero, exit zero, no retries. The actual image resolves the approved OCI index `sha256:07feb6398089a2da13ec8cf0584fd15e83a43f83d7c720423664f8bcc16e871c` to its authenticated Linux amd64 platform manifest. The log package identity matches the frozen local correction. The job retains configured 1 CPU/3 GiB, one task, 600 seconds, zero retries, the dedicated role-free identity and no application credentials or Cloud SQL binding.

| Actual cloud evidence | Verified result |
|---|---|
| Supervision | Probe PID 11 beneath launcher PID 1; isolation child PID 12 beneath probe PID 11. |
| Unchanged isolation | Seccomp enabled, IPv4/IPv6/Unix socket creation and raw socket syscall denied, parent-death guard passed. |
| Memory | Exact hard limit 3,221,225,472 bytes; diagnostic peak 172,666,880 bytes. This is not loaded-model memory. |
| CPU | Configured 1 CPU; measured quota 104,300 per 100,000 microseconds (1.043). Earlier diagnostic measured 0.806 with the same configured CPU. The cause of this variation is not established. |
| Swap | No active host swap devices; host total/free both zero. Combined cgroup limit is `9223372036854771712`, preserved exactly as a decimal string; no enforced zero-swap limit is established. |
| Qualification | Strict CPU check returns `cpu_limit_required`; `qualification_passed=false`, `inference_started=false`. |

Independent diagnostic verification accepts the actual resource facts, failed strict verdict, successful unchanged isolation and index/platform/execution binding. Exactly three cloud executions exist, two diagnostic-only. Ordinary rules-only news job, regional schedules, application data and service-account permissions remain unchanged. Raw metadata/logs, task status, authenticated manifest, verification and immutable claim are under `data/ner-cloud-check-20261022-cloud-startup-v2` and `data/ner-cloud-check-20261022-cloud-startup-v2.claim.json`.

**At this diagnostic checkpoint, the proposed next step was not yet authorized:** retain the strict local profile and add an explicitly versioned Cloud Run qualification profile. The later local approval/verification is recorded above. Independently verify actual job/execution configuration remains 1 CPU/3 GiB; record the finite positive measured CPU quota without rewriting it to one; retain hard memory/headroom and every performance deadline. For swap, distinguish an enforced zero allowance from host zero-capacity/zero-device evidence and recheck the accepted evidence throughout the workload. Missing, contradictory or unbounded CPU evidence must fail. Any use of host swap absence in place of an enforced per-container zero limit is a reviewed change in qualification criteria, not evidence of the old requirement passing. Obtain exact local-file approval first, then separate full-model cloud execution approval after preparation. Model weights, runtime, expected outputs and isolation remain unchanged.

## Local startup correction — verified checkpoint before cloud upload

The user approved five exact code files and the affected documentation, local tests and a diagnostic image build only. No new cloud operation, database access or NER inference was authorized or performed. Changes:

- `infrastructure/ner-check/Dockerfile` uses the new standard-library `backend/scripts/news_ner_cloud_entrypoint.py`. It acts as a Linux subreaper, starts the fixed isolated Python probe as its child, forwards SIGTERM/SIGINT, allows at most six seconds before forced shutdown and two seconds for orphan cleanup, reaps children, propagates failures and rejects arbitrary CLI commands. Leftover children produce failure rather than a false success. It adds no dependency and never imports model/application code.
- `backend/scripts/news_ner_cloud_probe.py` supports the actual v1 resource paths and existing v2 paths. Malformed present v2 files do not fall back to valid v1 data. The exact original one-CPU/three-GiB/no-swap requirements still apply. A single snapshot binds resource readings to the diagnostic verdict, avoiding changing-peak disagreement. Large resource integers use decimal strings in evidence instead of lossy Cloud Logging numbers. Bounded `/proc/swaps` and `meminfo` summaries omit filenames and distinguish host observations from an enforced container swap limit.
- `backend/scripts/qualify_news_ner_cloud.py` freezes both scripts, verifies the fixed entrypoint, removes dependency on Docker external init and checks actual local isolation/supervision/configuration. Diagnostic schema v2 independently checks resource/host-swap claims; successful collection never means successful inference. The original claim and frozen prediction oracle are retained.
- `backend/tests/test_news_ner_cloud.py` adds compatibility, rejection, evidence-integrity, single-snapshot and launcher-contract regressions. **103 tests pass**, zero skips/failures/errors across it and affected subprocess/two-/three-GiB suites. The first Windows launcher mock omitted a Linux constant: its three failures are retained, the fixture was corrected, and later checks pass. No test was removed to hide failure.

Nine actual Linux container cases pass: compatible v1 diagnostic; cloud-like v1 diagnostic with strict rejection; cloud-like preflight rejection; inherited credential rejection; child failure propagation; SIGTERM forwarding; SIGINT forwarding; forced shutdown; orphan cleanup/rejection. Final-image preflight and ordinary diagnostics additionally pass without Docker external init: launcher PID 1, probe PID 7 and isolation child PID 8. Unchanged seccomp, socket-family/raw-syscall denial and parent-death guard all pass. These are local compatibility/containment checks, not cloud model results. The cloud-like fixture continues reporting 80,600/100,000 CPU and unknown/unbounded swap allowance and fails strict qualification, as required.

| Final local identity | Value |
|---|---|
| Image / OCI index | `sha256:07feb6398089a2da13ec8cf0584fd15e83a43f83d7c720423664f8bcc16e871c` |
| Package | `d77bb1fdc072f0535bfe58d9f7da76507afddd453d9cdc1ddee7412d59734da3` |
| Freeze | `634481433ec546336a56bb97d661708f6944a2b791cc102285a59d6895ad2f01` |
| Proposed private tag, not uploaded | `asia-east1-docker.pkg.dev/lanes-project-508809/lanes/lanes-ner-check:diagnostic-d77bb1fdc072f0535bfe` |
| Private evidence | `data/ner-cloud-check-20261022-startup-v2` |

The image inventory exactly matches its frozen application/input/asset context: 21 application files, three inputs, 17 assets; no application settings, credentials or expected answers. All 418 original receipt files and original model/runtime hashes authenticate unchanged. The earlier startup-v1 build passed but was superseded locally after the resource snapshot consistency review; its image, source context and receipts remain intact. Thirteen stopped owned containers across the two local revisions were inspected and removed. No cloud cleanup occurred. Full authorization, first/intermediate/final test receipts and pre-edit sources remain in `data/ner-cloud-check-20261022-startup-correction-approval`.

**At this local checkpoint:** corrected diagnostic upload/update and one execution were pending. They were subsequently approved and completed as recorded above. Retain 1 CPU, 3 GiB, one task, 600 seconds, zero retries and no credentials. That check must confirm supervision/isolation and gather the new swap evidence. The earlier actual 0.806 CPU quota and lack of an enforced zero-swap limit are not resolved or accepted by this local correction; any qualification-contract decision requires explicit review. No full cloud model attempt is authorized.

## Cloud creation and first execution — failed, preserved

The verified image was uploaded to the existing private `lanes` Artifact Registry repository with independently read registry digest `sha256:37fbb6ee0d68b166038687200b39744dfd91c127ddad3de36b020aeb0b608123`. Created the dedicated `lanes-ner-check` service account and unscheduled job in `lanes-project-508809` / `asia-east1`: one CPU, three GiB, one task/parallelism one, timeout 600 seconds and retries zero. Actual configuration/IAM checks confirm no application roles, credentials/secrets, user-managed keys, volume/Cloud SQL bindings or matching regional schedule. The initial creation request encountered service-account visibility propagation; after read-only verification showed attachment permission available, creation succeeded without extra IAM grants. This creation retry was not a model execution.

One separately authorized execution, **`lanes-ner-check-m6bf8`**, ran October 22, 2026, approximately **10:43:54–10:44:10 AM Philippine time**. Cloud Run imported and started the image. Its single task/attempt zero exited **1**. The only probe event was `failed`, with `ner_check_failed` / **`FileNotFoundError`**. No successful preflight, model-ready, record or completion event was emitted. The independent result verifier rejects the event sequence as `incomplete_execution`; the cloud test is **not passed**.

The frozen probe does not report the missing pathname or startup stage. Its cgroup-v2 resource-file assumptions are a suspected compatibility issue, **not a confirmed diagnosis**. No model-result, performance or isolation claim can be made for this cloud execution. Do not infer an out-of-memory failure from this missing-file error. Do not weaken limits, fabricate measurements, retry the attempt or reclassify the local result as cloud acceptance.

Full creation/configuration/IAM, execution/task status, structured logs and immutable attempt claims are retained in ignored `data/ner-cloud-check-20261022-cloud-v1` and `data/ner-cloud-check-20261022-cloud.claim.json`. The model, deployed image, existing workers, database and schedules remain unchanged after the execution. The temporary job/account/image remain unscheduled and retained; cleanup was not authorized or performed. The subsequent local investigation and one diagnostic upload/update/execution were separately authorized and are recorded below; further cloud operations require new approval.

## Approved cloud diagnostic — confirmed startup incompatibilities

With explicit approval, uploaded the locally verified diagnostic OCI index `sha256:d338e078dbfaf60059249149da136643329e85c29d24ded1e7dfb62a1d66ddfd`, updated only the existing unscheduled test job to `--diagnostic-only`, verified its configuration, then executed **`lanes-ner-check-wpsmc` exactly once**. The execution completed at **11:20:30 AM Philippine time on October 22**, task exit zero, attempt zero, no retries. The registry-authenticated index resolves to Linux amd64 manifest `sha256:200f1d8ee412e142c3dd12f267d50541577b58402aa15adc7e0a4c079321fc60`, matching the execution image. The emitted package identity and authenticated assets match the frozen diagnostic package. Diagnostic exit zero means evidence collected; it does not mean startup checks or NER passed.

| Actual evidence | Finding |
|---|---|
| Resource-file layout | CPU/memory controllers use cgroup-v1 paths; a separate unified mount is present. Required root `cpu.max` is absent (`v2_cpu`), confirming the resource-check incompatibility. |
| Process supervision | Probe PID 1, parent PID 0; diagnostic child PID 10, parent PID 1. Unchanged isolation returns `parent_guard_failed`; seccomp readiness was not reached or proved. |
| CPU | Job/ execution configuration is 1 CPU; readable quota is 80,600 per 100,000 microseconds, or 0.806 CPU. Cause of this difference is not established. Do not represent these as equal. |
| Memory | Actual cgroup limit is exactly 3,221,225,472 bytes (3 GiB). Diagnostic peak is 161,259,520 bytes; this is not loaded-model memory. |
| Swap | Readable memory-plus-swap limit is very large, not the memory limit. Cloud Logging represents the large integer as a floating-point value. Zero swap cannot be established from this packet. |
| Scope | No model session, prediction records, database credentials/access, new IAM grants, production worker or schedule changes. |

Independent verification accepts the diagnostic packet and execution/image/configuration binding, while leaving `qualification_passed=false`. Exactly two cloud executions now exist: the original failed check and this diagnostic. The ordinary news job still has its original rules-only image/arguments; the dedicated identity still has no project roles and no regional scheduler targets the test job. Full logs, configuration, authenticated manifest, task status, verification and immutable claim are retained in ignored `data/ner-cloud-check-20261022-cloud-diagnostic-v1` and `data/ner-cloud-check-20261022-cloud-diagnostic.claim.json`.

Next proposed local-only work: an image launcher that supervises/reaps processes and forwards shutdown signals; v1/v2 resource reading that reports actual quotas and separately validates cloud configuration; bounded evidence for swap and fail-closed handling if it cannot be established. Preserve the original model/runtime, network denial, memory/headroom, deadlines, external prediction oracle and prior claims. Obtain approval for exact code files before editing and for any further cloud execution; do not simply accept the failed resource checks or bypass the parent guard.

References: [Google Cloud container contract](https://docs.cloud.google.com/run/docs/container-contract), [job CPU settings](https://docs.cloud.google.com/run/docs/configuring/jobs/cpu), [Linux cgroup-v1 memory controls](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v1/memory.html). These explain the platform/measurement contracts; they do not establish the cause of the 0.806 quota or prove swap absence.

## Diagnostic revision — local preparation checkpoint

The user requested investigation after reviewing the exact three proposed files. Updated only the probe, controller and tests, plus the same approved documentation. The NER inference runtime, model/tokenizer, resource limits and existing deployed image are unchanged. Original tooling bytes were snapshotted before this delta; old images, freezes, claims and receipts remain preserved. Do not overwrite or relabel the original local or cloud package.

- **83 tests pass**, zero skips/failures/errors. Retained-artifact checks explicitly skip on fresh checkouts without private artifacts; all ran here. A cgroup-v1 fixture reproduces the original generic missing-file failure, and the revised probe identifies the missing `v2_cpu` file at `resource_check` without printing arbitrary filenames or exception text.
- The new diagnostic-only mode authenticates inputs/assets, inventories only known cgroup-v1/v2 resource files and relevant mount metadata, and runs the unchanged isolation check in a bounded child. It never constructs a model session or claims NER qualification. The strict full-test resource contract is unchanged; readable alternative files do not silently create a pass.
- The built nonroot/no-network image passes ordinary local preflight and diagnostic collection. Three additional controlled container cases verify localized preflight failure with a fictional legacy cgroup mount, non-inference collection of that layout, and `parent_guard_failed` when deliberately running the supervisor as PID 1 without Docker's init process. These are **local fixture results**, not proof of either condition on Cloud Run.
- Five stopped owned diagnostic containers were removed after their inspection evidence was retained. No new neural inference, cloud upload/update/execution, database access or schedule change occurred in this revision. The original 418 predecessor files and NER runtime/bundle still authenticate unchanged.

Prepared image: `sha256:d338e078dbfaf60059249149da136643329e85c29d24ded1e7dfb62a1d66ddfd`. Diagnostic package: `64867a5e67028b193ecb87f3133ee27d6a0020864205726daf2e4b0165dff4bc`. Freeze: `b1ef34a53c86ce35f33ae3ff35f5d34f6f7d1966b503f08e700567b864ca8569`. Private preparation, tests, controlled-case logs and snapshots: `data/ner-cloud-check-20261022-diagnostic-v1`.

At this preparation checkpoint the proposed cloud action was upload and update of **only** `lanes-ner-check` to this image with `--diagnostic-only`, followed by one diagnostic execution; its later explicit approval and outcome are recorded above. It keeps the existing account, no application roles/credentials/database access, one CPU, three GiB, one task, 600 seconds and zero retries. Diagnose the real file layout and parent/isolation behavior before proposing a correction or another full NER attempt. This revision does not establish that Cloud Run NER works.

## Verified local delivery

- **75 tests pass**, zero skips/failures/errors, across the new cloud-check boundaries and existing subprocess/two-/three-GiB resource regression suites. No application dotenv, API startup or database fixtures are loaded.
- The separate image authenticates the existing inference bundle and unchanged runtime, and includes only inference application code, exact qualification inputs and model assets. Its cleaned final stage excludes the base image's old application/test files from its layers. Expected predictions/full graph hashes remain outside the image. A filesystem inventory confirms no application settings, migration code or expected-answer files.
- One separately claimed local inference attempt completes **355 requests**: 345 passages, six complete articles, three stress cases and one reviewed article. Independent verification matches all **355 complete proposal/graph/provenance hashes**, all **352 retained prediction records** and the reviewed article's **53 mentions**. This is known-input deployment regression evidence, not an unseen accuracy evaluation or a real history-seeding batch.
- Actual child seccomp/network-denial readiness and parent-death protection pass. The nonroot, read-only, no-network local container uses one CPU, three GiB/no swap, dropped capabilities and no new privileges. Clean loaded-model shutdown/reaping passes. An additional built-image credential guard rejects an injected fictional database setting before model startup.

| Measurement | Observed | Requirement |
|---|---:|---:|
| Model cold start | 1.5572 s | ≤60 s |
| Passage p95 | 0.03998 s | ≤1 s |
| Longest request | 11.1806 s | Stress ≤60 s; ordinary articles separately pass ≤30 s |
| Session | 23.2921 s | <450 s |
| Cleanup | 0.2523 s, child exit 0 | ≤5 s, clean exit |
| Combined cgroup peak | 1,877.5 MiB | <2,688 MiB |

The local image is `sha256:37fbb6ee0d68b166038687200b39744dfd91c127ddad3de36b020aeb0b608123` (approximately 1.34 GiB uncompressed). Package identity: `17ef610a2933c217fb3588b6d05422ca83613951ce915661e688464c602bf73b`. Freeze: `91ffefa3e853c1dea8dffa8cdfc6931070651429d9f005c31898d6d510f4a8cc`. A local image ID is not the registry digest required for cloud creation.

## Preservation, cleanup and remaining approval

All **418 prior three-GiB receipt/package files**, the original model/tokenizer/runtime and historical one-attempt claims authenticate unchanged. The new claim and full input/oracle/output/inspection evidence remain under ignored `data/ner-cloud-check-20261022-local-v1` and the separate local claim file. Three stopped owned test containers were removed after their inspections and successful verification were preserved. The image remains available for upload review. Automated tests and this evidence are retained.

At the original local checkpoint, read-only inspection confirmed the proposed job/account did not exist. The separately approved creation and failed execution are recorded above. The existing scheduled news worker remains the rules-only one-CPU/one-GiB job. Local backend configuration points to the existing Cloud SQL instance; local Valhalla configuration remains local. No database, migration, ordinary application setting, existing deployment or schedule was changed.

Upload, creation and the first execution approvals have been consumed. Cloud compatibility and resource/isolation measurements remain unverified; the failed attempt must not be automatically retried or silently weaken checks. Cloud image storage can still incur charges while the retained image exists. Compatibility/supervision edits, another execution, production integration and eventual cleanup remain separately gated by the user's approval.

After cloud acceptance, separately review production integration and eventual cleanup of temporary, unused cloud resources. Keep regression tests and verification records. Part 2A seeding and Part 2B active September examples remain unexecuted.

[Structured local verification](summary.json) · [Operator guide and cloud acceptance](../../guides/ner-cloud-check.md)
