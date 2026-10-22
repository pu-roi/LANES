# LANES held-out test evaluation — October 16, 2026

> **Last Updated:** October 16, 2026, 8:09 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The fixed-roster held-out evaluation passes once on **60 test passages (30 English / 30 Taglish), 290 location spans and 3 negative passages**. Primary original seed 0 scores **63.12 strict six-class F1**; exploratory Recipe A seed 0 scores **67.72**. Original seed 0 remains primary; no seed or recipe is selected using these test results. No training or runtime integration occurs.

## Results

| System | Strict six-class P | R | F1 | TP / FP / FN | Separate coarse LOC F1 |
|---|---:|---:|---:|---|---:|
| original-seed-0 | 64.96 | 61.38 | 63.12 | 178 / 96 / 112 | 79.79 |
| original-seed-1 | 75.00 | 70.34 | 72.60 | 204 / 68 / 86 | 82.21 |
| original-seed-2 | 69.66 | 69.66 | 69.66 | 202 / 88 / 88 | 81.38 |
| A-seed-0 | 69.31 | 66.21 | 67.72 | 192 / 85 / 98 | 81.48 |
| A-seed-1 | 72.54 | 71.03 | 71.78 | 206 / 78 / 84 | 80.84 |
| A-seed-2 | 72.50 | 70.00 | 71.23 | 203 / 77 / 87 | 83.16 |
| rules | 77.53 | 47.59 | 58.97 | 138 / 40 / 152 | 61.54 |
| native | — | — | — | — | 67.02 |

Original three-seed mean F1 is **68.46**, sample SD **4.85 percentage points**, range **63.12–72.60**. Recipe A mean is **70.24**, sample SD **2.20 points**, range **67.72–71.78**. Three seeds are descriptive evidence, not a significance test. Original seed 1 scores highest among the evaluated runs, but is not promoted.

All model choices and checkpoints were fixed before inference: original seed 0/1 at steps 455/700; recovered original seed 2 at 840; A seeds 0/1/2 at 875/945/630. Use selected-checkpoint/model, preserving the development earlier-step rule. Recipe B and built-in model-best are excluded. The freeze is **498b0db49690c8bd7ca0dacde5902759e30e9052b8438b4fc9f1b99af4db6243**, recorded at 2026-10-16T20:05:03.948809+08:00; inference starts at 2026-10-16T20:06:12.469091+08:00.

Native pretrained NER scores only native LOC predictions against the separate collapsed location references. Its **67.02 coarse LOC F1 cannot be compared as six-class performance**. ORG/PER remain diagnostics (35/30). All six reference classes collapse without joining adjacent entities. The frozen mention-rules baseline cannot emit LOCAL_AREA; its precision for that class remains null rather than invented. Rule diagnostics: 0.

Full precision/recall/F1, counts, per-class, language and language-class slices, negatives and family statistics are in [metrics.json](metrics.json). Scores measure **same-AI silver-reference agreement**, not independently verified accuracy.

## Measured limitations and next task

| Slice | Reference spans | Original seed 0 F1 | Recipe A seed 0 F1 |
|---|---:|---:|---:|
| BARANGAY | 31 | 64.41 | 69.44 |
| CITY | 73 | 77.78 | 80.52 |
| LANDMARK | 20 | 0.00 | 36.84 |
| LOCAL_AREA | 22 | 36.36 | 43.75 |
| PROVINCE | 75 | 82.86 | 80.29 |
| ROAD | 69 | 43.24 | 53.73 |
| english (30 passages) | 178 | 58.89 | 60.23 |
| taglish (30 passages) | 112 | 69.68 | 79.11 |

LANDMARK, LOCAL_AREA and ROAD remain weak, especially for the primary model; English F1 also trails Taglish. Recipe A's seed 0 test F1 is lower than its 71.81 development F1, and both families show variability. Improvement in this fixed comparison does not qualify a production model or establish field accuracy. Report original primary and exploratory results together without selecting another seed.

