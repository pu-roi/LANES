# Separate NER Cloud Run check

This is an unscheduled inference-only qualification job, not the automatic news worker. It uses the existing v19 control seed-0 model, tokenizer, location/context code and the retained 355-request workload. The API, Valhalla, scheduled rules-only news processing, Cloud SQL and unified history are unchanged. No training, publication or history seeding is performed.

Creating/uploading cloud artifacts, creating the job and executing it require the user's separate approval. Never use the normal root `cloudbuild.yaml` for this check: that pipeline deploys other components and executes migrations and the scheduled news worker.

## Current outcome — isolated full cloud qualification passed

The separately approved full execution **`lanes-ner-check-nbpmz` passed**, with all 355 graph/provenance results, 352 retained predictions, 53 reviewed mentions, 358 approved-profile resource snapshots, original timing/memory/isolation and clean shutdown independently verified. Actual saved job/execution settings, authenticated registry index/platform manifest, task attempt zero/exit zero, no retries, role-free/keyless runtime and absence of scheduling/Cloud SQL bindings also pass. Peak memory 2,067.3 MiB; cold start 4.9637 s; session 30.7342 s; cleanup 0.1835 s. [Indexed acceptance](../evaluations/ner-cloud-check-20261022/README.md#cloud-acceptance--full-frozen-workload-passed).

The exact profile image is now deployed on **only the unscheduled test job**, with diagnostic-only arguments cleared. Its consumed one-attempt claim and full evidence are retained under `data/ner-cloud-check-20261022-cloud-full-v1`. Do not rerun it under old approvals or reset any claim. This acceptance uses the explicit approved cloud criteria: configured 1 CPU verified independently, measured quota 1.043 recorded unchanged, actual hard 3 GiB memory limit and host-no-swap evidence at every checkpoint. It does not retroactively pass the original strict measured-one/enforced-zero checks.

Production automatic news processing remains rules-only; the API, Valhalla, Cloud SQL and schedules are unchanged. Do not connect workers, migrate or seed data under this test authorization. Prepare a concrete production-integration proposal for review and approval next. Retain automated tests, frozen expected outputs and all attempt evidence. The temporary test job/account/images stay unscheduled and retained until separately approved cleanup after handoff; do not remove them implicitly or remove regression tests.

## Approved resource profile — retained local preparation checkpoint

The user explicitly approved `cloud-run-v1` in the probe/controller/tests. It keeps `local-strict-v1` as the default and original local claim protection. Prepare explicitly with `--resource-profile cloud-run-v1`; the selection is hashed into the image input/configuration/identity and later operations cannot change it. The current model/runtime/launcher are unchanged. **150 tests and 12 Linux container cases pass**, plus final-image preflight/supervision/isolation and exact-context inventory; no NER was loaded or cloud changed during this revision.

Cloud CPU acceptance now combines independently verified actual job/execution configuration (1 CPU) with positive finite measured quotas recorded without rewriting them to one. Swap acceptance is either an enforced zero allowance or readable zero host devices/capacity/free, labeled as host evidence. Host evidence never claims an enforced container limit. Resource evidence is rechecked at all 358 full-workload checkpoints; unknown, malformed or contradictory evidence fails. Memory remains exactly 3 GiB, peak below 2,688 MiB; original prediction hashes, timing and isolation checks are unchanged. Earlier strict failures remain failed. Use frozen earlier scripts for their historical schemas rather than applying current tools to old source freezes.

Private current package: `data/ner-cloud-check-20261022-cloud-profile-v1`. Image: `sha256:e9fb8f878b3e84283cfd46da4e154db24357bd107bf15f8753f4b96510eb8e42`. Package: `ca02f710217295ca019c7162470fd4471bb20bcf6ad61e0f335478f2b690f79d`. Freeze: `6e89a749a81439187fa1dd60a9058843bb3e9af03af9be7e288ab11cd7f6a49b`. All preparation/build/diagnostic receipts already exist; do not overwrite them or use `execute-local`. The new `cloud-qualification-plan` command prepares a proposal only. Expected answers remain outside the image.

**At this preparation checkpoint, the next cloud action required explicit approval:** upload the exact image, update only `lanes-ner-check` and clear diagnostic-only args, resolve/authenticate the registry index/platform digest, verify actual unchanged account/limits/no credentials, and execute one full workload asynchronously with zero retries. Create a new immutable claim before dispatch; never reset prior claims or retry an ambiguous dispatch. The full test is 355 requests, not a seed/publication batch. Verify task status/attempt, structured logs, frozen model/results and every resource snapshot, then call `verify_cloud_configuration` on saved actual job/execution metadata. Results alone cannot prove configured CPU/settings. Retain registry/IAM/schedule evidence before public acceptance. Do not change the ordinary worker/API/Valhalla/Cloud SQL/schedules.

This reviewed new cloud profile does not establish that the old strict measured-one-CPU/enforced-zero-swap criteria passed. It preserves that local profile and separately records cloud configuration, actual measured CPU and the actual swap evidence basis. A failed future model attempt requires review and new approval before another run. Cleanup and production integration remain separate.

## Original cloud failure — retained checkpoint

The original local package and its 75 tests pass. With separate approval, its exact image and dedicated unscheduled job/account were created. One separately approved execution, `lanes-ner-check-m6bf8`, failed on October 22, 2026, at 10:44 AM Philippine time with `FileNotFoundError` before any successful preflight/model-ready/result event. The original probe did not localize the missing file. A later approved diagnostic confirms the required root cgroup-v2 CPU file is absent and the PID-1 parent guard fails. Preserve the cloud attempt claim and evidence. Do not rerun the job or bypass its checks. The diagnostic revision passes 83 local tests. Its approved cloud upload/update and single execution (`lanes-ner-check-wpsmc`) collected evidence successfully, without model loading; full NER acceptance remains open. [Evidence](../evaluations/ner-cloud-check-20261022/README.md).

The creation recipe below is retained operator guidance, not an instruction to recreate or update the existing job. The job now uses the approved diagnostic image/argument, retains the same limits/account and has no schedule or retries. Cloud SQL and the production news worker remain unchanged.

## Earlier corrected diagnostic — supervision passed

The corrected diagnostic image was separately approved, uploaded and executed once as `lanes-ner-check-b4b8m`. Actual Cloud Run supervision, seccomp/socket denial and parent-death guard pass. The memory limit is exactly 3 GiB. No model was loaded. Actual CPU quota is 1.043 despite configured 1 CPU (earlier diagnostic: 0.806); host swap devices/total/free are zero but the combined cgroup limit does not establish an enforced zero allowance. The strict original resource contract remains unsatisfied.

Do not run full inference or repeatedly retry diagnostics under the consumed approval. Review an explicit versioned cloud-specific resource profile before any code edits: verify configured CPU separately from recorded bounded quota; preserve memory/headroom, prediction oracle, isolation and deadlines; distinguish repeated host no-swap observations from an enforced container limit. Missing evidence must fail closed. At this checkpoint criteria/local edits were still pending; the later explicit profile approval is recorded above. A future full cloud execution still requires approval. The existing local strict profile remains intact. [Full evidence](../evaluations/ner-cloud-check-20261022/README.md#corrected-cloud-diagnostic--supervision-passes-resource-review-open).

## Local startup correction — retained preparation checkpoint

The approved five-file startup correction passes 103 tests and nine Linux containment/compatibility cases. The image now provides its own supervisor; local container checks intentionally omit Docker `--init`. The unchanged model child runs beneath the probe and retains its seccomp/socket denial and parent-death checks. SIGTERM/SIGINT are forwarded, child failures propagate, live orphan leaks fail and cleanup is bounded. Existing model/runtime files remain unchanged.

The probe now reads both controller layouts, preserves actual quotas and large numeric evidence, and separates bounded host swap observations from enforced container limits. Resource readings and their strict verdict use one snapshot. Diagnostic schema v2 requires these additional fields; use frozen earlier tools/receipts when examining the earlier v1 diagnostic rather than substituting current sources into its freeze. Exact one-CPU/three-GiB/no-swap full-qualification checks remain enforced. The earlier 0.806 CPU quota and unbounded combined swap allowance cannot become a pass simply because layout/supervision is corrected.

Final private package: `data/ner-cloud-check-20261022-startup-v2`. Image: `sha256:07feb6398089a2da13ec8cf0584fd15e83a43f83d7c720423664f8bcc16e871c`. Package: `d77bb1fdc072f0535bfe58d9f7da76507afddd453d9cdc1ddee7412d59734da3`. Freeze: `634481433ec546336a56bb97d661708f6944a2b791cc102285a59d6895ad2f01`. Prepare/build/preflight/diagnose and the proposal have already completed once. Do not overwrite their receipts or use `execute-local`; no new model attempt was approved. Thirteen stopped owned containers were removed after preserving inspection receipts. Keep both local revision images, contexts and evidence.

At preparation, `cloud-diagnostic-proposal.json` was a proposal only. Its later approved upload/update/execution is recorded above. Further cloud actions need new approval. The approved action targeted only `lanes-ner-check` with `--diagnostic-only`, independently resolve the registry index/platform manifest, verify actual unchanged settings and execute once with zero retries. No database credentials, scheduled worker or application roles are added. Review its real isolation/host-swap evidence and the remaining CPU/swap difference before proposing a full model check; diagnostic collection is never model acceptance.

## Earlier diagnostic-only workflow — retained checkpoint

The diagnostic revision changes only the host controller, probe and tests; it leaves the original model/runtime and full-test checks unchanged. Its `--diagnostic-only` flag validates input/assets and records a bounded resource-file inventory, strict-check outcome and real short-child isolation result. It does not load NER, start a model session or qualify predictions. The independent diagnostic verifier rejects inference/qualification success claims. Missing files now report a startup stage and a fixed resource alias; arbitrary exception messages, source bodies and secret paths are not logged.

The following local operations have already run once against the new, separate frozen package. Do not overwrite either package or rerun original one-attempt inference tooling:

```powershell
.\backend\venv\Scripts\python.exe -B backend/scripts/qualify_news_ner_cloud.py diagnose-local --output data/ner-cloud-check-20261022-diagnostic-v1 --freeze-sha256 b1ef34a53c86ce35f33ae3ff35f5d34f6f7d1966b503f08e700567b864ca8569
.\backend\venv\Scripts\python.exe -B backend/scripts/qualify_news_ner_cloud.py diagnostic-plan --output data/ner-cloud-check-20261022-diagnostic-v1 --freeze-sha256 b1ef34a53c86ce35f33ae3ff35f5d34f6f7d1966b503f08e700567b864ca8569
```

`diagnostic-plan` requires matching local preflight/diagnostic receipts and only prints a proposal. It does not call Google Cloud. The prepared image is `sha256:d338e078dbfaf60059249149da136643329e85c29d24ded1e7dfb62a1d66ddfd`; use a new diagnostic registry tag and independently read digest after any approved upload. An approved update/execution must target only the unscheduled test job, set `--diagnostic-only`, retain the existing account/limits/no credentials, and start at most one diagnostic task with zero retries. Inspect the actual configuration before execution. A diagnostic result is environment evidence, not a successful NER workload; another full model attempt needs its own reviewed correction and approval.

Both local fixture conditions are now confirmed by the approved cloud diagnostic: missing root `cpu.max` and `parent_guard_failed` with a PID-1 probe. Configured CPU is 1, measured quota is 80,600/100,000 (0.806 CPU); memory is exactly 3 GiB. The packet does not prove zero swap or successful seccomp. Preserve actual measurements rather than substituting configured values. The diagnostic OCI index/platform binding, logs and verification are indexed in the evaluation. No further execution or compatibility edit is authorized by that diagnostic approval.

## Original local preparation and verification — retained checkpoint

Run from the repository root with the normal Python interpreter, **without loading application dotenv files**. These tools do not import application settings, create a database engine or invoke `gcloud`.

The original package commands below document the earlier frozen checkpoint. Current wrapper source has an explicit later diagnostic delta and cannot be substituted into its source freeze. Preserve the old source snapshots, image and receipts; do not rewrite hashes or reset claims to make a rerun pass.

The qualification tests require the authenticated, ignored local model/receipt artifacts. A fresh checkout must provision those retained artifacts first; do not download a replacement model or regenerate expected answers to satisfy the checks.

```powershell
.\backend\venv\Scripts\python.exe -B backend/scripts/qualify_news_ner_cloud.py prepare --output data/ner-cloud-check-20261022-local-v1
```

Preparation requires a new direct child of ignored `data/`. It authenticates the previous three-GiB freeze, independent audit, all 418 retained package files, inference bundle and unchanged runtime bindings. It copies only the inference packages, probe, bundle and exact request/workload into the build context. Expected predictions and complete expected graph hashes remain outside that context. Current tooling receives its own freeze; earlier receipts and one-attempt claims are preserved.

Use the returned freeze hash in the subsequent commands:

```powershell
.\backend\venv\Scripts\python.exe -B backend/scripts/qualify_news_ner_cloud.py build --output data/ner-cloud-check-20261022-local-v1 --freeze-sha256 <freeze-sha256>
.\backend\venv\Scripts\python.exe -B backend/scripts/qualify_news_ner_cloud.py execute-local --output data/ner-cloud-check-20261022-local-v1 --freeze-sha256 <freeze-sha256>
.\backend\venv\Scripts\python.exe -B backend/scripts/qualify_news_ner_cloud.py verify-local --output data/ner-cloud-check-20261022-local-v1 --freeze-sha256 <freeze-sha256>
.\backend\venv\Scripts\python.exe -B backend/scripts/qualify_news_ner_cloud.py cloud-plan --output data/ner-cloud-check-20261022-local-v1 --freeze-sha256 <freeze-sha256>
```

`build` uses the independently pinned existing qualification base without network access or package installation. The final image exports its cleaned filesystem into a fresh stage, excluding inherited application/test files from its layers. It runs as UID/GID 65532 and contains no database settings or expected answers. Build preflight authenticates assets/workload/resources without starting the model.

`execute-local` creates an exclusive `data/ner-cloud-check-20261022-local.claim.json` before the single approved neural attempt. Never delete, overwrite or bypass that claim to retry. The local container uses one CPU, three GiB memory with no swap, no network, a read-only root, dropped capabilities, no new privileges and a bounded temporary filesystem. A failure preserves logs, partial results and stopped-container evidence. It does not rerun automatically; review and request approval for a separately designed follow-up.

`verify-local` independently checks all 355 source-bound proposal/graph/provenance hashes, the 352 retained neural prediction records, the reviewed article's 53 mentions, isolation readiness, real container configuration, shutdown and resource/timing limits. Stable result hashes exclude volatile measurements. Logs contain identities, hashes, counts and measurements rather than source text or full predictions. Unexpected results, duplicate/omitted records, missing measurement evidence and malformed logs cannot count as success. This is a deployment regression check using known inputs, not a new NER accuracy benchmark.

Receipts are exclusive writes: these are ordered one-time operations, not a rerun loop. Verification requires the stopped measurement container. After verification, retain its inspection JSON and remove only stopped containers bearing the matching package label. Keep the image for upload review. The recorded local verification and `cloud-plan` remain usable after that cleanup; do not rerun inference or regenerate a verification receipt.

## Proposed cloud configuration — not authorization to apply

| Setting | Value |
|---|---|
| Project / region | `lanes-project-508809` / `asia-east1` |
| Job | `lanes-ner-check`, unscheduled |
| Runtime service account | `lanes-ner-check@lanes-project-508809.iam.gserviceaccount.com` |
| Application permissions / secrets | None; no Cloud SQL binding or credentials |
| CPU / memory | 1 CPU / 3 GiB |
| Tasks / parallelism / retries | 1 / 1 / 0 |
| Task timeout | 600 seconds |
| Image | Unique package tag in the existing private `lanes` repository; bind creation to its registry digest after approved upload |

The `cloud-plan` command only prints this proposal after matching local verification. It performs no cloud operation. Local Docker image IDs are not registry manifest digests; do not substitute one for the other.

Before creation, inspect the proposed service account and effective IAM access, confirm no existing job will be overwritten, and review the exact image/configuration with the user. Cloud Run jobs use the second-generation execution environment, but this does not prove our seccomp, parent-death, cgroup, dependency or full-workload checks will pass there. [Google container runtime contract](https://docs.cloud.google.com/run/docs/container-contract).

After upload/creation approval, create only the dedicated service account, private image and unscheduled job. Do not grant application roles, mount Cloud SQL, attach secrets, change the API's traffic or update Cloud Scheduler. Supply the verified digest, service account and the table's limits explicitly. Keep job creation separate from execution: do not use `--execute-now`. Request execution approval after confirming the actual deployed configuration. Cloud artifact storage and executions can incur charges.

The reviewed creation command will have this form, **after** an approved image upload supplies the actual registry digest:

```powershell
gcloud run jobs create lanes-ner-check --project=lanes-project-508809 --region=asia-east1 --image=<verified-registry-image-at-sha256-digest> --service-account=lanes-ner-check@lanes-project-508809.iam.gserviceaccount.com --cpu=1 --memory=3Gi --tasks=1 --parallelism=1 --max-retries=0 --task-timeout=600s --set-env-vars=LANES_NER_CHECK_PROFILE=isolated
```

Create the dedicated service account without assigning application roles, after its creation is approved. Treat an existing resource with that name as a review condition rather than updating it silently. Image upload, creation, execution and eventual deletion are never performed by the local qualification controller.

## Cloud acceptance and cleanup

For an approved execution, bind its execution name, actual image digest, one-task/no-retry configuration and package identity. Retrieve the execution's complete structured logs and resource/status metadata into ignored `data/`. The same inference-free `verify_events` function in `qualify_news_ner_cloud.py` compares the probe events to the external frozen oracles; cloud-specific deployment/execution/IAM inspection must also pass before recording cloud acceptance. A locally successful image or a Cloud Run success exit alone is insufficient.

Both profiles require all 355 results and 352 retained predictions to match, including the full reviewed graph/53 mentions, plus cold start ≤60 seconds, passage p95 ≤1 second, article/reviewed requests ≤30 seconds, stress requests ≤60 seconds, cleanup ≤5 seconds with child exit 0, session <450 seconds and startup + longest request + cleanup ≤125 seconds. Combined cgroup peak must remain below 2,688 MiB at the actual three-GiB hard memory limit. CPU/swap qualification follows the explicitly frozen profile described above: strict local measured-one/zero-limit checks, or approved cloud configured-one/recorded-quota and labeled zero-swap evidence. Supported cgroup measurements and unchanged child seccomp network denial/parent-death guard remain mandatory. Unsupported cloud measurements/isolation are explicit failures; do not weaken checks to obtain a pass. A failed or interrupted attempt requires review before another approved execution.

This first job does not qualify database writes, the full scheduled pipeline or historical seeding. After success, separately review the production worker integration. Before deleting the temporary cloud job, test-only identity or unreferenced image, preserve the verified evidence and obtain cleanup approval. Keep automated tests and documentation for future releases; never remove the existing production news, migration, expiry or Valhalla resources as test cleanup.
