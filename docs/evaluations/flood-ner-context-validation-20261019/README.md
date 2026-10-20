# Frozen context-safeguard validation comparison

> **Last Updated:** October 19, 2026, 11:44 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The shadow method improves validation F1 from 71.60% to 76.54%, but does not qualify under the predeclared zero-new-strict-FP gate.** Keep v19 corrected control, seed 0 primary. No production integration or model-selection change occurred.

## Frozen scope

Exactly one comparison applied the unchanged `named_asset` and `shared_identifier` rules jointly to saved v19 control seed-0 predictions for **60 validation passages: 38 English / 22 Taglish, 85 reference spans**. The protocol, acceptance criteria, implementation and passing test hashes were bound before validation predictions were processed. No other rule combinations, ablations, revised rules or second comparison were tried.

The coordinator authenticated the qualified development container and projected validation-only views. The worker received raw text, opaque IDs and original predictions through the decision function; references, language and opaque group metadata remained separate scoring inputs. Training records were not emitted into the comparison view. No neural model was loaded, no inference or optimizer updates ran, and the completed research holdout stayed excluded.

## Measured result

| Validation metric | Unchanged control | Frozen shadow method |
|---|---:|---:|
| Strict TP / FP / FN | 58 / 19 / 27 | 62 / 15 / 23 |
| Precision | 75.32% | 80.52% |
| Recall | 68.24% | 72.94% |
| Micro F1 | 71.60% | 76.54% |
| Supported-label macro F1 | 68.46% | 74.63% |
| English F1, 50 reference spans | 69.47% | 77.89% |
| Taglish F1, 35 reference spans | 74.63% | 74.63% |
| Negative passages with false positives | 0 / 27 | 0 / 27 |

The original metrics reproduce exactly in counts and within 1e-12 for floating values. Overall shadow F1 increases by **4.94 percentage points**. This is a postprocessing result on reused validation data, not a newly trained neural model or independent evidence of generalization.

| Label | Reference spans | Control F1 | Shadow F1 |
|---|---:|---:|---:|
| BARANGAY | 19 | 74.29% | 77.78% |
| CITY | 23 | 85.11% | 86.96% |
| LANDMARK | 7 | 58.82% | 71.43% |
| LOCAL_AREA | 12 | 58.82% | 66.67% |
| PROVINCE | 10 | 85.71% | 85.71% |
| ROAD | 14 | 48.00% | 59.26% |

All supported class/language F1 slices are preserved or improved. Taglish ROAD has zero reference support and remains **unmeasured**, not zero F1; Taglish LANDMARK has only one reference span. Negative supports are 17 English and 10 Taglish, with zero false-positive passages before and after. [Full precision/recall/F1 and supports](metrics.json).

## Why the frozen gate fails

Five spans are retagged across **three passages in three of twenty connected groups**; the other 57 passages keep their predictions. There are no drops, new entities, resized boundaries or text edits.

| Strict transition | Count |
|---|---:|
| Gained correct entities | 4 |
| Lost correct entities / introduced FN | 0 |
| Resolved typed false positives | 5 |
| Introduced typed false positives | 1 |
| Persistent TP / FP / FN | 58 / 14 / 23 |

Four retags become exact correct typed spans. The remaining retag changes a previously incorrect LANDMARK prediction to ROAD, but the original span omits the beginning of a compound road name. The type-only safeguard cannot extend that boundary. It was a false positive before and remains a false positive afterward; **its exact typed-span identity changes**, so strict transition accounting records one resolved LANDMARK FP and one introduced ROAD FP. No previously correct entity is lost and no new textual entity is added.

This distinction matters: total FP falls from 19 to 15, yet the prospectively frozen policy forbids **any newly introduced strict typed FP**, including replacing one wrong typed span with a different wrong typed span. We do not loosen that criterion after seeing results, repair the boundary, change the annotation or try a reduced rule subset.

| Frozen acceptance check | Outcome |
|---|---|
| Overall strict micro F1 improves beyond 1e-12 | Pass |
| Zero introduced strict FP | **Fail: one** |
| Zero introduced strict FN | Pass |
| Supported class/language F1 does not decline | Pass |
| Negative-passage error counts do not increase | Pass |
| Eligible for a later integration proposal under this protocol | **No** |

`named_asset` matches ten predicted spans, makes three retags and abstains on three. `shared_identifier` matches two spans and retags both. These are joint-run diagnostics, not separate ablation results. The changed groups contribute two gained TPs; one gained TP plus the introduced FP; and one gained TP, respectively. Grouping remains conservative reporting relationships, not a claim of independent physical incidents. The small, concentrated result cannot establish robust performance. [Aggregate transitions, groups and decision](summary.json).

## Verification and preservation

**250 fresh focused tests pass, including 52 new validation-helper checks.** Constructed checks cover Unicode/repeated spans, strict transition reconciliation, ties, compensating harm, unsupported slices, missing references, source/language/group mismatches, stale hashes, altered rule subsets, occupied destinations, concurrency and blocked neural/network/training execution. All 48 frozen fictional core cases also pass preflight; no private passages appear in public tests.

The live comparison consumed one persistent attempt claim. Failure would preserve its evidence and prohibit automatic retry; no live failure or retry occurred. There was **one evaluation and no replay**. All sixty records have a comparison disposition: 57 original predictions preserved, two changed without a new strict error, and one changed with the introduced typed FP. Three complete saved articles and their changed passages were reviewed afterward to explain the result; no rules or references were changed.

**505 protected file hashes** and **55 stat-only completed-holdout entries** remain unchanged. The new worker checks only its scoped view and code bindings; broader preservation checks run separately without exposing completed-holdout content. Existing datasets, exports, tokenizer, models, historical scores and the training-study artifacts remain unchanged. Individual texts, identities, annotations and decisions remain in ignored private versioned packages. [Verification and reproducible hash bindings](verification.json).

## Completion

The bounded experiment is complete with a **does-not-qualify** outcome. Retain v19 control and keep the prototype separate from production. Any future method or revised acceptance policy requires a separately defined task; this result authorizes neither another rule search nor automatic training or integration.

Rule development was motivated by exposed validation findings. References remain **AI-assisted silver**, with reused-validation, limited-support and incomplete-history/accounting limitations. No unbiased, human-gold, certified-fresh or production-readiness claim follows. No collection, new passages, annotation/partition changes, neural inference, retraining, holdout evaluation, integration, upload, commit or push occurred. The desktop can remain off. [Operator guide](../../guides/ner-context-safeguard-validation.md).
