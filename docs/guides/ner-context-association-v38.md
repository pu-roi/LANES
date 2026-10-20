# V38 fixed-reference context operator guide

> **Last Updated:** October 19, 2026, 8:36 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Completed: contextual repair passes; overall connection remains blocked.** Four wrong links and eight contextual misses were repaired on unchanged references. Seven recognition-dependent misses, three contextual holds and unmeasured real Tagalog performance remain. [Results](../evaluations/flood-ner-context-fixed-links-20261019/README.md) · [Metrics](../evaluations/flood-ner-context-fixed-links-20261019/metrics.json).

## Read-only verification

From the laptop checkout with the existing private packages:

```powershell
$env:PYTHONPATH = 'backend'
.\backend\.venv\Scripts\python.exe -B -m training.flood_ner.context_run_v38 --grant .\backend\training\flood_ner\artifacts\context-association-fixed-links-20261019-v38\execution-grant.json --sha256 e9384d69b016550cf30a6c69547f6141e21140c509d321423f1a744dfc4b7f69
```

Require `verified_read_only`, `records: 262`, `training_started: false` and `application_connected: false`. Verification does not execute extraction or clear readiness. The single-use claim is consumed and the container stopped. Do not add `--execute`, remove claims/locks, reuse destinations or execute archived authoring helpers. A Git pull does not transfer ignored private packages.

## Evidence

- `context-association-fixed-links-20261019-v38` retains initial/final fictional oracles and correction receipt, predecessor authentication/preservation, fixed-reference/tokenizer qualification, 1,158-test receipt, code/test hashes, raw-only request, frozen protocol and grant, scoring script and strict saved-output analysis.
- `context-association-execution-20261019-v38` retains the one 262-input Linux execution, isolation and stopped-state receipts, outputs and timing. No references, expected answers, weights, validation or holdout entered its mounts.
- Original `context-reference-review-20261019-v37` references and representation supplement remain unchanged. All 19 old errors and every remaining miss are accounted privately. All 70 earlier supported mappings and all supported v37/rules-correct links remain retained.

All 238 fictional cases pass (English 90 / Tagalog 58 / Taglish 90). These are software checks, not new corpus members or evidence of pure-Tagalog real accuracy. Three new oracle authoring mistakes were corrected before final execution freeze; drafts are preserved. No post-result tuning or retry occurred.

## Next gate

Separately assess the seven recognition-dependent links, three reference holds and language limitations before proposing a bounded read-only LANES demonstration. The current model learns six location classes; learned DEPTH/TIME is unfinished. Do not use hidden fallback, alter mentions or interpret training-subset 96.55% F1 as general accuracy.

No training, new data, validation/holdout evaluation, production integration, upload, commit or push is authorized by this receipt. The desktop can remain off.
