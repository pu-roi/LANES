# LANES completed validation study — October 16, 2026

> **Last Updated:** October 16, 2026, 7:49 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The authorized seed 2 recovery and all four bounded trial runs completed. Recipe A wins the preregistered seed 0 comparison: **71.81**, versus **70.70** for B and **67.15** for the original. A receives the permitted robustness seeds 1/2; B does not. All selected scores reproduce after model reload on the same **60 development passages**. Original seed 0 remains the primary frozen result. No held-out test predictions or metrics were produced.

## Completed runs and selection

| Run | Selected step | Validation F1 | Final step |
|---|---:|---:|---:|
| Original seed 0 | 455 | 67.15 | 630 |
| Original seed 1 | 700 | 70.59 | 875 |
| Original seed 2 (recovered) | 840 | 72.29 | 1000 |
| Recipe A seed 0 | 875 | 71.81 | 1000 |
| Recipe A seed 1 | 945 | 73.61 | 1000 |
| Recipe A seed 2 | 630 | 72.41 | 980 |
| Recipe B seed 0 | 910 | 70.70 | 1000 |

Original family mean F1 is **70.01**, sample standard deviation **2.62 percentage points**; Recipe A mean is **72.61**, sample standard deviation **0.92 points**. These three-seed descriptive summaries are not significance tests. Seed 0 determines the recipe winner; a higher-scoring robustness seed never replaces the primary seed.

Selection uses unrounded strict six-class development F1; original wins equal scores, then A precedes B. Earlier checkpoints win within-run ties. Use **selected-checkpoint/model**, whose saved selection record enforces that rule; built-in model-best is diagnostic. The final step comes from model-last metadata, not the last displayed evaluation row. Recipe A seed 2 stops at step 980, exactly 350 steps after its best step 630; the other four new runs reach max_steps 1000. All new runs start before the session's 20:09:22 cutoff.

## Validation comparisons

| System | Six-class P | Six-class R | Six-class F1 | TP/FP/FN | Coarse LOC F1 |
|---|---:|---:|---:|---|---:|
| A-0 | 72.33 | 71.29 | 71.81 | 149/57/60 | 86.75 |
| A-1 | 74.51 | 72.73 | 73.61 | 152/52/57 | 86.20 |
| A-2 | 74.62 | 70.33 | 72.41 | 147/50/62 | 84.73 |
| B-0 | 71.57 | 69.86 | 70.70 | 146/58/63 | 84.26 |
| native | — | — | — | — | 68.83 |
| original-0 | 68.32 | 66.03 | 67.15 | 138/64/71 | 79.81 |
| original-1 | 72.36 | 68.90 | 70.59 | 144/55/65 | 82.84 |
| original-2 | 72.82 | 71.77 | 72.29 | 150/56/59 | 84.34 |
| rules | 84.13 | 50.72 | 63.28 | 106/20/103 | 63.88 |

Full exact/coarse metrics, TP/FP/FN, per-class, English/Taglish, language-class slices and negative support are in [metrics.json](metrics.json). Native pretrained LOC is a separate collapsed location task; it cannot be treated as six-class performance. Native ORG/PER remain diagnostics. Collapsing classes never merges adjacent spans.

The frozen rules mention component cannot emit **LOCAL_AREA**; its unavailable output remains explicit. No reference-driven relabeling or offset repair is applied. The validation set has 30 English / 30 Taglish passages and 209 location spans. Its six negative passages are all Taglish; English negative rate is **null** because support is zero. All nine systems produce zero false-positive passages on these six negatives. This small supported subset does not establish general specificity.

Inference receives raw passage strings. Reference entities are used for scoring and DocBin identity checks, never as model inputs. All scores measure agreement with **same-AI silver references**, not independent human gold accuracy. Forty contextual pairs remain training references, not a held-out contextual benchmark. Same-seed GPU training byte determinism is not established; this small exploratory study does not isolate a causal effect of patience or establish generalization.

## Configurations, failure history and GPU evidence

Recovery preserves original patience 175 / learning rate 0.001, changing only output relocation. Recipe A uses patience 350 / rate 0.001; B uses patience 350 / rate 0.0005. Each run starts independently with the pinned NER encoder and a fresh six-class head. Batch 8, dropout 0.1, evaluation frequency 35, max_epochs 30 and max_steps 1000 remain frozen. All seven variant configurations were hash-bound before any trial; unused B seeds 1/2 are configurations only. The [study manifest](study-manifest.json)'s training_started:false is its immutable preregistration-time field; actual completion is in [run-summary.json](run-summary.json).

The first seed 2 attempt failed on redirected cp1252 console output. Its original failed folder, logs and prior partial report remain unchanged. The researcher explicitly authorized one fresh retry and renewed the hour. UTF-8 configuration now applies to both launcher entry paths; cp1252 regression and real redirected subprocess transport tests pass. The one authorized recovery succeeds. Optimizer updates in the original failed worker remain unestablished.

Five-second nvidia-smi samples are available for all five new runs; [run-summary.json](run-summary.json) records observed GPU-wide utilization, memory and timestamps. They show activity during training, but do not attribute all device load to one process or establish earlier manual-run utilization. Logs and model weights stay in ignored private artifacts.

## Verification and preservation

**43 focused unittest methods pass** (10 launcher, 9 preparation, 12 export regressions, 8 comparison, 4 recipe). Coverage includes exact matching, Unicode offsets, negatives/undefined metrics, coarse LOC separation, raw-text inference, ties, changed inputs, invalid identities and overwrite refusal. No dependency installation or full historical suite rerun is claimed.

All **10,945 prior artifact files**, **23 pinned model files**, **22,759 research-environment file stats** and **109 CLI package versions** verify unchanged, as do requirements and .env. The environment audit checks size/mtime with bytecode excluded; it is not full environment content hashing. Original seeds 0/1, failed seed 2, historical checkpoints/forms/proposals, corpus annotations, source-use flags, tokenizer, partitions and context bindings remain unchanged. Corpus totals remain **400 samples / 138 articles / 40 pairs / 1,465 spans / 48 negatives**, **200 English / 200 Taglish**, **280/60/60 train/dev/test**.

The four new comparison requests repeat the same 60 development passages: **240 private passage representations**, including **20** representations where the selected passage equals the full original source body (5 per request). They add no articles or samples. Prediction files contain offsets/labels; public files contain metadata only.

Historical acquisition/use and predecessor limitations are retained: two historical references currently match their hashes without formal reconciliation; the IPOPHL historical reference still differs. The 11 invalid-fixture references and 10 copied-manifest aliases remain separately classified. This study supplies no new permission, legal conclusion, independent annotation review or production qualification.

[Verification](verification.json), [preservation](preservation.json), [output hashes](output-hashes.json), [run status/configuration/telemetry](run-summary.json). Original private execution evidence is in validation-study-execution-20261016-v2; weights remain under validation-study-20261016-v2/runs.

## Next task

Freeze the final experiment/checkpoint decision using these development results, retaining original seed 0 as primary and labeling Recipe A exploratory. Then perform the **separate held-out test evaluation** under the unchanged protocol; do not tune against test predictions. Production integration/acceptance, distribution decisions and deployment remain later gates.

No held-out test predictions, export, dependency/API/schema changes, deployment, external correspondence, commit, push or shutdown occurred. Planned work finished early within the renewed hour.

[Task plan](../../task_plan.md); [training plan](../../plans/lanes-ner-training-plan.md); [earlier partial report](../flood-ner-validation-study-20261016/README.md).
