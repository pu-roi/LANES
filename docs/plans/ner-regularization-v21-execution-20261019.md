# Regularization v21: conditional three-seed execution plan

> **Last Updated:** October 19, 2026, 1:28 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Status: completed after one successful run; the overall screening gate failed.** Candidate seed-0 F1 69.7143% trails control 71.6049%; ROAD/LOCAL_AREA improve. Seeds 1/2 were not run, and corrected control seed 0 remains primary. The new controller/scorer pass 291 tests and fresh GPU/schema verification; all 8,047 preservation checks pass. [Final execution evidence](../evaluations/flood-ner-regularization-v21-execution-20261019/README.md). The plan below preserves the fixed protocol and implementation design; the earlier [desktop verification](../evaluations/flood-ner-regularization-desktop-verification-20261019/README.md) is readiness history.

## Fixed inputs and boundaries

- Checkout: `roi-branch`, inspected at `4875cef4f03ecc4fdc2b3b0ff9d7e7bc43f36bad`; preserve all local changes, `.env`, backups, packages and historical results. No commit, push or deployment.
- Verified experiment: `backend/training/flood_ner/artifacts/regularization-desktop-20261018-v21`, exactly 20 files, including a twelve-file trainer package. Experiment manifest SHA-256: `35050682217749d945a3c5fecbe5d3771212b1df1276f9f5f95bad4c7d6a0e78`.
- Baseline: the three existing corrected v19 control runs, authenticated through the delivered `baseline-metrics.json`. Do not retrain control or substitute historical v16 scores.
- Existing interpreter: `backend/training/flood_ner/artifacts/gpu-qualification-20261015/research-env/Scripts/python.exe`.
- Existing pinned model: `backend/training/flood_ner/artifacts/gpu-qualification-20261015/model`, all 23 files at revision `51a40433059d8a2c25b98a48eca854f8789a491a`. No installation or replacement.
- Fixed 345 training / 60 validation membership, annotations, tokenizer and group assignment. No new articles, annotation edits, corpus regeneration or holdout access/evaluation.
- Candidate: L2 = 0.05 and `L2_is_weight_decay = true`. Keep batch size 8, dropout 0.1, learning rate 0.001, maximum 30 epochs/1,000 steps, evaluation every 35 steps and patience 175. Use the delivered seed-specific configs without edits.
- Every run starts from the pinned encoder with a fresh six-label head. Do not resume or initialize from a selected v19 checkpoint.

## Exact comparison rules

Values below come from the authenticated baseline; displayed percentages are rounded. Use full-precision strict entity F1 and the existing pure scheduler in `regularization_experiment.py`, with epsilon `1e-12` on the 0–1 scale.

| Control comparator | Overall F1 | ROAD F1 | LOCAL_AREA F1 |
|---|---:|---:|---:|
| Seed 0 | 71.60493827% | 48.00000000% | 58.82352941% |
| Seed 1 | 71.51515152% | 69.56521739% | 70.00000000% |
| Seed 2 | 66.27218935% | 33.33333333% | 63.15789474% |
| Arithmetic three-seed mean | 69.79742638% | 50.29951691% | 63.99380805% |

Validation ROAD support is 14 reference entities and LOCAL_AREA support is 12 for every seed. Preserve support counts; unsupported label/language slices remain unmeasured.

1. Train candidate seed 0 and validate its selected checkpoint.
2. Continue only if candidate seed-0 overall F1 exceeds control seed 0 by more than `1e-12`, and candidate ROAD and LOCAL_AREA F1 each differ from control seed 0 by at least `-1e-12`. An overall tie fails; a protected-label tie passes.
3. If screening fails, stop after one new run and retain corrected v19 control seed 0 as primary.
4. If screening passes, run candidate seed 1, then seed 2, sequentially. Seed 1 must complete and validate before seed 2 can begin. Do not impose an additional individual-seed performance gate; final confirmation uses the frozen three-seed means.
5. Retain the candidate only if its arithmetic mean overall F1 improves over corrected control's three-seed mean by more than `1e-12`, and its mean ROAD and mean LOCAL_AREA F1 each do not regress by more than `1e-12`. Screening must also have passed. Otherwise retain v19 control.
6. The retained family's seed 0 remains primary. Do not choose the best seed, ensemble, pool seed predictions or select models using holdout results.

## Implementation work before the first training run

Add a separate internal `regularization_experiment_execution.py`, development scoring worker and focused tests. The current v19 controller hardcodes its older five/seven-run family schedule, and its basic checkpoint worker does not return the full language/negative metric structure expected by the v21 scheduler. Do not dispatch the old controller or alter manifest-bound helpers to accommodate this experiment.

