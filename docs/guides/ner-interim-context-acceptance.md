# Interim context acceptance operator guide

> **Last Updated:** October 19, 2026, 5:07 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Offline context association checkpoint — not qualified

**Offline association implementation and one comparison are complete; acceptance failed.** All 24 eligible training proposals and 40 fictional cases were processed with references outside extraction; the two held records remain unscored. **36/40 behavior cases pass; 34 correct links gained, zero baseline-correct links lost and 20 new strict silver-reference disagreements.** Those disagreements include demonstrated scope/time errors and separately recorded reference/grouping concerns; none was relabeled or hidden. **277 fresh tests pass (61 new)**; a broader timed-out test attempt remains incomplete. No empirical retuning occurred.

**Next proposal:** separately repair clause/time updates, collective/list scope and nearby-facility abstention, and independently resolve the recorded reference questions. Freeze a successor before a separately authorized comparison. **Read-only LANES connection is not cleared.** Preserve 345/60/60, the two holds and completed holdout exclusion; no retraining/new data is needed for this repair proposal. Learned DEPTH/TIME remains unfinished; October 25 readiness is unestablished. [Executed outcome](../evaluations/flood-ner-context-association-20261019/README.md) · [Current operator guide](ner-context-association.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Current status

The [reference package](../evaluations/flood-ner-context-acceptance-20261019/README.md) qualifies **26 training dispositions: 20 retain / four corrected proposals / two holds**, plus **40 fictional cases**. The user selected the interim location-model + depth/time-rule demonstration priority. Learned DEPTH/TIME is still unfinished; this is not system integration or behavioral repair acceptance.

Read the [frozen specification](../plans/ner-interim-context-acceptance.md) before any later repair. The private package is `backend/training/flood_ner/artifacts/context-acceptance-20261019-v33/`; individual sources/references and all correction proposals remain ignored by Git. Do not publish them or use fixtures as corpus members.

## Read-only verification

From the laptop checkout, with its existing environment and private files present:

```powershell
.\backend\.venv\Scripts\python.exe -I -B .\backend\training\flood_ner\context_acceptance.py --bundle .\backend\training\flood_ner\artifacts\context-acceptance-20261019-v33\qualification-bundle.json --sha256 29fb14621933482015c2f1440259077b34e139da22ba3f7cc68164d28bbbbf00
```

Require `qualified_reference_package`, `records: 26`, `fictional_cases: 40`, `training_started: false`, `neural_inference: false`, `application_connected: false`. The command only validates references/fixtures with the frozen tokenizer. It creates no outputs, runs no extractor and loads no model weights. Its absolute private file bindings apply to this laptop; a Git pull alone transfers no ignored package. Do not alter frozen bindings or install resources automatically if a check fails.

`references.json` contains the original historical reference, exact current location-only counterpart, separate proposed contextual reference and review disposition. Eligible references have explicit per-field completeness. Two held records remain incomplete/unresolved; do not count empty/missing fields as negatives. `source-review-ledger.json`, `change-proposals.json`, `source-use.json`, `coverage.json` and `protocol.json` explain evidence, limits and allowed use.

`qualification-bundle.json`, `freeze.json`, `tested-bindings.json` and actual command receipts bind the inputs, implementations, tests and CPU verification. `private-manifest.json` authenticates package outputs at finalization; its hash is in the public aggregate. Preserve predecessors and failed development evidence. Do not execute preserved private scripts as a shortcut or regenerate evidence to match a desired outcome.

## Following task and limits

The next task is a separately scoped offline association repair/comparison using saved **training-only** v19 location predictions. Freeze the existing-rules baseline and implementations, supply no references to extraction, and test every fictional behavior case plus eligible real references. Report recognition and association separately, support/abstentions, new incorrect links and retained correct links. The current qualification verifies the expected references, not a working association engine.

Only then plan a read-only LANES connection. Keep the existing durable `rules_only` restriction and source/status/time/depth/geometry/expiry checks. Never coerce LOCAL_AREA into an administrative type or use a detected place as proof of flooding. Keep validation and the completed holdout closed for this interim development path; no new data, training, upload or push is automatic. The desktop can remain off.
