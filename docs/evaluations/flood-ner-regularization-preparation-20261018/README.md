# Existing-data weight-decay experiment: preparation complete

> **Last Updated:** October 18, 2026, 10:31 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

One new **twelve-file trainer package** is qualified locally for the unchanged **345 training / 60 validation** development dataset. Seed 0/1/2 configs change only optimizer `L2` from **0.01 to 0.05**, retaining `L2_is_weight_decay = true`. No inference, training, new data, annotation/partition change, research-holdout content access, upload, commit or push occurred.

**Next:** separately publish the code and privately deliver the experiment bundle, then verify its actual desktop GPU environment. Training is a later explicit execution task. This report measures preparation correctness, not improved model performance.

## Fixed experimental hypothesis

The development diagnosis measured v19 seed 0 training F1 of 98.09% versus 71.60% validation. Higher dropout and lower learning rate already failed the previous screening. This single trial tests stronger decoupled weight decay with all remaining training settings unchanged; 0.05 is a predeclared experimental value, not a proven optimum. The installed optimizer matches the [Thinc optimizer documentation](https://thinc.ai/docs/api-optimizers/): `L2_is_weight_decay` interprets `L2` as an AdamW-style decay term. No gain or 80% score is promised.

The declared recipe remains dropout 0.1, learning rate 0.001, batch 8, maximum 1,000 steps/30 epochs, patience 175 and evaluation every 35 steps. Initialization remains a fresh six-class head with the pinned pretrained NER encoder, vocabulary and frozen tokenizer; existing trained checkpoints are not resumed.

## Actual CPU qualification

Python **3.11.17 / spaCy 3.7.5** qualifies all 405 records and all three complete configurations. Registry resolution constructs uninitialized model graphs and an unused optimizer; it does not initialize a Language pipeline, load trained neural weights, invoke predictions or perform updates. Explicit guards block pipeline initialization/inference/update methods and outbound network/process operations. The resolved optimizers each report `L2 = 0.05`, weight-decay mode true and zero update entries.

| Invariant | Result |
|---|---|
| Membership | 345 train / 60 validation, unchanged |
| Languages | Train 170 English / 175 Taglish; validation 38 English / 22 Taglish |
| Location references | 840 train spans / 85 validation spans |
| Exports, annotations, grouping, identities | Unchanged bytes; source-exact Unicode/schema/token alignment checked |
| Serialization/reload | Text, IDs, token signatures and entities match; DocBin bytes round-trip exactly |
| Configs | Seeds 0/1/2, sole semantic difference is `training.optimizer.L2` |
| Historical anchors | 280 preserved through identical frozen partition metadata |
| Private delivery / actual desktop GPU | Pending |
| Inference / optimizer updates / training | None / 0 / none |

A constructed regression caught that spaCy `DocBin.from_bytes` restores IDs but does not enable user-data reserialization by default. The new checker now explicitly uses the frozen serializer's `store_user_data=True` setting. All seven original failing constructed cases are retained and pass. Neither the original serializer nor any export was modified.

The trainer directory contains exactly 12 manifested files. The surrounding experiment bundle contains 20 files total: package 12, three byte-identical control templates, protocol, baseline metrics, development-only source/group/language slice metadata, aggregate CPU qualification and a bundle manifest. No article captures, full JSON annotation ledgers or research-holdout corpus/predictions are included.

## Frozen later desktop schedule

The [protocol](experiment-protocol.json) binds authenticated existing v19 control development metrics. Its primary validation F1 is **71.60493827160493%** and three-seed mean **69.79742637862296%**. Existing control runs are reusable because the dataset, initialization and all other recipe settings remain identical. V16 and completed holdout results do not select this experiment.

1. Run candidate seed 0.
2. Continue sequentially to 1/2 only if seed 0 strict validation micro F1 exceeds control by more than 1e-12 and ROAD/LOCAL_AREA F1 do not regress beyond 1e-12.
3. Retain the candidate only if its three-seed overall mean also strictly improves and both protected-label means do not regress. Otherwise retain v19 control.

There are **at most three new runs**. Overall ties do not establish improvement; key-label ties pass non-regression. An execution failure stops the sequence without retry, extra configuration or destination reuse. A failed screening stops confirmation. Pure scheduler regressions exercise these decisions without dispatching any process.

The [full-precision baseline summary](baseline-summary.json) retains exact per-seed TP/FP/FN/support and protected-label scores. Baseline ROAD/LOCAL_AREA means are **50.29951690821256% / 63.9938080495356%**. The protected ROAD criterion is measured overall; Taglish validation ROAD remains unsupported, with one Taglish LANDMARK span. Scarce LOCAL_AREA examples and the unresolved school/gymnasium validation boundary remain unchanged.

Future execution must preserve raw logs, evaluation-step curves, resolved configs, checkpoint selection/reload evidence and all label/language/negative/train-versus-validation reporting. Current preparation grants no training permission. Results from this reused validation set will be development evidence, not a new unbiased test result.

## Evidence and completion

Fresh **341 tests plus four subtests pass** across eight focused suites, including 72 new constructed checks. The same 72 new checks also pass under the actual pinned neural environment; those are runtime rechecks, not additional unique tests. One existing spaCy/Click deprecation warning remains. Earlier 269/367-test results are historical.

All **374 protected file bindings** remain unchanged. The 55 existing research-holdout file entries were checked only by size/mtime metadata; their contents were not opened. Original model/data/review/journal/score artifacts, frozen evaluator sources and the consumed one-time comparison remain preserved.

- Preparation grant SHA-256: `4469a651021461070513aa16b00c3e1a83c454282f0560271d42948d15cf1e83`
- Experiment manifest SHA-256: `35050682217749d945a3c5fecbe5d3771212b1df1276f9f5f95bad4c7d6a0e78`
- Twelve-file trainer manifest SHA-256: `aea4d8dfe7f259deb44822c93b30e8b6797b0a5da17ed21d32a2dc9bd7eed6fd`
- Training export SHA-256: `6fc6edcefef912d06d099650edd8d7589fb34b60f580ddce00fb21078aeb0415`
- Validation export SHA-256: `6b98529d3d65e1f5b5664a843220e9f19d49028b9d5edb10d86d538e60bffb02`

See [CPU evidence](cpu-qualification.json), [verification hashes](verification.json) and [operator instructions](../../guides/ner-regularization-experiment.md). Private grants, slice metadata and packages remain ignored by Git. A Git pull does not transfer them.

References remain **AI-assisted silver**, with incomplete external history/acquisition records and no certified-fresh or human-gold claim. Public APIs, dependencies, database schemas and application behavior are unchanged. The laptop task is complete; private delivery, desktop receipt/GPU verification and actual experiment execution remain separate. The desktop can remain off for now.
