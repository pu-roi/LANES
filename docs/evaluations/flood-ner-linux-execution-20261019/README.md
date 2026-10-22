# Retained v19 Linux CPU qualification passed

> **Last Updated:** October 19, 2026, 1:29 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Gate 3 runtime qualification passes for the frozen local Linux profile.** V19 corrected control seed 0 remains retained. Exact prediction compatibility, runtime limits and executed failure-containment checks pass. This is not a live system connection, deployment qualification or an accuracy improvement.

Dataset membership remains **345 training / 60 validation / 60 completed research-holdout passages**. Only the 345 training passages were inferred for compatibility; validation and holdout were not evaluated or supplied to the worker. No training occurred.

## Authenticated environment and inputs

Docker Desktop is now **4.95.0.242831**, with Linux engine **29.8.2**. The earlier 4.91 crash and failed shutdown/restart records remain unchanged. The engine's recovery is not attributed solely to the launch method; the installed version changed between observations.

The unchanged backend Dockerfile and requirements build successfully, including the existing spatial-asset verification step. The isolated image resolves **Python 3.12.15, spaCy 3.7.5, Thinc 8.2.5, NumPy 1.26.4 and BLIS 0.7.11** on Linux x86_64. Its complete 152-package inventory is private and hash-bound. No existing Windows environment or dependency requirement was changed.

- Python base: `python@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1`.
- Built image: `sha256:a51ce2a6b0f19f382ce96bf63c265e060b37112098176c97c66c23e887794680`.

All 11 selected checkpoint files and 23 pinned pretrained-resource files authenticate. An inference-only tokenizer factory relocates paths in memory while preserving original config, tokenizer, vocabulary and model bytes. It imports no training callbacks, initializes no training pipeline and performs no optimizer updates.

The worker receives raw unchanged text, opaque IDs and hashes only. Original saved predictions stay outside its mounts and are joined by the coordinator after execution. Annotation references, full coordination packages and source-use evidence are not worker inputs.

Six complete saved training articles were read and separately assessed for exact full-extent, private transient computational evaluation. Their lengths are **490 / 2,290 / 10,001 characters** for English-associated sources and **568 / 1,654 / 8,755** for Taglish-associated sources. Selection is shortest/lower-median/longest by saved captured length and source hash, deduplicated by source. Associated training language does not imply uniform full-article language.

Full-copy amounts, publisher/quotation/media attribution, prior selected extents and saved project basis are recorded privately. This is a new case-specific assessment for the already authorized private research purpose, not automatic passage-permission inheritance, publisher AI permission, legal approval, new publisher-policy applicability or production use. No article, passage or label became a new corpus member. Existing history/acquisition/retention limitations remain.

Three fictional stress inputs include Unicode, repeated mentions, surrounding whitespace and an unchanged **100,000-character** maximum-length input. They remain outside dataset membership.

## Measured compatibility and performance

**All 345 predictions match the saved v19 seed-0 spans and types exactly: zero mismatches.** Record/text/hash joins, six-label span validation, frozen tokenizer serialization and token reconstruction pass. This measures runtime parity, not precision/recall/F1 or generalization.

The measurement container uses **two CPUs, 4 GiB RAM, swap capped at the same total, one worker, no network, read-only assets/inputs/root filesystem and no credentials or GPU**. Actual container inspection confirms these bindings. Cold host readiness includes the start operation and imports; worker model-load timing is recorded separately.

| Measurement | Actual | Frozen limit | Result |
|---|---:|---:|---|
| Cold host readiness | 4.078 s | 60 s | Pass |
| Warm passage p95 | 36.23 ms | 1 s | Pass |
| Slowest of six articles | 0.507 s | 30 s each | Pass |
| Maximum-length stress | 5.368 s | 60 s | Pass |
| Peak worker RSS | 1,883.52 MiB / 1.839 GiB | 3 GiB | Pass |
| Container execution wall time | 22.992 s | 1,200 s | Pass |

Warm passage median is **21.49 ms**, maximum **69.61 ms** and measured inference throughput **43.64 passages/s**. Article median is **93.74 ms**. These are local, single-worker workload observations, not a cloud SLA. Throughput uses measured inference-call durations and excludes joins, capture, geographic resolution, database work and the rest of the application. Peak RSS covers the worker workload including the maximum stress case; it is not the complete application/container footprint.

No limit was increased, text rewritten/truncated, chunking introduced, model changed or inference retried to obtain a pass. [Full aggregate timings, resource values and verification hashes](verification.json).

## Executed failure handling

Eight fictional-input probes execute in separate disposable containers bound to the same image and grant. They have one CPU, **128 MiB RAM with swap capped at the same total**, no network, no credentials and no corpus/model mounts. Deliberate memory exhaustion is contained to its own cgroup; unrelated database/routing containers and host settings are unchanged.

| Probe | Required observed outcome | Result |
|---|---|---|
| Missing asset | Source validator rejects absent fictional asset | Pass |
| Mismatched asset | Hash validator rejects changed fictional bytes | Pass |
| Malformed input | Raw-text workload validation rejects wrong text type | Pass |
| Oversized input | Validation rejects 100,001 characters | Pass |
| Timeout | Bounded wait expires; only owned container is killed and confirmed stopped | Pass; exit 137, OOM false |
| Controlled crash | Expected nonzero exit preserved and no automatic restart | Pass; exit 23 |
| Container OOM | Cgroup OOM is observed and process stops | Pass; exit 137, OOM true |
| Explicit new process/destination | Fresh fictional receipt succeeds without overwriting prior failure output | Pass; exit 0 |

Expected injected faults are successful tests because their prescribed containment/reporting checks passed; an unexpected result would have stopped the suite. They do not demonstrate recovery of a live application, database transaction, production worker or model service. Named containers remain stopped as evidence; no qualification container is running and the active lock is cleared after successful completion.

## Tests, preservation and decision

**475 fresh constructed regression checks pass before real dispatch**, including 82 checks for the new versioned runner. They cover stale bindings, reference/prediction separation, identity/text joins, Unicode spans, source-use scope, malformed/oversized inputs, fixed limits, measurement reconciliation, mounts/isolation, concurrent writers, partial receipts, interruption, fault outcomes and rejection of supplied readiness claims. The original v27 helpers/tests and Windows smoke helpers remain unchanged.

Final verification independently recomputes prediction parity and performance checks from actual worker output, inspects fault-state exits and receipt hashes, binds all probes to the exact image/grant and rechecks protected inputs. All **633 protected file hashes**, **55 stat-only holdout entries** and **27 stat-only prior-validation entries** remain unchanged. Individual texts, source identities, annotations, predictions, raw logs, package inventory and source-bound reviews stay in ignored private artifacts.

The qualified result is **compatibility passed / performance passed / failure handling passed**, under this local profile. AI-assisted silver status and incomplete-history/accounting limitations are preserved; no human-gold, certified-fresh or accuracy-improvement claim follows.

**Next: separately implement the read-only shadow adapter.** Keep the retained model and contextual evidence/placement gates intact. Durable processing still has a `rules_only` database constraint and requires a separately approved schema task before a neural processing mode can be persisted. No application integration, validation rerun, holdout access, training, deployment, upload, commit or push occurred. [Runtime guide](../../guides/ner-runtime-qualification.md) · [Integration design](../../plans/ner-v19-shadow-integration.md).
