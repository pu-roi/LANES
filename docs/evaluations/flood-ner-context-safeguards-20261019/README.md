# Training-only context-safeguard feasibility

> **Last Updated:** October 19, 2026, 11:09 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Two frozen text rules qualify for a later validation proposal; no validation comparison or integration ran.** The unchanged v19 corrected control seed-0 predictions on 345 training passages were studied with separate references. V19 control remains retained. This is a separate offline shadow method, not a model update.

## Measured scope and result

The coordinator authenticated the qualified development container and deterministically projected **345 training records: 170 English and 175 Taglish**. The study worker received only unchanged text, opaque IDs and predictions through the decision interface; references and language metadata were separate scoring inputs. No validation record was emitted into the study view. The completed holdout was excluded from content reads and scoring.

Rules, 48 fictional core cases, implementation/test hashes and the qualification policy were frozen before the empirical rule study. This work was **motivated by already exposed validation findings**. It is not blinded discovery, independent evaluation or evidence of improved generalization.

| Training metric | Saved control | Eligible shadow subset |
|---|---:|---:|
| Strict TP / FP / FN | 821 / 13 / 19 | 824 / 10 / 16 |
| Precision | 98.44% | 98.80% |
| Recall | 97.74% | 98.10% |
| Micro F1 | 98.09% | 98.45% |
| Supported-label macro F1 | 97.25% | 98.10% |
| English F1, 525 reference spans | 97.99% | 98.37% |
| Taglish F1, 315 reference spans | 98.25% | 98.57% |
| Negative passages with false positives | 0 / 103 | 0 / 103 |

There are **three retags in three passages**, zero drops and zero additions. Two LANDMARK predictions become ROAD using integral road suffixes. One ROAD prediction becomes LOCAL_AREA using an explicit contiguous shared identifier. Boundaries and text remain identical. Three typed false positives are resolved and three correct entities gained, with **zero introduced strict FP or FN**. All other 342 passages retain their original predictions. The negative supports are 38 English and 65 Taglish; neither method emits a prediction in them.

| Training label | Reference spans | Control F1 | Shadow F1 |
|---|---:|---:|---:|
| BARANGAY | 85 | 100.00% | 100.00% |
| CITY | 308 | 99.35% | 99.35% |
| LANDMARK | 58 | 91.23% | 92.86% |
| LOCAL_AREA | 19 | 97.30% | 100.00% |
| PROVINCE | 169 | 99.12% | 99.12% |
| ROAD | 201 | 96.50% | 97.26% |

All six labels have reference support in both training languages. [Full precision/recall/F1, label/language support, negatives and per-rule metrics](metrics.json) retain unsupported-slice semantics; constructed zero-support tests verify that unmeasured F1 stays null.

## Rule dispositions

| Frozen rule | Cue matches, including abstentions | Edits | Abstentions | Gained TP / resolved FP | Introduced FP / FN | Disposition |
|---|---:|---:|---:|---:|---:|---|
| `agency_actor` | 1 | 0 | 1 | 0 / 0 | 0 / 0 | Partially supported; corrective applicability unproven |
| `attribution_role` | 0 | 0 | 0 | 0 / 0 | 0 / 0 | Partially supported; unproven |
| `named_asset` | 126 | 2 | 17 | 2 / 2 | 0 / 0 | Feasible under the training gate |
| `explicit_barangay` | 75 | 0 | 0 | 0 / 0 | 0 / 0 | Partially supported; already-correct matches only |
| `explicit_locality` | 9 | 0 | 0 | 0 / 0 | 0 / 0 | Partially supported; already-correct matches only |
| `shared_identifier` | 2 | 1 | 0 | 1 / 1 | 0 / 0 | Feasible under the training gate |

The **organization/professional-role family is partially supported**: fictional exclusions pass, but there is no observed corrective action on saved training predictions. It must not be described as an empirically successful removal rule.

The **road/facility family is feasible only within this study's gate**: both observed corrections use road suffixes. Physical-facility correction has constructed support but no observed corrective training action. Ambiguous facility-shaped names abstain. These results do not establish facility generalization.

The **administrative/locality family is partially supported**: the shared-list rule qualifies, while direct barangay/locality rules have no observed corrections. The numeric correction depends on one existing training context; broader linguistic coverage remains unproven. Multiword/incomplete antecedents, ordinary counts, conflicting types and overlong lists do not justify forced changes.

All six rules together produce the same three retags, with 213 cue-matched spans and 18 abstentions. The separately recomputed qualifying subset (`named_asset`, `shared_identifier`) has 128 cue-matched spans and 17 abstentions, with no introduced errors. Counts are span-level decisions and are not article counts or unique rule-match sums. [Machine-readable dispositions](summary.json).

## Verification and preservation

**198 fresh tests pass**, including **94 new context-study tests**. The 48 core cases cover six themes × English/Taglish × supported action, valid-location counterexample, abstention and Unicode/repeated mentions. Thirty-six cases have definitive references; twelve ambiguous cases remain unscored. Fixtures never become dataset members.

Checks cover physical facilities, attribution ambiguity, shared-list scope, ordinary counts, conflicting rules, deterministic/idempotent spans, unchanged boundaries, missing references, training projection, stale hashes, occupied destinations and competing writers. A constructed end-to-end test removes parent files before study to demonstrate that the worker uses only the training view. CLI guards block neural-library imports, network transport and child/training processes. No model was loaded. The existing Python **3.12.14** backend environment performed saved-span arithmetic; no dependency was installed.

A second independent process reproduced **all 11 private study files byte-for-byte**. Every one of the 345 final record decisions and every evidence offset was checked. **451 protected file hashes** remain unchanged; **55 completed-holdout entries** were checked through size/mtime metadata only, without reading contents. Historical test counts describe earlier tasks and are not added to this result. [Verification and hash bindings](verification.json).

Private versioned coordination, training-view, study and replay packages contain grounding, full fixtures, frozen source bytes, original/proposed labels, exact evidence, strict transitions, rule/family dispositions and manifests. Individual training passages, annotations, source identities and predictions remain ignored by Git. No predecessor was overwritten.

## Next gate

A **separate task** may propose a frozen validation-only comparison of the two qualifying rules. Preserve this exact implementation, subset and decision criteria before opening validation predictions for that comparison. No further rule tuning or selection follows from the current training result. Any later validation findings must retain their reused-validation limitation; the completed holdout stays excluded.

The neural model, annotations, 345/60 partitions, unresolved validation boundary, frozen rules baseline and production extraction code remain unchanged. References remain **AI-assisted silver**, with incomplete-history/accounting limitations. No collection, additional passages, annotation edits, neural inference, training, integration, upload, commit or push occurred. The desktop can remain off. See the [operator guide](../../guides/ner-context-safeguards.md).
