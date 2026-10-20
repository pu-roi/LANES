# Saved-article location recognition gap assessment

> **Last Updated:** October 20, 2026, 12:05 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The remaining 19 unresolved article rows have been reviewed against their saved source and predictions. **17 location occurrences are missing, three have incomplete or overlong boundaries, and one has an incompatible type.** The assessment is complete; these recognition defects remain unresolved. The trained model, v40 proposals and accepted v42 context extractor are unchanged.

## Scope and evidence

This is a diagnosis of the same previously reviewed article, using the authenticated v42 request, article expectations, saved output, verification/promotion receipts and earlier article snapshot. No extraction or neural inference was run. These are source-supported review dispositions, not new reference annotations or independent accuracy measurements.

The private case ledger records the article URL, body hash, row and target offsets, overlapping original predictions, affected facts, source evidence, uncertainty and recommended disposition. It remains under the ignored `backend/training/flood_ner/artifacts/recognition-gap-assessment-20261020-v43/` directory. Here, v43 identifies the assessment package; it is not a new extractor version. [Aggregate verification](verification.json) · [Predecessor outcome](../flood-ner-context-repair-v42-20261019/README.md).

## Reconciled findings

| Source-occurrence disposition | Count | Meaning |
|---|---:|---|
| Missing mention | 17 | No saved neural span covers the required occurrence. |
| Incomplete boundary | 2 | Only part of the required name is recognized. |
| Overlong boundary | 1 | The mention includes a junction connector. |
| Incompatible type | 1 | A junction member is labeled CITY. |
| Exact, consumer-compatible span | 13 | Individually usable by the current consumer, but insufficient to resolve the incomplete row. This does not certify its semantic label. |
| **Total** | **34** | **21 deficient occurrences across 19 rows.** |

Eighteen rows contain measurements: 32 required location occurrences, including 20 deficient occurrences. One additional unmeasured junction has two required occurrences, including one missing occurrence. Counts refer to occurrences, not distinct place names. A name recognized elsewhere does not repair a missing or partial occurrence in another row.

All 19 rows have an evidence-backed disposition and at least one deficient target. Their **93 unique retained, unassigned facts** comprise 36 depth facts, 19 observation-time facts, 19 status facts and 19 access facts. The measured rows account for 90 facts; the unmeasured row accounts for three. Its missing depth cannot be borrowed from a neighboring row. Retaining these facts does not count as recovering their location associations.

Six target occurrences additionally need label or meaning review: an interior-area description, an exact but semantically uncertain landmark label, a short abbreviation and three numbered addresses. This review flag overlaps the categories above; it adds no cases to the total. No full name or label is guessed.

## Recommended next task

Conduct a separately frozen, offline **location-proposal feasibility study** before changing effective locations:

1. Study exact, source-delimited junction names, including repeated complete names within the same article. Require evidence for each occurrence; do not propagate a name merely because it appears elsewhere.
2. Study boundary and type correction as explicit proposals with original neural spans retained. Each proposal must record exact offsets, source evidence, rule identity and provenance. No correction may be described as a neural prediction.
3. Keep uncertain abbreviations, numbered addresses and location types unresolved until their annotation convention and source support are specified. Do not promise that one rule family can resolve every row.
4. Freeze implementation, workload, fictional positive/counterexample expectations and downstream acceptance before processing real inputs. Retain predecessor-correct locations/associations, qualifiers and time roles; require zero new incorrect resolved links and location false positives. Report abstention separately from recovery.

This recommendation does not implement a fallback, revise references or require retraining. The model's six learned location labels remain distinct from depth/time recognition rules and matching rules. Observation time stays separate from onset, report and publication time; subsided status and time remain extraction evidence. Database history, plotting and interface work remain subsequent tasks.

## Verification and limits

All eight input bindings, 34 source slices, 19 row dispositions and 93 unique affected facts reconcile without omissions or duplicate counting. All 208 protected hashes and 55 frozen v41 files match. V42 freeze bindings and promoted application hashes match. Historical metadata remains unchanged for 1,538 entries, with the earlier declared preview-config change accounted separately; all 82 excluded metadata entries match. These sets overlap. Validation/holdout contents were not opened.

No new articles, source fetch, geographic lookup, database access/write, extraction rerun, inference, model/rule change, upload, commit or push occurred. No new application tests were needed because application code did not change. Earlier v42 test results remain historical results, not fresh tests from this assessment.

Three held references, the separate non-flood access omission, unfinished learned DEPTH/TIME recognition and unmeasured real pure-Tagalog performance remain open. The reviewed article does not establish performance on other articles or languages. The backend preview remains disabled by default.
