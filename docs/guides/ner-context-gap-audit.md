# Existing-data context gap audit

> **Last Updated:** October 19, 2026, 4:07 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Later acceptance preparation

The [interim acceptance package](../evaluations/flood-ner-context-acceptance-20261019/README.md) now qualifies 26 training dispositions (20 retain / four corrected proposals / two holds) and 40 fictional cases. The user selected the temporary hybrid demonstration priority; learned DEPTH/TIME remains unfinished. Next separately implement/test offline association repairs under the [frozen specification](../plans/ner-interim-context-acceptance.md), before any read-only LANES connection. No prior artifact or production behavior is changed. [Current operator guide](ner-interim-context-acceptance.md).

**The earlier audit/comparison checkpoint below is historical.**

The v32 audit is complete: **405 records inventoried, one guarded rules pass completed**. Read the [aggregate report](../evaluations/flood-ner-context-gaps-20261019/README.md) before proposing implementation or training. V19 recognizes six location classes; learned DEPTH/TIME and complete relationships remain unfinished.

## Private evidence and safe verification

The ignored packages are `backend/training/flood_ner/artifacts/context-gap-coordination-20261019-v32` and `context-gap-rules-20261019-v32`. They contain individual source-bound findings and must not be published. `analysis-v2` is the final inventory; `analysis-v1` preserves the earlier mechanical-state presentation before effective source-review holds were made explicit.

From the laptop checkout, this command only verifies the consumed execution binding:

```powershell
.\backend\.venv\Scripts\python.exe -B .\backend\training\flood_ner\context_gap_runner.py --grant .\backend\training\flood_ner\artifacts\context-gap-coordination-20261019-v32\execution-grant.json --sha256 d8c204c716c2559a20f7f8da008bfa627f2ecc74272a6b866196c3adb1a38352
```

Require `verified_read_only`, `neural_inference: false`, `training_started: false`. **Do not add `--execute`**: the grant is consumed, its single-use claim is preserved and another real-data extraction is outside this completed task. No worker is running and its active lock is cleared.

`reproduce_inventory.py` inside the coordination package can reproduce analysis from saved, hash-bound outputs into an absent child directory using `--output`. It performs no extraction or model execution. Authenticate that script and its input/output manifest before any later reproduction. Do not import executable code from older private packages, restore archives or use holdout contents as a fallback.

The worker uses the qualified Linux image and existing rules, with no references/models/credentials mounted. Only the coordinator reads development references for the limited audit. The coordinator may load the frozen vocabulary/tokenizer to check alignment; it must not load neural weights. Publication timestamps enter extraction only when their existing source metadata supports them. Absence of a resolvable instant is not evidence of an extraction error.

## Interpretation and next scope

There are **26 exact contextual pilot counterparts**, all in training. Five are held and 21 support limited diagnostics. **379 records, including all 60 validation passages, have no matching contextual references**. Text-only editorial blocks and a context-rich schema cannot fill this gap. Empty rule output is not a genuine negative. Partial span intersections are not entity or association accuracy.

Next propose a source-bound contextual annotation/association specification and reference-completion task on existing texts. Keep location labels, membership and partitions intact. Rule repair and a later learned DEPTH/TIME experiment need their own evidence and authorization; a tested interim hybrid remains a scheduling recommendation, not cancellation of the trained-model goal. The completed holdout stays closed, and the desktop can remain off.

This audit changed no production endpoint, extractor, database, dependency or durable processing mode. Do not bypass `rules_only`, apply annotations, export, train, upload or push from these instructions.
