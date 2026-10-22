# Development error audit using existing NER data

> **Last Updated:** October 18, 2026, 5:27 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The three saved models reproduce their desktop validation scores on CPU. A large training/validation gap and a specific annotation-boundary inconsistency are demonstrated; no remaining training-code defect is demonstrated.** This is an audit and proposals task. The admitted dataset stays **345 training / 60 validation**, and the separate **60-passage research holdout stays unopened**. No new article, passage, optimizer update or training run was produced.

## Reproduced measurements

All 405 development records were scored with each of the three selected checkpoints: **1,215 prediction records**. The qualified Python 3.11.17/spaCy 3.7.5 CPU worker loaded saved weights, without initialization or training. It relocated only resource paths in memory/private metadata, verified all model/export/request hashes, exact source references, record/language joins, tokenization and serialized tokenizer identity. The three original checkpoints, source captures, references and frozen training helpers remain unchanged.

| Seed | Training micro F1 | Validation micro F1 | Validation supported-label macro F1 |
|---|---:|---:|---:|
| 0 (primary) | 99.40% | 66.67% | 64.45% |
| 1 | 89.88% | 65.41% | 64.99% |
| 2 | 98.51% | 67.46% | 66.56% |

The CPU validation F1/precision/recall reproduce the recorded desktop metrics within 1e-8. Strict scoring agrees with spaCy's entity scorer. Seed 0 remains primary; seed 2's slightly higher development score does not change the selection contract. Scores against fitted training examples measure fit, not unseen-article performance.

Seed 0 has **835 TP / 5 FP / 5 FN** on 840 training reference spans, versus **56 TP / 27 FP / 29 FN** on 85 validation spans. The 32.74-percentage-point F1 gap is consistent with overfitting and differences between examples; it does not establish a single causal explanation. Simply increasing the 1000-step limit is not supported as the first fix. Seed 1's selected 560-step checkpoint has a smaller training score but similar development performance; seeds 0/2 hit the configured maximum, while seed 1 stopped normally under patience 175.

| Seed 0 label | Validation references | TP | FP | FN | F1 |
|---|---:|---:|---:|---:|---:|
| BARANGAY | 19 | 11 | 5 | 8 | 62.86% |
| CITY | 23 | 19 | 10 | 4 | 73.08% |
| LANDMARK | 7 | 2 | 4 | 5 | 30.77% |
| LOCAL_AREA | 12 | 8 | 0 | 4 | 80.00% |
| PROVINCE | 10 | 9 | 1 | 1 | 90.00% |
| ROAD | 14 | 7 | 7 | 7 | 50.00% |

Validation contains **33 positive and 27 complete empty-location passages**, from 25 article groups. Seed 0 produces false positives on 2/27 negatives. English validation F1 is 68.04%; Taglish 64.79%. The language slices contain 50 and 35 reference entities respectively. Validation Taglish ROAD has zero reference support and LANDMARK only one reference; neither an overall score nor a tiny slice establishes bilingual class readiness. Training LOCAL_AREA support is 19 entities in 16 passages/14 captured articles.

## Source-bound review and proposals

All 60 validation passages/references received one completed AI-assisted review disposition. **59 retain their references; one retains its frozen scored reference with an unresolved landmark-boundary question for independent adjudication.** No validation member was removed, no validation label changed, and all 60 remain in the measured partition. The question concerns whether a generic facility qualifier belongs within a named landmark span; model agreement is not the deciding evidence.

Across seeds, 27 validation passages have a strict error. Full captured texts were read for 20 associated sources. An additional 54 training passages received focused review for related boundaries, list context, schools, roads, repeated names and LOCAL_AREA patterns; the remaining 291 training passages received mechanical/reference checks and scoring, not a new semantic re-audit. Seven training captured sources were also read in full, for **27 captured source contexts** in total. Root-cause interpretations remain AI-assisted silver.

**Nine training passages contain 12 proposed boundary corrections:** ten CITY and two PROVINCE occurrences omit explicit source designators included by the current conventions and later admitted examples. Proposed spans preserve source text, type, entity IDs, record count and grouping. All nine proposed references pass the shared schema, source-exact Unicode offsets, non-overlap and frozen-tokenizer checks. They remain draft proposals outside membership and have not been used to rescore any model. No validation correction is asserted merely to agree with predictions.

The private ledgers bind each disposition/proposal to record/source hashes, offsets, original annotations, source evidence and the existing convention document. No passage, source URL, individual annotation or candidate identity is published here. Overlap diagnostics distinguish wrong type, boundary and combined errors; links can be many-to-many and never change strict TP/FP/FN counts. Unsupported labels have null F1 and explicit support counts; macro F1 averages only labels with reference support.

## Verification and next task

New offline audit helpers leave historical fixed-400/successor training and export helpers unchanged. They authenticate the 72-member checkpoint payload plus embedded manifest, extract only 33 selected-model files into a new private destination, reject stale bindings/holdout inputs/duplicate identities/group fragmentation, and use a single-writer lock. Failures preserve logs; existing destinations are rejected.

Fresh affected-suite verification: **209 tests and 35 subtests pass**, including 53 new audit tests. Six suites cover the audit, shared evaluation, checkpoint preparation, tokenizer, annotation tooling and repository checkout bytes; one existing Click deprecation warning remains. Initial constructed checks caught a Windows lock-handle cleanup issue in the new audit helper; it was fixed before the completed runs. Run 01 and its helper bytes remain preserved; run02 uses final helper bindings and reproduces identical predictions, errors and metrics. Historical desktop 75-test results remain separate.

**Recommended next task:** select/admit a separate correction revision for the existing records, resolve or explicitly retain the validation-boundary question, then define a bounded experiment comparing the unchanged recipe/control with one-factor regularization candidates. Proposed settings for later consideration are dropout 0.2 versus 0.1 and learning rate 0.0005 versus 0.001; none was applied or trained. Preserve partitions and compare every model against the same reference revision. Keep the holdout isolated during tuning. No new collection or synthetic/new passages are requested; coverage limits remain explicit.

This audit does not establish human gold, certified freshness, heldout improvement or a guaranteed 80% F1 result. Existing limited-provenance research terms remain unchanged. No replacement export, admission, partition change, heldout inference, training, upload, commit or push occurred. The desktop can remain off. [Machine-readable aggregates](verification.json) · [Operator guide](../../guides/ner-development-error-audit.md).
