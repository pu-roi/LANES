# V41 context-repair operator guide

> **Last Updated:** October 19, 2026, 10:20 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The bounded offline repair passes.** Time cases 36/36, new regressions 36/36 and old context fixtures 238/238 pass. The combined unchanged proposal view scores 104 TP / 0 FP / 1 FN on the reviewed training subset. This is not system-connection approval. [Outcome and limits](../evaluations/flood-ner-context-repair-v41-20261019/README.md).

## Components and evidence

- `context_association_v41.py` is the separately versioned context extractor. Frozen v38/v40 remain unchanged; no global monkeypatching or location-rule execution is used.
- `context_cases_v41.py` contains 36 constructed expectations. `context_worker_v41.py` receives raw cached mention views only. It cannot load neural libraries or dispatch network/database/process operations.
- `context_study_v41.py` authenticates predecessors, freezes the study, permits one execution and scores references only in the coordinator. It reports original plus all four saved proposal views separately.
- `context-repair-authoring-20261019-v41` retains the bound 419-pass software receipt. `context-repair-prepared-20261019-v41` holds the freeze, raw-only request, constructed expectations and immutable `analysis-v1`. `context-repair-execution-20261019-v41` holds the isolated stopped-container receipts and raw outputs. `context-repair-verification-20261019-v41` holds independent saved-output verification and individual reviews.

All private packages are under the Git-ignored training artifacts directory. A Git pull does not transfer them. Expected answers, models and validation/holdout data are not worker mounts. Saved 345 training location rows and 36 location-fixture results are preserved, not regenerated on study inputs.

## Read-only verification

From the laptop repository root containing the private packages:

```powershell
$env:PYTHONPATH = 'backend'
.\backend\.venv\Scripts\python.exe -B -m training.flood_ner.context_study_v41 verify --freeze backend/training/flood_ner/artifacts/context-repair-prepared-20261019-v41/freeze.json --sha256 9678017c183f5b9372ef22b33ccf76aba890738a51742c7330ca0061f15f5abe
```

Require `verified_read_only` and `records: 334`. Verification checks bindings and preservation; it does not execute extraction or authorize integration.

The single-use claim is consumed and its owned container is stopped. Do not rerun `execute`, delete claims, reuse occupied destinations, overwrite the analysis or change a freeze to bypass this result. Private authoring/verification scripts may create files and are not generic read-only commands.

## Meaning and remaining work

Keep original neural mentions and rule-assisted provenance separate. A report/publication clock is not flood onset; explicit onset can appear before or after its predicate. Preserve joint indoor-depth scope, ranges, repeated updates and genuinely shared counterexamples. Keep unresolved dates, timezones and references unresolved.

The remaining strict miss concerns non-flood access. The three contextual reference holds remain held; real pure-Tagalog performance and learned DEPTH/TIME recognition remain unfinished. The bounded result uses exposed silver training references and constructed cases, not independent accuracy.

The user's desired history/no-current-map policy for subsided reports is recorded for later integration. No API, database, plotting, routing or frontend behavior changes here. The next task is a separately scoped extraction-only connection proposal, not automatic deployment or retraining. The desktop GPU can remain off.
