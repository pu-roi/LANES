# Offline NER location shadow comparison

> **Last Updated:** October 19, 2026, 4:07 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Later acceptance preparation

The [interim acceptance package](../evaluations/flood-ner-context-acceptance-20261019/README.md) now qualifies 26 training dispositions (20 retain / four corrected proposals / two holds) and 40 fictional cases. The user selected the temporary hybrid demonstration priority; learned DEPTH/TIME remains unfinished. Next separately implement/test offline association repairs under the [frozen specification](../plans/ner-interim-context-acceptance.md), before any read-only LANES connection. No prior artifact or production behavior is changed. [Current operator guide](ner-interim-context-acceptance.md).

**The earlier audit/comparison checkpoint below is historical.**

This file-only tool compares retained v19 seed-0 location mentions with the existing sentence-based rules finder. It is not registered in application callers or endpoints and creates no claims, reports, zones or database rows. No context/status/depth inference or geographic resolution is added.

## Follow-on context audit completed

The separate [depth/time/association gap audit](../evaluations/flood-ner-context-gaps-20261019/README.md) inventories all 405 records and completes one guarded passage-only rules pass. It finds only 26 exact contextual training counterparts (21 supported / five held) and no contextual validation references. Next propose contextual annotation/association conventions and source-bound reference completion on existing texts. This does not connect location mentions to live claims, train DEPTH/TIME, or reopen the completed holdout. [Audit guide](ner-context-gap-audit.md).

## Current status

**The repaired Linux comparison completed and independently verifies all 14 inputs.** Six saved training articles and eight fictional cases were processed in one explicitly authorized continuation. The old failed attempt remains preserved and stopped; its lease was archived after ownership/state verification. The successful container is stopped with exit 0 and its active lock is cleared. [Executed outcome and aggregate evidence](../evaluations/flood-ner-shadow-execution-20261019/README.md).

Cold readiness 5.688 s, slowest input 0.666 s, peak worker RSS 450.79 MiB and execution wall time 9.206 s pass unchanged limits. All 1,245 protected hashes and stat-only validation/holdout entries remain unchanged. The 604 passing checks are preparation evidence; no source change required another suite run.

The execution grant below is **consumed**. Read-only verification remains safe, but another execution is not authorized and the single-use claim prevents reuse. Neither agreement nor a larger mention count establishes correctness. No live processing, training or validation/holdout evaluation occurred.

**Next:** separately design source-exact location association with flood status, time, depth and uncertainty. Do not repeat the completed comparison or reopen the completed research holdout as part of that design.

## Read-only verification

Use the existing Python 3.12 backend environment. This command validates local bindings without starting a container, loading model weights or writing output:

```powershell
.\backend\.venv\Scripts\python.exe -B .\backend\training\flood_ner\shadow_comparison.py `
  --grant .\backend\training\flood_ner\artifacts\shadow-repair-qualification-20261019-v31\prepared-grant.json `
  --grant-sha256 01cb7f07b03ca17455e6af3a6d174c12f3dc586f451c86d401ed0923eb78a35e
```

Expected: `verified_read_only`, `inference_started: false`, `application_connected: false`. Private inputs are ignored by Git; pulling the checkout alone does not transfer this preparation. Do not install resources, alter paths inside frozen artifacts or substitute a different model/image to make verification pass.

## Historical procedure used for the completed explicit attempt

These steps describe the completed continuation and are not authorization for another run.

1. Authenticate the repaired grant, matching test receipt, six full-extent use reviews, workload, model/resources and image. The original failed grant is stale and must stay unusable.
2. Reconcile the failed lease against its recorded container identity and fresh Docker inspection. Require stopped state, PID 0 and matching image/attempt. Archive the existing lease into a new, exclusively created private reconciliation record; retain its bytes, hashes, single-use claim and failed outputs. Do not remove an uncertain/live owner's lease or stop unrelated containers.
3. Only in an explicitly requested continuation, invoke the controller with `--execute`, the repaired grant/hash and a new direct artifact destination such as `shadow-execution-20261019-v31`. Never reuse a destination or authorize another automatic attempt.
4. Keep the qualified image and two-CPU/4-GiB isolation. Limits remain 60-second cold readiness, 30 seconds per article, 3-GiB peak worker RSS and 1,200-second overall execution. No credentials, network, GPU, references or saved predictions are worker inputs.
5. On failure, preserve the stopped/uncertain container, lease, partial rows and private traceback; stop without retry. On success, independently reconcile every row/hash and comparison count, measurements and artifact preservation before publishing aggregates.

Only raw article text, opaque IDs and hashes enter the service. Neural results retain all six labels. Unknown rules types/context stay separate; no entity confidence is manufactured. Neural overlap is invalid; rules overlap remains a diagnostic. Exact/type pairs are one-to-one, boundary links are explanatory, and unpaired counts include boundary-linked mentions. These are disagreements, not model accuracy scores.

The worker uses the existing offline rules guard to permit inert ORM declarations while blocking drivers, connections, queries and network/process dispatch. It never starts the backend server or initializes training. The current production extractor and `rules_only` persistence constraint remain unchanged.

All individual source texts, mentions, identities and traces stay private. Publish only aggregate status, counts, measurements and verification hashes. No validation/holdout evaluation, new data, retraining, live integration, upload, commit or push belongs to this workflow. A completed comparison is followed by a separately scoped claim-context design and tests.