The new controller will reuse the existing v21 scheduler and unchanged successor launcher, along with validated checkpoint loading, raw-text inference and strict scoring helpers. It will:

- Authenticate inputs, baseline, implementation and test bindings before dispatch; preserve original package manifests and record this task's training authorization separately outside the frozen package.
- Admit only seeds 0, 1 and 2, in order, once each, under an exclusive experiment attempt and active lock. Reject concurrent execution, occupied destinations, unexpected outcomes and repeat attempts.
- Keep a durable record of each dispatched seed before starting it, so interruption cannot silently create a fourth run or authorize a retry. Never retry automatically or manually remove an active lock.
- Call `successor_training.py --start-training` with the delivered package, explicit seed, existing interpreter/model and an absent output directory. Keep `-I -B` isolation and the existing Windows runtime initialization.
- Preserve launcher stdout/stderr, raw training logs, resolved configs, selected/last checkpoints and per-run outcomes. Verify completed runs before recording scheduler outcomes.
- Stop on any launcher, checkpoint-loading, scoring, provenance or preservation failure. Preserve partial outputs and failure diagnostics; retain control if confirmation is incomplete.

The development worker will load the selected checkpoint on CPU using the existing qualified environment, confirm exactly the six expected labels and frozen tokenizer, and score raw text from the delivered training/validation DocBins. Join the authenticated `development-slices.json` by exact record ID, partition and text SHA-256 for language/group/negative metadata. Require exact 345/60 membership and the frozen language counts; never infer a language or substitute a holdout input. References stay in validation/scoring, outside model inference.

Return complete strict precision/recall/F1 and TP/FP/FN/support tables overall, by language, by label and language-by-label, plus negative-passage false positives, supported-label summaries and training/validation gaps. Use the existing `score_partition` semantics required by the scheduler. Training-set scoring is diagnostic and cannot select the checkpoint or family.

## Execution and evidence layout

Before execution, snapshot local state and relevant hashes privately, authenticate all package/baseline/source files, confirm the 23 pinned model files, and repeat actual read-only GPU/schema verification. Require the same four passing flags as the prior desktop receipt. Refuse missing resources, changed bindings or existing locks.

Create a new owner-only experiment root, refusing an existing destination:

`backend/training/flood_ner/artifacts/regularization-v21-experiment-20261019-v1`

Keep authorization, preservation ledgers, controller/worker identities and test evidence at that root. Run destinations will be:

1. `runs/stronger-weight-decay-seed-0`
2. `runs/stronger-weight-decay-seed-1` — only after seed-0 screening passes.
3. `runs/stronger-weight-decay-seed-2` — only after seed 1 completes and validates.

Each successful run requires a zero launcher/training exit, finite development metrics, valid `selection.json`, a loadable six-label selected checkpoint, unchanged checkpoint files during loading and independent strict development-score reproduction. Preserve the established bounded metadata-rounding check; use independently scored full-precision metrics for scheduler gates. Checkpoint selection remains development F1, with the earliest step on ties. Record only stopping reasons supported by logs and selected/last-step evidence.

## Tests and validation gates

Follow the repository testing skill. Before dispatch, run constructed tests for screening pass/failure, overall and protected-label ties at epsilon, mean regression, seed order/duplicates, maximum-three enforcement, failed-seed stopping, occupied destinations, concurrent attempts/locks and preservation of partial failures. Cover non-finite/forged metrics, wrong membership/language/text hashes, unsupported labels, missing or invalid checkpoints, tokenizer mismatches, metadata rounding, raw-text reference separation and portable CPU loading. Verify that a failure after dispatch prevents automatic continuation/retry.

Run new tests plus the applicable existing regularization, successor preparation and Windows runtime suites using the qualified interpreter, `--noconftest`, no shared pytest cache and a new private temporary directory. Keep constructed tests separate from real training and preserve their exact command/output. Previously passing 248 tests are readiness history, not a substitute for these new checks.

## Completion

Report every attempted seed's status, validation precision/recall/F1, ROAD/LOCAL_AREA F1, selected step, supported stopping reason and output location. For completed three-seed families, show arithmetic means and sample standard deviations, including the protected-label mean checks, alongside the authenticated v19 control.

Freeze the retention decision, primary seed-0 checkpoint hashes and configuration/tokenizer identities. Preserve all unsuccessful candidate models as research artifacts; do not deploy. Publish metadata-only evidence under `docs/evaluations/`, index it, and synchronize task/progress/operator records. Recheck `.env`, original packages, all pinned model files, source backups and historical runs against the private pre-execution ledger.

No holdout inference or additional research comparison follows. These are reused-validation, limited-provenance AI-assisted silver results with support/history limitations. Better performance is possible, not guaranteed; no 80% or historical-score acceptance threshold is added.
