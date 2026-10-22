# V37 offline association operator guide

> **Last Updated:** October 19, 2026, 8:05 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The bounded comparison is complete; LANES connection remains blocked.** Revised references show 90.45% association F1, four incorrect and 15 missed links. All 208 fictional cases pass, but zero-total-incorrect and baseline-retention acceptance fail. Do not treat this exposed training-subset score as independent accuracy. [Outcome](../evaluations/flood-ner-context-grouping-20261019/README.md) · [Metrics](../evaluations/flood-ner-context-grouping-20261019/metrics.json) · [Verification](../evaluations/flood-ner-context-grouping-20261019/verification.json).

## Read-only verification

From the laptop repository root, with the existing ignored private packages:

```powershell
$env:PYTHONPATH = 'backend'
.\backend\.venv\Scripts\python.exe -B -m training.flood_ner.context_run_v37 --grant .\backend\training\flood_ner\artifacts\context-association-grouping-20261019-v37\execution-grant.json --sha256 f35f57c13544a44b0e99ea1b97a784ffc8060f2cfe28b7543e1f359b00ecc04e
```

Require `verified_read_only`, `records: 232`, `training_started: false` and `application_connected: false`. This verifies bindings, not acceptance. The execution claim is consumed; the successful container is stopped. Do not add `--execute`, remove claims/locks, overwrite destinations, install missing resources or run archived authoring helpers to recreate evidence. A Git pull does not transfer ignored private data.

## Evidence and interpretation

- The private `context-reference-review-20261019-v37` package contains 23 uniform source-only reviews, 14 retained/nine corrected, unchanged entities/qualifiers/roles, all 103 prior relation mappings, full-article-only limitations, the representation supplement and three unchanged holds. The incidental generic-code/filename exposure receipt is preserved; no actual prediction/output/score data was exposed to that reviewer.
- The separate `context-association-grouping-20261019-v37` package contains all 39 old error dispositions, 70 pre-frozen correct-association mappings, reference/tokenizer qualification, 208 fixtures, raw-only request, protocol, implementation/tests, strict comparisons, remaining errors and preservation receipts.
- `context-association-execution-20261019-v37` preserves the one 232-input Linux attempt. No expected answers, references, models or validation/holdout data were mounted. Saved original-rules/v34/v35/v36 outputs were reused without rerunning those extractors.

The original 160 fixtures remain unchanged. Three new junction-access expectations were clarified from the source-only representation contract before implementation; draft bytes and changes are retained. One qualification checker failure on an omitted optional null role was fixed before freeze; no real-input execution retry occurred.

The 860 passing affected tests, including 299 new v37 checks, are separate from historical totals. The private analysis script and all scoring are bound before the real-input run. It performs saved-key scoring only. No post-result tuning is authorized.

Keep original-v36 and revised-v37 references/scores separate. The successor has 69.74% F1 under the unchanged old encoding and 90.45% under the clarified encoding. Neither number alone establishes system readiness or model improvement. All 70 pre-frozen mappings are retained, but an additional original-rules-correct local status under revised references is missed. That is a code omission, not missing neural recognition.

## Remaining gate

Four incorrect links and eight contextual misses remain, alongside seven links requiring absent/mistyped neural targets. Three reference holds remain. Pure-Tagalog real-world performance is unmeasured; Tagalog fixtures establish only constructed behavior checks. The trained model still recognizes six location labels; DEPTH/TIME are rules here.

A separately scoped task must address the remaining errors and limitations before proposing a read-only LANES demonstration. Preserve 345/60/60, the completed holdout exclusion and `rules_only` durable behavior. No automatic fallback, retagging, training, collection, production integration, upload or push follows. The desktop can remain off. [Representation clarification](../plans/ner-context-representation-v37.md).
