# Retained v19 runtime preflight and integration design

> **Last Updated:** October 19, 2026, 12:20 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Gate 3 remains open.** V19 corrected control seed 0 remains retained. Its Windows backend-runtime smoke test passes; Linux qualification is blocked by the unavailable Docker Linux engine. The shadow integration design is complete, but no application connection has been implemented.

## Verified outcome

| Check | Actual result |
|---|---|
| Selected checkpoint | All 11 model files match the scoped primary-checkpoint manifest. |
| Pinned resources | All 23 files match the pinned pretrained-resource manifest. |
| Existing backend runtime | Windows AMD64, Python 3.12.14, spaCy 3.7.5, Thinc 8.2.5, NumPy 1.26.4, BLIS 0.7.11. |
| Vocabulary | Floret-mode, width 200, successful load and lookup without the standalone floret distribution. |
| CPU neural smoke | Four fixed fictional probes, 40 timed warm calls; deterministic predictions and frozen tokenizer reconstruction equality pass. |
| Linux runtime | Docker CLI exists; server query fails because `dockerDesktopLinuxEngine` is unavailable. One start of the existing Desktop engine did not make its API available. |
| Application | Current rules processing is unchanged; no live model connection, database writes or provider request. |

The CPU probe measured model construction/load at **0.329 seconds**, the first four fictional calls together at **0.051 seconds**, warm median **13.13 ms** and maximum **14.67 ms** per call. These are laptop Windows smoke observations. Imports are excluded from load timing, peak RAM is unmeasured and tiny fictional passages cannot establish long-article latency, Linux compatibility or a production SLA. No accuracy score or model improvement was measured.

The worker overrides only the tokenizer construction config in memory to remove desktop path dependencies; original config/model bytes remain unchanged. It registers an inference-only tokenizer factory and never imports the training callback registry, initializes a pipeline or creates an optimizer. No training/validation/holdout texts or references are passed to it.

An initial dependency hypothesis incorrectly treated standalone floret as required. Its preserved first preflight is superseded by run02 and the successful vocabulary/CPU probes. No dependency was installed or changed. Existing spaCy code implements floret-format vector access itself; absence of that separate distribution is not an observed inference failure.

## Integration design findings

The current application calls the rules extractor and placement services. NER locations must remain inputs to contextual flood interpretation; they are not flood claims or verified geography. The design addresses unchanged-body offsets versus current stripping, repeated mentions, LOCAL_AREA mapping, explicit failure reporting, model/version identity, existing context/placement gates and separate shortlist callers.

Durable processing has a database `rules_only` mode constraint. The next connection must begin as a separate read-only shadow adapter; a future durable neural mode needs an explicitly approved migration. No constraint or schema has been changed. [Full design and Gate 3 acceptance requirements](../../plans/ner-v19-shadow-integration.md) Â· [Operator guide](../../guides/ner-runtime-qualification.md).

## Verification and next step

**322 fresh tests pass, including 54 new runtime checks.** They cover stale manifests, complete model/resource bindings, path traversal, invalid labels/spans, Unicode and repeated mentions, request privacy/scope, blocked training/network methods, subprocess errors/timeouts, malformed diagnostics, private output boundaries and overwrite rejection. The other 268 checks exercise the existing saved-prediction studies/comparisons with constructed fixtures. Frozen helpers, dependencies, public APIs and database schemas remain unchanged.

The private coordination package preserves exact requests, test/source bindings, raw Docker/environment diagnostics, outcomes and preservation receipts. Public [verification metadata](verification.json) contains only aggregates and hashes. Earlier research references remain AI-assisted silver with incomplete-history/accounting limitations. Data remains **345 training / 60 validation / 60 completed research holdout**.

Next finish Linux CPU qualification: hash-bound inference resources, training-only prediction parity, representative article latency, peak RSS and failure/restart tests under a frozen resource envelope. Then implement a separately scoped shadow adapter. No training, validation rerun, completed-holdout access, live integration, upload, commit or push occurred.
