# Linux CPU qualification: blocked before image build

> **Last Updated:** October 19, 2026, 12:43 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Gate 3 remains open. No Linux model inference or benchmark ran.** V19 corrected control seed 0 and the 345 training / 60 validation / 60 completed research-holdout passages remain unchanged. This task delivers a blocked preflight, tested measurement helpers and an authenticated training-only projection; it does not establish Linux qualification or start a system connection.

## Exact environment blocker

The Linux API pipe `dockerDesktopLinuxEngine` is absent and the WSL `docker-desktop` distribution reports **Stopped**. The latest recorded Docker backend startup crash says it cannot rename `%LOCALAPPDATA%/Docker/run/sailor-ingest.sock` to `sailor-ingest.sock.stale`: **“The file cannot be accessed by the system.”** Startup cancellation is logged at 12:08:51 PM and the crash report at 12:08:57 PM Asia/Manila. The underlying reason the socket is inaccessible is not established.

A normal start reports **Docker Desktop is already running**. One normal restart was attempted with a 30-second CLI timeout and 35-second wrapper timeout. Its pipe-capturing helper did not return a completed receipt and was interrupted; this is an uncertain command outcome, not evidence of a successful restart. A subsequent engine query still fails. Original evidence and an explicit missing-receipt disposition are retained privately. No socket was renamed/deleted, and no reset, reinstall, security change or system reboot occurred.

Further Docker troubleshooting stops here. The operator must restore normal Docker Desktop startup on the laptop before resuming qualification. Review its displayed error and local logs; avoid factory reset or data cleanup. Docker distinguishes ordinary restart from destructive cleanup/reset in its [troubleshooting guide](https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/). No diagnostics upload or support message was sent by this task.

## Separate outcomes

| Area | Actual outcome |
|---|---|
| Linux compatibility | **Unmeasured.** No image was built, no image/base digest or Linux package inventory was obtained, and no container was created. |
| Linux performance | **Unmeasured.** No startup, warm latency, throughput or RSS figures exist for this attempt. Earlier Windows smoke timings remain separate. |
| Failure handling | **Constructed regressions pass.** No real Linux fault/restart qualification has run. |
| Model/resource preservation | Eleven selected-checkpoint files and 23 pinned resource files authenticate against the frozen v26 identities. |
| Training-only inputs | All 345 authenticated records project into raw text, opaque ID, text hash and kind. Expected saved predictions remain separate; annotation references are not emitted. |
| Full article workload | **Pending.** No full-article use decision is inherited from passage permissions; eligible shortest/lower-median/longest sources per language must still be reviewed and frozen. |
| Dataset/model retention | V19 control seed 0 retained; data, tokenizer, models, partitions and recorded results unchanged. |

The task stopped before the image-build/measurement stage. The complete workload is not frozen, and compatibility/performance/failure gates are not passed. Do not interpret the blocked outcome, consistent manifests or passing mechanical tests as readiness.

## Implemented and verified preparation

New research-only controller/worker helpers preserve the Windows smoke and historical trainers. They enforce exact implementation/input bindings, a training-only projection, separate expected predictions, source-bound full-extent article reviews, six-class Unicode spans, opaque identity joins and strict prediction parity. Fictional stress inputs remain outside corpus membership.

The measurement path uses the unchanged backend Dockerfile and requirements. Its planned build pins the Python base using a named image context, an officially supported [Docker build-context override](https://docs.docker.com/build/concepts/context/#example-pin-or-override-images). It records the resulting image ID and resolved worker package inventory if execution becomes possible. Neither a base digest nor a Linux build was fabricated for this blocked attempt.

The frozen profile is **two CPUs / 4 GiB RAM / one worker**, with read-only assets/inputs/root filesystem, networking disabled, no credentials or GPU, bounded temporary memory and no automatic container restart. Limits remain 60-second cold readiness, 1-second warm passage p95, 30 seconds per saved article, 60 seconds for maximum-length stress, 3 GiB peak RSS and a 1,200-second overall guard. No limit is relaxed after observing results.

Command reservations precede dispatch; output is captured into exclusive files so descendant pipe handles cannot make the new helper wait indefinitely for captured streams. Timeout/interruption evidence remains private. This file-backed behavior is verified with constructed processes; the failed Docker restart was not repeated to test the change. Ambiguous attempts retain their owner lock and require explicit reconciliation before a new destination is used.

The controller deliberately cannot promote measurements into a Gate 3 pass through supplied readiness flags. Actual operational failure qualification remains separate from its measurement status. In this environment, neither phase could run.

**393 fresh regression tests pass, including 71 new Linux checks.** Checks cover malformed/oversized/raw-only inputs, missing/duplicate identities, Unicode offsets, annotation/reference separation, stale bindings, wrong runtime, source-use extent/purpose, deterministic article selection, fixed budgets, missing/nonfinite measurements, privacy of mounts, isolation inspection, exclusive receipts/locks, interrupted output, mocked crashes/OOM/timeouts and prevention of forged readiness. The remaining 322 tests recheck preserved research helpers with constructed fixtures, without application/database conftest imports. [Aggregate verification and hashes](verification.json).

## Resume requirements

1. Restore the Docker Linux engine without resetting existing data; require a successful Linux server query before dispatch.
2. Review existing complete training articles for the exact full-extent runtime use, choose the deterministic article workload and freeze its hashes with the 345 passages and fictional stress cases.
3. Freeze an execution grant against the current helper/test and unchanged backend bindings. Build the disposable image, run parity/performance checks and complete actual operational failure/restart verification. Preserve every failure; no automatic retry or raised limits.
4. Clear Gate 3 only from complete evidence. Then separately implement the read-only shadow adapter. Durable neural mode still requires its own approved schema task because saved processing is constrained to `rules_only`.

See the [operator guide](../../guides/ner-runtime-qualification.md) and [integration design](../../plans/ner-v19-shadow-integration.md). References remain AI-assisted silver with documented incomplete-history/accounting limitations. No article collection, validation evaluation, holdout access, neural inference, retraining, deployment, upload, commit or push occurred. The desktop GPU can remain off.