| System | False-positive negative passages / support |
|---|---:|
| original-seed-0 | 1 / 3 |
| original-seed-1 | 1 / 3 |
| original-seed-2 | 0 / 3 |
| A-seed-0 | 0 / 3 |
| A-seed-1 | 2 / 3 |
| A-seed-2 | 2 / 3 |
| rules | 0 / 3 |
| native | 3 / 3 |

Negative support is only **2 English / 1 Taglish** passages. These counts cannot establish a general false-activation rate or full flood-claim specificity; the rules comparison covers mentions, not the complete pipeline. Undefined metrics are kept as null. The 40 contextual pairs remain training references, not held-out place/depth/time/status association evidence.

The next task is the existing **Gate 3 model-qualification review**, using the saved private offset errors to document weak slices and readiness before **Gate 4 isolated integration**. No annotation correction or retraining is performed here. Future model tuning requires a fresh untouched holdout; these results are now exposed and cannot remain a selection-independent test for another tuning round. Independently verified accuracy claims require independent reference review. Full flood-fact association, isolated RSS-to-map acceptance, Linux/resource qualification, operational diagnostics, distribution/use dispositions and deployment remain separate gates.

## Execution, verification and preservation

A separate freeze command locks six model identities, development selections, configurations, input/contract/model/tokenizer bindings, rules assets, evaluator sources and exact test memberships. It produces no predictions. The evaluation command then uses the existing isolated Python 3.11 GPU runtime. Inference receives raw strings; gold entities/Docs are used only for identity checks and scoring. Worker inputs contain test locations only, excluding training/dev/context/control records.

An exclusive attempt marker is created before any rules/neural test inference and remains after success or failure. There is **one actual test evaluation attempt**, with all eight systems complete. The freeze manifest and seal remain unchanged. Repeated execution against that freeze or an existing output is refused.

Before the freeze, a preparation-only check exposed a constructed-control record_id filtering error. No freeze directory or test predictions were created. The filter was repaired, the original diagnostics preserved and a regression added. All **59 stdlib unittest methods** then passed **before inference** (43 prior regressions + 16 held-out tests). This is not a test-inference retry. Coverage includes roster/recovery resolution, changed hashes, split/identity guards, Unicode, raw strings, exact/coarse separation, nulls, negatives, existing-output and exclusive-attempt refusal, and retained failure diagnostics. No full historical suite rerun is claimed.

Independent reconstruction verifies **240 metric slices** from saved predictions; all seven six-class systems also match the original frozen scorer. Error-file FP/FN totals reconcile. Every system has the identical 60 record identities. [Reconciliation](reconciliation.json).

All **11,625 prior artifact files**, **23 pinned model files**, **22,759 research-environment file stats**, **109 CLI package versions**, requirements and .env remain unchanged. Research-environment checks use size/mtime with bytecode excluded, not full environment content hashing. Frozen corpus totals remain **400 samples / 138 articles / 40 contexts / 1,465 spans / 48 negatives; 200/200 languages; 280/60/60 partitions**. Original/failed/recovered training runs, source-use flags, annotations, historical forms and validation reports are preserved.

The new private request contains **60 selected test passage strings**, **2** of which equal the original complete source body. It adds no articles or samples. Predictions/error files contain IDs and offsets/labels, with no article bodies. Public files contain metadata only; no passage quotation is included.

Historical evidence gaps remain unchanged: two restored references now match without formal reconciliation, the IPOPHL historical reference remains hash-divergent, and the detailed desktop predecessor is unreconciled. Eleven invalid-fixture references and ten copied-manifest aliases remain separately classified. No new permission or source-use conclusion is supplied.

[Freeze manifest](freeze-manifest.json), [verification](verification.json), [preservation](preservation.json), [output hashes](output-hashes.json). Private results: heldout-test-evaluation-20261016-v1; freeze/marker: final-test-freeze-20261016-v1; logs/audits: heldout-test-execution-20261016-v1, all under ignored research artifacts.

No training, annotation/source-use changes, dependency/API/schema changes, deployment, external correspondence, commit, push or shutdown occurred. [Task plan](../../task_plan.md); [training plan](../../plans/lanes-ner-training-plan.md); [development study](../flood-ner-validation-study-20261016-v2/README.md).
